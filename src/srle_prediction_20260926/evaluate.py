from .core import *
from scipy.stats import spearmanr, rankdata


def summary(values):
    values=np.asarray(values,float)
    draws=bootstrap_counts(len(values))
    return float(values.mean()),*np.quantile(draws@values/len(values),[.025,.975]).tolist()


def sufficient(y,p):
    sy=np.where(np.abs(y)<=TOL,0,np.sign(y));sp=np.where(np.abs(p)<=TOL,0,np.sign(p))
    valid=sy!=0;correct=(sp==sy)&valid;half=correct.astype(float)+.5*((sp==0)&valid)
    return np.column_stack([np.ones(len(y)),y,p,y*y,p*p,y*p,(y-p)**2,np.abs(y-p),correct,valid,half,
        half*(sy>0),sy>0,half*(sy<0),sy<0])


def calculate(s):
    n,sy,sp,syy,spp,syp,sse,sae,correct,valid,half,poshalf,posn,neghalf,negn=s.T
    vary=syy-sy*sy/n;varp=spp-sp*sp/n
    with np.errstate(divide='ignore',invalid='ignore'):
        return {'mae':sae/n,'rmse':np.sqrt(sse/n),'mse':sse/n,'r2':1-sse/vary,
            'pearson':np.where(varp>1e-14,(syp-sy*sp/n)/np.sqrt(vary*varp),np.nan),
            'sign_accuracy_strict':correct/valid,'pairwise_accuracy_tie_half':half/valid,
            'balanced_accuracy_tie_half':.5*(poshalf/posn+neghalf/negn),
            'calibration_slope':np.where(varp>1e-14,(syp-sy*sp/n)/varp,np.nan)}


def score_tables(frame,kind):
    metrics=[];comparison=[]
    for (scheme,target),part in frame.groupby(['scheme','target']):
        cached={}
        for model,g in part.groupby('model'):
            groups=sorted(g.group.unique());ix=pd.Categorical(g.group,categories=groups).codes
            y=g.measured.to_numpy();p=g.predicted.to_numpy();raw=sufficient(y,p)
            stats=np.zeros((len(groups),raw.shape[1]));np.add.at(stats,ix,raw)
            boot=bootstrap_counts(len(groups))@stats
            point=calculate(stats.sum(0,keepdims=True));interval=calculate(boot)
            row={'kind':kind,'scheme':scheme,'target':target,'model':model,'observations':len(g),'statistical_groups':len(groups),'biological_contexts':1}
            for name,v in point.items():
                row[name]=float(v[0]);finite=interval[name][np.isfinite(interval[name])]
                lo,hi=np.quantile(finite,[.025,.975]) if len(finite) else [np.nan,np.nan]
                row[name+'_ci_low']=lo;row[name+'_ci_high']=hi
            row['spearman_descriptive']=float(spearmanr(y,p).statistic) if np.ptp(y)>TOL and np.ptp(p)>TOL else np.nan
            metrics.append(row);cached[model]=(groups,stats,boot)
        for model,(groups,stats,boot) in cached.items():
            for baseline in MODELS:
                if baseline==model:continue
                bg,bs,bb=cached[baseline];assert bg==groups
                with np.errstate(divide='ignore',invalid='ignore'):
                    gain=1-stats[:,6].sum()/bs[:,6].sum();draw=1-boot[:,6]/bb[:,6]
                finite=draw[np.isfinite(draw)];lo,hi=np.quantile(finite,[.025,.975]) if len(finite) else [np.nan,np.nan]
                comparison.append({'kind':kind,'scheme':scheme,'target':target,'model':model,'comparator':baseline,
                    'relative_mse_reduction':gain,'ci_low':lo,'ci_high':hi,'statistical_groups':len(groups),'biological_contexts':1})
    return pd.DataFrame(metrics),pd.DataFrame(comparison)


def build_effects(pred,roster):
    rows=[]
    for (scheme,model),g in pred.groupby(['scheme','model']):
        lookup=g.set_index('kmer').predicted_score
        part=roster.copy();part['scheme']=scheme;part['model']=model
        part['predicted_parent']=part.parent.map(lookup);part['predicted_candidate']=part.candidate.map(lookup)
        part['predicted_delta']=part.predicted_candidate-part.predicted_parent
        assert np.isfinite(part.predicted_delta).all()
        rows.append(part)
    return pd.concat(rows,ignore_index=True)


