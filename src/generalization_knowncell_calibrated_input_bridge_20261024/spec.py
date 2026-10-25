"""Fixed source/input identities; future root bindings are separate objects."""
from src.generalization_knowncell_joint_input_bridge_20261023.spec import (
    ROOT,CORE_SHA,NPZ_SHA,ROW_IDS_SHA,SOFTWARE_STATUS_SHA,PANDAS_SHA,V4_ORIGIN_SHA,
    NUMPY_PATH,NUMPY_SHA,MODEL_SHA,METADATA_PATH,COUNTS,ARRAY_STATUS,
)

NS='generalization_knowncell_calibrated_input_bridge_20261024'
SRC,REP,OUT=[ROOT/name/NS for name in ('src','reports','results')]
READY='results/'+NS+'/preparation_manifest.json'
READY_STATUS='SOURCE_ONLY_CALIBRATED_SUPPLIED_INPUT_BRIDGE_NOT_RUNTIME_INPUT_OR_FIT_ADMISSION'
ARRAY_PATH='results/generalization_knowncell_array_execution_20261024/array_admission_certificate.json'
ARRAY_SHA='8d8d39763b6c9fc226ba7f616fe891dad37556ac83694d39f10667c24aefb9fa'
LABEL_PATH='results/generalization_knowncell_labels_execution_20261024/original_pandas_label_certificate.json'
LABEL_STATUS='PASS_CALIBRATED_ORIGINAL_PANDAS_MIKL_LABELS_NO_FIT'
LABEL_REQUEST='results/generalization_knowncell_labels_execution_20261024/label_request_manifest.json'
LABEL_PROVIDER_STATUS='PASS_FRESH_CURRENT_RUNTIME_ORIGINS_FOR_LABEL_REQUEST'
PARSER='original_pandas_default_read_csv_low_memory_False_then_to_numpy_float'
POLICY_SHA='a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9'
AUTH_SHA='b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3'
SCOPE_SHA='c40b929187a35199e88523ab5c6b351789c45fddb3aebe6dcf68172684ce6495'
STAGES=('prefit','fit','replay','evaluation')
BINDING_STATUS='FROZEN_ROOT_CALIBRATED_SUPPLIED_INPUT_BINDINGS_NOT_FIT_PERMISSION'
STAGE_PROOF_STATUS='PASS_FRESH_CURRENT_RUNTIME_ORIGINS_FOR_KNOWNCELL_STAGE'
HASH_FIELDS=('metadata_bundle_sha256','array_certificate_sha256','array_supervisor_sha256',
    'label_certificate_sha256','runtime_binding_sha256','fit_source_manifest_sha256',
    'numeric_source_manifest_sha256','lifecycle_v2_manifest_sha256','native_profile_receipt_sha256',
    'bridge_readiness_sha256','reviewed_controller_admission_sha256',
    'reviewed_controller_source_sha256','caller_birth_sha256','current_stage_origin_proof_sha256')
LABEL_KEYS={'intervention_ids','measured_delta','parsed_effects_float64_sha256',
    'numeric_outcome_rows_admitted','parser','original_truth_orientation',
    'old_interpreter_bitwise_parity_established',
    'pinned_pandas_currentPython_and_invented_original_parser_test_certificate_required'}


def binding_path(stage):
    assert stage in STAGES
    return 'results/'+NS+'/root_bindings_'+stage+'.json'
