"""Scoped invented-list tests only; no scientific package/project-data imports."""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
from . import admission, contracts as c, kernels as k, prepare as p, selection as s
from .spec import NS, DESIGN_NS, ARMS, CELLS, CONFIGS, COUNTS, GATE, METADATA_COLUMNS, fixed_contract

ROOT = Path(__file__).resolve().parents[2]


def rows_fixture(unequal=False, unmatched=False):
    rows = []
    by_fold = {0: ('g0',), 1: ('g1', 'g2') if unequal else ('g1',), 2: ('g3',) if unequal else ('g2',)}
    for fold, genes in by_fold.items():
        for gene in genes:
            for cell in CELLS:
                for edit in (0, 1):
                    rows.append({'intervention_id': f'{gene}:{cell}:{edit}', 'dataset': 'mikl_gse173098',
                                 'cell_type': cell, 'endpoint_class': 'projection',
                                 'parent_context_id': f'{gene}:{cell}', 'biological_component': gene,
                                 'gene_transcript': gene, 'held_parent_fold': fold,
                                 'parent_sequence': f'invented_parent_{gene}',
                                 'mutant_sequence': f'invented_mutant_{gene}_{edit}'})
    if unmatched:
        for edit in (0, 1):
            row = next(r for r in rows if r['biological_component'] == 'g1' and r['cell_type'] == CELLS[0]).copy()
            row.update(intervention_id=f'unmatched:{edit}', parent_context_id='unmatched',
                       parent_sequence='unmatched_parent', mutant_sequence=f'unmatched_mutant_{edit}')
            rows.append(row)
    return rows


def truth_fixture(rows):
    return {row['intervention_id']: (-1. if row['intervention_id'].endswith(':0') else 1.) for row in rows}


def source_fixture(unmatched=False):
    rows = rows_fixture(unequal=True, unmatched=unmatched)
    train, _ = c.union_split(rows, 0); source = [rows[i] for i in train]
    truths = truth_fixture(source); batches = {}
    for config in CONFIGS:
        by_fold = {}
        for fold in (1, 2):
            good = (config['id'] == 'pair_005' and fold == 2) or (config['id'] == 'pair_05' and fold == 1)
            by_fold[fold] = {r['intervention_id']: truths[r['intervention_id']] * (1 if good else -1)
                             for r in source if r['held_parent_fold'] == fold}
        batches[config['id']] = by_fold
    return rows, truths, batches


