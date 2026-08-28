"""Evaluate the frozen strongest-fair-forward family for Phase 3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.features import normalize_sequence
from src.modeling.utrbert_features import sha256_bytes
from src.modeling.v3_forward import nested_forward_ridge
from src.modeling.v3_nested import directional_metrics, macro_metrics, selection_score


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/v2_6/nzip_nested_stack_predictions.csv.gz"
OUT = ROOT / "results/v3_phase3"
INTERIM = ROOT / "data/interim"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _map_absolute(
    frame: pd.DataFrame,
    features_path: Path,
    sequences_path: Path,
) -> tuple[np.ndarray, np.ndarray]:
    features = np.load(features_path, allow_pickle=False)
    sequences = np.load(sequences_path, allow_pickle=False)
    lookup = {
        sha256_bytes(normalize_sequence(sequence)): features[index]
        for index, sequence in enumerate(sequences)
    }
    mutant = np.vstack(
        [lookup[sha256_bytes(normalize_sequence(value))] for value in frame["mutant_sequence"]]
    ).astype(np.float32)
    parent = np.vstack(
        [lookup[sha256_bytes(normalize_sequence(value))] for value in frame["parent_sequence"]]
    ).astype(np.float32)
    return mutant, parent


def _run_or_load(name: str, frame: pd.DataFrame, mutant: np.ndarray, parent: np.ndarray):
    prediction_path = INTERIM / f"v3_forward_{name}_prediction.npy"
    tuning_path = INTERIM / f"v3_forward_{name}_tuning.csv"
    if prediction_path.exists() and tuning_path.exists():
        print(f"loaded cached forward comparator: {name}", flush=True)
        return np.load(prediction_path, allow_pickle=False), pd.read_csv(tuning_path)
    result = nested_forward_ridge(frame, mutant, parent)
    np.save(prediction_path, result.prediction, allow_pickle=False)
    result.tuning.to_csv(tuning_path, index=False, lineterminator="\n")
    return result.prediction, result.tuning


def main() -> None:
    frame = pd.read_csv(SOURCE)
    splice_mutant, splice_parent = _map_absolute(
        frame,
        INTERIM / "splicebert_v2_4_nzip_absolute.npy",
        INTERIM / "splicebert_v2_4_nzip_sequences.npy",
    )
    utr_mutant, utr_parent = _map_absolute(
        frame,
        INTERIM / "v3_3utrbert_absolute_features.npy",
        INTERIM / "v3_3utrbert_absolute_sequences.npy",
    )
    splice_prediction, splice_tuning = _run_or_load(
        "splicebert", frame, splice_mutant, splice_parent
    )
    utr_prediction, utr_tuning = _run_or_load(
        "3utrbert", frame, utr_mutant, utr_parent
    )
    predictions = {
        "forward_lightgbm": frame["pred_forward_lightgbm"].to_numpy(float),
        "forward_splicebert_absolute_ridge": splice_prediction,
        "forward_3utrbert_absolute_ridge": utr_prediction,
    }
    output = frame[["source_row", "parent_id", "delta_localization"]].copy()
    metrics = []
    macro_rows = []
    for model, prediction in predictions.items():
        output[f"{model}_score"] = prediction
        table = directional_metrics(frame, prediction, -prediction, model=model)
        metrics.append(table)
        row = macro_metrics(table)
        row["model"] = model
        row["selection_score"] = selection_score(table)
        macro_rows.append(row)
    macro = pd.DataFrame(macro_rows).sort_values(
        "selection_score", ascending=False, kind="stable"
    )
    maximum_score = float(macro["selection_score"].max())
    eligible = set(
        macro.loc[macro["selection_score"] >= maximum_score - 0.002, "model"].astype(str)
    )
    simplicity_order = (
        "forward_splicebert_absolute_ridge",
        "forward_3utrbert_absolute_ridge",
        "forward_lightgbm",
    )
    strongest = next(model for model in simplicity_order if model in eligible)
    output.to_csv(
        OUT / "forward_outer_predictions.csv.gz",
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    pd.concat(metrics, ignore_index=True).to_csv(
        OUT / "forward_parent_direction_metrics.csv", index=False, lineterminator="\n"
    )
    macro.to_csv(OUT / "forward_macro_metrics.csv", index=False, lineterminator="\n")
    tuning = []
    for model, table in (
        ("forward_splicebert_absolute_ridge", splice_tuning),
        ("forward_3utrbert_absolute_ridge", utr_tuning),
    ):
        value = table.copy()
        value.insert(0, "model", model)
        tuning.append(value)
    pd.concat(tuning, ignore_index=True).to_csv(
        OUT / "forward_inner_selections.csv", index=False, lineterminator="\n"
    )
    selection = {
        "strongest_fair_forward": strongest,
        "selection_rule": "highest frozen selection score; ties within 0.002 prefer simpler then historical",
        "candidate_count": 3,
        "protected_data_access": {
            "astrocyte_outcomes_opened": False,
            "moffatt_archive_opened": False,
        },
    }
    (OUT / "forward_selection.json").write_text(
        json.dumps(selection, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "phase": "v3_phase3_forward_comparators",
        "rows": len(frame),
        "parents": int(frame["parent_id"].nunique()),
        "source_sha256": sha256(SOURCE),
        "absolute_cache_hashes": {
            name: sha256(INTERIM / name)
            for name in (
                "splicebert_v2_4_nzip_absolute.npy",
                "splicebert_v2_4_nzip_sequences.npy",
                "v3_3utrbert_absolute_features.npy",
                "v3_3utrbert_absolute_sequences.npy",
            )
        },
        "selection": selection,
    }
    (OUT / "forward_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(macro.to_string(index=False))
    print(json.dumps(selection, indent=2))


if __name__ == "__main__":
    main()
