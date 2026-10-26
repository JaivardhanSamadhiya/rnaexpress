"""Pure supplied-metadata contracts; no paths are opened by these functions."""
import hashlib
import json
from pathlib import PurePosixPath, PureWindowsPath


def digest(raw):
    assert isinstance(raw, bytes)
    return hashlib.sha256(raw).hexdigest()


def valid_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def decode(raw):
    def unique(items):
        result = {}
        for key, value in items:
            assert key not in result, 'Duplicate JSON key: '+key
            result[key] = value
        return result
    def constant(value):
        raise AssertionError('Nonfinite JSON constant: '+value)
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=constant)
    assert isinstance(value, dict), 'Expected JSON object'
    return value


def relative_key(name):
    assert isinstance(name, str) and name and '\\' not in name
    path = PurePosixPath(name)
    assert not path.is_absolute() and '..' not in path.parts and '.' not in path.parts
    assert ':' not in name and str(path) == name, 'Noncanonical relative path: '+name
    return name


def sha_mapping(value):
    assert isinstance(value, dict) and value
    assert all(isinstance(name, str) and valid_sha(want) for name, want in value.items())
    return dict(value)


def payload_contract(base, expanded, full, caches, components):
    original = sha_mapping(base['files'])
    actual = sha_mapping(expanded['files'])
    assert len(original) == base['file_count'] == 7996
    assert len(actual) == expanded['file_count'] == 7998
    assert not set(original) & set(caches)
    assert actual == dict(original, **caches), 'Payload may expand only by the two fixed old caches'
    assert set(components) == {key.split('/')[0] for key in original}
    for key, want in actual.items():
        relative_key(key)
        assert full['files'].get(key) == want, 'Not the original runtime byte pin: '+key
    assert expanded['versions'] == base['versions'] == {'numpy':'1.26.4','pandas':'2.2.3','scipy':'1.14.1'}
    assert expanded['current_python_native_files'] == base['current_python_native_files']
    return actual


def compare_inventory(expected, observed, label):
    expected, observed = sha_mapping(expected), sha_mapping(observed)
    assert set(expected) == set(observed), label+' membership mismatch'
    for name, want in expected.items():
        assert observed[name] == want, label+' byte mismatch: '+name
    return len(observed)


def native_contract(old, observed, replacements, home):
    """Only the three predeclared CPython files may differ from prior native pins."""
    old, observed = sha_mapping(old), sha_mapping(observed)
    assert set(old) == set(observed), 'Bundled native roster changed'
    assert set(replacements) == {'python.exe','python3.dll','python312.dll'}
    expected_paths = {str(PureWindowsPath(home)/name): want for name, want in replacements.items()}
    # Windows path identity is deliberately lexical/case-normalized here; actual
    # resolved path containment/symlink validation belongs to the I/O producer.
    by_key = {str(PureWindowsPath(name)).casefold(): name for name in old}
    assert len(by_key) == len(old), 'Case-duplicate native path'
    changes = {}
    for expected_path, want in expected_paths.items():
        key = expected_path.casefold()
        assert key in by_key, 'Expected Python file absent: '+expected_path
        name = by_key[key]
        assert observed[name] == want, 'Wrong current Python fingerprint: '+name
        assert old[name] != want, 'Declared changed Python byte pin did not change'
        changes[name] = {'prior_sha256':old[name], 'current_sha256':want}
    assert len(changes) == 3
    for name in set(old)-set(changes):
        assert observed[name] == old[name], 'Additional native drift: '+name
    return changes


def accepted_v4(status, supervisor, completion, candidate, hashes, expected_manifest):
    assert status['status'] == 'VERIFIED_CURRENT_RUNTIME_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
    assert status['initial_manifest_sha256'] == expected_manifest
    assert status['metadata_array_label_and_fit_admissions_granted_here'] is False
    assert supervisor['status'] == 'PASS_BOUNDED_ONE_THREAD_INVENTED_PANDAS_SCIPY_PROFILE_V4'
    assert supervisor['exit_code'] == 0 and supervisor['failure'] is None
    assert supervisor['manifest_observed_final_sha256'] == expected_manifest
    assert completion['status'] == 'PASS_INVENTED_PANDAS_SCIPY_PROFILE_CURRENT_PYTHON_V4'
    assert candidate['status'] == 'PASS_PINNED_PANDAS223_CURRENT_PYTHON_AND_INVENTED_ORIGINAL_PARSER'
    assert supervisor['invented_completion_sha256'] == hashes['invented_profile_receipt.json']
    assert completion['actual_origin_receipt_sha256'] == candidate['actual_origin_receipt_sha256'] == hashes['actual_origin_receipt.json']
    assert completion['pandas_admission_candidate_sha256'] == hashes['pandas_admission_candidate.json']
    for name, want in status['verified_files'].items():
        assert hashes[name] == want, 'V4 acceptance byte-chain mismatch: '+name
    assert candidate['old_interpreter_bitwise_parity_established'] is False
    return True
