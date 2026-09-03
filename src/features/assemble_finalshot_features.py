"""Assemble the 103 frozen RBPNet signature shards into one memmap.

This remains outcome blind: it reads only cache shards, manifests, and the
certified intervention feature-row index.  Cell-context interactions are not
materialized here because they depend on assay rows rather than interventions.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "results" / "finalshot" / "rbp_signature_manifest.json"
OUT_MATRIX = ROOT / "data" / "interim" / "finalshot_rbpnet_features.npy"
OUT_METADATA = ROOT / "results" / "finalshot" / "rbp_feature_matrix_manifest.json"
OUT_DICTIONARY = ROOT / "results" / "finalshot" / "rbp_feature_dictionary.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = sorted(manifest["checkpoint_caches"], key=lambda item: item["task"])
    feature_names = manifest["feature_names"]
    if len(entries) != 103 or len(feature_names) != 9:
        raise RuntimeError("Frozen RBP signature dimensions changed")
    rows = manifest["source_interventions"]["interventions"]
    matrix = np.lib.format.open_memmap(
        OUT_MATRIX, mode="w+", dtype=np.float32, shape=(rows, len(entries) * len(feature_names))
    )
    dictionary: list[dict[str, object]] = []
    feature_row = np.arange(rows, dtype=np.int32)
    for group_index, entry in enumerate(entries):
        shard_path = ROOT / entry["feature_file"]
        if sha256(shard_path) != entry["feature_sha256"]:
            raise RuntimeError(f"Feature shard hash changed for {entry['task']}")
        with np.load(shard_path) as shard:
            values = shard["values"]
            if values.shape != (rows, 9) or not np.array_equal(shard["feature_row"], feature_row):
                raise RuntimeError(f"Feature shard row order changed for {entry['task']}")
            if shard["feature_names"].tolist() != feature_names or not np.isfinite(values).all():
                raise RuntimeError(f"Feature shard schema/value failure for {entry['task']}")
            start = group_index * 9
            matrix[:, start : start + 9] = values
        rbp = entry["task"].removesuffix("_HepG2")
        for within_group, feature_name in enumerate(feature_names):
            dictionary.append({
                "column_index": group_index * 9 + within_group,
                "group_index": group_index,
                "task": entry["task"],
                "human_rbp": rbp,
                "summary": feature_name,
                "role": "parent" if feature_name.startswith("parent_") else "delta",
            })
    matrix.flush()
    del matrix
    with OUT_DICTIONARY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dictionary[0]))
        writer.writeheader()
        writer.writerows(dictionary)
    metadata = {
        "phase": "FinalShot assembled RBPNet feature matrix",
        "signature_manifest_sha256": sha256(MANIFEST),
        "matrix_path": OUT_MATRIX.relative_to(ROOT).as_posix(),
        "matrix_shape": [rows, 927],
        "matrix_dtype": "float32",
        "matrix_sha256": sha256(OUT_MATRIX),
        "dictionary_path": OUT_DICTIONARY.relative_to(ROOT).as_posix(),
        "dictionary_sha256": sha256(OUT_DICTIONARY),
        "rbp_groups": 103,
        "features_per_group": 9,
        "feature_order": "alphabetical task, then frozen nine-summary order",
        "localization_outcomes_accessed": False,
        "nzip_outcomes_accessed": False,
        "astrocyte_data_accessed": False,
    }
    OUT_METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
