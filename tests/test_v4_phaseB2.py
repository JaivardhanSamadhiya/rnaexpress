"""Prospectively frozen leakage and mechanism tests for v4 Phase B2."""

from __future__ import annotations

import hashlib
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PHASE_B = ROOT / "results" / "v4_phaseB"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.modeling.v4_decision_models import geometry_features, source_set_weights
from src.modeling.v4_phaseB2_context import (
    add_matching_keys,
    build_context_blocks,
    control_donor_indices,
    cross_fitted_nuisance,
    fit_context,
    fit_context_alpha_grid,
    fit_nuisance,
    matched_pairs,
)


@lru_cache(maxsize=1)
def _rows() -> pd.DataFrame:
    return pd.read_csv(PHASE_B / "model_candidate_rows.csv.gz")


def _synthetic() -> pd.DataFrame:
    records = []
    for unit_number in range(6):
        for candidate in range(5):
            parent = "A" * 20
            mutant = parent[:candidate] + "C" + parent[candidate + 1 :]
            records.append(
                {
                    "dataset": "source_a" if unit_number < 3 else "source_b",
                    "assay_context": "ctx_a" if unit_number < 3 else "ctx_b",
                    "decision_set_id": f"set_{unit_number}",
                    "candidate_id": f"u{unit_number}_c{candidate}",
                    "biological_unit": f"unit_{unit_number}",
                    "biological_fold": unit_number % 3,
                    "parent_id": f"parent_{unit_number}",
                    "gene_id": f"gene_{unit_number}",
                    "parent_sequence": parent,
                    "mutant_sequence": mutant,
                    "localization_effect": unit_number + candidate / 5,
                    "edit_distance": 1,
                    "edit_fraction": 0.05,
                    "edit_cost": 1,
                    "substitution_count": 1,
                    "insertion_length": 0,
                    "deletion_length": 0,
                    "replacement_length": 0,
                    "changed_block_count": 1,
                    "mean_edit_position_1based": candidate + 1,
                    "first_edit_position_1based": candidate + 1,
                    "last_edit_position_1based": candidate + 1,
                    "edit_span_length": 1,
                    "intervention_class": "random_substitution",
                    "edit_tier": "exact_snv",
                    "motif_family": "not_applicable",
                }
            )
    return pd.DataFrame(records)


