"""Run the prospectively frozen RNAddress v4 Phase B2 evaluation.

Phase B2 asks only whether frozen parent/context representations predict
cross-fitted residual intervention effects beyond edit geometry.  It never
loads N-zip or Astrocyte paths and does not fine-tune the frozen encoder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.run_v4_phaseB_models import (
    ROWS,
    full_embedding_paths,
    selected_representation,
)
from src.modeling.v4_decision_models import decision_set_metrics, geometry_features
from src.modeling.v4_phaseB2_context import (
    ALPHAS,
    RANKS,
    SEED,
    ContextBlocks,
    add_matching_keys,
    assert_held_out,
    build_context_blocks,
    control_donor_indices,
    cross_fitted_nuisance,
    edit_band,
    fit_context,
    fit_nuisance,
    matched_pairs,
)


OUT = ROOT / "results" / "v4_phaseB2"
GZIP_OPTIONS = {"method": "gzip", "mtime": 0}
METRICS = (
    "directional_rank_percentile",
    "normalized_regret",
    "selected_normalized_utility",
    "good_selection_at_1",
    "good_selection_at_3",
    "good_selection_at_5",
    "oracle_recovered",
    "spearman",
)


@dataclass(frozen=True)
class ModelOption:
    family: str
    alpha: float
    rank: int = 0
    nuisance_level: str = "global"
    contrastive: bool = False
    group_robust: bool = False

    @property
    def name(self) -> str:
        return (
            f"{self.family}_a{int(self.alpha)}_r{self.rank}_"
            f"{self.nuisance_level}"
        )


def _options() -> list[ModelOption]:
    result = [ModelOption("M1", alpha) for alpha in ALPHAS]
    for family in ("M2", "M3"):
        for rank in RANKS:
            for alpha in ALPHAS:
                result.append(
                    ModelOption(
                        family,
                        alpha,
                        rank,
                        contrastive=family == "M3",
                    )
                )
    return result


def _subset_blocks(blocks: ContextBlocks, mask: np.ndarray) -> ContextBlocks:
    return ContextBlocks(**{field: getattr(blocks, field)[mask] for field in blocks.__dataclass_fields__})


def _load() -> tuple[pd.DataFrame, np.ndarray, ContextBlocks, dict[str, object]]:
    rows = pd.read_csv(ROWS)
    if set(rows["dataset"].unique()) != {
        "mikl_gse173098",
        "tdp43_gse288185",
        "moffatt_gse334718",
    }:
        raise ValueError("Phase B2 received an uncertified development source")
    model_name = selected_representation()
    feature_path, metadata_path = full_embedding_paths(model_name)
    embedded = np.load(feature_path, mmap_mode="r")
    mapped = np.asarray(embedded[rows["feature_row"].to_numpy(int)], dtype=np.float32)
    parent = mapped[:, :128]
    delta = mapped[:, 256:384]
    geometry = geometry_features(rows, categories=True)
    blocks = build_context_blocks(parent, delta, rows)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return rows, geometry, blocks, metadata


def _valid_eval(frame: pd.DataFrame, minimum: int = 5) -> np.ndarray:
    counts = frame.groupby("decision_set_id")["candidate_id"].transform("size")
    ranges = frame.groupby("decision_set_id")["localization_effect"].transform(
        lambda values: values.max() - values.min()
    )
    return counts.ge(minimum).to_numpy() & ranges.gt(0).to_numpy()


def _append_metrics(
    records: list[pd.DataFrame],
    frame: pd.DataFrame,
    score: np.ndarray,
    name: str,
    direction: str,
    evaluation: str,
) -> pd.DataFrame:
    metric = decision_set_metrics(frame, score, name, direction, SEED, evaluation)
    records.append(metric)
    return metric


def _context_value(
    frame: pd.DataFrame,
    full_score: np.ndarray,
    nuisance_score: np.ndarray,
    direction: str,
) -> dict[str, float]:
    full = decision_set_metrics(frame, full_score, "full", direction, SEED, "inner")
    nuisance = decision_set_metrics(frame, nuisance_score, "nuisance", direction, SEED, "inner")
    paired = full.merge(
        nuisance,
        on=["dataset", "decision_set_id", "biological_unit", "requested_direction"],
        suffixes=("_full", "_nuisance"),
        validate="one_to_one",
    )
    paired["rank_cv"] = (
        paired["directional_rank_percentile_full"]
        - paired["directional_rank_percentile_nuisance"]
    )
    paired["regret_cv"] = paired["normalized_regret_nuisance"] - paired["normalized_regret_full"]
    paired["good3_cv"] = paired["good_selection_at_3_full"] - paired["good_selection_at_3_nuisance"]
    units = (
        paired.groupby(["dataset", "biological_unit"])[["rank_cv", "regret_cv", "good3_cv"]]
        .mean()
        .reset_index()
    )
    sources = units.groupby("dataset")[["rank_cv", "regret_cv", "good3_cv"]].mean()
    return {column: float(sources[column].mean()) for column in ("rank_cv", "regret_cv", "good3_cv")}


def _option_features(blocks: ContextBlocks, option: ModelOption) -> tuple[np.ndarray, slice | None]:
    family = "M2" if option.family == "M4" and not option.contrastive else option.family
    if option.family == "M4":
        family = "M3" if option.contrastive else "M2"
    return blocks.features(family, option.rank)


def _pairs_for(frame: pd.DataFrame, option: ModelOption) -> tuple[np.ndarray, np.ndarray] | None:
    if not option.contrastive:
        return None
    cross, within, _ = matched_pairs(frame)
    return cross, within


def _select_record(records: list[dict[str, object]]) -> dict[str, object]:
    best_regret = max(float(record["regret_cv"]) for record in records)
    near = [record for record in records if float(record["regret_cv"]) >= best_regret - 0.002]
    complexity = {"M1": 1, "M2": 2, "M3": 3, "M4": 4}
    near.sort(
        key=lambda record: (
            complexity[str(record["family"])],
            int(record["rank"]),
            -float(record["alpha"]),
            -float(record["rank_cv"]),
            -float(record["good3_cv"]),
            str(record["nuisance_level"]),
        )
    )
    return near[0]


def _inner_select(
    frame: pd.DataFrame,
    geometry: np.ndarray,
    blocks: ContextBlocks,
    direction: str,
) -> tuple[ModelOption, list[dict[str, object]], dict[str, np.ndarray], list[pd.DataFrame]]:
    sign = 1 if direction == "increase" else -1
    nuisance_predictions: dict[str, np.ndarray] = {}
    nuisance_audits: list[pd.DataFrame] = []
    for level in ("global", "source"):
        prediction, audit = cross_fitted_nuisance(
            geometry,
            frame,
            source_specific=level == "source",
        )
        nuisance_predictions[level] = prediction
        audit["nuisance_level"] = level
        nuisance_audits.append(audit)

    option_predictions: dict[str, np.ndarray] = {}
    option_lookup: dict[str, ModelOption] = {}
    fold_values = frame["biological_fold"].to_numpy()
    for level in ("global", "source"):
        residual = frame["localization_effect"].to_numpy(float) - nuisance_predictions[level]
        for raw_option in _options():
            option = replace(raw_option, nuisance_level=level)
            option_lookup[option.name] = option
            features, interaction_slice = _option_features(blocks, option)
            predictions = np.full(len(frame), np.nan, dtype=float)
            for fold in sorted(pd.unique(fold_values)):
                validation = fold_values == fold
                training = ~validation
                train_rows = frame.loc[training].reset_index(drop=True)
                pairs = _pairs_for(train_rows, option)
                model = fit_context(
                    features[training],
                    residual[training],
                    train_rows,
                    option.family,
                    option.rank,
                    option.alpha,
                    interaction_slice,
                    pairs=pairs,
                )
                assert_held_out(train_rows, frame.loc[validation], "biological_unit")
                predictions[validation] = model.predict(features[validation])
            option_predictions[option.name] = predictions

    records: list[dict[str, object]] = []
    for name, prediction in option_predictions.items():
        option = option_lookup[name]
        values = _context_value(
            frame,
            sign * (nuisance_predictions[option.nuisance_level] + prediction),
            sign * nuisance_predictions[option.nuisance_level],
            direction,
        )
        records.append({**asdict(option), "name": name, **values})

    # M4 is a single conditional refit based on the best genuine interaction
    # candidate, exactly as frozen.  It does not open another hyperparameter grid.
    interaction_records = [record for record in records if record["family"] in {"M2", "M3"}]
    interaction_best = _select_record(interaction_records)
    if float(interaction_best["rank_cv"]) > 0 and float(interaction_best["regret_cv"]) >= 0.005:
        base = option_lookup[str(interaction_best["name"])]
        robust = replace(base, family="M4", group_robust=True)
        features, interaction_slice = _option_features(blocks, robust)
        residual = frame["localization_effect"].to_numpy(float) - nuisance_predictions[robust.nuisance_level]
        predictions = np.full(len(frame), np.nan, dtype=float)
        for fold in sorted(pd.unique(fold_values)):
            validation = fold_values == fold
            training = ~validation
            train_rows = frame.loc[training].reset_index(drop=True)
            pairs = _pairs_for(train_rows, robust)
            model = fit_context(
                features[training],
                residual[training],
                train_rows,
                robust.family,
                robust.rank,
                robust.alpha,
                interaction_slice,
                pairs=pairs,
                group_robust=True,
            )
            predictions[validation] = model.predict(features[validation])
        values = _context_value(
            frame,
            sign * (nuisance_predictions[robust.nuisance_level] + predictions),
            sign * nuisance_predictions[robust.nuisance_level],
            direction,
        )
        records.append({**asdict(robust), "name": robust.name, **values})
        option_lookup[robust.name] = robust

    selected_record = _select_record(records)
    selected = option_lookup[str(selected_record["name"])]
    return selected, records, nuisance_predictions, nuisance_audits


def _aggregate(set_metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = ["model", "evaluation", "dataset", "requested_direction", "biological_unit"]
    unit = (
        set_metrics.groupby(keys)
        .agg(decision_sets=("decision_set_id", "size"), **{metric: (metric, "mean") for metric in METRICS})
        .reset_index()
    )
    aggregate = (
        unit.groupby(["model", "evaluation", "dataset", "requested_direction"])
        .agg(
            biological_units=("biological_unit", "size"),
            decision_sets=("decision_sets", "sum"),
            **{metric: (metric, "mean") for metric in METRICS},
        )
        .reset_index()
    )
    return unit, aggregate


def evaluate_primary() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, geometry, blocks, embedding_metadata = _load()
    keyed = add_matching_keys(rows)
    cross_pairs, within_pairs, matched_audit = matched_pairs(rows)
    matched_audit.to_csv(OUT / "matched_strata_audit.csv.gz", index=False, compression=GZIP_OPTIONS)
    fold_values = rows["biological_fold"].to_numpy()
    predictions_by_direction: dict[str, dict[str, np.ndarray]] = {}
    selection_records: list[dict[str, object]] = []
    nuisance_audit_records: list[pd.DataFrame] = []

    for direction in ("increase", "decrease"):
        sign = 1 if direction == "increase" else -1
        output = {
            name: np.full(len(rows), np.nan, dtype=float)
            for name in (
                "nuisance",
                "full",
                "parent_invariant",
                "context_shuffle",
                "delta_shuffle",
                "interaction_knockout",
            )
        }
        output["context_control_eligible"] = np.zeros(len(rows), dtype=bool)
        output["delta_control_eligible"] = np.zeros(len(rows), dtype=bool)
        for outer_fold in range(5):
            test = fold_values == outer_fold
            train = ~test
            train_rows = rows.loc[train].reset_index(drop=True)
            test_rows = rows.loc[test].reset_index(drop=True)
            assert_held_out(train_rows, test_rows, "biological_unit")
            train_blocks = _subset_blocks(blocks, train)
            test_blocks = _subset_blocks(blocks, test)
            selected, records, nuisance_oof, audits = _inner_select(
                train_rows,
                geometry[train],
                train_blocks,
                direction,
            )
            for record in records:
                selection_records.append(
                    {"outer_fold": outer_fold, "direction": direction, **record, "selected": record["name"] == selected.name}
                )
            for audit in audits:
                audit = audit.copy()
                audit["outer_fold"] = outer_fold
                audit["direction"] = direction
                nuisance_audit_records.append(audit)

            residual = (
                train_rows["localization_effect"].to_numpy(float)
                - nuisance_oof[selected.nuisance_level]
            )
            nuisance_model = fit_nuisance(
                geometry[train],
                train_rows,
                source_specific=selected.nuisance_level == "source",
            )
            nuisance_test = nuisance_model.predict(
                geometry[test],
                test_rows["assay_context"],
                use_source=selected.nuisance_level == "source",
            )
            features_train, interaction_slice = _option_features(train_blocks, selected)
            features_test, _ = _option_features(test_blocks, selected)
            pairs = _pairs_for(train_rows, selected)
            context_model = fit_context(
                features_train,
                residual,
                train_rows,
                selected.family,
                selected.rank,
                selected.alpha,
                interaction_slice,
                pairs=pairs,
                group_robust=selected.group_robust,
            )
            if context_model.training_units & set(test_rows["biological_unit"].astype(str)):
                raise ValueError("Held biological unit entered context fitting")

            output["nuisance"][test] = sign * nuisance_test
            output["full"][test] = sign * (nuisance_test + context_model.predict(features_test))
            output["interaction_knockout"][test] = sign * (
                nuisance_test + context_model.predict(features_test, interaction_knockout=True)
            )

            null_train = train_blocks.parent_invariant()
            null_test = test_blocks.parent_invariant()
            null_model = fit_context(
                null_train,
                residual,
                train_rows,
                "M1",
                0,
                selected.alpha,
                None,
            )
            output["parent_invariant"][test] = sign * (
                nuisance_test + null_model.predict(null_test)
            )

            donors, eligible = control_donor_indices(test_rows)
            context_control = build_context_blocks(
                test_blocks.parent[donors], test_blocks.delta, test_rows
            )
            delta_control = build_context_blocks(
                test_blocks.parent, test_blocks.delta[donors], test_rows
            )
            context_features, _ = _option_features(context_control, selected)
            delta_features, _ = _option_features(delta_control, selected)
            test_indices = np.flatnonzero(test)
            output["context_shuffle"][test_indices[eligible]] = sign * (
                nuisance_test[eligible] + context_model.predict(context_features[eligible])
            )
            output["delta_shuffle"][test_indices[eligible]] = sign * (
                nuisance_test[eligible] + context_model.predict(delta_features[eligible])
            )
            output["context_control_eligible"][test_indices] = eligible
            output["delta_control_eligible"][test_indices] = eligible
            print(
                f"completed primary {direction} outer fold {outer_fold}: {selected.name}",
                flush=True,
            )
        predictions_by_direction[direction] = output

    selection = pd.DataFrame(selection_records)
    selection.to_csv(OUT / "inner_model_selection.csv.gz", index=False, compression=GZIP_OPTIONS)
    pd.concat(nuisance_audit_records, ignore_index=True).to_csv(
        OUT / "nuisance_crossfit_audit.csv", index=False
    )

    metric_records: list[pd.DataFrame] = []
    candidate_records: list[pd.DataFrame] = []
    for direction, scores in predictions_by_direction.items():
        for model in ("nuisance", "full", "parent_invariant", "interaction_knockout"):
            _append_metrics(metric_records, rows, scores[model], model, direction, "outer_biological_fold")
        for control in ("context_shuffle", "delta_shuffle"):
            eligible = scores[f"{control.split('_')[0]}_control_eligible"]
            subset = rows.loc[eligible].reset_index(drop=True)
            valid = _valid_eval(subset, minimum=5)
            subset = subset.loc[valid].reset_index(drop=True)
            original_indices = np.flatnonzero(eligible)[valid]
            _append_metrics(
                metric_records,
                subset,
                scores[control][original_indices],
                control,
                direction,
                "matched_control",
            )
            _append_metrics(
                metric_records,
                subset,
                scores["full"][original_indices],
                f"full_on_{control}",
                direction,
                "matched_control",
            )
        frame = rows[
            ["dataset", "decision_set_id", "candidate_id", "biological_unit", "biological_fold"]
        ].copy()
        frame["row_index"] = np.arange(len(rows))
        frame["requested_direction"] = direction
        for name, values in scores.items():
            frame[name] = values
        candidate_records.append(frame)

    set_metrics = pd.concat(metric_records, ignore_index=True)
    set_metrics.to_csv(OUT / "primary_set_metrics.csv.gz", index=False, compression=GZIP_OPTIONS)
    unit, aggregate = _aggregate(set_metrics)
    unit.to_csv(OUT / "primary_biological_unit_metrics.csv", index=False)
    aggregate.to_csv(OUT / "primary_aggregate_metrics.csv", index=False)
    pd.concat(candidate_records, ignore_index=True).to_csv(
        OUT / "primary_candidate_predictions.csv.gz", index=False, compression=GZIP_OPTIONS
    )
    run_record = {
        "phase": "v4_phaseB2_primary",
        "git_commit_at_run": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "selected_representation": selected_representation(),
        "embedding_metadata": embedding_metadata,
        "rows": len(rows),
        "decision_sets": int(rows["decision_set_id"].nunique()),
        "biological_units": int(rows["biological_unit"].nunique()),
        "cross_parent_pairs": int(len(cross_pairs)),
        "within_parent_pairs": int(len(within_pairs)),
        "scope_guards": {
            "nzip_outcomes_used": False,
            "astrocyte_outcomes_opened": False,
            "astrocyte_sequences_used": False,
            "encoder_fine_tuned": False,
            "dfl_used": False,
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    (OUT / "primary_run.json").write_text(json.dumps(run_record, indent=2) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class TransferScenario:
    family: str
    name: str
    train: np.ndarray
    test: np.ndarray
    held_column: str


def _transfer_scenarios(rows: pd.DataFrame) -> list[TransferScenario]:
    scenarios: list[TransferScenario] = []
    for source in sorted(rows["dataset"].unique()):
        scenarios.append(
            TransferScenario(
                "leave_source_out",
                f"leave_{source}_out",
                rows["dataset"].ne(source).to_numpy(),
                rows["dataset"].eq(source).to_numpy(),
                "dataset",
            )
        )
    mikl = rows["dataset"].eq("mikl_gse173098")
    for train_cell, test_cell in (("CAD", "Neuro-2a"), ("Neuro-2a", "CAD")):
        scenarios.append(
            TransferScenario(
                "cell_transfer",
                f"{train_cell}_to_{test_cell}",
                (mikl & rows["cell_type"].eq(train_cell)).to_numpy(),
                (mikl & rows["cell_type"].eq(test_cell)).to_numpy(),
                "assay_context",
            )
        )
    moffatt = rows["dataset"].eq("moffatt_gse334718")
    paired_units = set(
        rows.loc[moffatt]
        .groupby("biological_unit")["reporter"]
        .nunique()
        .loc[lambda values: values >= 2]
        .index
    )
    paired = moffatt & rows["biological_unit"].isin(paired_units)
    for train_reporter, test_reporter in (("Firefly", "GFP"), ("GFP", "Firefly")):
        scenarios.append(
            TransferScenario(
                "reporter_transfer",
                f"{train_reporter}_to_{test_reporter}",
                (paired & rows["reporter"].eq(train_reporter)).to_numpy(),
                (paired & rows["reporter"].eq(test_reporter)).to_numpy(),
                "assay_context",
            )
        )
    return scenarios


def _consensus_options() -> dict[str, ModelOption]:
    selection = pd.read_csv(OUT / "inner_model_selection.csv.gz")
    selected = selection[selection["selected"]].copy()
    result: dict[str, ModelOption] = {}
    columns = ["family", "alpha", "rank", "nuisance_level", "contrastive", "group_robust"]
    for direction, group in selected.groupby("direction"):
        counts = group.groupby(columns, dropna=False).size().rename("count").reset_index()
        counts["complexity"] = counts["family"].map({"M1": 1, "M2": 2, "M3": 3, "M4": 4})
        row = counts.sort_values(
            ["count", "complexity", "rank", "alpha"],
            ascending=[False, True, True, False],
        ).iloc[0]
        result[str(direction)] = ModelOption(
            family=str(row["family"]),
            alpha=float(row["alpha"]),
            rank=int(row["rank"]),
            nuisance_level="global",  # target-source residual is always unavailable
            contrastive=bool(row["contrastive"]),
            group_robust=bool(row["group_robust"]),
        )
    return result


def evaluate_transfer() -> None:
    rows, geometry, blocks, _ = _load()
    consensus = _consensus_options()
    metric_records: list[pd.DataFrame] = []
    audits: list[dict[str, object]] = []
    for number, scenario in enumerate(_transfer_scenarios(rows), start=1):
        train_rows_raw = rows.loc[scenario.train]
        train_valid = (
            train_rows_raw.groupby("decision_set_id")["candidate_id"].transform("size").ge(2)
            & train_rows_raw.groupby("decision_set_id")["localization_effect"].transform(
                lambda values: values.max() - values.min()
            ).gt(0)
        )
        train_indices = train_rows_raw.index[train_valid].to_numpy(int)
        test_rows_raw = rows.loc[scenario.test]
        test_valid = _valid_eval(test_rows_raw, minimum=5)
        test_indices = test_rows_raw.index[test_valid].to_numpy(int)
        train_rows = rows.iloc[train_indices].reset_index(drop=True)
        test_rows = rows.iloc[test_indices].reset_index(drop=True)
        if not len(train_rows) or not len(test_rows):
            audits.append(
                {
                    "family": scenario.family,
                    "scenario": scenario.name,
                    "status": "no_eligible_decision_sets",
                }
            )
            continue
        if scenario.family == "leave_source_out":
            assert_held_out(train_rows, test_rows, "dataset")
        else:
            if set(train_rows[scenario.held_column]) & set(test_rows[scenario.held_column]):
                raise ValueError(f"Transfer context leaked in {scenario.name}")

        train_blocks = _subset_blocks(blocks, np.isin(np.arange(len(rows)), train_indices))
        test_blocks = _subset_blocks(blocks, np.isin(np.arange(len(rows)), test_indices))
        nuisance_oof, nuisance_audit = cross_fitted_nuisance(
            geometry[train_indices], train_rows, source_specific=False
        )
        nuisance_model = fit_nuisance(geometry[train_indices], train_rows, source_specific=False)
        nuisance_test = nuisance_model.predict(
            geometry[test_indices], test_rows["assay_context"], use_source=False
        )
        for direction in ("increase", "decrease"):
            sign = 1 if direction == "increase" else -1
            option = consensus[direction]
            residual = train_rows["localization_effect"].to_numpy(float) - nuisance_oof
            train_features, interaction_slice = _option_features(train_blocks, option)
            test_features, _ = _option_features(test_blocks, option)
            context_model = fit_context(
                train_features,
                residual,
                train_rows,
                option.family,
                option.rank,
                option.alpha,
                interaction_slice,
                pairs=_pairs_for(train_rows, option),
                group_robust=option.group_robust,
            )
            full_score = sign * (nuisance_test + context_model.predict(test_features))
            nuisance_score = sign * nuisance_test
            for model, score in (("full", full_score), ("nuisance", nuisance_score)):
                metric = decision_set_metrics(
                    test_rows,
                    score,
                    model,
                    direction,
                    SEED,
                    scenario.name,
                )
                metric["scenario_family"] = scenario.family
                metric["scenario"] = scenario.name
                metric_records.append(metric)
        audits.append(
            {
                "family": scenario.family,
                "scenario": scenario.name,
                "status": "evaluated",
                "train_rows": len(train_rows),
                "train_units": int(train_rows["biological_unit"].nunique()),
                "train_sources": sorted(train_rows["dataset"].unique()),
                "test_rows": len(test_rows),
                "test_units": int(test_rows["biological_unit"].nunique()),
                "test_sources": sorted(test_rows["dataset"].unique()),
                "target_source_residual_used": False,
                "crossfit_folds": int(len(nuisance_audit)),
            }
        )
        print(f"completed transfer {number}: {scenario.name}", flush=True)

    set_metrics = pd.concat(metric_records, ignore_index=True)
    set_metrics.to_csv(OUT / "transfer_set_metrics.csv.gz", index=False, compression=GZIP_OPTIONS)
    keys = [
        "scenario_family",
        "scenario",
        "model",
        "dataset",
        "requested_direction",
        "biological_unit",
    ]
    unit = (
        set_metrics.groupby(keys)
        .agg(decision_sets=("decision_set_id", "size"), **{metric: (metric, "mean") for metric in METRICS})
        .reset_index()
    )
    aggregate = (
        unit.groupby(["scenario_family", "scenario", "model", "dataset", "requested_direction"])
        .agg(
            biological_units=("biological_unit", "size"),
            decision_sets=("decision_sets", "sum"),
            **{metric: (metric, "mean") for metric in METRICS},
        )
        .reset_index()
    )
    unit.to_csv(OUT / "transfer_biological_unit_metrics.csv", index=False)
    aggregate.to_csv(OUT / "transfer_aggregate_metrics.csv", index=False)
    (OUT / "transfer_audit.json").write_text(
        json.dumps(
            {
                "consensus_options": {key: asdict(value) for key, value in consensus.items()},
                "target_source_residual_used": False,
                "scenarios": audits,
                "scope_guards": {
                    "nzip_outcomes_used": False,
                    "astrocyte_outcomes_opened": False,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def evaluate_subgroups() -> None:
    rows, _, _, _ = _load()
    predictions = pd.read_csv(OUT / "primary_candidate_predictions.csv.gz")
    keyed = add_matching_keys(rows)
    cross_counts = keyed.groupby("phaseB2_cross_stratum").agg(
        rows=("candidate_id", "size"), units=("biological_unit", "nunique")
    )
    eligible_strata = set(cross_counts[(cross_counts["rows"] >= 20) & (cross_counts["units"] >= 5)].index)
    subgroup_records: list[pd.DataFrame] = []
    audit: list[dict[str, object]] = []

    masks: dict[str, np.ndarray] = {
        band: keyed["phaseB2_edit_band"].eq(band).to_numpy()
        for band in ("1", "2-5", "6-10", "11-25", "26-50", ">50")
    }
    masks["2-10"] = keyed["phaseB2_edit_band"].isin(["2-5", "6-10"]).to_numpy()
    masks["mikl_matched"] = (
        keyed["dataset"].eq("mikl_gse173098")
        & keyed["phaseB2_cross_stratum"].isin(eligible_strata)
    ).to_numpy()

    for direction in ("increase", "decrease"):
        score_rows = predictions[predictions["requested_direction"].eq(direction)].sort_values("row_index")
        if not np.array_equal(score_rows["row_index"].to_numpy(), np.arange(len(rows))):
            raise ValueError("Candidate prediction archive is misaligned")
        for subgroup, mask in masks.items():
            subset = rows.loc[mask].reset_index(drop=True)
            minimum = 2 if subgroup == "1" else 5
            valid = _valid_eval(subset, minimum=minimum)
            original = np.flatnonzero(mask)[valid]
            subset = subset.loc[valid].reset_index(drop=True)
            audit.append(
                {
                    "subgroup": subgroup,
                    "direction": direction,
                    "rows": len(subset),
                    "decision_sets": int(subset["decision_set_id"].nunique()) if len(subset) else 0,
                    "biological_units": int(subset["biological_unit"].nunique()) if len(subset) else 0,
                    "descriptive_only": subgroup == "1",
                }
            )
            if not len(subset):
                continue
            for model in ("full", "nuisance"):
                metric = decision_set_metrics(
                    subset,
                    score_rows[model].to_numpy(float)[original],
                    model,
                    direction,
                    SEED,
                    subgroup,
                )
                metric["subgroup"] = subgroup
                subgroup_records.append(metric)
    set_metrics = pd.concat(subgroup_records, ignore_index=True)
    set_metrics.to_csv(OUT / "subgroup_set_metrics.csv.gz", index=False, compression=GZIP_OPTIONS)
    unit = (
        set_metrics.groupby(
            ["subgroup", "model", "dataset", "requested_direction", "biological_unit"]
        )
        .agg(decision_sets=("decision_set_id", "size"), **{metric: (metric, "mean") for metric in METRICS})
        .reset_index()
    )
    aggregate = (
        unit.groupby(["subgroup", "model", "dataset", "requested_direction"])
        .agg(
            biological_units=("biological_unit", "size"),
            decision_sets=("decision_sets", "sum"),
            **{metric: (metric, "mean") for metric in METRICS},
        )
        .reset_index()
    )
    unit.to_csv(OUT / "subgroup_biological_unit_metrics.csv", index=False)
    aggregate.to_csv(OUT / "subgroup_aggregate_metrics.csv", index=False)
    pd.DataFrame(audit).to_csv(OUT / "subgroup_audit.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=("primary", "transfer", "subgroups", "all"),
        nargs="?",
        default="all",
    )
    args = parser.parse_args()
    if args.stage in {"primary", "all"}:
        evaluate_primary()
    if args.stage in {"transfer", "all"}:
        evaluate_transfer()
    if args.stage in {"subgroups", "all"}:
        evaluate_subgroups()


if __name__ == "__main__":
    main()
