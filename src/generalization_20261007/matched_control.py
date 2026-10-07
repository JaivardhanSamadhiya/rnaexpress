"""Postfit descriptive pair-only control, without another selection search.

This additive diagnostic reuses the completed scaling inner-fold results and
the already-frozen pair-normalized baseline family. It is not an additional
prospective primary model and cannot change the main generation's gate.
"""

from __future__ import annotations

import sys

from .common import *
from .engine import features
from . import route_scaling
from src.cross_assay_20260927.models import purge

CONTROL = OUT / 'matched_control'
CONFIGS = [dict(config) for config in route_scaling.CONFIGS if config['scaling'] == 'pair']
MODEL_ID = 'matched_pair_baseline'
KEYS = ['dataset', 'biological_component', 'parent_context_id', 'direction']
COMPARATORS = ('representation', 'mechanism')


def pinned_paths():
    paths = [
        SRC / 'matched_control.py', REP / 'matched_control_protocol.md',
        SRC / 'common.py', SRC / 'engine.py', SRC / 'route_scaling.py',
        ROOT / 'src/cross_assay_20260927/models.py',
        OUT / 'prefit_manifest.json', ART / 'scaling_features.npz',
        OUT / 'scaling/inner_selection.csv', OUT / 'scaling/run_complete.json',
    ]
    for track in COMPARATORS:
        paths.extend(OUT / track / filename for filename in
                     ('run_complete.json', 'decisions.csv', 'comparison.csv', 'predictions.csv.gz'))
    return paths


def prepare():
    """Make an immutable additive input manifest; no fitting or selections."""
    freeze_check()
    for track in ('scaling',) + COMPARATORS:
        receipt = readj(OUT / track / 'run_complete.json')
        assert receipt['status'] == 'PASS' and receipt['prediction_rows'] == 26258
        assert receipt['decision_rows'] == 10872 and not receipt['outer_target_selection']
    paths = pinned_paths()
    assert all(path.is_file() for path in paths)
    manifest = {
        'purpose': 'postfit descriptive family-matched pair-normalized short-feature control',
        'primary_gate_eligibility': False,
        'historical_results_changed': False,
        'configuration_order': CONFIGS,
        'fitting_allowed_only_after_manifest_commit': True,
        'files': {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths},
    }
    jsave(CONTROL / 'input_manifest.json', manifest)
    print('Matched descriptive control input manifest prepared; commit it before run', flush=True)


def check_manifest():
    freeze_check()
    path = CONTROL / 'input_manifest.json'
    manifest = readj(path)
    assert manifest['configuration_order'] == CONFIGS
    assert manifest['primary_gate_eligibility'] is False
    assert set(manifest['files']) == {p.relative_to(ROOT).as_posix() for p in pinned_paths()}
    for name, checksum in manifest['files'].items():
        assert sha256(ROOT / name) == checksum, name
    rel = path.relative_to(ROOT).as_posix()
    assert subprocess.check_output(['git', 'show', 'HEAD:' + rel], cwd=ROOT) == path.read_bytes()
    return manifest


def select_existing_inner(frame, table, held):
    """Select from the three existing pair configs using source results only."""
    test = frame.dataset.eq(held).to_numpy()
    train = purge(frame, ~test, test)
    source = frame.loc[train].reset_index(drop=True)
    inner_studies = sorted(source.dataset.unique())
    expected = {study for study in STUDIES if study != held}
    assert set(inner_studies) == expected
    scores = []
    for config in CONFIGS:
        values = []
        for inner in inner_studies:
            rows = table[
                table.outer_held.eq(held) & table.inner_held.eq(inner)
                & table.configuration.eq(config['id'])
            ]
            assert len(rows) == 1, 'Missing/duplicate original inner score'
            row = rows.iloc[0]
            validation = source.dataset.eq(inner).to_numpy()
            inner_train = purge(source, ~validation, validation)
            tr = source.loc[inner_train].reset_index(drop=True)
            ids = hashlib.sha256('|'.join(tr.intervention_id).encode()).hexdigest()
            assert row.training_ids_sha256 == ids
            assert int(row.training_rows) == len(tr)
            assert int(row.validation_rows) == int(validation.sum())
            assert held not in set(tr.dataset) and inner not in set(tr.dataset)
            assert np.isfinite(row.regret)
            values.append(float(row.regret))
        scores.append(float(np.mean(values)))
    best = min(scores)
    index = next(i for i, value in enumerate(scores) if value <= best + 1e-12)
    return dict(CONFIGS[index]), scores, train, test


