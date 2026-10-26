"""Pure exact-roster/full-native replacement contracts, with no I/O."""
from pathlib import PureWindowsPath
from src.generalization_current_python_refresh_20261025.contracts import sha_mapping


def full_native_contract(old, current, anchors, home, expected_changes=38):
    old,current = sha_mapping(old),sha_mapping(current)
    assert len(old) == len(current) == 42, 'Exactly42 bundled native files required'
    assert set(old) == set(current), 'Current native path roster must exactly equal prior42 paths'
    normalized = {str(PureWindowsPath(name)).casefold():name for name in current}
    assert len(normalized) == 42, 'Case-duplicate native paths'
    assert set(anchors) == {'python.exe','python3.dll','python312.dll'}
    for basename,want in anchors.items():
        name=normalized[str(PureWindowsPath(home)/basename).casefold()]
        assert current[name] == want, 'Root-reported current Python anchor mismatch: '+name
    changes={name:{'prior_sha256':old[name],'current_sha256':want}
        for name,want in current.items() if old[name] != want}
    assert len(changes) == expected_changes, 'Current discovery differs from declared38-change roster'
    return changes


def bind_discovery(value, old, anchors, home, status):
    assert value['status'] == status
    assert value['actually_loaded_DLL_origins_verified'] is False
    assert value['numerical_compatibility_established'] is False
    assert value['scientific_payload_files_read'] == 0 and value['biological_inputs_read'] is False
    changes=full_native_contract(old,value['current_native_files'],anchors,home)
    assert value['native_file_count'] == 42 and value['changed_file_count'] == 38
    assert value['unchanged_file_count'] == 4 and value['changes_from_prior_inventory'] == changes
    assert set(value['native_file_metadata']) == set(value['current_native_files'])
    return dict(value['current_native_files']),changes
