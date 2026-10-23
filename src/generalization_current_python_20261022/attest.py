"""Verify unchanged scientific-prefix bytes without importing numerical packages."""
import datetime
import json
from pathlib import Path
import subprocess
import sys

from src.generalization_prelib_numpy_profile_20261022.invented import ROOT, sha
from src.generalization_pum_process_probe_20261021 import headless
from src.generalization_splicebert_runtime_compatibility_20261007 import launcher

OUT = ROOT / 'results/generalization_current_python_20261022'
ATTESTATION = OUT / 'current_python_inventory.json'
EXPECTED_PYTHON = Path('C:/Users/jaisa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')


def committed(path):
    assert headless.GitFacade(subprocess).check_output(
        ['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT
    ) == path.read_bytes(), str(path)


def inventory_prefix(runtime):
    prefix = launcher.PREFIX.resolve()
    actual = {p.relative_to(prefix).as_posix() for p in prefix.rglob('*') if p.is_file()}
    assert actual == set(runtime['files']), 'Unexpected or missing scientific-prefix files'
    for rel, want in runtime['files'].items():
        path = prefix / rel
        assert not path.is_symlink() and path.resolve().is_relative_to(prefix)
        assert sha(path) == want, rel
    for rel, want in runtime['numpy_native_files'].items():
        assert runtime['files'][rel] == want
    return len(actual)


def native_python(expected):
    """Loaded Python DLL basenames must resolve to the attested bundled paths."""
    assert Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve()
    observed = {}
    for name, want in expected.items():
        path = Path(name).resolve()
        assert path.parent == EXPECTED_PYTHON.resolve().parent
        assert sha(path) == want, name
    by_name = {Path(name).name.casefold(): Path(name).resolve() for name in expected}
    for path in launcher.process_native_paths():
        key = path.name.casefold()
        if key.startswith('python') and path.suffix.casefold() == '.dll':
            assert key in by_name and path == by_name[key], str(path)
            observed[str(path)] = sha(path)
    assert by_name['python312.dll'] in [Path(x) for x in observed]
    return observed


def prepare():
    launcher.clean_import_state()
    assert sys.version_info[:2] == (3, 12) and sys.implementation.cache_tag == 'cpython-312'
    assert Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve()
    old_path = launcher.RUNTIME_RECEIPT
    committed(old_path)
    runtime = json.loads(old_path.read_bytes())
    assert runtime['status'] == 'PASS' and runtime['numpy_version'] == '1.26.4'
    assert Path(runtime['runtime_path']).resolve() == launcher.PREFIX.resolve()
    assert Path(runtime['python_executable']).resolve() == EXPECTED_PYTHON.resolve()
    current = {name: sha(name) for name in runtime['python_native_files']}
    assert {Path(x).name for x in current} == {'python.exe', 'python3.dll', 'python312.dll'}
    changes = {name: {'old_sha256': old, 'current_sha256': current[name]}
               for name, old in runtime['python_native_files'].items() if current[name] != old}
    count = inventory_prefix(runtime)
    loaded = native_python(current)
    receipt = {
        'UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'PASS_CURRENT_PYTHON_INVENTORY_UNCHANGED_PREFIX_COMPATIBILITY_PENDING',
        'python_executable': str(EXPECTED_PYTHON.resolve()), 'python_version': sys.version,
        'python_cache_tag': sys.implementation.cache_tag,
        'python_native_files': current, 'actually_loaded_python_DLLs': loaded,
        'changes_from_old_certificate': changes,
        'old_runtime_receipt': old_path.relative_to(ROOT).as_posix(),
        'old_runtime_receipt_sha256': sha(old_path),
        'unchanged_scientific_prefix_file_count': count,
        'unchanged_numpy_native_files': runtime['numpy_native_files'],
        'workspace_bundle_version_reported_by_dependency_tool': '26.1015.12040',
        'version_source': 'Codex load_workspace_dependencies response, 22 October2026 local',
        'old_exact_python_patch_version_known': False,
        'cause_of_binary_change_established': False,
        'numerical_packages_imported': False, 'numerical_compatibility_established': False,
        'biological_inputs_read': False, 'biological_models_fit': 0,
        'original_sources_certificates_prefix_and_guards_changed': False,
        'source_sha256': sha(__file__),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / '.gitattributes').write_text('* -text\n', encoding='utf-8')
    with ATTESTATION.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print('CURRENT_PYTHON_INVENTORY_ONLY', count, len(changes), sha(ATTESTATION), flush=True)


def check():
    """Fresh-process additive check; does not pretend the old Python pins pass."""
    committed(ATTESTATION)
    receipt = json.loads(ATTESTATION.read_bytes())
    assert receipt['status'] == 'PASS_CURRENT_PYTHON_INVENTORY_UNCHANGED_PREFIX_COMPATIBILITY_PENDING'
    assert receipt['source_sha256'] == sha(__file__)
    assert receipt['python_version'] == sys.version
    assert receipt['old_runtime_receipt_sha256'] == sha(launcher.RUNTIME_RECEIPT)
    committed(launcher.RUNTIME_RECEIPT)
    runtime = json.loads(launcher.RUNTIME_RECEIPT.read_bytes())
    assert inventory_prefix(runtime) == receipt['unchanged_scientific_prefix_file_count']
    loaded = native_python(receipt['python_native_files'])
    return runtime, {'current_python_inventory_sha256': sha(ATTESTATION),
                     'python_version': sys.version, 'actually_loaded_python_DLLs': loaded,
                     'current_python_native_files': receipt['python_native_files'],
                     'old_python_hash_contract_passes': False,
                     'unchanged_old_NumPy_file_contract_passes': True}


if __name__ == '__main__':
    assert sys.argv[1:] == ['prepare']
    prepare()