class ObjectiveTests(unittest.TestCase):
    def setUp(self):
        self.z = [[1., -.2], [-.7, .5], [.9, .8], [-1., -.4]]
        self.y = [1, -1, -1, 1]; self.w = [.1, .4, .2, .3]
        self.cells = [CELLS[0], CELLS[0], CELLS[1], CELLS[1]]
        self.theta = [.2, -.4, .6, .7]

    def test_fixed_contract(self): self.assertTrue(fixed_contract())

    def test_shrink10_gradient_finite_differences_all_lambdas(self):
        for config in CONFIGS:
            penalty = config['penalty']; _, gradient = k.joint_value_gradient(self.theta, self.z, self.y, self.w, self.cells, penalty)
            for index, expected in enumerate(gradient):
                left, right = list(self.theta), list(self.theta); left[index] -= 1e-6; right[index] += 1e-6
                f = lambda theta: k.joint_value_gradient(theta, self.z, self.y, self.w, self.cells, penalty)[0]
                self.assertLess(abs((f(right)-f(left))/2e-6 - expected), 2e-9)

    def test_multiplier1_independent_value_and_gradient_mapping(self):
        beta, delta = self.theta[:2], self.theta[2:]
        heads = [a+b for a,b in zip(beta, delta)] + [a-b for a,b in zip(beta, delta)]
        for config in CONFIGS:
            a, ga = k.shared_reference(self.theta, self.z, self.y, self.w, self.cells, config['penalty'], 1.)
            b, gb = k.independent_value_gradient(heads, self.z, self.y, self.w, self.cells, config['penalty'])
            self.assertAlmostEqual(a, b, places=13)
            for j in range(2):
                self.assertAlmostEqual(ga[j], gb[j]+gb[j+2], places=13)
                self.assertAlmostEqual(ga[j+2], gb[j]-gb[j+2], places=13)

    def test_independent_conditional_weight_normalization(self):
        heads = [.3, -.2, .7, -.4]; penalty = .05
        actual, _ = k.independent_value_gradient(heads, self.z, self.y, self.w, self.cells, penalty)
        expected = 0.
        for cell, coef in ((CELLS[0], heads[:2]), (CELLS[1], heads[2:])):
            conditional = math.fsum(k.residual(y*k.dot(row,coef), y, 2*w)[0]
                                    for row,y,w,c in zip(self.z,self.y,self.w,self.cells) if c==cell)
            expected += .5 * (conditional + penalty/2*k.dot(coef,coef))
        self.assertAlmostEqual(actual, expected, places=13)

    def test_zero_delta_objective_and_beta_gradient_equal_pooled(self):
        a, ga = k.pooled_value_gradient(self.theta[:2], self.z, self.y, self.w, self.cells, .05)
        b, gb = k.joint_value_gradient(self.theta[:2]+[0.,0.], self.z, self.y, self.w, self.cells, .05)
        self.assertAlmostEqual(a,b,places=13)
        for x,y in zip(ga,gb[:2]): self.assertAlmostEqual(x,y,places=13)

    def test_fixed_extra_penalty_has_exact_value_and_gradient_effect(self):
        a, ga = k.shared_reference(self.theta,self.z,self.y,self.w,self.cells,.05,1.)
        b, gb = k.joint_value_gradient(self.theta,self.z,self.y,self.w,self.cells,.05)
        self.assertAlmostEqual(b-a,.05/2*9*k.dot(self.theta[2:],self.theta[2:]),places=13)
        self.assertEqual(ga[:2],gb[:2])
        for j in range(2): self.assertAlmostEqual(gb[j+2]-ga[j+2],.05*9*self.theta[j+2],places=13)

    def test_large_margins_remain_finite(self):
        for sign in (-1,1):
            value, gradient = k.joint_value_gradient([sign*1000.,0.],[[1.],[1.]],[1,-1],[.5,.5],list(CELLS),.05)
            self.assertTrue(all(math.isfinite(v) for v in [value]+gradient))

    def test_pair_reversal_preserves_value_and_gradient(self):
        a = k.joint_value_gradient(self.theta,self.z,self.y,self.w,self.cells,.05)
        b = k.joint_value_gradient(self.theta,[[-v for v in row] for row in self.z],[-v for v in self.y],self.w,self.cells,.05)
        for x,y in zip([a[0]]+a[1],[b[0]]+b[1]): self.assertAlmostEqual(x,y,places=13)

    def test_unequal_cell_mass_and_wrong_cell_alias_fail(self):
        for weights in ([.1,.3,.2,.4],[.1,-.1,.5,.5]):
            with self.assertRaises(AssertionError): k.joint_value_gradient(self.theta,self.z,self.y,weights,self.cells,.05)
        with self.assertRaises(AssertionError): k.joint_value_gradient(self.theta,self.z,self.y,self.w,['CAD']*3+['N2A'],.05)

    def test_common_scale_and_unsupported_coefficients(self):
        scaling = k.common_scale([[2.,0.],[-1.,0.]],[.5,.5])
        self.assertAlmostEqual(scaling['pair_rms'][0],math.sqrt(2.5))
        self.assertEqual(scaling['active'],[True,False]); self.assertEqual(scaling['scale'][1],1.)
        k.check_support([1.,0.],scaling)
        with self.assertRaises(AssertionError): k.check_support([1.,1e-20],scaling)

    def test_known_cell_heads_can_differ_on_identical_sequence_features(self):
        scaling = k.common_scale([[1.,0.],[1.,0.]],[.5,.5])
        model = {'scaling':scaling,'beta':[0.,0.],'delta':[1.,0.]}
        self.assertEqual(k.reference_scores('joint_shrink10',[[2.,0.],[2.,0.]],list(CELLS),model),[2.,-2.])
        independent = {'scaling':scaling,'heads':{CELLS[0]:[1.,0.],CELLS[1]:[-1.,0.]}}
        self.assertEqual(k.reference_scores('independent',[[2.,0.],[2.,0.]],list(CELLS),independent),[2.,-2.])


