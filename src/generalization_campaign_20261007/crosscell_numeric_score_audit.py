"""Additive current-byte crosscell score audit; never fit or revise old files.

Only original admitted mean labels/identities and frozen crosscell feature
arrays/checkpoints are read. Full-validation canonical prediction anchors exact
ties; independent coefficient arithmetic uses the pinned shared audit helper.
"""
from src.research_20260921 import common as _runtime_bootstrap
from src.generalization_crosscell_20261007.common import (
    ROOT, np, pd, sha256, readj, clean, CORE, META, TRACKS, WIDTHS, TASKS, FOLDS,
    OUT as ORIGINAL_OUT, ART as ORIGINAL_ART,
)
from src.generalization_crosscell_20261007.routes import module
from src.generalization_crosscell_20261007.splits import outer_masks, inner_masks
from src.generalization_crosscell_20261007.verify import check_model
from src.generalization_rbp_20261007.canonical_inner_replay import canonical_scores, decisions_equal
from pathlib import Path
import argparse, hashlib, json, os, subprocess, unittest
from unittest.mock import patch

OUT = ROOT / 'results/generalization_campaign_20261007'
SCORE_ATOL, REGRET_ATOL = 1e-9, 1e-12


def immutable_json(path, obj):
    path = Path(path).resolve(); assert path.is_relative_to(OUT.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(clean(obj), indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    if path.exists(): assert path.read_bytes() == raw, 'Preserve earlier audit ' + str(path)
    else:
        with path.open('xb') as stream: stream.write(raw)


def ids(frame):
    return hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()


def parsed_values_hash(values):
    return hashlib.sha256(np.ascontiguousarray(values, dtype='<f8').tobytes()).hexdigest()


def admitted_frame():
    """Default parser/row order, metadata first then ONLY Mikl mean labels."""
    foundation = ROOT / 'results/generalization_20261007/prefit_manifest.json'
    admission = ROOT / 'results/probabilistic_ranking_20260928/prefit_manifest.json'
    assert readj(foundation)['files'][admission.relative_to(ROOT).as_posix()] == sha256(admission)
    assert readj(admission)['files'][CORE.relative_to(ROOT).as_posix()] == sha256(CORE)
    original = pd.read_csv(CORE, usecols=META, low_memory=False)
    assert len(original) == 26258 and original.intervention_id.is_unique
    original['original_core_row'] = np.arange(len(original))
    frame = original[original.dataset.eq('mikl_gse173098')].reset_index(drop=True)
    assert len(frame) == 13781 and frame.biological_component.nunique() == 187
    assert set(frame.endpoint_class) == {'projection'} and set(frame.cell_type) == {'CAD', 'Neuro-2a'}
    permitted = set(frame.original_core_row.astype(int) + 1)
    truth = pd.read_csv(CORE, usecols=['intervention_id', 'measured_delta'], low_memory=False,
        skiprows=lambda row: row > 0 and row not in permitted)
    assert list(truth.intervention_id) == list(frame.intervention_id)
    frame['measured_delta'] = truth.measured_delta.to_numpy(float)
    assert np.isfinite(frame.measured_delta).all()
    original_rows = pd.read_csv(ORIGINAL_OUT / 'row_index.csv.gz', usecols=META, low_memory=False)
    pd.testing.assert_frame_equal(frame[META], original_rows[META])
    return frame


def independent_choices(frame, scores):
    """Vectorized lexical extrema and original-truth arithmetic, no engine metric."""
    value = frame[['intervention_id', 'dataset', 'biological_component', 'parent_context_id', 'measured_delta']].copy()
    scores = np.asarray(scores, dtype=float)
    assert scores.shape == (len(value),) and np.isfinite(scores).all() and value.intervention_id.is_unique
    value['_score'] = scores
    grouped = value.groupby('parent_context_id')
    assert grouped.dataset.nunique().eq(1).all() and grouped.biological_component.nunique().eq(1).all()
    limits = grouped.measured_delta.agg(['min', 'max', 'size'])
    assert limits['size'].ge(2).all() and (limits['max'] > limits['min']).all()
    rows = []
    for direction in (-1, 1):
        chosen = value.assign(_utility=direction * value._score).sort_values(
            ['parent_context_id', '_utility', 'intervention_id'], ascending=[True, False, True], kind='stable').drop_duplicates('parent_context_id')
        bounds = limits.loc[chosen.parent_context_id]
        best = bounds['max'].to_numpy() if direction == 1 else -bounds['min'].to_numpy()
        effect = direction * chosen.measured_delta.to_numpy(float)
        wrong, feasible, unavoidable = effect < -1e-12, best > 1e-12, best < -1e-12
        record = chosen[['dataset', 'biological_component', 'parent_context_id']].reset_index(drop=True)
        record['direction'] = direction; record['selected_id'] = chosen.intervention_id.to_numpy()
        record['regret'] = (best - effect) / (bounds['max'] - bounds['min']).to_numpy()
        record['wrong_direction'] = wrong.astype(float); record['avoidable_wrong'] = (wrong & feasible).astype(float)
        record['no_feasible_candidate'] = (~feasible).astype(float); record['unavoidable_wrong'] = (wrong & unavoidable).astype(float)
        record['neutral_only_alternative_wrong'] = (wrong & ~feasible & ~unavoidable).astype(float)
        rows.append(record)
    return pd.concat(rows, ignore_index=True)


def original_macro(choices):
    return float(choices.groupby(['dataset', 'biological_component']).regret.mean().groupby('dataset').mean().mean())


def source_choice(configs, values):
    assert len(configs) == 3 and len(values) == 3 and np.isfinite(values).all()
    minimum = min(values)
    return next(config for config, value in zip(configs, values) if value <= minimum + 1e-12)


def bound_actual_coefficients(model, matrix, rows, predictor):
    # canonical_scores explicitly loads actual checkpoint mean/scale/beta,
    # computes coefficients=beta/scale, then blocked SUM((X-mean)*coefficients).
    # It independently bounds those column sums against ONE original full
    # validation float64 predictor call. We never turn the bound into tie bands.
    canonical, error = canonical_scores(model, matrix, rows, predictor, batch_rows=1024)
    assert error <= SCORE_ATOL
    coefficient_digest = hashlib.sha256(b''.join(np.asarray(model[key], dtype='<f8').tobytes()
        for key in ('mean', 'scale', 'beta'))).hexdigest()
    return canonical, error, coefficient_digest


def disjoint(training, target):
    assert not set(training.biological_component) & set(target.biological_component)
    assert not set(training.gene_transcript.str.strip().str.upper()) & set(target.gene_transcript.str.strip().str.upper())
    assert not (set(training.parent_sequence) | set(training.mutant_sequence)) & (set(target.parent_sequence) | set(target.mutant_sequence))


def source_paths():
    paths = [Path(__file__), CORE, ORIGINAL_OUT / 'prefit_manifest.json', ORIGINAL_OUT / 'row_index.csv.gz',
        ORIGINAL_OUT / 'verification_receipt.json', ROOT / 'results/generalization_20261007/prefit_manifest.json',
        ROOT / 'results/probabilistic_ranking_20260928/prefit_manifest.json', OUT / 'crosscell_numeric_synthetic_01.json']
    for name in ['generalization_crosscell_20261007/common.py', 'generalization_crosscell_20261007/engine.py',
                 'generalization_crosscell_20261007/routes.py', 'generalization_crosscell_20261007/splits.py',
                 'generalization_crosscell_20261007/verify.py', 'generalization_rbp_20261007/canonical_inner_replay.py',
                 'generalization_rbp_20261007/inner_replay.py', 'generalization_20261007/route_scaling.py',
                 'cross_assay_20260927/models.py', 'research_20260921/common.py']:
        paths.append(ROOT / 'src' / name)
    for track in TRACKS:
        paths.append(ORIGINAL_ART / (track + '_model_features.npz'))
        paths.extend(path for path in (ORIGINAL_OUT / track).rglob('*') if path.is_file())
    paths += [Path(np.__file__), Path(pd.__file__)]
    return sorted(set(paths))


def run():
    for name in ('PYTHONDONTWRITEBYTECODE', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS'): assert os.environ.get(name) == '1'
    destination = OUT / 'crosscell_numeric_score_audit_01.json'; assert not destination.exists()
    tests = readj(OUT / 'crosscell_numeric_synthetic_01.json')
    assert tests['status'] == 'PASS' and tests['audit_source_sha256'] == sha256(__file__)
    from src.generalization_crosscell_20261007.common import freeze_check
    freeze_check()  # Includes complete old preservation checks before any read.
    assert readj(ORIGINAL_OUT / 'verification_receipt.json')['status'] == 'PASS'
    paths = source_paths(); observed = {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths}
    frame = admitted_frame(); prefit_sha = sha256(ORIGINAL_OUT / 'prefit_manifest.json')
    inner_count, outer_count, maximum, saved_maximum, choices_count = 0, 0, 0., 0., 0
    records, selections, outer_records = [], [], []
    for track in TRACKS:
        complete = readj(ORIGINAL_OUT / track / 'run_complete.json')
        assert complete['status'] == 'PASS' and complete['fit_files'] == 42 and complete['prediction_rows'] == 13781
        assert complete['prefit_manifest_sha256'] == prefit_sha
        with np.load(ORIGINAL_ART / (track + '_model_features.npz'), allow_pickle=False) as archive:
            assert archive.files == ['features']; matrix = archive['features'].astype(float)
        assert matrix.shape == (len(frame), WIDTHS[track]) and np.isfinite(matrix).all()
        predictor = module(track).predict_model; configs = module(track).CONFIGS
        folds = readj(ORIGINAL_OUT / track / 'folds.json')
        assert len(folds) == 6 and {(row['task'], row['fold']) for row in folds} == {(t, f) for t in TASKS for f in FOLDS}
        inner_saved = pd.read_csv(ORIGINAL_OUT / track / 'inner_folds.csv', float_precision='round_trip')
        selected_saved = pd.read_csv(ORIGINAL_OUT / track / 'source_selection.csv', float_precision='round_trip')
        outer_saved = pd.read_csv(ORIGINAL_OUT / track / 'predictions.csv.gz', float_precision='round_trip')
        decision_saved = pd.read_csv(ORIGINAL_OUT / track / 'decisions.csv', float_precision='round_trip')
        assert len(inner_saved) == 36 and len(selected_saved) == 18
        assert len(outer_saved) == len(frame) and outer_saved.intervention_id.is_unique and set(outer_saved.intervention_id) == set(frame.intervention_id)
        assert set(outer_saved.track) == set(decision_saved.model) == {track}
        assert not decision_saved.duplicated(['task', 'gene_fold', 'parent_context_id', 'direction']).any()
        for fold in folds:
            task, held = fold['task'], int(fold['fold']); train, test = outer_masks(frame, task, held)
            source = frame.loc[train].reset_index(drop=True); target = frame.loc[test].reset_index(drop=True)
            disjoint(source, target); source_x = matrix[train]; prefix = task + '__fold' + str(held)
            assert ids(source) == fold['training_ids_sha256'] and ids(target) == fold['test_ids_sha256']
            values = []
            for config in configs:
                oof = np.full(len(source), np.nan)
                for inner in sorted(source.held_parent_fold.unique()):
                    allowed, validation = inner_masks(source, int(inner))
                    tr, va = source.loc[allowed].reset_index(drop=True), source.loc[validation].reset_index(drop=True)
                    disjoint(tr, va); disjoint(tr, target)
                    path = ORIGINAL_OUT / track / 'fits' / (prefix + '__inner' + str(inner) + '_' + config['id'] + '.json')
                    model = readj(path); check_model(model, tr, config, track)
                    score, error, coefficients_sha = bound_actual_coefficients(model, source_x, np.flatnonzero(validation), predictor)
                    maximum = max(maximum, error); oof[validation] = score
                    independent = independent_choices(va, score); regret = original_macro(independent)
                    row = inner_saved[inner_saved.task.eq(task) & inner_saved.outer_fold.eq(held) & inner_saved.inner_fold.eq(inner) & inner_saved.configuration.eq(config['id'])]
                    assert len(row) == 1 and abs(float(row.iloc[0].regret) - regret) <= REGRET_ATOL
                    assert row.iloc[0].training_ids_sha256 == ids(tr) and int(row.iloc[0].training_rows) == len(tr) and int(row.iloc[0].validation_rows) == len(va)
                    records.append({'track': track, 'task': task, 'outer_fold': held, 'inner_fold': int(inner), 'configuration': config,
                        'checkpoint': path.relative_to(ROOT).as_posix(), 'checkpoint_sha256': sha256(path), 'actual_coefficient_triplet_sha256': coefficients_sha,
                        'training_ids_sha256': ids(tr), 'validation_ids_sha256': ids(va), 'canonical_scores_float64_sha256': parsed_values_hash(score),
                        'independent_arithmetic_max_error': error, 'canonical_original_truth_regret': regret,
                        'lexical_choices_sha256': hashlib.sha256(independent.to_csv(index=False, lineterminator='\n').encode()).hexdigest()})
                    inner_count += 1
                assert np.isfinite(oof).all()
                value = original_macro(independent_choices(source, oof)); values.append(value)
                row = selected_saved[selected_saved.task.eq(task) & selected_saved.outer_fold.eq(held) & selected_saved.configuration.eq(config['id'])]
                assert len(row) == 1 and abs(float(row.iloc[0].combined_source_oof_macro_regret) - value) <= REGRET_ATOL
                assert abs(fold['all_source_oof_scores'][config['id']] - value) <= REGRET_ATOL
            config = source_choice(configs, values); assert config == fold['selected_configuration']
            selections.append({'track': track, 'task': task, 'outer_fold': held, 'source_only_oof_values': dict(zip([c['id'] for c in configs], values)), 'selected_configuration': config})
            path = ORIGINAL_OUT / track / 'fits' / (prefix + '__outer_' + config['id'] + '.json')
            model = readj(path); check_model(model, source, config, track)
            score, error, coefficients_sha = bound_actual_coefficients(model, matrix, np.flatnonzero(test), predictor)
            maximum = max(maximum, error)
            saved = outer_saved[outer_saved.task.eq(task) & outer_saved.gene_fold.eq(held)].set_index('intervention_id').loc[target.intervention_id]
            assert set(saved.configuration) == {config['id']}
            saved_error = float(np.max(abs(score - saved.score.to_numpy(float)))); assert saved_error <= SCORE_ATOL
            saved_maximum = max(saved_maximum, saved_error)
            independent = independent_choices(target, score)
            decisions_equal(independent, decision_saved[decision_saved.task.eq(task) & decision_saved.gene_fold.eq(held)])
            outer_records.append({'track': track, 'task': task, 'outer_fold': held, 'configuration': config,
                'checkpoint': path.relative_to(ROOT).as_posix(), 'checkpoint_sha256': sha256(path), 'actual_coefficient_triplet_sha256': coefficients_sha,
                'target_ids_sha256': ids(target), 'independent_arithmetic_max_error': error, 'saved_scores_max_error': saved_error,
                'canonical_original_truth_regret': original_macro(independent), 'decisions': len(independent)})
            choices_count += len(independent); outer_count += 1
            print('Numeric inner audit', track, task, held, 'PASS', flush=True)
        assert len(list((ORIGINAL_OUT / track / 'fits').glob('*.json'))) == 42
        del matrix, source_x
    assert inner_count == 252 and outer_count == 42
    freeze_check()  # Recheck old preservation and frozen inputs at completion.
    assert all(sha256(ROOT / name) == expected for name, expected in observed.items()), 'Current observed inputs changed during replay'
    immutable_json(destination, {'status': 'PASS', 'inner_checkpoints_checked': inner_count, 'outer_checkpoints_checked': outer_count,
        'actual_models_checked': inner_count + outer_count, 'maximum_independent_arithmetic_error': maximum,
        'maximum_saved_outer_score_error': saved_maximum, 'outer_original_truth_decisions_checked': choices_count,
        'coefficient_formula': 'Actual checkpoint beta/scale; independent blocked sum((X-mean)*(beta/scale)) versus one canonical full-validation float64 predict_model call',
        'exact_tie_policy': 'Canonical full-validation scores; original lexical intervention ID, no tolerance ties',
        'source_only_selection': 'Combined two-fold source OOF predictions, equal original gene weights, fixed grid/1e-12 order ties',
        'inner_prediction_scope': 'No inner candidate arrays originally saved; current coefficient formula bounded, canonical original-truth choices/regrets and original selections reconstructed',
        'observed_input_sha256': observed, 'observed_digest_scope': 'Postfit observed bytes, not retroactive checkpoint creation-time certification',
        'prefit_manifest_sha256': prefit_sha, 'mean_effect_float64_sha256': parsed_values_hash(frame.measured_delta),
        'original_mikl_row_ids_sha256': ids(frame), 'preservation_before_and_after': True, 'numerical_threads': 1,
        'loaded_numeric_libraries': {'numpy_version': np.__version__, 'pandas_version': pd.__version__, 'numpy_init_sha256': sha256(np.__file__), 'pandas_init_sha256': sha256(pd.__file__)},
        'source_rows': 13781, 'source_components': 187, 'inner': records, 'selections': selections, 'outer': outer_records,
        'models_fit': 0, 'protected_outcomes_read': False, 'replicate_evidence_opened': False, 'historical_data_npz_loaded': False,
        'gate_or_result_changed': False, 'independent_confirmation': False})
    print('Crosscell independent numerical-inner audit PASS', inner_count, outer_count, maximum, flush=True)


def fake_frame(truth=(0., 1.)):
    n = len(truth)
    return pd.DataFrame({'intervention_id': ['i' + str(i) for i in range(n)], 'dataset': ['fake'] * n,
        'biological_component': ['g'] * n, 'parent_context_id': ['p'] * n, 'measured_delta': truth})


class SyntheticTests(unittest.TestCase):
    def test_actual_coefficient_sums_and_one_full_shape_call(self):
        model = {'mean': [1., 2.], 'scale': [2., 4.], 'beta': [3., -2.], 'active': [True, True]}
        matrix = np.asarray([[3., 6.], [5., 2.], [9., 10.]])
        calls = []
        def scorer(m, x):
            calls.append(x.shape); return ((x - m['mean']) / m['scale']) @ np.asarray(m['beta'])
        score, error, checksum = bound_actual_coefficients(model, matrix, [0, 2], scorer)
        np.testing.assert_allclose(score, [1., 8.]); self.assertEqual(calls, [(2, 2)])
        self.assertEqual(error, 0.); self.assertEqual(len(checksum), 64)
        with self.assertRaises(AssertionError): bound_actual_coefficients(model, matrix, [0, 2], lambda m, x: scorer(m, x) + 1.)

    def test_canonical_ties_are_not_redefined_by_small_independent_difference(self):
        model = {'mean': [0., 0.], 'scale': [1., 1.], 'beta': [1., 1.], 'active': [True, True]}
        matrix = np.asarray([[1., 0.], [1., 1e-12]])
        score, error, _ = bound_actual_coefficients(model, matrix, [0, 1], lambda m, x: np.ones(len(x)))
        self.assertGreater(error, 0.); self.assertLess(error, SCORE_ATOL)
        chosen = independent_choices(fake_frame(), score)
        self.assertEqual(set(chosen.selected_id), {'i0'}); self.assertAlmostEqual(original_macro(chosen), .5)

    def test_analytic_extrema_regret_and_error_categories(self):
        positive = independent_choices(fake_frame((-2., 3.)), np.asarray([0., 1.]))
        self.assertEqual(original_macro(positive), 0.)
        reverse = independent_choices(fake_frame((-2., 3.)), np.asarray([1., 0.]))
        self.assertEqual(original_macro(reverse), 1.)
        for truth, category in [((-2., -1.), 'unavoidable_wrong'), ((-1., 0.), 'neutral_only_alternative_wrong'), ((-1., 1.), 'avoidable_wrong')]:
            chosen = independent_choices(fake_frame(truth), np.zeros(2))
            self.assertEqual(chosen[chosen.direction.eq(1)].iloc[0][category], 1.)

    def test_gene_weighting_not_candidate_or_fold_weighting(self):
        a = fake_frame(); b = fake_frame().assign(intervention_id=['j0','j1'], biological_component='h', parent_context_id='q')
        c = fake_frame().assign(intervention_id=['k0','k1'], biological_component='k', parent_context_id='r')
        frame = pd.concat([a,b,c],ignore_index=True); score = np.asarray([0.,1.,1.,0.,1.,0.])
        self.assertAlmostEqual(original_macro(independent_choices(frame,score)), 2/3)

    def test_source_selection_fixed_tolerance_and_target_independence(self):
        configs = [{'id': 'a'}, {'id': 'b'}, {'id': 'c'}]
        self.assertEqual(source_choice(configs,[.2+5e-13,.2,.3]),configs[0])
        self.assertEqual(source_choice(configs,[.3,.2,.4]),configs[1])
        with self.assertRaises(AssertionError): source_choice(configs,[np.nan,.2,.3])

    def test_metadata_or_duplicate_decision_corruption_rejected(self):
        d = independent_choices(fake_frame(),np.asarray([0.,1.]))
        with self.assertRaises(AssertionError): decisions_equal(d,d.assign(biological_component='wrong'))
        with self.assertRaises(AssertionError): decisions_equal(d,pd.concat([d,d.iloc[:1]]))


def synthetic():
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticTests))
    if not result.wasSuccessful(): raise SystemExit(1)
    immutable_json(OUT / 'crosscell_numeric_synthetic_01.json', {'status': 'PASS', 'tests': result.testsRun,
        'audit_source_sha256': sha256(__file__), 'canonical_helper_sha256': sha256(ROOT / 'src/generalization_rbp_20261007/canonical_inner_replay.py'),
        'project_models_read': False, 'project_feature_arrays_read': False, 'project_labels_read': False,
        'models_fit': 0, 'scope': 'Invented coefficient arithmetic/shape calls, canonical ties, analytic extrema/error categories, component weighting and config/metadata invariants'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['synthetic', 'run']); args = parser.parse_args()
    synthetic() if args.mode == 'synthetic' else run()
