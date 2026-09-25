"""Inventory established intervention links, never nearest-sequence invented parents."""
from .common import *
from functools import lru_cache
import itertools
from rapidfuzz.distance import Levenshtein
from scipy.stats import pearsonr
import openpyxl

PHASE=ROOT/'results/v4_phaseA'
RESEARCH=ROOT/'results/research_20260921'


@lru_cache(maxsize=None)
def geometry(parent,mutant):
    if set(parent+mutant)-set('ACGT'): raise ValueError('Invalid sequence')
    ops=Levenshtein.editops(parent,mutant)
    distance=Levenshtein.distance(parent,mutant)
    if len(ops)!=distance: raise ValueError('Distance/alignment mismatch')
    aligned=len(parent)==len(mutant)
    positions=[i+1 for i,(a,b) in enumerate(zip(parent,mutant)) if a!=b] if aligned else []
    subs=sum(o.tag=='replace' for o in ops)
    ins=sum(o.tag=='insert' for o in ops)
    dels=sum(o.tag=='delete' for o in ops)
    return {'substitution_count':len(positions) if aligned else subs,
        'insertion_count':0 if aligned else ins,'deletion_count':0 if aligned else dels,
        'total_edit_distance':distance,'minimum_alignment_substitutions':subs,
        'minimum_alignment_insertions':ins,'minimum_alignment_deletions':dels,
        'edit_positions':';'.join(map(str,positions)) if aligned else ';'.join(f'{o.tag}:{o.src_pos+1}:{o.dest_pos+1}' for o in ops),
        'edit_span':max(positions)-min(positions)+1 if positions else 0,
        'changed_bases':len(positions) if aligned else distance,
        'edit_size_band':band(len(positions) if aligned else distance),
        'minimum_distance_band':band(distance),
        'coordinate_semantics':'1-based corresponding insert coordinates' if aligned else 'one deterministic optimal alignment; not uniquely established physical edits'}


def certified():
    manifest=readj(PHASE/'source_manifest.json')
    for name in ('common_intervention_outcomes.csv.gz','mikl_interventions.csv.gz'):
        if sha256(PHASE/name)!=manifest['outputs'][name]['sha256']: raise ValueError('PhaseA input changed')
    from src.research_20260921.common import load_certified
    modeling=load_certified()
    modeling=modeling[modeling.outcome_valid].drop_duplicates(['dataset','parent_id','mutant_id','assay_context'])
    folds=modeling[['dataset','parent_id','mutant_id','cell_type','reporter','assay','candidate_id','biological_fold','biological_unit']]
    keys=['dataset','parent_id','mutant_id','cell_type','reporter','assay']
    if folds.duplicated(keys).any(): raise ValueError('Ambiguous model join')
    table=pd.read_csv(PHASE/'common_intervention_outcomes.csv.gz')
    table=table[table.outcome_valid].drop_duplicates(keys).merge(folds,on=keys,how='left',validate='one_to_one')
    table['biological_context']=table.dataset+'|'+table.assay+'|'+table.reporter+'|'+table.cell_type
    table['parent_localization']=np.nan
    table['mutant_localization']=np.nan
    table['localization_change']=table.localization_effect
    table['reference_value']=0.0
    table['reference_semantics']='paired/author WT-normalized effect; absolute measurements absent from admitted common table; zero is reference coordinate only'
    table['provenance_confidence']='VERIFIED_SOURCE_PAIR_WITH_ASSAY_CAVEATS'
    table['previous_exposure']='historical development; not independent confirmation'
    table['evaluation_status']=np.where(table.biological_fold.notna(),'existing_grouped_development_cohort','inventory_only_outside_historical_model_cohort')
    table['replicate_information']=table.replicate_count.astype(str)+' labels; '+table.uncertainty_semantics
    # Explicit usecols excludes stability and unrelated outcome columns.
    reps=pd.read_csv(PHASE/'mikl_interventions.csv.gz',usecols=['parent_id','mutant_id','raw_delta_cad_replicates','raw_delta_n2a_replicates'])
    lookup=reps.set_index(['parent_id','mutant_id'])
    table['replicate_delta_values']=''
    for i,r in table[table.dataset.eq('mikl_gse173098')].iterrows():
        table.at[i,'replicate_delta_values']=lookup.loc[(r.parent_id,r.mutant_id),'raw_delta_cad_replicates' if r.cell_type=='CAD' else 'raw_delta_n2a_replicates']
    return table


