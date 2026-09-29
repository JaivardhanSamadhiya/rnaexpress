from .common import *
from scipy.stats import spearmanr

def run():
    frozen();c=pd.read_csv(ART/'model_comparison.csv');c=c[c.stage.eq('held_assay')];d=pd.read_csv(OUT/'decision_metrics.csv');d=d[d.stage.eq('held_assay')];base=pd.read_csv(OLD/'strongest_simple_envelope.csv').set_index('dataset');hard=c[c.model.eq('H0')].set_index('dataset');old=pd.read_csv(OLD/'decision_metrics.csv',usecols=['stage','model','dataset','biological_component','regret']);old=old[old.stage.eq('held_assay')];units=sorted(d.biological_component.unique());wi={u:i for i,u in enumerate(units)};weights=np.random.default_rng(20260928).exponential(1,(5000,len(units)));verdicts=[];gains=[]
    cal=pd.read_csv(ART/'calibration.csv');cal=cal[cal.stage.eq('held_assay')&cal.endpoint.eq('replicate')];cal_checks=[]
    for name in PRIMARY[1:]+SECONDARY:
        rows=[];boot=[];calrows=[]
        for study in STUDIES:
            m=c[c.model.eq(name)&c.dataset.eq(study)].iloc[0];h=hard.loc[study];b=base.loc[study]
            rows.append({'model':name,'dataset':study,'regret':m.regret,'avoidable_wrong':m.avoidable_wrong,'simple_baseline':b['model'],'gain_vs_simple':b.regret-m.regret,'gain_vs_H0':h.regret-m.regret,'avoidable_harm_vs_simple':m.avoidable_wrong-b.avoidable_wrong,'avoidable_harm_vs_H0':m.avoidable_wrong-h.avoidable_wrong})
            aa=d[d.model.eq(name)&d.dataset.eq(study)].groupby('biological_component').regret.mean();bb=old[old.model.eq(b['model'])&old.dataset.eq(study)].groupby('biological_component').regret.mean();assert set(aa.index)==set(bb.index);g=bb.loc[aa.index]-aa;w=weights[:,[wi[u] for u in aa.index]];boot.append(w@g.to_numpy()/w.sum(1))
            q=cal[cal.model.eq(name)&cal.dataset.eq(study)];hh=cal[cal.model.eq('H0')&cal.dataset.eq(study)]
            if len(q) and len(hh):calrows.append({'model':name,'dataset':study,'brier_gain':hh.brier.iloc[0]-q.brier.iloc[0],'logloss_gain':hh.log_loss.iloc[0]-q.log_loss.iloc[0],'ece':q.ece.iloc[0]})
        t=pd.DataFrame(rows);gain=t.gain_vs_simple.to_numpy();risk=t.avoidable_harm_vs_simple.to_numpy();hgain=t.gain_vs_H0.to_numpy();hrisk=t.avoidable_harm_vs_H0.to_numpy();ci=np.quantile(np.mean(boot,axis=0),[.025,.975]);positive=np.maximum(gain,0);share=positive.max()/positive.sum() if positive.sum()>0 else 1.;special=t.dataset.isin([STUDIES[1],'srle'])
        checks={'four_assays':len(t)==4,'macro_regret_at_most_0_468':t.regret.mean()<=.468,'macro_gain_vs_simple_at_least_0_02':gain.mean()>=.02,'three_assays_gain_vs_simple_at_least_0_02':int((gain>=.02).sum())>=3,'three_assays_gain_vs_H0_at_least_0_01':int((hgain>=.01).sum())>=3,'Mikl_SRLE_harm_at_most_0_01_vs_both':bool((t.loc[special,'gain_vs_simple']>=-.01).all() and (t.loc[special,'gain_vs_H0']>=-.01).all()),'no_assay_regret_harm_vs_simple_over_0_05':gain.min()>=-.05,'macro_avoidable_harm_at_most_0_02_vs_both':risk.mean()<=.02 and hrisk.mean()<=.02,'each_avoidable_harm_at_most_0_05_vs_both':risk.max()<=.05 and hrisk.max()<=.05,'leave_best_assay_out_positive':np.delete(gain,np.argmax(gain)).mean()>0,'no_assay_over_60pct_positive_gain':share<=.60,'descriptive_bootstrap_lower_at_least_minus_0_01':ci[0]>=-.01}
        cc=pd.DataFrame(calrows);calpass=len(cc)==3 and cc.brier_gain.mean()>=.005 and cc.logloss_gain.mean()>=.01 and cc.brier_gain.min()>=-.01 and cc.ece.mean()<=.05
        eligible=name in PRIMARY[1:];score=t.regret.mean()+.25*t.avoidable_wrong.mean()+.05*(gain<0).mean()+.10*t.regret.max()
        verdicts.append({'model':name,'primary_selection_eligible':eligible,'passes_decision_checks':all(checks.values()),'passes_primary_gate':eligible and all(checks.values()),'checks':checks,'macro_regret':t.regret.mean(),'macro_gain_vs_H0':hgain.mean(),'macro_gain_vs_simple':gain.mean(),'median_gain_vs_H0':float(np.median(hgain)),'assays_helped_vs_H0':int((hgain>0).sum()),'assays_harmed_vs_H0':int((hgain<0).sum()),'worst_harm_vs_H0':float(max(0,-hgain.min())),'gain_ci_low':ci[0],'gain_ci_high':ci[1],'calibration_claim_gate_passes':bool(calpass),'composite':score});gains.extend(rows);cal_checks.extend(calrows)
    passing=[v for v in verdicts if v['passes_primary_gate']]
    if passing:
        minimum=min(v['composite'] for v in passing);selected=min((v for v in passing if v['composite']<=minimum+1e-12),key=lambda v:PRIMARY.index(v['model']))['model']
    else:selected=None
    jsave(OUT/'gate_verdict.json',{'status':'PASS_TO_SEPARATELY_FROZEN_REPRESENTATION_COMBINATION' if selected else 'NO-GO','selected_model':selected,'models':verdicts,'prior_gate_unchanged':'NO-GO','new_independent_dataset_discovery_allowed':False,'second_experiment_allowed':bool(selected),'criteria_changed_after_results':False,'independent_confirmation':False})
    csvsave(OUT/'per_assay_gains.csv',pd.DataFrame(gains));csvsave(OUT/'calibration_gains.csv',pd.DataFrame(cal_checks))
    raw=pd.read_csv(OUT/'matched_raw_replicate_decisions.csv');summary=macro(raw,['model_regret','uniform_regret','replicate_regret','wrong_direction']);den=summary.uniform_regret-summary.replicate_regret;summary['fraction_recovered']=np.where(den>1e-12,(summary.uniform_regret-summary.model_regret)/den,np.nan);csvsave(OUT/'matched_reproducibility_summary.csv',summary)
    prior=pd.read_csv(ROOT/'results/failure_audit_20260928/replicate_choice_summary.csv').set_index('dataset')
    for row in summary.itertuples():assert abs(row.replicate_regret-prior.loc[row.dataset,'regret'])<1e-12
    reliability=pd.read_csv(ROOT/'results/failure_audit_20260928/replicate_pair_summary.csv').set_index('dataset');assoc=[]
    for name in PRIMARY[1:]:
        g=pd.DataFrame(gains);g=g[g.model.eq(name)&g.dataset.isin(reliability.index)].set_index('dataset');rr=reliability.loc[g.index,'ordering_agreement'];rho=float(spearmanr(rr,g.gain_vs_H0).statistic);assoc.append({'model':name,'assays':len(g),'reliability_vs_gain_spearman':rho,'interpretation':'prespecified descriptive n=3 association, not mechanism or selection criterion'})
    csvsave(OUT/'reliability_gain_association.csv',pd.DataFrame(assoc));print('New generation gate:',selected or 'NO-GO',flush=True)
    print(pd.DataFrame([{k:v for k,v in r.items() if k!='checks'} for r in verdicts]).to_string(index=False),flush=True)
if __name__=='__main__':run()
