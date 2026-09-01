"""Phase B uncertainty, auxiliary-label, SNV, and budget feasibility audits."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_v4_phaseB_models import ROWS, feature_blocks
from src.modeling.v4_decision_models import (
    decision_set_metrics,
    normalized_utility,
    source_set_weights,
)


OUT = ROOT / "results" / "v4_phaseB"
GZIP_OPTIONS = {"method": "gzip", "mtime": 0}


def _mikl_uncertainty(rows: pd.DataFrame, features: np.ndarray) -> dict[str, object]:
    mask = rows["dataset"].eq("mikl_gse173098").to_numpy()
    source = rows.loc[mask].reset_index(drop=True)
    x = features[mask]
    metrics = []
    for sign, direction in ((1, "increase"), (-1, "decrease")):
        scores = {
            "unweighted": np.full(len(source), np.nan),
            "inverse_variance": np.full(len(source), np.nan),
        }
        for fold in range(5):
            train = source["biological_fold"].ne(fold).to_numpy()
            test = ~train
            train_rows = source.loc[train].reset_index(drop=True)
            scaler = StandardScaler().fit(x[train])
            x_train = scaler.transform(x[train])
            target = normalized_utility(train_rows, sign)
            base_weight = source_set_weights(train_rows)
            uncertainty = train_rows["effect_uncertainty"].to_numpy(float)
            if not np.isfinite(uncertainty).all():
                raise ValueError("Mikl uncertainty sensitivity requires finite SE")
            inverse = 1.0 / (uncertainty**2 + 0.25**2)
            inverse /= np.median(inverse)
            inverse = np.clip(inverse, 0.1, 10.0)
            for name, weight in (
                ("unweighted", base_weight),
                ("inverse_variance", base_weight * inverse),
            ):
                model = Ridge(alpha=100.0)
                model.fit(x_train, target, sample_weight=weight)
                scores[name][test] = model.predict(scaler.transform(x[test]))
        for name, score in scores.items():
            metric = decision_set_metrics(
                source, score, f"mikl_{name}", direction, 17, "held_gene_uncertainty"
            )
            metric["weighting"] = name
            metrics.append(metric)
    set_metrics = pd.concat(metrics, ignore_index=True)
    set_metrics.to_csv(OUT / "uncertainty_set_metrics.csv", index=False)
    unit = (
        set_metrics.groupby(["weighting", "requested_direction", "biological_unit"])
        .agg(
            decision_sets=("decision_set_id", "size"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
        )
        .reset_index()
    )
    aggregate = (
        unit.groupby(["weighting", "requested_direction"])
        .agg(
            biological_units=("biological_unit", "size"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
        )
        .reset_index()
    )
    aggregate.to_csv(OUT / "uncertainty_aggregate_metrics.csv", index=False)
    wide = aggregate.pivot(index="requested_direction", columns="weighting")
    gains = []
    for direction in sorted(aggregate["requested_direction"].unique()):
        plain = aggregate[
            aggregate["requested_direction"].eq(direction)
            & aggregate["weighting"].eq("unweighted")
        ].iloc[0]
        weighted = aggregate[
            aggregate["requested_direction"].eq(direction)
            & aggregate["weighting"].eq("inverse_variance")
        ].iloc[0]
        gains.append(
            {
                "direction": direction,
                "rank_gain": float(
                    weighted["directional_rank_percentile"]
                    - plain["directional_rank_percentile"]
                ),
                "regret_gain": float(
                    plain["normalized_regret"] - weighted["normalized_regret"]
                ),
                "good3_gain": float(weighted["good_selection_at_3"] - plain["good_selection_at_3"]),
            }
        )
    return {
        "scope": "Mikl only",
        "method": "inverse 1/(SE^2+0.25^2), median normalized, clipped to [0.1,10]",
        "gains": gains,
        "retention_rule": "regret gain >=0.01 without worse transfer; sensitivity cannot select global model",
    }


def _exact_snv_descriptive(rows: pd.DataFrame) -> dict[str, object]:
    selection = json.loads((OUT / "model_selection.json").read_text(encoding="utf-8"))
    kind = selection["selected_model_kind"]
    archive = np.load(OUT / "outer_candidate_scores.npz")
    records = []
    exact = rows["edit_cost"].eq(1)
    for direction, sign in (("increase", 1), ("decrease", -1)):
        key = (
            f"ptr_hierarchical_{direction}"
            if kind == "ptr"
            else f"{kind}_hierarchical_{direction}_seed17"
        )
        scores = np.asarray(archive[key], dtype=float)
        for decision_id, indices in rows.groupby("decision_set_id", sort=True).indices.items():
            indices = np.asarray(indices, dtype=int)
            exact_indices = indices[exact.iloc[indices].to_numpy()]
            if len(exact_indices) == 0:
                continue
            true = rows.iloc[indices]["localization_effect"].to_numpy(float) * sign
            predicted = scores[indices]
            true_percentile = 1.0 - (rankdata(-true, method="average") - 1.0) / (len(indices) - 1.0)
            predicted_percentile = 1.0 - (
                rankdata(-predicted, method="average") - 1.0
            ) / (len(indices) - 1.0)
            local = {value: pos for pos, value in enumerate(indices)}
            for index in exact_indices:
                position = local[int(index)]
                records.append(
                    {
                        "direction": direction,
                        "dataset": rows.iloc[index]["dataset"],
                        "decision_set_id": decision_id,
                        "candidate_id": rows.iloc[index]["candidate_id"],
                        "mutant_id": rows.iloc[index]["mutant_id"],
                        "true_rank_percentile_within_full_set": true_percentile[position],
                        "predicted_rank_percentile_within_full_set": predicted_percentile[position],
                        "effect": rows.iloc[index]["localization_effect"],
                        "score": scores[index],
                    }
                )
    frame = pd.DataFrame(records)
    frame.to_csv(OUT / "exact_snv_descriptive.csv", index=False)
    aggregate = []
    for (dataset, direction), group in frame.groupby(["dataset", "direction"]):
        correlation = spearmanr(
            group["predicted_rank_percentile_within_full_set"],
            group["true_rank_percentile_within_full_set"],
        ).statistic
        aggregate.append(
            {
                "dataset": dataset,
                "direction": direction,
                "assay_rows": len(group),
                "unique_interventions": int(group["mutant_id"].nunique()),
                "rank_percentile_spearman": float(correlation) if np.isfinite(correlation) else None,
                "mean_absolute_rank_percentile_error": float(
                    np.mean(
                        np.abs(
                            group["predicted_rank_percentile_within_full_set"]
                            - group["true_rank_percentile_within_full_set"]
                        )
                    )
                ),
            }
        )
    return {
        "selection_gate_allowed": False,
        "reason": "19 distinct interventions and no exact-SNV-only decision set has >=5 candidates",
        "rows": aggregate,
    }


def _minimum_budget(rows: pd.DataFrame) -> dict[str, object]:
    records = []
    for direction, sign in (("increase", 1), ("decrease", -1)):
        for decision_id, group in rows.groupby("decision_set_id", sort=True):
            utility = group["localization_effect"].to_numpy(float) * sign
            normalized = (utility - utility.min()) / (utility.max() - utility.min())
            qualifying = group.iloc[np.flatnonzero(normalized >= 0.90)]
            records.append(
                {
                    "direction": direction,
                    "dataset": group["dataset"].iloc[0],
                    "decision_set_id": decision_id,
                    "biological_unit": group["biological_unit"].iloc[0],
                    "distinct_edit_costs": int(group["edit_cost"].nunique()),
                    "minimum_cost_for_regret_le_0_10": int(qualifying["edit_cost"].min()),
                }
            )
    frame = pd.DataFrame(records)
    frame.to_csv(OUT / "minimum_budget_feasibility.csv", index=False)
    return {
        "decision_direction_tasks": len(frame),
        "tasks_with_multiple_edit_costs": int(frame["distinct_edit_costs"].gt(1).sum()),
        "fraction_with_multiple_edit_costs": float(frame["distinct_edit_costs"].gt(1).mean()),
        "minimum_cost_distribution": {
            str(int(key)): int(value)
            for key, value in frame["minimum_cost_for_regret_le_0_10"].value_counts().sort_index().items()
        },
        "future_claim": "feasibility analysis only; no generative minimum-budget model was trained",
    }


def main() -> None:
    rows = pd.read_csv(ROWS)
    primary = feature_blocks(rows)["parent_plus_delta"]
    result = {
        "uncertainty": _mikl_uncertainty(rows, primary),
        "robust_dfl": {
            "implemented": False,
            "reason": "Mikl SE is valid, TDP pair-level uncertainty is absent, and Moffatt diagnostic raw-ratio SE is not author-effect uncertainty",
        },
        "stability_auxiliary": {
            "tested": False,
            "reason": "certified Mikl stability effects are all missing and TDP EV5 remains quarantined for duplicate keys",
        },
        "structural_auxiliary": {
            "tested": False,
            "reason": "Moffatt SHAPE is an intervention-design family, not a certified sequence-level structural target",
        },
        "exact_snv": _exact_snv_descriptive(rows),
        "minimum_budget": _minimum_budget(rows),
        "scope_guards": {"nzip_outcomes_used": False, "astrocyte_outcomes_opened": False},
    }
    (OUT / "auxiliary_analysis.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
