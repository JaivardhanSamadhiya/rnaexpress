"""Invented cross-stage identity regressions; no model or project execution."""
import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

from . import projection as p
from . import spec
from src.generalization_knowncell_prefit_projection_20261024 import tests as v1tests
from src.generalization_knowncell_joint_campaign_20261023.writer_v2 import Campaign
from src.generalization_knowncell_campaign_replay_20261023 import replay

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'results'/spec.NS


def bind(actual, admission, context, *, verifier=None, reader=None):
    raw, ar, cr = v1tests.seal(actual, admission, context)
    def exact_reader(name, commit):
        if (name, commit) == (context['root_admission_relative_path'], context['root_admission_commit']): return ar
        if (name, commit) == (admission['prefit_relative_path'], admission['prefit_commit']): return raw
        raise AssertionError('Unexpected invented commit request')
    def invented_verifier(binding): return True  # Only an invented fixture, no actual owner authority.
    return p.bind_calibrated_plan(raw, ar, cr, committed_reader=reader or exact_reader,
        verify_root_context=verifier or invented_verifier)


class StopBeforePool(Exception): pass


class Cases(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.old, cls.actual, cls.admission, cls.fit_context = v1tests.fixture()

    def contexts(self):
        fit, independent = deepcopy(self.fit_context), deepcopy(self.fit_context)
        independent['current_owner_receipt_sha256'] = '6'*64
        return fit, independent

    def test_v1_later_stage_identity_blocker_is_reproduced_without_modifying_v1(self):
        fit, independent = self.contexts()
        first = v1tests.bind(self.actual, self.admission, fit)
        second = v1tests.bind(self.actual, self.admission, independent)
        self.assertNotEqual(first.identity(), second.identity())
        self.assertEqual(first.document(), second.document())

    def test_two_honest_current_contexts_have_equal_campaign_identity_distinct_operational_context(self):
        fit, independent = self.contexts(); calls = []
        def verifier(binding): calls.append(binding['context']['current_owner_receipt_sha256']); return True
        first = bind(self.actual, self.admission, fit, verifier=verifier)
        second = bind(self.actual, self.admission, independent, verifier=verifier)
        self.assertEqual(calls, ['5'*64, '6'*64])
        self.assertEqual(first.identity(), second.identity())
        self.assertNotEqual(first.verified_context_raw, second.verified_context_raw)
        self.assertNotEqual(first.operational_context(), second.operational_context())
        self.assertEqual(first.operational_context()['stable_campaign_identity_sha256'],
                         second.operational_context()['stable_campaign_identity_sha256'])
        self.assertEqual(first.operational_context()['current_owner_receipt_sha256'], '5'*64)
        self.assertEqual(second.operational_context()['current_owner_receipt_sha256'], '6'*64)

    def test_current_proof_raw_encoding_changes_only_operational_descriptor(self):
        first = bind(self.actual, self.admission, self.fit_context)
        raw, ar, cr = v1tests.seal(self.actual, self.admission, self.fit_context)
        differently_encoded = (json.dumps(json.loads(cr), indent=2)+'\n').encode()
        self.assertNotEqual(cr, differently_encoded)
        def reader(name, commit): return ar if name == self.fit_context['root_admission_relative_path'] else raw
        second = p.bind_calibrated_plan(raw, ar, differently_encoded,
            committed_reader=reader, verify_root_context=lambda binding: True)
        self.assertEqual(first.identity(), second.identity())
        self.assertNotEqual(first.operational_context()['caller_verified_context_sha256'],
                            second.operational_context()['caller_verified_context_sha256'])

    def test_stable_descriptor_contains_no_current_owner_or_context_bytes_hash(self):
        plan = bind(self.actual, self.admission, self.fit_context)
        descriptor = plan.identity()['calibrated_resource_compatibility_view']
        self.assertNotIn('caller_verified_context_sha256', descriptor)
        self.assertNotIn('current_owner_receipt_sha256', descriptor)
        self.assertEqual(descriptor['compatibility_identity_version'], 2)
        self.assertEqual(descriptor['root_admission_commit'], self.fit_context['root_admission_commit'])
        self.assertEqual(descriptor['prefit_owner_receipt_sha256'], self.admission['prefit_owner_receipt_sha256'])
        self.assertEqual(descriptor['actual_prefit_raw_sha256'], plan.prefit_sha256)
        self.assertEqual(descriptor['legacy_view_canonical_sha256'], p.original.legacy.hash_value(plan.document()))
        self.assertFalse(descriptor['actual_execution_authority_granted_here'])

    def test_actual_prefit_or_stable_admission_change_still_changes_campaign_identity(self):
        first = bind(self.actual, self.admission, self.fit_context)
        changed = deepcopy(self.actual); changed['resource_calibration']['opaque_owner'][1] = 99
        second = bind(changed, self.admission, self.fit_context)
        self.assertNotEqual(first.identity(), second.identity())
        context = deepcopy(self.fit_context); context['root_admission_commit'] = '7'*40
        third = bind(self.actual, self.admission, context)
        self.assertNotEqual(first.identity(), third.identity())

    def test_original_writer_birth_and_replay_identity_checks_accept_new_current_owner_without_models(self):
        fit, independent = self.contexts()
        fit_plan = bind(self.actual, self.admission, fit)
        replay_plan = bind(self.actual, self.admission, independent)
        with tempfile.TemporaryDirectory() as directory:
            campaign = Campaign(Path(directory)/'invented_campaign', fit_plan)
            birth_raw = (campaign.directory/'campaign_birth.json').read_bytes()
            records = [{'task_key': replay.lifecycle.task_key(task), 'birth_raw': b'{}',
                        'checkpoint_raw': b'{}', 'completion_raw': b'{}'} for task in replay.lifecycle.task_roster()]
            complete = {'status': 'COMPLETE63_CHECKPOINT84_UNIT_LIFECYCLE_NOT_SCIENTIFIC_REPLAY_OR_GATE',
                **fit_plan.identity(), 'campaign_birth_sha256': replay.lifecycle.digest(birth_raw),
                'inner_checkpoints': 54, 'outer_checkpoints': 9,
                'checkpoint_receipt_sha256': {row['task_key']: replay.lifecycle.digest(b'{}') for row in records},
                'independent_numeric_and_selection_replay_complete': False, 'biological_or_gate_claim': False}
            def stop(task): raise StopBeforePool('Both original identity equalities passed; no pool/model examined')
            def forbidden(*args): self.fail('No arithmetic/model work is allowed in this test')
            with self.assertRaisesRegex(StopBeforePool, 'Both original identity equalities passed'):
                replay._verify(None, replay_plan, birth_raw, records, replay.lifecycle.canonical_bytes(complete),
                    pool_check=stop, arithmetic_check=forbidden, fresh=lambda: None)
            self.assertEqual(list(campaign.directory.iterdir()), [campaign.directory/'campaign_birth.json'])

    def test_actual_raw_flag_science_and_metadata_pool_objects_are_preserved(self):
        plan = bind(self.actual, self.admission, self.fit_context)
        prepared = p.original.PreparedPools([object()],
            {name: {'binding': value} for name, value in deepcopy(self.old['source_pools']).items()}, deepcopy(self.old))
        result = p.rebind_prepared(plan, prepared)
        self.assertIs(result.metadata, prepared.metadata); self.assertIs(result.pools, prepared.pools)
        self.assertEqual(plan.actual_document(), self.actual)
        self.assertIs(plan.actual_document()['resource_exception_applies'], True)
        self.assertIs(plan.document()['resource_exception_applies'], False)
        self.assertEqual(result.prefit_document, plan.document())
        self.assertEqual(prepared.prefit_document, self.old)
        with self.assertRaises(FrozenInstanceError): plan.verified_context_raw = b'changed'
        with self.assertRaises(AssertionError): p.rebind_prepared(v1tests.bind(self.actual, self.admission, self.fit_context), prepared)

    def test_each_current_context_requires_real_verifier_contract_again(self):
        fit, independent = self.contexts()
        bind(self.actual, self.admission, fit)
        for wrong in (False, 1, None):
            with self.subTest(wrong=wrong), self.assertRaises(AssertionError):
                bind(self.actual, self.admission, independent, verifier=lambda binding: wrong)
        with self.assertRaises(AssertionError): bind(self.actual, self.admission, independent, reader=lambda *args: b'wrong')
        independent['actual_owner_resource_runtime_and_source_closure_verified'] = False
        with self.assertRaises(AssertionError): bind(self.actual, self.admission, independent)

    def test_operational_context_is_detached_and_never_claims_fresh_state_or_stage_authority(self):
        plan = bind(self.actual, self.admission, self.fit_context)
        value = plan.operational_context(); value['supplied_verified_context']['current_owner_receipt_sha256'] = '0'*64
        actual = plan.operational_context()
        self.assertEqual(actual['current_owner_receipt_sha256'], '5'*64)
        self.assertFalse(actual['fresh_state_checks_performed_by_this_method'])
        self.assertFalse(actual['actual_stage_authority_granted_here'])
        self.assertTrue(actual['current_stage_context_excluded_from_stable_campaign_identity'])

    def test_no_production_read_write_probe_alias_or_native_import(self):
        tree = ast.parse((ROOT/'src'/spec.NS/'projection.py').read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): self.fail('No external direct imports needed')
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or '').split('.')[0], ('numpy', 'pandas', 'scipy', 'os', 'ctypes', 'pathlib', 'subprocess'))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, ('open', 'exec', 'eval', '__import__', 'setattr'))


