"""Metadata-only freeze. Does not create authorization or launch a worker."""
import ast
import json
from pathlib import Path
import sys

from . import worker
from src.generalization_pum_process_probe_20261021 import headless


def run():
    assert not worker.AUTH.exists()
    files = []
    scientific = {}
    for namespace in ('generalization_prelib_bounded_execution_20261022',):
        for base in ('src', 'reports'):
            for path in (worker.ROOT / base / namespace).glob('*'):
                if path.is_file():
                    files.append(path)
                    if path.suffix == '.py':
                        ast.parse(path.read_text(encoding='utf-8'))
    for rel in (
        'src/generalization_prelib_pooled_lineage_20261009/pipeline.py',
        'src/generalization_prelib_pooled_lineage_20261009/contracts.py',
        'src/generalization_prelib_pooled_lineage_20261009/verify.py',
    ):
        scientific[rel] = worker.sha(worker.ROOT / rel)
        files.append(worker.ROOT / rel)
    for rel in (
        'src/generalization_current_python_20261022/attest.py',
        'src/generalization_prelib_numpy_profile_20261022/invented.py',
        'src/generalization_prelib_numpy_profile_v2_20261022/invented.py',
        'src/generalization_splicebert_runtime_compatibility_20261007/launcher.py',
        'src/generalization_splicebert_runtime_compatibility_20261007/common.py',
        'src/generalization_pum_process_probe_20261021/headless.py',
        'src/generalization_pum_resource_calibration_20261009/winjob.py',
        'results/generalization_current_python_20261022/current_python_inventory.json',
        'results/generalization_prelib_numpy_profile_v2_20261022/preparation_manifest_reviewed.json',
        'results/generalization_prelib_numpy_profile_v2_20261022/invented_numpy_receipt.json',
        'results/generalization_prelib_numpy_profile_v2_20261022/supervisor_receipt.json',
        'results/generalization_prelib_bounded_execution_20261022/synthetic_tests_receipt.json',
        'results/generalization_prelib_bounded_execution_20261022/synthetic_tests_reviewed_receipt.json',
        'results/generalization_prelib_pooled_lineage_20261009/implementation_manifest.json',
        'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json',
    ):
        files.append(worker.ROOT / rel)
    assert json.loads((worker.ROOT / 'results/generalization_prelib_numpy_profile_v2_20261022/supervisor_receipt.json').read_bytes())['status'] == 'PASS_BOUNDED_INVENTED_NUMPY_PROFILE_V2'
    tests = json.loads((worker.OUT / 'synthetic_tests_reviewed_receipt.json').read_bytes())
    assert tests['source_files'] == {p.relative_to(worker.ROOT).as_posix(): worker.sha(p)
                                     for p in Path(__file__).resolve().parent.glob('*.py')}
    manifest = {
        'status': 'FROZEN_PRELIB_ONLY_OPERATIONAL_ADAPTER_AWAITING_EXPLICIT_APPROVAL',
        'files': {path.relative_to(worker.ROOT).as_posix(): worker.sha(path) for path in files},
        'scientific_files': scientific, 'python_executable': sys.executable,
        'python_executable_sha256': worker.sha(sys.executable), 'native_origins': headless.native_origins(),
        'phases': list(worker.PHASES), 'biological_input_or_target_payloads_read_in_preparation': False,
        'process_memory_cap_bytes': 768 * 2**20, 'job_memory_cap_bytes': 896 * 2**20,
        'active_process_cap': 2, 'scientific_workers': 1, 'numerical_threads': 2,
        'startup_physical_floor_bytes': 512 * 2**20, 'stop_physical_floor_bytes': 256 * 2**20,
        'minimum_system_commit_reserve_bytes': 2**30, 'stage_deadline_seconds': 1800,
        'replaces_only_named_pipeline_process_local_callbacks': ['fresh', 'numpy_runtime'],
        'additional_scoped_bindings': {'save': 'Completion receipt provenance only; scientific arrays/checkpoints untouched',
                                       'subprocess': 'Pinned direct detached GitFacade only'},
        'all_four_module_bindings_restored': True,
        'other_workers_guards_unchanged': True, 'automatic_retry_or_partial_resume': False,
        'spending_authorized': False, 'user_approval_record_required_before_execution': True,
    }
    worker.save(worker.MANIFEST, manifest)
    print('PRELIB_ADAPTER_PREPARED_NOT_AUTHORIZED', worker.sha(worker.MANIFEST), flush=True)


if __name__ == '__main__':
    run()
