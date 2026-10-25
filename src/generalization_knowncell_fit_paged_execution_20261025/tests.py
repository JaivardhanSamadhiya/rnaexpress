"""Invented exact-input and owned fixed-FIT controller tests; no native calls."""
import ast
import copy
import json
import tempfile
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import common as c,inputs,build,worker as w,supervise as supervisor,calibration as cal,projection_io as projection_io
from . import resident,monitor
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_prefit_execution_20261024.tests import old_document,Matrix,Archive

class Cases(unittest.TestCase):
    def setUp(self):
        changed=patch.object(c,'NUMERIC_PAGING_PROFILE_SHA','a'*64)
        changed.start();self.addCleanup(changed.stop)

    def evidence(self):
        return {'owned_working_set_toy_sha256':c.PAGING_TOY_SHA,'numerical_paging_profile_sha256':c.NUMERIC_PAGING_PROFILE_SHA}

    def resident_cap(self):
        return {'before':{'minimum':204800,'maximum':1413120,'flags':10},
            'after':{'minimum':204800,'maximum':190*2**20,'flags':6},
            'only_suspended_owned_child_changed':True,'private_and_job_caps_or_live_guards_changed':False}

    def successful_observed(self):
        return {'owned_working_set_cap':self.resident_cap(),'measured_resident_ceiling':c.RESIDENT_MEASURED_CEILING,
            'resident_configuration_checks':1,'final_lifetime_resident_counters_checked':True,
            'peak_working_set':190*2**20,'final_process_handle_peak_sample':{'working_set':0,'peak_working_set':190*2**20}}

    def test_actual_additional_human_response_and_exact_failed_attempt_required(self):
        value={'status':'EXPLICIT_HUMAN_AUTHORIZATION_ONE_PAGED_FIXED_KNOWNCELL_FIT',
            'approved_answer':c.RETRY_ANSWER,'explicit_human_response_recorded':True,'generation_manifest_sha256':'1'*64,
            'approval_scope_sha256':'2'*64,'interrupted_attempt_audit_sha256':c.INTERRUPTED_AUDIT_SHA,
            'additional_attempts_authorized':1,'partial_resume_authorized':False,'automatic_retry_authorized':False,
            'spending_authorized':False,'minimum_startup_physical_available':c.RETRY_STARTUP_PHYSICAL,
            'owned_resident_policy':c.resident_policy(),'paging_evidence':self.evidence()}
        value['managed_supervisor_required']=True
        c.retry_authorization_contract(value,'1'*64,'2'*64)
        for key,bad in [('approved_answer','continue'),('explicit_human_response_recorded',False),
                ('additional_attempts_authorized',2),('partial_resume_authorized',True),
                ('interrupted_attempt_audit_sha256','0'*64),('generation_manifest_sha256','0'*64),
                ('approval_scope_sha256','0'*64),('spending_authorized',True),('managed_supervisor_required',False)]:
            changed=dict(value);changed[key]=bad
            with self.subTest(key=key),self.assertRaises(AssertionError):c.retry_authorization_contract(changed,'1'*64,'2'*64)

    def test_one_GiB_paged_startup_and_original_active_policy_unchanged(self):
        memory={'physical_available':2**30,'commit_headroom':3*2**30,'disk_available':2*2**30}
        self.assertIsNone(c.resource_failure(memory,0,startup=True))
        memory['physical_available']-=1
        self.assertIsNotNone(c.resource_failure(memory,0,startup=True))
        self.assertIsNone(c.resource_failure(memory,0))
        memory['physical_available']=256*2**20-1
        self.assertIsNotNone(c.resource_failure(memory,0))
    def source_and_manifest(self):
        m={'files':{c.WORKER_SOURCE:'5'*64,c.runtime.PREPARATION:'6'*64,c.BRIDGE_READY:'7'*64}}
        r={'status':'REVIEWED_SOURCE_ONLY_FIXED_FIT_CONTROLLER_NOT_INPUT_OR_FIT_AUTHORITY',
            'stage':c.STAGE,'invocation':c.INVOCATION,'generation_manifest_sha256':'1'*64,
            'controller_source':c.WORKER_SOURCE,'controller_source_sha256':'5'*64,
            'runtime_provider_preparation_sha256':'6'*64,'bridge_readiness_sha256':'7'*64,
            'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,
            'approval_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),
            'actual_input_or_FIT_authority_granted':False,'stable_scientific_source_bindings':dict(c.STABLE_SCIENTIFIC_BINDINGS)}
        return r,m

    def run_record(self):
        pins={**c.INPUT_PINS,c.REQUEST:'2'*64,c.STATIC_BINDING:'3'*64,
            c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix():'4'*64,
            **{name:'5'*64 for name in (c.PREFIT,c.PREFIT_COMPLETION,c.PREFIT_SUPERVISOR,c.PROJECTION_ADMISSION)}}
        return {'status':'FROZEN_ONE_EXACT63_CHECKPOINT84_UNIT_FIT_RUN','stage':c.STAGE,'invocation':c.INVOCATION,
            'generation_manifest_sha256':'1'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
            'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),
            'runtime_import_authorized':True,'array_reload_authorized':True,'saved_label_read_authorized':True,
            'pool_preparation_authorized':True,'model_fitting_authorized':True,'CORE_read_authorized':False,
            'data_pins':{c.NPZ:c.NPZ_SHA},'input_pins':pins,'actual_prefit_commit':'a'*40,
            'projection_root_admission_commit':'b'*40,'checkpoint_count':63,'optimizer_units':84,'resume':False,
            'retry_authorization_sha256':'7'*64,'minimum_startup_physical_available':c.RETRY_STARTUP_PHYSICAL,
            'interrupted_attempt_audit_sha256':c.INTERRUPTED_AUDIT_SHA,'managed_supervisor_required':True,
            'owned_resident_policy':c.resident_policy(),'paging_evidence':self.evidence()}

    def test_source_admission_has_no_temporal_cycle_or_changed_scientific_sources(self):
        r,m=self.source_and_manifest();c.source_admission_contract(r,'1'*64,m)
        for key in ('run_admission_sha256','static_root_binding_sha256','caller_birth_sha256'):
            bad=dict(r);bad[key]='0'*64
            with self.subTest(key=key),self.assertRaises(AssertionError):c.source_admission_contract(bad,'1'*64,m)
        bad=copy.deepcopy(r);bad['stable_scientific_source_bindings']['fit_source_manifest_sha256']='0'*64
        with self.assertRaises(AssertionError):c.source_admission_contract(bad,'1'*64,m)

    def test_run_rejects_extra_data_CORE_changed_counts_and_resume(self):
        c.run_contract(self.run_record(),'1'*64)
        for key,value in [('CORE_read_authorized',True),('checkpoint_count',62),('optimizer_units',83),
                ('resume',True),('actual_prefit_commit','HEAD')]:
            bad=self.run_record();bad[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):c.run_contract(bad,'1'*64)
        bad=self.run_record();bad['input_pins']['results/unadmitted.json']='0'*64
        with self.assertRaises(AssertionError):c.run_contract(bad,'1'*64)

    def test_exact_commit_reader_detached_command_and_rejects_wrong_path_or_commit(self):
        r=self.run_record();raw=b'invented committed object';r['input_pins'][c.PREFIT]=c.sha(raw)
        reader=projection_io.ExactCommitReader(r)
        with patch.object(projection_io.guard,'fresh_gate'),patch.object(projection_io.guard,'guarded_bytes',return_value=b'git'),\
                patch.object(projection_io,'DIRECT_GIT_SHA256',c.sha(b'git')),\
                patch.object(projection_io.subprocess,'check_output',return_value=raw) as git:
            self.assertEqual(reader(c.PREFIT,'a'*40),raw)
            self.assertEqual(git.call_args.args[0],[str(projection_io.DIRECT_GIT),'show','a'*40+':'+c.PREFIT])
            self.assertEqual(git.call_args.kwargs,{'cwd':c.ROOT,'creationflags':8})
            for name,commit in ((c.PREFIT,'b'*40),('results/wrong.json','a'*40),(c.PREFIT,'HEAD')):
                with self.subTest(name=name,commit=commit),self.assertRaises(AssertionError):reader(name,commit)
            self.assertEqual(git.call_count,1)

    def test_commit_reader_rejects_wrong_return_bytes(self):
        reader=projection_io.ExactCommitReader(self.run_record())
        with patch.object(projection_io.guard,'fresh_gate'),patch.object(projection_io.guard,'guarded_bytes',return_value=b'git'),\
                patch.object(projection_io,'DIRECT_GIT_SHA256',c.sha(b'git')),\
                patch.object(projection_io.subprocess,'check_output',return_value=b'wrong'):
            with self.assertRaises(AssertionError):reader(c.PREFIT,'a'*40)

    def test_integrity_hook_requires_exact_tasks_objects_pool_and_runtime_checks(self):
        class Folder:
            def exists(self):return False
            def mkdir(self):pass
            def __truediv__(self,name):return name
        identity={'stable':'identity'};plan=SimpleNamespace(identity=lambda:identity,document=lambda:{'science':'fixed'},prefit_sha256='a'*64)
        prepared=SimpleNamespace(prefit_document=plan.document());campaign=SimpleNamespace(plan=plan)
        objects=tuple(object() for _ in range(4));events=[]
        def runtime(binding,evidence,phase,*,task_key):
            events.append('runtime')
            return {**dict(zip(('np','pd','minimize','expit'),objects)),
                'fresh_origin_proof':{'checkpoint_refresh_count':list(c.runtime.CHECKPOINT_KEYS).index(task_key)+1}}
        with patch.object(c,'CHECKPOINT_PROOFS',Folder()),patch.object(c,'admit_authorization'),\
                patch.object(c,'verify_owner'),patch.object(c,'check_live_inputs'),patch.object(c,'verify_sources'),\
                patch.object(c,'read_run'),patch.object(w,'accepted_runtime',side_effect=runtime),\
                patch.object(w.adapter.original,'check_pool',side_effect=lambda *_:events.append('pool')) as pool,\
                patch.object(w.guard,'fresh_gate'),patch.object(c,'save_new',side_effect=lambda *_:'b'*64) as saved:
            hook,hashes=w.make_integrity_hook('1'*64,'2'*64,{}, {},objects,prepared,plan)
            roster=lc.task_roster();task=roster[0];key=lc.task_key(task)
            self.assertIs(hook(task_key=key,task=task,plan=plan,prepared=prepared,campaign=campaign),True)
            self.assertEqual(events,['runtime','pool']);self.assertEqual(pool.call_count,1);self.assertEqual(saved.call_count,1)
            self.assertEqual(list(hashes),[key])
            with self.assertRaises(AssertionError):hook(task_key=key,task=task,plan=plan,prepared=prepared,campaign=campaign)
            with self.assertRaises(AssertionError):hook(task_key=lc.task_key(roster[1]),task=roster[1],plan=plan,prepared=object(),campaign=campaign)

    def test_integrity_hook_native_or_pool_failure_cannot_return_true(self):
        class Folder:
            def exists(self):return False
            def mkdir(self):pass
        plan=SimpleNamespace(identity=lambda:{},document=lambda:{},prefit_sha256='a'*64)
        prepared=SimpleNamespace(prefit_document={});task=lc.task_roster()[0]
        with patch.object(c,'CHECKPOINT_PROOFS',Folder()),patch.object(c,'admit_authorization'),patch.object(c,'verify_owner'),\
                patch.object(c,'check_live_inputs'),patch.object(w,'accepted_runtime',side_effect=AssertionError('native changed')):
            hook,_=w.make_integrity_hook('1'*64,'2'*64,{}, {},(),prepared,plan)
            with self.assertRaisesRegex(AssertionError,'native changed'):
                hook(task_key=lc.task_key(task),task=task,plan=plan,prepared=prepared,campaign=SimpleNamespace(plan=plan))

    def test_runtime_binding_uses_exact_deferred_generation(self):
        from src.generalization_knowncell_fit_paged_runtime_20261025.tests import request
        req=request();manifest={'files':{c.runtime.PREPARATION:'b'*64,c.runtime.SOURCE:'e'*64}}
        self.assertEqual(w.runtime_binding(req,'a'*64,manifest)['provider_preparation_manifest_sha256'],'b'*64)
        req['provider_preparation_manifest_sha256']='0'*64
        with self.assertRaises(AssertionError):w.runtime_binding(req,'a'*64,manifest)

    def test_scientific_delegation_and_five_alias_bodies_unchanged(self):
        from src.generalization_knowncell_joint_runner_20261023.runner import run_campaign
        from src.generalization_knowncell_joint_engine_20261023 import adapter_v2
        self.assertIs(w.run_campaign,run_campaign);self.assertIs(w.adapter,adapter_v2)
        prior=(c.ROOT/'src/generalization_knowncell_prefit_execution_20261024/calibration.py').read_text()
        current=Path(cal.__file__).read_text().replace(c.NS,'generalization_knowncell_prefit_execution_20261024')
        current=current.replace(c.INVOCATION,'fixed_prefit').replace("stage=='fit'","stage=='prefit'")
        self.assertEqual(ast.dump(ast.parse(prior),include_attributes=False),ast.dump(ast.parse(current),include_attributes=False))
    def test_exact_original_NPZ_load_feature_astype_and_C_byte_contract(self):
            raw=b'invented_npz';matrix=Matrix();archive=Archive(matrix);calls=[]
            np=SimpleNamespace(ndarray=Matrix,load=lambda stream,**kw:(calls.append(kw) or archive),
                isfinite=lambda value:SimpleNamespace(all=lambda:True))
            cert={'actual_npz_sha256':c.sha(raw),'rows':2,'columns':3,'same_allele_feature_bytes_equal':True,
                  'underlying_report':{'post_original_astype_float_C_bytes_sha256':c.sha(matrix.bits)}}
            with patch.object(c,'SHAPE',(2,3)),patch.object(c,'NPZ_SHA',c.sha(raw)),patch.object(c,'ARRAY_CAST_SHA',c.sha(matrix.bits)),\
                 patch.object(inputs.guard,'fresh_gate'):
                self.assertIs(inputs.matrix_from_bytes(np,raw,cert),matrix)
                self.assertEqual(calls,[{'allow_pickle':False}]);self.assertEqual(matrix.casts,[float])
                matrix.bits=struct.pack('<6d',1.,2.,3.,4.,5.,0.)
                with self.assertRaises(AssertionError):inputs.matrix_from_bytes(np,raw,cert)

    def test_wrong_NPZ_hash_stops_before_native_load(self):
            np=SimpleNamespace(load=lambda *args,**kw:self.fail('No native call'))
            with self.assertRaises(AssertionError):inputs.matrix_from_bytes(np,b'invented wrong bytes',{})

    def test_persisted_labels_repack_exact_signed_zero_bits_without_CORE_parser(self):
            ids=['one','two'];values=[.125,-0.];bits=c.sha(struct.pack('<2d',*values))
            bundle={'metadata':{'rows':[{'intervention_id':value} for value in ids]}}
            fields={'generation_manifest_sha256':'1'*64,'run_admission_sha256':'2'*64,'birth_sha256':'3'*64,
                'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA}
            label={'status':'PASS_CALIBRATED_ORIGINAL_PANDAS_MIKL_LABELS_NO_FIT',**fields,'metadata_bundle_sha256':c.METADATA_SHA,
                'array_certificate_sha256':c.ARRAY_CERTIFICATE_SHA,'array_supervisor_sha256':c.ARRAY_SUPERVISOR_SHA,
                'resource_exception_applies':True,'original_resource_guards_unchanged':False,'models_fitted':0,'actual_feature_reads':0,
                'label_access_does_not_authorize_fitting':True,'labels_result':{'intervention_ids':ids,'numeric_outcome_rows_admitted':2,
                    'parser':c.labels.PARSER,'original_truth_orientation':True,'old_interpreter_bitwise_parity_established':False,
                    'measured_delta':values,'parsed_effects_float64_sha256':bits}}
            saved={'status':'PASS_EXACT_LABELS_EXECUTION_PENDING_ROOT_REVIEW_AND_COMMIT','failure':None,
                'certificate_sha256':c.LABEL_CERTIFICATE_SHA,**fields,'model_fits':0,'numerical_outcomes_admitted':2}
            with patch.object(c,'COUNT',2),patch.object(c,'ROW_IDS_SHA',c.sha(b'one|two')),patch.object(c,'LABEL_BITS_SHA',bits):
                self.assertEqual(inputs.persisted_label_contract(bundle,label,saved),ids)
                label['labels_result']['measured_delta'][1]=0.
                with self.assertRaises(AssertionError):inputs.persisted_label_contract(bundle,label,saved)

    def test_exact_nine_pool_adapter_and_sampler_factory_forwarding(self):
            doc=old_document();sampler=object.__new__(build.original_sampler.GuardedSampler);sampler.identity={'invented_sampler_identity':True}
            pools={key:{'binding':value} for key,value in doc['source_pools'].items()}
            prepared=build.adapter.PreparedPools([],pools,doc)
            data={'metadata':[],'features':object(),'effects':{},'admissions':{}}
            with patch.object(lc,'COUNTS',doc['counts']),patch.object(build.guard,'fresh_gate'),\
                 patch.object(build.original_sampler,'load_original_sampler',return_value=sampler) as factory,\
                 patch.object(build.adapter,'prepare_pools',return_value=prepared) as adapter,\
                 patch.object(build.adapter.original,'pool_binding',side_effect=lambda np,pool:pool['binding']) as rebound:
                result,identity=build.prepare_original_pools(object(),object(),data,{'runtime_acceptance_after_array':{'stable_anchor_only':True}})
                self.assertIs(result,prepared);self.assertIs(identity,sampler.identity);self.assertEqual(rebound.call_count,9)
                self.assertEqual(factory.call_args.kwargs,{'root_start':True});self.assertEqual(adapter.call_count,1)
                self.assertEqual(adapter.call_args.kwargs['admissions'],data['admissions'])

    def test_guard_alias_transaction_bodies_and_caps_unchanged(self):
            from src.generalization_knowncell_labels_execution_v2_20261024 import calibration as oldcal
            def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(path).read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef)}
            oldf,newf=functions(oldcal.__file__),functions(cal.__file__)
            for name in ('_snapshot','_installed','_plain_copy','_annotated_copy','_source_module'):
                self.assertEqual(oldf[name],newf[name])
            self.assertEqual(cal.TARGETS,oldcal.TARGETS);self.assertEqual(c.PROCESS_CAP,768*2**20);self.assertEqual(c.JOB_CAP,896*2**20)
            self.assertEqual(c.resource_policy()['startup_commit_headroom'],1920*2**20)

    def test_partial_outputs_reject_without_probe_or_worker(self):
            with patch.object(c.os.path,'lexists',side_effect=lambda path:path==c.OUTPUT),self.assertRaises(AssertionError):c.require_new_outputs()

    def test_durable_journal_exclusive_and_bounded_without_truncating(self):
        from .journal import Journal
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invented.jsonl'
            with Journal(path) as journal:
                journal.event('INVENTED',counter=1)
                initial=path.read_bytes()
                journal.MAX_BYTES=len(initial)
                with self.assertRaises(AssertionError):journal.event('OVERFLOW')
                self.assertEqual(path.read_bytes(),initial)
            with self.assertRaises(FileExistsError):
                with Journal(path):pass
            self.assertEqual(path.read_bytes(),initial)

    def test_journal_throttles_samples_and_persists_terminal_sample(self):
        from .journal import Journal
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invented.jsonl'
            with Journal(path) as journal:
                value={'elapsed_seconds':0.,'exit_code':None,'pending_failure':None}
                journal.sample(value)
                journal.sample({**value,'elapsed_seconds':.5})
                journal.sample({**value,'elapsed_seconds':.6,'exit_code':0})
            lines=[json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(lines),2)
            self.assertEqual(lines[-1]['exit_code'],0)

    def monitor_dependencies(self):
        job=SimpleNamespace(terminated=0)
        def terminate():job.terminated+=1
        job.terminate=terminate
        job.accounting=lambda:{'active_processes':1,'peak_process_memory_used':100,'peak_job_memory_used':100}
        child=SimpleNamespace(process_handle=object(),exit_code=lambda:None)
        memory=lambda:{'physical_available':3*2**30,'commit_headroom':4*2**30,'disk_available':4*2**30}
        process=lambda _:{'working_set':100,'peak_working_set':100,'peak_private_commit':100}
        return job,child,memory,process

    def test_monitor_uses_total_stage_start_and_cannot_reset_deadline(self):
        from .monitor import observe
        job,child,memory,process=self.monitor_dependencies()
        with patch.object(monitor.working_set,'verify',return_value=True):
            result=observe(job,child,memory,process,lambda:1801.,lambda _:self.fail('No wait after deadline'),started=0.,working_set_receipt=self.resident_cap())
        self.assertIsNotNone(result['failure'])
        self.assertGreaterEqual(job.terminated,1)
        self.assertEqual(result['elapsed_seconds'],1801.)

    def test_telemetry_failure_stops_owned_job_and_is_not_silently_ignored(self):
        from .monitor import observe
        job,child,memory,process=self.monitor_dependencies()
        def broken(_):raise OSError('invented disk failure')
        with patch.object(monitor.working_set,'verify',return_value=True):
            result=observe(job,child,memory,process,lambda:10.,lambda _:self.fail('No wait after telemetry failure'),record=broken,started=0.,working_set_receipt=self.resident_cap())
        self.assertIn('invented disk failure',result['failure'])
        self.assertGreaterEqual(job.terminated,1)

    def test_complete_scientific_fit_body_is_AST_identical_to_preserved_attempt(self):
        from src.generalization_knowncell_fit_retry_execution_20261025 import worker as frozen
        def body(module):return next(n for n in ast.parse(Path(module.__file__).read_text()).body
            if isinstance(n,ast.FunctionDef) and n.name=='fit')
        self.assertEqual(ast.dump(body(w),include_attributes=False),ast.dump(body(frozen),include_attributes=False))

    def test_final_journal_fsync_failure_cannot_leave_a_PASS_receipt(self):
        from . import journal as jm
        from src.generalization_pum_process_probe_20261021 import headless
        memory={'physical_available':5*2**30,'commit_headroom':4*2**30,'disk_available':4*2**30}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            def final_event(*args,**kwargs):
                kwargs['journal'].event('SUPERVISOR_READY_FOR_FINAL_COMMIT')
                return {'status':'PASS'}
            with patch.object(c,'JOURNAL',path/'journal.jsonl'),patch.object(c,'FAULT_LOG',path/'fault.log'),\
                    patch.object(c,'admit_authorization'),patch.object(c,'read_run'),patch.object(c,'require_new_outputs'),\
                    patch.object(headless,'memory',return_value=memory),patch.object(supervisor,'_run',side_effect=final_event),\
                    patch.object(supervisor,'commit_receipt') as commit,patch.object(supervisor.faulthandler,'enable'),\
                    patch.object(supervisor.faulthandler,'disable'),\
                    patch.object(jm.os,'fsync',side_effect=[None,OSError('invented final fsync'),None]),\
                    self.assertRaisesRegex(OSError,'invented final fsync'):
                try:supervisor.run('1'*64,'2'*64,root_start=True)
                finally:commit.assert_not_called()

    def test_terminal_commit_samples_deadline_after_completed_telemetry(self):
        from src.generalization_pum_process_probe_20261021 import headless
        receipt={'status':'PASS_FIXED63_CHECKPOINT84_UNIT_FIT_LIFECYCLE_PENDING_INDEPENDENT_REPLAY',
            'failure':None,'birth_sha256':c.sha(b'birth'),'checkpoints':63,'optimizer_units':84,
            'owned_resident_policy':c.resident_policy(),'owned_resident_cap':self.resident_cap(),'observed':self.successful_observed()}
        memory={'physical_available':3*2**30,'commit_headroom':4*2**30,'disk_available':4*2**30}
        with patch.object(c,'JOURNAL',SimpleNamespace(read_bytes=lambda:b'closed journal\n')),\
                patch.object(c,'BIRTH',SimpleNamespace(read_bytes=lambda:b'birth')),\
                patch.object(c,'admit_authorization'),patch.object(c,'read_run'),patch.object(c,'verify_sources'),\
                patch.object(headless,'memory',return_value=memory),patch.object(supervisor.time,'monotonic',return_value=1801.),\
                patch.object(c,'save_new') as saved,self.assertRaises(AssertionError):
            supervisor.commit_receipt(receipt,'1'*64,'2'*64,0.)
        self.assertEqual(saved.call_count,1)
        committed=saved.call_args.args[1]
        self.assertEqual(committed['status'],'FAILED_OR_BLOCKED_FIT_INVOCATION_PRESERVED_NO_RETRY')
        self.assertIsNone(committed['checkpoints'])
        self.assertTrue(committed['mandatory_journal_closed_before_receipt'])

    def test_pending_numerical_profile_and_changed_resident_policy_cannot_admit(self):
        run=self.run_record();c.run_contract(run,'1'*64)
        for kind in ('profile','toy','cap'):
            bad=copy.deepcopy(run)
            if kind=='profile':bad['paging_evidence']['numerical_paging_profile_sha256']='0'*64
            elif kind=='toy':bad['paging_evidence']['owned_working_set_toy_sha256']='0'*64
            else:bad['owned_resident_policy']['measured_current_and_lifetime_ceiling']+=1
            with self.subTest(kind=kind),self.assertRaises(AssertionError):c.run_contract(bad,'1'*64)
        with patch.object(c,'NUMERIC_PAGING_PROFILE_SHA','PENDING_ROOT_REVIEWED_NUMERICAL_PAGING_PROFILE_SHA'),self.assertRaises(AssertionError):
            c.run_contract(run,'1'*64)
        value,child,baseline,certificate=self.numeric_fixture()
        resident.numeric_profile_contract(value,child,baseline,certificate)
        for kind in ('units','optimizer','native','certificate','child_hash','full_study'):
            a,b,d,e=copy.deepcopy((value,child,baseline,certificate))
            if kind=='units':b['invented_optimizer_units']=11
            elif kind=='optimizer':d['optimizer']['invented_case']=2
            elif kind=='native':b['final_native_proof']['fresh_full_NumPy_payload_check']=False
            elif kind=='certificate':e['three_full_buffer_hashes_independently_recomputed']=False
            elif kind=='child_hash':a['child_completion_sha256']='0'*64
            else:a['full_FIT_or_old_interpreter_parity_established']=True
            with self.subTest(kind=kind),self.assertRaises(AssertionError):resident.numeric_profile_contract(a,b,d,e)

    def numeric_fixture(self):
        optimizer={'status':'PASS_INVENTED_SCIPY_SOLVER_REFERENCE_AND_SCORER','scipy_optimizer_units':12,'biological_model_fits':0,'invented_case':1}
        compact=json.dumps(optimizer,sort_keys=True,allow_nan=False,separators=(',',':')).encode('utf8')
        proof={'fresh_full_NumPy_payload_check':True,'old_interpreter_bitwise_parity_established':False,
            'actually_loaded_current_python_native_files':{'invented_only':'never_loaded'},
            'actually_loaded_scientific_native_files':{'invented_only':'never_loaded'},
            'actually_loaded_scientific_modules':{'invented_only':'never_loaded'}}
        value={'status':c.NUMERIC_PAGING_REQUIRED_STATUS,'failure':None,'preparation_manifest_sha256':c.NUMERIC_PAGING_MANIFEST_SHA,
            'child_completion_sha256':c.NUMERIC_PAGING_CHILD_SHA,'closed_parent_log_sha256':c.NUMERIC_PAGING_JOURNAL_SHA,
            'requested_resident_maximum':c.RESIDENT_CONFIGURED_LIMIT,'measured_resident_ceiling':c.RESIDENT_MEASURED_CEILING,
            'peak_working_set':190*2**20,'peak_private_commit':500*2**20,'elapsed_seconds':10.,'minimum_sampled_physical_available':512*2**20,
            'memory_after':{'physical_available':2**30,'commit_headroom':3*2**30,'disk_available':2**30},
            'additional_resident_cap':self.resident_cap(),'unchanged_job_caps':{'process_memory_limit':c.PROCESS_CAP,
                'job_memory_limit':c.JOB_CAP,'active_process_limit':2,'limit_flags':8968},'invented_optimizer_units':12,
            'biological_rows_read':0,'scientific_attempts':0,'full_FIT_or_old_interpreter_parity_established':False}
        child={'status':'PASS_INVENTED_PAGED_NATIVE_NUMERICAL_PROFILE','preparation_manifest_sha256':c.NUMERIC_PAGING_MANIFEST_SHA,
            'invented_optimizer_units':12,'biological_rows_read':0,'biological_model_fits':0,'bytes':384*2**20,
            'hashes':['1'*64]*3,'optimizer':optimizer,'canonical_optimizer_sha256':c.sha(compact),
            'initial_native_proof':proof,'final_native_proof':copy.deepcopy(proof)}
        baseline={'status':'PASS_INVENTED_PANDAS_SCIPY_PROFILE_CURRENT_PYTHON_V4','optimizer':copy.deepcopy(optimizer)}
        cert={'status':'VERIFIED_INVENTED_NATIVE_PAGING_NUMERICAL_PROFILE_NOT_BIOLOGICAL_ADMISSION',
            'source_generation_sha256':c.NUMERIC_PAGING_MANIFEST_SHA,'supervisor_receipt_sha256':c.NUMERIC_PAGING_PROFILE_SHA,
            'child_completion_sha256':c.NUMERIC_PAGING_CHILD_SHA,'closed_parent_journal_sha256':c.NUMERIC_PAGING_JOURNAL_SHA,
            'verification_source_sha256':c.NUMERIC_PAGING_CERTIFY_SOURCE_SHA,'original_twelve_invented_optimizer_results_exact':True,
            'three_full_buffer_hashes_independently_recomputed':True,'full_study_runtime_or_biological_generalization_established':False,
            'biological_rows_read':0,'biological_fits_or_attempts':0}
        return value,child,baseline,cert

    def test_resident_current_lifetime_boundary_and_cap_receipt(self):
        resident.installed_contract(self.resident_cap())
        resident.counters({'working_set':192*2**20,'peak_working_set':192*2**20})
        for kind in ('current','peak','noninteger','negative','invalid_order'):
            sample={'working_set':190*2**20,'peak_working_set':192*2**20}
            if kind=='current':sample['working_set']=192*2**20+1
            elif kind=='peak':sample['peak_working_set']=192*2**20+1
            elif kind=='noninteger':sample['working_set']=1.0
            elif kind=='negative':sample['working_set']=-1
            else:sample['working_set']=sample['peak_working_set']+1
            with self.subTest(kind=kind),self.assertRaises(AssertionError):resident.counters(sample)
        for field,value in (('maximum',192*2**20),('flags',10),('minimum',0)):
            bad=self.resident_cap();bad['after'][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):resident.installed_contract(bad)

    def test_monitor_rechecks_running_policy_and_final_lifetime_counters(self):
        job,child,memory,process=self.monitor_dependencies()
        exits=iter((None,0));child.exit_code=lambda:next(exits)
        with patch.object(monitor.working_set,'verify',return_value=True) as verify:
            result=monitor.observe(job,child,memory,process,lambda:10.,lambda _:None,started=0.,working_set_receipt=self.resident_cap())
        self.assertIsNone(result['failure']);self.assertEqual(result['exit_code'],0)
        self.assertEqual(result['resident_configuration_checks'],1);self.assertEqual(verify.call_count,1)
        self.assertTrue(result['final_lifetime_resident_counters_checked'])
        resident.observed_contract(result,self.resident_cap())

    def test_monitor_overshoot_changed_policy_and_final_overshoot_poison_pass(self):
        for kind in ('sample_current','sample_peak','changed_policy','final_peak'):
            job,child,memory,process=self.monitor_dependencies();calls=[]
            child.exit_code=lambda:0 if kind=='final_peak' else None
            def counters(_):
                calls.append(1);peak=100;current=100
                if kind=='sample_current':current=c.RESIDENT_MEASURED_CEILING+1
                elif kind=='sample_peak' or kind=='final_peak' and len(calls)>1:peak=c.RESIDENT_MEASURED_CEILING+1
                return {'working_set':current,'peak_working_set':peak,'peak_private_commit':100}
            problem=AssertionError('changed configuration') if kind=='changed_policy' else None
            with self.subTest(kind=kind),patch.object(monitor.working_set,'verify',side_effect=problem,return_value=True):
                result=monitor.observe(job,child,memory,counters,lambda:10.,lambda _:self.fail('No wait after failure'),
                    started=0.,working_set_receipt=self.resident_cap())
            self.assertIsNotNone(result['failure']);self.assertGreaterEqual(job.terminated,1)
            if kind=='final_peak':
                self.assertFalse(result['final_lifetime_resident_counters_checked'])
                self.assertGreater(result['final_process_handle_peak_sample']['peak_working_set'],c.RESIDENT_MEASURED_CEILING)
            elif kind in ('sample_current','sample_peak'):
                self.assertTrue(any(result['last_process_handle_sample'][key]>c.RESIDENT_MEASURED_CEILING for key in ('working_set','peak_working_set')))

    def test_paged_native_helper_is_exact_reused_V2_and_science_bodies_unchanged(self):
        from src.generalization_owned_workingset_probe_v2_20261025 import working_set
        self.assertIs(supervisor.working_set,working_set);self.assertIs(monitor.working_set,working_set)
        self.assertEqual(c.sha(Path(working_set.__file__).read_bytes()),c.WORKING_SET_SOURCE_SHA)
        old='generalization_knowncell_fit_roomy_execution_20261025';old_runtime='generalization_knowncell_fit_roomy_runtime_20261025'
        for name in ('build.py','inputs.py','calibration.py','projection_io.py','terminal.py','journal.py'):
            raw=(c.ROOT/'src'/c.NS/name).read_text().replace(c.NS,old).replace(c.runtime.NS,old_runtime)
            with self.subTest(name=name):self.assertEqual(ast.dump(ast.parse(raw)),ast.dump(ast.parse((c.ROOT/'src'/old/name).read_text())))
        def function(path,name):return next(n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
        self.assertEqual(ast.dump(function(w.__file__,'fit')),ast.dump(function(c.ROOT/'src'/old/'worker.py','fit')))

    def test_resident_apply_precedes_first_resume_and_failure_never_resumes(self):
        from src.generalization_pum_process_probe_20261021 import headless
        for fail in (False,True):
            events=[];cap=self.resident_cap()
            child=SimpleNamespace(pid=201,process_handle=object(),_resumed=False,close=lambda:events.append('close'))
            def resume():events.append('resume');child._resumed=True
            child.resume=resume
            limits={'process_memory_limit':c.PROCESS_CAP,'job_memory_limit':c.JOB_CAP,'active_process_limit':2,'limit_flags':headless.original.LIMIT_FLAGS}
            job=SimpleNamespace(limits=lambda:limits,terminate=lambda:events.append('terminate'))
            def spawn(*args):events.append('spawn');return child
            job.spawn=spawn
            class Context:
                def __enter__(self):return job
                def __exit__(self,*_):pass
            def apply(actual_job,actual_child):
                events.append('apply');self.assertIs(actual_job,job);self.assertIs(actual_child,child);self.assertFalse(child._resumed)
                if fail:raise OSError('invented cap installation failure')
                return cap
            def observe(*args,**kwargs):
                events.append('observe');self.assertTrue(child._resumed)
                self.assertEqual(kwargs['started'],0.);self.assertEqual(kwargs['working_set_receipt'],cap)
                return {'failure':'invented stop after verified launch','exit_code':None}
            memory={'physical_available':2*2**30,'commit_headroom':4*2**30,'disk_available':4*2**30}
            journal=SimpleNamespace(event=lambda status,**kwargs:events.append(status),sample=lambda value:events.append('sample'))
            run=self.run_record()
            with self.subTest(fail=fail),patch.object(c,'admit_authorization',return_value={}),patch.object(c,'read_run',return_value=run),\
                    patch.object(c,'read_source_admission'),patch.object(c,'require_new_outputs'),patch.object(c,'verify_sources'),\
                    patch.object(c,'save_new',return_value=c.sha(b'birth')),patch.object(c,'BIRTH',SimpleNamespace(read_bytes=lambda:b'birth')),\
                    patch.object(headless,'Job',return_value=Context()),patch.object(headless,'memory',return_value=memory),\
                    patch.object(headless,'process_memory',return_value={'peak_working_set':100,'peak_private_commit':100}),\
                    patch.object(supervisor.working_set,'apply',side_effect=apply),patch.object(supervisor,'observe',side_effect=observe),\
                    patch.object(supervisor.time,'monotonic',return_value=10.):
                receipt=supervisor._run('1'*64,'2'*64,root_start=True,journal=journal,started=0.)
            self.assertIsNotNone(receipt['failure'])
            if fail:self.assertNotIn('resume',events);self.assertNotIn('observe',events)
            else:self.assertLess(events.index('apply'),events.index('resume'));self.assertLess(events.index('resume'),events.index('observe'))


def run(*,draft=False):
    assert type(draft) is bool
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    clean=lambda:not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert clean() and not c.RUN_ADMISSION.exists() and not c.SOURCE_ADMISSION.exists()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    filename='synthetic_tests_receipt_draft.json' if draft else 'synthetic_tests_receipt.json'
    c.save_new(c.OUT/filename,{'status':'PASS_INVENTED_FIXED_FIT_EXECUTION_NOT_ACTUAL_FIT',
        'tests':result.testsRun,'sources':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources},
        'actual_jobs':0,'actual_resource_probes':0,'actual_provider_invocations':0,'project_payload_reads':0,
        'actual_pools_prepared':0,'optimizer_calls':0,'scientific_imports':False,
        'numeric_pool_and_runtime_edges_in_tests_are_private_mocks':True,'draft_before_numerical_paging_profile':draft})


if __name__=='__main__':run()