class MetadataTests(unittest.TestCase):
    def test_both_cell_outer_and_inner_coverage(self):
        rows = rows_fixture(); targeted = Counter()
        for outer in (0,1,2):
            train,target = c.union_split(rows,outer); targeted.update(target)
            source = [rows[i] for i in train]; validated = Counter()
            for inner in set((0,1,2))-{outer}:
                left,right = c.union_split(source,inner); validated.update(right)
                self.assertEqual({source[i]['cell_type'] for i in left},set(CELLS))
                self.assertEqual({source[i]['cell_type'] for i in right},set(CELLS))
            self.assertEqual(validated,Counter(range(len(source))))
        self.assertEqual(targeted,Counter(range(len(rows))))

    def test_gene_and_allele_contradictions_stop(self):
        rows = rows_fixture()
        for row in rows:
            if row['held_parent_fold']==1: row['gene_transcript']=' G0 '
        with self.assertRaises(AssertionError): c.union_split(rows,0)
        rows = rows_fixture(); rows[4]['mutant_sequence']=rows[0]['parent_sequence']
        with self.assertRaises(AssertionError): c.union_split(rows,0)

    def test_component_fold_and_partial_context_fail(self):
        rows = rows_fixture(); rows[0]['held_parent_fold']=1
        with self.assertRaises(AssertionError): c.union_split(rows,0)
        rows = rows_fixture(); rows[0]['parent_context_id']=rows[4]['parent_context_id']
        with self.assertRaises(AssertionError): c.union_split(rows,0)

    def test_metadata_rejects_labels_and_population_change(self):
        rows = rows_fixture(); rows[0]['measured_delta']=1.
        with self.assertRaises(AssertionError): c.validate_rows(rows)
        with self.assertRaises(AssertionError): c.full_metadata_contract(rows_fixture())

    def test_pairing_never_intersects_menus(self):
        rows = rows_fixture(); pairs, unmatched = c.exact_pairs(rows)
        self.assertEqual((len(pairs),len(unmatched)),(3,0))
        rows[-1]['mutant_sequence']='different_fullmenu_member'
        pairs,unmatched = c.exact_pairs(rows)
        self.assertEqual((len(pairs),len(unmatched)),(2,2))

    def test_duplicate_alleles_and_cell_ambiguity_fail(self):
        rows=rows_fixture(); rows[1]['mutant_sequence']=rows[0]['mutant_sequence']
        with self.assertRaises(AssertionError): c.exact_pairs(rows)
        rows=rows_fixture(); rows[0]['cell_type']='N2A'
        with self.assertRaises(AssertionError): c.validate_rows(rows)

    def test_hierarchical_weights_equal_cell_gene_despite_unequal_menus(self):
        rows = rows_fixture(unequal=True,unmatched=True); weights=c.hierarchical_weights(rows)
        for cell in CELLS:
            for gene in ('g0','g1','g2','g3'):
                mass=math.fsum(w for row,w in zip(rows,weights) if row['cell_type']==cell and row['biological_component']==gene)
                self.assertAlmostEqual(mass,1/8)

    def test_original_allpairs_and_missing_context_preference_contract(self):
        rows=rows_fixture(); truths=truth_fixture(rows)
        left=list(range(0,len(rows),2)); right=[i+1 for i in left]
        weights=c.preference_contract(rows,truths,left,right,[-1]*len(left))
        self.assertAlmostEqual(math.fsum(weights),1.)
        with self.assertRaises(AssertionError): c.preference_contract(rows,truths,left[:-1],right[:-1],[-1]*(len(left)-1))
        with self.assertRaises(AssertionError): c.preference_contract(rows,truths,left,right,[1]*len(left))

    def test_checkpoint_roster_exact_63_files_84_units(self):
        roster=c.checkpoint_roster(); self.assertEqual(len(roster),63)
        self.assertEqual(sum(r['optimizer_units'] for r in roster),84)
        for arm in ARMS: self.assertEqual(sum(r['arm']==arm for r in roster),21)
        self.assertEqual(sum(r['phase']=='inner' for r in roster),54)


