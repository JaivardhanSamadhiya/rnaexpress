"""Build and audit the outcome-free RNAddress v3 mechanistic feature block."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.v3_mechanistic_features import build_mechanistic_features


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/v2/nzip_development_predictions.csv.gz"
CACHE = ROOT / "data/interim/v3_nzip_structure_cache.json"
FEATURES = ROOT / "data/interim/v3_nzip_mechanistic_features.npy"
OUT = ROOT / "results/v3_phase3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    frame = pd.read_csv(SOURCE)
    if len(frame) != 4_395 or frame["parent_id"].nunique() != 15:
        raise ValueError("Frozen N-zip shape changed")
    result = build_mechanistic_features(frame, CACHE)
    np.save(FEATURES, result.values, allow_pickle=False)

    schema = pd.DataFrame(
        {
            "feature_index": np.arange(len(result.names), dtype=int),
            "feature_name": result.names,
            "families": [";".join(value) for value in result.families],
            "minimum": result.values.min(axis=0),
            "maximum": result.values.max(axis=0),
            "mean": result.values.mean(axis=0),
            "standard_deviation": result.values.std(axis=0),
            "nonzero_fraction": (result.values != 0).mean(axis=0),
        }
    )
    schema.to_csv(OUT / "mechanistic_feature_schema.csv", index=False, lineterminator="\n")
    family_rows = []
    all_families = sorted({family for values in result.families for family in values})
    for family in all_families:
        indices = [index for index, values in enumerate(result.families) if family in values]
        family_rows.append(
            {
                "family": family,
                "feature_count": len(indices),
                "nonconstant_feature_count": int(
                    sum(float(np.ptp(result.values[:, index])) > 0 for index in indices)
                ),
                "feature_indices": ";".join(map(str, indices)),
            }
        )
    pd.DataFrame(family_rows).to_csv(
        OUT / "mechanistic_feature_families.csv", index=False, lineterminator="\n"
    )
    manifest = {
        "phase": "v3_phase3_mechanistic_feature_audit",
        "analysis_class": "DEVELOPMENT_OUTCOME_FREE_FEATURE_BUILD",
        "rows": len(frame),
        "parents": int(frame["parent_id"].nunique()),
        "feature_count_without_stability": len(result.names),
        "source_sha256": sha256(SOURCE),
        "feature_cache": str(FEATURES.relative_to(ROOT)).replace("\\", "/"),
        "feature_cache_sha256": sha256(FEATURES),
        "structure_cache": str(CACHE.relative_to(ROOT)).replace("\\", "/"),
        "structure_cache_sha256": sha256(CACHE),
        "structure_sequence_count": 4_410,
        "fixed_radii": [5, 10, 20],
        "motif_family_count": 5,
        "measurement_aware_target_feasible": False,
        "stability_auxiliary_pending": True,
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    (OUT / "mechanistic_feature_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
