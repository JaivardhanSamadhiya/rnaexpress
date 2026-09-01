"""Leakage, alignment, and decision-metric gates for RNAddress v4 Phase B."""

from __future__ import annotations

import hashlib
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "v4_phaseB"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@lru_cache(maxsize=1)
def _rows() -> pd.DataFrame:
    return pd.read_csv(OUT / "model_candidate_rows.csv.gz")


def test_no_nzip_or_astrocyte_outcome_access() -> None:
    files = [
        *ROOT.glob("src/analysis/*v4_phaseB*.py"),
        *ROOT.glob("src/modeling/v4_*.py"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in files)
    assert "data/processed/nzip" not in combined
    assert "astrocyte_gse330741" not in combined
    assert "data/raw/astrocyte" not in combined
    protected = ROOT / "src/pairing/audit_astrocyte.py"
    assert hashlib.sha256(protected.read_bytes()).hexdigest() == (
        "78fd563f4e51866bc6d0e18aac9bfbbedf20ad0986e6bd087caf9b0b11901a78"
    )


def test_no_candidate_from_held_parent_enters_training() -> None:
    rows = _rows()
    assert rows.groupby(["dataset", "parent_id"])["biological_fold"].nunique().max() == 1
    for fold in range(5):
        held = set(rows.loc[rows["biological_fold"].eq(fold), "parent_id"])
        train = set(rows.loc[rows["biological_fold"].ne(fold), "parent_id"])
        assert held.isdisjoint(train)


def test_no_held_gene_enters_gene_level_training() -> None:
    rows = _rows()
    gene_sources = rows[rows["dataset"].isin(["mikl_gse173098", "tdp43_gse288185"])]
    assert gene_sources.groupby(["dataset", "gene_id"])["biological_fold"].nunique().max() == 1


def test_unseen_source_context_cannot_use_a_residual() -> None:
    from src.modeling.v4_decision_models import fit_predict_then_rank

    rng = np.random.default_rng(2)
    frame = pd.DataFrame(
        {
            "dataset": ["source_a"] * 40,
            "decision_set_id": np.repeat(["a", "b"], 20),
            "candidate_id": [f"c{i}" for i in range(40)],
            "biological_unit": np.repeat(["u1", "u2"], 20),
            "assay_context": ["seen"] * 40,
            "localization_effect": np.tile(np.linspace(-1, 1, 20), 2),
        }
    )
    features = rng.normal(size=(40, 4))
    model = fit_predict_then_rank(features, frame, 1)
    probe = rng.normal(size=(3, 4))
    global_score = model.predict(probe, pd.Series(["unseen"] * 3), use_residual=False)
    transfer_score = model.predict(probe, pd.Series(["unseen"] * 3), use_residual=True)
    assert np.allclose(global_score, transfer_score)


def test_candidate_sets_have_comparable_assay_outcomes() -> None:
    rows = _rows()
    comparable = ["dataset", "assay", "reporter", "cell_type", "outcome_semantics"]
    assert rows.groupby("decision_set_id")[comparable].nunique().to_numpy().max() == 1
    assert rows.groupby("decision_set_id")["candidate_id"].size().min() >= 5
    assert rows.groupby("decision_set_id")["localization_effect"].agg(np.ptp).gt(0).all()


def test_direction_sign_and_normalized_utility_are_correct() -> None:
    from src.modeling.v4_decision_models import normalized_utility

    frame = pd.DataFrame(
        {
            "decision_set_id": ["x"] * 3,
            "localization_effect": [-2.0, 0.0, 2.0],
        }
    )
    assert np.allclose(normalized_utility(frame, 1), [0.0, 0.5, 1.0])
    assert np.allclose(normalized_utility(frame, -1), [1.0, 0.5, 0.0])


def test_normalized_regret_and_directional_rank_are_correct() -> None:
    from src.modeling.v4_decision_models import decision_set_metrics

    frame = pd.DataFrame(
        {
            "dataset": ["d"] * 3,
            "decision_set_id": ["x"] * 3,
            "candidate_id": ["a", "b", "c"],
            "biological_unit": ["u"] * 3,
            "localization_effect": [0.0, 1.0, 2.0],
        }
    )
    result = decision_set_metrics(frame, np.array([0.0, 3.0, 1.0]), "m", "increase", 17, "t")
    assert result.loc[0, "normalized_regret"] == 0.5
    assert result.loc[0, "directional_rank_percentile"] == 0.5


def test_parent_context_can_change_the_same_edit_action() -> None:
    rows = pd.read_csv(OUT / "representation_benchmark_rows.csv.gz")
    cache = np.load(ROOT / "data/interim/v4_phaseB_3utrbert_benchmark_features.npy", mmap_mode="r")
    operation_key = rows["reference_subsequence"].astype(str) + ">" + rows["alternate_subsequence"].astype(str)
    chosen = None
    for _, indices in rows.assign(operation_key=operation_key).groupby("operation_key").indices.items():
        indices = np.asarray(indices, dtype=int)
        parents = rows.iloc[indices]["parent_id"].to_numpy(str)
        if len(set(parents)) >= 2:
            first = indices[0]
            second = indices[np.flatnonzero(parents != parents[0])[0]]
            chosen = (first, second)
            break
    assert chosen is not None
    vectors = cache[rows.iloc[list(chosen)]["feature_row"].to_numpy(int), 256:384]
    difference = vectors[0] - vectors[1]
    assert not np.allclose(difference, 0)
    coefficient = difference
    scores = vectors @ coefficient
    assert scores[0] != scores[1]


def test_edit_geometry_is_deterministic() -> None:
    from src.modeling.v4_decision_models import geometry_features

    sample = _rows().iloc[:50].copy()
    first = geometry_features(sample)
    second = geometry_features(sample.copy())
    assert np.array_equal(first, second)
    assert np.isfinite(first).all()


def test_exact_sequence_hashes_match_source_sequences() -> None:
    from src.modeling.v4_embeddings import sequence_hash

    rows = _rows().drop_duplicates(["dataset", "parent_id", "mutant_id"]).iloc[::997]
    for sequence in pd.concat([rows["parent_sequence"], rows["mutant_sequence"]]):
        assert sequence_hash(sequence) == hashlib.sha256(sequence.encode("ascii")).hexdigest()


def test_context_delta_uses_aligned_edited_positions() -> None:
    from src.modeling.v4_embeddings import FrozenEncoder

    encoder = FrozenEncoder.__new__(FrozenEncoder)
    encoder.name = "splicebert"
    encoder.hidden_size = 2
    parent_hidden = torch.zeros((1, 6, 2))
    mutant_hidden = parent_hidden.clone()
    mutant_hidden[0, 3] = torch.tensor([4.0, 8.0])
    pooled = encoder.context_raw(parent_hidden, mutant_hidden, "AAAA", "AACA", radius=0)
    assert np.allclose(pooled[:2], [0.0, 0.0])
    assert np.allclose(pooled[2:4], [1.0, 2.0])
    assert np.allclose(pooled[4:6], [4.0, 8.0])
    assert np.allclose(pooled[6:8], [4.0, 8.0])


def test_scaling_is_fit_without_held_group_values() -> None:
    train = np.array([[0.0], [2.0], [4.0]])
    held_a = np.array([[100.0]])
    held_b = np.array([[-1000.0]])
    scaler_a = StandardScaler().fit(train)
    scaler_b = StandardScaler().fit(train)
    assert np.array_equal(scaler_a.mean_, scaler_b.mean_)
    assert not np.array_equal(scaler_a.transform(held_a), scaler_b.transform(held_b))
    source = (ROOT / "src/analysis/run_v4_phaseB_models.py").read_text(encoding="utf-8")
    assert "StandardScaler().fit(features[train])" in source


def test_dfl_fit_excludes_held_outcomes() -> None:
    from src.modeling.v4_decision_models import fit_dfl

    rng = np.random.default_rng(5)
    full = pd.DataFrame(
        {
            "dataset": ["d"] * 12,
            "decision_set_id": np.repeat(["a", "b", "held"], 4),
            "candidate_id": [f"c{i}" for i in range(12)],
            "biological_unit": np.repeat(["u1", "u2", "u3"], 4),
            "assay_context": ["ctx"] * 12,
            "localization_effect": np.tile([0.0, 1.0, 2.0, 3.0], 3),
        }
    )
    changed = full.copy()
    changed.loc[changed["decision_set_id"].eq("held"), "localization_effect"] *= 10_000
    features = rng.normal(size=(12, 3)).astype(np.float32)
    train = full["decision_set_id"].ne("held").to_numpy()
    first = fit_dfl(features[train], full.loc[train].reset_index(drop=True), 1, 17, maximum_epochs=3)
    second = fit_dfl(features[train], changed.loc[train].reset_index(drop=True), 1, 17, maximum_epochs=3)
    probe = rng.normal(size=(2, 3))
    assert np.allclose(first.global_scores(probe), second.global_scores(probe))


def test_permutation_controls_break_the_intended_relationship() -> None:
    from src.analysis.run_v4_phaseB_controls import (
        permute_outcomes_within_source,
        permute_parent_context_features,
        permute_scores_within_decision_set,
    )

    frame = pd.DataFrame(
        {
            "dataset": ["d"] * 6,
            "decision_set_id": ["a"] * 3 + ["b"] * 3,
            "localization_effect": np.arange(6.0),
        }
    )
    assert not np.array_equal(
        frame["localization_effect"], permute_outcomes_within_source(frame, 17)["localization_effect"]
    )
    features = np.arange(6 * 260, dtype=float).reshape(6, 260)
    assert not np.array_equal(features, permute_parent_context_features(frame, features, 17))
    scores = np.arange(6.0)
    assert not np.array_equal(scores, permute_scores_within_decision_set(frame, scores, 17))


def test_phaseB_scope_manifests_keep_protected_data_false() -> None:
    for name in (
        "decision_set_audit.json",
        "representation_benchmark_summary.json",
    ):
        text = (OUT / name).read_text(encoding="utf-8").lower()
        assert '"nzip_outcomes_used": false' in text
        assert '"astrocyte_outcomes_opened": false' in text


def test_reproducibility_manifest_records_missing_optional_packages(monkeypatch) -> None:
    from importlib.metadata import PackageNotFoundError

    from src.analysis.build_v4_phaseB_manifest import package_versions

    def fake_version(package: str) -> str:
        if package == "optional-model-runtime":
            raise PackageNotFoundError(package)
        return "1.2.3"

    monkeypatch.setattr("importlib.metadata.version", fake_version)
    assert package_versions(["core", "optional-model-runtime"]) == {
        "core": "1.2.3",
        "optional-model-runtime": "not-installed",
    }
