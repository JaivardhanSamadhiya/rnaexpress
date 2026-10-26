"""Pure supplied-metadata contracts, never a software scan or admission."""
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from . import spec


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(',', ':'), ensure_ascii=True).encode('utf8')


def decode(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            assert key not in value, 'Duplicate JSON key: ' + key
            value[key] = item
        return value
    value = json.loads(raw, object_pairs_hook=pairs,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    assert isinstance(value, dict)
    return value


def pin_map(value):
    assert isinstance(value, dict) and value
    assert all(isinstance(key, str) and isinstance(want, str) and len(want) == 64
               and all(x in '0123456789abcdef' for x in want) for key, want in value.items())
    return dict(value)


def relative_key(key):
    assert isinstance(key, str) and key and '\\' not in key and ':' not in key
    path = PurePosixPath(key)
    assert not path.is_absolute() and all(x not in ('', '.', '..') for x in path.parts)
    assert path.as_posix() == key
    return key


def native_maps(inventory, discovery):
    """The supplied current42 discovery is fixed, not arbitrary future hashes."""
    current = pin_map(inventory['current_bundled_stdlib_native_files'])
    assert len(current) == 42 and current == discovery['current_native_files']
    assert inventory['current_native_file_count'] == 42
    assert inventory['changed_native_file_count'] == 38
    assert inventory['native_discovery_sha256'] == spec.DISCOVERY_SHA
    normalized = {str(PureWindowsPath(key)).casefold(): key for key in current}
    assert len(normalized) == 42, 'Native path aliases'
    home = PureWindowsPath(str(spec.EXPECTED_PYTHON.parent))
    three = {}
    for basename, want in spec.ANCHORS.items():
        original = normalized[str(home / basename).casefold()]
        assert current[original] == want
        three[original] = want
    return current, three


def inventory_contract(inventory, discovery, base, expanded, runtime):
    assert inventory['status'] == spec.INVENTORY_STATUS, 'Successful fresh inventory is mandatory'
    assert inventory['private_material_verification_sha256']==spec.MATERIAL_VERIFICATION_SHA
    assert inventory['storage_relocation_explicitly_verified'] is True
    assert Path(inventory['actual_selected_scientific_prefix']).resolve()==spec.PREFIX.resolve()
    assert inventory['initial_preparation_manifest_sha256'] == spec.INVENTORY_MANIFEST_SHA
    assert inventory['scientific_packages_imported'] is False
    assert inventory['actually_loaded_python_DLL_origins_verified'] is False
    assert inventory['numerical_compatibility_established'] is False
    assert inventory['biological_inputs_read'] is False
    assert inventory['biological_model_fits'] == 0 and inventory['stage_authority_granted'] is False
    assert inventory['historical_V4_acceptance_reused_for_new_Python'] is False
    current, three = native_maps(inventory, discovery)
    files = pin_map(inventory['selected_scientific_payload_files'])
    assert len(files) == 7998 and inventory['selected_scientific_payload_file_count'] == 7998
    assert files == expanded['files'] == dict(base['files'], **spec.ADDITIONAL_CACHES)
    assert len(base['files']) == 7996
    assert inventory['two_explicit_possible_cache_payloads'] == spec.ADDITIONAL_CACHES
    assert inventory['unchanged_versions_from_package_metadata'] == {'numpy': '1.26.4', 'pandas': '2.2.3', 'scipy': '1.14.1'}
    for name, want in files.items():
        relative_key(name)
        assert runtime['files'][name] == want
    assert expanded['native_files'] == base['native_files']
    native = {name: want for name, want in files.items() if Path(name).suffix.lower() in ('.dll', '.pyd')}
    assert native == expanded['native_files']
    return files, native, current, three


def compare_results(actual, expected):
    """Exact canonical comparisons of all three unchanged original results."""
    assert actual['parser']['status'] == 'PASS_INVENTED_EXACT_DEFERRED_PARSER'
    optimizer = actual['optimizer']
    assert optimizer['status'] == 'PASS_INVENTED_SCIPY_SOLVER_REFERENCE_AND_SCORER'
    assert optimizer['scipy_optimizer_units'] == 12 and optimizer['biological_model_fits'] == 0
    assert set(actual) == {'parser', 'optimizer', 'extra_deferred_native_contracts'}
    return {key: _equal(actual[key], expected[key]) for key in actual}


def _equal(actual, expected):
    assert canonical(actual) == canonical(expected), 'Original invented profile result differs'
    return digest(canonical(actual))


def resource_failure(memory, elapsed, *, startup=False):
    import math
    assert math.isfinite(elapsed) and elapsed >= 0
    if memory['physical_available'] < (512 if startup else 256) * 2**20:
        return 'physical reserve'
    if memory['commit_headroom'] < (1920 * 2**20 if startup else 2**30):
        return 'global commit reserve'
    if memory['disk_available'] < 2**30:
        return 'disk reserve'
    if elapsed > spec.DEADLINE:
        return '150-second diagnostic deadline'


def validate_child(result, expected_results, expected_sha, parent_pid, child_pid, expected_hash):
    assert result['status'] == spec.CHILD_PASS
    assert result['parent_pid'] == parent_pid and result['child_pid'] == child_pid
    assert result['preparation_manifest_sha256'] == expected_sha
    assert result['bytes'] == spec.BYTES and result['hashes'] == [expected_hash] * 3
    assert result['invented_optimizer_units'] == 12
    assert result['biological_rows_read'] == result['biological_model_fits'] == 0
    assert result['canonical_result_sha256'] == compare_results(result['results'], expected_results)