def decision_tables(effects):
    decisions=[];candidates=[]
    for (scheme,model,parent),g in effects.groupby(['scheme','model','parent'],sort=True):
        g=g.sort_values('candidate').reset_index(drop=True);group=g.group.iloc[0]
        for direction in (-1,1):
            predicted=direction*g.predicted_delta.to_numpy();chosen=int(np.argmax(predicted))
            order=np.argsort(-predicted,kind='stable');prank=np.empty(len(g),int);prank[order]=np.arange(1,len(g)+1)
            row={'scheme':scheme,'model':model,'parent':parent,'group':group,'direction':direction,
                'selected':g.candidate.iloc[chosen],'candidates':len(g),'predicted_delta':g.predicted_delta.iloc[chosen]}
            uniform={**row,'model':'uniform','selected':'expected_uniform_choice','predicted_delta':np.nan}
            ranks={}
            for target in ('published','rep1','rep2'):
                y=g[target+'_delta'].to_numpy();truth=direction*y;assert np.ptp(truth)>0
                rank=rankdata(-truth,method='min');ranks[target]=rank
                regret=(truth.max()-truth)/np.ptp(truth)
                fields={'regret':regret,'correct_direction':(truth>TOL).astype(float),
                        'wrong_direction':(truth<-TOL).astype(float),'tie':(np.abs(truth)<=TOL).astype(float),
                        'best_choice':(rank==1).astype(float),'measured_delta':y}
                for name,values in fields.items():
                    row[target+'_'+name]=float(values[chosen]);uniform[target+'_'+name]=float(values.mean())
            a=direction*g.rep1_delta.to_numpy();b=direction*g.rep2_delta.to_numpy()
            paired={'wrong_both':(a<-TOL)&(b<-TOL),'correct_both':(a>TOL)&(b>TOL),
                'replicate_opposite':((a>TOL)&(b<-TOL))|((a<-TOL)&(b>TOL))}
            for name,values in paired.items():row[name]=float(values[chosen]);uniform[name]=float(values.mean())
            decisions.append(row)
            if model=='composition':decisions.append(uniform)
            for i,r in g.iterrows():
                candidates.append({'evaluation_split':scheme,'model_name':model,'parent':parent,'context':r.biological_context,
                    'group':group,'candidate':r.candidate,'sequence':r.candidate,'parent_sequence':parent,
                    'changed_positions':r.changed_positions_1based,'edited_window_length':6,'changed_bases':2,
                    'direction':direction,'measured_value':r.candidate_published,'predicted_value':r.predicted_candidate,
                    'measured_delta':r.published_delta,'predicted_delta':r.predicted_delta,
                    'rep1_delta':r.rep1_delta,'rep2_delta':r.rep2_delta,
                    'predicted_rank':int(prank[i]),'measured_rank':float(ranks['published'][i]),
                    'rep1_measured_rank':float(ranks['rep1'][i]),'rep2_measured_rank':float(ranks['rep2'][i]),
                    'selected':i==chosen,'correct_direction':bool(direction*r.published_delta>TOL),
                    'rep1_correct_direction':bool(direction*r.rep1_delta>TOL),'rep2_correct_direction':bool(direction*r.rep2_delta>TOL),
                    'wrong_both':bool(paired['wrong_both'][i]),'provenance_status':'PARTIAL; same experiment constituent replicates'})
    return pd.DataFrame(decisions),pd.DataFrame(candidates)


def summarize_decisions(decisions):
    values=[c for c in decisions if c.endswith(('_regret','_correct_direction','_wrong_direction','_tie','_best_choice'))]+['wrong_both','correct_both','replicate_opposite']
    records=[];contrasts=[]
    for direction in (-1,1,0):
        d=decisions if direction==0 else decisions[decisions.direction.eq(direction)]
        table=d.groupby(['scheme','model','group'])[values].mean().reset_index()
        for (scheme,model),g in table.groupby(['scheme','model']):
            row={'scheme':scheme,'model':model,'direction':direction,'statistical_groups':len(g),'biological_contexts':1}
            for name in values:
                value,lo,hi=summary(g[name]);row[name]=value;row[name+'_ci_low']=lo;row[name+'_ci_high']=hi
            records.append(row)
        for scheme,g in table.groupby('scheme'):
            for model in MODELS:
                primary=g[g.model.eq(model)].set_index('group').sort_index()
                for comparator in ('uniform','composition','kmer123','position_pair'):
                    if model==comparator:continue
                    base=g[g.model.eq(comparator)].set_index('group').loc[primary.index]
                    for name in ('published_regret','rep1_regret','rep2_regret','wrong_both'):
                        gain=base[name]-primary[name];v,lo,hi=summary(gain)
                        contrasts.append({'scheme':scheme,'direction':direction,'model':model,'comparator':comparator,
                            'metric':name,'gain':v,'ci_low':lo,'ci_high':hi,'fraction_groups_improved':float((gain>TOL).mean()),
                            'statistical_groups':len(primary),'biological_contexts':1})
    return pd.DataFrame(records),pd.DataFrame(contrasts)


