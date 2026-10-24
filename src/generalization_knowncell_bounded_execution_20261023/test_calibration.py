"""Private stand-alone module doubles only; never patch production aliases."""
from datetime import datetime, timezone
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

from . import calibration as c

ENV = {name:'1' for name in c.THREAD_KEYS}
MANIFEST = 'a'*64


def snapshot(physical=512*2**20,commit=2**30,disk=2**30):
    return {'physical_available':physical,'commit_headroom':commit,'disk_available':disk}


def private_fixture(states=None):
    """Invented schema values are not approvals or public owner verification."""
    evidence = {'parent_pid':os.getppid(),'birth_sha256':'b'*64}
    owner = {'current_pid':os.getpid(),'parent_pid':os.getppid(),'birth_sha256':'b'*64,
             'manifest_sha256':MANIFEST,'in_owned_job':True,'continuous_monitoring_owned_by_controller':True}
    authorization = {'manifest_sha256':MANIFEST,'approval_sha256':'c'*64,
                     'explicit_human_approval':True,'allowed_stages':list(c.STAGES),'owned_job_required':True}
    common = types.SimpleNamespace(verify_owner=Mock(return_value=copy.deepcopy(owner)))
    memory = Mock(side_effect=iter(states)) if states is not None else Mock(side_effect=lambda:snapshot())
    session = c._Session('metadata',MANIFEST,authorization,owner,evidence,memory,common)
    def original(snapshot,environment):
        raise RuntimeError('Invented original must be restored, never invoked during calibration')
    modules = []
    for name,_ in c.TARGETS:
        module = types.ModuleType(name)
        module.require_resources = original
        module.unrelated = object()
        modules.append(module)
    return session,modules,original,memory,common


