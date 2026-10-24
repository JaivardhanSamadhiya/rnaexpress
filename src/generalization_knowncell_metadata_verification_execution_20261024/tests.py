"""Invented provenance, parity and lifecycle checks; no actual input or Job."""
import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
from . import common as c
from . import calibration as a
from . import supervise as s
from .inputs import verify_acquisition
from .worker import _assemble_payload

SRC=c.ROOT/'src'/c.NS
OLD=c.ROOT/'src/generalization_knowncell_bounded_execution_20261023'


def run_document():
    return {'status':'ROOT_FROZEN_ACTUAL_SECOND_METADATA_INPUT_ADMISSION','invocation':c.INVOCATION,'category':'metadata',
        'generation_manifest_sha256':'a'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
        'approval_scope_sha256':c.SCOPE_SHA,'authorization_sha256':c.AUTH_SHA,'resource_policy':c.resource_policy(),
        'acquisition_namespace':c.ACQ_NS,'acquisition_generation_manifest_sha256':c.ACQ_GENERATION_SHA,
        'acquisition_retry_authorization_sha256':'c'*64,
        'input_pins':{path:c.METADATA_ADMISSION_SHA if path==c.METADATA_ADMISSION else 'd'*64 for path in c.INPUT_PATHS.values()},
        'core_path':c.CORE,'core_sha256':c.CORE_SHA,'numeric_outcome_parsing_authorized':False,
        'array_access_authorized':False,'model_fitting_authorized':False}


def node_map(path):
    tree=ast.parse(path.read_text(encoding='utf8'));result={}
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):result[node.name]=node
        if isinstance(node,ast.ClassDef):
            for child in node.body:
                if isinstance(child,ast.FunctionDef):result[node.name+'.'+child.name]=child
    return result


