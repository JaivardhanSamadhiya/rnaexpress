"""Invented supplied bytes only; no project prefit, probe, native call or fit."""
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
from src.generalization_knowncell_joint_campaign_20261023 import spec as old_spec
from src.generalization_knowncell_joint_campaign_20261023.writer_v2 import Campaign

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'results'/spec.NS


def fixture():
    ids = ['invented_projection_%05d' % i for i in range(old_spec.COUNTS['all_rows'])]
    folds = [i % 3 for i in range(len(ids))]
    old = {'status': old_spec.PREFIT_STATUS, 'counts': dict(old_spec.COUNTS),
        'arms': list(old_spec.ARMS), 'configs': list(old_spec.CONFIGS), 'numerical_threads': 1,
        spec.FIELD: False, 'runtime_binding_sha256': 'a'*64,
        'metadata_admission_sha256': 'b'*64, 'feature_admission_sha256': 'c'*64,
        'label_admission_sha256': 'd'*64, 'fit_source_manifest_sha256': 'e'*64,
        'all_row_ids': ids, 'all_row_folds': folds, 'source_pools': {},
        'input_admission_bindings': {'runtime_binding_sha256': 'a'*64, 'invented_input_sha256': 'f'*64}}
    for outer in old_spec.FOLDS:
        for inner in (None, *[f for f in old_spec.FOLDS if f != outer]):
            excluded = {outer} if inner is None else {outer, inner}
            target_fold = outer if inner is None else inner
            train = [row_id for row_id, fold in zip(ids, folds) if fold not in excluded]
            target = [row_id for row_id, fold in zip(ids, folds) if fold == target_fold]
            old['source_pools'][p.legacy.pool_key(outer, inner)] = {
                'training_ids': train, 'validation_ids': target,
                'training_ids_sha256': p.legacy.id_hash(train),
                'validation_ids_sha256': p.legacy.id_hash(target),
                'training_rows': len(train), 'validation_rows': len(target), 'training_pairs': len(train)//2,
                'both_cells_confirmed': True, 'full_original_menus_confirmed': True,
                'gene_component_allele_contradictions': 0,
                **{field: 'f'*64 for field in old_spec.POOL_HASH_FIELDS}}
    actual = deepcopy(old)
    actual[spec.FIELD] = True
    actual['resource_calibration'] = {'truthful_calibrated_resource_usage': True, 'opaque_owner': ['invented', 17]}
    actual['prefit_owner_receipt_sha256'] = '1'*64
    raw = p.legacy.canonical_bytes(actual)
    admission = {'status': spec.ADMISSION_STATUS, 'schema_version': 1,
        'prefit_relative_path': 'results/invented_projection/actual_prefit.json',
        'prefit_sha256': p.legacy.digest(raw), 'prefit_commit': '2'*40,
        'runtime_binding_sha256': 'a'*64, 'projection_source_manifest_sha256': '3'*64,
        'approved_policy_manifest_sha256': spec.POLICY_SHA, 'authorization_sha256': spec.AUTH_SHA,
        'approval_scope_sha256': spec.SCOPE_SHA, 'prefit_owner_receipt_sha256': '1'*64,
        'input_admission_bindings_sha256': p.legacy.hash_value(actual['input_admission_bindings']),
        'additional_top_level_provenance_fields': ['prefit_owner_receipt_sha256', 'resource_calibration'],
        'scientific_settings_changed': False, 'permitted_projection': deepcopy(spec.PROJECTION),
        'actual_stage_authority_granted_here': False}
    admission_raw = p.legacy.canonical_bytes(admission)
    context = {'status': spec.CONTEXT_STATUS,
        'root_admission_relative_path': 'results/invented_projection/root_admission.json',
        'root_admission_commit': '4'*40, 'root_admission_sha256': p.legacy.digest(admission_raw),
        'prefit_sha256': p.legacy.digest(raw), 'current_runtime_binding_sha256': 'a'*64,
        'projection_source_manifest_sha256': '3'*64,
        'approved_policy_manifest_sha256': spec.POLICY_SHA, 'authorization_sha256': spec.AUTH_SHA,
        'approval_scope_sha256': spec.SCOPE_SHA, 'prefit_owner_receipt_sha256': '1'*64,
        'current_owner_receipt_sha256': '5'*64,
        'input_admission_bindings_sha256': admission['input_admission_bindings_sha256'],
        'actual_owner_resource_runtime_and_source_closure_verified': True,
        'actual_stage_authority_granted_by_this_library': False}
    return old, actual, admission, context