def sirloin():
    from src.research_20260921.sirloin_transfer import verify
    verify()
    frame=pd.read_csv(RESEARCH/'sirloin_transfer_predictions.csv')
    ids=set(frame.id)|set(frame.parent)
    book=openpyxl.load_workbook(ROOT/'data/external/research_20260921/sirloin_dataset_ev1.xlsx',read_only=True,data_only=True)
    values={}
    for row in book['NucLibC'].iter_rows(min_row=3,max_col=8,values_only=True):
        if row[0] in ids: values[row[0]]=pd.to_numeric(pd.Series(row[6:8]),errors='coerce').tolist()
    book.close()
    if set(values)!=ids: raise ValueError('Missing admitted SIRLOIN reference')
    rows=[]
    for r in frame.itertuples():
        p,m=np.array(values[r.parent]),np.array(values[r.id])
        rows.append({'dataset':'sirloin','parent_id':r.parent,'mutant_id':r.id,'gene_name':r.parent,
            'parent_sequence':r.reference,'mutant_sequence':r.sequence,'parent_localization':float(p.mean()),
            'mutant_localization':float(m.mean()),'localization_change':float((m-p).mean()),
            'biological_context':'NucLibC|nuclear enrichment','replicate_count':2,'replicate_information':'discovery Rep1/2 only; not3/4 or NucLibB',
            'replicate_delta_values':';'.join(map(str,m-p)),'effect_uncertainty':np.nan,
            'outcome_semantics':'mutant minus matched-parent nuclear enrichment, mean of admitted two replicates',
            'reference_semantics':'measured matched parent','provenance_confidence':'VERIFIED_SEQUENCE_AND_DISCOVERY_JOIN',
            'previous_exposure':'prior frozen external discovery pilot; gate failed',
            'evaluation_status':'fixed_source_predictions_only; two parents; no target fitting' if np.isfinite(np.r_[p,m]).all() else 'missing_discovery_measurement; inventory_only',
            'intervention_class':'single_substitution','biological_fold':np.nan})
    return pd.DataFrame(rows)


def srle():
    # Reuse only the original frozen eligible test-neighbor decisions, not new neighborhoods.
    frozen=readj(RESEARCH/'srle_uniform_risk_freeze.json')
    for p,h in frozen['files'].items():
        if sha256(ROOT/p)!=h: raise ValueError('SRLE freeze changed')
    pred=pd.read_csv(RESEARCH/'robustness_predictions.csv').set_index('kmer')
    raw=pd.read_csv(RESEARCH/'raw_replication_scores.csv').set_index('kmer')
    saved=pd.read_csv(RESEARCH/'raw_swap_evaluation.csv')
    parents=sorted(saved.parent.unique())
    original=pd.read_csv(RESEARCH/'robustness_swap_predictions.csv')
    original_parents=set(original.parent)
    # Eligibility follows original 70 prediction classes and >=2 train/test sequence rule.
    keys={s:tuple(s.count(b) for b in 'ACGT') for s in pred.index}
    eligible_classes={k for k in set(keys.values()) if sum(keys[s]==k and pred.loc[s,'test'] for s in pred.index)>=2 and sum(keys[s]==k and not pred.loc[s,'test'] for s in pred.index)>=2}
    eligible={s for s in pred.index if pred.loc[s,'test'] and keys[s] in eligible_classes}
    from src.research_20260921.robustness import swaps
    rows=[]
    for parent in parents:
        if parent not in original_parents: raise ValueError('Unexpected original parent')
        candidates=[s for s in swaps(parent) if s in eligible]
        if not raw.loc[[parent]+candidates,'eligible'].all(): raise ValueError('Saved retained parent lost count coverage')
        for mutant in candidates:
            p=raw.loc[parent,['NRS1','NRS2']].to_numpy(float)
            m=raw.loc[mutant,['NRS1','NRS2']].to_numpy(float)
            rows.append({'dataset':'srle','parent_id':parent,'mutant_id':mutant,'gene_name':'HBB_reporter',
                'parent_sequence':parent,'mutant_sequence':mutant,'parent_localization':float(p.mean()),
                'mutant_localization':float(m.mean()),'localization_change':float((m-p).mean()),
                'biological_context':'HBB_3UTR_sixmer_reporter','replicate_count':2,
                'replicate_information':'constituent Rep1/2, same experiment as training aggregate',
                'replicate_delta_values':';'.join(map(str,m-p)), 'effect_uncertainty':np.nan,
                'outcome_semantics':'fixed-depth log2 nuclear/cytoplasmic NRS difference',
                'reference_semantics':'measured sixmer anchor, not independent biological parent',
                'provenance_confidence':'PARTIAL_AUTHOR_TABLE_CHAIN; VERIFIED_LOCAL_COUNTS',
                'previous_exposure':'source training and previous measured-swap evaluations',
                'evaluation_status':'original_test_neighbors; within_shared_reporter; no parent-heldout claim',
                'intervention_class':'composition_preserving_swap','composition':str(keys[parent]),'biological_fold':np.nan})
    if len(rows)!=1744 or len(parents)!=592: raise ValueError('Frozen SRLE roster mismatch')
    return pd.DataFrame(rows)


