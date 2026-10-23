"""Supplied-byte validation. NO file loader, runtime import or project admission."""
import hashlib
import io
import json
import sys
from src.generalization_knowncell_joint_implementation_20261022.contracts import (
    full_metadata_contract, ids_sha, metadata_sha,
)
from src.generalization_knowncell_joint_implementation_20261022.admission import require_resources
from .envelope import inspect_supplied_npz
from .inspect_bytes import checked_sha, source_row_bytes
from .spec import SHAPE, STATUS


def supplied_json(raw, expected_sha256):
    assert isinstance(raw, bytes) and len(raw) <= 2 * 2**20
    actual = checked_sha(raw, expected_sha256)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, 'Duplicate supplied receipt field'
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique), actual


def creation_order_contract(rows, creation_bytes, metadata_bytes, *,
                            expected_creation_sha256, expected_metadata_sha256,
                            expected_row_ids_sha256, expected_shape=SHAPE):
    """Pure identity check. Caller binds these explicit pins to original freezes.

    The generic expected_shape argument exists for tiny invented contract
    tests. validate_supplied_array below fixes the real13781x102 shape and
    separately proves the full metadata/menu/split/count contract.
    """
    assert rows and len(rows) == expected_shape[0]
    assert len({row['intervention_id'] for row in rows}) == len(rows)
    assert isinstance(expected_row_ids_sha256, str) and len(expected_row_ids_sha256) == 64
    assert ids_sha(rows) == expected_row_ids_sha256
    creation, creation_sha = supplied_json(creation_bytes, expected_creation_sha256)
    metadata, metadata_sha256 = supplied_json(metadata_bytes, expected_metadata_sha256)
    assert creation['status'] == metadata['status'] == 'PASS'
    assert creation['rows'] == metadata['rows'] == expected_shape[0]
    assert type(creation['widths']['simple']) is int and creation['widths']['simple'] == expected_shape[1]
    assert creation['row_ids_sha256'] == metadata['row_ids_sha256'] == expected_row_ids_sha256
    assert metadata['components'] == len({row['biological_component'] for row in rows})
    assert creation['outcome_columns_read'] is False and creation['new_features_or_outcomes_generated'] is False
    assert creation['project_fits_run'] is False and metadata['outcome_columns_read'] is False
    assert metadata['original_alleles_retained'] is True and metadata['project_fits_run'] is False
    return {'rows': len(rows), 'columns': expected_shape[1],
            'row_ids_sha256': expected_row_ids_sha256, 'supplied_metadata_sha256': metadata_sha(rows),
            'supplied_creation_receipt_sha256': creation_sha, 'supplied_metadata_receipt_sha256': metadata_sha256,
            'creation_order_matches_supplied_metadata': True,
            'original_freeze_alias_or_commit_NOT_verified_here': True}


def crosscell_allele_bytes(rows, row_bytes, columns):
    """Exact bytes for every identical(parent,mutant) group represented in both cells."""
    groups = {}; iterator = iter(row_bytes)
    for row in rows:
        try: values = next(iterator)
        except StopIteration as error: raise AssertionError('Missing supplied feature row') from error
        assert isinstance(values, bytes) and len(values) == columns*8
        assert row['cell_type'] in ('CAD', 'Neuro-2a')
        key = row['parent_sequence'], row['mutant_sequence']
        if key not in groups:
            groups[key] = {'first': values, 'cells': set(), 'rows': 0, 'all_bytes_equal': True}
        group = groups[key]
        group['all_bytes_equal'] &= values == group['first']
        group['cells'].add(row['cell_type']); group['rows'] += 1
    try: next(iterator)
    except StopIteration: pass
    else: raise AssertionError('Extra supplied feature rows')
    represented = [group for group in groups.values() if len(group['cells']) == 2]
    assert all(group['all_bytes_equal'] for group in represented), 'Cross-cell exact-allele feature BYTES differ'
    return {'crosscell_allele_groups': len(represented), 'crosscell_rows_checked': sum(group['rows'] for group in represented),
            'all_crosscell_matching_allele_bytes_equal': True, 'tolerance_or_zero_filling_used': False}


def _native_rows(inspection):
    """Endian conversion by bytes only; no numeric rounding or normalization."""
    header = inspection['npy']; source = header['descr'][0]
    native = '<' if sys.byteorder == 'little' else '>'
    reverse = source != '=' and source != native
    for row in source_row_bytes(inspection['npy_bytes'], header):
        yield b''.join(row[i:i+8][::-1] for i in range(0, len(row), 8)) if reverse else row


