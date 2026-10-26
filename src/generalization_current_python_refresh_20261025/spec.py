"""Fixed identities from existing metadata and root-reported new fingerprints."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_current_python_refresh_20261025'
SRC, REP, OUT = (ROOT / kind / NS for kind in ('src', 'reports', 'results'))
MANIFEST = OUT / 'preparation_manifest.json'
SOURCE_CACHE = OUT / 'never_created_source_cache'
EXPECTED_PYTHON = Path('C:/Users/jaisa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
PREFIX = ROOT / 'data/interim/mechanism_v2/runtime'
PRIOR_PYTHON = 'results/generalization_current_python_20261022/current_python_inventory.json'
BASE_PAYLOAD = 'results/generalization_knowncell_parser_profile_20261022/payload_inventory.json'
PAYLOAD = 'results/generalization_knowncell_parser_profile_v3_20261023/payload_inventory.json'
V4_MANIFEST = 'results/generalization_knowncell_parser_profile_v4_20261023/preparation_manifest.json'
V4_STATUS = 'results/generalization_knowncell_parser_profile_v4_20261023/verified_native_status.json'
V4_DIR = 'results/generalization_knowncell_parser_profile_v4_20261023/'
OLD_RUNTIME = 'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json'
PRIOR_PINS = {
    PRIOR_PYTHON: 'db59c8f19ed8fc3a4a2adcf96b240146c48ba0f1c649e2e2d48f41e5dcf45d59',
    BASE_PAYLOAD: 'b08697fe556bfe8109ace7feb823886aa147d6854cf6ecdc65113b7d8d71fff2',
    PAYLOAD: '026274a6dcb9a494c44c679cccb12a5bbdce3cdae085e37578ed877eb832c842',
    V4_MANIFEST: '61781e1ef932a2eb36a368279d96bd52b35bf0eaf286dc8f80021e42fd5a2daa',
    V4_STATUS: 'e1938a597c18ecf144c42724371aed2c58c8a064889fef89d5ba8a767497d821',
    V4_DIR+'supervisor_receipt.json': 'd7c70d0670df090a8aa388985ff35e2ada9ee53bdb06048217176787c233a9ed',
    V4_DIR+'invented_profile_receipt.json': 'dfc00f70af703437b394f74fbd92f8f81e0926b82a0be5b95a01cabebd29c312',
    V4_DIR+'actual_origin_receipt.json': 'dc3e6a1e2f31b5d6c868de7302feb0e1e719835cc370f0eb5eacb307d08b5b2b',
    V4_DIR+'pandas_admission_candidate.json': '923ff701e31b7c09969ff01dc63cb6560821a97176e8e85bd76cb841021c260e',
    OLD_RUNTIME: '36d103ee3bbfff30bb1af04a3fa4f640adf61dbedddf1247ceea9d97e5bad039',
}
NEW_NATIVE_BY_BASENAME = {
    'python.exe': '4623dc531b0883c3e714da5cb30e9b73e12aa5145f0d92c7b191ab1dcf699dfe',
    'python3.dll': 'f0d65efd7e2bc8f036d428de0db1b4743e5ebe51f133b7a6afd10d6913b7ce60',
    'python312.dll': '9930d881ee11a91f7fd43ab28d5305194fbd2f88ea4a07661453c6885f409afd',
}
ADDITIONAL_CACHES = {
    '__pycache__/six.cpython-312.pyc': '2fc898ba80bcfb113342227edf336e24464df508595c14fc0a7d5e8890036b39',
    '__pycache__/threadpoolctl.cpython-312.pyc': 'ec9cbda12b506fe60ba25f4a4f479750478ce6b52043dea0d3cffa8fbbb699bd',
}
PREPARATION_STATUS = 'PREPARED_CURRENT_PYTHON_REFRESH_SOURCE_ONLY_NO_INVENTORY_OR_COMPATIBILITY'
INVENTORY_STATUS = 'PASS_FRESH_CURRENT_PYTHON_BYTES_UNCHANGED_SELECTED_PAYLOAD_COMPATIBILITY_PENDING'
V4_STATUS_VALUE = 'VERIFIED_CURRENT_RUNTIME_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
