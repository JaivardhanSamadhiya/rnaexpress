"""Pure static review evidence; no module execution or biological payloads."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_current_study_execution_20261026'
REVIEW_NS = 'generalization_current_study_review_20261026'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    receipt_path = ROOT / 'results' / NS / 'invented_tests_receipt_final.json'
    receipt_raw = receipt_path.read_bytes()
    tests = json.loads(receipt_raw)
    assert tests['tests'] == 12
    assert tests['failures'] == tests['errors'] == 0
    assert tests['actual_data_reads'] == tests['actual_native_jobs'] == 0
    pins = {}
    for name, want in tests['source_sha256'].items():
        assert name.startswith('src/' + NS + '/') and name.endswith('.py')
        raw = (ROOT / name).read_bytes()
        assert sha(raw) == want
        ast.parse(raw, filename=name)
        pins[name] = want
    assert len(pins) == 9
    for name in ('reports/' + NS + '/protocol.md',
                 'reports/' + NS + '/approval_scope.md'):
        pins[name] = sha((ROOT / name).read_bytes())
    core_manifest = 'results/generalization_current_fixed_fit_core_20261026/source_preparation_manifest.json'
    assert sha((ROOT / core_manifest).read_bytes()) == '1041ce0d2b1307273b79d5c26352300b8b566f9aa2bc30386d873e95a40806f8'
    pins[core_manifest] = sha((ROOT / core_manifest).read_bytes())
    core_receipt = 'results/generalization_current_fixed_fit_core_20261026/synthetic_tests_receipt.json'
    assert sha((ROOT / core_receipt).read_bytes()) == '4452f0aa26bdc43d1df5860f95861d54757f9f0214d506689d6287ddc8f7e749'
    pins[core_receipt] = sha((ROOT / core_receipt).read_bytes())
    pins[receipt_path.relative_to(ROOT).as_posix()] = sha(receipt_raw)
    pins[Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__).read_bytes())
    observed_absent = []
    for suffix in ('execution_manifest.json', 'manual_authorization.json',
                   'prefit/run_admission.json', 'prefit/attempt_birth.json',
                   'fit/run_admission.json', 'fit/attempt_birth.json'):
        name = 'results/' + NS + '/' + suffix
        assert not (ROOT / name).exists(), name
        observed_absent.append(name)
    base_report = ROOT / 'reports' / REVIEW_NS / 'source_review.md'
    report = base_report.read_text(encoding='utf8')
    report += '\nThe final reviewed source receipt is `invented_tests_receipt_final.json`; its raw SHA256 is `' + sha(receipt_raw) + '`. The reviewed startup repair appears in `supervise.py:7`, `worker.py:7`, `prepare.py:9` and `common.py:50`. Exact committed-byte admission appears in `common.py:80` and `common.py:127`; successful-producer reconstruction appears in `prepare.py:73`. The final source-freezer also refuses an existing authorization, stage admission, birth or stage output.\n\nReviewed source SHA256 values:\n\n'
    report += '\n'.join('- `' + name + '`: `' + want + '`' for name, want in sorted(pins.items()) if name.startswith('src/')) + '\n'
    report_raw = report.encode('utf8')
    out_report = ROOT / 'reports' / NS / 'source_review.md'
    out_receipt = ROOT / 'results' / NS / 'source_review_receipt.json'
    assert not out_report.exists() and not out_receipt.exists()
    for name, want in pins.items():
        assert sha((ROOT / name).read_bytes()) == want, name
    with out_report.open('xb') as stream:
        stream.write(report_raw)
    result = {
        'status': 'SOURCE_LOGIC_REVIEW_PASS_FINAL_MANIFEST_AND_ACTUAL_AUTHORITY_PENDING',
        'remaining_concrete_source_blockers': [],
        'reviewed_files_sha256': pins,
        'review_report_sha256': sha(report_raw),
        'observed_absent_at_review': observed_absent,
        'own_python_ast_count': 9,
        'invented_controller_tests_reported_not_rerun': 12,
        'actual_biological_payload_reads': 0,
        'actual_scientific_imports_or_native_calls': 0,
        'actual_jobs_or_fits': 0,
        'independent_final_manifest_closure_verified': False,
        'native_compatibility_or_biological_generalization_certified_here': False,
        'new_human_authority_created_here': False,
    }
    raw = (json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    with out_receipt.open('xb') as stream:
        stream.write(raw)
    print('SOURCE_REVIEW_PASS', sha(report_raw), sha(raw))


if __name__ == '__main__':
    main()