def provenance_fixture():
    """All JSON bodies invented; no real approval/input file is manufactured."""
    manifest={'status':'PROPOSED_ONE_CORRECTED_METADATA_ACQUISITION_AWAITING_ADDITIONAL_HUMAN_APPROVAL',
        'stages':['metadata'],'implemented_entrypoints':['metadata'],'resource_policy':c.resource_policy(),
        'original_resource_manifest_sha256':c.POLICY_SHA,'original_resource_authorization_sha256':c.AUTH_SHA,
        'original_resource_scope_sha256':c.SCOPE_SHA,'files':{'src/'+c.ACQ_NS+'/worker.py':'d'*64},
        'preserved_failed_attempt':{'results/generalization_knowncell_bounded_execution_20261023/metadata_supervisor_receipt.json':'f'*64}}
    generation=c.sha(c.canonical(manifest))
    metadata_admission={'status':'FROZEN_METADATA_ADMISSION_JOINT_KNOWNCELL','data_pins':{c.CORE:c.CORE_SHA},
                        'label_access_authorized':False,'model_fitting_authorized':False}
    mdsha=c.sha(c.canonical(metadata_admission))
    auth={'status':'EXACT_HUMAN_ONE_CORRECTED_METADATA_APPROVAL_RECORDED','answer':'Approve one corrected metadata acquisition',
        'execution_manifest_sha256':generation,'approved_stages':['metadata'],'additional_owned_invocations':1,
        'original_resource_execution_manifest_sha256':c.POLICY_SHA,'original_resource_authorization_sha256':c.AUTH_SHA,
        'original_resource_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),
        'failed_metadata_supervisor_receipt_sha256':'f'*64,'label_access_authorized':False,'model_fitting_authorized':False,
        'spending_authorized':False,'automatic_retry_authorized':False,'scientific_protocol_changes_authorized':False,
        'scheduled_tasks_authorized':False,'question':'INVENTED ONLY','question_item_id':'INVENTED'}
    authsha=c.sha(c.canonical(auth))
    birth={'stage':'metadata','automatic_retry':False,'execution_manifest_sha256':generation,
           'authorization_sha256':authsha,'resource_policy':c.resource_policy()}
    birthsha=c.sha(c.canonical(birth))
    metadata={'row_ids_sha256':'e'*64};contract={'metadata_sha256':'e'*64}
    normalization={'status':'PASS_EXACT_ORIGINAL_JSON_METADATA_SERIALIZATION_NORMALIZATION',
        'before_canonical_sha256':'e'*64,'after_canonical_sha256':'e'*64,
        'metadata_canonical_sha256':c.sha(c.canonical(metadata)),
        'contract_canonical_sha256':c.sha(c.canonical(contract)),
        'only_original_JSON_tuple_to_array_semantics':True,'scientific_values_or_hashes_changed':False}
    bundle={'status':'PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION','metadata_admission_sha256':mdsha,
        'core_sha256':c.CORE_SHA,'numeric_outcome_rows_admitted':0,'actual_feature_reads':0,'models_fitted':0,
        'every_payload_open_fresh_original_resource_gated':False,'metadata':metadata,'contract':contract,
        'resource_calibration':{'execution_manifest_sha256':generation,'authorization_sha256':authsha,
            'birth_sha256':birthsha,'stage':'metadata','scientific_metadata_and_contracts_unchanged':True},
        'metadata_serialization_normalization':normalization}
    bundlesha=c.sha(c.canonical(bundle))
    completion={'status':'PASS_CALIBRATED_METADATA_WORKER_CALLBACKS_RESTORED','execution_manifest_sha256':generation,
        'birth_sha256':birthsha,'resource_policy':c.resource_policy(),'metadata_bundle_sha256':bundlesha,
        'metadata_admission_sha256':mdsha,'callbacks_restored':True,'scientific_packages_imported':False,
        'fresh_calibrated_guard_calls':15,'original_resource_manifest_sha256':c.POLICY_SHA,
        'original_resource_authorization_sha256':c.AUTH_SHA,'original_3GiB_resource_guard_unchanged':False,
        'actual_feature_reads':0,'model_fits':0,'numerical_outcome_rows_admitted':0,
        'metadata_serialization_normalization':normalization}
    supervisor={'status':'PASS_CALIBRATED_METADATA_PENDING_INDEPENDENT_RECONSTRUCTION','failure':None,'worker_started':True,
        'execution_manifest_sha256':generation,'authorization_sha256':authsha,'resource_policy':c.resource_policy(),
        'birth_sha256':birthsha,'worker_completion_sha256':c.sha(c.canonical(completion)),
        'metadata_bundle_sha256':bundlesha,'original_3GiB_resource_guard_unchanged':False,
        'actual_feature_reads':0,'model_fits':0,'numerical_labels_admitted':0}
    values={'bundle':bundle,'acquisition_completion':completion,'acquisition_supervisor':supervisor,
            'acquisition_birth':birth,'acquisition_generation_manifest':manifest,
            'acquisition_retry_authorization':auth,'metadata_admission':metadata_admission}
    raw={key:c.canonical(value) for key,value in values.items()}
    doc=run_document();doc['acquisition_generation_manifest_sha256']=generation
    doc['acquisition_retry_authorization_sha256']=authsha
    doc['input_pins']={c.INPUT_PATHS[key]:c.sha(value) for key,value in raw.items()}
    return values,raw,doc,{'ACQ_GENERATION_SHA':generation,'METADATA_ADMISSION_SHA':mdsha}


