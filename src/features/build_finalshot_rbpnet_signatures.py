"""Reconstruct frozen RBPNet output-space intervention signatures.

This script is deliberately outcome blind.  It reads only the certified v4
sequence/intervention index and the frozen checkpoint manifest.  Profiles are
cached checkpoint-by-checkpoint so the multi-hour CPU run is resumable.
"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INTERVENTIONS = ROOT / "results" / "v4_phaseB" / "model_interventions.csv.gz"
CHECKPOINT_MANIFEST = ROOT / "results" / "finalshot" / "rbpnet_checkpoint_manifest.csv"
MODEL_DIR = ROOT / "data" / "raw" / "finalshot_resource_audit" / "RBPNet_models" / "models"
DEFAULT_RUNTIME = ROOT / "tmp" / "finalshot_rbpnet_runtime"
RBNET_SOURCE = ROOT / "data" / "raw" / "finalshot_resource_audit" / "rbpnet"
DEFAULT_CACHE = ROOT / "data" / "interim" / "finalshot_rbpnet_cache"
FINAL_MANIFEST = ROOT / "results" / "finalshot" / "rbp_signature_manifest.json"
FEATURE_NAMES = np.asarray([
    "delta_mass_radius10",
    "delta_mass_radius25",
    "delta_mass_radius50",
    "max_abs_delta_radius25",
    "binding_gained_global",
    "binding_lost_global",
    "parent_mass_radius25",
    "parent_mixing_coefficient",
    "delta_mixing_coefficient",
])
EXPECTED_INTERVENTIONS = 62_665
EXPECTED_SEQUENCES = 72_998
EXPECTED_CHECKPOINTS = 103
RBNET_COMMIT = "8ee000dcdb897e0eeed6a46a855604299e914ca7"
ARCHIVE_SHA256 = "dc182e51d7b3ffe046ec7de56ab7e98a9ec0bd2f789d8e6bd61168b3718c355d"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sequence_sha256(sequence: str) -> str:
    return hashlib.sha256(sequence.encode("ascii")).hexdigest()


def write_json_atomic(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_npz_atomic(path: Path, **arrays: np.ndarray) -> None:
    temporary = path.with_name(path.name + ".partial.npz")
    np.savez(temporary, **arrays)
    temporary.replace(path)


def load_sequence_index(cache: Path) -> tuple[pd.DataFrame, list[str], np.ndarray, np.ndarray]:
    interventions = pd.read_csv(INTERVENTIONS)
    if len(interventions) != EXPECTED_INTERVENTIONS:
        raise RuntimeError(f"Expected {EXPECTED_INTERVENTIONS} interventions, found {len(interventions)}")
    required = {"feature_row", "parent_sequence", "mutant_sequence"}
    if not required.issubset(interventions):
        raise RuntimeError("Certified intervention index lacks required sequence columns")
    if not np.array_equal(np.sort(interventions["feature_row"].to_numpy()), np.arange(len(interventions))):
        raise RuntimeError("feature_row is not a complete zero-based index")

    hash_to_sequence: dict[str, str] = {}
    for sequence in pd.concat(
        [interventions["parent_sequence"], interventions["mutant_sequence"]], ignore_index=True
    ).astype(str):
        digest = sequence_sha256(sequence)
        previous = hash_to_sequence.setdefault(digest, sequence)
        if previous != sequence:
            raise RuntimeError("SHA-256 collision in development sequences")
    if len(hash_to_sequence) != EXPECTED_SEQUENCES:
        raise RuntimeError(f"Expected {EXPECTED_SEQUENCES} unique sequences, found {len(hash_to_sequence)}")
    hashes = sorted(hash_to_sequence)
    sequences = [hash_to_sequence[digest] for digest in hashes]
    lengths = np.asarray([len(sequence) for sequence in sequences], dtype=np.int16)
    if set(lengths.tolist()) != {150, 260}:
        raise RuntimeError(f"Unexpected native sequence lengths: {sorted(set(lengths.tolist()))}")
    if any(set(sequence) - set("ACGT") for sequence in sequences):
        raise RuntimeError("Certified sequence contains a non-ACGT character")

    index_by_hash = {digest: index for index, digest in enumerate(hashes)}
    parent_index = np.asarray(
        [index_by_hash[sequence_sha256(str(sequence))] for sequence in interventions["parent_sequence"]],
        dtype=np.int32,
    )
    mutant_index = np.asarray(
        [index_by_hash[sequence_sha256(str(sequence))] for sequence in interventions["mutant_sequence"]],
        dtype=np.int32,
    )
    starts = np.empty(len(interventions), dtype=np.int16)
    ends = np.empty(len(interventions), dtype=np.int16)
    for row_index, (parent, mutant) in enumerate(
        zip(interventions["parent_sequence"].astype(str), interventions["mutant_sequence"].astype(str))
    ):
        changed = np.flatnonzero(np.frombuffer(parent.encode("ascii"), dtype=np.uint8) !=
                                 np.frombuffer(mutant.encode("ascii"), dtype=np.uint8))
        if changed.size == 0:
            raise RuntimeError(f"Zero-edit intervention at feature row {row_index}")
        starts[row_index] = int(changed.min())
        ends[row_index] = int(changed.max()) + 1
        if len(parent) != len(mutant):
            raise RuntimeError("FinalShot protocol requires aligned equal-length sequence pairs")

    index_frame = pd.DataFrame({
        "sequence_sha256": hashes,
        "length": lengths,
        "sequence": sequences,
    })
    index_path = cache / "sequence_index.csv.gz"
    index_frame.to_csv(index_path, index=False, compression={"method": "gzip", "mtime": 0})
    np.savez(cache / "intervention_index.npz", parent_index=parent_index, mutant_index=mutant_index,
             edit_start=starts, edit_end=ends,
             feature_row=interventions["feature_row"].to_numpy(dtype=np.int32))
    return interventions, sequences, lengths, np.stack([parent_index, mutant_index, starts, ends], axis=1)


def one_hot(sequences: list[str]) -> np.ndarray:
    length = len(sequences[0])
    encoded = np.empty((len(sequences), length), dtype=np.uint8)
    lookup = np.full(256, 255, dtype=np.uint8)
    lookup[ord("A")], lookup[ord("C")], lookup[ord("G")], lookup[ord("T")] = 0, 1, 2, 3
    for index, sequence in enumerate(sequences):
        encoded[index] = lookup[np.frombuffer(sequence.encode("ascii"), dtype=np.uint8)]
    if (encoded == 255).any():
        raise RuntimeError("Non-ACGT input reached one-hot encoder")
    return np.eye(4, dtype=np.float32)[encoded]


def infer_checkpoint(
    model_path: Path,
    task: str,
    sequences: list[str],
    lengths: np.ndarray,
    batch_size: int,
    load_model,
    tf,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    started = time.time()
    model = load_model(model_path)
    profiles = np.zeros((len(sequences), int(lengths.max())), dtype=np.float32)
    mixing = np.empty(len(sequences), dtype=np.float32)
    target_key = f"{task}_profile_target"
    mixing_key = f"{task}_mixing_coefficient"
    batches = 0
    for native_length in sorted(set(lengths.tolist())):
        group = np.flatnonzero(lengths == native_length)
        for offset in range(0, len(group), batch_size):
            indices = group[offset : offset + batch_size]
            batch = one_hot([sequences[index] for index in indices])
            outputs = model(batch, training=False)
            if target_key not in outputs or mixing_key not in outputs:
                raise RuntimeError(f"Checkpoint output schema changed for {task}")
            probability = tf.nn.softmax(outputs[target_key], axis=1).numpy().astype(np.float32)
            # The serialized head emits an unconstrained logit.  RBPNet's
            # official prediction._to_probs applies sigmoid before exposing it
            # as the mixing coefficient.
            alpha = tf.nn.sigmoid(outputs[mixing_key]).numpy().reshape(-1).astype(np.float32)
            if probability.shape != (len(indices), native_length) or alpha.shape != (len(indices),):
                raise RuntimeError(f"Checkpoint output dimensions changed for {task}")
            profiles[indices, :native_length] = probability
            mixing[indices] = alpha
            batches += 1
    sums = np.asarray([profiles[index, :length].sum() for index, length in enumerate(lengths)])
    if not np.isfinite(profiles).all() or not np.isfinite(mixing).all():
        raise RuntimeError(f"Non-finite checkpoint output for {task}")
    if not np.allclose(sums, 1.0, atol=2e-6, rtol=0):
        raise RuntimeError(f"Target profile failed normalization for {task}")
    if (mixing < 0).any() or (mixing > 1).any():
        raise RuntimeError(f"Mixing coefficient outside [0,1] for {task}")
    diagnostics = {
        "seconds": time.time() - started,
        "batches": batches,
        "profile_sum_max_abs_error": float(np.max(np.abs(sums - 1.0))),
        "mixing_min": float(mixing.min()),
        "mixing_max": float(mixing.max()),
    }
    tf.keras.backend.clear_session()
    del model
    gc.collect()
    return profiles, mixing, diagnostics


def summarize_interventions(
    profiles: np.ndarray,
    mixing: np.ndarray,
    lengths: np.ndarray,
    pair_index: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    features = np.empty((len(pair_index), len(FEATURE_NAMES)), dtype=np.float32)
    positions = np.arange(profiles.shape[1])[None, :]
    max_gain_loss_error = 0.0
    max_global_delta_error = 0.0
    for offset in range(0, len(pair_index), 4096):
        batch = pair_index[offset : offset + 4096]
        parent_index, mutant_index = batch[:, 0], batch[:, 1]
        starts, ends = batch[:, 2:3], batch[:, 3:4]
        native_lengths = lengths[parent_index, None]
        if not np.array_equal(native_lengths[:, 0], lengths[mutant_index]):
            raise RuntimeError("Parent/mutant native lengths differ")
        parent = profiles[parent_index]
        delta = profiles[mutant_index] - parent
        valid = positions < native_lengths
        delta = np.where(valid, delta, 0.0)

        masks = {}
        for radius in (10, 25, 50):
            left = np.maximum(0, starts - radius)
            right = np.minimum(native_lengths, ends + radius)
            masks[radius] = (positions >= left) & (positions < right)
        gain = np.maximum(delta, 0.0).sum(axis=1)
        loss = np.maximum(-delta, 0.0).sum(axis=1)
        global_delta = delta.sum(axis=1)
        max_gain_loss_error = max(max_gain_loss_error, float(np.max(np.abs(gain - loss))))
        max_global_delta_error = max(max_global_delta_error, float(np.max(np.abs(global_delta))))

        target = features[offset : offset + len(batch)]
        target[:, 0] = np.where(masks[10], delta, 0.0).sum(axis=1)
        target[:, 1] = np.where(masks[25], delta, 0.0).sum(axis=1)
        target[:, 2] = np.where(masks[50], delta, 0.0).sum(axis=1)
        target[:, 3] = np.where(masks[25], np.abs(delta), -np.inf).max(axis=1)
        target[:, 4] = gain
        target[:, 5] = loss
        target[:, 6] = np.where(masks[25], parent, 0.0).sum(axis=1)
        target[:, 7] = mixing[parent_index]
        target[:, 8] = mixing[mutant_index] - mixing[parent_index]
    if not np.isfinite(features).all():
        raise RuntimeError("Non-finite intervention signature")
    if max_global_delta_error > 5e-6 or max_gain_loss_error > 5e-6:
        raise RuntimeError("Binding-delta conservation invariant failed")
    return features, {
        "max_abs_global_signed_delta": max_global_delta_error,
        "max_abs_gain_loss_difference": max_gain_loss_error,
    }


def configure_runtime(runtime: Path):
    sys.path.insert(0, str(RBNET_SOURCE))
    sys.path.insert(0, str(runtime))
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import tensorflow as tf  # type: ignore
    from rbpnet.load import load_model  # type: ignore
    return load_model, tf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    args.cache.mkdir(parents=True, exist_ok=True)
    profile_dir, feature_dir = args.cache / "profiles", args.cache / "features"
    profile_dir.mkdir(exist_ok=True)
    feature_dir.mkdir(exist_ok=True)
    interventions, sequences, lengths, pair_index = load_sequence_index(args.cache)
    sequence_hashes = np.asarray([sequence_sha256(sequence) for sequence in sequences], dtype="S64")

    checkpoints = pd.read_csv(CHECKPOINT_MANIFEST).sort_values("task").reset_index(drop=True)
    if len(checkpoints) != EXPECTED_CHECKPOINTS:
        raise RuntimeError(f"Expected {EXPECTED_CHECKPOINTS} checkpoints, found {len(checkpoints)}")
    selected = checkpoints
    if args.only:
        selected = selected[selected["task"].isin(args.only)]
        missing = set(args.only) - set(selected["task"])
        if missing:
            raise RuntimeError(f"Unknown requested checkpoint(s): {sorted(missing)}")
    if args.limit is not None:
        selected = selected.head(args.limit)

    progress_path = args.cache / "progress_manifest.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.exists() else {}
    load_model = tf = None
    for ordinal, row in enumerate(selected.itertuples(index=False), start=1):
        task = str(row.task)
        model_path = MODEL_DIR / str(row.filename)
        if sha256(model_path) != str(row.sha256):
            raise RuntimeError(f"Checkpoint hash mismatch: {task}")
        profile_path = profile_dir / f"{task}.npz"
        feature_path = feature_dir / f"{task}.npz"
        if profile_path.exists() and feature_path.exists():
            entry = progress.get(task, {})
            if entry.get("profile_sha256") == sha256(profile_path) and entry.get("feature_sha256") == sha256(feature_path):
                print(f"[{ordinal}/{len(selected)}] {task}: verified cached", flush=True)
                continue

        print(f"[{ordinal}/{len(selected)}] {task}: starting", flush=True)
        if profile_path.exists():
            with np.load(profile_path) as cached:
                if not np.array_equal(cached["sequence_sha256"], sequence_hashes):
                    raise RuntimeError(f"Sequence order mismatch in cached profile: {task}")
                profiles = cached["target_profile"].astype(np.float32)
                mixing = cached["mixing"].astype(np.float32)
            inference_diagnostics = progress.get(task, {}).get("inference", {"resumed": True})
        else:
            if load_model is None:
                load_model, tf = configure_runtime(args.runtime)
            profiles, mixing, inference_diagnostics = infer_checkpoint(
                model_path, task, sequences, lengths, args.batch_size, load_model, tf
            )
            write_npz_atomic(profile_path, sequence_sha256=sequence_hashes, lengths=lengths,
                             target_profile=profiles, mixing=mixing)

        features, signature_diagnostics = summarize_interventions(profiles, mixing, lengths, pair_index)
        write_npz_atomic(
            feature_path,
            feature_row=interventions["feature_row"].to_numpy(dtype=np.int32),
            feature_names=FEATURE_NAMES,
            values=features,
        )
        progress[task] = {
            "checkpoint_sha256": str(row.sha256),
            "profile_file": profile_path.relative_to(ROOT).as_posix(),
            "profile_sha256": sha256(profile_path),
            "feature_file": feature_path.relative_to(ROOT).as_posix(),
            "feature_sha256": sha256(feature_path),
            "inference": inference_diagnostics,
            "signature": signature_diagnostics,
        }
        write_json_atomic(progress_path, progress)
        del profiles, mixing, features
        gc.collect()
        print(f"[{ordinal}/{len(selected)}] {task}: complete ({inference_diagnostics.get('seconds', 0):.1f}s)", flush=True)

    complete = set(progress) == set(checkpoints["task"])
    if complete:
        entries = [dict(task=task, **progress[task]) for task in sorted(progress)]
        manifest = {
            "phase": "FinalShot RBPNet output-space reconstruction",
            "protocol_commit": "30c89a3",
            "rbpnet_commit": RBNET_COMMIT,
            "rbpnet_archive_sha256": ARCHIVE_SHA256,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "tensorflow": getattr(tf, "__version__", "2.15.1 (resumed cache)"),
            "source_interventions": {
                "path": INTERVENTIONS.relative_to(ROOT).as_posix(),
                "bytes": INTERVENTIONS.stat().st_size,
                "sha256": sha256(INTERVENTIONS),
                "interventions": len(interventions),
            },
            "sequence_index": {
                "path": (args.cache / "sequence_index.csv.gz").relative_to(ROOT).as_posix(),
                "sha256": sha256(args.cache / "sequence_index.csv.gz"),
                "unique_sequences": len(sequences),
                "length_counts": {str(value): int((lengths == value).sum()) for value in sorted(set(lengths))},
            },
            "profile_output": "softmax-normalized protein-specific target profile at native sequence length",
            "feature_names": FEATURE_NAMES.tolist(),
            "checkpoint_count": len(entries),
            "checkpoint_caches": entries,
            "localization_outcomes_accessed": False,
            "nzip_outcomes_accessed": False,
            "astrocyte_data_accessed": False,
        }
        write_json_atomic(FINAL_MANIFEST, manifest)
        print(f"Complete manifest: {FINAL_MANIFEST}", flush=True)
    else:
        print(f"Partial cache: {len(progress)}/{len(checkpoints)} checkpoints", flush=True)


if __name__ == "__main__":
    main()