def seal(actual, admission, context):
    raw = p.legacy.canonical_bytes(actual)
    admission = deepcopy(admission); context = deepcopy(context)
    admission['prefit_sha256'] = context['prefit_sha256'] = p.legacy.digest(raw)
    ar = p.legacy.canonical_bytes(admission)
    context['root_admission_sha256'] = p.legacy.digest(ar)
    return raw, ar, p.legacy.canonical_bytes(context)


def bind(actual, admission, context, *, verifier=None, reader=None):
    raw, ar, cr = seal(actual, admission, context)
    def exact_reader(name, commit):
        if (name, commit) == (context['root_admission_relative_path'], context['root_admission_commit']): return ar
        if (name, commit) == (admission['prefit_relative_path'], admission['prefit_commit']): return raw
        raise AssertionError('Unexpected invented commit request')
    def invented_verifier(value):
        assert value['context']['status'] == spec.CONTEXT_STATUS
        assert value['actual_prefit_raw_sha256'] == p.legacy.digest(raw)
        return True  # Invented fixture, expressly not a production authority.
    return p.bind_calibrated_plan(raw, ar, cr, committed_reader=reader or exact_reader,
        verify_root_context=verifier or invented_verifier)


class Cases(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.original, cls.actual, cls.admission, cls.context = fixture()

    def plan(self): return bind(self.actual, self.admission, self.context)

    def test_legacy_validator_rejects_actual_true_but_projection_preserves_every_other_value(self):
        with self.assertRaises(AssertionError): p.legacy.validate_prefit(self.actual)
        plan = self.plan(); view = plan.document()
        self.assertIsInstance(plan, p.legacy.BoundPlan)
        self.assertIs(plan.actual_document()[spec.FIELD], True); self.assertIs(view[spec.FIELD], False)
        self.assertEqual(set(view), set(self.actual))
        for name in self.actual:
            if name != spec.FIELD: self.assertEqual(p.legacy.canonical_bytes(view[name]), p.legacy.canonical_bytes(self.actual[name]))
        self.assertEqual(p.legacy.strict_json(plan.prefit_raw), self.actual)
        self.assertNotEqual(p.legacy.canonical_bytes(view), plan.prefit_raw)

    def test_raw_whitespace_hash_and_exact_commits_are_retained(self):
        raw = (json.dumps(self.actual, indent=2)+'\n').encode()
        admission = deepcopy(self.admission); admission['prefit_sha256'] = p.legacy.digest(raw)
        ar = p.legacy.canonical_bytes(admission)
        context = deepcopy(self.context); context['prefit_sha256'] = p.legacy.digest(raw)
        context['root_admission_sha256'] = p.legacy.digest(ar)
        seen = []
        def reader(name, commit):
            seen.append((name, commit)); return ar if name == context['root_admission_relative_path'] else raw
        plan = p.bind_calibrated_plan(raw, ar, p.legacy.canonical_bytes(context),
            committed_reader=reader, verify_root_context=lambda binding: True)
        self.assertIs(plan.prefit_raw, raw); self.assertEqual(plan.prefit_sha256, p.legacy.digest(raw))
        self.assertEqual(seen, [(context['root_admission_relative_path'], context['root_admission_commit']),
                                (admission['prefit_relative_path'], admission['prefit_commit'])])

    def test_document_actual_document_and_identity_return_detached_json(self):
        plan = self.plan(); one = plan.document(); one['resource_calibration']['opaque_owner'][1] = 99
        actual = plan.actual_document(); actual['source_pools'].clear()
        identity = plan.identity(); identity['calibrated_resource_compatibility_view']['sole_projection']['actual_value'] = False
        self.assertEqual(plan.actual_document(), self.actual)
        self.assertEqual(plan.document()['resource_calibration'], self.actual['resource_calibration'])
        self.assertIs(plan.identity()['calibrated_resource_compatibility_view']['sole_projection']['actual_value'], True)
        with self.assertRaises(FrozenInstanceError): plan.prefit_raw = b'changed'

    def test_campaign_identity_binds_raw_view_owner_runtime_and_sole_projection(self):
        plan = self.plan(); identity = plan.identity(); detail = identity['calibrated_resource_compatibility_view']
        self.assertEqual(identity['prefit_sha256'], p.legacy.digest(plan.prefit_raw))
        self.assertEqual(detail['actual_document_canonical_sha256'], p.legacy.hash_value(self.actual))
        self.assertEqual(detail['legacy_view_canonical_sha256'], p.legacy.hash_value(plan.document()))
        self.assertNotEqual(detail['actual_document_canonical_sha256'], detail['legacy_view_canonical_sha256'])
        self.assertEqual(detail['sole_projection'], spec.PROJECTION)
        self.assertFalse(detail['document_is_actual_persisted_prefit_provenance'])
        self.assertFalse(detail['original_resource_guards_unchanged'])
        self.assertFalse(detail['actual_execution_authority_granted_here'])
        self.assertEqual(detail['prefit_owner_receipt_sha256'], self.admission['prefit_owner_receipt_sha256'])

    def test_original_writer_accepts_subclass_and_persists_descriptor_in_invented_birth(self):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as folder:
            campaign = Campaign(Path(folder)/'invented_checkpoints', plan)
            birth = p.legacy.strict_json((campaign.directory/'campaign_birth.json').read_bytes())
            self.assertEqual(birth['calibrated_resource_compatibility_view'], plan.identity()['calibrated_resource_compatibility_view'])
            self.assertEqual(birth['prefit_sha256'], plan.prefit_sha256)
            self.assertEqual(campaign.plan.document(), plan.document())
            self.assertEqual(list(campaign.directory.iterdir()), [campaign.directory/'campaign_birth.json'])

    def test_bind_requires_truthful_true_and_original_scientific_validator(self):
        for flag in (False, 1, None):
            changed = deepcopy(self.actual); changed[spec.FIELD] = flag
            with self.subTest(flag=flag), self.assertRaises(AssertionError): bind(changed, self.admission, self.context)
        for key, value in (('numerical_threads', 2), ('configs', []), ('all_row_ids', [])):
            changed = deepcopy(self.actual); changed[key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError): bind(changed, self.admission, self.context)

    def test_wrong_commit_bytes_and_context_verification_result_reject(self):
        for reader in (lambda name, commit: b'changed', lambda name, commit: False):
            with self.assertRaises(AssertionError): bind(self.actual, self.admission, self.context, reader=reader)
        for result in (False, 1, {'PASS': True}, None):
            with self.subTest(result=result), self.assertRaises(AssertionError):
                bind(self.actual, self.admission, self.context, verifier=lambda binding: result)

    def test_verifier_bound_request_cannot_be_mutated(self):
        def mutating(binding): binding['context']['current_owner_receipt_sha256'] = '0'*64; return True
        with self.assertRaisesRegex(AssertionError, 'mutated'): bind(self.actual, self.admission, self.context, verifier=mutating)

    def test_owner_runtime_inputs_sources_and_original_approval_bindings_are_required(self):
        for key in ('projection_source_manifest_sha256', 'prefit_owner_receipt_sha256',
                    'input_admission_bindings_sha256', 'authorization_sha256', 'approval_scope_sha256',
                    'approved_policy_manifest_sha256', 'runtime_binding_sha256'):
            changed = deepcopy(self.admission); changed[key] = '0'*64
            with self.subTest(key=key), self.assertRaises(AssertionError): bind(self.actual, changed, self.context)
        for key, value in (('current_runtime_binding_sha256', '0'*64), ('current_owner_receipt_sha256', ''),
                           ('actual_owner_resource_runtime_and_source_closure_verified', False)):
            changed = deepcopy(self.context); changed[key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError): bind(self.actual, self.admission, changed)

    def test_missing_unknown_schema_or_false_projection_declaration_reject(self):
        for mutation in ('missing', 'extra', 'projection', 'stage_authority'):
            changed = deepcopy(self.admission)
            if mutation == 'missing': del changed['prefit_owner_receipt_sha256']
            elif mutation == 'extra': changed['unknown_override'] = True
            elif mutation == 'projection': changed['permitted_projection']['actual_value'] = False
            else: changed['actual_stage_authority_granted_here'] = True
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError): bind(self.actual, changed, self.context)

    def test_duplicate_nonfinite_or_unsafe_supplied_data_reject(self):
        raw, ar, cr = seal(self.actual, self.admission, self.context)
        for broken in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'):
            with self.assertRaises((AssertionError, KeyError, ValueError)):
                p.bind_calibrated_plan(broken, ar, cr, committed_reader=lambda *args: raw, verify_root_context=lambda b: True)
        for path in ('../escape.json', 'results/../escape.json', 'results\\escape.json', 'D:/escape.json'):
            changed = deepcopy(self.admission); changed['prefit_relative_path'] = path
            with self.subTest(path=path), self.assertRaises(AssertionError): bind(self.actual, changed, self.context)

    def prepared(self, document=None):
        pools = {name: {'binding': deepcopy(value), 'opaque_native_array_not_touched': object()}
                 for name, value in self.original['source_pools'].items()}
        return p.PreparedPools([object()], pools, deepcopy(document or self.original))

    def test_rebind_retains_exact_metadata_pool_objects_and_all_actual_provenance(self):
        prepared = self.prepared(); old_document = deepcopy(prepared.prefit_document); plan = self.plan()
        rebound = p.rebind_prepared(plan, prepared)
        self.assertIsNot(rebound, prepared); self.assertIs(rebound.metadata, prepared.metadata)
        self.assertIs(rebound.pools, prepared.pools)
        self.assertEqual(prepared.prefit_document, old_document)
        self.assertEqual(rebound.prefit_document, plan.document())
        for field in self.admission['additional_top_level_provenance_fields']:
            self.assertEqual(rebound.prefit_document[field], self.actual[field])
        task = p.legacy.task_roster()[0]
        self.assertEqual(plan.pool(task), prepared.pools[p.legacy.pool_key(task['outer_fold'], task['inner_fold'])]['binding'])

    def test_rebind_rejects_original_key_removal_change_and_pool_binding_change(self):
        for mode in ('removed', 'changed', 'pool', 'extra_pool'):
            prepared = self.prepared()
            if mode == 'removed': prepared.prefit_document['only_old_key'] = True
            elif mode == 'changed': prepared.prefit_document['fit_source_manifest_sha256'] = '0'*64
            elif mode == 'pool': next(iter(prepared.pools.values()))['binding']['pair_weights_sha256'] = '0'*64
            else: prepared.pools['unknown_pool'] = {'binding': {}}
            with self.subTest(mode=mode), self.assertRaises(AssertionError): p.rebind_prepared(self.plan(), prepared)

    def test_rebind_requires_exact_root_declared_provenance_additions(self):
        admission = deepcopy(self.admission); admission['additional_top_level_provenance_fields'] = []
        plan = bind(self.actual, admission, self.context)
        with self.assertRaises(AssertionError): p.rebind_prepared(plan, self.prepared())

    def test_no_production_reader_writer_probe_native_import_or_old_monkeypatch(self):
        source = (ROOT/'src'/spec.NS/'projection.py').read_text(encoding='utf-8'); tree = ast.parse(source)
        forbidden = {'numpy', 'pandas', 'scipy', 'ctypes', 'subprocess', 'os', 'pathlib'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): self.assertFalse({alias.name.split('.')[0] for alias in node.names} & forbidden)
            if isinstance(node, ast.ImportFrom): self.assertNotIn((node.module or '').split('.')[0], forbidden)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, ('open', 'exec', 'eval', '__import__', 'setattr'))
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute): self.assertFalse(isinstance(target.value, ast.Name) and target.value.id == 'legacy')