class SelectionTests(unittest.TestCase):
    def test_combined_oof_selects_not_equal_fold_macros(self):
        rows,truths,batches=source_fixture()
        result=s.select_source_config(rows,0,truths,batches)
        self.assertEqual(result['selected_config']['id'],'pair_05')
        self.assertAlmostEqual(result['configuration_metrics']['pair_005']['macro_regret'],2/3)
        self.assertAlmostEqual(result['configuration_metrics']['pair_05']['macro_regret'],1/3)

    def test_selector_rejects_outer_truth_missing_scores_and_wrong_fold(self):
        rows,truths,batches=source_fixture(); truths[rows[0]['intervention_id']]=1.
        with self.assertRaises(AssertionError): s.select_source_config(rows,0,truths,batches)
        rows,truths,batches=source_fixture(); one=next(iter(batches['pair_005'][1])); del batches['pair_005'][1][one]
        with self.assertRaises(AssertionError): s.select_source_config(rows,0,truths,batches)
        rows,truths,batches=source_fixture(); one=next(iter(batches['pair_005'][1])); batches['pair_005'][2][one]=batches['pair_005'][1].pop(one)
        with self.assertRaises(AssertionError): s.select_source_config(rows,0,truths,batches)

    def test_unmatched_menus_predicted_but_cannot_select(self):
        rows,truths,batches=source_fixture(unmatched=True)
        original=s.select_source_config(rows,0,truths,batches)
        for config in CONFIGS:
            for values in batches[config['id']].values():
                for key in values:
                    if key.startswith('unmatched:'): values[key]*=-1000
        changed=s.select_source_config(rows,0,truths,batches)
        self.assertEqual(original,changed)

    def test_exact_primary_roster_and_candidate_count_required(self):
        rows=rows_fixture(); pairs,_=c.exact_pairs(rows); truths=truth_fixture(rows)
        records=s.decisions(rows,truths,truths)
        self.assertEqual(s.primary_metrics(records,pairs)['macro_regret'],0.)
        with self.assertRaises(AssertionError): s.primary_metrics(records[:-1],pairs)
        records[0]['candidates']=3
        with self.assertRaises(AssertionError): s.primary_metrics(records,pairs)

    def test_lexical_id_exact_tie_and_no_near_tie_band(self):
        rows=rows_fixture(); truths=truth_fixture(rows); scores={key:0. for key in truths}
        records=s.decisions(rows,scores,truths)
        chosen=next(row for row in records if row['direction']==1 and row['parent_context_id']=='g0:CAD')
        self.assertEqual(chosen['selected_id'],'g0:CAD:0')
        scores['g0:CAD:1']=1e-16
        chosen=next(row for row in s.decisions(rows,scores,truths) if row['direction']==1 and row['parent_context_id']=='g0:CAD')
        self.assertEqual(chosen['selected_id'],'g0:CAD:1')

    def test_reference_rounding_bound_retains_canonical_choice(self):
        rows=rows_fixture(); truths=truth_fixture(rows); canonical={key:0. for key in truths}
        reference=dict(canonical); reference['g0:CAD:1']=1e-16
        retained,error=s.bound_reference(canonical,reference)
        self.assertIs(retained,canonical); self.assertGreater(error,0.)
        chosen=next(row for row in s.decisions(rows,retained,truths) if row['direction']==1 and row['parent_context_id']=='g0:CAD')
        self.assertEqual(chosen['selected_id'],'g0:CAD:0')
        reference['g0:CAD:1']=1e-8
        with self.assertRaises(AssertionError): s.bound_reference(canonical,reference)

    def test_wrong_direction_error_decomposition(self):
        rows=rows_fixture(); scores={r['intervention_id']:0. for r in rows}
        for effects, expected in (((-2.,-1.),(0.,1.,0.)),((-1.,0.),(0.,0.,1.)),((-1.,1.),(1.,0.,0.))):
            truths={r['intervention_id']:effects[int(r['intervention_id'][-1])] for r in rows}
            for row in s.decisions(rows,scores,truths):
                if row['direction']!=1: continue
                self.assertEqual((row['avoidable_wrong'],row['unavoidable_wrong'],row['neutral_only_alternative_wrong']),expected)
                self.assertEqual(sum(expected),row['wrong_direction'])

    def test_fixed_config_order_tolerance_and_nan_rejection(self):
        self.assertEqual(s.choose_config([.3+5e-13,.3,.5])['id'],'pair_005')
        self.assertEqual(s.choose_config([.3+2e-12,.3,.5])['id'],'pair_05')
        with self.assertRaises(AssertionError): s.choose_config([.3,float('nan'),.5])


