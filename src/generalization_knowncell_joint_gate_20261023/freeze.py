"""Source-only freeze; does not import NumPy or read any project decisions."""
import ast
import json
from pathlib import Path

from src.generalization_prelib_numpy_profile_20261022.invented import ROOT, sha


def run():
    namespace = 'generalization_knowncell_joint_gate_20261023'
    source, report, output = [ROOT / folder / namespace for folder in ('src', 'reports', 'results')]
    paths = [p for p in source.glob('*') if p.is_file()] + [p for p in report.glob('*') if p.is_file()]
    for path in source.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    # The first eight-case receipt is a preserved pre-review draft. It is not
    # used to certify the corrected source or to admit native/project work.
    for filename in ('synthetic_tests_receipt.json', 'synthetic_tests_reviewed_receipt.json', '.gitattributes'):
        paths.append(output / filename)
    reviewed = json.loads((output / 'synthetic_tests_reviewed_receipt.json').read_bytes())
    assert reviewed['source_files'] == {p.relative_to(ROOT).as_posix(): sha(p) for p in source.glob('*.py')}
    for rel in (
        'src/generalization_knowncell_joint_design_20261009/spec.py',
        'reports/generalization_knowncell_joint_design_20261009/protocol.md',
        'src/generalization_knowncell_joint_implementation_20261022/contracts.py',
        'src/generalization_knowncell_joint_implementation_20261022/selection.py',
        'src/generalization_knowncell_joint_implementation_20261022/spec.py',
        'src/generalization_crosscell_20261007/bootstrap.py',
        'src/generalization_knowncell_20261007/gate.py',
    ):
        paths.append(ROOT / rel)
    manifest = {
        'status': 'FROZEN_DEFERRED_PAIRED_GATE_SOURCE_NOT_NATIVE_OR_PROJECT_ADMISSION',
        'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
        'native_bootstrap_tested': False, 'project_decision_payloads_read': False,
        'project_gate_run': False, 'original_gate_thresholds_changed': False,
        'original_runtime_or_resource_guards_changed': False,
        'first8_test_receipt_preserved': True,
        'prospective_review_changes': ['Accept legitimate zero exponential weights while requiring positive row sums',
                                       'Reject nonfinite primary summaries as integrity failures'],
    }
    with (output / 'preparation_manifest.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(manifest, indent=2) + '\n')
    print('DEFERRED_PRIMARY_GATE_PREPARED', sha(output / 'preparation_manifest.json'), flush=True)


if __name__ == '__main__':
    run()
