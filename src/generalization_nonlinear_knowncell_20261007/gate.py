"""Unchanged conditional-cell thresholds and matched readout/loss contrasts."""
from .common import *
from .evaluate import task_summary
from src.generalization_knowncell_20261007.gate import compare

def baseline_checks(value, prefix):
    return {prefix + '_mean_gain_0_01': value['mean_gain'] >= .01,
        prefix + '_each_cell_gain_0_005': min(value['per_known_cell_gain'].values()) >= .005,
        prefix + '_bootstrap_lower_positive': value['gain_ci'][0] > 0,
        prefix + '_macro_wrong_harm_0_02': value['macro_wrong_direction_harm'] <= .02,
        prefix + '_each_cell_wrong_harm_0_05': max(value['wrong_direction_harm'].values()) <= .05,
        prefix + '_leave_best_fold_positive': value['remaining_gain'] > 0}

def information_checks(value, prefix):
    return {prefix + '_information_mean_0_01': value['mean_gain'] >= .01,
            prefix + '_information_leave_best_positive': value['remaining_gain'] > 0}

def run():
    freeze_check(); receipt = readj(OUT / 'verification_receipt.json')
    assert receipt['status'] == 'PASS' and receipt['evaluation_manifest_sha256'] == sha256(OUT / 'evaluation_manifest.json')
    assert receipt['predictors_checked'] == receipt['crossed_state_predictors_rechecked'] == 84 and receipt['same_checkpoint_both_states_verified']
    assert receipt['maximum_score_error'] < 1e-9 and receipt['pairwise_known_controls_predictors_replayed'] == 42
    assert receipt['pairwise_known_control_maximum_error'] <= 1e-9
    checked_files(receipt['result_files'])
    assert receipt['pairwise_known_control_replay_receipt_sha256'] == sha256(OUT / 'pairwise_known_control_replay.json')
    data = {track: pd.read_csv(OUT / track / 'decisions.csv', float_precision='round_trip') for track in TRACKS}
    pairwise = {feature: pd.read_csv(KNOWN_OUT / feature / 'decisions.csv', float_precision='round_trip') for feature in FEATURE_TRACKS}
    information = {'structure': ['raw'], 'bert': ['lookup'], 'combined': ['structure', 'bert']}
    results = []
    for track in TRACKS:
        values = task_summary(data[track]).set_index('task')
        checks = {'macro_regret_at_most_0_48': float(values.regret.mean()) <= .48,
                  'each_known_cell_below_uniform': bool((values.regret < .5).all())}
        baselines, additional = {}, {}
        for control in ('base', 'simple'):
            for origin, tables in (('pairwise', pairwise), ('hgb', data)):
                key = origin + '/' + control; table = tables[control if origin == 'pairwise' else key]
                value = compare(data[track], table); baselines[key] = value; checks.update(baseline_checks(value, key))
        if track in INFORMED:
            feature = track.split('/')[1]
            matched = {'pairwise/' + feature: pairwise[feature], 'ridge/' + feature: data['ridge/' + feature]}
            matched.update({'hgb/' + control: data['hgb/' + control] for control in information[feature]})
            for key, table in matched.items():
                value = compare(data[track], table); additional[key] = value; checks.update(information_checks(value, key))
        results.append({'track': track, 'claim_eligible': track in INFORMED, 'passes': track in INFORMED and all(checks.values()),
            'checks': checks, 'macro_regret': float(values.regret.mean()), 'per_known_cell': values.reset_index().to_dict('records'),
            'baseline_comparisons': baselines, 'information_and_matched_loss_controls': additional})
    jsave(OUT / 'gate_verdict.json', {'status': 'CONDITIONAL_CELL_DEVELOPMENT_GO' if any(row['passes'] for row in results) else 'NO-GO',
        'tracks': results, 'new_fits': 0, 'original_nonlinear_gate_unchanged': True, 'original_pairwise_known_gate_unchanged': True,
        'evaluation_manifest_sha256': sha256(OUT / 'evaluation_manifest.json'), 'verification_receipt_sha256': sha256(OUT / 'verification_receipt.json'),
        'thresholds_changed_after_performance': False, 'independent_confirmation': False,
        'scope': 'Matched pointwise HGB/ridge source-checkpoint evaluation on held genes conditional on represented cell; not a new cell-conditioning method or unseen-cell confirmation'})

if __name__ == '__main__':
    run()