def failure_tables(effects,decisions):
    g=effects[effects.scheme.eq('purged_composition_holdout')&effects.model.eq('position_pair')].copy()
    g['absolute_error']=np.abs(g.predicted_delta-g.published_delta)
    g['direction_error']=(np.sign(g.predicted_delta)!=np.sign(g.published_delta)).astype(float)
    g['replicate_disagreement']=(np.sign(g.rep1_delta)!=np.sign(g.rep2_delta)).astype(float)
    g['magnitude_bin']=pd.cut(np.abs(g.published_delta),[-np.inf,.1,.25,.5,np.inf],labels=['<=0.1','0.1-0.25','0.25-0.5','>0.5'])
    g['replicate_difference_bin']=pd.cut(np.abs(g.rep1_delta-g.rep2_delta),[-np.inf,.1,.25,.5,np.inf],labels=['<=0.1','0.1-0.25','0.25-0.5','>0.5'])
    g['C_count']=g.parent.str.count('C');g['CCC_any']=g.parent.str.contains('CCC')|g.candidate.str.contains('CCC')
    records=[]
    for factor in ('magnitude_bin','replicate_difference_bin','C_count','CCC_any','changed_position_span','replicate_disagreement'):
        for level,h in g.groupby(factor,observed=True):
            records.append({'factor':factor,'level':str(level),'candidate_edges':len(h),'groups':h.group.nunique(),
                'mae':h.absolute_error.mean(),'direction_error':h.direction_error.mean(),
                'scope':'descriptive overlapping edges; no filter or threshold is used to change main results'})
    chosen=decisions[decisions.scheme.eq('purged_composition_holdout')&decisions.model.eq('position_pair')].copy()
    chosen['average_replicate_regret']=(chosen.rep1_regret+chosen.rep2_regret)/2
    examples=[]
    for direction in (-1,1):
        part=chosen[chosen.direction.eq(direction)]
        for label,subset in [('median',part),('representative_wrong_both',part[part.wrong_both.eq(1)])]:
            if subset.empty:continue
            subset=subset.assign(distance_to_median=np.abs(subset.average_replicate_regret-subset.average_replicate_regret.median()))
            r=subset.sort_values(['distance_to_median','parent','selected']).iloc[0].to_dict();r['selection_rule']=label;examples.append(r)
    return pd.DataFrame(records),pd.DataFrame(examples)


def run():
    receipt=readj(OUT/'fit_receipt.json')
    for p,h in receipt['outputs'].items():assert sha256(ROOT/p)==h
    pred=pd.read_csv(ART/'srle_heldout_predictions.csv',dtype={'group':str},float_precision='round_trip')
    roster=pd.read_csv(ART/'srle_observation_inventory.csv',dtype={'group':str,'composition_before':str,'composition_after':str},float_precision='round_trip')
    effects=build_effects(pred,roster);csvsave(OUT/'edit_effect_predictions.csv',effects)
    score_rows=[];effect_rows=[]
    for target,column in [('published','nrs'),('rep1','NRS1'),('rep2','NRS2')]:
        a=pred[['scheme','model','group',column,'predicted_score']].rename(columns={column:'measured','predicted_score':'predicted'});a['target']=target;score_rows.append(a)
        b=effects[['scheme','model','group',target+'_delta','predicted_delta']].rename(columns={target+'_delta':'measured','predicted_delta':'predicted'});b['target']=target;effect_rows.append(b)
    metrics=[];comparisons=[]
    for kind,frames in [('score',score_rows),('edit_delta',effect_rows)]:
        a,b=score_tables(pd.concat(frames,ignore_index=True),kind);metrics.append(a);comparisons.append(b)
    csvsave(OUT/'prediction_metrics.csv',pd.concat(metrics,ignore_index=True))
    csvsave(OUT/'prediction_comparisons.csv',pd.concat(comparisons,ignore_index=True))
    decisions,candidates=decision_tables(effects)
    csvsave(ART/'srle_candidate_selection.csv',candidates)
    csvsave(ART/'heldout_candidate_predictions.csv',candidates)
    csvsave(OUT/'decision_rows.csv',decisions)
    a,b=summarize_decisions(decisions);csvsave(OUT/'decision_metrics.csv',a);csvsave(OUT/'decision_comparisons.csv',b)
    failures,examples=failure_tables(effects,decisions)
    csvsave(OUT/'failure_analysis.csv',failures);csvsave(OUT/'example_choices.csv',examples)
    old=pd.read_csv(OLD/'raw_swap_evaluation.csv')
    original=decisions[decisions.scheme.eq('sequence_holdout')&decisions.model.isin(old.model.unique())]
    matches=old.merge(original,on=['parent','model','direction'],suffixes=('_old','_new'),validate='many_to_one')
    assert len(matches)==len(old) and (matches.selected_old==matches.selected_new).all()
    jsave(OUT/'evaluation_receipt.json',{'status':'PASS','candidate_rows':len(candidates),'decision_rows':len(decisions),
        'historical_choices_reproduced':len(matches),'biological_contexts':1,'models_reselected':False,
        'scope':'Exploratory fixed sequence-group audit on already-exposed data; no independent validation',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in (OUT/'prediction_metrics.csv',OUT/'prediction_comparisons.csv',ART/'srle_candidate_selection.csv',OUT/'decision_metrics.csv')}})
    print(pd.concat(metrics).query("kind == 'edit_delta' and target == 'published' and model in ['composition','kmer123','position_pair']")[['scheme','model','rmse','pearson','sign_accuracy_strict']].to_string(index=False),flush=True)


if __name__=='__main__':run()
