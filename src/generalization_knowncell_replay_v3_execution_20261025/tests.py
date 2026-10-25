"""Invented exact-input and owned fixed-FIT controller tests; no native calls."""
import ast
import copy
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import common as c,inputs,build,worker as w,supervise as supervisor,calibration as cal,projection_io as projection_io
from . import fit_journal as fj,terminal
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_prefit_execution_20261024.tests import old_document,Matrix,Archive

class Cases(unittest.TestCase):
    def setUp(self):
        self.fit_generation=patch.object(c,'FIT_GENERATION_SHA','7'*64)
        self.fit_generation.start();self.addCleanup(self.fit_generation.stop)

    def test_campaign_roster_requires_exact191_and_zero_new_optimizer_calls(self):
        run=self.run_record();c.run_contract(run,'1'*64)
        self.assertEqual(len(run['campaign_pins']),191)
        for change in ('missing','extra','new_fit','changed_hash'):
            item=copy.deepcopy(run)
            if change=='missing':item['campaign_pins'].pop(next(iter(item['campaign_pins'])))
            if change=='extra':item['campaign_pins']['results/extra.json']='0'*64
            if change=='new_fit':item['new_optimizer_calls']=1
            if change=='changed_hash':item['campaign_pins'][next(iter(item['campaign_pins']))]='bad'
            with self.subTest(change=change),self.assertRaises(AssertionError):c.run_contract(item,'1'*64)

    def test_public_replay_and_sampler_delegation_no_optimizer(self):
        from src.generalization_knowncell_campaign_replay_20261023.replay import verify_campaign
        self.assertIs(w.verify_campaign,verify_campaign)
        tree=ast.parse(Path(w.__file__).read_text())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertFalse(any(isinstance(n.func,ast.Name) and n.func.id in ('minimize','run_campaign') for n in calls))
        self.assertFalse(any(isinstance(n.func,ast.Attribute) and n.func.attr in ('fit_prepared','make_fit_callback') for n in calls))

    def test_calibration_and_monitor_only_declared_stage_substitutions(self):
        from . import monitor
        old=(c.ROOT/'src/generalization_knowncell_fit_retry_execution_20261025/calibration.py').read_text()
        new=Path(cal.__file__).read_text().replace(c.NS,'generalization_knowncell_fit_retry_execution_20261025')
        new=new.replace(c.INVOCATION,'fixed_63_checkpoint_84_optimizer_unit_fit').replace("stage=='replay'","stage=='fit'")
        self.assertEqual(ast.dump(ast.parse(old),include_attributes=False),ast.dump(ast.parse(new),include_attributes=False))
        old=(c.ROOT/'src/generalization_knowncell_fit_retry_execution_20261025/monitor.py').read_text()
        self.assertEqual(ast.dump(ast.parse(old),include_attributes=False),ast.dump(ast.parse(Path(monitor.__file__).read_text()),include_attributes=False))
    def source_and_manifest(self):
            m={'files':{c.WORKER_SOURCE:'5'*64,c.runtime.PREPARATION:'6'*64,c.BRIDGE_READY:'7'*64}}
            r={'status':'REVIEWED_SOURCE_ONLY_INDEPENDENT_REPLAY_CONTROLLER_NOT_INPUT_OR_FIT_AUTHORITY',
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
                **{name:'5'*64 for name in (c.PREFIT,c.PREFIT_COMPLETION,c.PREFIT_SUPERVISOR,c.PROJECTION_ADMISSION,c.FIT_REPORT,c.FIT_COMPLETION,c.FIT_SUPERVISOR,c.FIT_JOURNAL)}}
            return {'status':'FROZEN_ONE_INDEPENDENT63_CHECKPOINT_REPLAY_RUN_NO_FIT','stage':c.STAGE,'invocation':c.INVOCATION,
                'generation_manifest_sha256':'1'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
                'fit_generation_manifest_sha256':c.FIT_GENERATION_SHA,
                'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),
                'runtime_import_authorized':True,'array_reload_authorized':True,'saved_label_read_authorized':True,
                'pool_preparation_authorized':True,'model_fitting_authorized':False,'CORE_read_authorized':False,
                'data_pins':{c.NPZ:c.NPZ_SHA},'input_pins':pins,'actual_prefit_commit':'a'*40,
                'projection_root_admission_commit':'b'*40,'checkpoint_count':63,'recorded_optimizer_units':84,'new_optimizer_calls':0,'resume':False,'campaign_pins':{name:'6'*64 for name in c.campaign_paths()}}

    def test_source_admission_has_no_temporal_cycle_or_changed_scientific_sources(self):
            r,m=self.source_and_manifest();c.source_admission_contract(r,'1'*64,m)
            for key in ('run_admission_sha256','static_root_binding_sha256','caller_birth_sha256'):
                bad=dict(r);bad[key]='0'*64
                with self.subTest(key=key),self.assertRaises(AssertionError):c.source_admission_contract(bad,'1'*64,m)
            bad=copy.deepcopy(r);bad['stable_scientific_source_bindings']['fit_source_manifest_sha256']='0'*64
            with self.assertRaises(AssertionError):c.source_admission_contract(bad,'1'*64,m)

    def test_run_rejects_extra_data_CORE_changed_counts_and_resume(self):
            c.run_contract(self.run_record(),'1'*64)
            for key,value in [('CORE_read_authorized',True),('checkpoint_count',62),('recorded_optimizer_units',83),
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

    def test_runtime_binding_uses_exact_deferred_generation(self):
            from src.generalization_knowncell_replay_v3_runtime_20261025.tests import request
            req=request();manifest={'files':{c.runtime.PREPARATION:'b'*64,c.runtime.SOURCE:'e'*64}}
            self.assertEqual(w.runtime_binding(req,'a'*64,manifest)['provider_preparation_manifest_sha256'],'b'*64)
            req['provider_preparation_manifest_sha256']='0'*64
            with self.assertRaises(AssertionError):w.runtime_binding(req,'a'*64,manifest)

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

    def journal_case(self):
        run=self.run_record()
        shared={'generation_manifest_sha256':c.FIT_GENERATION_SHA,'run_admission_sha256':'8'*64,'birth_sha256':'9'*64}
        report={'status':'ACTUAL_ONE_OWNED_FIXED_FIT_LIFECYCLE_NOT_REPLAY_OR_EVALUATION',**shared,
            'parent_pid':120,'worker_pid':121,'plan_identity':{'invented_plan':True},'actual_prefit_sha256':'5'*64,
            'projection_root_admission_sha256':run['input_pins'][c.PROJECTION_ADMISSION],
            'checkpoints':63,'optimizer_units':84,'CORE_reread':False,'independent_replay_complete':False,'evaluation_or_gate_run':False}
        completion={'status':'PASS_FIXED_FIT_WORKER_CALLBACKS_RESTORED_LIFECYCLE_ONLY',**shared,
            'parent_pid':120,'worker_pid':121,'report_sha256':run['input_pins'][c.FIT_REPORT],
            'actual_prefit_sha256':'5'*64,'checkpoints':63,'optimizer_units':84,'callbacks_restored':True}
        saved={'status':fj.PASS,**shared,'failure':None,'report_sha256':run['input_pins'][c.FIT_REPORT],
            'worker_completion_sha256':run['input_pins'][c.FIT_COMPLETION],
            'mandatory_journal_closed_before_receipt':True,'observed':{'exit_code':0,'failure':None,'samples':1},
            'parent_terminal_lifecycle_validation':{'files_sha256':{name.rsplit('/',1)[1]:want for name,want in run['campaign_pins'].items()}}}
        events=[
            {'status':'MANAGED_SUPERVISOR_ENTERED','parent_pid':120,'root_start':True},
            {'status':'FIT_BIRTH_DURABLE','parent_pid':120,**shared},
            {'status':'OWNED_CHILD_ASSIGNED','worker_pid':121,'limits':{'invented_no_native_query':True}},
            {'status':'OWNED_CHILD_RESUMED','worker_pid':121},
            {'status':'OWNED_WORKER_SAMPLE','elapsed_seconds':.25,'exit_code':0,'pending_failure':None},
            {'status':'OWNED_CHILD_MONITOR_RETURNED','worker_pid':121,'observed':saved['observed']},
            {'status':'SUPERVISOR_READY_FOR_FINAL_COMMIT','intended_receipt_status':fj.PASS,'failure':None}]
        for index,event in enumerate(events):event['monotonic']=index+1
        raw=self.journal_bytes(events);self.bind_journal(raw,run,saved)
        return raw,events,saved,report,completion,run

    @staticmethod
    def journal_bytes(events):
        return b''.join((json.dumps(event,sort_keys=True,allow_nan=False)+'\n').encode('utf8') for event in events)

    @staticmethod
    def bind_journal(raw,run,saved):
        saved['mandatory_journal_sha256']=run['input_pins'][c.FIT_JOURNAL]=c.sha(raw)

    def test_roomy_generation_and_raw_journal_are_mandatory_exact_run_inputs(self):
        run=self.run_record();c.run_contract(run,'1'*64)
        for kind in ('generation','journal_missing','old_path'):
            bad=copy.deepcopy(run)
            if kind=='generation':bad['fit_generation_manifest_sha256']='0'*64
            elif kind=='journal_missing':del bad['input_pins'][c.FIT_JOURNAL]
            else:
                old=c.FIT_JOURNAL.replace('fit_roomy_execution','fit_managed_execution')
                bad['input_pins'][old]=bad['input_pins'].pop(c.FIT_JOURNAL)
            with self.subTest(kind=kind),self.assertRaises(AssertionError):c.run_contract(bad,'1'*64)
        with patch.object(c,'FIT_GENERATION_SHA','PENDING_ROOT_FROZEN_ROOMY_FIT_GENERATION'),self.assertRaises(AssertionError):
            c.run_contract(run,'1'*64)

    def test_valid_journal_and_fit_contract_preserve_original_full_campaign(self):
        raw,events,saved,report,completion,run=self.journal_case()
        receipt=fj.validate(raw,saved,report,completion,run)
        self.assertEqual(receipt['status'],fj.STATUS);self.assertEqual(receipt['journal_lines'],7)
        self.assertFalse(receipt['physical_durability_retroactively_established'])
        self.assertFalse(receipt['old_fit_owner_reused_as_current_replay_owner'])
        plan=SimpleNamespace(identity=lambda:{'invented_plan':True},prefit_sha256='5'*64)
        self.assertEqual(w.fit_contract(report,completion,saved,run,plan,raw),receipt)
        self.assertEqual(len(run['campaign_pins']),191)
        for field,value in (('checkpoints',62),('optimizer_units',83),('plan_identity',{})):
            bad=copy.deepcopy(report);bad[field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):w.fit_contract(bad,completion,saved,run,plan,raw)

    def test_jsonl_never_enters_generic_input_object_decode(self):
        raw,*_=self.journal_case()
        inputs_raw={c.FIT_JOURNAL:raw,c.FIT_REPORT:b'{"invented_object":true}\n'}
        decoded=fj.decode_input_objects(inputs_raw)
        self.assertEqual(decoded,{c.FIT_REPORT:{'invented_object':True}})
        with self.assertRaises((ValueError,AssertionError)):c.decode(raw)
        with self.assertRaises(AssertionError):fj.decode_input_objects({c.FIT_REPORT:b'{}'})
        tree=ast.parse(Path(w.__file__).read_text())
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call)]
        self.assertTrue(any(isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name)
            and node.func.value.id=='fit_journal' and node.func.attr=='decode_input_objects' for node in calls))

    def test_journal_rejects_wrong_hash_missing_closed_or_nonboolean_closed(self):
        for kind in ('raw_hash','saved_hash','missing','false','integer'):
            raw,events,saved,report,completion,run=self.journal_case()
            if kind=='raw_hash':raw=raw.replace(b'120',b'122')
            elif kind=='saved_hash':saved['mandatory_journal_sha256']='0'*64
            elif kind=='missing':saved.pop('mandatory_journal_closed_before_receipt')
            elif kind=='false':saved['mandatory_journal_closed_before_receipt']=False
            else:saved['mandatory_journal_closed_before_receipt']=1
            with self.subTest(kind=kind),self.assertRaises((AssertionError,KeyError)):fj.validate(raw,saved,report,completion,run)

    def test_journal_rejects_incomplete_nonfinite_duplicate_and_oversize_bytes(self):
        for kind in ('truncated','blank','CRLF','duplicate','NaN','overflow','longline','maxbytes'):
            raw,events,saved,report,completion,run=self.journal_case()
            if kind=='truncated':raw=raw[:-1]
            elif kind=='blank':raw+=b'\n'
            elif kind=='CRLF':raw=raw.replace(b'\n',b'\r\n')
            elif kind=='duplicate':raw=raw.replace(b'"monotonic": 1',b'"monotonic": 1, "monotonic": 1',1)
            elif kind=='NaN':raw=raw.replace(b'"monotonic": 1',b'"monotonic": NaN',1)
            elif kind=='overflow':raw=raw.replace(b'"monotonic": 1',b'"monotonic": 1e999',1)
            elif kind=='longline':events[0]['padding']='x'*fj.MAX_LINE_BYTES;raw=self.journal_bytes(events)
            self.bind_journal(raw,run,saved)
            if kind=='maxbytes':
                with patch.object(fj,'MAX_BYTES',len(raw)-1),self.assertRaises(AssertionError):fj.validate(raw,saved,report,completion,run)
            else:
                with self.subTest(kind=kind),self.assertRaises((AssertionError,ValueError)):fj.validate(raw,saved,report,completion,run)

    def test_journal_rejects_wrong_event_roster_order_intent_and_monitor_return(self):
        for kind in ('missing_sample','reorder','duplicate_birth','extra_final','exception','failed_intent','final_failure',
                     'clock_reverse','sample_failure','sample_nonexit','sample_negative_elapsed','monitor_mismatch'):
            raw,events,saved,report,completion,run=self.journal_case()
            if kind=='missing_sample':events.pop(4)
            elif kind=='reorder':events[1],events[2]=events[2],events[1]
            elif kind=='duplicate_birth':events.insert(2,copy.deepcopy(events[1]))
            elif kind=='extra_final':events.append({**events[-1],'monotonic':8})
            elif kind=='exception':events[-1]['status']='MANAGED_SUPERVISOR_EXCEPTION'
            elif kind=='failed_intent':events[-1]['intended_receipt_status']='FAILED_OR_BLOCKED_FIT_INVOCATION_PRESERVED_NO_RETRY'
            elif kind=='final_failure':events[-1]['failure']='invented final failure'
            elif kind=='clock_reverse':events[4]['monotonic']=0
            elif kind=='sample_failure':events[4]['pending_failure']='reserve'
            elif kind=='sample_nonexit':events[4]['exit_code']=None
            elif kind=='sample_negative_elapsed':events[4]['elapsed_seconds']=-.5
            elif kind=='monitor_mismatch':events[-2]['observed']={'exit_code':0,'failure':None,'samples':2}
            raw=self.journal_bytes(events);self.bind_journal(raw,run,saved)
            with self.subTest(kind=kind),self.assertRaises(AssertionError):fj.validate(raw,saved,report,completion,run)

    def test_journal_binds_generation_run_birth_parent_and_worker(self):
        for kind in ('all_old_generation','birth_generation','birth_run','birth_sha','parent','assigned','resumed','returned','completion_pid','boolean_pid'):
            raw,events,saved,report,completion,run=self.journal_case()
            if kind=='all_old_generation':
                for obj in (report,completion,saved,events[1]):obj['generation_manifest_sha256']='0'*64
            elif kind=='birth_generation':events[1]['generation_manifest_sha256']='0'*64
            elif kind=='birth_run':events[1]['run_admission_sha256']='0'*64
            elif kind=='birth_sha':events[1]['birth_sha256']='0'*64
            elif kind=='parent':events[0]['parent_pid']=122
            elif kind=='assigned':events[2]['worker_pid']=122
            elif kind=='resumed':events[3]['worker_pid']=122
            elif kind=='returned':events[-2]['worker_pid']=122
            elif kind=='completion_pid':completion['worker_pid']=122
            elif kind=='boolean_pid':report['parent_pid']=True
            raw=self.journal_bytes(events);self.bind_journal(raw,run,saved)
            with self.subTest(kind=kind),self.assertRaises(AssertionError):fj.validate(raw,saved,report,completion,run)

    def test_parent_revalidates_bound_journal_and_protects_summary(self):
        self.assertIn('fit_journal_validation',terminal.PROTECTED)
        tree=ast.parse(Path(terminal.__file__).read_text())
        body=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='validate_report')
        self.assertTrue(any(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
            and isinstance(node.func.value,ast.Name) and node.func.value.id=='fit_journal'
            and node.func.attr=='validate' for node in ast.walk(body)))

    def test_v2_scientific_helpers_runtime_and_current_owner_paths_unchanged(self):
        old_ns='generalization_knowncell_replay_v2_execution_20261025'
        old_runtime='generalization_knowncell_replay_v2_runtime_20261025'
        for name in ('build.py','inputs.py','projection_io.py','calibration.py','monitor.py','supervise.py'):
            old=(c.ROOT/'src'/old_ns/name).read_text()
            new=(c.ROOT/'src'/c.NS/name).read_text().replace(c.NS,old_ns).replace(c.runtime.NS,old_runtime)
            with self.subTest(file=name):self.assertEqual(ast.dump(ast.parse(old)),ast.dump(ast.parse(new)))
        for name in ('__init__.py','contracts.py','provider.py','spec.py','prepare.py','tests.py'):
            old=(c.ROOT/'src'/old_runtime/name).read_text()
            new=(c.ROOT/'src'/c.runtime.NS/name).read_text().replace(c.NS,old_ns).replace(c.runtime.NS,old_runtime)
            with self.subTest(file=name):self.assertEqual(ast.dump(ast.parse(old)),ast.dump(ast.parse(new)))
        def functions(path):
            return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(Path(path).read_text()).body if isinstance(node,ast.FunctionDef)}
        old=functions(c.ROOT/'src'/old_ns/'worker.py');new=functions(w.__file__)
        for name in ('runtime_binding','static_contract','current_owner_context','accepted_runtime','read_campaign','run','main'):
            self.assertEqual(old[name],new[name],name)
        self.assertEqual(functions(c.ROOT/'src'/old_ns/'terminal.py')['result_contract'],functions(terminal.__file__)['result_contract'])


def run(*,draft=False):
    assert type(draft) is bool
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    clean=lambda:not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert clean() and not c.RUN_ADMISSION.exists() and not c.SOURCE_ADMISSION.exists()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    filename='synthetic_tests_receipt_draft.json' if draft else 'synthetic_tests_receipt.json'
    c.save_new(c.OUT/filename,{'status':'PASS_INVENTED_INDEPENDENT_REPLAY_EXECUTION_NOT_ACTUAL_REPLAY',
        'tests':result.testsRun,'sources':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources},
        'actual_jobs':0,'actual_resource_probes':0,'actual_provider_invocations':0,'project_payload_reads':0,
        'actual_pools_prepared':0,'optimizer_calls':0,'scientific_imports':False,
        'numeric_pool_and_runtime_edges_in_tests_are_private_mocks':True,
        'draft_before_roomy_fit_generation_supplied':draft})


if __name__=='__main__':run()
