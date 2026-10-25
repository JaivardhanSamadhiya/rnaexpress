"""Repeat the unchanged invented suite after a static marker-allowlist repair."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest
from . import tests as original
from . import spec


def main():
    root = Path(__file__).resolve().parents[2]
    out = root/'results'/spec.NS
    forbidden = ('numpy', 'pandas', 'scipy', 'torch', 'openvino', 'sklearn')
    assert not any(name.split('.')[0] in forbidden for name in sys.modules)
    initial_receipt = (out/'synthetic_tests_receipt.json').read_bytes()
    assert original.p.legacy.digest(initial_receipt) == '728c9f29ba039620c33f78c4f087a132bab90ff71e860f3933362c81232cc280'
    paths = sorted((root/'src'/spec.NS).glob('*.py'))
    before = {p.relative_to(root).as_posix(): original.p.legacy.digest(p.read_bytes()) for p in paths}
    with (out/'synthetic_tests_attempt_02.log').open('x', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(original.Cases))
    assert result.wasSuccessful() and result.testsRun == 15
    assert not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert {p.relative_to(root).as_posix(): original.p.legacy.digest(p.read_bytes()) for p in paths} == before
    assert (out/'synthetic_tests_receipt.json').read_bytes() == initial_receipt
    receipt = {'status': 'PASS_INVENTED_CALIBRATED_PREFIT_PROJECTION_NOT_ACTUAL_ADMISSION',
        'UTC': datetime.now(timezone.utc).isoformat(), 'tests': result.testsRun, 'source_files': before,
        'initial_test_receipt_sha256': original.p.legacy.digest(initial_receipt),
        'preserved_preparation_failure': 'preparation_attempt_01_incident.json',
        'project_payload_reads': 0, 'actual_resource_probes': 0, 'actual_optimizer_calls': 0,
        'actual_owner_contexts_verified': 0, 'actual_Git_calls': 0, 'native_or_scientific_imports': False,
        'actual_prefit_or_admission_created': False, 'production_context_verifiers_used': 0,
        'invented_temporary_campaign_birth_only': True, 'production_resources_or_stage_authority_granted': False}
    raw = (json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    with (out/'synthetic_tests_receipt_reviewed.json').open('xb') as stream: stream.write(raw)
    print('PASS_REVIEWED_INVENTED_PREFIT_PROJECTION', result.testsRun, original.p.legacy.digest(raw), flush=True)


if __name__ == '__main__': main()