def main():
    forbidden = ('numpy', 'pandas', 'scipy', 'torch', 'openvino', 'sklearn')
    assert not any(name.split('.')[0] in forbidden for name in sys.modules)
    paths = sorted((ROOT/'src'/spec.NS).glob('*.py'))
    hashes = {path.relative_to(ROOT).as_posix(): p.original.legacy.digest(path.read_bytes()) for path in paths}
    with (OUT/'synthetic_tests_attempt_01.log').open('x', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert {path.relative_to(ROOT).as_posix(): p.original.legacy.digest(path.read_bytes()) for path in paths} == hashes
    receipt = {'status': 'PASS_INVENTED_REPLAY_STABLE_PREFIT_IDENTITY_NOT_ACTUAL_STAGE_AUTHORITY',
        'UTC': datetime.now(timezone.utc).isoformat(), 'tests': result.testsRun, 'source_files': hashes,
        'project_payload_reads': 0, 'actual_Git_calls': 0, 'actual_owner_contexts_verified': 0,
        'native_or_scientific_imports': False, 'actual_resource_probes': 0, 'actual_optimizer_calls': 0,
        'actual_models_or_checkpoints_created': 0, 'invented_temporary_campaign_birth_only': True,
        'original_private_replay_stopped_before_pool_or_model': True, 'actual_stage_authority_granted': False}
    raw = (json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    with (OUT/'synthetic_tests_receipt.json').open('xb') as stream: stream.write(raw)
    print('PASS_REPLAY_STABLE_PREFIT_IDENTITY', result.testsRun, p.original.legacy.digest(raw), flush=True)


if __name__ == '__main__': main()
