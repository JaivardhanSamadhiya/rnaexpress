"""Compact single-base encoder deltas. Model imports occur only after guards."""
from collections import defaultdict
import hashlib
import io
import os
import sys
import time

from .common import *
from src.generalization_splicebert_20261007.features import changed_positions, lookup_delta, projection_arrays
from src.generalization_splicebert_20261007.backend_probe import tokenize_lists, INPUT_NAMES, IR, MODEL, CHECKPOINT_SHA

GLOBAL_PROJECTION = BACK_ART / "global_projection.npy"
LOCAL_PROJECTION = BACK_ART / "local_projection.npy"
THREADS, BATCH, SHARD_ALLELES = 2, 2, 256
BACKEND_RECEIPT = BACK_OUT / "backend_synthetic_receipt.json"
OV_RUNTIME = NEXT_ART / "runtime"


def projections():
    proposal = readj(BACK_OUT / "feature_proposal.json")
    arrays = []
    expected_arrays = projection_arrays()
    for path, key, expected in zip((GLOBAL_PROJECTION, LOCAL_PROJECTION), ("global_projection_sha256", "local_projection_sha256"), expected_arrays):
        assert sha256(path) == proposal[key]
        matrix = np.load(path, allow_pickle=False)
        assert matrix.shape == (512, 128) and matrix.dtype == np.float32 and np.isfinite(matrix).all()
        np.testing.assert_array_equal(matrix, expected)
        arrays.append(matrix)
    return arrays


def backend_check():
    """Actual author/backend/runtime bytes, plus fixed synthetic parity checks."""
    preparation = BACK_OUT / "backend_preparation_manifest.json"
    committed(preparation)
    prepared = readj(preparation)
    assert prepared["status"] == "FROZEN_SYNTHETIC_BACKEND_PREPARATION_ONLY"
    for name, expected in prepared["files"].items():
        assert sha256(ROOT / name) == expected, name
    resource = readj(BACK_OUT / "resource_audit.json")
    assert resource["status"] == "PASS" and resource["public_free"]
    assert resource["author_archive_identity"] == "All selected checkpoint/tokenizer members byte-identical"
    for name, record in resource["cached_files"].items():
        assert sha256(MODEL / name) == record["sha256"]
    assert sha256(MODEL / "pytorch_model.bin") == CHECKPOINT_SHA
    backend = readj(BACKEND_RECEIPT)
    validate_backend_receipt(backend)
    assert backend["IR_xml_sha256"] == sha256(IR) and backend["IR_bin_sha256"] == sha256(IR.with_suffix(".bin"))
    runtime_receipt = readj(NEXT_OUT / "bert_runtime_integrity.json")
    actual = {path.relative_to(ROOT).as_posix() for path in OV_RUNTIME.rglob("*") if path.is_file()}
    assert actual == set(runtime_receipt["files"])
    for name, expected in runtime_receipt["files"].items():
        assert (ROOT / name).resolve().is_relative_to(OV_RUNTIME.resolve())
        assert sha256(ROOT / name) == expected, name
    return backend


def validate_backend_receipt(backend):
    """Pure receipt predicate; it never substitutes for actual-file checks."""
    assert backend["status"] == "PASS" and backend["scope"] == "SYNTHETIC_CPU_BACKEND_ADMISSION_ONLY"
    assert backend["checkpoint_sha256"] == CHECKPOINT_SHA
    assert backend["project_alleles_inferred"] == backend["models_fit"] == 0 and not backend["outcomes_used"]
    assert backend["synthetic_alleles"] == 16 and backend["CPU_threads"] == THREADS
    comparisons = backend["comparisons"]
    assert len(comparisons) == 8 and sorted(row["length_nt"] for row in comparisons) == [46, 46, 150, 150, 190, 190, 260, 260]
    for row in comparisons:
        assert all(row["checks"].values())
        assert row["maximum_hidden_absolute_difference"] <= .001
        assert row["mean_hidden_absolute_difference"] <= .0001
        assert row["minimum_token_cosine"] >= .999999


def production_guard(root_start=False):
    from src.generalization_splicebert_20261007.resources import resource_state
    assert root_start, "Root explicitly starts production after backend admission and commit"
    state = resource_state()
    assert state["resource_admission_now"], "Require fresh 3 GiB free RAM and 5 GiB disk"
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert os.environ.get("OPENBLAS_NUM_THREADS") == os.environ.get("OMP_NUM_THREADS") == str(THREADS)
    production_check()
    backend = backend_check()
    projections()
    spec = readj(OUT / "feature_spec.json")
    assert spec["threads"] == THREADS and spec["batch_size"] == BATCH and spec["shard_alleles"] == SHARD_ALLELES
    assert not (OUT / "features_receipt.json").exists(), "Preserve completed production"
    state = resource_state()
    assert state["resource_admission_now"], "Resource headroom changed during validation"
    return backend, state


