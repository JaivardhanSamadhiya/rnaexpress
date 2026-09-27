from .common import *
from src.research_20260921.robustness import count_features
import itertools

VOCAB={k:[''.join(x) for x in itertools.product('ACGT',repeat=k)] for k in (1,2,3)}


def run():
    source,effects,choices,fits,roster=load()
    x=count_features(source.kmer.to_numpy());lookup={s:i for i,s in enumerate(source.kmer)}
    pi=np.array([lookup[s] for s in roster.parent]);ci=np.array([lookup[s] for s in roster.candidate]);delta=x[ci]-x[pi]
    assert np.all(delta[:,:4]==0)
    for row in roster.itertuples():
        changed=[i for i,(a,b) in enumerate(zip(row.parent,row.candidate)) if a!=b]
        assert len(changed)==2
        i,j=changed;assert row.parent[i]==row.candidate[j] and row.parent[j]==row.candidate[i]
    pair=roster.copy();feature_columns={}
    for k,start,end in ((1,0,4),(2,4,20),(3,20,84)):
        for j,feature in enumerate(VOCAB[k],start):
            feature_columns[f'parent_{k}mer_{feature}']=x[pi,j];feature_columns[f'candidate_{k}mer_{feature}']=x[ci,j];feature_columns[f'delta_{k}mer_{feature}']=delta[:,j]
    pair=pd.concat([pair,pd.DataFrame(feature_columns)],axis=1)
    pair['delta2_zero']=np.all(delta[:,4:20]==0,axis=1);pair['delta3_zero']=np.all(delta[:,20:84]==0,axis=1)
    selected=effects[effects.scheme.eq('purged_composition_holdout')]
    for model in ('2mer','3mer','kmer123','position_pair'):
        table=selected[selected.model.eq(model)].set_index(['parent','candidate']).predicted_delta
        pair['pred_'+model]=[table.loc[(a,b)] for a,b in zip(pair.parent,pair.candidate)]
    coefficients=[];beta={}
    for fit in fits:
        c=fit['coefficients']['2mer'];raw=np.array(c['coefficient'])/np.array(c['scale']);centered=raw-raw.mean()
        for j,feature in enumerate(VOCAB[2]):
            coefficients.append({'scheme':fit['scheme'],'held_group':fit['held_group'],'feature':feature,
                'standardized_coefficient':c['coefficient'][j],'training_scale':c['scale'][j],
                'count_coefficient':raw[j],'centered_count_coefficient':centered[j],
                'frequency_all_sequences':float(np.mean(x[:,4+j]>0)),
                'frequency_original_training':float(np.mean(x[~source.test,4+j]>0)),
                'frequency_scored_sequences':float(np.mean(x[source.scored,4+j]>0))})
        if fit['scheme']=='purged_composition_holdout':beta[fit['held_group']]=(raw,centered)
    table=pd.DataFrame(coefficients);csvsave(OUT/'coefficient_folds.csv',table)
    stable=[]
    for (scheme,feature),g in table.groupby(['scheme','feature']):
        a=g.centered_count_coefficient.to_numpy()
        stable.append({'scheme':scheme,'feature':feature,'overlapping_fits':len(g),
            'median_centered_coefficient':np.median(a),'q25':np.quantile(a,.25),'q75':np.quantile(a,.75),
            'min':a.min(),'max':a.max(),'positive_fraction':np.mean(a>TOL),'negative_fraction':np.mean(a<-TOL),
            'uncertainty_status':'fold distribution, not independent confidence interval'})
    csvsave(OUT/'coefficient_stability.csv',pd.DataFrame(stable))
    contributions=[];errors=[]
    for i,row in pair.iterrows():
        raw,centered=beta[row.group];change=delta[i,4:20];pieces=change*raw;cpieces=change*centered
        errors.extend([abs(pieces.sum()-row.pred_2mer),abs(cpieces.sum()-row.pred_2mer)])
        for j,feature in enumerate(VOCAB[2]):
            contributions.append({'parent':row.parent,'candidate':row.candidate,'group':row.group,'feature':feature,
                'parent_count':x[pi[i],j+4],'candidate_count':x[ci[i],j+4],'delta_count':change[j],
                'raw_count_coefficient':raw[j],'centered_count_coefficient':centered[j],
                'raw_contribution':pieces[j],'centered_contribution':cpieces[j],
                'predicted_effect':row.pred_2mer,'measured_effect':row.published_delta,
                'correct_sign':sign(row.pred_2mer)==sign(row.published_delta),
                'replicate_sign_agreement':sign(row.rep1_delta)==sign(row.rep2_delta)})
    assert max(errors)<1e-12
    contributions=pd.DataFrame(contributions)
    csvsave(ART/'edit_features.csv',pair);csvsave(ART/'dinucleotide_contributions.csv',contributions)
    summary=contributions.groupby('feature').agg(mean_absolute_contribution=('centered_contribution',lambda v:np.abs(v).mean()),
        mean_signed_contribution=('centered_contribution','mean'),changed_fraction=('delta_count',lambda v:(v!=0).mean())).reset_index()
    summary['absolute_contribution_share']=summary.mean_absolute_contribution/summary.mean_absolute_contribution.sum()
    summary=summary.sort_values('absolute_contribution_share',ascending=False);csvsave(OUT/'contribution_summary.csv',summary)
    associations=[]
    for (feature,change),g in contributions.groupby(['feature','delta_count']):
        associations.append({'feature':feature,'delta_count':change,'edges':len(g),'groups':g.group.nunique(),
            'direction_accuracy':float(g.correct_sign.mean()),'mean_effect':g.measured_effect.mean(),
            'replicate_sign_agreement':g.replicate_sign_agreement.mean(),'interpretation':'descriptive association; correlated features and edges'})
    csvsave(OUT/'feature_outcome_associations.csv',pd.DataFrame(associations))
    examples=[]
    for flag in (True,False):
        g=pair[pair.delta2_zero.eq(flag)].sort_values(['parent','candidate'])
        if len(g):examples.append(g.iloc[0])
    csvsave(OUT/'edit_examples.csv',pd.DataFrame(examples))
    jsave(OUT/'decomposition_receipt.json',{'status':'PASS','edges':len(pair),'delta1_identically_zero':True,
        'two_position_unequal_base_exchange_verified':True,'zero_delta2_edges':int(pair.delta2_zero.sum()),
        'zero_delta3_edges':int(pair.delta3_zero.sum()),'max_contribution_reconstruction_error':max(errors),
        'top4_absolute_centered_contribution_share':float(summary.absolute_contribution_share.iloc[:4].sum()),
        'coefficient_interpretation':'predictive sequence-order structure; overlapping fits, noncausal attribution'})
    print(readj(OUT/'decomposition_receipt.json'))


if __name__=='__main__':run()
