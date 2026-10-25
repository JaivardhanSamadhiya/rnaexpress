"""Invented lifecycle/storage/gate tests; no project data or scientific runtime."""
import ast
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from . import common as c,worker as w,results_io as io,terminal,calibration as cal
from src.generalization_knowncell_joint_gate_20261023 import gate


def run_record():
    return {'status':'FROZEN_ONE_COMPLETE_OUTER_EVALUATION_RUN_NO_FIT','stage':c.STAGE,'invocation':c.INVOCATION,
        'generation_manifest_sha256':'1'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,
        'approval_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),'runtime_import_authorized':True,
        'saved_label_read_authorized':True,'evaluation_authorized':True,'CORE_read_authorized':False,
        'model_fitting_authorized':False,'array_reload_authorized':False,'pool_preparation_authorized':False,'data_pins':{},
        'input_pins':{**c.INPUT_PINS,c.REQUEST:'2'*64,c.STATIC_BINDING:'3'*64,c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix():'4'*64,
            **{name:'5'*64 for name in (c.PREFIT,c.PREFIT_COMPLETION,c.PREFIT_SUPERVISOR,c.PROJECTION_ADMISSION,c.REPLAY_REPORT,c.REPLAY_COMPLETION,c.REPLAY_SUPERVISOR)}},
        'actual_prefit_commit':'a'*40,'projection_root_admission_commit':'b'*40,'checkpoint_count':63,
        'recorded_optimizer_units':84,'new_optimizer_calls':0,'resume':False,'independent_replay_required':True}


def result():
    primary={arm:{'components':187,'macro_regret':.49,'per_cell_regret':{cell:.49 for cell in terminal.CELLS}} for arm in terminal.ARMS}
    comparison={name:{'mean_gain':0.,'remaining_gain':0.,'macro_wrong_direction_harm':0.,
        'per_cell_gain':{cell:0. for cell in terminal.CELLS},'wrong_direction_harm':{cell:0. for cell in terminal.CELLS}}
        for name in ('pooled','independent')}
    bootstrap={'draws':5000,'seed':20261007,'components':['invented_'+str(i) for i in range(187)],
        'fixed_predictions_only':True,'std_random_or_refits_used':False,'intervals':{'pooled':[-.01,.01],'independent':[-.01,.01]}}
    verdict=gate.thresholds(primary['joint_shrink10'],comparison,bootstrap['intervals'])
    return {'status':verdict['status'],'scope':'represented_known_cells_unseen_genes_exposed_development',
        'model_fits_or_refits':0,'new_configuration_selection':False,'independent_confirmation':False,
        'unknown_cell_generalization':False,'novelty_certified':False,'localization_generalization_pass':False,
        'coverage':{'rows_per_arm':13781,'outer_records':9,'each_row_once_per_arm':True,'unmatched_predictions_retained':True},
        'all_decisions':{arm:[{'invented':True}]*9650 for arm in terminal.ARMS},
        'primary_decisions':{arm:[{'invented':True}]*9632 for arm in terminal.ARMS},
        'unmatched_decisions':{arm:[{'invented':True}]*18 for arm in terminal.ARMS},
        'primary_summaries':primary,'comparisons':comparison,'bootstrap':bootstrap,'gate':verdict}


