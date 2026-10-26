"""Invented stdlib/array-double tests only. No fitter is called, even mocked."""
import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import arithmetic as a, supplied, spec
from .declarations import ReadOnlySavedCampaign
from src.generalization_knowncell_joint_engine_20261023.tests import tiny_pool
from src.generalization_knowncell_joint_numeric_20261022.fake_array import Array, FakeNP
from src.generalization_knowncell_joint_numeric_20261022 import numeric
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_joint_campaign_20261023.writer import unit_spec
from src.generalization_knowncell_joint_campaign_20261023.tests import plan_for, model_for
from src.generalization_knowncell_joint_implementation_20261022.admission import birth_identity
from src.generalization_knowncell_joint_implementation_20261022.spec import CONFIGS, CELLS


def checkpoint_fixture(arm):
    _, _, pool = tiny_pool()
    task = {'arm':arm,'optimizer_units':2 if arm == 'independent' else 1}
    zero = [0.] * 102
    model = {'arm':arm,'config':dict(CONFIGS[1]),'feature_width':102,
        'canonical_mean':numeric.CANONICAL_MEAN,'canonical_scorer':numeric.SCORER,
        'optimizer_method':numeric.METHOD,'optimizer_options':dict(numeric.OPTIONS),
        'training_rows':pool['binding']['training_rows'],'training_pairs':pool['binding']['training_pairs'],
        'optimizer_units':task['optimizer_units'],'scaling':deepcopy(pool['prepared']['scaling'])}
    weights = pool['prepared']['weights'].tolist()
    cells = [pool['rows'][i]['cell_type'] for i in pool['left']]
    z, labels = pool['prepared']['z'].tolist(), pool['labels']
    if arm == 'independent':
        model['heads'] = {cell:list(zero) for cell in CELLS}
        value, _ = a.scalar.independent_value_gradient(zero+zero,z,labels,weights,cells,CONFIGS[1]['penalty'])
        conditional = {cell:a.conditional_objective(zero,z,labels,weights,cells,cell,CONFIGS[1]['penalty']) for cell in CELLS}
    else:
        model['beta'] = list(zero)
        if arm == 'joint_shrink10': model['delta'] = list(zero)
        function = a.scalar.joint_value_gradient if arm == 'joint_shrink10' else a.scalar.pooled_value_gradient
        value, gradient = function(zero+zero if arm == 'joint_shrink10' else zero,z,labels,weights,cells,CONFIGS[1]['penalty'])
        conditional = {'joint' if arm == 'joint_shrink10' else 'pooled':(value,gradient)}
    model['objective'] = value
    model['optimizer_summaries'] = {name:{'objective':value,'maximum_gradient_abs':max(abs(v) for v in gradient),
        'success':True,'message':'invented saved declaration; no optimizer called','iterations':0}
        for name,(value,gradient) in conditional.items()}
    predictions = {'row_ids':list(pool['binding']['validation_ids']), 'scores':[0.]*pool['binding']['validation_rows'],
        'canonical_shape':[pool['binding']['validation_rows'],102],'canonical_order':'C',
        'canonical_dtype':'float64','canonical_scorer':numeric.SCORER}
    return pool,task,model,predictions