def test_01_nzip_outcomes_are_inaccessible() -> None:
    sources = [
        ROOT / "src/analysis/run_v4_phaseB2.py",
        ROOT / "src/modeling/v4_phaseB2_context.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in sources)
    assert "data/processed/nzip" not in combined
    assert "reconstruct_nzip" not in combined


def test_02_astrocyte_outcomes_are_inaccessible() -> None:
    sources = [
        ROOT / "src/analysis/run_v4_phaseB2.py",
        ROOT / "src/modeling/v4_phaseB2_context.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in sources)
    assert "data/raw/astrocyte" not in combined
    protected = ROOT / "src/pairing/audit_astrocyte.py"
    assert hashlib.sha256(protected.read_bytes()).hexdigest() == (
        "78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78"
    )


def test_03_nuisance_predictions_are_cross_fitted() -> None:
    frame = _synthetic()
    features = geometry_features(frame)
    _, audit = cross_fitted_nuisance(features, frame, source_specific=False)
    assert len(audit) == frame["biological_fold"].nunique()
    assert audit["unit_overlap"].eq(0).all()
    assert audit["test_rows"].sum() == len(frame)


def test_04_residual_labels_never_use_own_fold_outcomes() -> None:
    frame = _synthetic()
    features = geometry_features(frame)
    first, _ = cross_fitted_nuisance(features, frame, source_specific=False)
    changed = frame.copy()
    held = changed["biological_fold"].eq(0)
    changed.loc[held, "localization_effect"] += 100_000
    second, _ = cross_fitted_nuisance(features, changed, source_specific=False)
    assert np.allclose(first[held], second[held])


def test_05_held_parent_is_absent_from_training() -> None:
    rows = _rows()
    assert rows.groupby(["dataset", "parent_id"])["biological_fold"].nunique().max() == 1


def test_06_held_gene_is_absent_from_training() -> None:
    rows = _rows()
    genes = rows[rows["dataset"].isin(["mikl_gse173098", "tdp43_gse288185"])]
    assert genes.groupby(["dataset", "gene_id"])["biological_fold"].nunique().max() == 1


def test_07_held_source_is_absent_from_training() -> None:
    from src.analysis.run_v4_phaseB2 import _transfer_scenarios

    rows = _rows()
    for scenario in _transfer_scenarios(rows):
        if scenario.family != "leave_source_out":
            continue
        assert set(rows.loc[scenario.train, "dataset"]).isdisjoint(
            set(rows.loc[scenario.test, "dataset"])
        )


def test_08_target_source_residual_is_disabled() -> None:
    frame = _synthetic()
    features = geometry_features(frame)
    model = fit_nuisance(features, frame, source_specific=True)
    probe = features[:3]
    unseen = pd.Series(["unseen_context"] * 3)
    assert np.allclose(
        model.predict(probe, unseen, use_source=False),
        model.predict(probe, unseen, use_source=True),
    )


def test_09_matched_strata_preserve_nuisance_geometry() -> None:
    frame = _synthetic()
    keyed = add_matching_keys(frame)
    donors, eligible = control_donor_indices(frame)
    assert eligible.all()
    assert np.array_equal(
        keyed.loc[eligible, "phaseB2_cross_stratum"].to_numpy(),
        keyed.iloc[donors[eligible]]["phaseB2_cross_stratum"].to_numpy(),
    )


def test_10_context_shuffle_changes_only_context() -> None:
    frame = _synthetic()
    rng = np.random.default_rng(10)
    parent = np.repeat(np.arange(6), 5)[:, None] * np.ones((len(frame), 128))
    delta = rng.normal(size=(len(frame), 128))
    blocks = build_context_blocks(parent, delta, frame)
    donors, eligible = control_donor_indices(frame)
    shuffled = build_context_blocks(blocks.parent[donors], blocks.delta, frame)
    assert not np.array_equal(shuffled.parent[eligible], blocks.parent[eligible])
    assert np.array_equal(shuffled.delta, blocks.delta)
    assert np.array_equal(shuffled.numeric, blocks.numeric)


def test_11_geometry_remains_intact_in_context_controls() -> None:
    frame = _synthetic()
    before = geometry_features(frame)
    donors, _ = control_donor_indices(frame)
    controlled = frame.copy()
    controlled["parent_id"] = frame.iloc[donors]["parent_id"].to_numpy()
    assert np.array_equal(before, geometry_features(controlled))


def test_12_interaction_knockout_sets_only_bilinear_columns_to_zero() -> None:
    frame = _synthetic()
    rng = np.random.default_rng(12)
    blocks = build_context_blocks(
        rng.normal(size=(len(frame), 128)),
        rng.normal(size=(len(frame), 128)),
        frame,
    )
    features, interaction_slice = blocks.features("M2", 4)
    model = fit_context(
        features,
        frame["localization_effect"].to_numpy(),
        frame,
        "M2",
        4,
        100,
        interaction_slice,
    )
    knocked = features.copy()
    knocked[:, interaction_slice] = 0
    assert np.allclose(model.predict(knocked), model.predict(features, interaction_knockout=True))
    assert np.array_equal(knocked[:, : interaction_slice.start], features[:, : interaction_slice.start])


def test_13_bilinear_term_responds_to_parent_changes() -> None:
    frame = _synthetic().iloc[:2].copy()
    delta = np.ones((2, 128))
    parent = np.zeros((2, 128))
    parent[1] = 1
    blocks = build_context_blocks(parent, delta, frame)
    features, interaction_slice = blocks.features("M2", 16)
    assert not np.allclose(features[0, interaction_slice], features[1, interaction_slice])


def test_14_same_parent_and_edit_is_deterministic() -> None:
    frame = _synthetic().iloc[:2].copy()
    parent = np.ones((2, 128))
    delta = np.full((2, 128), 2.0)
    first = build_context_blocks(parent, delta, frame).features("M2", 8)[0]
    second = build_context_blocks(parent.copy(), delta.copy(), frame.copy()).features("M2", 8)[0]
    assert np.array_equal(first, second)


def test_15_biological_unit_weighting_is_hierarchical() -> None:
    frame = _synthetic()
    weights = source_set_weights(frame)
    weighted = frame.assign(weight=weights)
    source_totals = weighted.groupby("dataset")["weight"].sum()
    assert np.allclose(source_totals, source_totals.iloc[0])
    unit_totals = weighted.groupby(["dataset", "biological_unit"])["weight"].sum()
    assert np.allclose(unit_totals, unit_totals.iloc[0])


def test_16_no_moffatt_parent_dominates_by_row_count() -> None:
    rows = _rows()
    weights = source_set_weights(rows)
    moffatt = rows["dataset"].eq("moffatt_gse334718")
    totals = rows.loc[moffatt].assign(weight=weights[moffatt]).groupby("biological_unit")["weight"].sum()
    assert np.allclose(totals, totals.iloc[0])


def test_17_exact_snv_is_never_an_independent_gate() -> None:
    rows = _rows()
    snv = rows[rows["edit_tier"].eq("exact_snv")]
    assert len(snv) == 38
    assert snv["decision_set_id"].nunique() > 0
    # A dense trp53 shape-replicate set has six assay rows, but every SNV-only
    # set still represents one biological parent.  It is therefore not an
    # independent-parent transfer gate regardless of raw candidate count.
    assert snv.groupby("decision_set_id")["biological_unit"].nunique().max() == 1
    set_sizes = snv.groupby("decision_set_id")["candidate_id"].size()
    eligible_sets = set(set_sizes[set_sizes >= 5].index)
    assert len(eligible_sets) == 2
    assert snv[snv["decision_set_id"].isin(eligible_sets)]["biological_unit"].nunique() == 1
    protocol = (ROOT / "reports/v4_phaseB2_protocol.md").read_text(encoding="utf-8")
    assert "Exact 1-nt results are descriptive only" in protocol


def test_matched_pair_membership_is_outcome_blind() -> None:
    frame = _synthetic()
    first_cross, first_within, _ = matched_pairs(frame)
    changed = frame.copy()
    changed["localization_effect"] = np.arange(len(changed))[::-1]
    second_cross, second_within, _ = matched_pairs(changed)
    assert np.array_equal(first_cross, second_cross)
    assert np.array_equal(first_within, second_within)


def test_shared_gram_ridge_matches_individual_ridge() -> None:
    frame = _synthetic()
    rng = np.random.default_rng(19)
    features = rng.normal(size=(len(frame), 9))
    target = frame["localization_effect"].to_numpy() + rng.normal(size=len(frame))
    individual = fit_context(features, target, frame, "M1", 0, 100.0, None)
    shared = fit_context_alpha_grid(
        features, target, frame, "M1", 0, (10.0, 100.0, 1_000.0), None
    )[100.0]
    probe = rng.normal(size=(11, 9))
    assert np.allclose(individual.predict(probe), shared.predict(probe), atol=1e-8)