class Encoder:
    def __init__(self, backend):
        # No Torch, tokenizer package, unpickling or remote code in production.
        sys.path.insert(0, str(OV_RUNTIME))
        import openvino as ov
        assert ov.get_version() == backend["openvino_version"]
        self.compiled = ov.Core().compile_model(str(IR), "CPU", {"INFERENCE_NUM_THREADS": THREADS,
            "INFERENCE_PRECISION_HINT": "f32", "NUM_STREAMS": 1})
        assert len(self.compiled.inputs) == 3 and len(self.compiled.outputs) == 1
        assert {port.get_any_name() for port in self.compiled.inputs} == set(INPUT_NAMES)

    def hidden(self, sequences):
        batch = certified_batch(sequences)
        inputs = {name: np.asarray(value, dtype=np.int64) for name, value in tokenize_lists(batch).items()}
        hidden = np.asarray(self.compiled(inputs)[0])
        assert hidden.shape == (BATCH, len(sequences[0]) + 2, 512)
        assert hidden.dtype == np.float32 and np.isfinite(hidden).all()
        return hidden[:len(sequences)]


def certified_batch(sequences):
    """Duplicate an odd tail allele, preserving the certified batch2 shape."""
    assert 1 <= len(sequences) <= BATCH and len(set(map(len, sequences))) == 1
    assert all(sequence and set(sequence) <= set("ACGT") for sequence in sequences)
    return list(sequences) + [sequences[-1]] * (BATCH - len(sequences))


def requirements(encoded):
    required = defaultdict(set)
    for parent, mutant in zip(encoded.parent_sequence, encoded.mutant_sequence):
        positions = changed_positions(parent, mutant)
        assert len(positions), "Every admitted candidate must be an actual edit"
        required[parent].update(map(int, positions)); required[mutant].update(map(int, positions))
    alleles = sorted(required, key=lambda sequence: (len(sequence), hashlib.sha256(sequence.encode()).hexdigest(), sequence))
    return required, alleles


def compact_values(hidden, length, positions, pglobal, plocal):
    assert hidden.shape == (length + 2, 512) and np.isfinite(hidden).all()
    positions = np.asarray(positions, dtype=np.int16)
    assert len(positions) and np.array_equal(positions, np.unique(positions))
    assert positions.min() >= 0 and positions.max() < length
    return (hidden[1:length + 1].mean(0) @ pglobal).astype(np.float32), (hidden[positions + 1] @ plocal).astype(np.float32)


def assemble_pair(parent, mutant, summaries):
    positions = changed_positions(parent, mutant)
    if not len(positions):
        return np.zeros(256, dtype=np.float32)
    gp, pp, tp = summaries[parent]; gm, pm, tm = summaries[mutant]
    pi, mi = np.searchsorted(pp, positions), np.searchsorted(pm, positions)
    assert np.all(pi < len(pp)) and np.all(mi < len(pm))
    np.testing.assert_array_equal(pp[pi], positions); np.testing.assert_array_equal(pm[mi], positions)
    result = np.r_[gm - gp, (tm[mi] - tp[pi]).mean(0)].astype(np.float32)
    assert result.shape == (256,) and np.isfinite(result).all()
    return result


def validate_shard(path, expected_hashes, offsets, positions, spec_sha):
    path = Path(path)
    sidecar_path = path.with_suffix(".json")
    assert sidecar_path.is_file(), "Preserve unreceipted/orphan shard"
    sidecar = readj(sidecar_path)
    assert sidecar["sha256"] == sha256(path), "Cached shard changed"
    assert sidecar["spec_sha256"] == spec_sha and sidecar["allele_hashes"] == expected_hashes.tolist()
    with np.load(path, allow_pickle=False) as data:
        assert set(data.files) == {"allele_hashes", "offsets", "positions", "globals", "tokens"}
        np.testing.assert_array_equal(data["allele_hashes"], expected_hashes)
        np.testing.assert_array_equal(data["offsets"], offsets)
        np.testing.assert_array_equal(data["positions"], positions)
        globals_, tokens = data["globals"].copy(), data["tokens"].copy()
    assert globals_.dtype == tokens.dtype == np.float32
    assert globals_.shape == (len(expected_hashes), 128) and tokens.shape == (int(offsets[-1]), 128)
    assert np.isfinite(globals_).all() and np.isfinite(tokens).all()
    return globals_, tokens