class AdmissionTests(unittest.TestCase):
    def test_resources_before_action_and_no_PUM_exception(self):
        environment={key:'1' for key in admission.THREAD_KEYS}; events=[]
        def probe(): events.append('probe'); return {'physical_available':3*2**30,'disk_available':2**30}
        def action(): events.append('action'); return 'invented'
        self.assertEqual(admission.before_action(action,probe,environment),'invented')
        self.assertEqual(events,['probe','action'])
        for snapshot in ({'physical_available':3*2**30-1,'disk_available':2**30},
                         {'physical_available':3*2**30,'disk_available':2**30-1},
                         {'physical_available':3*2**30,'disk_available':2**30,'PUM_resource_exception_applied':True}):
            with self.assertRaises(AssertionError): admission.before_action(action,lambda:snapshot,environment)
        self.assertEqual(events,['probe','action'])
        environment['OMP_NUM_THREADS']='2'
        with self.assertRaises(AssertionError): admission.before_action(action,probe,environment)

    def test_birth_identity_binds_distinct_scientific_inputs(self):
        arguments={name:'a'*64 for name in ('training_ids_sha256','training_metadata_sha256','training_features_sha256',
                   'training_effects_sha256','original_pair_roster_sha256','pair_weights_sha256',
                   'common_scaling_sha256','runtime_binding_sha256','prefit_sha256')}
        first=admission.birth_identity(arm='joint_shrink10',phase='inner',outer_fold=0,inner_fold=1,
                                       configuration=CONFIGS[0],**arguments)
        self.assertEqual(first['deviation_multiplier'],10.)
        self.assertFalse(first['old_fitted_checkpoint_reuse'])
        arguments['training_effects_sha256']='b'*64
        second=admission.birth_identity(arm='joint_shrink10',phase='inner',outer_fold=0,inner_fold=1,
                                        configuration=CONFIGS[0],**arguments)
        self.assertNotEqual(first,second)
        with self.assertRaises(AssertionError): admission.birth_identity(arm='pooled',phase='inner',outer_fold=0,inner_fold=0,configuration=CONFIGS[0],**arguments)

    def test_path_alias_collisions_and_escape_rejected(self):
        self.assertEqual(p.normalize_map({'a\\b':'a'*64}),{'a/b':'a'*64})
        for mapping in ({'a\\b':'a'*64,'a/b':'a'*64},{'../x':'a'*64},{'C:/x':'a'*64}):
            with self.assertRaises(AssertionError): p.normalize_map(mapping)

    def test_design_source_contract_never_reads_declared_biological_inputs(self):
        files={f'src/{DESIGN_NS}/{name}':name.encode() for name in ('__init__.py','spec.py','kernels.py','contracts.py','tests.py','freeze.py')}
        files[f'reports/{DESIGN_NS}/protocol.md']=b'invented protocol'
        design={'status':'FROZEN_STATIC_JOINT_KNOWNCELL_DESIGN_NOT_PROJECT_ADMISSION','arms':list(ARMS),
                'configs':list(CONFIGS),'counts':COUNTS,'gate':GATE,'project_dataset_reads':0,'project_feature_reads':0,
                'project_outcome_reads':0,'models_fitted':0,'scientific_runtimes_imported':False,
                'requires_separate_root_committed_metadata_and_FIT_admissions':True,
                'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()},
                'declared_future_inputs_not_opened':{value:{'actual_bytes_rehashed':False,'declared_sha256':'a'*64}
                                                    for key,value in p.ALIASES.items() if key in ('core','feature')}}
        accessed=[]
        def read(name): accessed.append(name); return files[name]
        self.assertEqual(set(p.design_source_contract(design,read)),set(files))
        self.assertEqual(set(accessed),set(files))
        design['files'][next(iter(files))]='0'*64
        with self.assertRaises(AssertionError): p.design_source_contract(design,read)


def run():
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    assert not any(name in sys.modules for name in forbidden)
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    assert result.wasSuccessful()
    assert not any(name in sys.modules for name in forbidden)
    source=ROOT/'src'/NS; paths=sorted(source.glob('*.py'))
    for path in paths: ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    payload={'status':'PASS_INVENTED_STDLIB_IMPLEMENTATION_CHECKS','tests':result.testsRun,
             'elapsed_seconds':time.monotonic()-started,'generated_utc':datetime.now(timezone.utc).isoformat(),
             'python_executable':sys.executable,'python_version':sys.version,'scientific_runtimes_imported':False,
             'project_dataset_reads':0,'project_feature_reads':0,'project_outcome_reads':0,'models_fitted':0,
             'actual_optimizer_calls':0,'full_trainer_implemented':False,
             'source_files':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}
    target=ROOT/'results'/NS/'synthetic_tests_receipt.json'
    with target.open('xb') as handle: handle.write((json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
    print('INVENTED_STDLIB_CHECKS_PASS',result.testsRun,hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__': run()