def logical_roster_fixture():
    """Symbolic cohort/zero models for lifecycle tests, not numerical validation."""
    plan = plan_for()
    campaign_raw = lc.canonical_bytes({'status':'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS',**plan.identity()})
    records, by_key = [], {}
    hash_fields = ('training_ids_sha256','training_metadata_sha256','training_features_sha256','training_effects_sha256',
                   'original_pair_roster_sha256','pair_weights_sha256','common_scaling_sha256')
    for task in lc.task_roster():
        key = lc.task_key(task); pool = plan.pool(task)
        config = dict(next(value for value in CONFIGS if value['id'] == task['configuration_id'])) if task['phase']=='inner' else dict(CONFIGS[1])
        selection = None
        if task['phase']=='outer':
            predecessors = {lc.task_key(old):lc.digest(by_key[lc.task_key(old)]['checkpoint_raw']) for old in lc.task_roster()
                if old['phase']=='inner' and old['arm']==task['arm'] and old['outer_fold']==task['outer_fold']}
            selection = {'arm':task['arm'],'outer_fold':task['outer_fold'],'selected_config':config,
                'source_only':True,'primary_paired_only':True,
                'selection_rule':'concatenated_paired_OOF_equal_cell_component_context_direction_regret',
                'prefit_sha256':plan.prefit_sha256,'runtime_binding_sha256':plan.runtime_binding_sha256,
                'source_training_ids_sha256':pool['training_ids_sha256'],
                'configuration_metrics_sha256':'8'*64,'inner_checkpoint_sha256':predecessors}
        identity = birth_identity(arm=task['arm'],phase=task['phase'],outer_fold=task['outer_fold'],inner_fold=task['inner_fold'],
            configuration=config,runtime_binding_sha256=plan.runtime_binding_sha256,prefit_sha256=plan.prefit_sha256,
            **{name:pool[name] for name in hash_fields})
        birth = {'task_key':key,'identity':identity,'campaign_birth_sha256':lc.digest(campaign_raw),
            'source_pool_sha256':lc.hash_value(pool),'full_validation_shape':[pool['validation_rows'],102],
            'prefit_commit':plan.prefit_commit,'source_only_selection':selection,
            'source_only_selection_sha256':lc.hash_value(selection) if selection else None,
            **{name:pool[name] for name in ('validation_ids_sha256','validation_metadata_sha256',
                'validation_features_sha256','validation_effects_sha256','validation_rows')}}
        birth_raw = lc.canonical_bytes(birth)
        model = model_for(task,birth,pool)
        prediction = {'row_ids':pool['validation_ids'],'scores':[0.]*pool['validation_rows'],
            'canonical_shape':[pool['validation_rows'],102],'canonical_order':'C',
            'canonical_dtype':'float64','canonical_scorer':numeric.SCORER}
        saved_raw = lc.canonical_bytes({'task_key':key,'birth_sha256':lc.digest(birth_raw),'model':model,'predictions':prediction})
        complete = {'status':'CHECKPOINT_LIFECYCLE_COMPLETE_NOT_NUMERICAL_REPLAY','task_key':key,
            'birth_sha256':lc.digest(birth_raw),'model_sha256':lc.digest(saved_raw),
            'optimizer_invocations':[{'name':name,'dimension':width,'started':True,'returned':True} for name,width in unit_spec(task['arm'])],
            'optimizer_units':task['optimizer_units'],'configuration':config,
            'source_only_selection_sha256':birth['source_only_selection_sha256'],'campaign_birth_sha256':lc.digest(campaign_raw)}
        item = {'task_key':key,'birth_raw':birth_raw,'checkpoint_raw':saved_raw,'completion_raw':lc.canonical_bytes(complete)}
        records.append(item); by_key[key] = item
    return plan,campaign_raw,records,by_key


