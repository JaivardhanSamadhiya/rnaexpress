from .common import *
from src.srle_prediction_20260926.core import training_mask,counts
from src.research_20260921.robustness import count_features
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
from scipy.spatial.distance import cdist


def run():
    source,effects,choices,fits,roster=load();encoded=np.array([list(s) for s in source.kmer]);x=count_features(source.kmer.to_numpy())
    records=[]
    for group,g in source[source.scored].groupby('group'):
        train=training_mask(source,'purged_composition_holdout',group);ix=g.index.to_numpy();ti=np.flatnonzero(train)
        h=(encoded[ix,None,:]!=encoded[None,ti,:]).sum(2)
        lev=process.cdist(g.kmer.tolist(),source.loc[train,'kmer'].tolist(),scorer=Levenshtein.distance,dtype=np.uint8,workers=1)
        c=cdist(x[ix,:4],x[ti,:4],metric='cityblock');d2=cdist(x[ix,4:20],x[ti,4:20],metric='cityblock')
        d3=cdist(x[ix,20:84],x[ti,20:84],metric='cityblock');cos=cdist(x[ix,4:20],x[ti,4:20],metric='cosine')
        low=x[ti,4:20].min(0);high=x[ti,4:20].max(0)
        extrap=((x[ix,4:20]<low)|(x[ix,4:20]>high)).sum(1)
        excess=np.maximum(low-x[ix,4:20],0)+np.maximum(x[ix,4:20]-high,0)
        for j,row in enumerate(g.itertuples()):
            records.append({'sequence':row.kmer,'group':group,'training_sequences':len(ti),
                'hamming':int(h[j].min()),'local_window_hamming':int(h[j].min()),'levenshtein':int(lev[j].min()),
                'composition_l1':int(c[j].min()),'nearest_2mer_l1':int(d2[j].min()),'nearest_3mer_l1':int(d3[j].min()),
                'nearest_2mer_cosine_distance':float(cos[j].min()),'out_of_range_2mer_features':int(extrap[j]),
                'excess_2mer_count_sum':float(excess[j].sum()),'nearest_hamming_sequence':source.kmer.iloc[ti[h[j].argmin()]],
                'nearest_2mer_sequence':source.kmer.iloc[ti[d2[j].argmin()]]})
    nearest=pd.DataFrame(records);assert nearest.hamming.min()>=3 and nearest.levenshtein.min()>=3 and nearest.composition_l1.min()>=6
    csvsave(ART/'nearest_training_sequences.csv',nearest)
    pair=effects[effects.scheme.eq('purged_composition_holdout')].copy();lookup=nearest.set_index('sequence')
    for metric in ('hamming','levenshtein','nearest_2mer_l1','nearest_3mer_l1','nearest_2mer_cosine_distance','out_of_range_2mer_features'):
        a=pair.parent.map(lookup[metric]);b=pair.candidate.map(lookup[metric])
        pair['minimum_'+metric]=np.minimum(a,b);pair['maximum_'+metric]=np.maximum(a,b)
    pair['mse']=(pair.predicted_delta-pair.published_delta)**2;pair['baseline_mse']=pair.published_delta**2
    pair['absolute_error']=np.abs(pair.predicted_delta-pair.published_delta)
    pair['strict_sign_correct']=(sign(pair.predicted_delta)==sign(pair.published_delta)).astype(float)
    csvsave(ART/'edit_prediction_diagnostics.csv',pair)
    records=[]
    for factor in ('minimum_hamming','minimum_levenshtein','minimum_nearest_2mer_l1','minimum_nearest_3mer_l1','maximum_out_of_range_2mer_features'):
        for (model,value),g in pair.groupby(['model',factor]):
            stats=g.groupby('group')[['mse','baseline_mse']].agg(['sum','count'])
            a=stats[('mse','sum')].to_numpy();b=stats[('baseline_mse','sum')].to_numpy();ix=draws(len(stats))
            gains=1-a[ix].sum(1)/b[ix].sum(1)
            lo,hi=np.quantile(gains,[.025,.975]) if len(stats)>=5 else (np.nan,np.nan)
            records.append({'model':model,'distance_metric':factor,'distance':value,'edges':len(g),'groups':len(stats),
                'mse_improvement_vs_no_change':1-a.sum()/b.sum(),'ci_low':lo,'ci_high':hi,
                'mae':g.absolute_error.mean(),'strict_sign_accuracy':g.strict_sign_correct.mean(),
                'ci_status':'conditional class bootstrap' if len(stats)>=5 else 'insufficient groups for displayed interval'})
    csvsave(OUT/'similarity_performance.csv',pd.DataFrame(records))
    jsave(OUT/'similarity_receipt.json',{'status':'PASS','heldout_sequences':len(nearest),
        'minimum_hamming':int(nearest.hamming.min()),'minimum_levenshtein':int(nearest.levenshtein.min()),
        'hamming_counts':nearest.hamming.value_counts().sort_index().to_dict(),
        'levenshtein_counts':nearest.levenshtein.value_counts().sort_index().to_dict(),
        'feature_2mer_distance_counts':nearest.nearest_2mer_l1.value_counts().sort_index().to_dict(),
        'not_a_second_context':True})
    print(readj(OUT/'similarity_receipt.json'))


if __name__=='__main__':run()