def compare_existing(control_decisions, frame):
    """Require identical decision and candidate rosters before comparisons."""
    control_summary = summary(control_decisions)
    comparisons, paired = [], []
    for track in COMPARATORS:
        target = pd.read_csv(OUT / track / 'decisions.csv', float_precision='round_trip')
        assert not target.duplicated(KEYS).any() and not control_decisions.duplicated(KEYS).any()
        merged = control_decisions.merge(target, on=KEYS, suffixes=('_control', '_enriched'), validate='one_to_one')
        assert len(merged) == len(control_decisions) == len(target) == 10872
        assert np.array_equal(merged.candidates_control, merged.candidates_enriched)
        assert np.array_equal(merged.no_feasible_candidate_control, merged.no_feasible_candidate_enriched)
        predictions = pd.read_csv(OUT / track / 'predictions.csv.gz', usecols=['dataset', 'intervention_id'])
        assert len(predictions) == 26258 and not predictions.duplicated(['dataset', 'intervention_id']).any()
        assert set(map(tuple, predictions.to_numpy())) == set(map(tuple, frame[['dataset', 'intervention_id']].to_numpy()))
        rows = merged[KEYS + ['regret_control', 'regret_enriched', 'avoidable_wrong_control', 'avoidable_wrong_enriched']].copy()
        rows['enriched_track'] = track
        rows['regret_gain_enriched'] = rows.regret_control - rows.regret_enriched
        rows['avoidable_error_worsening_enriched'] = rows.avoidable_wrong_enriched - rows.avoidable_wrong_control
        paired.append(rows)
        target_summary = summary(target)
        joined = control_summary.merge(target_summary, on='dataset', suffixes=('_control', '_enriched'), validate='one_to_one')
        joined['enriched_track'] = track
        joined['regret_gain_enriched'] = joined.regret_control - joined.regret_enriched
        joined['avoidable_error_worsening_enriched'] = joined.avoidable_wrong_enriched - joined.avoidable_wrong_control
        comparisons.append(joined)
    return pd.concat(comparisons, ignore_index=True), pd.concat(paired, ignore_index=True)


def run():
    check_manifest()
    assert not (CONTROL / 'run_complete.json').exists(), 'Preserve completed descriptive control'
    frame, base = load()
    x = features('scaling')
    assert x.shape == (26258, 246) and np.array_equal(x, base)
    table = pd.read_csv(OUT / 'scaling/inner_selection.csv', float_precision='round_trip')
    assert len(CONFIGS) == 3
    predictions, choices, folds = [], [], []
    replay_errors = []
    for held in STUDIES:
        config, inner_scores, train, test = select_existing_inner(frame, table, held)
        source = frame.loc[train].reset_index(drop=True)
        target = frame.loc[test].reset_index(drop=True)
        train_hash = hashlib.sha256('|'.join(source.intervention_id).encode()).hexdigest()
        fit_path = CONTROL / 'fits' / (held + '_' + config['id'] + '.json')
        if fit_path.exists():
            model = readj(fit_path)
            assert model['_training_ids_sha256'] == train_hash and model['_config'] == config
        else:
            model = route_scaling.fit_model(source, x[train], config)
            model['_training_ids_sha256'] = train_hash
            model['_training_studies'] = sorted(source.dataset.unique())
            model['_training_components'] = sorted(source.biological_component.unique())
            model['_config'] = dict(config)
            jsave(fit_path, model)
        assert held not in model['_training_studies']
        score = route_scaling.predict_model(model, x[test])
        # A separately expressed sum checks the saved-model arithmetic.
        direct = np.sum((x[test] - np.asarray(model['mean'])) * (np.asarray(model['beta']) / np.asarray(model['scale'])), axis=1)
        error = float(np.max(np.abs(score - direct)))
        assert np.allclose(score, direct, rtol=1e-11, atol=1e-12)
        replay_errors.append(error)
        choices.append(decisions(target, score, MODEL_ID))
        predictions.extend({'model': MODEL_ID, 'dataset': held, 'intervention_id': row.intervention_id,
                            'score': float(score[j]), 'configuration': config['id']}
                           for j, row in enumerate(target.itertuples()))
        folds.append({
            'held': held, 'selected_configuration': config,
            'all_inner_scores': dict(zip([c['id'] for c in CONFIGS], inner_scores)),
            'inner_selection_reused': True, 'outer_target_selection': False,
            'training_ids_sha256': train_hash,
            'test_ids_sha256': hashlib.sha256('|'.join(target.intervention_id).encode()).hexdigest(),
            'training_studies': model['_training_studies'],
            'training_components': model['_training_components'], 'test_rows': len(target),
        })
        print('matched pair-only control', held, config['id'], 'outer complete', flush=True)
    decision_table = pd.concat(choices, ignore_index=True)
    comparison, paired = compare_existing(decision_table, frame)
    csvsave(CONTROL / 'decisions.csv', decision_table)
    csvsave(CONTROL / 'predictions.csv.gz', pd.DataFrame(predictions), True)
    csvsave(CONTROL / 'comparison.csv', summary(decision_table))
    csvsave(CONTROL / 'comparison_vs_enriched.csv', comparison)
    csvsave(CONTROL / 'paired_gain.csv.gz', paired, True)
    jsave(CONTROL / 'folds.json', folds)
    jsave(CONTROL / 'run_complete.json', {
        'status': 'PASS', 'purpose': 'postfit descriptive family-matched control',
        'primary_gate_eligibility': False, 'outer_target_selection': False,
        'new_grid_or_features': False, 'inner_fits_reused': 36,
        'fit_files': len(list((CONTROL / 'fits').glob('*.json'))),
        'prediction_rows': len(predictions), 'decision_rows': len(decision_table),
        'same_decision_roster_checks': 2, 'model_arithmetic_max_error': max(replay_errors),
        'input_manifest_sha256': sha256(CONTROL / 'input_manifest.json'),
        'main_prefit_manifest_sha256': sha256(OUT / 'prefit_manifest.json'),
    })
    print('Matched descriptive control complete', flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('prepare', 'run')
    (prepare if sys.argv[1] == 'prepare' else run)()
