"""Invented selector provenance tests; no arrays, scientific imports or checkpoints."""
from copy import deepcopy
from datetime import datetime, timezone
import ast
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import Mock, patch
from . import adapter as original
from . import adapter_v2 as revised
from src.generalization_knowncell_joint_implementation_20261022.tests import rows_fixture

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results' / original.NS
ENV = {key: '1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}


def probe(): return {'physical_available':3*2**30, 'disk_available':2**30}


class InventedCampaign:
    def __init__(self, document):
        self._immutable = deepcopy(document)
        self.plan = type('InventedPlan', (), {
            'document': lambda _self: deepcopy(self._immutable),
            'pool': lambda _self, task: deepcopy(self._immutable['source_pools']['outer0_final']),
        })()
        self.tasks = {'outer': {'arm':'pooled', 'outer_fold':0, 'inner_fold':None, 'phase':'outer'}}
        self.check_saved = Mock(side_effect=AssertionError('No checkpoint may be read before immutable input checks'))
        self.paths = Mock(side_effect=AssertionError('No checkpoint path may be requested before immutable input checks'))


def fixture():
    metadata = rows_fixture()
    train, _ = original.reference.union_split(metadata, 0)
    rows = [metadata[i] for i in train]
    effects = [-1. if row['intervention_id'].endswith(':0') else 1. for row in rows]
    binding = {'training_ids':[row['intervention_id'] for row in rows],
               'training_ids_sha256':original.reference.ids_sha(rows),
               'training_metadata_sha256':original.reference.metadata_sha(rows),
               'training_effects_json_sha256':original.lifecycle.hash_value(effects),
               'training_rows':len(rows)}
    # Preserve the ORIGINAL alias relationship. Replacing pool['binding'] later
    # does not change document['source_pools']; this is the reported V1 gap.
    document = {'source_pools':{'outer0_final':binding}}
    prepared = revised.PreparedPools(metadata, {'outer0_final':{'rows':rows, 'effects':effects, 'binding':binding}}, document)
    return prepared, InventedCampaign(document), prepared.pools['outer0_final']


class Tests(unittest.TestCase):
    def invoke(self, prepared, campaign, delegate):
        with patch.object(original, 'Campaign', InventedCampaign), patch.object(original, 'select_outer', delegate):
            return revised.select_outer(prepared, campaign, 'pooled', 0, probe=probe, environment=ENV)

    def assert_unread(self, campaign, delegate):
        campaign.check_saved.assert_not_called(); campaign.paths.assert_not_called(); delegate.assert_not_called()

    def test_original_numerical_exports_are_unchanged_objects(self):
        self.assertIs(revised.prepare_pools, original.prepare_pools)
        self.assertIs(revised.make_fit_callback, original.make_fit_callback)
        self.assertIs(revised.PreparedPools, original.PreparedPools)

    def test_valid_immutable_source_delegates_once_without_substitution(self):
        prepared, campaign, _ = fixture(); expected = {'invented_receipt':True}; delegate = Mock(return_value=expected)
        result = self.invoke(prepared, campaign, delegate)
        self.assertIs(result, expected)
        delegate.assert_called_once_with(prepared, campaign, 'pooled', 0, probe=probe, environment=ENV)
        campaign.check_saved.assert_not_called()

    def test_replacement_binding_and_changed_truth_cannot_bypass_prefit_equality(self):
        prepared, campaign, pool = fixture(); pool['effects'][0] *= -1.
        replacement = dict(pool['binding']); replacement['training_effects_json_sha256'] = original.lifecycle.hash_value(pool['effects'])
        pool['binding'] = replacement
        # These original selector checks WOULD all pass; only the immutable
        # bound-pool comparison closes this particular replacement bypass.
        self.assertEqual(prepared.prefit_document, campaign.plan.document())
        self.assertEqual(original.reference.metadata_sha(pool['rows']), replacement['training_metadata_sha256'])
        self.assertEqual(original.lifecycle.hash_value(pool['effects']), replacement['training_effects_json_sha256'])
        delegate = Mock()
        with self.assertRaisesRegex(AssertionError, 'immutable bound pool'): self.invoke(prepared, campaign, delegate)
        self.assert_unread(campaign, delegate)

    def test_changed_truth_without_rebinding_fails_before_checkpoint_read(self):
        prepared, campaign, pool = fixture(); pool['effects'][0] *= -1.; delegate = Mock()
        with self.assertRaisesRegex(AssertionError, 'Source effects'): self.invoke(prepared, campaign, delegate)
        self.assert_unread(campaign, delegate)

    def test_changed_ID_order_fails_before_checkpoint_read(self):
        prepared, campaign, pool = fixture(); pool['rows'] = list(reversed(pool['rows'])); delegate = Mock()
        with self.assertRaisesRegex(AssertionError, 'Source ID order'): self.invoke(prepared, campaign, delegate)
        self.assert_unread(campaign, delegate)

    def test_changed_metadata_same_IDs_fails_before_checkpoint_read(self):
        prepared, campaign, pool = fixture(); pool['rows'][0]['mutant_sequence'] = 'DIFFERENT_INVENTED_MUTANT'; delegate = Mock()
        with self.assertRaisesRegex(AssertionError, 'Source metadata'): self.invoke(prepared, campaign, delegate)
        self.assert_unread(campaign, delegate)

    def test_missing_effect_or_changed_prefit_stops_before_checkpoint_read(self):
        prepared, campaign, pool = fixture(); pool['effects'].pop(); delegate = Mock()
        with self.assertRaisesRegex(AssertionError, 'Incomplete source'): self.invoke(prepared, campaign, delegate)
        self.assert_unread(campaign, delegate)
        prepared, campaign, pool = fixture(); pool['binding']['training_rows'] += 1; delegate = Mock()
        with self.assertRaisesRegex(AssertionError, 'Prepared document'): self.invoke(prepared, campaign, delegate)
        self.assert_unread(campaign, delegate)

    def test_original_floor_still_applies_before_selection_checks(self):
        prepared, campaign, _ = fixture(); delegate = Mock()
        with patch.object(original,'Campaign',InventedCampaign), patch.object(original,'select_outer',delegate):
            with self.assertRaises(AssertionError):
                revised.select_outer(prepared,campaign,'pooled',0,
                    probe=lambda:{'physical_available':3*2**30-1,'disk_available':2**30},environment=ENV)
        self.assert_unread(campaign, delegate)


def run():
    forbidden = ('numpy','pandas','scipy','torch','openvino','sklearn')
    assert not any(name in sys.modules for name in forbidden)
    started = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    assert result.wasSuccessful() and not any(name in sys.modules for name in forbidden)
    paths = sorted((ROOT/'src'/original.NS).glob('*.py'))
    for path in paths: ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    receipt = {'status':'PASS_INVENTED_IMMUTABLE_PLAN_SELECTOR_V2_NOT_PROJECT_ADMISSION',
               'tests':result.testsRun, 'elapsed_seconds':time.monotonic()-started,
               'generated_utc':datetime.now(timezone.utc).isoformat(),
               'scientific_imports':False, 'native_optimizer_calls':0, 'models_fitted':0,
               'project_metadata_reads':0, 'project_feature_reads':0, 'project_outcome_reads':0,
               'actual_checkpoint_reads':0, 'replacement_binding_cannot_substitute_source_truths':True,
               'source_ID_order_checked_before_checkpoint_reads':True,
               'source_files':{p.relative_to(ROOT).as_posix():original.lifecycle.digest(p.read_bytes()) for p in paths}}
    path = OUT/'synthetic_tests_receipt_v2.json'
    with path.open('xb') as handle: handle.write(original.lifecycle.canonical_bytes(receipt))
    print('IMMUTABLE_SELECTOR_V2_STDLIB_PASS', result.testsRun, original.lifecycle.digest(path.read_bytes()), flush=True)


if __name__ == '__main__': run()
