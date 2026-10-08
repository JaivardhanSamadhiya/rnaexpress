"""Invented frames/coefficients/trees only; no estimator fitting or project outputs."""
import unittest
from unittest.mock import patch
from .common import np, pd, TRACKS, FEATURE_TRACKS, INFORMED, TASKS, FOLDS, META, rowhash, validate_source_reference
from .splits import masks, exact_menu_pairs
from .predict import independent_hgb, independent_ridge, canonical_scores, score_match
from .evaluate import select_source, source_model
from .verify import exact_decision_roster
from .gate import baseline_checks, information_checks
from .canonical_paired_contrast import shared_matrix, common_choices
from src.generalization_nonlinear_crosscell_20261007.routes import module
from src.generalization_knowncell_20261007.gate import compare
from src.generalization_rbp_20261007.canonical_inner_replay import decision_table, decisions_equal

def toy():
    parents, variants = ['AAAAC', 'CCCCA', 'GGGGA'], ['AAAAT', 'CCCCT', 'GGGGT']
    rows = []
    for cell in ('CAD', 'Neuro-2a'):
        for fold in FOLDS:
            for allele in (0, 1):
                rows.append({'intervention_id': cell + str(fold) + str(allele), 'dataset': 'mikl_gse173098',
                    'cell_type': cell, 'endpoint_class': 'projection', 'held_parent_fold': fold,
                    'biological_component': 'gene' + str(fold), 'gene_transcript': 'G' + str(fold),
                    'parent_context_id': cell + '_p' + str(fold), 'parent_sequence': parents[fold],
                    'mutant_sequence': variants[fold] + str(allele), 'measured_delta': float(allele) - .5})
    return pd.DataFrame(rows)

def tree_model():
    tree = {'value': [0., -1., 2.], 'feature_idx': [0, 0, 0], 'num_threshold': [.5, 0., 0.],
            'missing_go_to_left': [0, 0, 0], 'left': [1, 0, 0], 'right': [2, 0, 0], 'is_leaf': [0, 1, 1]}
    return {'kind': 'numeric_hgb_json_v1', 'width': 2, 'baseline': .25, 'trees': [tree, tree], 'sklearn_version': '1.5.2', 'iterations': 2}

def ridge_model():
    return {'kind': 'weighted_pointwise_ridge_json_v1', 'width': 2, 'mean': [1., 3.], 'scale': [2., 1.],
            'raw_rms': [2., 0.], 'supported': [True, False], 'beta': [2., 0.], 'intercept': .25,
            'alpha': .05, 'support_cutoff': 1e-12}