def main():
    forbidden = ('numpy', 'pandas', 'scipy', 'torch', 'openvino', 'sklearn')
    assert not any(name.split('.')[0] in forbidden for name in sys.modules)
    started_sources = {path.relative_to(ROOT).as_posix(): p.legacy.digest(path.read_bytes())
                       for path in (ROOT/'src'/spec.NS).glob('*.py')}
    with (OUT/'synthetic_tests_attempt_01.log').open('x', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in forbidden for name in sys.modules)
    final_sources = {path.relative_to(ROOT).as_posix(): p.legacy.digest(path.read_bytes())
                     for path in (ROOT/'src'/spec.NS).glob('*.py')}
    assert final_sources == started_sources
    receipt = {'status': 'PASS_INVENTED_CALIBRATED_PREFIT_PROJECTION_NOT_ACTUAL_ADMISSION',
        'UTC': datetime.now(timezone.utc).isoformat(), 'tests': result.testsRun, 'source_files': final_sources,
        'actual_prefit_or_admission_created': False, 'project_payload_reads': 0, 'native_or_scientific_imports': False,
        'actual_resource_probes': 0, 'actual_owner_contexts_verified': 0, 'actual_Git_calls': 0,
        'actual_optimizer_calls': 0, 'invented_temporary_campaign_birth_only': True,
        'production_context_verifiers_used': 0, 'production_resources_or_stage_authority_granted': False}
    raw = (json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    with (OUT/'synthetic_tests_receipt.json').open('xb') as stream: stream.write(raw)
    print('PASS_INVENTED_CALIBRATED_PREFIT_PROJECTION', result.testsRun, p.legacy.digest(raw), flush=True)


if __name__ == '__main__': main()
