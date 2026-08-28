"""Evaluate the committed TDP-43 v2 lock without changing frozen predictions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.modeling.metrics import rank_percentile


ROOT = Path(__file__).resolve().parents[2]
PREDICTIONS = ROOT / "results" / "v2_tdp43_lock" / "tdp43_v2_frozen_predictions.csv.gz"
FREEZE_MANIFEST = ROOT / "results" / "v2_tdp43_lock" / "tdp43_v2_prediction_freeze_manifest.json"
OUTCOMES = ROOT / "data" / "frozen" / "outcomes" / "tdp43_v2_locked_outcomes.csv.gz"
OUT_DIR = ROOT / "results" / "v2_tdp43_lock"
OUT_JOINED = OUT_DIR / "tdp43_v2_revealed_predictions.csv.gz"
OUT_METRICS = OUT_DIR / "tdp43_v2_lock_gene_direction_metrics.csv"
OUT_MACRO = OUT_DIR / "tdp43_v2_lock_macro.csv"
OUT_GATE = OUT_DIR / "tdp43_v2_lock_gate.json"
CUSTOM = "nested_context_external_stack"
MODELS = {
    CUSTOM: "pred_nested_context_external_stack",
    "forward_lightgbm": "pred_forward_lightgbm",
    "motif_accessibility_ridge": "pred_motif_accessibility_ridge",
}
OUTCOME_KEY = ["parent_id", "mutant_id"]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(frame: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for (gene_id, gene_name), gene in frame.groupby(["gene_id", "gene_name"], sort=True):
        measured = gene["delta_localization"].to_numpy(float)
        for model, column in MODELS.items():
            predicted = gene[column].to_numpy(float)
            rho = float(spearmanr(predicted, measured).statistic)
            if not np.isfinite(rho):
                rho = 0.0
            for direction, sign in (("increase", 1.0), ("decrease", -1.0)):
                measured_utility = sign * measured
                predicted_utility = sign * predicted
                selected = int(np.argmax(predicted_utility))
                best = float(np.max(measured_utility))
                worst = float(np.min(measured_utility))
                selected_utility = float(measured_utility[selected])
                regret = best - selected_utility
                records.append(
                    {
                        "model": model,
                        "gene_id": gene_id,
                        "gene_name": gene_name,
                        "direction": direction,
                        "n_candidates": len(gene),
                        "selected_parent_id": str(gene.iloc[selected]["parent_id"]),
                        "selected_mutant_id": str(gene.iloc[selected]["mutant_id"]),
                        "measured_effect": float(measured[selected]),
                        "measured_utility": selected_utility,
                        "best_measured_utility": best,
                        "regret": regret,
                        "normalized_regret": regret / (best - worst) if best > worst else 0.0,
                        "rank_percentile": rank_percentile(measured_utility, selected),
                        "spearman": rho,
                        "random_expected_rank_percentile": 0.5,
                    }
                )
    return pd.DataFrame.from_records(records)


def main() -> None:
    freeze = json.loads(FREEZE_MANIFEST.read_text())
    if file_sha256(PREDICTIONS) != freeze["artifact_sha256"][
        "results\\v2_tdp43_lock\\tdp43_v2_frozen_predictions.csv.gz"
    ]:
        raise ValueError("Committed TDP-43 prediction artifact hash changed")
    if file_sha256(OUTCOMES) != freeze["locked_outcomes_expected_sha256_unread"]:
        raise ValueError("TDP-43 locked outcome artifact hash changed")
    predictions = pd.read_csv(PREDICTIONS)
    outcomes = pd.read_csv(OUTCOMES)
    if len(predictions) != 1_006 or len(outcomes) != 1_006:
        raise ValueError("TDP-43 lock row count changed")
    frame = predictions.merge(
        outcomes, on=OUTCOME_KEY, how="inner", validate="one_to_one"
    )
    if len(frame) != 1_006 or frame["gene_id"].nunique() != 4:
        raise ValueError("TDP-43 prediction/outcome merge is incomplete")
    metrics = evaluate(frame)
    numeric = [
        "n_candidates",
        "measured_effect",
        "measured_utility",
        "best_measured_utility",
        "regret",
        "normalized_regret",
        "rank_percentile",
        "spearman",
        "random_expected_rank_percentile",
    ]
    by_gene = metrics.groupby(["model", "gene_id"], as_index=False)[numeric].mean()
    macro = by_gene.groupby("model", as_index=False)[numeric].mean()
    macro = macro.sort_values("rank_percentile", ascending=False)
    table = macro.set_index("model")
    comparators = ["forward_lightgbm", "motif_accessibility_ridge"]
    strongest = max(
        comparators, key=lambda model: float(table.loc[model, "rank_percentile"])
    )
    gene_rank = by_gene.pivot(index="gene_id", columns="model", values="rank_percentile")
    gain = gene_rank[CUSTOM] - gene_rank[strongest]
    custom_spearman = by_gene[by_gene["model"] == CUSTOM].set_index("gene_id")["spearman"]
    checks = {
        "macro_directional_rank_percentile_above_0_550": bool(
            table.loc[CUSTOM, "rank_percentile"] > 0.550
        ),
        "positive_gain_over_forward_lightgbm": bool(
            table.loc[CUSTOM, "rank_percentile"]
            > table.loc["forward_lightgbm", "rank_percentile"]
        ),
        "positive_gain_over_motif_accessibility_ridge": bool(
            table.loc[CUSTOM, "rank_percentile"]
            > table.loc["motif_accessibility_ridge", "rank_percentile"]
        ),
        "positive_spearman_in_at_least_3_of_4_genes": bool(
            (custom_spearman > 0).sum() >= 3
        ),
        "positive_gain_after_removing_most_favorable_gene": bool(
            gain.drop(gain.idxmax()).mean() > 0
        ),
    }
    gate = {
        "selected_custom": CUSTOM,
        "strongest_comparator": strongest,
        "gate_checks": checks,
        "tdp43_locked_gate_pass": bool(all(checks.values())),
        "custom_macro": {
            key: float(table.loc[CUSTOM, key])
            for key in ["rank_percentile", "normalized_regret", "spearman"]
        },
        "rank_percentile_gain": {
            comparator: float(
                table.loc[CUSTOM, "rank_percentile"]
                - table.loc[comparator, "rank_percentile"]
            )
            for comparator in comparators
        },
        "custom_within_gene_spearman": {
            str(gene): float(value) for gene, value in custom_spearman.items()
        },
        "custom_minus_strongest_rank_gain_by_gene": {
            str(gene): float(value) for gene, value in gain.items()
        },
        "astrocyte_reveal_authorized": bool(all(checks.values())),
    }
    frame.to_csv(OUT_JOINED, index=False, compression="gzip")
    metrics.to_csv(OUT_METRICS, index=False)
    macro.to_csv(OUT_MACRO, index=False)
    OUT_GATE.write_text(json.dumps(gate, indent=2) + "\n")
    print(macro[["model", "rank_percentile", "normalized_regret", "spearman"]].to_string(index=False))
    print(json.dumps(gate, indent=2), flush=True)


if __name__ == "__main__":
    main()
