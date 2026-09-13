"""Mechanism-v5 guard tests. These never produce or inspect an outer score."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.mechanism_v5 import evaluate, io
from src.mechanism_v5.features import (au_delta, au_fraction, delta_frequency,
                                       kmer_frequency, kmer_names, normalize,
                                       random_projection)


def test_normalize_maps_rna_to_dna():
    assert normalize('acguACGU') == 'ACGTACGT'


def test_kmer_frequency_is_length_invariant_up_to_window_edge_effects():
    """A 150 nt and a 260 nt source must be broadly comparable.

    Exact equality is impossible: the final k-window is truncated, so per-k
    frequencies carry an O(1/L) boundary bias. The tolerance here records the
    real size of that bias rather than pretending it is absent. The arms do not
    depend on it vanishing -- see the two tests below.
    """
    # The real lengths in play: Mikl is 150 nt, Moffatt and TDP43 are 260 nt.
    short_len, long_len = 152, 260
    short = kmer_frequency(['ACGT' * (short_len // 4)], ks=(1, 2, 3))
    long = kmer_frequency(['ACGT' * (long_len // 4)], ks=(1, 2, 3))
    # Analytic bound: each per-k frequency sits within 1/(L-k+1) of uniform, so
    # two lengths can differ by at most the sum of their bounds. No magic number.
    bound = 1.0 / (short_len - 3 + 1) + 1.0 / (long_len - 3 + 1)
    assert np.max(np.abs(short - long)) <= bound
    # k=1 has no truncated window and is therefore exact at any length.
    assert np.allclose(short[0, :4], long[0, :4], atol=1e-12)


def test_finite_difference_cancels_length_bias_for_a_linear_model():
    """Arm B trains at 260 nt and scores at 150 nt, so this cancellation is load-bearing.

    Both arms only ever difference two sequences of equal length, and a linear
    model gives w.x_m - w.x_p = w.(x_m - x_p), so any length-dependent offset
    cancels exactly.
    """
    rng = np.random.default_rng(0)
    weights = rng.normal(size=4 + 16 + 64)

    def predict(seqs):
        return kmer_frequency(seqs, ks=(1, 2, 3)) @ weights

    mutant, parent = 'ACGTACGTAA' * 15, 'ACGTACGTGG' * 15
    direct = predict([mutant])[0] - predict([parent])[0]
    via_delta = delta_frequency([mutant], [parent], (1, 2, 3)) @ weights
    assert np.isclose(direct, via_delta[0], atol=1e-12)


def test_delta_features_are_identical_for_equal_length_pairs_at_any_length():
    """The same edit evaluated in a longer context shifts delta by O(1/L), not by scale."""
    small = delta_frequency(['AAGGAAGG' * 5], ['AAGGAAGC' * 5], (1, 2))
    large = delta_frequency(['AAGGAAGG' * 20], ['AAGGAAGC' * 20], (1, 2))
    assert np.sign(small).tolist() == np.sign(large).tolist()


def test_kmer_frequency_sums_to_one_per_k():
    matrix = kmer_frequency(['ACGTACGTAC'], ks=(1, 2, 3))
    assert np.isclose(matrix[0, :4].sum(), 1.0)
    assert np.isclose(matrix[0, 4:20].sum(), 1.0)
    assert np.isclose(matrix[0, 20:].sum(), 1.0)


def test_delta_frequency_is_zero_for_identical_sequences():
    assert np.allclose(delta_frequency(['ACGTACGT'], ['ACGTACGT'], (1, 2)), 0.0)


def test_delta_frequency_is_antisymmetric():
    a, b = ['ACGTACGTAA'], ['ACGTACGTGG']
    assert np.allclose(delta_frequency(a, b, (1, 2)), -delta_frequency(b, a, (1, 2)))


def test_au_fraction_and_delta():
    assert au_fraction('AATT') == 1.0
    assert au_fraction('GGCC') == 0.0
    assert np.isclose(au_delta(['AATT'], ['GGCC'])[0, 0], 1.0)


def test_random_projection_is_seed_reproducible():
    features = np.arange(12, dtype=float).reshape(3, 4)
    assert np.allclose(random_projection(features, 7, 4), random_projection(features, 7, 4))
    assert not np.allclose(random_projection(features, 7, 4),
                           random_projection(features, 8, 4))


def test_kmer_names_width():
    assert len(kmer_names((1, 2, 3))) == 4 + 16 + 64


def test_writes_outside_mechanism_v5_are_refused():
    with pytest.raises(PermissionError):
        io.output_path('results/mechanism_v4/should_not_write.json')


def test_holdout_loader_refuses_unconditionally():
    with pytest.raises(PermissionError):
        io.open_holdout()


def test_only_hash_pinned_tables_load():
    with pytest.raises(PermissionError):
        io.load_development('results/v4_phaseB/model_interventions.csv.gz')


def test_design_declares_commitment_and_both_arms():
    design = io.load_design()
    assert design['committed_before_scoring'] is True
    assert set(design['arms']) == {'A_cross_gene_edit_direction',
                                   'B_cross_source_finite_difference'}
    assert design['diagnostics_that_shaped_this_design']['refuted_hypothesis']


def test_confident_subset_keeps_only_significant_rows_and_labels_by_sign():
    table = pd.DataFrame({
        'mutant_sequence': ['A', 'B', 'C', 'D'],
        'effect': [1.0, -1.0, 0.05, 2.0],
        'uncertainty': [0.1, 0.1, 1.0, 0.1],
        'parent': ['A', 'B', 'C', 'D'],
        'gene': ['g1', 'g2', 'g3', 'g4'],
        'component': ['c1', 'c2', 'c3', 'c4'],
        'fold': [0, 1, 2, 3],
    })
    conf = evaluate.confident(table)
    assert set(conf.mutant_sequence) == {'A', 'B', 'D'}
    assert conf.set_index('mutant_sequence').label.to_dict() == {'A': 1, 'B': 0, 'D': 1}


def test_group_integrity_detects_a_gene_straddling_folds():
    """Arm A must refuse to report integrity when a gene spans train and test."""
    rng = np.random.default_rng(0)
    n = 120
    features = rng.normal(size=(n, 4))
    labels = rng.integers(0, 2, n)
    fold_ids = rng.integers(0, 5, n)
    folds = [fold_ids == f for f in range(5)]
    shared_gene = np.array(['same'] * n)
    result = evaluate._grouped_auroc(features, labels, folds,
                                     np.arange(n).astype(str), shared_gene, seed=0)
    assert result['group_integrity'] is False
