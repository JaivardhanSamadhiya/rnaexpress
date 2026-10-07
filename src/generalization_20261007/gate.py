"""Retain the strict transfer gate; never select settings on outer outcomes."""
from .common import *

def run():
    freeze_check()
    old=pd.read_csv(ROOT/'artifacts/cross_assay_20260927/model_comparison.csv')
    old=old[old.stage.eq('held_assay')].set_index(['model','dataset'])
    simple={s:min(float(old.loc[m,s].regret) for m in ['uniform','metadata','composition']) for s in STUDIES}
    h0={s:float(old.loc['interaction_3',s].regret) for s in STUDIES}
    simple_wrong={}
    for s in STUDIES:
        m=min(['uniform','metadata','composition'],key=lambda m:(float(old.loc[m,s].regret),float(old.loc[m,s].avoidable_wrong),m))
        simple_wrong[s]=float(old.loc[m,s].avoidable_wrong)
    results=[]
    all_decisions=[]
    prior=pd.read_csv(ROOT/'results/cross_assay_20260927/decision_metrics.csv')
    prior=prior[prior.stage.eq('held_assay')]
    for track in TRACKS:
        assert readj(OUT/track/'run_complete.json')['status']=='PASS'
        comp=pd.read_csv(OUT/track/'comparison.csv').set_index('dataset')
        d=pd.read_csv(OUT/track/'decisions.csv');all_decisions.append(d)
        g=np.array([simple[s]-float(comp.loc[s].regret) for s in STUDIES])
        gh=np.array([h0[s]-float(comp.loc[s].regret) for s in STUDIES])
        wrong=np.array([float(comp.loc[s].avoidable_wrong)-simple_wrong[s] for s in STUDIES])
        wrong_h=np.array([float(comp.loc[s].avoidable_wrong)-float(old.loc['interaction_3',s].avoidable_wrong) for s in STUDIES])
        positive=np.maximum(g,0)
        share=float(positive.max()/positive.sum()) if positive.sum()>0 else 1.
        # Same equal-source descriptive component bootstrap as prior generation.
        rng=np.random.default_rng(SEED)
        boot=np.zeros(5000)
        for s in STUDIES:
            selected=min(['uniform','metadata','composition'],key=lambda m:(float(old.loc[m,s].regret),float(old.loc[m,s].avoidable_wrong),m))
            a=prior[prior.dataset.eq(s)&prior.model.eq(selected)].groupby('biological_component').regret.mean()
            b=d[d.dataset.eq(s)].groupby('biological_component').regret.mean()
            assert set(a.index)==set(b.index)
            values=(a-b.reindex(a.index)).to_numpy()
            weights=rng.exponential(1,size=(5000,len(values)));weights/=weights.sum(1,keepdims=True)
            boot+=weights@values/4
        checks={
            'macro_regret_at_most_0_468':float(comp.regret.mean())<=.468,
            'macro_gain_vs_simple_at_least_0_02':float(g.mean())>=.02,
            'three_assays_gain_vs_simple_at_least_0_02':int((g>=.02).sum())>=3,
            'three_assays_gain_vs_H0_at_least_0_01':int((gh>=.01).sum())>=3,
            'Mikl_SRLE_harm_at_most_0_01_vs_both':all(float(comp.loc[s].regret)<=min(simple[s],h0[s])+.01 for s in ['mikl_gse173098','srle']),
            'any_assay_harm_vs_simple_at_most_0_05':bool((g>=-.05).all()),
            'macro_avoidable_harm_at_most_0_02_vs_both':max(float(wrong.mean()),float(wrong_h.mean()))<=.02,
            'each_avoidable_harm_at_most_0_05_vs_both':max(float(wrong.max()),float(wrong_h.max()))<=.05,
            'leave_best_assay_out_positive':float(np.delete(g,np.argmax(g)).mean())>0,
            'max_positive_gain_share_at_most_0_60':share<=.6,
            'descriptive_bootstrap_lower_at_least_minus_0_01':float(np.quantile(boot,.025))>=-.01}
        results.append({'track':track,'passes':all(checks.values()),'checks':checks,
            'macro_regret':float(comp.regret.mean()),'macro_gain_vs_H0':float(gh.mean()),
            'macro_gain_vs_simple':float(g.mean()),'assays_helped_vs_H0':int((gh>0).sum()),
            'assays_harmed_vs_H0':int((gh<0).sum()),'worst_harm_vs_H0':float(-gh.min()),
            'gain_ci':[float(np.quantile(boot,.025)),float(np.quantile(boot,.975))],
            'per_assay':[{ 'dataset':s,'regret':float(comp.loc[s].regret),'gain_vs_H0':float(gh[i]),
                'gain_vs_simple':float(g[i]),'avoidable_wrong':float(comp.loc[s].avoidable_wrong)} for i,s in enumerate(STUDIES)]})
    jsave(OUT/'gate_verdict.json',{'status':'DEVELOPMENT_GO' if any(r['passes'] for r in results) else 'NO-GO',
        'tracks':results,'criteria_changed_after_results':False,'independent_confirmation':False,
        'future_probabilities':'No calibrated probability or absolute-benefit claim; no abstention is tested',
        'multiple_routes':'Five declared comparisons on a repeatedly exposed benchmark; gate is a development filter, not novelty or confirmation'})
    csvsave(ART/'model_comparison.csv',pd.concat([pd.read_csv(OUT/t/'comparison.csv') for t in TRACKS],ignore_index=True))
    csvsave(ART/'decision_metrics.csv.gz',pd.concat(all_decisions,ignore_index=True),True)
    print(readj(OUT/'gate_verdict.json')['status'],flush=True)

if __name__=='__main__':run()
