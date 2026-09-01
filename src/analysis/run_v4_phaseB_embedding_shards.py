"""Outcome-free CPU/GPU sharding for the definitive 3UTRBERT cache."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_v4_phaseB_models import INTERVENTIONS, full_embedding_paths
from src.modeling.v4_embeddings import embed_pairs_resumable, sha256


INTERIM = ROOT / "data/interim"
SHARD_ROWS = {
    "gpu": INTERIM / "v4_phaseB_3utrbert_missing_gpu.csv.gz",
    "cpu": INTERIM / "v4_phaseB_3utrbert_missing_cpu.csv.gz",
}


def shard_paths(device: str) -> tuple[Path, Path]:
    return (
        INTERIM / f"v4_phaseB_3utrbert_missing_{device}_features.npy",
        INTERIM / f"v4_phaseB_3utrbert_missing_{device}_features.json",
    )


def prepare() -> None:
    frame = pd.read_csv(INTERVENTIONS)
    full_path, _ = full_embedding_paths("3utrbert")
    full = np.load(full_path, mmap_mode="r")
    pending = ~np.isfinite(full[:, 0])
    work = frame.loc[pending].copy()
    work["original_feature_row"] = np.flatnonzero(pending)
    group_sizes = work.groupby("parent_id", sort=True).size().sort_values(ascending=False)
    assigned = {"gpu": [], "cpu": []}
    load = {"gpu": 0.0, "cpu": 0.0}
    capacity = {"gpu": 1.75, "cpu": 1.0}
    for parent_id, count in group_sizes.items():
        device = min(load, key=lambda value: (load[value] / capacity[value], value))
        assigned[device].append(parent_id)
        load[device] += float(count)
    audit = {"pending_rows": int(pending.sum()), "completed_rows_preserved": int((~pending).sum())}
    for device in ("gpu", "cpu"):
        shard = work[work["parent_id"].isin(assigned[device])].copy()
        shard = shard.sort_values(["parent_id", "dataset", "mutant_id"]).reset_index(drop=True)
        shard.to_csv(SHARD_ROWS[device], index=False, compression={"method": "gzip", "mtime": 0})
        audit[device] = {
            "rows": len(shard),
            "parent_groups": int(shard["parent_id"].nunique()),
            "original_rows_sha256": sha256(SHARD_ROWS[device]),
        }
    if sum(audit[device]["rows"] for device in ("gpu", "cpu")) != int(pending.sum()):
        raise ValueError("Embedding shard partition is incomplete")
    (INTERIM / "v4_phaseB_3utrbert_shard_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))


def embed(device: str, inference_device: str | None = None) -> None:
    frame = pd.read_csv(SHARD_ROWS[device])
    feature_path, metadata_path = shard_paths(device)
    backend_device = inference_device or device
    embed_pairs_resumable(
        frame,
        "3utrbert",
        feature_path,
        metadata_path,
        batch_size=64,
        backend=f"openvino_{backend_device}",
    )
    print(f"{device} shard sha256={sha256(feature_path)}", flush=True)


def merge() -> None:
    full_path, metadata_path = full_embedding_paths("3utrbert")
    full = np.lib.format.open_memmap(full_path, mode="r+")
    shard_records = {}
    occupied = set()
    for device in ("gpu", "cpu"):
        rows = pd.read_csv(SHARD_ROWS[device])
        features_path, shard_metadata = shard_paths(device)
        features = np.load(features_path, mmap_mode="r")
        if not np.isfinite(features).all() or len(features) != len(rows):
            raise ValueError(f"Incomplete {device} embedding shard")
        target = rows["original_feature_row"].to_numpy(int)
        if occupied.intersection(target):
            raise ValueError("Embedding shards overlap")
        occupied.update(target.tolist())
        full[target] = features
        full.flush()
        shard_records[device] = {
            "rows": len(rows),
            "features_sha256": sha256(features_path),
            "metadata_sha256": sha256(shard_metadata),
        }
    if not np.isfinite(full).all():
        raise ValueError("Merged full embedding cache is incomplete")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["completed_rows"] = len(full)
    metadata["inference_backends"] = ["torch", "openvino_gpu", "openvino_cpu"]
    metadata["openvino_equivalence_audit"] = "results/v4_phaseB/openvino_backend_equivalence.json"
    metadata["shards"] = shard_records
    metadata["feature_sha256"] = sha256(full_path)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "embed", "merge"])
    parser.add_argument("--device", choices=["gpu", "cpu"])
    parser.add_argument("--inference-device", choices=["gpu", "cpu"])
    args = parser.parse_args()
    if args.stage == "prepare":
        prepare()
    elif args.stage == "embed":
        if args.device is None:
            parser.error("--device is required for embed")
        embed(args.device, args.inference_device)
    else:
        merge()


if __name__ == "__main__":
    main()