class Cases(unittest.TestCase):
    def setUp(self):
        self.byte_patch = patch.object(Array,'tobytes',lambda value,order='C':struct.pack('<'+'d'*len(value.flat()),*value.flat()),create=True)
        self.byte_patch.start()
        self.fit_patch = patch.object(numeric,'fit_prepared',side_effect=AssertionError('No fitter even in invented tests'))
        self.fit_patch.start()
    def tearDown(self):
        self.fit_patch.stop(); self.byte_patch.stop()

    def test_three_arms_match_original_pure_arithmetic_without_optimizer(self):
        for arm in ('pooled','independent','joint_shrink10'):
            values = checkpoint_fixture(arm)
            result = a.inspect_checkpoint(FakeNP,*values,fresh=lambda:None)
            self.assertTrue(result['exact_canonical_scores_equal'])
            self.assertEqual(result['new_optimizer_calls'],0)
            self.assertLess(result['maximum_objective_difference'],1e-14)
            self.assertFalse(result['old_campaign_closure_or_current_owner_certified'])

    def test_sub_tolerance_canonical_drift_still_rejected(self):
        pool,task,model,predictions = checkpoint_fixture('pooled')
        predictions['scores'][0] = 1e-12
        with self.assertRaisesRegex(AssertionError,'Exact canonical'):
            a.inspect_checkpoint(FakeNP,pool,task,model,predictions,fresh=lambda:None)

    def test_changed_weights_effect_order_and_gradient_are_rejected(self):
        for changed in ('weights','effects','gradient'):
            pool,task,model,predictions = checkpoint_fixture('independent')
            if changed=='weights': pool['prepared']['weights'].data[0] += .01
            if changed=='effects': pool['effects'][0],pool['effects'][1] = pool['effects'][1],pool['effects'][0]
            if changed=='gradient': model['optimizer_summaries'][CELLS[0]]['maximum_gradient_abs'] += .001
            with self.subTest(changed=changed),self.assertRaises(AssertionError):
                a.inspect_checkpoint(FakeNP,pool,task,model,predictions,fresh=lambda:None)

    def test_full_validation_shape_for_both_heads(self):
        values = checkpoint_fixture('independent'); shapes = []; original = Array.__matmul__
        def observed(left,right): shapes.append(left.shape); return original(left,right)
        with patch.object(Array,'__matmul__',observed): a.inspect_checkpoint(FakeNP,*values,fresh=lambda:None)
        self.assertEqual(shapes,[(4,102),(4,102)])

    def test_new_resource_callback_failure_precedes_array_use(self):
        values = checkpoint_fixture('pooled')
        def refuse(): raise RuntimeError('future owned forensic resource failure')
        with self.assertRaisesRegex(RuntimeError,'forensic resource'):
            a.inspect_checkpoint(None,*values,fresh=refuse)

    def test_read_only_saved_reader_cannot_write_or_finish(self):
        reader = ReadOnlySavedCampaign(Path('C:/invented_only'),SimpleNamespace(identity=lambda:{}),'a'*64)
        with self.assertRaisesRegex(AssertionError,'cannot write'): reader.write_checkpoint('anything',None)
        with self.assertRaisesRegex(AssertionError,'cannot finish'): reader.finish()

    def test_full63_symbolic_roster_without_campaign_complete_never_claims_formal_replay(self):
        plan,birth,records,by_key = logical_roster_fixture()
        def pool_check(task): return {'binding':plan.pool(task)}
        def numeric_check(pool,task,model,predictions):
            return {'status':spec.NUMERICAL_STATUS,'arm':task['arm'],'source_rows':pool['binding']['training_rows'],
                'source_pairs':pool['binding']['training_pairs'],'target_rows':pool['binding']['validation_rows'],
                'new_optimizer_calls':0,'exact_canonical_scores_equal':True,'tolerance_strictly_below':spec.TOLERANCE,
                'outer_performance_computed':False,'old_campaign_closure_or_current_owner_certified':False,
                'recorded_optimizer_units_not_refitted':task['optimizer_units'],**{name:0. for name in a.ERROR_FIELDS}}
        def selected(plan,task,pool,items,expected,checked):
            self.assertEqual(len([key for key in checked if expected[key]['arm']==task['arm'] and expected[key]['outer_fold']==task['outer_fold']]),6)
            return lc.strict_json(by_key[lc.task_key(task)]['birth_raw'])['source_only_selection'],{}
        with patch.object(supplied,'_selection',side_effect=selected):
            result = supplied._inspect(None,None,plan,birth,records,fresh=lambda:None,pool_check=pool_check,numeric_check=numeric_check)
        self.assertEqual(result['verified_checkpoints'],63)
        self.assertEqual(result['recorded_optimizer_units_not_refitted'],84)
        self.assertEqual(result['source_only_reselections_equal'],9)
        self.assertTrue(result['original_formal_replay_still_ineligible'])
        self.assertNotIn('canonical_outer_records',result)
        self.assertFalse(result['outer_performance_computed_or_published'])

    def test_incomplete_supplied_roster_fails_before_pool_use(self):
        plan,birth,records,_ = logical_roster_fixture()
        def refuse(*_): raise RuntimeError('pool must not be inspected')
        with self.assertRaises(AssertionError):
            supplied._inspect(None,None,plan,birth,records[:-1],fresh=lambda:None,pool_check=refuse,numeric_check=refuse)

    def test_production_source_has_no_fitter_gate_or_formal_replay_calls(self):
        forbidden = {'minimize','fit_prepared','run_campaign','evaluate','verify_campaign'}
        for path in spec.SRC.glob('*.py'):
            if path.name in ('tests.py','prepare.py'): continue
            tree = ast.parse(path.read_text(encoding='utf8'))
            called = {node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id
                for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Attribute,ast.Name))}
            self.assertFalse(called & forbidden,path.name)


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    sources = {path.relative_to(spec.ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in spec.SRC.glob('*.py')}
    receipt = {'status':'PASS_INVENTED_FORENSIC_KERNELS_AND_SYMBOLIC_ROSTER_NOT_ACTUAL_CHECKPOINT_ANALYSIS',
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'source_sha256':sources,
        'actual_biological_payload_reads':0,'actual_native_operations':0,'fitter_invocations_even_mocked':0,
        'actual63_numerical_consistency_established':False,'actual_owned_controller_or_input_admission_ready':False}
    path = spec.OUT/'synthetic_tests_receipt_reviewed.json'
    with path.open('x',encoding='utf8',newline='\n') as stream:
        json.dump(receipt,stream,sort_keys=True,indent=2,allow_nan=False); stream.write('\n')
    print('FORENSIC_SOURCE_TESTS_ONLY',result.testsRun,hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__': run()
