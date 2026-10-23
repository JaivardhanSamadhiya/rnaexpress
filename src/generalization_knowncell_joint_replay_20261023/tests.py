"""Invented array doubles; deliberately no scientific imports or refits."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
from . import arithmetic as r
from src.generalization_knowncell_joint_engine_20261023.tests import tiny_pool, ENV, probe
from src.generalization_knowncell_joint_numeric_20261022.fake_array import Array, FakeNP, expit
from src.generalization_knowncell_joint_numeric_20261022.tests import OptimizerSpy
from src.generalization_knowncell_joint_numeric_20261022 import numeric

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_knowncell_joint_replay_20261023'


def fixture(arm):
    _, _, pool = tiny_pool()
    one = [.2]+[0.]*101
    answers = [one, [-.3]+[0.]*101] if arm == 'independent' else [one+([-.1]+[0.]*101 if arm == 'joint_shrink10' else [])]
    model = numeric.fit_prepared(FakeNP, OptimizerSpy(answers), expit, pool['prepared'], arm, r.CONFIGS[1])
    task = {'arm':arm, 'optimizer_units':2 if arm == 'independent' else 1}
    scores = numeric.canonical_scores(FakeNP, model, pool['validation_features'],
                                      [row['cell_type'] for row in pool['validation_metadata']]).tolist()
    prediction = {'row_ids':pool['binding']['validation_ids'], 'scores':scores,
                  'canonical_shape':[len(scores),102], 'canonical_order':'C',
                  'canonical_dtype':'float64', 'canonical_scorer':model['canonical_scorer']}
    return pool, task, model, prediction


class Cases(unittest.TestCase):
    def setUp(self):
        self.patcher = patch.object(Array, 'tobytes', lambda value,order='C':struct.pack('<'+'d'*len(value.flat()), *value.flat()), create=True)
        self.patcher.start()
    def tearDown(self):
        self.patcher.stop()

    def test_all_three_arms_match_independent_scaling_objective_gradient_and_scores(self):
        for arm in ('pooled', 'independent', 'joint_shrink10'):
            pool, task, model, predictions = fixture(arm)
            result = r.replay_checkpoint(FakeNP, pool, task, model, predictions, probe=probe, environment=ENV)
            self.assertTrue(result['exact_canonical_scores_equal'])
            self.assertEqual(result['new_optimizer_calls'], 0)
            self.assertLess(result['maximum_objective_difference'], 1e-14)

    def test_sub_tolerance_canonical_change_is_still_rejected(self):
        pool, task, model, predictions = fixture('pooled')
        predictions['scores'][0] += 1e-12
        with self.assertRaisesRegex(AssertionError, 'Exact canonical'):
            r.replay_checkpoint(FakeNP, pool, task, model, predictions, probe=probe, environment=ENV)

    def test_wrong_source_weights_cannot_pass_on_matching_scores(self):
        pool, task, model, predictions = fixture('independent')
        pool['prepared']['weights'].data[0] += .01
        with self.assertRaises(AssertionError):
            r.replay_checkpoint(FakeNP, pool, task, model, predictions, probe=probe, environment=ENV)

    def test_changed_source_effect_order_is_rejected(self):
        pool, task, model, predictions = fixture('joint_shrink10')
        pool['effects'][0],pool['effects'][1] = pool['effects'][1],pool['effects'][0]
        with self.assertRaises(AssertionError):
            r.replay_checkpoint(FakeNP, pool, task, model, predictions, probe=probe, environment=ENV)

    def test_saved_gradient_corruption_is_rejected(self):
        pool, task, model, predictions = fixture('pooled')
        model['optimizer_summaries']['pooled']['maximum_gradient_abs'] += .001
        with self.assertRaisesRegex(AssertionError, 'arithmetic difference'):
            r.replay_checkpoint(FakeNP, pool, task, model, predictions, probe=probe, environment=ENV)

    def test_full_shape_both_head_replay(self):
        pool, task, model, predictions = fixture('independent')
        shapes = []
        original = Array.__matmul__
        def observed(left, right):
            shapes.append(left.shape)
            return original(left, right)
        with patch.object(Array, '__matmul__', observed):
            r.independent_canonical(FakeNP, model, pool['validation_features'],
                                    [row['cell_type'] for row in pool['validation_metadata']])
        self.assertEqual(shapes, [(4,102), (4,102)])

    def test_resource_floor_fails_before_array_use(self):
        pool, task, model, predictions = fixture('pooled')
        with self.assertRaisesRegex(AssertionError, 'three-GiB'):
            r.replay_checkpoint(None, pool, task, model, predictions,
                                probe=lambda:{'physical_available':3*2**30-1, 'disk_available':2**30}, environment=ENV)


def run():
    forbidden = ('numpy', 'pandas', 'scipy', 'sklearn', 'torch')
    assert not any(name in sys.modules for name in forbidden)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and not any(name in sys.modules for name in forbidden)
    sources = sorted((ROOT/'src'/NS).glob('*.py'))
    payload = {'status':'PASS_INVENTED_DEFERRED_CHECKPOINT_ARITHMETIC_REPLAY', 'tests':result.testsRun,
               'UTC':datetime.now(timezone.utc).isoformat(),
               'sources':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
               'scientific_imports':False, 'actual_optimizer_calls':0, 'project_payload_reads':0,
               'full_campaign_replay_or_gate_complete':False}
    with (ROOT/'results'/NS/'synthetic_tests_receipt.json').open('xb') as handle:
        handle.write((json.dumps(payload, sort_keys=True, indent=2, allow_nan=False)+'\n').encode())


if __name__ == '__main__':
    run()
