"""Fixed paths and policy. Importing this module performs no native operation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_current_numeric_refresh_20261025'
SRC, REP, OUT = (ROOT / kind / NS for kind in ('src', 'reports', 'results'))
MANIFEST = OUT / 'preparation_manifest.json'
SOURCE_CACHE = ROOT / 'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
PREFIX = ROOT / 'data/interim/mechanism_v2/runtime'
INVENTORY = ROOT / 'results/generalization_current_python_refresh_v2_20261025/current_python_inventory_refresh.json'
INVENTORY_MANIFEST = ROOT / 'results/generalization_current_python_refresh_v2_20261025/preparation_manifest.json'
INVENTORY_MANIFEST_SHA = 'a5764e60c81abd4ff807e007f9140db054a0ad671e1bee650bfb278f36078c4f'
DISCOVERY = ROOT / 'results/generalization_current_python_refresh_v2_20261025/current_native_discovery.json'
DISCOVERY_SHA = '1b7f635bc7fc0abb8cf02321f63b24c2ec95e4dce4dd11ec645e565ecf2b4782'
INVENTORY_STATUS = 'PASS_FRESH_CURRENT42_PYTHON_BYTES_UNCHANGED7998_PAYLOAD_COMPATIBILITY_PENDING'
OLD_PROFILE = ROOT / 'results/generalization_owned_paged_numeric_profile_20261025/preparation_manifest.json'
OLD_PROFILE_SHA = '7ea9881afeadf5c357a80df862ae1941ba9bf49a5854f30ae53f16343a4e21d1'
V4_DIR = ROOT / 'results/generalization_knowncell_parser_profile_v4_20261023'
V4_STATUS = V4_DIR / 'verified_native_status.json'
V4_STATUS_SHA = 'e1938a597c18ecf144c42724371aed2c58c8a064889fef89d5ba8a767497d821'
BASELINE = V4_DIR / 'invented_profile_receipt.json'
OLD_RUNTIME = ROOT / 'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json'
BASE_INVENTORY = ROOT / 'results/generalization_knowncell_parser_profile_20261022/payload_inventory.json'
EXPANDED_INVENTORY = ROOT / 'results/generalization_knowncell_parser_profile_v3_20261023/payload_inventory.json'
EXPECTED_PYTHON = Path('C:/Users/jaisa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
ANCHORS = {
    'python.exe': '4623dc531b0883c3e714da5cb30e9b73e12aa5145f0d92c7b191ab1dcf699dfe',
    'python3.dll': 'f0d65efd7e2bc8f036d428de0db1b4743e5ebe51f133b7a6afd10d6913b7ce60',
    'python312.dll': '9930d881ee11a91f7fd43ab28d5305194fbd2f88ea4a07661453c6885f409afd',
}
ADDITIONAL_CACHES = {
    '__pycache__/six.cpython-312.pyc': '2fc898ba80bcfb113342227edf336e24464df508595c14fc0a7d5e8890036b39',
    '__pycache__/threadpoolctl.cpython-312.pyc': 'ec9cbda12b506fe60ba25f4a4f479750478ce6b52043dea0d3cffa8fbbb699bd',
}
THREAD_ENV = {key: '1' for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')}
THREAD_ENV.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
STATUS = 'FROZEN_INVENTED_CURRENT42_PAGED_PARSER_OPTIMIZER_EXTRAS_PROFILE'
CHILD_PASS = 'PASS_INVENTED_CURRENT42_PAGED_PARSER_OPTIMIZER_EXTRAS'
PARENT_PASS = 'PASS_INVENTED_CURRENT42_RUNTIME_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
BYTES = 384 * 2**20
RESIDENT_CEILING = 192 * 2**20
DEADLINE = 150
