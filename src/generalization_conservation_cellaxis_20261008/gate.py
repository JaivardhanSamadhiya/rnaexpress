"""Identical numerical narrow gates, explicitly separate crossed/represented axes."""
from .common import *
from .numeric import task_summary
from src.generalization_conservation_cellaxis_20261008.contracts import comparison_checks,information_checks


def compare(candidate,control,tasks):
    np,*_=runtime()
    from src.generalization_crosscell_20261007.bootstrap import shared_bootstrap
    gains={};wrong={};avoidable={}
    for task in tasks:
        a,b=[v[v.task.eq(task)].groupby('biological_component')[['regret','wrong_direction','avoidable_wrong']].mean() for v in (control,candidate)]
        assert set(a.index)==set(b.index) and len(a)==s.COMPONENTS
        gains[task]=a.regret-b.regret.reindex(a.index)
        wrong[task]=float((b.wrong_direction-a.wrong_direction.reindex(b.index)).mean())
        avoidable[task]=float((b.avoidable_wrong-a.avoidable_wrong.reindex(b.index)).mean())
    means={task:float(v.mean()) for task,v in gains.items()}
    foldmap=candidate[['biological_component','gene_fold']].drop_duplicates().set_index('biological_component').gene_fold
    assert foldmap.index.is_unique and set(foldmap.values)==set(s.FOLDS)
    foldgains={fold:float(np.mean([v[v.index.map(foldmap).to_numpy()==fold].mean() for v in gains.values()])) for fold in s.FOLDS}
    best=max(s.FOLDS,key=lambda fold:(foldgains[fold],-fold))
    remaining=float(np.mean([v[v.index.map(foldmap).to_numpy()!=best].mean() for v in gains.values()]))
    components=sorted(set(next(iter(gains.values())).index))
    assert all(set(v.index)==set(components) for v in gains.values())
    component_gain={gene:float(np.mean([v.loc[gene] for v in gains.values()])) for gene in components}
    best_gene=min(components,key=lambda gene:(-component_gain[gene],str(gene)))
    remaining_gene=float(np.mean([v.drop(index=best_gene).mean() for v in gains.values()]))
    interval=shared_bootstrap(gains,5000,s.SEED)
    return {'mean_gain':float(np.mean(list(means.values()))),'per_cell_gain':means,
        'gain_ci':[float(np.quantile(interval,.025)),float(np.quantile(interval,.975))],
        'removed_best_gene_fold':best,'remaining_gain':remaining,'fold_gains':foldgains,
        'wrong_direction_harm':wrong,'macro_wrong_direction_harm':float(np.mean(list(wrong.values()))),
        'avoidable_wrong_harm':avoidable,'macro_avoidable_wrong_harm':float(np.mean(list(avoidable.values()))),
        'removed_best_gene_component':best_gene,'remaining_gene_gain':remaining_gene}


def run(axis,root_start=False):
    assert root_start and axis in ('crossed','represented');np,pd,*_=runtime()
    if axis=='crossed':
        prefit_check();receipt=readj(OUT/'crossed_verification_receipt.json');tasks=s.TASKS
        assert receipt['status']=='PASS' and receipt['prefit_sha256']==sha256(PREFIT)
        assert receipt['new_inner_replayed']==144 and receipt['new_outer_replayed']==24
    else:
        evaluation_check();receipt=readj(OUT/'represented_verification_receipt.json');tasks=s.KNOWN_TASKS
        assert receipt['status']=='PASS' and receipt['evaluation_sha256']==sha256(EVALUATION) and receipt['same_checkpoint_both_states_verified']
    hash_files(receipt['files']);assert not (OUT/(axis+'_gate_verdict.json')).exists()
    data={}
    for track in s.TRACKS:
        folder=OLD_OUT/track if axis=='crossed' and track in s.REUSED_CONTROLS else OUT/axis/track
        data[track]=pd.read_csv(folder/'decisions.csv',float_precision='round_trip')
    results=[]
    for track in s.TRACKS:
        summary=task_summary(data[track]).set_index('task')
        assert set(summary.index)==set(tasks)
        checks={'macro_regret_at_most_0_48':float(summary.regret.mean())<=.48,
                'each_cell_regret_below_0_5':bool((summary.regret<.5).all())}
        comparisons={};ablations={}
        for control in s.REUSED_CONTROLS:
            result=compare(data[track],data[control],tasks);comparisons[control]=result
            checks.update({control+'_'+key:value for key,value in comparison_checks(result).items()})
        for control in s.INFORMATION_CONTROLS.get(track,[]):
            result=compare(data[track],data[control],tasks);ablations[control]=result
            checks.update({control+'_'+key:value for key,value in information_checks(result).items()})
        results.append({'track':track,'claim_eligible':track in s.INFORMED,
            'passes':track in s.INFORMED and all(checks.values()),'checks':checks,
            'macro_regret':float(summary.regret.mean()),'per_cell':summary.reset_index().to_dict('records'),
            'baseline_controls':comparisons,'information_controls':ablations})
    go=any(r['passes'] for r in results)
    jsave(OUT/(axis+'_gate_verdict.json'),{'status':('CROSSED_CELL_DEVELOPMENT_GO' if axis=='crossed' else 'REPRESENTED_CELL_DEVELOPMENT_GO') if go else 'NO-GO',
        'axis':axis,'tracks':results,'all_old_gates_unchanged':True,'independent_confirmation':False,
        'no_primary_whole_assay_reinterpretation':True,'thresholds_changed_after_results':False,
        'new_fits_for_represented_evaluation':0})


if __name__=='__main__':
    import sys
    run(sys.argv[1],'--root-start' in sys.argv[2:])