def _materialize_supplied(raw, inspection, np, *, resource_probe, environment):
    """Deferred ORIGINAL NumPy load+astype(float), testable with a tiny mock only."""
    assert getattr(np, '__name__', None) == 'numpy'
    assert checked_sha(raw, inspection['raw_npz_sha256']) == inspection['raw_npz_sha256']
    require_resources(resource_probe(), environment)  # Immediate fresh gate before NumPy call.
    with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
        assert archive.files == ['features']
        matrix = archive['features'].astype(float)  # Exact original convention, including default order.
    assert matrix.shape == tuple(inspection['npy']['shape'])
    assert matrix.dtype.kind == 'f' and matrix.dtype.itemsize == 8 and not matrix.dtype.hasobject and matrix.dtype.isnative
    assert np.isfinite(matrix).all()
    actual = matrix.tobytes(order='C')
    rows, columns = matrix.shape; assert len(actual) == rows*columns*8
    for index, expected in enumerate(_native_rows(inspection)):
        assert actual[index*columns*8:(index+1)*columns*8] == expected, 'Deferred load/cast altered scalar feature bits'
    return matrix, actual


def validate_supplied_array(raw_npz, metadata_rows, creation_receipt_bytes, metadata_receipt_bytes, *,
                             expected_npz_sha256, expected_creation_sha256, expected_metadata_sha256,
                             expected_row_ids_sha256, np, external_runtime_accepted,
                             external_runtime_receipt_sha256, resource_probe, environment):
    """Validate already supplied bytes; NEVER certify a project alias or FIT stage.

    Preconditions belong to a FUTURE separate wrapper: real source/Git/pin
    admission, accepted current-Python NumPy origins, real fresh resource
    probe, and guarded payload acquisition. No wrapper exists in this module.
    """
    assert external_runtime_accepted is True
    assert isinstance(external_runtime_receipt_sha256, str) and len(external_runtime_receipt_sha256) == 64
    assert all(c in '0123456789abcdef' for c in external_runtime_receipt_sha256)
    require_resources(resource_probe(), environment)  # Before examining supplied project metadata/array.
    inspection = inspect_supplied_npz(raw_npz, expected_npz_sha256, SHAPE)
    identity = creation_order_contract(metadata_rows, creation_receipt_bytes, metadata_receipt_bytes,
        expected_creation_sha256=expected_creation_sha256, expected_metadata_sha256=expected_metadata_sha256,
        expected_row_ids_sha256=expected_row_ids_sha256, expected_shape=SHAPE)
    metadata_proof = full_metadata_contract(metadata_rows)
    assert metadata_proof['row_ids_sha256'] == expected_row_ids_sha256
    original_parity = crosscell_allele_bytes(metadata_rows, source_row_bytes(inspection['npy_bytes'], inspection['npy']), SHAPE[1])
    assert original_parity['crosscell_allele_groups'] > 0
    matrix, native_bytes = _materialize_supplied(raw_npz, inspection, np, resource_probe=resource_probe, environment=environment)
    row_size = SHAPE[1]*8
    parity = crosscell_allele_bytes(metadata_rows,
        (native_bytes[i*row_size:(i+1)*row_size] for i in range(SHAPE[0])), SHAPE[1])
    report = {'status': STATUS, 'rows': SHAPE[0], 'columns': SHAPE[1], 'all_columns_finite': True,
              'supplied_npz_sha256': inspection['raw_npz_sha256'],
              'supplied_npy_sha256': inspection['npy']['npy_sha256'],
              'post_original_astype_float_C_bytes_sha256': hashlib.sha256(native_bytes).hexdigest(),
              'compressed_bytes': inspection['compressed_bytes'], 'expanded_bytes': inspection['expanded_bytes'],
              'creation_identity': identity, 'original_storage_parity': original_parity,
              'native_astype_parity': parity, 'exact_astype_value_bits_replayed': True,
              'supplied_metadata_full_counts_and_split_contract_checked': True,
              'external_runtime_receipt_sha256': external_runtime_receipt_sha256,
              'external_runtime_acceptance_is_caller_precondition_not_certified_here': True,
              'fresh_original_resource_gates_checked': 2,
              'actual_project_paths_opened': 0, 'actual_project_alias_or_Git_commit_certified': False,
              'project_metadata_array_or_FIT_admission_granted': False,
              'PUM_resource_exception_applies': False, 'models_fitted': 0}
    return matrix, report