class Cases(unittest.TestCase):
    def test_failed_or_incomplete_replay_cannot_reach_evaluator(self):
        for index in (0,1,2):
            values=[{'status':'ACTUAL_ONE_OWNED_INDEPENDENT63_CHECKPOINT_REPLAY_NO_EVALUATION'},
                {'status':'PASS_INDEPENDENT_REPLAY_WORKER_CALLBACKS_RESTORED_NO_EVALUATION'},
                {'status':'PASS_INDEPENDENT63_CHECKPOINT_REPLAY_PENDING_ROOT_ACCEPTANCE','failure':None}]
            values[index]['status']='FAILED_OR_INCOMPLETE'
            with self.subTest(index=index),self.assertRaises(AssertionError):w.replay_contract(*values,{}, {},{})

    def test_lossless_deterministic_complete_result_and_separate_summary(self):
        value={'status':'invented','all_decisions':{'a':[{'effect':-0.,'value':.125}]},
            'primary_decisions':{},'unmatched_decisions':{},'bootstrap':{'interval':[.1,.2]}}
        first,cert=io.encode(value);second,other=io.encode(value)
        self.assertEqual(first,second);self.assertEqual(cert,other)
        restored=io.decode(first,cert);self.assertEqual(io.lc.canonical_bytes(value),io.lc.canonical_bytes(restored))
        self.assertNotIn('all_decisions',io.summary(value));self.assertIn('all_decisions',restored)

    def test_storage_rejects_changed_bytes_lengths_and_oversized_result(self):
        compressed,cert=io.encode({'value':1.})
        with self.assertRaises(AssertionError):io.decode(compressed[:-1],cert)
        changed=dict(cert);changed['canonical_json_sha256']='0'*64
        with self.assertRaises(AssertionError):io.decode(compressed,changed)
        with patch.object(io,'MAX_RAW',8),self.assertRaises(AssertionError):io.encode({'value':'too long'})

    def test_no_array_pool_fit_or_extra_inputs_in_evaluation_run(self):
        c.run_contract(run_record(),'1'*64)
        for key in ('CORE_read_authorized','array_reload_authorized','pool_preparation_authorized','model_fitting_authorized'):
            item=run_record();item[key]=True
            with self.subTest(key=key),self.assertRaises(AssertionError):c.run_contract(item,'1'*64)
        item=run_record();item['data_pins']={c.NPZ:c.NPZ_SHA}
        with self.assertRaises(AssertionError):c.run_contract(item,'1'*64)

    def test_complete_replay_and_zero_new_fits_mandatory(self):
        for key,bad in (('independent_replay_required',False),('checkpoint_count',62),('recorded_optimizer_units',83),('new_optimizer_calls',1),('resume',True)):
            item=run_record();item[key]=bad
            with self.subTest(key=key),self.assertRaises(AssertionError):c.run_contract(item,'1'*64)

    def test_static_binding_cannot_contain_current_proof_or_changed_inputs(self):
        run=run_record();manifest={'files':{c.WORKER_SOURCE:'6'*64}}
        value={'status':'FROZEN_COMPLETE_REPLAY_AND_ORIGINAL_EVALUATION_INPUTS_NO_FIT','stage':c.STAGE,'generation_manifest_sha256':'1'*64,
            'controller_source':c.WORKER_SOURCE,'controller_source_sha256':'6'*64,'controller_source_admission_sha256':'4'*64,
            **{key:run['input_pins'][name] for key,name in (('metadata_bundle_sha256',c.METADATA_BUNDLE),('label_certificate_sha256',c.LABEL_CERTIFICATE),
                ('replay_report_sha256',c.REPLAY_REPORT),('actual_prefit_sha256',c.PREFIT),('projection_root_admission_sha256',c.PROJECTION_ADMISSION))},
            'stable_admitted_runtime_binding_sha256':c.ARRAY_RUNTIME_ANCHOR_SHA,'original_evaluation_source_manifest_sha256':c.EVALUATION_READY_SHA,
            'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
            'no_new_fit_array_or_pool_authority':True}
        request={'stable_admitted_runtime_binding_sha256':c.ARRAY_RUNTIME_ANCHOR_SHA,'static_root_binding_sha256':'3'*64,
            'generation_manifest_sha256':'1'*64,'controller_source_admission_sha256':'4'*64,
            'actual_prefit_sha256':'5'*64,'projection_root_admission_sha256':'5'*64}
        w.static_contract(value,request,run,'1'*64,manifest)
        for key,bad in (('caller_birth_sha256','0'*64),('replay_report_sha256','0'*64),('no_new_fit_array_or_pool_authority',False)):
            changed=dict(value);changed[key]=bad
            with self.subTest(key=key),self.assertRaises(AssertionError):w.static_contract(changed,request,run,'1'*64,manifest)

    def test_NO_GO_is_valid_complete_evaluation_and_gate_cannot_be_replaced(self):
        value=result();self.assertEqual(value['status'],'NO-GO');terminal.result_contract(value)
        bad=copy.deepcopy(value);bad['gate']['checks']={key:True for key in bad['gate']['checks']}
        with self.assertRaises(AssertionError):terminal.result_contract(bad)

    def test_original_complete_counts_bootstrap_and_scope_required(self):
        for change in ('missing','seed','draws','unknown_cell','refit'):
            value=result()
            if change=='missing':value['primary_decisions']['pooled']=value['primary_decisions']['pooled'][:-1]
            if change=='seed':value['bootstrap']['seed']+=1
            if change=='draws':value['bootstrap']['draws']=4999
            if change=='unknown_cell':value['unknown_cell_generalization']=True
            if change=='refit':value['model_fits_or_refits']=1
            with self.subTest(change=change),self.assertRaises(AssertionError):terminal.result_contract(value)

    def test_evaluator_is_original_object_without_sampler_or_fitting_calls(self):
        from src.generalization_knowncell_joint_evaluation_20261023.evaluation import evaluate
        self.assertIs(w.evaluate,evaluate)
        tree=ast.parse(Path(w.__file__).read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        forbidden=('reload_matrix','prepare_pools','run_campaign','minimize','fit_prepared','select_outer')
        self.assertFalse(any((isinstance(n.func,ast.Name) and n.func.id in forbidden) or
            (isinstance(n.func,ast.Attribute) and n.func.attr in forbidden) for n in calls))

    def test_calibration_same_five_aliases_and_monitor_after_declared_stage_changes(self):
        old=(c.ROOT/'src/generalization_knowncell_replay_execution_20261024/calibration.py').read_text()
        new=Path(cal.__file__).read_text().replace(c.NS,'generalization_knowncell_replay_execution_20261024')
        new=new.replace(c.INVOCATION,'independent_checkpoint_and_source_selection_replay').replace("stage=='evaluation'","stage=='replay'")
        self.assertEqual(ast.dump(ast.parse(old),include_attributes=False),ast.dump(ast.parse(new),include_attributes=False))
        self.assertEqual(len(cal.TARGETS),5)

    def test_partial_output_or_full_result_file_refuses_new_birth(self):
        with patch.object(c.os.path,'lexists',side_effect=lambda p:p==c.EVALUATION_DATA),self.assertRaises(AssertionError):c.require_new_outputs()

    def test_runtime_request_matches_stage_and_forbids_array_or_pool_permission(self):
        from src.generalization_knowncell_evaluation_runtime_20261025.tests import request
        req=request();m={'files':{c.runtime.PREPARATION:'b'*64,c.runtime.SOURCE:'e'*64}}
        w.runtime_binding(req,'a'*64,m)
        req['array_reload_authorized']=True
        with self.assertRaises(AssertionError):w.runtime_binding(req,'a'*64,m)


def run():
    clean=lambda:not any(n.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for n in sys.modules)
    assert clean() and not c.RUN_ADMISSION.exists() and not c.SOURCE_ADMISSION.exists()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases));assert result.wasSuccessful() and clean()
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    c.save_new(c.OUT/'synthetic_tests_receipt.json',{'status':'PASS_INVENTED_FROZEN_EVALUATION_EXECUTION_NOT_ACTUAL_EVALUATION',
        'tests':result.testsRun,'sources':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources},
        'actual_jobs':0,'actual_resource_probes':0,'actual_provider_invocations':0,'project_payload_reads':0,
        'actual_pools_prepared':0,'optimizer_calls':0,'scientific_imports':False,'fixture_decisions_are_invented':True})


if __name__=='__main__':run()
