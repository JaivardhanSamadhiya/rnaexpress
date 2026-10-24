from pathlib import Path

NS='generalization_knowncell_joint_input_bridge_20261023'
ROOT=Path(__file__).resolve().parents[2]
SRC,REP,OUT=[ROOT/name/NS for name in ('src','reports','results')]
READY='results/'+NS+'/preparation_manifest.json'
ORIGINAL_MODULE='src.cross_assay_20260927.models'
MODEL_SOURCE='src/cross_assay_20260927/models.py'
MODEL_SHA='a7d43f49c37e0e2a86e5c9c64cbf97bca78aabab36a007f10f886fb916d54d71'
COMMON_SOURCE='src/cross_assay_20260927/common.py'
COMMON_SHA='dfb658f9fd437bae5fef2b1ae33ae0bd9167a1b118394756bab8e81f8b6745dc'
SEED=20260927
CACHE_PREFIX=ROOT/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
METADATA_PATH='results/generalization_knowncell_joint_loader_20261022/admitted_metadata.json'
ARRAY_PATH='results/generalization_knowncell_joint_loader_20261022/simple102_array_admission.json'
FIT_PATH='results/generalization_knowncell_joint_loader_20261022/fit_label_admission_manifest.json'
CORE_PATH='results/probabilistic_ranking_20260928/candidate_index.csv'
CORE_SHA='773d6145bbe4b17ff50597e47eba13f0b2977a3ddf541a1b238adcb7ff433e3d'
NPZ_SHA='490ab90c1289ea50a75ff6960b9a979f2f2bd747b1c9419ed7c085383272c8a6'
ROW_IDS_SHA='d5a603fb35e25af47d60cc10ac41ae18458c094b855de29561cdecb5edaa0ce2'
SOFTWARE_STATUS_SHA='e1938a597c18ecf144c42724371aed2c58c8a064889fef89d5ba8a767497d821'
PANDAS_SHA='923ff701e31b7c09969ff01dc63cb6560821a97176e8e85bd76cb841021c260e'
V4_ORIGIN_SHA='dc3e6a1e2f31b5d6c868de7302feb0e1e719835cc370f0eb5eacb307d08b5b2b'
NUMPY_PATH=ROOT/'data/interim/mechanism_v2/runtime/numpy/__init__.py'
NUMPY_SHA='150b19558caf78c0e3cc6994ec652399e972595ca649cea1a69c801ef23e4b1c'
ARRAY_STATUS='PASS_EXACT_FROZEN_SIMPLE102_ROWS_VALUES_AND_ALLELE_PARITY'
PROVIDER_STATUS='PASS_FRESH_CURRENT_RUNTIME_ORIGINS_FOR_ARRAY_REQUEST'
COUNTS={'rows':13781,'columns':102}
BINDING_HASHES=('metadata_bundle_sha256','array_certificate_sha256','fit_label_admission_sha256',
    'runtime_binding_sha256','fit_source_manifest_sha256','native_profile_receipt_sha256',
    'numeric_source_manifest_sha256','lifecycle_v2_manifest_sha256')