class NonlinearKnownCellTests(unittest.TestCase):
    def test_fourteen_tracks_only_three_informed(self):
        self.assertEqual(len(TRACKS), 14); self.assertEqual(len(INFORMED), 3)
        self.assertEqual(set(TRACKS), {learner + '/' + feature for learner in ('hgb', 'ridge') for feature in FEATURE_TRACKS})
        self.assertTrue(all(name.startswith('hgb/') for name in INFORMED))

    def test_original_masks_same_cell_held_gene_menus(self):
        frame = toy()
        for task, (cell, _) in TASKS.items():
            seen = []
            for fold in FOLDS:
                train, test, opposite = masks(frame, task, fold)
                self.assertEqual(set(frame.loc[train].cell_type), {cell}); self.assertEqual(set(frame.loc[test].cell_type), {cell})
                self.assertEqual(int(test.sum()), 2); self.assertEqual(int(opposite.sum()), 2)
                seen.extend(frame.loc[test].intervention_id)
            self.assertEqual(len(seen), len(set(seen))); self.assertEqual(set(seen), set(frame[frame.cell_type.eq(cell)].intervention_id))

    def test_same_cell_allele_overlap_blocks_reuse(self):
        frame = toy(); frame.loc[frame.intervention_id.eq('CAD00'), 'mutant_sequence'] = 'CCCCA'
        with self.assertRaisesRegex(AssertionError, 'Same-cell allele overlap'):
            masks(frame, 'CAD_known', 0)

    def test_exact_full_menus_no_intersection_trim(self):
        frame = toy(); pairs, excluded = exact_menu_pairs(frame)
        self.assertEqual(len(pairs), 3); self.assertFalse(excluded)
        frame.loc[frame.intervention_id.eq('Neuro-2a01'), 'mutant_sequence'] = 'OTHER'
        pairs, excluded = exact_menu_pairs(frame)
        self.assertEqual(len(pairs), 2); self.assertEqual(sum(value['rows'] for value in excluded), 4)

    def test_hgb_independent_partition_matches_native_threshold(self):
        model = tree_model(); x = np.array([[.5, 4.], [.50000000001, 9.], [-1., 0.]])
        native = module('hgb/simple').predict_model(model, x)
        np.testing.assert_array_equal(native, [-1.75, 4.25, -1.75])
        np.testing.assert_array_equal(independent_hgb(model, x), native)
        score, bound = canonical_scores('hgb/simple', model, x, module('hgb/simple').predict_model)
        self.assertEqual(bound, 0.); np.testing.assert_array_equal(score, native)

    def test_ridge_independent_coefficients_support(self):
        model = ridge_model(); x = np.array([[1., 1e5], [3., -1e5]])
        np.testing.assert_allclose(independent_ridge(model, x), [.25, 2.25], atol=0, rtol=0)
        score, bound = canonical_scores('ridge/simple', model, x, module('ridge/simple').predict_model)
        self.assertEqual(bound, 0.); np.testing.assert_array_equal(score, [.25, 2.25])

    def test_bad_tree_and_nonfinite_inputs_rejected(self):
        model = tree_model(); model['trees'][0]['left'][0] = 0
        with self.assertRaises(AssertionError): independent_hgb(model, np.zeros((2, 2)))
        with self.assertRaises(AssertionError): independent_ridge(ridge_model(), np.array([[np.nan, 0.]]))

    def test_canonical_exact_ties_not_alternate_arithmetic(self):
        model = ridge_model(); x = np.array([[1., 0.], [1. + 1e-12, 0.]])
        canonical, error = canonical_scores('ridge/simple', model, x, lambda model, values: np.full(len(values), .25))
        self.assertLess(error, 1e-9)
        frame = toy().query('cell_type == "CAD" and held_parent_fold == 0').reset_index(drop=True)
        result = decision_table(frame, canonical)
        self.assertEqual(set(result.selected_id), {frame.intervention_id.iloc[0]})

    def test_saved_score_changed_is_rejected(self):
        with self.assertRaises(AssertionError): score_match(np.array([1.]), np.array([1.01]))

    def test_fixed_source_configuration_grid_and_target_invariance(self):
        from . import evaluate
        frame = toy(); train, test, opposite = masks(frame, 'CAD_known', 0); configs = module('hgb/simple').CONFIGS
        values = [.4, .4 - 5e-13, .6]
        roster = [{'task': source, 'fold': fold} for _, source in TASKS.values() for fold in FOLDS]
        selected = next(row for row in roster if row == {'task': 'CAD_to_N2A', 'fold': 0})
        selected.update({'all_source_oof_scores': dict(zip([c['id'] for c in configs], values)), 'selected_configuration': configs[0],
            'training_ids_sha256': rowhash(frame.loc[train]), 'test_ids_sha256': rowhash(frame.loc[opposite]),
            'training_components': sorted(frame.loc[train].biological_component.unique()), 'training_cell': 'CAD', 'test_rows': int(opposite.sum())})
        rows = pd.DataFrame([{'task': 'CAD_to_N2A', 'outer_fold': 0, 'configuration': c['id'], 'combined_source_oof_macro_regret': v} for c, v in zip(configs, values)])
        changed = frame.copy(); changed.loc[test, 'measured_delta'] = 1000.
        for candidate in (frame, changed):
            with patch.object(evaluate, 'readj', return_value=roster), patch.object(evaluate.pd, 'read_csv', return_value=rows), \
                 patch.object(evaluate, 'load_checkpoint', return_value={'synthetic': True}), patch.object(evaluate, 'check_model') as checker:
                _, config, _, _, _ = source_model('hgb/simple', 'CAD_known', 0, candidate, np.zeros((len(frame), 102)))
                self.assertEqual(config, configs[0]); self.assertEqual(len(checker.call_args.args), 5)
        self.assertEqual(select_source(configs, [.6, .5, .4]), configs[2])

    def test_roster_rejects_model_dataset_extra_missing(self):
        frame = toy(); rows = []
        for task, (cell, _) in TASKS.items():
            for fold, context in frame[frame.cell_type.eq(cell)][['held_parent_fold', 'parent_context_id']].drop_duplicates().itertuples(index=False, name=None):
                rows.extend({'model': 'hgb/simple', 'dataset': 'mikl_gse173098', 'task': task, 'gene_fold': fold, 'parent_context_id': context, 'direction': d} for d in (-1, 1))
        saved = pd.DataFrame(rows); exact_decision_roster(saved, frame, 'hgb/simple')
        for value in (saved.assign(model='bad'), saved.assign(dataset='bad'), saved.iloc[:-1], pd.concat((saved, saved.iloc[:1]))):
            with self.assertRaises(AssertionError): exact_decision_roster(value, frame, 'hgb/simple')

    def test_gate_baseline_and_information_thresholds_are_frozen(self):
        value = {'mean_gain': .02, 'per_known_cell_gain': {'CAD_known': .02, 'N2A_known': .02}, 'gain_ci': [.001, .03],
            'macro_wrong_direction_harm': 0., 'wrong_direction_harm': {'CAD_known': 0., 'N2A_known': 0.}, 'remaining_gain': .02}
        self.assertTrue(all(baseline_checks(value, 'fixed').values())); self.assertTrue(all(information_checks(value, 'fixed').values()))
        value['remaining_gain'] = 0.
        self.assertFalse(all(baseline_checks(value, 'fixed').values())); self.assertFalse(all(information_checks(value, 'fixed').values()))

    def test_shared_gene_bootstrap_and_unequal_fold_weight(self):
        from src.generalization_crosscell_20261007.bootstrap import shared_bootstrap
        a = pd.Series([1., -1.], index=['g1', 'g2'])
        np.testing.assert_allclose(shared_bootstrap({'CAD_known': a, 'N2A_known': -a}, 64, 4), 0., atol=1e-15, rtol=0)
        rows = []
        for task in TASKS:
            for component, fold, gain in [('a', 0, .1), ('b', 1, .02), ('c', 2, .04), ('d', 2, .04)]:
                rows.append({'task': task, 'biological_component': component, 'gene_fold': fold, 'regret': .5 - gain, 'wrong_direction': 0.})
        candidate = pd.DataFrame(rows); control = candidate.copy(); control['regret'] = .5
        value = compare(candidate, control); self.assertEqual(value['removed_best_gene_fold'], 0)
        self.assertAlmostEqual(value['remaining_gain'], (.02 + .04 + .04) / 3)

    def test_metadata_loader_called_without_outcomes(self):
        from . import common
        frame = toy()
        with patch('src.generalization_knowncell_20261007.common.load', return_value=frame) as admitted, \
             patch.object(common.pd, 'read_csv', return_value=frame[META]):
            value = common.load(False); self.assertEqual(len(value), len(frame)); admitted.assert_called_once_with(False)

    def test_paired_state_same_allele_bytes_and_one_choice(self):
        frame = toy(); pairs, _ = exact_menu_pairs(frame)
        matrix = np.zeros((len(frame), 2)); matrix[:, 0] = frame.held_parent_fold.to_numpy()
        rows, shared = shared_matrix(frame, matrix, pd.DataFrame(pairs), 0)
        self.assertEqual(len(shared), 2)
        result = common_choices(rows, np.ones(len(rows)), 'CAD_known')
        self.assertEqual(result.selected_mutant_sequence.nunique(), 1)
        changed = matrix.copy(); changed[frame.intervention_id.eq('Neuro-2a00'), 0] += 1.
        with self.assertRaisesRegex(AssertionError, 'feature-byte inequality'):
            shared_matrix(frame, changed, pd.DataFrame(pairs), 0)

    def test_existing_windows_prefit_separator_binding(self):
        reference = {'status': 'FROZEN_PREFIT', 'files': {'artifacts\\f\\base.npz': 'fixed'}}
        validate_source_reference(reference, {'artifacts/f/base.npz': 'fixed'})
        with self.assertRaises(AssertionError): validate_source_reference(reference, {'artifacts/f/base.npz': 'changed'})
        reference['files']['artifacts/f/base.npz'] = 'fixed'
        with self.assertRaises(AssertionError): validate_source_reference(reference, {'artifacts/f/base.npz': 'fixed'})

if __name__ == '__main__':
    unittest.main()
