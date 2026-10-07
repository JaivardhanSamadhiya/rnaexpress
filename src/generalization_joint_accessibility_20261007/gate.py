"""Original strict gate plus joint-vs-marginal and duplication comparisons."""
from .common import *
from .control_reuse import check as control_check
from src.generalization_splicebert_downstream_20261007.gate import strict_checks, incremental_checks
from src.generalization_next_20261007.bootstrap import shared_bootstrap

def run():
    freeze_check(); input_check(); control = control_check()
    verification = readj(OUT / 'verification_receipt.json')
    assert verification['status'] == 'PASS' and verification['prefit_manifest_sha256'] == sha256(OUT / 'prefit_manifest.json')
    assert verification['inner_original_truth_regrets_replayed'] == 72 and verification['outer_targets_replayed'] == 8
    for key in ('maximum_inner_score_error', 'maximum_outer_arithmetic_score_error', 'maximum_outer_score_error', 'maximum_outer_independent_vs_saved_score_error'):
        assert verification[key] < 1e-9
    assert verification['direct_pair_credit_and_recovery_checked'] and verification['all_source_only_configurations_reselected_from_replay']
    for name, expected in verification['files'].items():
        assert sha256(ROOT / name) == expected, name
    old = pd.read_csv(ROOT / 'artifacts/cross_assay_20260927/model_comparison.csv')
    old = old[old.stage.eq('held_assay')].set_index(['model', 'dataset'])
    simple_models = {study: min(['uniform', 'metadata', 'composition'], key=lambda model: (float(old.loc[model, study].regret), float(old.loc[model, study].avoidable_wrong), model)) for study in STUDIES}
    simple = {study: min(float(old.loc[model, study].regret) for model in ['uniform', 'metadata', 'composition']) for study in STUDIES}
    h0 = {study: float(old.loc['interaction_3', study].regret) for study in STUDIES}
    prior = pd.read_csv(ROOT / 'results/cross_assay_20260927/decision_metrics.csv'); prior = prior[prior.stage.eq('held_assay')]
    def path(track, filename):
        return (RBP_OUT if track in CONTROLS else OUT) / track / filename
    comparisons = {track: pd.read_csv(path(track, 'comparison.csv'), float_precision='round_trip').set_index('dataset') for track in CONTROLS + TRACKS}
    all_decisions = [pd.read_csv(path(track, 'decisions.csv'), float_precision='round_trip') for track in CONTROLS]
    results = []
    for track in TRACKS:
        complete = readj(OUT / track / 'run_complete.json')
        assert complete['status'] == 'PASS' and complete['fit_files'] == 40 and complete['prediction_rows'] == 26258 and complete['prefit_manifest_sha256'] == sha256(OUT / 'prefit_manifest.json')
        comp = comparisons[track]; assert set(comp.index) == set(STUDIES) and comp.index.is_unique
        d = pd.read_csv(OUT / track / 'decisions.csv', float_precision='round_trip'); all_decisions.append(d)
        regrets = np.asarray([float(comp.loc[study].regret) for study in STUDIES])
        gains = np.asarray([simple[study] - float(comp.loc[study].regret) for study in STUDIES])
        gain_h0 = np.asarray([h0[study] - float(comp.loc[study].regret) for study in STUDIES])
        wrong = np.asarray([float(comp.loc[study].avoidable_wrong) - float(old.loc[simple_models[study], study].avoidable_wrong) for study in STUDIES])
        wrong_h0 = np.asarray([float(comp.loc[study].avoidable_wrong) - float(old.loc['interaction_3', study].avoidable_wrong) for study in STUDIES])
        by_study = {}
        for study in STUDIES:
            a = prior[prior.dataset.eq(study) & prior.model.eq(simple_models[study])].groupby('biological_component').regret.mean()
            b = d[d.dataset.eq(study)].groupby('biological_component').regret.mean()
            assert set(a.index) == set(b.index); by_study[study] = a - b.reindex(a.index)
        bootstrap = shared_bootstrap(by_study, draws=5000, seed=SEED)
        checks, share = strict_checks(regrets, gains, gain_h0, wrong, wrong_h0, bootstrap)
        incremental = []
        if track == 'joint':
            for comparator in ('access', 'duplicate_marginal'):
                gain = np.asarray([float(comparisons[comparator].loc[study].regret) - float(comp.loc[study].regret) for study in STUDIES])
                additional = incremental_checks(gain)
                incremental.append({'comparator': comparator, 'mean_gain': float(gain.mean()), 'per_assay_gain': dict(zip(STUDIES, gain.tolist())),
                    'checks': additional, 'passes': all(additional.values())})
        passes = track == 'joint' and all(checks.values()) and all(value['passes'] for value in incremental)
        results.append({'track': track, 'passes': passes, 'historical_gate_passes': all(checks.values()),
            'checks': checks, 'incremental_comparisons': incremental, 'macro_regret': float(regrets.mean()),
            'macro_gain_vs_simple': float(gains.mean()), 'macro_gain_vs_H0': float(gain_h0.mean()), 'max_positive_gain_share': share,
            'gain_ci': [float(np.quantile(bootstrap, .025)), float(np.quantile(bootstrap, .975))],
            'per_assay': [{'dataset': study, 'regret': float(regrets[i]), 'gain_vs_simple': float(gains[i]), 'gain_vs_H0': float(gain_h0[i]),
                          'avoidable_wrong': float(comp.loc[study].avoidable_wrong)} for i, study in enumerate(STUDIES)]})
    csvsave(ART / 'model_comparison.csv', pd.concat([pd.read_csv(path(track, 'comparison.csv'), float_precision='round_trip') for track in CONTROLS + TRACKS], ignore_index=True))
    csvsave(ART / 'decision_metrics.csv.gz', pd.concat(all_decisions, ignore_index=True), True)
    jsave(OUT / 'gate_verdict.json', {'status': 'DEVELOPMENT_GO' if any(row['passes'] for row in results) else 'NO-GO',
        'tracks': results, 'prefit_manifest_sha256': sha256(OUT / 'prefit_manifest.json'), 'verification_receipt_sha256': sha256(OUT / 'verification_receipt.json'),
        'control_reuse_receipt_sha256': sha256(OUT / 'control_reuse_receipt.json'), 'criteria_changed_after_results': False,
        'reused_control_fits': control['reused_control_fits'], 'new_fit_checkpoints': 80, 'reused_controls_are_new_evidence': False,
        'independent_confirmation': False, 'observed_data_followup': True, 'whole_site_opening_is_binding_or_occupancy': False,
        'method_is_novel': False, 'duplicate_columns': 'Width matched L2 redundancy control; does not match full rank or establish causal mechanism',
        'calibration': 'Relative candidate utility only; development evidence does not establish probabilities, absolute localization or a new biological mechanism'})
    print(readj(OUT / 'gate_verdict.json')['status'], flush=True)

if __name__ == '__main__':
    run()
