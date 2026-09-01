"""Run the frozen RNAddress v4 transfer and edit-budget evaluations.

All target outcomes are used only after a target regime has been held out from
fitting.  Source-transfer predictions always use the shared global head.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_v4_phaseB_models import ROWS, feature_blocks
from src.modeling.v4_decision_models import (
    decision_set_metrics,
    fit_dfl,
    fit_pairwise,
    fit_predict_then_rank,
    normalized_utility,
    source_set_weights,
)


OUT = ROOT / "results" / "v4_phaseB"
SEED = 17
GZIP_OPTIONS = {"method": "gzip", "mtime": 0}


@dataclass(frozen=True)
class Scenario:
    family: str
    name: str
    train: np.ndarray
    test: np.ndarray


def _valid_training(rows: pd.DataFrame, mask: np.ndarray) -> np.ndarray:
    subset = rows.loc[mask]
    counts = subset.groupby("decision_set_id")["candidate_id"].transform("size")
    ranges = subset.groupby("decision_set_id")["localization_effect"].transform(
        lambda value: value.max() - value.min()
    )
    valid = counts.ge(2) & ranges.gt(0)
    output = np.zeros(len(rows), dtype=bool)
    output[subset.index.to_numpy()] = valid.to_numpy()
    return output


def _valid_test(rows: pd.DataFrame, mask: np.ndarray) -> np.ndarray:
    subset = rows.loc[mask]
    counts = subset.groupby("decision_set_id")["candidate_id"].transform("size")
    ranges = subset.groupby("decision_set_id")["localization_effect"].transform(
        lambda value: value.max() - value.min()
    )
    valid = counts.ge(5) & ranges.gt(0)
    output = np.zeros(len(rows), dtype=bool)
    output[subset.index.to_numpy()] = valid.to_numpy()
    return output


def _edit_band(cost: pd.Series) -> pd.Series:
    return pd.cut(
        cost,
        bins=[0, 1, 5, 10, 25, 50, np.inf],
        labels=["1", "2-5", "6-10", "11-25", "26-50", ">50"],
        include_lowest=True,
        right=True,
    ).astype(str)


def scenarios(rows: pd.DataFrame) -> list[Scenario]:
    result: list[Scenario] = []
    datasets = sorted(rows["dataset"].unique())
    for held in datasets:
        result.append(
            Scenario(
                "leave_source_out",
                f"leave_{held}_out",
                rows["dataset"].ne(held).to_numpy(),
                rows["dataset"].eq(held).to_numpy(),
            )
        )

    mikl = rows["dataset"].eq("mikl_gse173098")
    for train_cell, test_cell in (("CAD", "Neuro-2a"), ("Neuro-2a", "CAD")):
        result.append(
            Scenario(
                "cell_transfer",
                f"{train_cell}_to_{test_cell}",
                (mikl & rows["cell_type"].eq(train_cell)).to_numpy(),
                (mikl & rows["cell_type"].eq(test_cell)).to_numpy(),
            )
        )

    moffatt = rows["dataset"].eq("moffatt_gse334718")
    paired_units = set(
        rows.loc[moffatt]
        .groupby("biological_unit")["reporter"]
        .nunique()
        .loc[lambda value: value >= 2]
        .index
    )
    paired = moffatt & rows["biological_unit"].isin(paired_units)
    for train_reporter, test_reporter in (("Firefly", "GFP"), ("GFP", "Firefly")):
        result.append(
            Scenario(
                "reporter_transfer",
                f"{train_reporter}_to_{test_reporter}",
                (paired & rows["reporter"].eq(train_reporter)).to_numpy(),
                (paired & rows["reporter"].eq(test_reporter)).to_numpy(),
            )
        )

    for operation in sorted(rows["intervention_class"].unique()):
        result.append(
            Scenario(
                "leave_operation_out",
                f"leave_{operation}_out",
                rows["intervention_class"].ne(operation).to_numpy(),
                rows["intervention_class"].eq(operation).to_numpy(),
            )
        )

    for tier in (
        "small_local_edit",
        "motif_scale_edit",
        "regional_edit",
        "large_element_edit",
    ):
        result.append(
            Scenario(
                "leave_edit_tier_out",
                f"leave_{tier}_out",
                rows["edit_tier"].ne(tier).to_numpy(),
                rows["edit_tier"].eq(tier).to_numpy(),
            )
        )

    bands = _edit_band(rows["edit_cost"])
    for band in ("1", "2-5", "6-10", "11-25", "26-50", ">50"):
        result.append(
            Scenario(
                "edit_band_holdout",
                f"leave_edit_{band}_out",
                bands.ne(band).to_numpy(),
                bands.eq(band).to_numpy(),
            )
        )
    for maximum in (5, 10):
        result.append(
            Scenario(
                "small_edit_bridge",
                f"train_excluding_1-{maximum}_test_1-{maximum}",
                rows["edit_cost"].gt(maximum).to_numpy(),
                rows["edit_cost"].le(maximum).to_numpy(),
            )
        )
    return result


def _fit(kind: str, features: np.ndarray, rows: pd.DataFrame, sign: int):
    if kind == "ptr":
        return fit_predict_then_rank(features, rows, sign)
    if kind == "pairwise":
        return fit_pairwise(features, rows, sign, SEED)
    if kind == "dfl":
        return fit_dfl(features, rows, sign, SEED)
    raise ValueError(kind)


def _ridge_score(
    train_features: np.ndarray,
    train_rows: pd.DataFrame,
    test_features: np.ndarray,
    sign: int,
) -> np.ndarray:
    scaler = StandardScaler().fit(train_features)
    model = Ridge(alpha=100.0)
    model.fit(
        scaler.transform(train_features),
        normalized_utility(train_rows, sign),
        sample_weight=source_set_weights(train_rows),
    )
    return model.predict(scaler.transform(test_features))


def _random_exact(template: pd.DataFrame) -> pd.DataFrame:
    result = template.copy()
    result["model"] = "random_exact"
    result["directional_rank_percentile"] = 0.5
    result["normalized_regret"] = result["random_expected_regret"]
    result["selected_normalized_utility"] = 1.0 - result["random_expected_regret"]
    result["selected_experimental_utility"] = np.nan
    for k in (1, 3, 5):
        result[f"good_selection_at_{k}"] = result[f"random_good_selection_at_{k}"]
    result["oracle_recovered"] = 1.0 / result["candidate_count"]
    result["spearman"] = 0.0
    return result


def _aggregate(set_metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    unit = (
        set_metrics.groupby(
            ["scenario_family", "scenario", "model", "requested_direction", "dataset", "biological_unit"]
        )
        .agg(
            decision_sets=("decision_set_id", "size"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            selected_normalized_utility=("selected_normalized_utility", "mean"),
            selected_experimental_utility=("selected_experimental_utility", "mean"),
            good_selection_at_1=("good_selection_at_1", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
            good_selection_at_5=("good_selection_at_5", "mean"),
            oracle_recovered=("oracle_recovered", "mean"),
            random_expected_regret=("random_expected_regret", "mean"),
            spearman=("spearman", "mean"),
        )
        .reset_index()
    )
    aggregate = (
        unit.groupby(["scenario_family", "scenario", "model", "requested_direction", "dataset"])
        .agg(
            biological_units=("biological_unit", "size"),
            decision_sets=("decision_sets", "sum"),
            directional_rank_percentile=("directional_rank_percentile", "mean"),
            normalized_regret=("normalized_regret", "mean"),
            selected_normalized_utility=("selected_normalized_utility", "mean"),
            selected_experimental_utility=("selected_experimental_utility", "mean"),
            good_selection_at_1=("good_selection_at_1", "mean"),
            good_selection_at_3=("good_selection_at_3", "mean"),
            good_selection_at_5=("good_selection_at_5", "mean"),
            oracle_recovered=("oracle_recovered", "mean"),
            random_expected_regret=("random_expected_regret", "mean"),
            spearman=("spearman", "mean"),
        )
        .reset_index()
    )
    return unit, aggregate


def main() -> None:
    rows = pd.read_csv(ROWS)
    blocks = feature_blocks(rows)
    primary = blocks["parent_plus_delta"]
    selected_kind = json.loads((OUT / "model_selection.json").read_text(encoding="utf-8"))[
        "selected_model_kind"
    ]
    model_kinds = ["ptr"] if selected_kind == "ptr" else ["ptr", selected_kind]
    all_metrics: list[pd.DataFrame] = []
    audit: list[dict[str, object]] = []
    for number, scenario in enumerate(scenarios(rows), start=1):
        train_mask = _valid_training(rows, scenario.train)
        test_mask = _valid_test(rows, scenario.test)
        train_rows = rows.loc[train_mask].reset_index(drop=True)
        test_rows = rows.loc[test_mask].reset_index(drop=True)
        if len(train_rows) == 0 or len(test_rows) == 0:
            audit.append(
                {
                    "scenario_family": scenario.family,
                    "scenario": scenario.name,
                    "status": "descriptive_only_no_eligible_candidate_set",
                    "raw_train_rows": int(scenario.train.sum()),
                    "raw_test_rows": int(scenario.test.sum()),
                }
            )
            continue
        train_features = primary[train_mask]
        test_features = primary[test_mask]
        for sign, direction in ((1, "increase"), (-1, "decrease")):
            template = None
            for kind in model_kinds:
                model = _fit(kind, train_features, train_rows, sign)
                score = model.predict(test_features, test_rows["assay_context"], use_residual=False)
                metric = decision_set_metrics(
                    test_rows, score, f"{kind}_global", direction, SEED, scenario.name
                )
                template = metric
                metric["scenario_family"] = scenario.family
                metric["scenario"] = scenario.name
                all_metrics.append(metric)
            metadata_score = _ridge_score(
                blocks["metadata_only"][train_mask],
                train_rows,
                blocks["metadata_only"][test_mask],
                sign,
            )
            metric = decision_set_metrics(
                test_rows, metadata_score, "metadata_ridge", direction, SEED, scenario.name
            )
            metric["scenario_family"] = scenario.family
            metric["scenario"] = scenario.name
            all_metrics.append(metric)
            size_metric = decision_set_metrics(
                test_rows,
                test_rows["edit_cost"].to_numpy(float),
                "edit_size_heuristic",
                direction,
                SEED,
                scenario.name,
            )
            size_metric["scenario_family"] = scenario.family
            size_metric["scenario"] = scenario.name
            all_metrics.append(size_metric)
            random_metric = _random_exact(template)
            random_metric["scenario_family"] = scenario.family
            random_metric["scenario"] = scenario.name
            all_metrics.append(random_metric)
        audit.append(
            {
                "scenario_family": scenario.family,
                "scenario": scenario.name,
                "status": "evaluated",
                "train_rows": len(train_rows),
                "train_decision_sets": int(train_rows["decision_set_id"].nunique()),
                "train_biological_units": int(train_rows["biological_unit"].nunique()),
                "test_rows": len(test_rows),
                "test_decision_sets": int(test_rows["decision_set_id"].nunique()),
                "test_biological_units": int(test_rows["biological_unit"].nunique()),
            }
        )
        print(f"completed transfer scenario {number}: {scenario.family}/{scenario.name}", flush=True)

    set_metrics = pd.concat(all_metrics, ignore_index=True)
    set_metrics.to_csv(OUT / "transfer_set_metrics.csv.gz", index=False, compression=GZIP_OPTIONS)
    unit, aggregate = _aggregate(set_metrics)
    unit.to_csv(OUT / "transfer_biological_unit_metrics.csv", index=False)
    aggregate.to_csv(OUT / "transfer_aggregate_metrics.csv", index=False)
    (OUT / "transfer_scenario_audit.json").write_text(
        json.dumps(
            {
                "selected_model_kind": selected_kind,
                "seed": SEED,
                "target_residual_used": False,
                "scenarios": audit,
                "scope_guards": {"nzip_outcomes_used": False, "astrocyte_outcomes_opened": False},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