def run():
    table=pd.concat([certified(),sirloin(),srle()],ignore_index=True)
    geometries=pd.DataFrame([geometry(a,b) for a,b in zip(table.parent_sequence,table.mutant_sequence)])
    # Original metadata fields are retained with an explicit prefix; never overwritten as a correction.
    for c in set(table.columns)&set(geometries.columns): table=table.rename(columns={c:'source_'+c})
    table=pd.concat([table,geometries],axis=1)
    table['pair_id']=[sha256_text('|'.join(map(str,(r.dataset,r.parent_id,r.mutant_id,r.biological_context)))) for r in table.itertuples()]
    if table.pair_id.duplicated().any(): raise ValueError('Duplicate intervention measurement')
    csvsave('small_edit_pairs.csv.gz',table)
    counts=[]
    for (dataset,b),g in table.groupby(['dataset','edit_size_band']):
        variants=g[['parent_id','mutant_id']].drop_duplicates()
        parents=g.groupby('parent_id').mutant_id.nunique()
        counts.append({'dataset':dataset,'edit_size_band':b,'variant_context_measurements':len(g),'distinct_parent_mutant_pairs':len(variants),
            'unique_parents':g.parent_id.nunique(),'unique_genes':g.gene_name.nunique(),'contexts':g.biological_context.nunique(),
            'variants_per_parent_min':int(parents.min()),'variants_per_parent_median':float(parents.median()),'variants_per_parent_max':int(parents.max()),
            'parent_contexts_with_2_candidates':int((g.groupby(['parent_id','biological_context']).mutant_id.nunique()>=2).sum()),
            'effect_variance_descriptive':float(g.localization_change.var()),
            'effect_uncertainty_available':int(g.effect_uncertainty.notna().sum()),
            'span_le6_measurements':int((g.edit_span<=6).sum()),
            'minimum_alignment_distance_differs':int((g.total_edit_distance!=g.changed_bases).sum()),
            'independence_note':'single shared reporter, overlapping neighborhoods' if dataset=='srle' else ('two parents only' if dataset=='sirloin' else 'parent/gene clustering required; already exposed source')})
    csvsave('small_edit_size_counts.csv',pd.DataFrame(counts))
    minimum=table.groupby(['dataset','minimum_distance_band']).agg(measurements=('pair_id','size'),parents=('parent_id','nunique'),genes=('gene_name','nunique')).reset_index()
    csvsave('minimum_distance_counts.csv',minimum)
    model=table[table.dataset.eq('mikl_gse173098')&table.changed_bases.between(1,6)&table.biological_fold.notna()].copy()
    # All original folds, never a new favorable resplit. No same parent or gene straddles folds.
    for key in ('parent_id','gene_name','parent_sequence','mutant_sequence'):
        if model.groupby(key).biological_fold.nunique().max()!=1: raise ValueError('Fold leakage '+key)
    allalleles=pd.concat([model[['parent_sequence','biological_fold']].rename(columns={'parent_sequence':'sequence'}),model[['mutant_sequence','biological_fold']].rename(columns={'mutant_sequence':'sequence'})])
    if allalleles.groupby('sequence').biological_fold.nunique().max()!=1: raise ValueError('Cross-allele leakage')
    csvsave('mikl_existing_fold_eligible.csv.gz',model)
    receipt={'status':'PASS','pairs':len(table),'prediction_eligible_mikl_measurements':len(model),
        'prediction_eligible_mikl_genes':model.gene_name.nunique(),'distance_discrepancies_are_metric_definitions_not_source_errors':True,
        'excluded_sources':{'nzip':'quarantined uncertified truth','astrocyte':'sealed','mutREL':'unadmitted mutation-event semantics','Wen':'unadmitted RNA/outcome mapping',
            'Arora':'tiled alternatives; no declared paired small edit reference','context2022':'tiled/context alternatives; no admitted same-context small-mutant lineage',
            'Shukla':'tiled alternatives; raw/processed mapping unresolved','SEERS':'random inserts; no declared parent-mutant mapping; failed/inconclusive prior screen',
            'Faraway':'intron configuration and barcodes; not admitted small RNA-sequence substitutions','external_stability':'wrong endpoint; admission failed'},
        'inputs':{p:sha256(ROOT/p) for p in ('results/v4_phaseA/common_intervention_outcomes.csv.gz','results/v4_phaseA/mikl_interventions.csv.gz','results/v4_phaseB/model_candidate_rows.csv.gz','results/research_20260921/sirloin_transfer_predictions.csv','results/research_20260921/robustness_predictions.csv','results/research_20260921/raw_replication_scores.csv')},
        'outputs':{p:sha256(OUT/p) for p in ('small_edit_pairs.csv.gz','small_edit_size_counts.csv','minimum_distance_counts.csv','mikl_existing_fold_eligible.csv.gz')}}
    jsave('inventory_receipt.json',receipt)
    print(pd.DataFrame(counts)[['dataset','edit_size_band','distinct_parent_mutant_pairs','unique_parents','unique_genes','contexts']].to_string(index=False))


def sha256_text(value):
    import hashlib
    return hashlib.sha256(value.encode()).hexdigest()[:24]


if __name__=='__main__': run()
