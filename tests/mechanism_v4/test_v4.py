"""Mechanism-v4 guard tests. These never produce or inspect an outer score."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.mechanism_v4 import evaluate, io
from src.mechanism_v4.features import kmer_matrix, kmer_names, normalize


def test_normalize_maps_rna_to_dna():
    assert normalize('acguACGU') == 'ACGTACGT'


def test_kmer_names_has_expected_width():
    assert len(kmer_names((1, 2, 3, 4, 5))) == 4 + 16 + 64 + 256 + 1024


def test_kmer_counts_are_sliding_windows():
    matrix = kmer_matrix(['AAAA'], ks=(1, 2))
    names = kmer_names((1, 2))
    assert matrix[0, names.index('A')] == 4
    assert matrix[0, names.index('AA')] == 3
    assert matrix[0, names.index('AC')] == 0


def test_kmer_counts_skip_ambiguous_windows():
    matrix = kmer_matrix(['ACNGT'], ks=(2,))
    names = kmer_names((2,))
    assert matrix[0, names.index('AC')] == 1
    assert matrix[0, names.index('GT')] == 1
    assert matrix[0].sum() == 2


def test_writes_outside_mechanism_v4_are_refused():
    with pytest.raises(PermissionError):
        io.output_path('results/mechanism_v2/should_not_write.json')


def test_holdout_loader_refuses_unconditionally():
    with pytest.raises(PermissionError):
        io.open_holdout()


def test_only_hash_pinned_tables_load():
    with pytest.raises(PermissionError):
        io.load_development('results/v4_phaseB/model_interventions.csv.gz')


def test_design_declares_it_was_committed_before_scoring():
    design = io.load_design()
    assert design['committed_before_scoring'] is True
    assert design['primary_source'] == 'moffatt_gse334718'
    assert design['boundaries_unchanged']


def _toy_units(n=200):
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        'mutant_sequence': [''.join(rng.choice(list('ACGT'), 40)) for _ in range(n)],
        'effect': rng.normal(size=n),
        'component': rng.integers(0, 10, n).astype(str),
        'gene': rng.integers(0, 4, n).astype(str),
        'fold': rng.integers(0, 5, n),
        'label': rng.integers(0, 2, n),
    })


def test_t1_folds_partition_every_sequence_exactly_once():
    units = _toy_units()
    folds = evaluate._t1_folds(units, seed=20260912)
    covered = np.concatenate(folds)
    assert sorted(covered.tolist()) == list(range(len(units)))


def test_t1_folds_keep_each_gene_represented_in_training():
    units = _toy_units()
    folds = evaluate._t1_folds(units, seed=20260912)
    for test in folds:
        train = np.setdiff1d(np.arange(len(units)), test)
        assert set(units.gene.to_numpy()[train]) == set(units.gene.unique())


def test_group_integrity_flag_detects_a_straddling_component():
    """T2 must refuse to report integrity when a component spans train and test."""
    units = _toy_units()
    units['component'] = 'shared'
    params = {'max_iter': 5, 'learning_rate': 0.1, 'max_depth': 3}
    folds = [np.where(units.fold.to_numpy() == f)[0] for f in range(5)]
    result = evaluate._run_estimand(
        folds, kmer_matrix(units.mutant_sequence, (1, 2)), units.label.to_numpy(),
        units.effect.to_numpy(), params, 0, units, check_groups=True)
    assert result['group_integrity'] is False
