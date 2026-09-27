"""Fixed full-roster diagnostics; no fit, tuning, exclusion or deployed confidence rule."""
from .common import *
from scipy.stats import spearmanr
from math import comb

PRIMARY='purged_composition_holdout'
METRICS=['published_regret','published_correct_direction','published_wrong_direction','published_best_choice','wrong_both','correct_both','replicate_opposite','beats_uniform','top3_best_recovery']

def bins(a):
    return pd.cut(np.abs(a),[-np.inf,.1,.25,.5,np.inf],labels=['<=0.1','0.1-0.25','0.25-0.5','>0.5']).astype(str)

def corr(a,b,rank=False):
    return float(spearmanr(a,b).statistic if rank else np.corrcoef(a,b)[0,1]) if np.ptp(a)>TOL and np.ptp(b)>TOL else np.nan

def run():
    source,effects,choices,fits,roster=load()
    diag=pd.read_csv(ART/'edit_prediction_diagnostics.csv',dtype={'group':str},float_precision='round_trip')
    feat=pd.read_csv(ART/'edit_features.csv',dtype={'group':str},float_precision='round_trip')
    near=pd.read_csv(ART/'nearest_training_sequences.csv',dtype={'group':str},float_precision='round_trip').set_index('sequence')
    candidates=pd.read_csv(OLDART/'srle_candidate_selection.csv',dtype={'group':str},float_precision='round_trip')
    candidates['decision_unit_id']=candidates.parent+'|'+candidates.direction.astype(str)
    candidates['selected_increase']=candidates.selected & candidates.direction.eq(1)
    candidates['selected_decrease']=candidates.selected & candidates.direction.eq(-1)
    candidates['selection_probability']=candidates.selected.astype(float)
    candidates['rep1_direction']=sign(candidates.rep1_delta)
    candidates['rep2_direction']=sign(candidates.rep2_delta)
    for field in ('hamming','levenshtein','nearest_2mer_l1','nearest_3mer_l1','out_of_range_2mer_features'):
        for endpoint in ('parent','candidate'):
            candidates[endpoint+'_'+field]=candidates[endpoint].map(near[field]).where(candidates.evaluation_split.eq(PRIMARY))
    candidates['distance_scope']='strict-purge training only; NA for other splits'
    dc=[c for c in feat if c.startswith('delta_2mer_')]
    candidates=candidates.merge(feat[['parent','candidate']+dc],on=['parent','candidate'],validate='many_to_one')
    uni=candidates[candidates.model_name.eq('composition')].copy()
    uni['model_name']='uniform';uni['predicted_delta']=np.nan;uni['predicted_value']=np.nan;uni['predicted_rank']=np.nan
    uni['selected']=False;uni['selected_increase']=False;uni['selected_decrease']=False
    uni['selection_probability']=1/uni.groupby(['evaluation_split','parent','direction']).candidate.transform('size')
    candidates=pd.concat([candidates,uni],ignore_index=True)
    csvsave(ART/'all_candidate_recommendations.csv',candidates)
    strict=candidates[candidates.evaluation_split.eq(PRIMARY)].copy()
    d=choices[choices.scheme.eq(PRIMARY)].copy()
    extra=[];bench=[];ranks=[];potential=[]
    bypred=effects[effects.scheme.eq(PRIMARY)].pivot(index=['parent','candidate'],columns='model',values='predicted_delta')
    for (parent,direction),g0 in strict[strict.model_name.eq('composition')].groupby(['parent','direction']):
        g0=g0.sort_values('candidate');n=len(g0);group=g0.group.iloc[0]
        a=direction*g0.rep1_delta.to_numpy();b=direction*g0.rep2_delta.to_numpy();y=direction*g0.measured_delta.to_numpy()
        cb=(a>TOL)&(b>TOL);wb=(a<-TOL)&(b<-TOL)
        potential.append({'parent':parent,'direction':direction,'group':group,'any_correct_both':float(cb.any()),'any_avoids_wrong_both':float((~wb).any()),'all_wrong_both':float(wb.all()),'candidate_count':n})
        i1=int(np.argmax(a));i2=int(np.argmax(b))
        ranks.append({'parent':parent,'direction':direction,'group':group,'candidate_count':n,'rank_spearman':corr(a,b,True),
                      'preferred_differs':float(i1!=i2),'best_sets_overlap':float(np.any((a==a.max())&(b==b.max())))})
        for use,truth,ix,label in [(a,b,i1,'rep1_select_rep2_evaluate'),(b,a,i2,'rep2_select_rep1_evaluate')]:
            bench.append({'parent':parent,'direction':direction,'group':group,'benchmark':label,'selected':g0.candidate.iloc[ix],
                'regret':(truth.max()-truth[ix])/np.ptp(truth),'correct_direction':float(truth[ix]>TOL),'wrong_direction':float(truth[ix]<-TOL),'best_recovery':float(truth[ix]==truth.max()),
                'wrong_both':float(wb[ix]),'not_an_absolute_ceiling':True})
    potential=pd.DataFrame(potential);csvsave(OUT/'candidate_feasibility.csv',potential)
    ranks=pd.DataFrame(ranks);csvsave(OUT/'replicate_candidate_ranks.csv',ranks)
    csvsave(OUT/'replicate_rank_summary.csv',group_summary(ranks,['rank_spearman','preferred_differs','best_sets_overlap']))
    bench=pd.DataFrame(bench);csvsave(OUT/'replicate_choice_benchmarks.csv',bench)
    csvsave(OUT/'replicate_choice_summary.csv',group_summary(bench,['regret','correct_direction','wrong_direction','best_recovery','wrong_both'],['benchmark']))
    csvsave(OUT/'candidate_feasibility_summary.csv',group_summary(potential,['any_correct_both','any_avoids_wrong_both','all_wrong_both']))
    grouped={(m,p,int(s)):g.sort_values('predicted_rank',kind='stable') for (m,p,s),g in strict.groupby(['model_name','parent','direction'])}
    feasibility=potential.set_index(['parent','direction'])
    uniform=d[d.model.eq('uniform')].set_index(['parent','direction'])
    for row in d.itertuples():
        g=grouped[row.model,row.parent,int(row.direction)];n=len(g);f=feasibility.loc[row.parent,row.direction]
        truth=row.direction*g.measured_delta.to_numpy();regrets=(truth.max()-truth)/np.ptp(truth)
        u=float(uniform.loc[(row.parent,row.direction),'published_regret'])
        if row.model=='uniform':
            m=int((truth==truth.max()).sum());top=1-comb(n-m,3)/comb(n,3) if n>3 and n-m>=3 else (1. if n>3 else np.nan)
            beat=float(np.mean(regrets<u-TOL));margin=effect=agreement=distance=extrap=np.nan
            ca=float(np.mean(g.wrong_both))*float(f.any_correct_both)
            cb=float(np.mean(g.wrong_both))*float(not f.any_correct_both and f.any_avoids_wrong_both)
            cc=float(np.mean(g.wrong_both))*float(f.all_wrong_both)
            mag=float(np.mean(np.abs(g.measured_delta)))
        else:
            chosen=g[g.selected].iloc[0];assert chosen.candidate==row.selected
            top=float(g.head(3).measured_rank.eq(1).any()) if n>3 else np.nan
            beat=float(row.published_regret<u-TOL)
            scores=row.direction*g.predicted_delta.to_numpy();margin=float(scores[0]-scores[1]);effect=float(scores[0])
            pr=bypred.loc[row.parent,row.selected];agreement=-abs(pr['2mer']-pr['3mer'])
            distance=-max(near.loc[row.parent,'nearest_2mer_l1'],near.loc[row.selected,'nearest_2mer_l1'])
            extrap=-max(near.loc[row.parent,'out_of_range_2mer_features'],near.loc[row.selected,'out_of_range_2mer_features'])
            ca=row.wrong_both*float(f.any_correct_both);cb=row.wrong_both*float(not f.any_correct_both and f.any_avoids_wrong_both);cc=row.wrong_both*float(f.all_wrong_both)
            assert abs(ca+cb+cc-row.wrong_both)<TOL
            mag=abs(chosen.measured_delta)
        extra.append({'model':row.model,'parent':row.parent,'direction':row.direction,'beats_uniform':beat,'top3_best_recovery':top,
            'signal_margin':margin,'signal_directional_effect':effect,'signal_model_agreement':agreement,'signal_feature_distance':distance,'signal_extrapolation':extrap,
            'wrong_both_correct_alternative':ca,'wrong_both_ambiguous_alternative':cb,'wrong_both_unavoidable':cc,'measured_selected_magnitude':mag})
    d=d.merge(pd.DataFrame(extra),on=['model','parent','direction'],validate='one_to_one')
    d['measured_magnitude_bin']=bins(d.measured_selected_magnitude)
    csvsave(ART/'recommendation_decisions.csv',d)
    summaries=group_summary(d,METRICS+['wrong_both_correct_alternative','wrong_both_ambiguous_alternative','wrong_both_unavoidable'],['model'])
    csvsave(OUT/'recommendation_summary.csv',summaries)
    csvsave(OUT/'recommendation_by_size.csv',group_summary(d,METRICS,['model','candidates']))
    csvsave(OUT/'recommendation_by_magnitude.csv',group_summary(d[d.model.ne('uniform')],METRICS,['model','measured_magnitude_bin']))
    csvsave(OUT/'recommendation_by_direction.csv',group_summary(d,METRICS,['model','direction']))
    dist=[];distribution=[]
    for model,g in strict.groupby('model_name'):
        for (parent,direction),h in g.groupby(['parent','direction']):
            truth=direction*h.measured_delta.to_numpy();r=(truth.max()-truth)/np.ptp(truth)
            for (_,row),regret in zip(h.iterrows(),r):
                if row.selection_probability>0:distribution.append({'model':model,'parent':parent,'direction':direction,'group':row.group,'candidate':row.candidate,'regret':regret,'weight':row.selection_probability})
    distribution=pd.DataFrame(distribution);csvsave(OUT/'regret_distribution.csv',distribution)
    for model,g in distribution.groupby('model'):
        g=g.sort_values('regret');cdf=g.weight.cumsum()/g.weight.sum()
        row={'model':model,'scope':'equal decision mass, uniform exact mixture; not class-balanced quantiles'}
        for p in (.1,.25,.5,.75,.9):row['q'+str(int(p*100))]=float(g.regret.iloc[min(np.searchsorted(cdf,p),len(g)-1)])
        dist.append(row)
    csvsave(OUT/'regret_quantiles.csv',pd.DataFrame(dist))
    coverage=[]
    for model in ('2mer','kmer123'):
        g=d[d.model.eq(model)]
        for signal in [c for c in d if c.startswith('signal_')]:
            ordered=g.sort_values([signal,'parent','direction'],ascending=[False,True,True]);assert ordered[signal].notna().all()
            for frac in (1.,.8,.6,.4,.2):
                subset=ordered.iloc[:int(np.ceil(len(g)*frac))]
                row=group_summary(subset,METRICS).iloc[0].to_dict()
                row.update(model=model,signal=signal,requested_coverage=frac,actual_coverage=len(subset)/len(g),threshold=float(subset[signal].iloc[-1]),signal_unique_values=g[signal].nunique(),status='exploratory; fixed prediction-only ranking, lexicographic ties; no deployed threshold')
                coverage.append(row)
    csvsave(OUT/'confidence_coverage.csv',pd.DataFrame(coverage))
    # Full-edge failure diagnostics, retaining every frozen model and edge.
    diag['measured_magnitude_bin']=bins(diag.published_delta);diag['predicted_magnitude_bin']=bins(diag.predicted_delta)
    diag['replicate_disagreement_bin']=bins(diag.rep1_delta-diag.rep2_delta)
    diag['replicate_sign_agreement']=(sign(diag.rep1_delta)==sign(diag.rep2_delta)).astype(float)
    diag['candidate_count']=diag.parent.map(roster.groupby('parent').size())
    diag['C_count']=diag.parent.str.count('C');diag=diag.merge(feat[['parent','candidate','delta2_zero','delta3_zero']+dc],on=['parent','candidate'],validate='many_to_one')
    csvsave(ART/'full_failure_diagnostics.csv',diag)
    failures=[]
    for factor in ['measured_magnitude_bin','predicted_magnitude_bin','replicate_disagreement_bin','replicate_sign_agreement','candidate_count','C_count','changed_position_span','delta2_zero','group','maximum_out_of_range_2mer_features']:
        for (model,level),g in diag.groupby(['model',factor]):
            failures.append({'model':model,'factor':factor,'level':str(level),'edges':len(g),'groups':g.group.nunique(),'mae':g.absolute_error.mean(),'sign_accuracy':g.strict_sign_correct.mean(),'replicate_sign_agreement':g.replicate_sign_agreement.mean(),'status':'descriptive; no posthoc exclusion'})
    csvsave(OUT/'failure_strata.csv',pd.DataFrame(failures))
    continuous=[]
    for model,g in diag.groupby('model'):
        for factor in ['minimum_hamming','minimum_levenshtein','minimum_nearest_2mer_l1','minimum_nearest_3mer_l1','maximum_nearest_2mer_cosine_distance','maximum_out_of_range_2mer_features']:
            continuous.append({'model':model,'factor':factor,'unique_values':g[factor].nunique(),'spearman_absolute_error':corr(g[factor],g.absolute_error,True),'interpretation':'descriptive correlated edges; constant predictor has no estimable gradient'})
    csvsave(OUT/'similarity_continuous.csv',pd.DataFrame(continuous))
    rr=roster.copy();rr['sign_agreement']=(sign(rr.rep1_delta)==sign(rr.rep2_delta)).astype(float);rr['magnitude_bin']=bins(rr.published_delta)
    rs=[]
    for level,g in [('all',rr)]+list(rr.groupby('magnitude_bin')):
        stat=group_summary(g,['sign_agreement']).iloc[0].to_dict()
        stat.update(magnitude_bin=level,pearson=corr(g.rep1_delta,g.rep2_delta),spearman=corr(g.rep1_delta,g.rep2_delta,True),edge_sign_agreement=g.sign_agreement.mean())
        rs.append(stat)
    csvsave(OUT/'replicate_effect_reliability.csv',pd.DataFrame(rs))
    examples=[]
    k=d[d.model.eq('kmer123')].copy();k['average_replicate_regret']=(k.rep1_regret+k.rep2_regret)/2
    for direction in (-1,1):
        for label,field in [('success','correct_both'),('failure','wrong_both')]:
            sub=k[k.direction.eq(direction)&k[field].eq(1)].copy()
            sub['distance_to_median']=abs(sub.average_replicate_regret-sub.average_replicate_regret.median())
            row=sub.sort_values(['distance_to_median','parent','selected']).iloc[0].to_dict();row['example_type']=label;examples.append(row)
    csvsave(OUT/'representative_examples.csv',pd.DataFrame(examples))
    jsave(OUT/'recommendation_receipt.json',{'status':'PASS','all_split_candidate_rows_including_uniform':len(candidates),'strict_candidate_rows_including_uniform':len(strict),'strict_decision_rows':len(d),'coverage_rows':len(coverage),'new_models_fitted':0,'posthoc_exclusions':0,'biological_contexts':1})
    print(summaries[['model','published_regret','wrong_both','beats_uniform']].to_string(index=False))

if __name__=='__main__':run()
