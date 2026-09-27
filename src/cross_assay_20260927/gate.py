"""Frozen decision rule; failed development gate prohibits new-data discovery."""
from .common import *
from .metrics import aggregate

def run():
    frozen();f=pd.read_csv(OUT/'decision_metrics.csv');compare=pd.read_csv(ART/'model_comparison.csv');core=compare[compare.stage.eq('held_assay')]
    simple=config()['simple_baselines'];baseline=core[core.model.isin(simple)].sort_values(['dataset','regret','avoidable_wrong','model']).groupby('dataset').first().reset_index()
    csvsave(OUT/'strongest_simple_envelope.csv',baseline)
    d=f[f.stage.eq('held_assay')];units=sorted(d.biological_component.unique());rng=np.random.default_rng(SEED);weights=rng.exponential(1,(5000,len(units)));unit_lookup={u:i for i,u in enumerate(units)};allgains=[];verdicts=[]
    for model in config()['models']:
        if model in simple:continue
        per=[];boots=[]
        for study in config()['core_studies']:
            base=baseline[baseline.dataset.eq(study)].iloc[0];p=core[core.dataset.eq(study)&core.model.eq(model)].iloc[0]
            per.append({'model':model,'dataset':study,'baseline':base.model,'regret':p.regret,'regret_gain':base.regret-p.regret,'avoidable_wrong':p.avoidable_wrong,'avoidable_wrong_worsening':p.avoidable_wrong-base.avoidable_wrong})
            a=d[d.dataset.eq(study)&d.model.eq(model)].groupby('biological_component').regret.mean();b=d[d.dataset.eq(study)&d.model.eq(base.model)].groupby('biological_component').regret.mean();assert set(a.index)==set(b.index)
            gains=b.loc[a.index]-a;w=weights[:,[unit_lookup[u] for u in a.index]];boots.append((w@gains.to_numpy())/w.sum(1))
        t=pd.DataFrame(per);allgains.extend(per);gain=t.regret_gain.to_numpy();risk=t.avoidable_wrong_worsening.to_numpy();ci=np.quantile(np.mean(boots,axis=0),[.025,.975]);pos=np.maximum(gain,0);share=float(pos.max()/pos.sum()) if pos.sum()>0 else 1.
        checks={'all_four_core_studies':len(t)==4,'at_least_three_studies_gain_0_02':int((gain>=.02).sum())>=3,'macro_gain_at_least_0_02':gain.mean()>=.02,'leave_best_study_out_positive':np.delete(gain,np.argmax(gain)).mean()>0,'no_study_over_60pct_positive_gain':share<=.60,'macro_avoidable_harm_at_most_0_02':risk.mean()<=.02,'no_study_avoidable_harm_over_0_05':risk.max()<=.05,'no_study_regret_harm_over_0_05':gain.min()>=-.05,'descriptive_gain_lower_at_least_minus_0_01':ci[0]>=-.01}
        composite=t.regret.mean()+.25*t.avoidable_wrong.mean()+.05*(gain<0).mean()+.10*t.regret.max()
        verdicts.append({'model':model,'passes':all(checks.values()),'checks':checks,'macro_regret':t.regret.mean(),'macro_gain':gain.mean(),'gain_ci_low':ci[0],'gain_ci_high':ci[1],'macro_avoidable_wrong':t.avoidable_wrong.mean(),'macro_avoidable_worsening':risk.mean(),'studies_helped':int((gain>0).sum()),'studies_harmed':int((gain<0).sum()),'studies_helped_at_least_0_02':int((gain>=.02).sum()),'max_positive_gain_share':share,'composite':composite})
    def choose(pool):
        best=min(v['composite'] for v in pool);schema=readj(OUT/'feature_schema.json')['columns']
        return min((v for v in pool if v['composite']<=best+1e-12),key=lambda v:(len(schema[config()['models'][v['model']][0]]),v['model']))
    passing=[v for v in verdicts if v['passes']];leader=choose(verdicts)
    selected=choose(passing)['model'] if passing else None
    result={'status':'GO_TO_METADATA_ONLY_DISCOVERY' if selected else 'NO-GO','selected_model':selected,'descriptive_leader_not_validated':leader['model'],'new_dataset_discovery_allowed':bool(selected),'independent_confirmation':False,'models':verdicts,'criteria_changed_after_results':False}
    jsave(OUT/'gate_verdict.json',result);csvsave(OUT/'per_assay_baseline_gains.csv',pd.DataFrame(allgains))
    # Feature transfer matrix distinguishes optimistic resubstitution from genuine held units.
    effects=[]
    for model in config()['models']:
        for study in config()['core_studies']:
            row={'model':model,'dataset':study}
            for stage,label in [('within_assay','within_assay_gain_optimistic'),('held_parent','held_parent_gain'),('held_assay','held_assay_gain')]:
                s=compare[compare.stage.eq(stage)&compare.dataset.eq(study)]
                m=s[s.model.eq(model)];base=s[s.model.eq('composition')]
                row[label]=float(base.regret.iloc[0]-m.regret.iloc[0]) if len(m) and len(base) else np.nan
            effects.append(row)
    csvsave(ART/'feature_transfer_matrix.csv',pd.DataFrame(effects))
    # Coverage/risk uses only the fixed confidence threshold grid, never a chosen favorable cutoff.
    curves=[]
    for (stage,model,dataset),g in f[f.stage.isin(['held_assay','secondary_sirloin']) & ~f.model.eq('uniform')].groupby(['stage','model','dataset']):
        for threshold in config()['abstention']['thresholds']:
            accepted=g.abstention_confidence.ge(threshold);unit_coverage=g.assign(accepted=accepted).groupby('biological_component').accepted.mean();keep=g[accepted]
            risk=keep.groupby('biological_component')[['regret','correct_direction','wrong_direction','avoidable_wrong']].mean().mean()
            curves.append({'stage':stage,'model':model,'dataset':dataset,'threshold':threshold,'coverage':unit_coverage.mean(),'accepted_decisions':len(keep),'total_decisions':len(g),**{k:risk.get(k,np.nan) for k in ('regret','correct_direction','wrong_direction','avoidable_wrong')}})
    csvsave(OUT/'coverage_risk.csv',pd.DataFrame(curves))
    print(result['status'],'selected',selected,'descriptive leader',leader['model'])
    print(pd.DataFrame([{k:v for k,v in x.items() if k!='checks'} for x in verdicts]).to_string(index=False))
if __name__=='__main__':run()
