"""Fixed compatible-cell gate; preserve the separate four-source NO-GO."""
from .experiment_common import *
from .engine import task_summary
from .bootstrap import shared_bootstrap,family_bootstrap


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
    families=family_bootstrap(gains,5000,SEED)
    wrong_a,wrong_b=component_values(control,'wrong_direction'),component_values(candidate,'wrong_direction')
    wrong={task:float((wrong_b[task]-wrong_a[task].reindex(wrong_b[task].index)).mean()) for task in TASKS}
    return {'mean_gain':float(np.mean(list(means.values()))),'per_crossed_cell_gain':means,
        'gain_ci':[float(np.quantile(bootstrap,.025)),float(np.quantile(bootstrap,.975))],
        'family_gain_ci':[float(np.quantile(families,.025)),float(np.quantile(families,.975))],
        'fold_gains':fold_gains,'removed_best_gene_fold':best,'remaining_gain':remaining,
        'wrong_direction_harm':wrong,'macro_wrong_direction_harm':float(np.mean(list(wrong.values())))}


def unpurged_diagnostic(decisions_by_track):
    # This diagnostic is prespecified and never contributes to selection/gates.
    receipt=readj(UNPURGED_OUT/'verification_receipt.json');assert receipt['status']=='PASS'
    files={};rows=[]
    for track in TRACKS:
        path=UNPURGED_OUT/track/'decisions.csv'
        finished=readj(UNPURGED_OUT/track/'run_complete.json')
        assert finished['status']=='PASS' and finished['prefit_manifest_sha256']==sha256(UNPURGED_OUT/'prefit_manifest.json')
        old=pd.read_csv(path,float_precision='round_trip');new=decisions_by_track[track]
        columns=['task','gene_fold','parent_context_id','direction','dataset','biological_component']
        left=old[columns].sort_values(columns).reset_index(drop=True)
        right=new[columns].sort_values(columns).reset_index(drop=True)
        pd.testing.assert_frame_equal(left,right)
        files[path.relative_to(ROOT).as_posix()]=sha256(path)
        comparison=compare(new,old)
        rows.append({'track':track,'same_target_roster':True,'unpurged_minus_purged_regret':comparison,
                     'interpretation':'descriptive sensitivity to the fixed stricter source purge; no gate/threshold selection'})
    return {'tracks':rows,'input_hashes':files,'manifest_sha256':sha256(UNPURGED_OUT/'prefit_manifest.json'),
            'integrity_scope':'Late postfit observed decision/verification SHA, not creation-time result binding; original replay PASS required',
            'verification_receipt_sha256':sha256(UNPURGED_OUT/'verification_receipt.json')}


def run():
    freeze_check()
    verification=readj(OUT/'verification_receipt.json');assert verification['status']=='PASS'
    for name,digest in verification['result_files'].items():assert sha256(ROOT/name)==digest
    decisions_by_track={}
    for track in TRACKS:
        assert readj(OUT/track/'run_complete.json')['status']=='PASS'
        decisions_by_track[track]=pd.read_csv(OUT/track/'decisions.csv',float_precision='round_trip')
    feature_controls={'structure':['raw'],'bert':['lookup'],'combined':['structure','bert']}
    results=[]
    for track in TRACKS:
        d=decisions_by_track[track];comp=task_summary(d).set_index('task')
        checks={'mean_normalized_regret_at_most_0_48':float(comp.regret.mean())<=.48,
            'both_crossed_cells_improve_uniform':bool((comp.regret<.5).all())}
        incremental={}
        for control in ('base','simple'):
            comparison=compare(d,decisions_by_track[control]);incremental[control]=comparison
            checks.update({control+'_mean_gain_at_least_0_01':comparison['mean_gain']>=.01,
                control+'_each_cell_gain_at_least_0_005':min(comparison['per_crossed_cell_gain'].values())>=.005,
                control+'_paired_bootstrap_lower_above_zero':comparison['gain_ci'][0]>0,
                control+'_family_bootstrap_lower_above_zero':comparison['family_gain_ci'][0]>0,
                control+'_macro_wrong_harm_at_most_0_02':comparison['macro_wrong_direction_harm']<=.02,
                control+'_each_cell_wrong_harm_at_most_0_05':max(comparison['wrong_direction_harm'].values())<=.05,
                control+'_positive_after_removing_best_gene_fold':comparison['remaining_gain']>0})
        feature_comparisons={}
        for control in feature_controls.get(track,[]):
            comparison=compare(d,decisions_by_track[control]);feature_comparisons[control]=comparison
            checks[control+'_feature_mean_gain_at_least_0_01']=comparison['mean_gain']>=.01
            checks[control+'_feature_positive_after_best_fold_removed']=comparison['remaining_gain']>0
        results.append({'track':track,'claim_eligible':track in INFORMED,
            'passes':track in INFORMED and all(checks.values()),'checks':checks,
            'macro_regret':float(comp.regret.mean()),'per_crossed_cell':comp.reset_index().to_dict('records'),
            'incremental_controls':incremental,'feature_controls':feature_comparisons})
    diagnostics=unpurged_diagnostic(decisions_by_track)
    freeze_check()
    jsave(OUT/'gate_verdict.json',{'status':'NARROW_DEVELOPMENT_GO' if any(r['passes'] for r in results) else 'NO-GO',
        'tracks':results,'unpurged_diagnostic':diagnostics,
        'similarity_scope':'global unit150nt editdistance<=30, not evolutionaryhomology',
        'gene_components':187,'similarity_families':184,'four_source_gate_unchanged':True,'independent_confirmation':False,
        'criteria_changed_after_results':False,'claim_scope':'Original150nt similarity-family-excluded gene/cell transfer within exposed Mikl assay only',
        'controls_not_claim_eligible':['simple','base','raw','lookup']})
    csvsave(ART/'model_comparison.csv',pd.concat([task_summary(decisions_by_track[t]) for t in TRACKS],ignore_index=True))
    print(readj(OUT/'gate_verdict.json')['status'],flush=True)


if __name__=='__main__':run()
