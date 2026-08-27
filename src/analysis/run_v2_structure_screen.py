"""Outcome-safe fixed-center screen of the preregistered structure ranker."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.v2_features import build_v2_features
from src.modeling.v2_structure import build_structure_augmented_features
from src.modeling.v2_models import fit_factorized_context_ranker


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
CACHE = ROOT / "data" / "interim" / "modeling" / "viennarna_sequence_cache.json"
OUT = ROOT / "results" / "v2" / "nzip_structure_screen_predictions.csv.gz"
METRICS = ROOT / "results" / "v2" / "nzip_structure_screen_metrics.csv"
MACRO = ROOT / "results" / "v2" / "nzip_structure_screen_macro.csv"
THRESHOLD = 0.6758642587586807


def main() -> None:
    frame = pd.read_csv(SOURCE)
    features = build_structure_augmented_features(frame, build_v2_features(frame), CACHE)
    frame["pred_factorized_context_structure"] = np.nan
    for fold, parent_id in enumerate(sorted(frame["parent_id"].unique()), start=1):
        test = frame.index[frame["parent_id"] == parent_id].to_numpy(int)
        train = frame.index[frame["parent_id"] != parent_id].to_numpy(int)
        frame.loc[test, "pred_factorized_context_structure"] = fit_factorized_context_ranker(
            train, test, frame, features
        )
        print(f"completed structure outer fold {fold}/15: {parent_id}", flush=True)
    metrics = evaluate_predictions(
        frame,
        {
            "factorized_context_structure": "pred_factorized_context_structure",
            "factorized_context_sequence": "pred_factorized_context_ranker",
            "forward_lightgbm": "pred_forward_lightgbm",
            "metadata_only": "pred_metadata_only",
        },
        THRESHOLD,
    )
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    frame.to_csv(OUT, index=False, compression="gzip")
    metrics.to_csv(METRICS, index=False)
    macro.to_csv(MACRO, index=False)
    print(macro[["model", "rank_percentile", "normalized_regret", "spearman"]].to_string(index=False))


if __name__ == "__main__":
    main()
