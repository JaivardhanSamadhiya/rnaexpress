"""Separate current42-file discovery and unchanged old scientific payload."""
from src.generalization_current_python_refresh_20261025.spec import (
    ROOT, EXPECTED_PYTHON, PREFIX, PRIOR_PYTHON, BASE_PAYLOAD, PAYLOAD,
    V4_MANIFEST, V4_STATUS, V4_DIR, OLD_RUNTIME, PRIOR_PINS,
    NEW_NATIVE_BY_BASENAME, ADDITIONAL_CACHES,
)
NS = 'generalization_current_python_refresh_v2_20261025'
SRC, REP, OUT = (ROOT/kind/NS for kind in ('src','reports','results'))
MANIFEST = OUT/'preparation_manifest.json'
DISCOVERY = OUT/'current_native_discovery.json'
SOURCE_CACHE = OUT/'never_created_source_cache'
V1_MANIFEST = ROOT/'results/generalization_current_python_refresh_20261025/preparation_manifest.json'
V1_MANIFEST_SHA = '5938ddf65c3cc9784771854efd54ba046ea09ff3a2d3a5a73144caa9d25fb241'
UNUSED_NOTE = ROOT/'reports/generalization_current_python_refresh_20261025/unused_scope_01.md'
PREPARATION_STATUS = 'PREPARED_CURRENT42_PYTHON_REFRESH_SOURCE_AND_DISCOVERY_NOT_SCIENTIFIC_INVENTORY'
DISCOVERY_STATUS = 'DISCOVERED_CURRENT42_NATIVE_BYTE_PINS_NOT_COMPATIBILITY_OR_ORIGIN_PROOF'
INVENTORY_STATUS = 'PASS_FRESH_CURRENT42_PYTHON_BYTES_UNCHANGED7998_PAYLOAD_COMPATIBILITY_PENDING'