class Cases(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ,ENV)
        self.environment.start()
        self.assertIsNone(c._ACTIVE)
    def tearDown(self):
        self.assertIsNone(c._ACTIVE)
        self.environment.stop()

    def test_public_signature_and_stage_enum_have_no_probe_or_module_injection(self):
        self.assertEqual(set(inspect.signature(c.calibrated).parameters),{'stage','manifest_sha','owner_evidence'})
        self.assertEqual(c.STAGES,('metadata','array','labels','prefit','fit','replay','evaluation'))
        self.assertEqual(len(c.TARGETS),5)

    def test_missing_real_approval_stops_before_probe_and_target_loading(self):
        # Only the private import edge is mocked. There is no real approval file
        # or public calibrated lease, and no fake file is persisted.
        denied = types.SimpleNamespace(admit_authorization=Mock(side_effect=FileNotFoundError('Human authorization absent')))
        with patch.object(c.importlib,'import_module',return_value=denied),patch.object(c,'_source_module') as sources:
            with self.assertRaisesRegex(FileNotFoundError,'authorization absent'):
                with c.calibrated('metadata',MANIFEST,{}):
                    self.fail('No authorized body may run')
            sources.assert_not_called()

    def test_invalid_stage_rejected_before_any_module_import(self):
        with patch.object(c.importlib,'import_module') as imported:
            with self.assertRaises(AssertionError):
                with c.calibrated('all_projects',MANIFEST,{}):pass
            imported.assert_not_called()

    def test_exact_five_aliases_and_unrelated_fields_restore_identically(self):
        session,modules,original,memory,common = private_fixture()
        unrelated = [module.unrelated for module in modules]
        with c._installed(session,modules,original):
            self.assertFalse(session.restored)
            self.assertTrue(all(module.require_resources is session._wrapper for module in modules))
            for module in modules:
                result = module.require_resources({'physical_available':256*2**20,'disk_available':2**30},ENV)
                self.assertFalse(result['original_resource_guards_unchanged'])
            self.assertEqual(session.calls,5)
        self.assertTrue(session.restored)
        self.assertTrue(all(module.require_resources is original for module in modules))
        self.assertEqual([module.unrelated for module in modules],unrelated)
        self.assertEqual(memory.call_count,5);self.assertEqual(common.verify_owner.call_count,5)

    def test_body_exception_restores_and_marks_failure(self):
        session,modules,original,_,_ = private_fixture()
        with self.assertRaisesRegex(ValueError,'invented body'):
            with c._installed(session,modules,original):raise ValueError('invented body')
        self.assertTrue(session.restored);self.assertTrue(session.failed)
        self.assertTrue(all(module.require_resources is original for module in modules))

    def test_nested_or_duplicate_modules_cannot_replace_outer_context(self):
        session,modules,original,_,_ = private_fixture()
        other,_,_,_,_ = private_fixture()
        with c._installed(session,modules,original):
            with self.assertRaisesRegex(AssertionError,'nested'):
                with c._installed(other,modules,original):pass
            self.assertIs(c._ACTIVE,session)
        duplicate = modules[:-1]+[modules[0]]
        with self.assertRaises(AssertionError):
            with c._installed(other,duplicate,original):pass

    def test_already_replaced_alias_stops_before_any_install(self):
        session,modules,original,_,_ = private_fixture()
        replaced = lambda *args:None
        modules[2].require_resources = replaced
        with self.assertRaisesRegex(AssertionError,'already replaced'):
            with c._installed(session,modules,original):pass
        self.assertIs(modules[2].require_resources,replaced)
        self.assertTrue(all(module.require_resources is original for module in modules if module is not modules[2]))

    def test_active_replacement_is_detected_and_all_originals_restored(self):
        session,modules,original,_,_ = private_fixture()
        with self.assertRaisesRegex(RuntimeError,'transaction integrity'):
            with c._installed(session,modules,original):
                modules[1].require_resources = lambda *args:None
                modules[0].require_resources(snapshot(),ENV)
        self.assertTrue(session.restored);self.assertTrue(session.failed)
        self.assertTrue(all(module.require_resources is original for module in modules))

    def test_partial_install_exception_restores_even_the_throwing_assignment(self):
        session,modules,original,_,_ = private_fixture()
        class OnceFailing(types.ModuleType):
            def __setattr__(self,name,value):
                types.ModuleType.__setattr__(self,name,value)
                if name=='require_resources' and getattr(self,'armed',False):
                    types.ModuleType.__setattr__(self,'armed',False)
                    raise RuntimeError('invented partial install failure')
        module = OnceFailing(modules[2].__name__)
        module.armed = False;module.require_resources = original;module.armed = True
        modules[2] = module
        with self.assertRaisesRegex(RuntimeError,'partial install'):
            with c._installed(session,modules,original):pass
        self.assertTrue(session.restored);self.assertTrue(session.failed)
        self.assertTrue(all(module.require_resources is original for module in modules))

    def test_deleted_alias_still_restores_all_five_callbacks_before_integrity_error(self):
        session,modules,original,_,_ = private_fixture()
        with self.assertRaisesRegex(RuntimeError,'transaction integrity'):
            with c._installed(session,modules,original):
                del modules[2].require_resources
        self.assertTrue(session.restored);self.assertTrue(session.failed)
        self.assertIsNone(c._ACTIVE)
        self.assertTrue(all(module.require_resources is original for module in modules))

    def test_startup_and_live_boundaries_are_distinct_and_fresh(self):
        session,modules,original,memory,_ = private_fixture([snapshot(),snapshot(256*2**20),snapshot(300*2**20)])
        session._real_check(startup=True)
        with c._installed(session,modules,original):
            modules[0].require_resources(snapshot(),ENV)
            modules[1].require_resources(snapshot(),ENV)
        self.assertEqual(memory.call_count,3)
        self.assertEqual(session.minimum_physical,256*2**20)
        self.assertEqual(session.minimum_commit,2**30)
        session,_,_,_,_ = private_fixture([snapshot(512*2**20-1)])
        with self.assertRaisesRegex(AssertionError,'physical reserve'):session._real_check(startup=True)

    def test_real_low_physical_commit_or_disk_stops_despite_generous_supplied_snapshot(self):
        for actual in (snapshot(256*2**20-1),snapshot(commit=2**30-1),snapshot(disk=2**30-1)):
            session,modules,original,_,_ = private_fixture([actual])
            with self.subTest(actual=actual),self.assertRaises(AssertionError):
                with c._installed(session,modules,original):
                    modules[0].require_resources(snapshot(20*2**30),ENV)
            self.assertTrue(session.restored);self.assertTrue(session.failed)

    def test_supplied_snapshot_is_not_ignored_or_replaced_by_good_real_probe(self):
        damaged = [snapshot(256*2**20-1),snapshot(disk=2**30-1),snapshot(commit=2**30-1),
                   dict(snapshot(),physical_available=True),dict(snapshot(),PUM_resource_exception_applied=True)]
        for supplied in damaged:
            session,modules,original,memory,_ = private_fixture()
            with self.subTest(supplied=supplied),self.assertRaises(AssertionError):
                with c._installed(session,modules,original):modules[0].require_resources(supplied,ENV)
            self.assertTrue(session.restored)
            memory.assert_not_called()

    def test_actual_environment_and_supplied_environment_must_both_be_one_thread(self):
        for actual,supplied in ((ENV,dict(ENV,OMP_NUM_THREADS='2')),(dict(ENV,OMP_NUM_THREADS='2'),ENV)):
            session,modules,original,_,_ = private_fixture()
            with patch.dict(os.environ,actual),self.assertRaisesRegex(AssertionError,'one numerical thread'):
                with c._installed(session,modules,original):modules[0].require_resources(snapshot(),supplied)
            self.assertTrue(session.restored)

    def test_owner_parent_or_birth_replacement_cannot_pass(self):
        session,modules,original,_,common = private_fixture()
        changed = dict(session.owner,in_owned_job=False)
        common.verify_owner.return_value = changed
        with self.assertRaises(AssertionError):
            with c._installed(session,modules,original):modules[0].require_resources(snapshot(),ENV)
        self.assertTrue(session.restored)
        with self.assertRaises(AssertionError):c._authorization(dict(session.authorization,manifest_sha256='d'*64),'metadata',MANIFEST)

    def test_caught_guard_failure_poison_prevents_successful_context_exit(self):
        session,modules,original,_,_ = private_fixture([snapshot(256*2**20-1)])
        with self.assertRaisesRegex(AssertionError,'caught resource failure'):
            with c._installed(session,modules,original):
                try:modules[0].require_resources(snapshot(),ENV)
                except AssertionError:pass
        self.assertTrue(session.restored)
        with self.assertRaises(AssertionError):session.annotate({'status':'PASS'})

    def test_four_metadata_claims_corrected_without_altering_scientific_payload(self):
        session,modules,original,_,_ = private_fixture()
        payload = {'status':'PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION',
                   'metadata':{'rows':[{'intervention_id':'invented:1','parent_sequence':'AAA','mutant_sequence':'ACA'}],
                               'row_ids_sha256':'d'*64},
                   'contract':{'metadata_sha256':'e'*64,'splits':[{'outer_fold':0,'target_indices':[0]}]},
                   'every_payload_open_fresh_original_resource_gated':True,
                   'payload_reads':{name:{'fresh_original_resource_gate_before_open':True,'actual_sha256':str(i)*64}
                                    for i,name in enumerate(('core','paired_inventory','unmatched_inventory'),1)}}
        before = copy.deepcopy(payload)
        with c._installed(session,modules,original):annotated = session.annotate(payload)
        self.assertEqual(payload,before)
        self.assertEqual(annotated['metadata'],before['metadata']);self.assertEqual(annotated['contract'],before['contract'])
        self.assertEqual(annotated['status'],before['status'])
        self.assertFalse(annotated['every_payload_open_fresh_original_resource_gated'])
        self.assertTrue(all(row['fresh_original_resource_gate_before_open'] is False for row in annotated['payload_reads'].values()))
        self.assertFalse(annotated['resource_calibration']['callbacks_restored_at_annotation'])
        self.assertTrue(session.restored)
        self.assertEqual(len(annotated['resource_calibration']['resource_annotation_changes']),4)

    def test_recursive_operational_annotation_preserves_gate_status_and_names_calibrated_count(self):
        session,_,_,_,_ = private_fixture()
        value = {'status':'JOINT_KNOWN_CELL_DEVELOPMENT_GO','nested':[
            {'original_resource_guards_unchanged':True,'original_resource_guards_changed':False,
             'original_scientific_guards_changed':False,
             'fresh_original_resource_gates_checked':2,'source_core_read':{'fresh_original_resource_gate_before_open':True}}]}
        result = session.annotate(value)
        row = result['nested'][0]
        self.assertEqual(result['status'],value['status'])
        self.assertFalse(row['original_resource_guards_unchanged']);self.assertTrue(row['original_resource_guards_changed'])
        self.assertFalse(row['original_scientific_guards_changed'])
        self.assertEqual(row['calibrated_resource_gates_checked'],2);self.assertNotIn('fresh_original_resource_gates_checked',row)
        self.assertFalse(row['source_core_read']['fresh_original_resource_gate_before_open'])
        self.assertEqual(session.annotate({'status':'PASS_ORIGINAL_FLOOR_METADATA'})['status'],'PASS_BOUNDED_RESOURCE_CALIBRATION_METADATA')

    def test_unreviewed_guard_fields_reject_instead_of_changing_scientific_policy(self):
        session,_,_,_,_ = private_fixture()
        for value in ({'original_scientific_guards_changed':True},{'original_scientific_guard_unchanged':True},
                      {'new_original_resource_guards_unchanged':True}):
            with self.subTest(value=value),self.assertRaises(AssertionError):session.annotate(value)
        self.assertIs(session.annotate({'original_scientific_guards_changed':False})['original_scientific_guards_changed'],False)

    def test_optional_later_stage_controller_admission_is_preserved_as_provenance(self):
        session,_,_,_,_ = private_fixture()
        session.owner['stage_controller_admission_sha256'] = 'd'*64
        self.assertEqual(session.annotate({})['resource_calibration']['stage_controller_admission_sha256'],'d'*64)

    def test_resource_claim_inside_hashed_metadata_is_rejected_not_rewritten(self):
        session,_,_,_,_ = private_fixture()
        with self.assertRaisesRegex(AssertionError,'protected scientific'):
            session.annotate({'metadata':{'fresh_original_resource_gate_before_open':True}})
        first = session.annotate({'status':'PASS'})
        with self.assertRaisesRegex(AssertionError,'duplicate'):session.annotate(first)


def run():
    prohibited = ('numpy','pandas','scipy','torch','openvino','sklearn')
    def clean():return not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in prohibited)
    assert clean()
    actual_targets_before = {name:sys.modules.get(name) for name,_ in c.TARGETS}
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    assert {name:sys.modules.get(name) for name,_ in c.TARGETS}==actual_targets_before
    source = Path(__file__).resolve().parent
    sources = sorted(source.glob('*.py'))
    receipt = {'status':'PASS_INVENTED_PROPOSED_KNOWNCELL_RESOURCE_TRANSACTION_NOT_AUTHORIZATION',
               'UTC':datetime.now(timezone.utc).isoformat(),'tests':result.testsRun,
               'sources':{path.relative_to(c.ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
               'actual_workers':0,'project_payloads':0,'model_fits':0,
               'actual_resource_probes':0,'production_alias_patches':0,'scientific_imports':False,
               'human_approval_created':False,'actual_owned_job_or_lower_floor_safety_validated':False}
    output = c.ROOT/'results'/c.NS/'calibration_tests_receipt.json'
    with output.open('xb') as stream:
        stream.write((json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())


if __name__=='__main__':run()
