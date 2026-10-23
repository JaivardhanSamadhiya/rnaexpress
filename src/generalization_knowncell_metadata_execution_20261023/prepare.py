"""Prepare exact metadata-only admission without traversing project data."""
import ast
from datetime import datetime, timezone
import json
import sys
from .common import *


def run():
    ready_raw = (ROOT / READY).read_bytes()
    assert sha(ready_raw) == READY_SHA
    ready = json.loads(ready_raw)
    assert ready['status'] == 'SOURCE_FROZEN_SELECTIVE_LOADER_NOT_PROJECT_ADMISSION'
    pins = dict(ready['files'])
    for name, expected in pins.items():
        assert sha((ROOT / name).read_bytes()) == expected, name
    pins[READY] = READY_SHA
    admission = {
        'namespace': 'generalization_knowncell_joint_loader_20261022',
        'mode': 'metadata', 'status': 'FROZEN_METADATA_ADMISSION_JOINT_KNOWNCELL',
        'label_access_authorized': False, 'model_fitting_authorized': False,
        'PUM_resource_exception_applies': False, 'PRELib_resource_exception_applies': False,
        'numerical_threads': 1, 'source_readiness_sha256': READY_SHA,
        'data_pins': ready['declared_data_pins'],
        'scope': 'Mikl metadata, exact menus, inherited folds and split contradictions only',
        'whole_core_CSV_tokens_traversed': True,
        'numerical_outcomes_parsed_or_retained': False,
        'arrays_sequences_from_other_studies_and_protected_outcomes_admitted': False,
        'root_committed_manifest_and_original_floors_required': True,
    }
    receipt_path = OUT / 'synthetic_tests_receipt_reviewed.json'
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['status'] == 'PASS_INVENTED_METADATA_EXECUTION_CONTROL_CHECKS'
    sources = sorted((ROOT / 'src' / NS).glob('*.py'))
    assert receipt['sources'] == {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sources}
    for path in sources:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    own = sources + [ROOT/'src'/NS/'.gitattributes', ROOT/'reports'/NS/'protocol.md',
                     ROOT/'reports'/NS/'.gitattributes', OUT/'.gitattributes', receipt_path]
    pins.update({p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in own})
    # Reuse unchanged, already bounded Windows process control; no scientific
    # runtime helper is imported or granted this metadata admission.
    # These two directories are namespace packages, without __init__.py files.
    for name in ('src/generalization_pum_process_probe_20261021/headless.py',
                 'src/generalization_pum_resource_calibration_20261009/winjob.py'):
        pins[name] = sha((ROOT/name).read_bytes())
    assert pins['src/generalization_pum_process_probe_20261021/headless.py'] == '7f741f1e024243546b8ab53b65f4b5245a1fc71a7d9e6de86757bf468c1928f0'
    assert pins['src/generalization_pum_resource_calibration_20261009/winjob.py'] == '3a2b470f116e87ff6233cdc8710b2703cf33b908dae68ece7fb4592227b5f741'
    inventory_path = ROOT/'results/generalization_current_python_20261022/current_python_inventory.json'
    assert sha(inventory_path.read_bytes()) == 'db59c8f19ed8fc3a4a2adcf96b240146c48ba0f1c649e2e2d48f41e5dcf45d59'
    # Exactly the already declared interpreter executable and two DLLs.
    python_files = {str(Path(sys.executable).resolve()): 'b07b03b9ba866a341a3c13ee69710fbc8d43d4ce2523dee13f6df5c25378d15b',
                    str(Path(sys.executable).resolve().parent/'python3.dll'): 'f91ca7e29e8b4cc9ed7a4a935c1b2558c5c8f23398cb20d7048f977aa16fce8b',
                    str(Path(sys.executable).resolve().parent/'python312.dll'): '3b33d49d879dbf3a8aa3fff1bf3859275e76c188a3adec4e7ffe728243652a87'}
    for name, expected in python_files.items():
        assert sha(Path(name).read_bytes()) == expected, name
    pins[inventory_path.relative_to(ROOT).as_posix()] = sha(inventory_path.read_bytes())
    pins[ADMISSION] = save_new(ROOT/ADMISSION, admission)
    save_new(MANIFEST, {
        'status': STATUS, 'generated_utc': datetime.now(timezone.utc).isoformat(),
        'files': pins, 'python_native_files': python_files,
        'python_executable': str(Path(sys.executable).resolve()),
        'metadata_admission_sha256': pins[ADMISSION],
        'allowed_project_payloads': [name for name in ready['declared_data_pins'] if not name.endswith('.npz')],
        'output_bundle': BUNDLE, 'numerical_outcomes_admitted': 0, 'array_reads': 0, 'model_fits': 0,
        'physical_RAM_floor': 3*2**30, 'disk_floor': 2**30, 'numerical_threads': 1,
        'process_cap': 768*2**20, 'job_cap': 896*2**20, 'active_process_cap': 2,
        'lifetime_seconds': 300, 'automatic_retry': False, 'guard_changes': False,
        'requires_exact_committed_source_before_root_start': True,
    })
    print('METADATA_ONLY_SOURCE_READY', sha(MANIFEST.read_bytes()), flush=True)


if __name__ == '__main__':
    run()
