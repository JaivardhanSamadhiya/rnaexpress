"""Run v2 negative controls without accessing either locked dataset."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.metrics import evaluate_predictions, parent_macro
from src.modeling.v2_features import build_v2_features
from src.modeling.v2_models import fit_factorized_context_ranker


ROOT = Path(__file__).resolve().parents[2]
PREDICTIONS = ROOT / "results" / "v2" / "nzip_development_predictions.csv.gz"
METRICS = ROOT / "results" / "v2" / "nzip_hostile_control_metrics.csv"
SUMMARY = ROOT / "results" / "v2" / "nzip_hostile_control_summary.json"
THRESHOLD = 0.6758642587586807
SEED = 20260826


def main() -> None:
    frame = pd.read_csv(PREDICTIONS)
    features = build_v2_features(frame)
    shuffled = frame.copy()
    rng = np.random.default_rng(SEED)
    shuffled["delta_localization"] = shuffled.groupby("parent_id")[
        "delta_localization"
    ].transform(lambda values: rng.permutation(values.to_numpy()))
    frame["pred_shuffled_labels"] = np.nan
    for fold, parent_id in enumerate(sorted(frame["parent_id"].unique()), start=1):
        test = frame.index[frame["parent_id"] == parent_id].to_numpy(int)
        train = frame.index[frame["parent_id"] != parent_id].to_numpy(int)
        frame.loc[test, "pred_shuffled_labels"] = fit_factorized_context_ranker(
            train, test, shuffled, features
        )
        print(f"completed shuffled-label fold {fold}/15: {parent_id}", flush=True)
    metrics = evaluate_predictions(
        frame,
        {
            "factorized_context_ranker": "pred_factorized_context_ranker",
            "shuffled_labels": "pred_shuffled_labels",
            "shuffled_edit_identity": "pred_shuffled_edit_identity",
        },
        THRESHOLD,
    )
    macro = parent_macro(metrics).sort_values("rank_percentile", ascending=False)
    shuffled_rank = float(
        macro.set_index("model").loc["shuffled_labels", "rank_percentile"]
    )
    summary = {
        "shuffled_label_rank_percentile": shuffled_rank,
        "threshold": 0.530,
        "passes": bool(shuffled_rank <= 0.530),
    }
    metrics.to_csv(METRICS, index=False)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(macro[["model", "rank_percentile", "normalized_regret", "spearman"]].to_string(index=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
