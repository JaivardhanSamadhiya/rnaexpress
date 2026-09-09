"""Small tests for reporting/audit additions; no protected data are loaded."""
import numpy as np
import pytest
from src.analysis.summarize_finalshot_cell_control import verify_row_hashes
from src.analysis.summarize_finalshot_tdp_geometry import exact_geometry_keys


def test_exact_geometry_match_requires_all_features_equal():
    matrix = np.array([[1, 2], [1, 2], [1, 3]], dtype=np.float32)
    keys = exact_geometry_keys(matrix)
    assert keys[0] == keys[1] and keys[0] != keys[2]
    assert exact_geometry_keys(matrix.astype(np.float64)) == keys


def test_cell_control_hash_guard_checks_every_seed_and_inner_fit():
    row = {'rows_sha256': 'expected', 'unit_overlap': 0}
    metadata = {'seed_refits': [dict(row, seed=seed) for seed in (17, 41, 89)],
                'inner_grid': [{'seed_fit_audits': [row.copy()]}]}
    verify_row_hashes('M3', metadata, 'expected')
    metadata['inner_grid'][0]['seed_fit_audits'][0]['rows_sha256'] = 'wrong'
    with pytest.raises(AssertionError):
        verify_row_hashes('M3', metadata, 'expected')


def test_cell_control_hash_guard_rejects_missing_seed_and_overlap():
    row = {'rows_sha256': 'expected', 'unit_overlap': 0}
    metadata = {'seed_refits': [dict(row, seed=seed) for seed in (17, 41)], 'inner_grid': []}
    with pytest.raises(AssertionError):
        verify_row_hashes('M3', metadata, 'expected')
    metadata['seed_refits'].append(dict(row, seed=89, unit_overlap=1))
    with pytest.raises(AssertionError):
        verify_row_hashes('M3', metadata, 'expected')


def test_cell_control_direct_hash_guard_accepts_both_original_schemas():
    verify_row_hashes('M1', {'input_hashes': {'rows': 'expected'}}, 'expected')
    verify_row_hashes('M2', {'rows_sha256': 'expected'}, 'expected')
    with pytest.raises(AssertionError):
        verify_row_hashes('M2', {'rows_sha256': 'wrong'}, 'expected')
