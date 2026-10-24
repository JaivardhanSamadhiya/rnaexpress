"""Invented genuine tuple-contract regression; no worker, probes or inputs."""
import ast
import copy
import hashlib
import inspect
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import common as c,worker as w,calibration as calibration,supervise as supervise
from src.generalization_knowncell_joint_implementation_20261022 import contracts as metadata
from src.generalization_knowncell_joint_implementation_20261022.tests import rows_fixture

OLD = c.ROOT/'src'/c.ORIGINAL_NS
SRC = c.ROOT/'src'/c.NS


def genuine_contract_fixture():
    rows = rows_fixture(unequal=True,unmatched=True)
    pairs,unmatched = metadata.exact_pairs(rows)
    paired_contexts = {context for pair in pairs for context in pair['contexts'].values()}
    counts = {'all_rows':len(rows),'CAD_rows':sum(row['cell_type']=='CAD' for row in rows),
              'Neuro-2a_rows':sum(row['cell_type']=='Neuro-2a' for row in rows),
              'components':len({row['biological_component'] for row in rows}),
              'paired_menus':len(pairs),'paired_rows':sum(row['parent_context_id'] in paired_contexts for row in rows),
              'paired_contexts':len(paired_contexts),'paired_directional_decisions':2*len(paired_contexts),
              'unmatched_contexts':len(unmatched),'unmatched_rows':sum(row['parent_context_id'] in unmatched for row in rows)}
    original_counts = metadata.COUNTS
    with patch.object(metadata,'COUNTS',counts):
        # This is the ORIGINAL pure implementation, not a handwritten contract.
        contract = metadata.full_metadata_contract(rows)
    assert metadata.COUNTS is original_counts
    return {'status':'PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION',
            'metadata':{'rows':rows,'row_ids_sha256':metadata.ids_sha(rows),'whole_core_bytes_traversed':True},
            'contract':contract,'metadata_admission_sha256':'a'*64,'numeric_outcome_rows_admitted':0,
            'actual_feature_reads':0,'models_fitted':0,'every_payload_open_fresh_original_resource_gated':True,
            'payload_reads':{name:{'fresh_original_resource_gate_before_open':True,'actual_sha256':str(i)*64}
                             for i,name in enumerate(('core','paired_inventory','unmatched_inventory'),1)}}


def private_annotator():
    owner = {'current_pid':os.getpid(),'parent_pid':os.getppid(),'birth_sha256':'b'*64}
    return calibration._Session('metadata','c'*64,{'approval_sha256':'d'*64},owner,
                                {'parent_pid':os.getppid(),'birth_sha256':'b'*64},
                                lambda:(_ for _ in ()).throw(AssertionError('No native or fake probe should run')),
                                SimpleNamespace())


def retry_approval():
    return {'status':'EXACT_HUMAN_ONE_CORRECTED_METADATA_APPROVAL_RECORDED','execution_manifest_sha256':'e'*64,
            'approved_stages':['metadata'],'additional_owned_invocations':1,
            'original_resource_execution_manifest_sha256':c.ORIGINAL_MANIFEST_SHA,
            'original_resource_authorization_sha256':c.ORIGINAL_AUTH_SHA,'original_resource_scope_sha256':c.ORIGINAL_SCOPE_SHA,
            'failed_metadata_supervisor_receipt_sha256':c.PRESERVED_FAILURE['results/'+c.ORIGINAL_NS+'/metadata_supervisor_receipt.json'],
            'resource_policy':c.resource_policy(),'spending_authorized':False,'scientific_protocol_changes_authorized':False,
            'label_access_authorized':False,'model_fitting_authorized':False,
            'automatic_retry_authorized':False,'scheduled_tasks_authorized':False,
            'question':'Invented parser fixture only, not an asked or answered human question',
            'question_item_id':'invented-test-only','answer':'Approve one corrected metadata acquisition'}


