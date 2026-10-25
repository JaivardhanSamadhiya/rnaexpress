"""Only same-NPZ reload and persisted-label bits; no CORE reader or parser."""
import io
import math
import struct
from . import common as c
from src.generalization_knowncell_joint_loader_20261022 import guard,loader
from src.generalization_knowncell_array_admission_20261023.admit import bounded_array_bytes


def read_bound(name,want):
    raw=guard.guarded_bytes(c.relative(name),maximum=64*2**20)
    assert c.sha(raw)==c.valid_sha(want),name
    guard.fresh_gate();loader._committed(name,raw)
    return raw


def matrix_from_bytes(np,raw,array_certificate):
    """Original np.load(...allow_pickle=False)['features'].astype(float)."""
    assert type(raw) is bytes and len(raw)<=32*2**20 and c.sha(raw)==c.NPZ_SHA
    assert array_certificate['actual_npz_sha256']==c.NPZ_SHA
    assert array_certificate['rows']==c.SHAPE[0] and array_certificate['columns']==c.SHAPE[1]
    assert array_certificate['same_allele_feature_bytes_equal'] is True
    guard.fresh_gate()
    with np.load(io.BytesIO(raw),allow_pickle=False) as archive:
        assert archive.files==['features'],'Original sole-feature NPZ roster changed'
        guard.fresh_gate();matrix=archive['features'].astype(float)
    assert type(matrix) is np.ndarray and matrix.shape==c.SHAPE
    assert matrix.dtype.kind=='f' and matrix.dtype.itemsize==8 and matrix.dtype.isnative and not matrix.dtype.hasobject
    guard.fresh_gate();assert np.isfinite(matrix).all()
    guard.fresh_gate();bits=matrix.tobytes(order='C')
    assert len(bits)==8*c.SHAPE[0]*c.SHAPE[1] and c.sha(bits)==c.ARRAY_CAST_SHA
    assert c.sha(bits)==array_certificate['underlying_report']['post_original_astype_float_C_bytes_sha256']
    return matrix


def reload_matrix(np,array_certificate):
    raw,read=bounded_array_bytes(c.ROOT/c.NPZ,c.NPZ_SHA)
    matrix=matrix_from_bytes(np,raw,array_certificate)
    del raw
    return matrix,read


def persisted_label_contract(bundle,labels,supervisor):
    ids=[row['intervention_id'] for row in bundle['metadata']['rows']]
    assert len(ids)==len(set(ids))==c.COUNT and c.sha('|'.join(ids).encode())==c.ROW_IDS_SHA
    assert labels['status']=='PASS_CALIBRATED_ORIGINAL_PANDAS_MIKL_LABELS_NO_FIT'
    assert labels['metadata_bundle_sha256']==c.METADATA_SHA and labels['array_certificate_sha256']==c.ARRAY_CERTIFICATE_SHA
    assert labels['array_supervisor_sha256']==c.ARRAY_SUPERVISOR_SHA
    assert labels['resource_exception_applies'] is True and labels['original_resource_guards_unchanged'] is False
    assert labels['models_fitted']==labels['actual_feature_reads']==0 and labels['label_access_does_not_authorize_fitting'] is True
    assert supervisor['status']=='PASS_EXACT_LABELS_EXECUTION_PENDING_ROOT_REVIEW_AND_COMMIT' and supervisor['failure'] is None
    assert supervisor['certificate_sha256']==c.LABEL_CERTIFICATE_SHA
    for field in ('generation_manifest_sha256','run_admission_sha256','birth_sha256','approved_policy_manifest_sha256',
                  'authorization_sha256','approval_scope_sha256'):
        assert supervisor[field]==labels[field]
    assert supervisor['model_fits']==0 and supervisor['numerical_outcomes_admitted']==c.COUNT
    original=labels['labels_result'];assert original['intervention_ids']==ids
    assert original['numeric_outcome_rows_admitted']==c.COUNT
    assert original['parser']==c.labels.PARSER and original['original_truth_orientation'] is True
    assert original['old_interpreter_bitwise_parity_established'] is False
    values=original['measured_delta']
    assert type(values) is list and len(values)==len(ids) and all(type(value) is float and math.isfinite(value) for value in values)
    assert c.sha(b''.join(struct.pack('<d',value) for value in values))==original['parsed_effects_float64_sha256']==c.LABEL_BITS_SHA
    return ids
