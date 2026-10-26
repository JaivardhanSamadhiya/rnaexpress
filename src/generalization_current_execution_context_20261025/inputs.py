"""Supplied historical input equivalence, never a reader or runtime admission."""
import math
import struct
from . import contracts as c,spec
from .plan import from_supplied
from src.generalization_knowncell_joint_implementation_20261022.contracts import ids_sha


def validate_supplied(np,matrix,raws,reference_raw):
    """Pure library boundary: current owned loading/authority is still external."""
    reference=c.decode(reference_raw);objects=c.check_supplied(raws,reference)
    for key,want in spec.DATA_PINS.items():assert reference['file_sha256'][key]==want
    assert reference['historical_runtime_anchor_sha256']==spec.HISTORICAL_ARRAY_ANCHOR
    assert reference['historical_native_profile_origin_sha256']==spec.HISTORICAL_PROFILE_ORIGIN
    plan=from_supplied(raws['prefit'],raws['projection'],reference_raw)
    bundle,array,labels=objects['metadata'],objects['array'],objects['labels']
    assert bundle['status']=='PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION'
    rows=bundle['metadata']['rows'];assert type(rows) is list and len(rows)==spec.ROW_COUNT
    ids=[row['intervention_id'] for row in rows]
    assert len(ids)==len(set(ids)) and ids_sha(rows)==spec.ROW_IDS_SHA
    actual=plan.actual_document();assert actual['all_row_ids']==ids
    assert actual['counts']['all_rows']==len(ids)
    assert array['status']=='PASS_EXACT_FROZEN_SIMPLE102_ROWS_VALUES_AND_ALLELE_PARITY'
    assert array['same_allele_feature_bytes_equal'] is True and array['original_row_ids_sha256']==spec.ROW_IDS_SHA
    assert array['rows']==len(ids) and array['columns']==spec.FEATURE_WIDTH
    assert labels['status']=='PASS_CALIBRATED_ORIGINAL_PANDAS_MIKL_LABELS_NO_FIT'
    original=labels['labels_result']
    assert original['intervention_ids']==ids and original['numeric_outcome_rows_admitted']==len(ids)
    assert original['original_truth_orientation'] is True and original['old_interpreter_bitwise_parity_established'] is False
    values=original['measured_delta'];label_bits=c.pack_labels(ids,values)
    assert c.digest(label_bits)==original['parsed_effects_float64_sha256']==spec.LABEL_BITS_SHA
    assert type(matrix) is np.ndarray and matrix.shape==(len(ids),spec.FEATURE_WIDTH)
    assert matrix.dtype.kind=='f' and matrix.dtype.itemsize==8 and matrix.dtype.isnative and not matrix.dtype.hasobject
    raw=matrix.tobytes(order='C')
    assert type(raw) is bytes and len(raw)==8*len(ids)*spec.FEATURE_WIDTH
    assert all(math.isfinite(value) for (value,) in struct.iter_unpack('<d',raw))
    assert c.digest(raw)==array['underlying_report']['post_original_astype_float_C_bytes_sha256']==spec.FEATURE_BYTES_SHA
    allele_bytes={};width=8*spec.FEATURE_WIDTH
    for index,row in enumerate(rows):
        allele=(row['parent_sequence'],row['mutant_sequence']);bits=raw[index*width:(index+1)*width]
        assert all(type(value) is str and value for value in allele)
        assert allele not in allele_bytes or allele_bytes[allele]==bits,'Identical allele has different feature bytes'
        allele_bytes[allele]=bits
    admissions=c.decode(c.canonical(actual['input_admission_bindings']))
    for key,want in spec.STABLE_SCIENTIFIC_BINDINGS.items():assert admissions[key]==want
    assert admissions['runtime_binding_sha256']==reference['historical_runtime_anchor_sha256']
    for key,data_key in (('feature_admission_sha256','array'),('label_admission_sha256','labels')):
        assert admissions[key]==reference['file_sha256'][data_key]
    assert admissions['input_row_ids_sha256']==ids_sha(rows)
    assert admissions['input_features_sha256']==c.digest(c.canonical({'shape':[len(ids),spec.FEATURE_WIDTH],'dtype':'float64','order':'C'})+raw)
    assert admissions['input_effects_sha256']==c.digest(c.canonical({'shape':[len(ids)],'dtype':'float64','order':'C'})+label_bits)
    return {'metadata':rows,'features':matrix,'effects':dict(zip(ids,values)),'admissions':admissions,'plan':plan,
        'historical_input_report':{'status':'VALIDATED_SUPPLIED_HISTORICAL_BITS_NOT_CURRENT_RUNTIME_OR_FIT_ADMISSION',
            'row_count':len(ids),'feature_bytes_sha256':c.digest(raw),'label_bits_sha256':c.digest(label_bits),
            'historical_reference_sha256':c.digest(reference_raw),'scientific_plan_identity_sha256':c.digest(c.canonical(plan.identity())),
            'historical_runtime_anchor_sha256':reference['historical_runtime_anchor_sha256'],
            'no_CORE_read_label_reparse_or_recomputation':True,'current_native_identity_verified_here':False,
            'actual_stage_authority_granted_here':False}}
