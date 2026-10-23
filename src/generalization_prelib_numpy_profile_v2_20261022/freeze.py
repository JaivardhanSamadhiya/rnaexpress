"""Freeze source and current-interpreter inventory before invented native work."""
import ast
import json
import sys

from .invented import ROOT, OUT, sha
from src.generalization_current_python_20261022.attest import ATTESTATION


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / '.gitattributes').write_text('* -text\n', encoding='utf-8')
    source = ROOT / 'src/generalization_prelib_numpy_profile_v2_20261022'
    for path in source.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    files = list(source.glob('*')) + list((ROOT / 'reports/generalization_prelib_numpy_profile_v2_20261022').glob('*'))
    for rel in (
        'src/generalization_current_python_20261022/attest.py',
        'src/generalization_prelib_numpy_profile_20261022/invented.py',
        'src/generalization_prelib_pooled_lineage_20261009/pipeline.py',
        'src/generalization_prelib_pooled_lineage_20261009/contracts.py',
        'src/generalization_splicebert_runtime_compatibility_20261007/launcher.py',
        'src/generalization_splicebert_runtime_compatibility_20261007/common.py',
        'src/generalization_pum_process_probe_20261021/headless.py',
        'src/generalization_pum_resource_calibration_20261009/winjob.py',
        'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json',
    ):
        files.append(ROOT / rel)
    files.append(ATTESTATION)
    # Preserve the pre-review draft as evidence; it is not an admission input.
    files.append(OUT / 'preparation_manifest.json')
    manifest = {
        'status': 'FROZEN_INVENTED_ONLY_CURRENT_PYTHON_NUMPY_CALIBRATION_V2',
        'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in files if p.is_file()},
        'python_executable': sys.executable, 'python_executable_sha256': sha(sys.executable),
        'seed': 20261022, 'rows': 4054, 'columns': [84, 85, 85], 'penalties': [0.005, 0.05, 0.5],
        'numerical_thread_count': 2, 'deadline_seconds': 120,
        'process_memory_limit_bytes': 768 * 2**20, 'job_memory_limit_bytes': 896 * 2**20,
        'active_process_limit': 2, 'startup_physical_floor_bytes': 512 * 2**20,
        'stop_physical_floor_bytes': 256 * 2**20, 'system_commit_reserve_bytes': 2**30,
        'project_biological_inputs_read': False, 'biological_guards_unchanged': True,
        'v1_failure_preserved': True,
        'v2_changes': ['Separate current-Python inventory; old NumPy payload contract remains unchanged',
                       'Additional independent scalar-fsum RMS and support verification',
                       'Repeat loaded NumPy/Python origin checks after lazy numerical imports'],
    }
    with (OUT / 'preparation_manifest_reviewed.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    print('INVENTED_V2_REVIEWED_FREEZE', sha(OUT / 'preparation_manifest_reviewed.json'), flush=True)


if __name__ == '__main__':
    run()
