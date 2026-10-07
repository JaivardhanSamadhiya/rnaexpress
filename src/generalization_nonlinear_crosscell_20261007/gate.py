"""Fixed compatible-cell gate; preserve the separate four-source NO-GO."""
from .common import *
from .engine import task_summary
from .bootstrap import shared_bootstrap


def component_values(d,column):
    return {task:d[d.task.eq(task)].groupby('biological_component')[column].mean() for task in TASKS}


def compare(candidate,control):
    a,b=component_values(control,'regret'),component_values(candidate,'regret')
    gains={}
    for task in TASKS:
        assert set(a[task].index)==set(b[task].index)
        gains[task]=a[task]-b[task].reindex(a[task].index)
    means={task:float(v.mean()) for task,v in gains.items()}
    foldmap=candidate[['biological_component','gene_fold']].drop_duplicates().set_index('biological_component').gene_fold
    assert foldmap.index.is_unique
    fold_gains={fold:float(np.mean([v[v.index.map(foldmap).to_numpy()==fold].mean() for v in gains.values()])) for fold in FOLDS}
    best=max(FOLDS,key=lambda fold:(fold_gains[fold],-fold))
    remaining=float(np.mean([v[v.index.map(foldmap).to_numpy()!=best].mean() for v in gains.values()]))
    bootstrap=shared_bootstrap(gains,5000,SEED)
    wrong_a,wrong_b=component_values(control,'wrong_direction'),component_values(candidate,'wrong_direction')
    wrong={task:float((wrong_b[task]-wrong_a[task].reindex(wrong_b[task].index)).mean()) for task in TASKS}
    return {'mean_gain':float(np.mean(list(means.values()))),'per_crossed_cell_gain':means,
        'gain_ci':[float(np.quantile(bootstrap,.025)),float(np.quantile(bootstrap,.975))],
        'fold_gains':fold_gains,'removed_best_gene_fold':best,'remaining_gain':remaining,
        'wrong_direction_harm':wrong,'macro_wrong_direction_harm':float(np.mean(list(wrong.values())))}


def run():
    freeze_check()
    verified=readj(OUT/'verification_receipt.json');assert verified['status']=='PASS'
    for name,expected in verified['result_files'].items():assert sha256(ROOT/name)==expected,name
    from src.generalization_crosscell_20261007.common import freeze_check as linear_freeze_check
    linear_freeze_check()
    assert readj(LINEAR_OUT/'verification_receipt.json')['status']=='PASS'
    decisions_by_track={}
    for track in TRACKS:
        assert readj(OUT/track/'run_complete.json')['status']=='PASS'
        decisions_by_track[track]=pd.read_csv(OUT/track/'decisions.csv')
    linear_decisions={track:pd.read_csv(LINEAR_OUT/track/'decisions.csv') for track in FEATURE_TRACKS}
    for track in FEATURE_TRACKS:
        receipt=readj(LINEAR_OUT/track/'run_complete.json')
        assert receipt['status']=='PASS' and receipt['prefit_manifest_sha256']==sha256(LINEAR_OUT/'prefit_manifest.json')
        identity=['task','gene_fold','biological_component','parent_context_id','direction']
        for learner in ('hgb','ridge'):
            a=decisions_by_track[learner+'/'+track][identity].sort_values(identity).reset_index(drop=True)
            b=linear_decisions[track][identity].sort_values(identity).reset_index(drop=True)
            pd.testing.assert_frame_equal(a,b)
    feature_controls={'hgb/structure':['hgb/raw'],'hgb/bert':['hgb/lookup'],'hgb/combined':['hgb/structure','hgb/bert']}
    results=[]
    for track in TRACKS:
        d=decisions_by_track[track];comp=task_summary(d).set_index('task')
        checks={'mean_normalized_regret_at_most_0_48':float(comp.regret.mean())<=.48,
            'both_crossed_cells_improve_uniform':bool((comp.regret<.5).all())}
        incremental={}
        controls={control:decisions_by_track[control] for control in ('hgb/base','hgb/simple')}
        controls.update({'pairwise/'+control:linear_decisions[control] for control in ('base','simple')})
        for control,control_decisions in controls.items():
            comparison=compare(d,control_decisions);incremental[control]=comparison
            checks.update({control+'_mean_gain_at_least_0_01':comparison['mean_gain']>=.01,
                control+'_each_cell_gain_at_least_0_005':min(comparison['per_crossed_cell_gain'].values())>=.005,
                control+'_paired_bootstrap_lower_above_zero':comparison['gain_ci'][0]>0,
                control+'_macro_wrong_harm_at_most_0_02':comparison['macro_wrong_direction_harm']<=.02,
                control+'_each_cell_wrong_harm_at_most_0_05':max(comparison['wrong_direction_harm'].values())<=.05,
                control+'_positive_after_removing_best_gene_fold':comparison['remaining_gain']>0})
        feature_comparisons={}
        linear_comparison=compare(d,linear_decisions[feature_track(track)])
        checks['corresponding_linear_mean_gain_at_least_0_01']=linear_comparison['mean_gain']>=.01
        checks['corresponding_linear_positive_after_best_fold_removed']=linear_comparison['remaining_gain']>0
        pointwise_comparison=compare(d,decisions_by_track['ridge/'+feature_track(track)])
        checks['corresponding_pointwise_ridge_mean_gain_at_least_0_01']=pointwise_comparison['mean_gain']>=.01
        checks['corresponding_pointwise_ridge_positive_after_best_fold_removed']=pointwise_comparison['remaining_gain']>0
        for control in feature_controls.get(track,[]):
            comparison=compare(d,decisions_by_track[control]);feature_comparisons[control]=comparison
            checks[control+'_feature_mean_gain_at_least_0_01']=comparison['mean_gain']>=.01
            checks[control+'_feature_positive_after_best_fold_removed']=comparison['remaining_gain']>0
        results.append({'track':track,'claim_eligible':track in INFORMED,
            'passes':track in INFORMED and all(checks.values()),'checks':checks,
            'macro_regret':float(comp.regret.mean()),'per_crossed_cell':comp.reset_index().to_dict('records'),
            'incremental_controls':incremental,'feature_controls':feature_comparisons,
            'corresponding_linear_control':linear_comparison,'corresponding_pointwise_ridge':pointwise_comparison})
    jsave(OUT/'gate_verdict.json',{'status':'NARROW_DEVELOPMENT_GO' if any(r['passes'] for r in results) else 'NO-GO',
        'tracks':results,'four_source_gate_unchanged':True,'independent_confirmation':False,
        'criteria_changed_after_results':False,'claim_scope':'Nonlinear pointwise regressor, exposed unseen-gene crossed-cell selection only',
        'pointwise_objective_and_readout_changed':True,
        'linear_comparator_result_hashes':{track:sha256(LINEAR_OUT/track/'decisions.csv') for track in FEATURE_TRACKS},
        'controls_not_claim_eligible':[track for track in TRACKS if track not in INFORMED]})
    csvsave(ART/'model_comparison.csv',pd.concat([task_summary(decisions_by_track[t]) for t in TRACKS],ignore_index=True))
    print(readj(OUT/'gate_verdict.json')['status'],flush=True)


if __name__=='__main__':run()
