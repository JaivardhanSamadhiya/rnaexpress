"""Invented records and mocked bootstrap only; no project/native execution."""
import ast
from collections import Counter
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from . import evaluation as e
from src.generalization_knowncell_joint_campaign_20261023.spec import SCORER
from src.generalization_knowncell_joint_implementation_20261022.tests import rows_fixture, truth_fixture

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_knowncell_joint_evaluation_20261023'
ENV = {key:'1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}


def probe():
    return {'physical_available':3*2**30, 'disk_available':2**30}


def fixture():
    rows = rows_fixture(unequal=True, unmatched=True)
    effects = truth_fixture(rows)
    records = []
    for arm in e.ARMS:
        for fold in e.FOLDS:
            target = [row for row in rows if row['held_parent_fold'] == fold]
            records.append({'arm':arm, 'outer_fold':fold, 'predictions':{
                'row_ids':[row['intervention_id'] for row in target],
                'scores':[effects[row['intervention_id']]*(1. if arm == 'joint_shrink10' else -1.) for row in target],
                'canonical_shape':[len(target),102], 'canonical_dtype':'float64',
                'canonical_order':'C', 'canonical_scorer':SCORER}})
    pairs, unmatched = e.contracts.exact_pairs(rows)
    by_cell = Counter(row['cell_type'] for row in rows)
    paired_contexts = {context for pair in pairs for context in pair['contexts'].values()}
    small_counts = {'all_rows':len(rows), 'CAD_rows':by_cell[e.CELLS[0]], 'Neuro-2a_rows':by_cell[e.CELLS[1]],
                    'components':len({row['biological_component'] for row in rows}),
                    'paired_menus':len(pairs), 'paired_rows':sum(row['parent_context_id'] in paired_contexts for row in rows),
                    'paired_contexts':len(paired_contexts), 'paired_directional_decisions':2*len(paired_contexts),
                    'unmatched_contexts':len(unmatched),
                    'unmatched_rows':sum(row['parent_context_id'] in unmatched for row in rows)}
    return rows, effects, records, small_counts


@contextmanager
def invented_counts(counts):
    """Test-process substitution only; the actual entrypoint keeps fixed counts."""
    with ExitStack() as stack:
        for module in (e, e.contracts, e.gate):
            stack.enter_context(patch.object(module, 'COUNTS', counts))
        stack.enter_context(patch.object(e, 'FULL_DECISIONS_PER_ARM',
                                        counts['paired_directional_decisions']+2*counts['unmatched_contexts']))
        yield


def bootstrap_for(rows):
    def invented(np, comparisons):
        assert np == 'invented-bootstrap-sentinel' and set(comparisons) == {'pooled','independent'}
        return {'components':sorted({row['biological_component'] for row in rows}),
                'draws':5000, 'seed':20261007, 'fixed_predictions_only':True,
                'std_random_or_refits_used':False,
                'shared_original_exponential_draws_sha256':'0'*64,
                'intervals':{name:[.1,1.] for name in comparisons}}
    return invented


class Cases(unittest.TestCase):
    def test_all_arms_all_folds_retain_unmatched_and_only_fixed_joint_is_eligible(self):
        rows, effects, records, counts = fixture()
        with invented_counts(counts), patch.object(e.gate,'native_shared_bootstrap',side_effect=bootstrap_for(rows)) as boot:
            result = e.evaluate('invented-bootstrap-sentinel',rows,effects,records,probe=probe,environment=ENV)
        self.assertEqual(boot.call_count,1)
        self.assertEqual(result['status'],'JOINT_KNOWN_CELL_DEVELOPMENT_GO')
        self.assertEqual(result['gate']['claim_eligible_arm'],'joint_shrink10')
        self.assertEqual(result['coverage']['rows_per_arm'],len(rows))
        self.assertTrue(result['coverage']['each_row_once_per_arm'])
        for arm in e.ARMS:
            self.assertEqual(len(result['all_decisions'][arm]),18)
            self.assertEqual(len(result['primary_decisions'][arm]),16)
            self.assertEqual(len(result['unmatched_decisions'][arm]),2)
            self.assertTrue(result['secondary_summaries_nongating'][arm]['all_contexts']['nongating'])
        self.assertFalse(result['input_provenance_or_full_campaign_replay_certified_here'])
        self.assertFalse(result['unknown_cell_generalization'])
        self.assertFalse(result['independent_confirmation'])

    def test_missing_outer_record_and_duplicate_outer_key_stop(self):
        rows, _, records, _ = fixture()
        for damaged in (records[:-1], records[:-1]+[copy.deepcopy(records[0])]):
            with self.subTest(records=len(damaged)), self.assertRaises(AssertionError):
                e.collect_outer(rows,damaged)

    def test_changed_exact_fold_ID_order_is_rejected(self):
        rows, _, records, _ = fixture()
        records[0]['predictions']['row_ids'].reverse()
        records[0]['predictions']['scores'].reverse()
        with self.assertRaisesRegex(AssertionError,'target ID order'):
            e.collect_outer(rows,records)

    def test_missing_unmatched_predictions_cannot_form_an_intersection(self):
        rows, _, records, _ = fixture()
        record = next(record for record in records if any(identifier.startswith('unmatched:') for identifier in record['predictions']['row_ids']))
        p = record['predictions']
        keep = [i for i,identifier in enumerate(p['row_ids']) if not identifier.startswith('unmatched:')]
        p['row_ids'] = [p['row_ids'][i] for i in keep]
        p['scores'] = [p['scores'][i] for i in keep]
        p['canonical_shape'][0] = len(keep)
        with self.assertRaises(AssertionError):
            e.collect_outer(rows,records)

    def test_wrong_arm_fold_and_canonical_shape_are_rejected(self):
        for field,value in (('arm','new_arm'),('outer_fold',True)):
            rows, _, records, _ = fixture()
            records[0][field] = value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                e.collect_outer(rows,records)
        rows, _, records, _ = fixture()
        records[0]['predictions']['canonical_shape'][1] = 101
        with self.assertRaises(AssertionError):
            e.collect_outer(rows,records)

    def test_nonfinite_integer_and_boolean_scores_are_rejected(self):
        for value in (float('nan'),float('inf'),0,True):
            rows, _, records, _ = fixture()
            records[0]['predictions']['scores'][0] = value
            with self.subTest(value=value), self.assertRaises(AssertionError):
                e.collect_outer(rows,records)

    def test_full_effect_roster_and_finite_values_required(self):
        for mutation in ('missing','extra','nan'):
            rows,effects,records,counts = fixture()
            if mutation == 'missing':
                effects.pop(next(iter(effects)))
            elif mutation == 'extra':
                effects['not_an_original_id'] = 1.
            else:
                effects[next(iter(effects))] = float('nan')
            with invented_counts(counts), patch.object(e.gate,'native_shared_bootstrap') as boot:
                with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                    e.evaluate(None,rows,effects,records,probe=probe,environment=ENV)
                boot.assert_not_called()

    def test_exact_score_ties_and_sub_tolerance_difference_keep_original_choices(self):
        rows,effects,records,_ = fixture()
        for record in records:
            record['predictions']['scores'] = [0.]*len(record['predictions']['scores'])
        scores,_ = e.collect_outer(rows,records)
        tied = e.selection.decisions(rows,scores['pooled'],effects)
        context = rows[0]['parent_context_id']
        self.assertTrue(all(row['selected_id'].endswith(':0') for row in tied if row['parent_context_id'] == context))
        record = records[0]
        target = record['predictions']['row_ids']
        record['predictions']['scores'][target.index(rows[1]['intervention_id'])] = 1e-12
        scores,_ = e.collect_outer(rows,records)
        untied = e.selection.decisions(rows,scores['pooled'],effects)
        self.assertEqual(next(row['selected_id'] for row in untied if row['parent_context_id'] == context and row['direction'] == 1),rows[1]['intervention_id'])

    def test_nongating_missing_secondary_cell_is_explicit_not_zero_filled(self):
        rows,effects,records,_ = fixture()
        scores,_ = e.collect_outer(rows,records)
        decisions = e.selection.decisions(rows,scores['pooled'],effects)
        unmatched = [row for row in decisions if row['parent_context_id'] == 'unmatched']
        result = e.secondary_summary(unmatched,'invented_unmatched')
        self.assertTrue(result['nongating'])
        self.assertIsNone(result['per_cell'][e.CELLS[1]]['regret'])
        self.assertIsNone(result['macro']['regret'])

    def test_startup_resource_gate_precedes_any_input_iteration(self):
        class NoIteration:
            def __iter__(self):
                raise RuntimeError('must not iterate')
        with self.assertRaisesRegex(AssertionError,'three-GiB'):
            e.evaluate(None,NoIteration(),{},[],probe=lambda:{'physical_available':3*2**30-1,'disk_available':2**30},environment=ENV)

    def test_fresh_bootstrap_resource_gate_precedes_bootstrap(self):
        rows,effects,records,counts = fixture()
        snapshots = iter([probe(),{'physical_available':3*2**30-1,'disk_available':2**30}])
        with invented_counts(counts),patch.object(e.gate,'native_shared_bootstrap') as boot:
            with self.assertRaisesRegex(AssertionError,'three-GiB'):
                e.evaluate(None,rows,effects,records,probe=lambda:next(snapshots),environment=ENV)
            boot.assert_not_called()

    def test_final_resource_failure_cannot_return_go(self):
        rows,effects,records,counts = fixture()
        snapshots = iter([probe(),probe(),{'physical_available':3*2**30,'disk_available':2**30-1}])
        with invented_counts(counts),patch.object(e.gate,'native_shared_bootstrap',side_effect=bootstrap_for(rows)) as boot:
            with self.assertRaisesRegex(AssertionError,'one-GiB'):
                e.evaluate('invented-bootstrap-sentinel',rows,effects,records,probe=lambda:next(snapshots),environment=ENV)
            self.assertEqual(boot.call_count,1)

    def test_actual_entrypoint_does_not_admit_small_fixture_as_project(self):
        rows,effects,records,_ = fixture()
        with patch.object(e.gate,'native_shared_bootstrap') as boot:
            with self.assertRaises(AssertionError):
                e.evaluate(None,rows,effects,records,probe=probe,environment=ENV)
            boot.assert_not_called()

    def test_bootstrap_component_roster_cannot_change(self):
        rows,effects,records,counts = fixture()
        def bad_bootstrap(np,comparisons):
            result = bootstrap_for(rows)(np,comparisons)
            result['components'] = result['components'][:-1]
            return result
        with invented_counts(counts),patch.object(e.gate,'native_shared_bootstrap',side_effect=bad_bootstrap):
            with self.assertRaises(AssertionError):
                e.evaluate('invented-bootstrap-sentinel',rows,effects,records,probe=probe,environment=ENV)


def run():
    forbidden = ('numpy','pandas','scipy','sklearn','torch','openvino')
    def clear():
        return not any(name == prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in forbidden)
    assert clear()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clear()
    sources = sorted((ROOT/'src'/NS).glob('*.py'))
    for path in sources:
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    receipt = {'status':'PASS_INVENTED_SUPPLIED_OUTER_EVALUATION_NOT_PROJECT_ADMISSION',
               'tests':result.testsRun,'UTC':datetime.now(timezone.utc).isoformat(),
               'sources':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
               'project_payload_reads':0,'scientific_imports':False,'native_bootstrap_run':False,
               'actual_optimizer_calls':0,'small_counts_used_only_in_invented_tests':True,
               'actual_input_provenance_or_project_evaluation_complete':False}
    with (ROOT/'results'/NS/'synthetic_tests_receipt.json').open('xb') as stream:
        stream.write((json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())


if __name__ == '__main__':
    run()
