"""Fixed software evidence and the first explicitly supported caller stage."""
from pathlib import Path

NS = 'generalization_knowncell_runtime_provider_20261023'
ROOT = Path(__file__).resolve().parents[2]
MODULE = 'src.'+NS+'.provider'
SOURCE = 'src/'+NS+'/provider.py'
PREPARATION = 'results/'+NS+'/preparation_manifest.json'
CACHE_PREFIX = ROOT/'results'/NS/'source_cache_must_remain_absent'
REQUEST = 'results/generalization_knowncell_array_admission_20261023/array_request_manifest.json'
REQUEST_STATUS = 'FROZEN_ARRAY_ONLY_REQUEST_JOINT_KNOWNCELL_NO_LABEL_OR_FIT'
PHASES = ('before_array','after_array')
SOFTWARE_STATUS = 'results/generalization_knowncell_parser_profile_v4_20261023/verified_native_status.json'
SOFTWARE_STATUS_SHA = 'e1938a597c18ecf144c42724371aed2c58c8a064889fef89d5ba8a767497d821'
PANDAS_ADMISSION = 'results/generalization_knowncell_joint_loader_20261022/pandas_admission.json'
PANDAS_ADMISSION_SHA = '923ff701e31b7c09969ff01dc63cb6560821a97176e8e85bd76cb841021c260e'
PROFILE_OUT = 'results/generalization_knowncell_parser_profile_v4_20261023/'
PROFILE_MANIFEST = PROFILE_OUT+'preparation_manifest.json'
PROFILE_MANIFEST_SHA = '61781e1ef932a2eb36a368279d96bd52b35bf0eaf286dc8f80021e42fd5a2daa'
PROFILE_ORIGIN = PROFILE_OUT+'actual_origin_receipt.json'
PROFILE_ORIGIN_SHA = 'dc3e6a1e2f31b5d6c868de7302feb0e1e719835cc370f0eb5eacb307d08b5b2b'
RUNTIME_MODULE = 'src.generalization_knowncell_parser_profile_v3_20261023.runtime'
SCIENTIFIC_PREFIX = ROOT/'data/interim/mechanism_v2/runtime'
PROVIDER_STATUS = 'PASS_FRESH_CURRENT_RUNTIME_ORIGINS_FOR_ARRAY_REQUEST'
PREPARATION_STATUS = 'DEFERRED_REAL_CURRENT_RUNTIME_PROVIDER_SOURCE_NOT_ACTUAL_RUNTIME_OR_PROJECT_ADMISSION'
BINDING_FIELDS = {'request_relative_path','request_sha256','provider_preparation_manifest_sha256',
                  'software_status_sha256','pandas_admission_sha256'}
BLOCKED = ('numpy','pandas','scipy','sklearn','torch','openvino','transformers')


def static_allowed(name):
    if name=='artifacts/'+NS+'/.gitattributes':
        return True
    if name.startswith('src/'):
        return name.endswith('.py') or name.endswith('/.gitattributes')
    if name.startswith('reports/'):
        return name.endswith('.md') or name.endswith('/.gitattributes')
    if name in ('artifacts/generalization_splicebert_runtime_compatibility_20261007/numpy_official_member_parity.json',
                'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json'):
        return True
    allowed = (NS,'generalization_current_python_20261022','generalization_knowncell_array_contract_20261022',
               'generalization_knowncell_joint_loader_20261022','generalization_knowncell_joint_gate_20261023',
               'generalization_knowncell_joint_numeric_20261022','generalization_knowncell_parser_profile_20261022',
               'generalization_knowncell_parser_profile_v3_20261023','generalization_knowncell_parser_profile_v4_20261023',
               'generalization_prelib_numpy_profile_v2_20261022','generalization_splicebert_20261007',
               'generalization_splicebert_runtime_compatibility_20261007')
    return any(name.startswith('results/'+namespace+'/') for namespace in allowed) and name.endswith(('.json','.log','/.gitattributes'))
