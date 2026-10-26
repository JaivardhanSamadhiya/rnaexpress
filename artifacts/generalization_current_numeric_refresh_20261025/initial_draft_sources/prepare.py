"""Future final freeze requires a successful committed fresh inventory first."""
import ast
import importlib
import json
from pathlib import Path
import subprocess
import sys
from . import spec
from .contracts import decode, digest, inventory_contract, relative_key


def merge(files, name, want):
    relative_key(name)
    assert name not in files or files[name] == want, 'Conflicting source/static pin: ' + name
    files[name] = want


def checked_manifest(path, expected_sha):
    raw = path.read_bytes()
    assert digest(raw) == expected_sha
    value = decode(raw)
    for name, want in value['files'].items():
        relative_key(name)
        candidate = spec.ROOT / name
        assert not candidate.is_symlink() and digest(candidate.read_bytes()) == want, name
    return value


def run(expected_inventory_sha):
    from .probe import source_mode
    source_mode()
    assert not spec.MANIFEST.exists(), 'No overwrite or resume'
    assert isinstance(expected_inventory_sha, str) and len(expected_inventory_sha) == 64
    # The failed/absent inventory cannot be turned into compatibility evidence.
    inventory_raw = spec.INVENTORY.read_bytes()
    assert digest(inventory_raw) == expected_inventory_sha
    inventory = decode(inventory_raw)
    assert inventory['status'] == spec.INVENTORY_STATUS
    committed = subprocess.check_output(['git', 'show', 'HEAD:' + spec.INVENTORY.relative_to(spec.ROOT).as_posix()],
                                        cwd=spec.ROOT, creationflags=0x8 if sys.platform == 'win32' else 0)
    assert committed == inventory_raw, 'Fresh successful inventory must be committed'
    old = checked_manifest(spec.OLD_PROFILE, spec.OLD_PROFILE_SHA)
    fresh = checked_manifest(spec.INVENTORY_MANIFEST, spec.INVENTORY_MANIFEST_SHA)
    assert digest(spec.DISCOVERY.read_bytes()) == spec.DISCOVERY_SHA
    discovery = decode(spec.DISCOVERY.read_bytes())
    base = decode(spec.BASE_INVENTORY.read_bytes())
    expanded = decode(spec.EXPANDED_INVENTORY.read_bytes())
    runtime = decode(spec.OLD_RUNTIME.read_bytes())
    files, _, _, _ = inventory_contract(inventory, discovery, base, expanded, runtime)
    assert len(files) == 7998
    assert digest(spec.V4_STATUS.read_bytes()) == spec.V4_STATUS_SHA
    accepted = decode(spec.V4_STATUS.read_bytes())
    assert accepted['status'] == 'VERIFIED_CURRENT_RUNTIME_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
    for name, want in accepted['verified_files'].items():
        assert digest((spec.V4_DIR / name).read_bytes()) == want, name
    receipt_path = spec.OUT / 'synthetic_tests_receipt.json'
    tested = decode(receipt_path.read_bytes())
    assert tested['status'] == 'PASS_STDLIB_INVENTED_CURRENT42_NUMERIC_SOURCE_CONTRACTS'
    assert tested['failures'] == tested['errors'] == 0 and tested['tests'] >= 12
    assert tested['scientific_imports_native_jobs_biological_reads'] == 0
    own = {path.relative_to(spec.ROOT).as_posix(): digest(path.read_bytes()) for path in spec.SRC.glob('*.py')}
    assert tested['source_sha256'] == own
    result_files = dict(old['files'])
    for name, want in fresh['files'].items():
        merge(result_files, name, want)
    extras = [spec.OLD_PROFILE, spec.INVENTORY_MANIFEST, spec.INVENTORY, receipt_path]
    extras += [path for folder in (spec.SRC, spec.REP, spec.OUT, spec.ROOT / 'artifacts' / spec.NS)
               for path in folder.iterdir() if path.is_file()]
    # Import sources only; never execute profile/runtime/bootstrap functions.
    for suffix in ('runtime', 'probe', 'tests', 'prepare'):
        importlib.import_module('src.' + spec.NS + '.' + suffix)
    for module_name in (
        'src.generalization_current_python_20261022.attest',
        'src.generalization_knowncell_parser_profile_20261022.parser_profile',
        'src.generalization_knowncell_parser_profile_20261022.optimizer_profile',
        'src.generalization_knowncell_parser_profile_20261022.extras_v2',
        'src.generalization_knowncell_parser_profile_v3_20261023.cache_integrity',
    ):
        importlib.import_module(module_name)
    imported = {}
    for name, module in tuple(sys.modules.items()):
        candidate = getattr(module, '__file__', None)
        if not candidate:
            continue
        path = Path(candidate).resolve()
        if path.is_relative_to(spec.ROOT) and path.suffix == '.py':
            key = path.relative_to(spec.ROOT).as_posix()
            imported[name] = key
            extras.append(path)
            parent = path.parent
            while parent.is_relative_to(spec.ROOT / 'src'):
                init = parent / '__init__.py'
                if init.exists():
                    extras.append(init)
                parent = parent.parent
    for path in extras:
        assert not path.is_symlink()
        key = path.relative_to(spec.ROOT).as_posix()
        merge(result_files, key, digest(path.read_bytes()))
    for name in result_files:
        if name.endswith('.py'):
            ast.parse((spec.ROOT / name).read_text(encoding='utf8'), filename=name)
    value = {
        'status': spec.STATUS, 'namespace': spec.NS, 'files': dict(sorted(result_files.items())),
        'file_count': len(result_files), 'source_import_closure': imported,
        'fresh_inventory_sha256': expected_inventory_sha, 'current_native_file_count': 42,
        'selected_scientific_payload_file_count': 7998,
        'original_V4_reference_results_are_historical_not_current_admission': True,
        'invented_optimizer_units': 12, 'padding_bytes': spec.BYTES,
        'requested_working_set_maximum': 190 * 2**20, 'measured_resident_ceiling': spec.RESIDENT_CEILING,
        'private_process_cap': 768 * 2**20, 'job_cap': 896 * 2**20, 'active_process_limit': 2,
        'startup_physical_floor': 512 * 2**20, 'live_physical_floor': 256 * 2**20,
        'startup_commit_headroom': 1920 * 2**20, 'live_commit_and_disk_floor': 2**30,
        'deadline_seconds': spec.DEADLINE, 'threads': 1, 'automatic_retry': False,
        'unused_scientific_payloads_freshly_rehashed_by_this_prepare': False,
        'biological_datasets_read': False, 'biological_model_fits': 0,
        'numerical_native_profile_executed': False, 'biological_admission_granted': False,
    }
    with spec.MANIFEST.open('x', encoding='utf8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    print('CURRENT42_INVENTED_PROFILE_FROZEN_NOT_EXECUTED', len(result_files), digest(spec.MANIFEST.read_bytes()), flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 3 and sys.argv[1] == '--fresh-inventory-sha'
    run(sys.argv[2])
