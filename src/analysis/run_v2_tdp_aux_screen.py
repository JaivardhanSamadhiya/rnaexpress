"""Screen TDP-43-development multitask context pretraining on N-zip LOPO."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.v2_features import build_v2_features
from src.modeling.v2_models import fit_factorized_context_with_tdp_auxiliary


ROOT = Path(__file__).resolve().parents[2]
NZIP = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
TDP_DEV = ROOT / "data" / "processed" / "tdp43_v2_development_pairs.csv.gz"
OUT = ROOT / "results" / "v2" / "nzip_tdp_aux_screen_predictions.csv.gz"
METRICS = ROOT / "results" / "v2" / "nzip_tdp_aux_screen_metrics.csv"
MACRO = ROOT / "results" / "v2" / "nzip_tdp_aux_screen_macro.csv"
THRESHOLD = 0.6758642587586807


def main() -> None:
    frame = pd.read_csv(NZIP)
    auxiliary = pd.read_csv(TDP_DEV)
    if auxiliary["gene_id"].nunique() != 12 or len(auxiliary) != 3_560:
        raise ValueError("TDP-43 development boundary changed")
    nzip_features = build_v2_features(frame)
    auxiliary_features = build_v2_features(auxiliary)
    frame["pred_factorized_context_tdp_aux"] = np.nan
    for fold, parent_id in enumerate(sorted(frame["parent_id"].unique()), start=1):
        test = frame.index[frame["parent_id"] == parent_id].to_numpy(int)
        train = frame.index[frame["parent_id"] != parent_id].to_numpy(int)
        frame.loc[test, "pred_factorized_context_tdp_aux"] = (
            fit_factorized_context_with_tdp_auxiliary(
                train,
                test,
                frame,
                nzip_features,
                auxiliary,
                auxiliary_features,
            )
        )
        print(f"completed TDP-aux outer fold {fold}/15: {parent_id}", flush=True)
    metrics = evaluate_predictions(
        frame,
        {
            "factorized_context_tdp_aux": "pred_factorized_context_tdp_aux",
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
