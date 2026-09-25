"""Report measurement sufficiency; do not filter a model cohort by reliability."""
from .common import *
from .evaluate import corr
from scipy.stats import t


def run():
    frame=pd.read_csv(OUT/'small_edit_pairs.csv.gz',low_memory=False)
    rows=[]
    for (dataset,context,b),g in frame.groupby(['dataset','biological_context','edit_size_band']):
        valid=g[np.isfinite(g.localization_change)]
        raw=[]
        for value in valid.replicate_delta_values.dropna():
            values=np.array([float(v) for v in str(value).split(';')])
            if len(values)>1 and np.isfinite(values).all(): raw.append(values)
        sizes={len(x) for x in raw}
        paircorr=[]; clear=np.nan; pairedn=len(raw)
        if len(raw)>2 and len(sizes)==1:
            x=np.array(raw)
            for a in range(x.shape[1]):
                for c in range(a+1,x.shape[1]): paircorr.append(corr(x[:,a],x[:,c]))
            if dataset=='mikl_gse173098':
                se=x.std(axis=1,ddof=1)/np.sqrt(x.shape[1])
                clear=float(np.mean(np.abs(x.mean(axis=1))>t.ppf(.975,x.shape[1]-1)*se))
        parents=valid.groupby('parent_id').mutant_id.nunique()
        eligible_parents=set(parents[parents>=2].index)
        rows.append({'dataset':dataset,'context':context,'edit_size_band':b,
            'inventory_measurements':len(g),'finite_measurements':len(valid),'parents':valid.parent_id.nunique(),
            'genes':valid.gene_name.nunique(),'parents_with_at_least_two_candidates':len(eligible_parents),
            'genes_with_at_least_two_candidates':valid[valid.parent_id.isin(eligible_parents)].gene_name.nunique(),
            'effect_variance':float(valid.localization_change.var()),'replicate_delta_rows':pairedn,
            'mean_pairwise_replicate_delta_pearson':float(np.nanmean(paircorr)) if paircorr and np.isfinite(paircorr).any() else np.nan,
            'raw_paired_t95_nonzero_fraction':clear,
            'measurable_effect_status':'diagnostic raw-count delta t interval, n=3, not confidence on author-processed effect' if dataset=='mikl_gse173098' else 'not established from supplied paired uncertainty',
            'parent_population_inference':'not independent biological parents' if dataset=='srle' else ('only two parents' if dataset=='sirloin' else 'gene clustering required; reused development source'),
            'model_eligibility_changed':False})
    csvsave('small_edit_data_sufficiency.csv',pd.DataFrame(rows))
    print('Saved',len(rows),'source/context/edit-size sufficiency rows')


if __name__=='__main__': run()