def terminal_fixture():
    admission=run_document();contract={'row_ids_sha256':c.HELPER_ROW_IDS_SHA,'metadata_sha256':'e'*64}
    compact=(json.dumps(contract,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode()
    independent={'status':c.HELPER_STATUS,'counts':dict(c.HELPER_COUNTS),'row_ids_sha256':c.HELPER_ROW_IDS_SHA,
        'metadata_sha256':'e'*64,'all_core_ids_sha256':'f'*64,'all_core_rows_independently_parsed':26258,
        'outer_masks_rebuilt':3,'inner_masks_rebuilt':6,'reconstructed_contract':contract,
        'canonical_contract_sha256':c.sha(compact),'parsed_outcome_values':0,'model_fits':0,
        'requires_guarded_original_CORE_SHA_and_Git_ownership_from_caller':True}
    for key in ('source_CSV_metadata_derivation_independently_verified','original_core_position_alignment_independently_verified',
                'nonMikl_full_core_ID_roster_independently_verified','both_cells_used_for_every_purge',
                'source_and_target_full_menus_preserved','original_row_order_preserved'):independent[key]=True
    for key in ('raw_CORE_byte_SHA_proven_here','author_biological_lineage_independently_verified','reference_builder_or_parser_called',
                'metadata_rows_normalized_or_modified','extra_filtering_or_gene_alias_repair','array_label_or_FIT_permission_granted',
                'unused_outcome_fields_numerically_converted'):independent[key]=False
    protected=c.sha(c.canonical(independent))
    value={'status':'PASS_INDEPENDENT_METADATA_DERIVATION_AND_CONTRACT_WITH_OWNED_RAW_READ_PROOF',
        'invocation':c.INVOCATION,'category':'metadata','generation_manifest_sha256':'a'*64,'parent_pid':111,'worker_pid':222,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'run_admission_sha256':'b'*64,'birth_sha256':'c'*64,'independent_helper_source_manifest_sha256':c.HELPER_MANIFEST_SHA,
        'acquisition_input_hashes':admission['input_pins'],'acquisition_source_generation_sha256':c.ACQ_GENERATION_SHA,
        'each_acquisition_input_committed_bytes_checked':True,'array_label_or_FIT_permission_granted':False,
        'numerical_outcomes_admitted':0,'actual_feature_reads':0,'model_fits':0,'canonical_scientific_values_preserved':True,
        'outer_raw_CORE_SHA_verified_against_frozen_admission':True,'original_resource_guards_unchanged':False,
        'payload_reads':{key:{'actual_sha256':admission['input_pins'][path],'raw_bytes_traversed':1,
                             'fresh_original_resource_gate_before_open':False} for key,path in c.INPUT_PATHS.items()},
        'core_read':{'actual_sha256':c.CORE_SHA,'raw_bytes_traversed':1,'fresh_original_resource_gate_before_open':False},
        'independent_verification':independent,'independent_verifier_canonical_sha256':protected,
        'resource_calibration':{'execution_manifest_sha256':'a'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
            'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,'invocation':c.INVOCATION,'stage':'metadata',
            'birth_sha256':'c'*64,'parent_pid':111,'current_pid':222,'callbacks_restored_at_annotation':False,
            'fresh_calibrated_guard_calls':15,'startup_physical_floor':512*2**20,'live_physical_floor':256*2**20,
            'disk_floor':2**30,'live_global_commit_reserve':2**30,'scientific_protocol_settings_changed':False,
            'scientific_metadata_and_contracts_unchanged':True}}
    completion={'status':'PASS_SECOND_METADATA_WORKER_INDEPENDENT_CONTRACT_CALLBACKS_RESTORED',
        'invocation':c.INVOCATION,'category':'metadata','generation_manifest_sha256':'a'*64,'parent_pid':111,'worker_pid':222,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'run_admission_sha256':'b'*64,'birth_sha256':'c'*64,'callbacks_restored':True,'fresh_calibrated_guard_calls':15,
        'numerical_outcomes_admitted':0,'actual_feature_reads':0,'model_fits':0,'scientific_packages_imported':False,
        'original_3GiB_resource_guard_unchanged':False,'resource_policy':c.resource_policy(),
        'independent_report_sha256':c.sha(c.canonical(value)),'independent_helper_source_manifest_sha256':c.HELPER_MANIFEST_SHA,
        'independent_helper_result_canonical_sha256':protected,'metadata_counts':dict(c.HELPER_COUNTS),
        'row_ids_sha256':c.HELPER_ROW_IDS_SHA,'metadata_sha256':'e'*64,'all_core_ids_sha256':'f'*64}
    return value,completion,admission


class Checks(unittest.TestCase):
    def test_guard_and_restoration_bodies_identical_to_frozen_production(self):
        old=node_map(OLD/'calibration.py');new=node_map(SRC/'calibration.py')
        names=('_sha','_hash','_environment','_snapshot','_owner','_resource_key','_check_scientific_subtree',
               '_annotated_copy','_plain_copy','_installed','_source_module','_Session.__init__',
               '_Session._real_check','_Session._aliases','_Session._invoke')
        for name in names:
            self.assertEqual(ast.dump(old[name]),ast.dump(new[name]),name)

    def test_monitor_body_identical_to_corrected_frozen_controller(self):
        self.assertEqual(ast.dump(node_map(OLD/'supervise.py')['observe']),
                         ast.dump(node_map(SRC/'monitor.py')['observe']))
        self.assertIs(c.resource_failure,c.policy.resource_failure)
        self.assertIs(c.resource_policy,c.policy.resource_policy)

    def test_exact_five_targets_thresholds_and_resource_annotation_allowlist(self):
        old=ast.parse((OLD/'calibration.py').read_text(encoding='utf8'))
        literals={x.targets[0].id:ast.literal_eval(x.value) for x in old.body if isinstance(x,ast.Assign)
                  and len(x.targets)==1 and isinstance(x.targets[0],ast.Name) and x.targets[0].id in ('TARGETS','RESOURCE_BOOLEANS')}
        self.assertEqual(a.TARGETS,literals['TARGETS']);self.assertEqual(len(a.TARGETS),5)
        self.assertEqual(a.RESOURCE_BOOLEANS,literals['RESOURCE_BOOLEANS'])
        self.assertEqual((a.STARTUP_PHYSICAL,a.LIVE_PHYSICAL),(512*2**20,256*2**20))
        p=c.resource_policy();self.assertEqual(p['startup_commit_headroom'],1920*2**20)
        self.assertEqual((p['process_cap'],p['job_cap'],p['lifetime_seconds_per_stage']),(768*2**20,896*2**20,1800))

    def test_new_production_common_and_distinct_birth_paths(self):
        self.assertEqual(a.NS,c.NS)
        self.assertNotEqual(c.BIRTH,c.policy.birth_path('metadata'))
        self.assertTrue(c.BIRTH.is_relative_to(c.OUT))
        self.assertEqual(c.birth_path('metadata'),c.BIRTH)
        with self.assertRaises(AssertionError):c.birth_path('fit')
        self.assertEqual(c.INVOCATION,'independent_metadata_verification')

    def test_generation_and_approved_policy_identities_are_not_relabelled(self):
        value={'generation_manifest_sha256':'a'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
               'approval_scope_sha256':c.SCOPE_SHA,'approval_sha256':c.AUTH_SHA,'approved_invocation':c.INVOCATION,
               'explicit_human_approval':True,'owned_job_required':True,'allowed_stages':list(c.STAGES)}
        self.assertEqual(a._authorization(value,'metadata','a'*64),value)
        for key,wrong in (('generation_manifest_sha256','b'*64),('approved_policy_manifest_sha256','a'*64),
                          ('approved_invocation','metadata_acquisition'),('approval_scope_sha256','b'*64)):
            bad=dict(value);bad[key]=wrong
            with self.assertRaises(AssertionError):a._authorization(bad,'metadata','a'*64)

    def test_actual_run_input_contract_has_exact_aliases_and_forbids_new_labels(self):
        doc=run_document();self.assertIs(c.run_contract(doc,'a'*64),doc)
        for field,wrong in (('invocation','metadata_acquisition'),('category','fit'),
                            ('generation_manifest_sha256','b'*64),('core_sha256','a'*64),
                            ('numeric_outcome_parsing_authorized',True),('array_access_authorized',True)):
            bad=copy.deepcopy(doc);bad[field]=wrong
            with self.assertRaises(AssertionError):c.run_contract(bad,'a'*64)
        bad=copy.deepcopy(doc);bad['input_pins']['invented_other.csv']='f'*64
        with self.assertRaises(AssertionError):c.run_contract(bad,'a'*64)

    def test_missing_or_changed_input_admission_fails_before_any_commit_helper(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invented.json'
            with patch.object(c,'RUN_ADMISSION',path),patch.object(c,'committed') as git:
                with self.assertRaises(FileNotFoundError):c.read_run('a'*64,'b'*64,check_commit=True)
                path.write_bytes(c.canonical(run_document()))
                with self.assertRaisesRegex(AssertionError,'Initial input admission'):c.read_run('a'*64,'b'*64,check_commit=True)
                git.assert_not_called()

    def test_owner_wrong_parent_fails_before_birth_or_native_access(self):
        with patch.object(c,'source_mode',return_value={}),patch.object(c.os,'getppid',return_value=10),\
             patch.object(Path,'read_bytes',side_effect=AssertionError('must not read')):
            with self.assertRaises(AssertionError):c.verify_owner('metadata','a'*64,{
                'parent_pid':11,'birth_sha256':'b'*64,'run_admission_sha256':'c'*64})

    def test_root_start_or_missing_actual_admission_never_reaches_output_creation(self):
        with patch.object(c,'admit_authorization') as admit:
            with self.assertRaises(AssertionError):s.run('a'*64,'b'*64)
            admit.assert_not_called()
        with patch.object(c,'admit_authorization',return_value={}),\
             patch.object(c,'read_run',side_effect=FileNotFoundError('invented no actual admission')),\
             patch.object(c,'require_new_outputs') as outputs,patch.object(c,'save_new') as birth:
            with self.assertRaises(FileNotFoundError):s.run('a'*64,'b'*64,root_start=True)
            outputs.assert_not_called();birth.assert_not_called()

    def test_every_partial_output_prevents_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            paths=[Path(folder)/str(i) for i in range(5)]
            with patch.multiple(c,BIRTH=paths[0],WORKER_LOG=paths[1],COMPLETION=paths[2],SUPERVISOR=paths[3],REPORT=paths[4]):
                c.require_new_outputs()
                for path in paths:
                    path.write_text('invented retained')
                    with self.assertRaisesRegex(AssertionError,'no resume'):c.require_new_outputs()
                    self.assertEqual(path.read_text(),'invented retained');path.unlink()

    def test_explicit_child_command_carries_both_initial_identities_and_new_birth(self):
        command=s.command('a'*64,'b'*64,'c'*64)
        self.assertEqual(command[1:4],['-S','-B','-X'])
        self.assertEqual(command[-5:],['src.'+c.NS+'.worker',str(os.getpid()),'a'*64,'b'*64,'c'*64])
        self.assertIn('pycache_prefix='+str(c.CACHE_PREFIX),command)

    def test_json_boundary_tuple_normalization_preserves_scientific_canonical_hash(self):
        value={'metadata':{'rows':[{'intervention_id':'invented'}]},
               'contract':{'pairs':[{'mutant_sequences':('ACA','ATA')}],'splits':[{'mask':(1,2)}]}}
        raw=c.canonical(value);normalized=c.json_normalized(value)
        self.assertEqual(c.canonical(normalized),raw)
        self.assertEqual(c.sha(c.canonical(normalized['contract'])),c.sha(c.canonical(value['contract'])))
        self.assertEqual(normalized['contract']['pairs'][0]['mutant_sequences'],['ACA','ATA'])
        self.assertIsInstance(value['contract']['pairs'][0]['mutant_sequences'],tuple)

    def test_scientific_helper_flags_stay_outside_operational_annotation(self):
        class InventedSession:
            def annotate(self,payload):
                return a._annotated_copy(payload,[],[])
        scientific={'requires_guarded_original_CORE_SHA_and_Git_ownership_from_caller':True,
                    'raw_CORE_byte_SHA_proven_here':False,'reconstructed_contract':{'pairs':[(1,2)]}}
        before=c.canonical(scientific)
        with self.assertRaisesRegex(AssertionError,'Unreviewed'):
            a._annotated_copy(scientific,[],[])
        result=_assemble_payload(InventedSession(),{'payload_reads':{'core':{
            'actual_sha256':'d'*64,'fresh_original_resource_gate_before_open':True}}},scientific)
        self.assertEqual(c.canonical(result['independent_verification']),before)
        self.assertFalse(result['payload_reads']['core']['fresh_original_resource_gate_before_open'])
        self.assertEqual(result['independent_verifier_canonical_sha256'],c.sha(before))

    def test_failed_first_acquisition_status_is_never_promoted(self):
        doc=run_document();raws={key:c.canonical({}) for key in c.INPUT_PATHS}
        doc['input_pins']={c.INPUT_PATHS[key]:c.sha(raw) for key,raw in raws.items()}
        with self.assertRaises((AssertionError,KeyError)):verify_acquisition(raws,doc)
        self.assertNotEqual(c.ACQ_NS,'generalization_knowncell_bounded_execution_20261023')

    def test_corrected_provenance_links_and_failed_status_rejection_on_invented_bodies(self):
        values,raw,doc,overrides=provenance_fixture()
        # Private invented constants are patched only in this new test module's
        # sibling namespace. No real approval/input path or producer is invoked.
        with patch.multiple(c,**overrides):
            c.run_contract(doc,'a'*64)
            self.assertEqual(verify_acquisition(raw,doc),values['bundle'])
            for key,field,wrong in (('acquisition_supervisor','status','FAILED_OR_BLOCKED_CALIBRATED_ATTEMPT_PRESERVED_NO_RETRY'),
                                    ('acquisition_completion','callbacks_restored',False),
                                    ('acquisition_retry_authorization','answer','Approve this exact known-cell resource calibration')):
                damaged=copy.deepcopy(values);damaged[key][field]=wrong
                damaged_raw={name:c.canonical(value) for name,value in damaged.items()}
                altered=copy.deepcopy(doc)
                altered['input_pins']={c.INPUT_PATHS[name]:c.sha(value) for name,value in damaged_raw.items()}
                if key=='acquisition_retry_authorization':
                    altered['acquisition_retry_authorization_sha256']=c.sha(damaged_raw[key])
                with self.subTest(key=key),self.assertRaises(AssertionError):verify_acquisition(damaged_raw,altered)

    def test_completion_requires_new_identity_restoration_and_zero_scientific_access(self):
        _,value,_=terminal_fixture()
        self.assertIs(s.completion_contract(value,'a'*64,'b'*64,'c'*64,parent_pid=111,worker_pid=222),value)
        for field,wrong in (('callbacks_restored',False),('model_fits',1),('scientific_packages_imported',True),
                            ('generation_manifest_sha256',c.POLICY_SHA),('original_3GiB_resource_guard_unchanged',True)):
            bad=dict(value);bad[field]=wrong
            with self.assertRaises(AssertionError):s.completion_contract(bad,'a'*64,'b'*64,'c'*64,parent_pid=111,worker_pid=222)

    def test_terminal_report_semantics_bind_owner_core_helper_counts_and_protected_hash(self):
        value,completion,admission=terminal_fixture()
        checked=s.validate_report(c.canonical(value),'a'*64,'b'*64,'c'*64,completion,admission,parent_pid=111,worker_pid=222)
        self.assertEqual(checked,value)
        for target,field,wrong in (('top','worker_pid',333),('core','actual_sha256','f'*64),
                                  ('helper','status','PASS_INVENTED_ONLY'),('helper','source_CSV_metadata_derivation_independently_verified',False),
                                  ('helper','counts',dict(c.HELPER_COUNTS,all_rows=13780)),
                                  ('top','independent_helper_source_manifest_sha256','f'*64),
                                  ('helper','metadata_sha256','f'*64)):
            damaged=copy.deepcopy(value)
            owner=damaged if target=='top' else damaged['core_read'] if target=='core' else damaged['independent_verification']
            owner[field]=wrong
            # A hash-only terminal certification would accept rehashed bytes;
            # these immutable semantic bindings must still reject the report.
            changed_completion=dict(completion,independent_report_sha256=c.sha(c.canonical(damaged)))
            with self.subTest(target=target,field=field),self.assertRaises(AssertionError):
                s.validate_report(c.canonical(damaged),'a'*64,'b'*64,'c'*64,changed_completion,admission,parent_pid=111,worker_pid=222)

    def test_no_eager_scientific_imports_or_work_at_import(self):
        for path in SRC.glob('*.py'):
            tree=ast.parse(path.read_text(encoding='utf8'))
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):self.assertFalse(any(x.name.split('.')[0] in ('numpy','pandas','scipy','torch') for x in node.names))
                if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').split('.')[0] in ('numpy','pandas','scipy','torch'))


def run():
    assert not c.RUN_ADMISSION.exists(),'Invented tests never create or use actual input admission'
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for name in sys.modules)
    c.save_new(c.OUT/'synthetic_tests_receipt_reviewed.json',{
        'status':'PASS_INVENTED_SECOND_METADATA_PRODUCTION_SOURCE_NOT_ACTUAL_EXECUTION',
        'tests':result.testsRun,'source_files':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in SRC.glob('*.py')},
        'actual_jobs':0,'actual_resource_probes':0,'project_payloads_read':0,'model_fits':0,
        'scientific_imports':False,'original_326_sources_modified':False,
        'actual_approval_records_created':False,
        'actual_input_admission_present':False,'guard_restore_and_monitor_source_parity':True})


if __name__=='__main__':run()