def ast_functions(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    return {node.name:ast.dump(node,include_attributes=False) for node in tree.body
            if isinstance(node,(ast.FunctionDef,ast.ClassDef))}


class Cases(unittest.TestCase):
    def test_original_full_metadata_contract_really_contains_the_failed_tuple_shape(self):
        bundle = genuine_contract_fixture()
        self.assertIsInstance(bundle['contract']['pairs'][0]['mutant_sequences'],tuple)
        self.assertEqual(bundle['contract']['row_ids_sha256'],bundle['metadata']['row_ids_sha256'])
        with self.assertRaisesRegex(AssertionError,'JSON receipts'):
            private_annotator().annotate(bundle)

    def test_normalization_preserves_exact_original_json_bytes_and_all_scientific_hashes(self):
        bundle = genuine_contract_fixture();before = c.canonical(bundle)
        original = copy.deepcopy(bundle)
        normalized,proof = w.normalize_metadata_bundle(bundle)
        self.assertEqual(c.canonical(normalized),before)
        self.assertEqual(bundle,original)
        self.assertIsInstance(normalized['contract']['pairs'][0]['mutant_sequences'],list)
        self.assertEqual(proof['before_canonical_sha256'],proof['after_canonical_sha256'])
        self.assertEqual(proof['metadata_canonical_sha256'],c.sha(c.canonical(bundle['metadata'])))
        self.assertEqual(proof['contract_canonical_sha256'],c.sha(c.canonical(bundle['contract'])))
        self.assertEqual(metadata.ids_sha(normalized['metadata']['rows']),metadata.ids_sha(bundle['metadata']['rows']))
        self.assertEqual(metadata.metadata_sha(normalized['metadata']['rows']),metadata.metadata_sha(bundle['metadata']['rows']))
        annotated = private_annotator().annotate(normalized)
        self.assertEqual(c.canonical(annotated['metadata']),c.canonical(bundle['metadata']))
        self.assertEqual(c.canonical(annotated['contract']),c.canonical(bundle['contract']))
        self.assertFalse(annotated['every_payload_open_fresh_original_resource_gated'])
        self.assertTrue(all(item['fresh_original_resource_gate_before_open'] is False for item in annotated['payload_reads'].values()))

    def test_normalization_does_not_create_broad_tuple_or_nonjson_acceptance(self):
        with self.assertRaises(AssertionError):calibration._plain_copy((1,2))
        bundle = genuine_contract_fixture();bundle['unserializable'] = object()
        with self.assertRaises(TypeError):w.normalize_metadata_bundle(bundle)
        with self.assertRaises(AssertionError):c.relative('../outside')
        with self.assertRaises(AssertionError):
            calibration._snapshot({'physical_available':True,'disk_available':2**30},
                                  {name:'1' for name in calibration.THREAD_KEYS})

    def test_every_calibration_function_and_class_body_is_identical_to_frozen_original(self):
        self.assertEqual(ast_functions(OLD/'calibration.py'),ast_functions(SRC/'calibration.py'))
        self.assertEqual(calibration.STAGES,('metadata',))
        self.assertEqual(calibration.NS,c.NS)
        self.assertEqual(len(calibration.TARGETS),5)
        text=(SRC/'calibration.py').read_text(encoding='utf-8')
        self.assertNotIn(c.ORIGINAL_NS,text)
        self.assertEqual(set(inspect.signature(calibration.calibrated).parameters),{'stage','manifest_sha','owner_evidence'})

    def test_supervisor_monitor_command_and_resource_policy_functions_are_unchanged(self):
        old_super,new_super=ast_functions(OLD/'supervise.py'),ast_functions(SRC/'supervise.py')
        for name in ('observe','command'):
            self.assertEqual(old_super[name],new_super[name],name)
        old,new = ast_functions(OLD/'common.py'),ast_functions(SRC/'common.py')
        for name in ('resource_policy','resource_failure','source_mode','save_new','verify_owner','relative','valid_sha'):
            self.assertEqual(old[name],new[name],name)
        command=supervise.command('metadata','e'*64,'f'*64)
        self.assertIn('src.'+c.NS+'.worker',command)
        with self.assertRaises(AssertionError):supervise.command('array','e'*64,'f'*64)

    def test_new_authorization_is_exactly_one_corrected_metadata_attempt(self):
        self.assertTrue(c.approval_contract(retry_approval(),'e'*64))
        for key,value in (('answer','Approve this exact known-cell resource calibration'),('approved_stages',['metadata','array']),
                          ('additional_owned_invocations',2),('execution_manifest_sha256','0'*64),
                          ('original_resource_authorization_sha256','0'*64),('label_access_authorized',True),
                          ('automatic_retry_authorized',True)):
            document=retry_approval();document[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):c.approval_contract(document,'e'*64)

    def test_original_approval_does_not_satisfy_new_retry_contract(self):
        record=retry_approval();record['status']='EXACT_HUMAN_KNOWNCELL_RESOURCE_APPROVAL_RECORDED'
        with self.assertRaises(AssertionError):c.approval_contract(record,'e'*64)
        self.assertNotEqual(c.AUTH,c.ROOT/c.ORIGINAL_AUTH)
        self.assertEqual(c.STAGES,('metadata',))
        self.assertEqual(c.IMPLEMENTED_STAGES,('metadata',))

    def test_original_evidence_parses_only_captured_hash_and_git_checked_bytes(self):
        from src.generalization_knowncell_bounded_execution_20261023 import common as original
        names={c.ORIGINAL_MANIFEST:c.ORIGINAL_MANIFEST_SHA,c.ORIGINAL_AUTH:c.ORIGINAL_AUTH_SHA,
               c.ORIGINAL_SCOPE:c.ORIGINAL_SCOPE_SHA,**c.PRESERVED_FAILURE}
        document={'approval_scope_sha256':c.ORIGINAL_SCOPE_SHA,'approved_owned_invocations':c.ORIGINAL_INVOCATIONS}
        failed='results/'+c.ORIGINAL_NS+'/metadata_supervisor_receipt.json'
        failure={'status':'FAILED_OR_BLOCKED_CALIBRATED_ATTEMPT_PRESERVED_NO_RETRY',
                 'execution_manifest_sha256':c.ORIGINAL_MANIFEST_SHA,'authorization_sha256':c.ORIGINAL_AUTH_SHA,
                 'metadata_bundle_sha256':None,'worker_completion_sha256':None,
                 'numerical_labels_admitted':0,'actual_feature_reads':0,'model_fits':0}
        supplied={name:('invented '+name).encode() for name in names}
        supplied[c.ORIGINAL_AUTH]=c.canonical(document);supplied[failed]=c.canonical(failure)
        hash_map={raw:names[name] for name,raw in supplied.items()}
        reads=[]
        def read(path):
            name=path.relative_to(c.ROOT).as_posix();reads.append(name)
            assert reads.count(name)==1,'Evidence must not be reopened after captured verification'
            return supplied[name]
        with patch.object(Path,'read_bytes',read),patch.object(c,'sha',side_effect=lambda raw:hash_map[raw]),\
             patch.object(c,'committed') as committed,patch.object(original,'approval_contract',return_value=True):
            evidence=c.verify_original_evidence()
        self.assertEqual(set(reads),set(names));self.assertEqual(committed.call_count,len(names))
        self.assertEqual(evidence['original_resource_authorization_sha256'],c.ORIGINAL_AUTH_SHA)

    def test_supervisor_binds_normalization_to_actual_supplied_terminal_json(self):
        normalized,proof=w.normalize_metadata_bundle(genuine_contract_fixture())
        bundle=private_annotator().annotate(normalized)
        bundle['metadata_serialization_normalization']=proof
        completion={'metadata_serialization_normalization':proof,
                    'original_resource_manifest_sha256':c.ORIGINAL_MANIFEST_SHA,
                    'original_resource_authorization_sha256':c.ORIGINAL_AUTH_SHA,
                    'row_ids_sha256':bundle['metadata']['row_ids_sha256'],
                    'metadata_sha256':bundle['contract']['metadata_sha256'],
                    'metadata_admission_sha256':bundle['metadata_admission_sha256']}
        self.assertEqual(supervise.validate_normalization(completion,c.canonical(bundle)),proof)
        for field in ('metadata','contract'):
            changed=copy.deepcopy(bundle);changed[field]['injected']='changed'
            with self.subTest(field=field),self.assertRaises(AssertionError):
                supervise.validate_normalization(completion,c.canonical(changed))
        changed=copy.deepcopy(completion);changed['metadata_serialization_normalization']['after_canonical_sha256']='0'*64
        with self.assertRaises(AssertionError):supervise.validate_normalization(changed,c.canonical(bundle))

    def test_future_factory_uses_fixed_new_common_and_no_callback_rebinding(self):
        with patch.object(calibration.importlib,'import_module') as imported:
            imported.return_value=SimpleNamespace(admit_authorization=lambda value:(_ for _ in ()).throw(FileNotFoundError('Retry approval absent')))
            with self.assertRaisesRegex(FileNotFoundError,'approval absent'):
                with calibration.calibrated('metadata','e'*64,{}):self.fail('No actual authorized context')
            imported.assert_called_once_with('src.'+c.NS+'.common')


def run():
    forbidden=('numpy','pandas','scipy','torch','sklearn','openvino')
    def clean():return not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in forbidden)
    assert clean() and not c.AUTH.exists()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources=sorted(SRC.glob('*.py'))
    for path in sources:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    receipt={'status':'PASS_INVENTED_CORRECTED_METADATA_JSON_REGRESSION_NOT_RETRY_AUTHORIZATION',
             'UTC':c.datetime.now(c.timezone.utc).isoformat(),'tests':result.testsRun,
             'sources':{path.relative_to(c.ROOT).as_posix():c.sha(path.read_bytes()) for path in sources},
             'actual_workers':0,'actual_resource_probes':0,'project_metadata_reads':0,'project_array_reads':0,
             'project_label_reads':0,'model_fits':0,'production_alias_patches':0,'actual_approval_created':False,
             'original_pure_contract_called_with_invented_fixture_and_test_only_counts':True,
             'native_or_scientific_imports':False,'corrected_full_size_serialization_not_executed':True}
    c.save_new(c.OUT/'synthetic_tests_receipt.json',receipt)


if __name__=='__main__':run()
