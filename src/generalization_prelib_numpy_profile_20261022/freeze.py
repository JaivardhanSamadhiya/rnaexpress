"""Record an invented-only source/runtime freeze without importing NumPy."""
import ast
import json
import sys

from .invented import ROOT, OUT, sha


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / '.gitattributes').write_text('* -text\n', encoding='utf-8')
    source = ROOT / 'src/generalization_prelib_numpy_profile_20261022'
    for path in source.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    files = list(source.glob('*')) + list((ROOT / 'reports/generalization_prelib_numpy_profile_20261022').glob('*'))
    for rel in (
        'src/generalization_prelib_pooled_lineage_20261009/pipeline.py',
        'src/generalization_prelib_pooled_lineage_20261009/contracts.py',
        'src/generalization_splicebert_runtime_compatibility_20261007/launcher.py',
        'src/generalization_splicebert_runtime_compatibility_20261007/common.py',
        'src/generalization_pum_process_probe_20261021/headless.py',
        'src/generalization_pum_resource_calibration_20261009/winjob.py',
        'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json',
    ):
        files.append(ROOT / rel)
    receipt = {
        'status': 'FROZEN_INVENTED_ONLY_NUMPY_CALIBRATION',
        'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in files if p.is_file()},
        'python_executable': sys.executable, 'python_executable_sha256': sha(sys.executable),
        'synthetic_rows': 4054, 'synthetic_columns': [84, 85, 85],
        'penalties': [0.005, 0.05, 0.5], 'project_inputs_or_targets_read': False,
        'numerical_thread_count': 2, 'deadline_seconds': 120,
        'original_scientific_guards_unchanged': True,
    }
    with (OUT / 'preparation_manifest.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, indent=2) + '\n')
    print('INVENTED_ONLY_FREEZE', sha(OUT / 'preparation_manifest.json'))


if __name__ == '__main__':
    run()