def produce(root_start=False):
    backend, headroom = production_guard(root_start)
    original, encoded = sequence_frames()
    plan = readj(OUT / "plan_receipt.json")
    assert row_identity(encoded) == plan["encoded_row_identity_sha256"]
    assert metadata_identity(original) == plan["original_metadata_identity_sha256"]
    pglobal, plocal = projections()
    required, alleles = requirements(encoded)
    assert len(alleles) == 18220
    inventory = [{"index": index, "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
        "length": len(sequence), "required_positions": sorted(required[sequence])} for index, sequence in enumerate(alleles)]
    spec_sha = sha256(OUT / "feature_spec.json")
    cache = ART / "compact_cache"; cache.mkdir(parents=True, exist_ok=True)
    jsave(cache / "index.json", {"encoded_row_identity_sha256": row_identity(encoded), "alleles": inventory, "spec_sha256": spec_sha})
    summaries, shards, encoder = {}, [], None
    groups = defaultdict(list)
    for index, sequence in enumerate(alleles):
        groups[len(sequence)].append(index)
    started = time.perf_counter(); shard_number = 0
    for length, indexes in sorted(groups.items()):
        for offset in range(0, len(indexes), SHARD_ALLELES):
            ids = indexes[offset:offset + SHARD_ALLELES]
            sequences = [alleles[index] for index in ids]
            positions = [np.asarray(sorted(required[sequence]), dtype=np.int16) for sequence in sequences]
            hashes = np.asarray([inventory[index]["sequence_sha256"] for index in ids])
            boundaries = np.r_[0, np.cumsum([len(position) for position in positions])]
            flat_positions = np.concatenate(positions)
            path = cache / f"shard_{shard_number:04d}.npz"; shard_number += 1
            if not path.exists():
                assert not path.with_suffix(".json").exists(), "Preserve orphan sidecar"
                if encoder is None:
                    encoder = Encoder(backend)
                globals_ = np.empty((len(ids), 128), dtype=np.float32)
                tokens = np.empty((int(boundaries[-1]), 128), dtype=np.float32)
                for first in range(0, len(ids), BATCH):
                    batch = sequences[first:first + BATCH]
                    hidden = encoder.hidden(batch)
                    for local, values in enumerate(hidden):
                        index = first + local
                        global_, local_ = compact_values(values, length, positions[index], pglobal, plocal)
                        globals_[index] = global_
                        tokens[boundaries[index]:boundaries[index + 1]] = local_
                buffer = io.BytesIO()
                np.savez_compressed(buffer, allele_hashes=hashes, offsets=boundaries, positions=flat_positions, globals=globals_, tokens=tokens)
                save(path, buffer.getvalue())
                jsave(path.with_suffix(".json"), {"sha256": sha256(path), "spec_sha256": spec_sha,
                    "allele_hashes": hashes.tolist(), "scope": "Creation-time immutable content digest; required before resume"})
            globals_, tokens = validate_shard(path, hashes, boundaries, flat_positions, spec_sha)
            for local, sequence in enumerate(sequences):
                summaries[sequence] = (globals_[local].copy(), positions[local].copy(), tokens[boundaries[local]:boundaries[local + 1]].copy())
            shards.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path),
                "sidecar_path": path.with_suffix(".json").relative_to(ROOT).as_posix(), "sidecar_sha256": sha256(path.with_suffix(".json")), "alleles": len(ids)})
            print("SpliceBERT compact shard", shard_number, "alleles", len(summaries), "of", len(alleles), "elapsed_s", round(time.perf_counter() - started, 1), flush=True)
    features = np.empty((len(encoded), 256), dtype=np.float32); lookup = np.empty_like(features)
    for index, (parent, mutant) in enumerate(zip(encoded.parent_sequence, encoded.mutant_sequence)):
        features[index] = assemble_pair(parent, mutant, summaries)
        lookup[index] = lookup_delta(parent, mutant, pglobal, plocal)
    matrixsave(ART / "splicebert_features.npz", features); matrixsave(ART / "lookup_features.npz", lookup)
    jsave(OUT / "features_receipt.json", {"status": "PASS", "scope": "Outcome-free single-base feature production; no fitting",
        "rows": len(encoded), "columns": 256, "unique_alleles": len(alleles), "encoded_row_identity_sha256": row_identity(encoded),
        "original_metadata_identity_sha256": metadata_identity(original), "spec_sha256": spec_sha,
        "production_manifest_sha256": sha256(OUT / "feature_production_manifest.json"), "backend_receipt_sha256": sha256(BACKEND_RECEIPT),
        "splicebert_features_sha256": sha256(ART / "splicebert_features.npz"), "lookup_features_sha256": sha256(ART / "lookup_features.npz"),
        "compact_shards": shards, "cache_index_sha256": sha256(cache / "index.json"),
        "required_projected_tokens": sum(len(required[sequence]) for sequence in alleles),
        "threads": THREADS, "batch_size": BATCH, "headroom_before_import": headroom, "elapsed_seconds": time.perf_counter() - started,
        "outcomes_used": False, "models_fit": 0, "SRLE46nt_OOD": True})


if __name__ == "__main__":
    assert sys.argv[1:] == ["produce", "--root-start"]
    produce(root_start=True)
