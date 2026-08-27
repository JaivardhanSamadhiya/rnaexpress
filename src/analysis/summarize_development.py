"""Create auditable development summaries before the internal lock is opened."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.metrics import bootstrap_parent_differences


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results/internal"
METRICS = RESULTS / "development_parent_direction_metrics.csv"
MACRO = RESULTS / "development_macro_metrics.csv"
RELIABILITY = ROOT / "reports/assay_reliability.json"
OUT_BOOT = RESULTS / "development_parent_bootstrap.csv"
OUT_PARENT = RESULTS / "development_per_parent_comparison.csv"
OUT_REPORT = ROOT / "reports/development_results.md"


def fmt(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    metrics = pd.read_csv(METRICS)
    macro = pd.read_csv(MACRO)
    reliability = json.loads(RELIABILITY.read_text())
    selected = "pairwise_rank"
    comparisons = ["retrieval", "forward_extratrees", "substitution_mean", "nzip_mikl_joint"]
    bootstrap: list[dict[str, object]] = []
    bootstrap_metrics = [
        "rank_percentile",
        "normalized_regret",
        "success_at_1",
        "success_at_3",
        "success_at_5",
        "spearman",
    ]
    for baseline in comparisons:
        bootstrap.extend(
            bootstrap_parent_differences(
                metrics, selected, baseline, bootstrap_metrics, draws=10000
            )
        )
    pd.DataFrame(bootstrap).to_csv(OUT_BOOT, index=False)

    parent = metrics.groupby(["model", "parent_id"], as_index=False)[
        [
            "rank_percentile",
            "normalized_regret",
            "success_at_1",
            "success_at_3",
            "success_at_5",
            "spearman",
        ]
    ].mean()
    selected_parent = parent[parent["model"] == selected].drop(columns="model")
    retrieval_parent = parent[parent["model"] == "retrieval"].drop(columns="model")
    comparison = selected_parent.merge(
        retrieval_parent, on="parent_id", suffixes=("_pairwise", "_retrieval")
    )
    comparison["rank_percentile_gain"] = (
        comparison["rank_percentile_pairwise"] - comparison["rank_percentile_retrieval"]
    )
    comparison.to_csv(OUT_PARENT, index=False)

    lookup = macro.set_index("model")
    pairwise = lookup.loc[selected]
    retrieval_row = lookup.loc["retrieval"]
    forward = lookup.loc["forward_extratrees"]
    mikl_only = lookup.loc["mikl_only"]
    mikl_joint = lookup.loc["nzip_mikl_joint"]
    mikl_prior = lookup.loc["intervention_plus_mikl_prior"]
    intervention = lookup.loc["intervention_extratrees"]
    positive = int((comparison["rank_percentile_gain"] > 1e-12).sum())
    negative = int((comparison["rank_percentile_gain"] < -1e-12).sum())
    tied = len(comparison) - positive - negative

    boot = pd.DataFrame(bootstrap)
    rank_vs_retrieval = boot[
        (boot["baseline_model"] == "retrieval") & (boot["metric"] == "rank_percentile")
    ].iloc[0]
    rank_vs_forward = boot[
        (boot["baseline_model"] == "forward_extratrees")
        & (boot["metric"] == "rank_percentile")
    ].iloc[0]

    text = f"""# RNAddress development results

Generated before the three locked N-zip parents were opened. Astrocyte outcomes remain sealed.

## Assay reliability and target definition

The 12 development parents contain 3,540 SNVs. The preregistered binary threshold resolved to **{reliability['policy']['binary_success_threshold_log2']:.3f} log2 localization units**. Only {reliability['nzip_development']['fraction_effectively_null']:.1%} of SNVs are within that threshold, {reliability['nzip_development']['fraction_beneficial_increase']:.1%} exceed it in the increase direction, and {reliability['nzip_development']['fraction_beneficial_decrease']:.1%} exceed it in the decrease direction. Effects are strongly asymmetric, so rank percentile and regret remain primary.

WT-versus-shScramble negative-control agreement is modest (Spearman {reliability['nzip_development']['wt_vs_shscramble_agreement']['spearman']:.3f}; MAE {reliability['nzip_development']['wt_vs_shscramble_agreement']['mae']:.3f}). This is not a true technical replicate and does not justify a hard statistical noise ceiling.

## Outer leave-one-parent-out results

| Method | Rank percentile | Normalized regret | Spearman | Success@1 | Success@3 | Success@5 |
|---|---:|---:|---:|---:|---:|---:|
"""
    for _, row in macro.iterrows():
        text += (
            f"| {row['model']} | {fmt(row['rank_percentile'])} | "
            f"{fmt(row['normalized_regret'])} | {fmt(row['spearman'])} | "
            f"{fmt(row['success_at_1'])} | {fmt(row['success_at_3'])} | "
            f"{fmt(row['success_at_5'])} |\n"
        )
    text += f"""

Pairwise ranking is selected because its macro rank percentile is **{pairwise['rank_percentile']:.3f}**, versus {retrieval_row['rank_percentile']:.3f} for retrieval and {forward['rank_percentile']:.3f} for forward-model exhaustive search. Its normalized regret is {pairwise['normalized_regret']:.3f}, versus {retrieval_row['normalized_regret']:.3f} and {forward['normalized_regret']:.3f} respectively.

The pairwise-minus-retrieval rank-percentile gain is {rank_vs_retrieval['mean_difference']:.3f}, with parent-bootstrap 95% CI [{rank_vs_retrieval['ci95_low']:.3f}, {rank_vs_retrieval['ci95_high']:.3f}]. Versus forward search, the gain is {rank_vs_forward['mean_difference']:.3f}, CI [{rank_vs_forward['ci95_low']:.3f}, {rank_vs_forward['ci95_high']:.3f}]. These intervals cross zero: the development advantage is promising but not confirmatory.

Pairwise ranking beats retrieval on {positive} parents, loses on {negative}, and ties on {tied}. The gain is not restricted to one or two parents, but heterogeneity is substantial. Binary Success@3 is {pairwise['success_at_3']:.3f}, slightly below retrieval's {retrieval_row['success_at_3']:.3f}; continuous ranking, not thresholded success, drives selection as preregistered.

## Mikl ablation

- Mikl-only transfer: rank percentile {mikl_only['rank_percentile']:.3f}; below random expectation 0.5.
- Joint N-zip+Mikl training: {mikl_joint['rank_percentile']:.3f}; useful signal, but below pairwise N-zip ranking.
- N-zip intervention forest alone: {intervention['rank_percentile']:.3f}.
- The same forest with a Mikl prior: {mikl_prior['rank_percentile']:.3f}; no benefit.

Mikl therefore does not enter the selected primary model. Its multi-base intervention distribution is not treated as homogeneous with N-zip SNVs.

## Development verdict

**PROMISING, NOT YET CONFIRMED.** Pairwise intervention ranking clears random and simple substitution baselines and improves the primary metric over retrieval and strong forward search. Parent-bootstrap uncertainty remains wide, and thresholded Success@K does not dominate retrieval. The frozen three-parent N-zip result is required before authorizing external reveal.

All runtime-driven deviations are disclosed in `reports/preregistration_deviations.md`. No hyperparameter was selected from aggregate performance; fixed grid-center configurations were used for all outer folds.
"""
    OUT_REPORT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
