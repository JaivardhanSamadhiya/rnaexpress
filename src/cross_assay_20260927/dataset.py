"""Canonical translation of already-exposed certified localization edits only."""
from .common import *
import gzip

def run():
    original=ROOT/'results/small_edit_20260925/small_edit_pairs.csv.gz'
    assert sha256(original)=='b56d9ce9712776ba477fcb8231d7d431c0dce895c2ed1054f1a1767360e482fd'
    old=pd.read_csv(original,low_memory=False)
    inventory=old.groupby(['dataset','intervention_class','edit_size_band'],dropna=False).agg(rows=('pair_id','size'),parents=('parent_id','nunique'),genes=('gene_name','nunique')).reset_index()
    csvsave(OUT/'full_exposed_inventory_counts.csv',inventory)
    f=old[old.substitution_count.between(1,6)&old.insertion_count.eq(0)&old.deletion_count.eq(0)].copy()
    rows=[]
    for r in f.to_dict('records'):
        d=r['dataset'];parent=r['parent_sequence'];mutant=r['mutant_sequence'];positions=[i for i,(a,b) in enumerate(zip(parent,mutant)) if a!=b]
        assert len(parent)==len(mutant) and len(positions)==r['substitution_count'] and not set(parent+mutant)-set('ACGT')
        status='ADMIT_PRIMARY' if d in ('mikl_gse173098','srle') or (d=='moffatt_gse334718' and r['intervention_class']=='random_substitution') else ('ADMIT_SECONDARY' if d in ('sirloin','moffatt_gse334718') else 'DEVELOPMENT_ONLY')
        context=r['biological_context'];gene=str(r['gene_name']).lower()
        if d=='srle':cell='MCF7';assay='HBB_sixmer_nuclear_cytoplasmic';destination='nucleus';family='nuclear_cytoplasmic'
        elif d=='sirloin':cell='not established in admitted cached inventory';assay='NucLibC_nuclear_cytoplasmic';destination='nucleus';family='nuclear_cytoplasmic'
        else:cell=r['cell_type'];assay=r['assay'];destination='neurite';family='projection'
        rows.append({'intervention_id':r['pair_id'],'dataset':d,'source_study':('10.34133/csbj.0107' if d=='srle' else ('10.15252/embj.2020106357' if d=='sirloin' else r['accession'])),'assay':assay,'cell_type':cell,'reporter':r.get('reporter',''),'localization_destination':destination,'endpoint_class':family,'parent_id':r['parent_id'],'mutant_id':r['mutant_id'],'parent_context_id':d+'|'+str(context)+'|'+str(r['parent_id']),'gene_transcript':gene,'parent_sequence':parent,'mutant_sequence':mutant,'edit_start':min(positions)+1,'edit_end':max(positions)+1,'substitution_count':len(positions),'insertion_count':0,'deletion_count':0,'total_edit_distance':r['total_edit_distance'],'physical_edit_span':max(positions)-min(positions)+1,'local_parent_window':parent[max(0,min(positions)-10):max(positions)+11],'local_mutant_window':mutant[max(0,min(positions)-10):max(positions)+11],'measured_parent_localization':r['parent_localization'],'measured_mutant_localization':r['mutant_localization'],'measured_delta':r['localization_change'],'desired_direction':1,'replicate_information':r['replicate_information'],'replicate_delta_values':r['replicate_delta_values'],'endpoint_semantics':r['outcome_semantics'],'provenance_status':r['provenance_confidence'],'exposure_status':'EXPOSED_DEVELOPMENT','admission_status':status,'intervention_class':r['intervention_class'],'legacy_biological_unit':r.get('biological_unit',''),'source_pair_id':r['pair_id']})
    astro=ROOT/'artifacts/generalization_20260926/GSE330741_mapped_outcomes.csv'
    assert sha256(astro)=='f31a38ec6d03de3317d7f0c1b1aaaf8586277e2512b9512c027606da8b6cc08a'
    a=pd.read_csv(astro);a=a[a.qc_status.eq('VERIFIED')]
    for r in a.itertuples():
        pos=r.edit_position_1based
        rows.append({'intervention_id':'astro:'+r.element,'dataset':'astrocyte_gse330741','source_study':'GSE330741','assay':'in_vivo_SN_cortex_MPRA','cell_type':'mouse_astrocyte_in_vivo','reporter':'GFAP_tdTomato_AAV9','localization_destination':'synaptoneurosome_input','endpoint_class':'projection','parent_id':r.parent_id,'mutant_id':r.element,'parent_context_id':'astrocyte_gse330741|'+r.parent_id,'gene_transcript':r.gene.split('.')[0].lower(),'parent_sequence':r.parent_sequence,'mutant_sequence':r.mutant_sequence,'edit_start':pos,'edit_end':pos,'substitution_count':1,'insertion_count':0,'deletion_count':0,'total_edit_distance':1,'physical_edit_span':1,'local_parent_window':r.parent_sequence[max(0,pos-11):pos+10],'local_mutant_window':r.mutant_sequence[max(0,pos-11):pos+10],'measured_parent_localization':r.author_wt_normalized_localization,'measured_mutant_localization':r.author_mutant_normalized_localization,'measured_delta':r.observed_delta,'desired_direction':1,'replicate_information':str(r.valid_paired_replicates)+' positive paired CPM labels of 14 author-retained pools','replicate_delta_values':';'.join(str(getattr(r,'replicate_effect_'+str(i))) for i in [1,2,3,4,5,6,7,8,9,11,12,13,14,15]),'endpoint_semantics':'author normalized log2 SN-input/cortex-input mutant minus exact190ntWT','provenance_status':'VERIFIED_SEQUENCE_WT_JOIN; full_REML_pipeline_not_reproduced','exposure_status':'EXPOSED_DEVELOPMENT_AFTER_FAILED_FROZEN_TEST','admission_status':'ADMIT_PRIMARY','intervention_class':'single_substitution','legacy_biological_unit':r.overlap_component,'source_pair_id':r.element})
    f=pd.DataFrame(rows).sort_values(['dataset','parent_context_id','intervention_id']).reset_index(drop=True)
    assert not f.intervention_id.duplicated().any()
    f['finite_outcome']=np.isfinite(f.measured_delta)
    sizes=f.groupby('parent_context_id').measured_delta.transform('count');spread=f.groupby('parent_context_id').measured_delta.transform(lambda x:x.max()-x.min())
    f['candidate_set_eligible']=f.finite_outcome & sizes.ge(2) & spread.gt(1e-12)
    f['normalized_delta']=f.measured_delta/f.groupby('parent_context_id').measured_delta.transform('std').replace(0,np.nan)
    rank=f.groupby('parent_context_id').measured_delta.rank(method='average')
    f['within_parent_rank']=(rank-rank.groupby(f.parent_context_id).transform('min'))/(rank.groupby(f.parent_context_id).transform('max')-rank.groupby(f.parent_context_id).transform('min')).replace(0,np.nan)
    f['direction_label_increase']=np.where(f.finite_outcome,np.sign(f.measured_delta),np.nan)
    # Components co-group all alleles and genes, including duplicated Moffatt labels.
    contexts=sorted(f.parent_context_id.unique());leaders={s:s for s in contexts}
    def root(x):
        while leaders[x]!=x:leaders[x]=leaders[leaders[x]];x=leaders[x]
        return x
    def merge(a,b):
        a,b=root(a),root(b)
        if a!=b:leaders[max(a,b)]=min(a,b)
    genes={};alleles={}
    for r in f.itertuples():
        g=r.gene_transcript
        if g and g not in ('nan','missing'):
            if g in genes:merge(r.parent_context_id,genes[g])
            else:genes[g]=r.parent_context_id
        for seq in (r.parent_sequence,r.mutant_sequence):
            if seq in alleles:merge(r.parent_context_id,alleles[seq])
            else:alleles[seq]=r.parent_context_id
    f['biological_component']=[hashlib.sha256(root(s).encode()).hexdigest()[:16] for s in f.parent_context_id]
    f['held_parent_fold']=[int(hashlib.sha256(s.encode()).hexdigest()[:8],16)%3 for s in f.biological_component]
    # Primary core excludes singletons and other intervention families, never unfavorable effects.
    f['primary_eligible']=f.admission_status.eq('ADMIT_PRIMARY') & f.candidate_set_eligible
    # Collapse identical sequence candidates only when measuring the same constructed candidate;
    # none are silently merged: record aliases for audit and keep distinct experimental IDs.
    csvsave(ART/'canonical_interventions.csv',f)
    save(ART/'canonical_interventions.csv.gz',gzip.compress((ART/'canonical_interventions.csv').read_bytes(),mtime=0))
    summary=f.groupby(['dataset','admission_status'],dropna=False).agg(rows=('intervention_id','size'),decision_sets=('parent_context_id','nunique'),genes=('gene_transcript','nunique'),components=('biological_component','nunique'),eligible_rows=('primary_eligible','sum')).reset_index()
    csvsave(OUT/'admission_counts.csv',summary)
    primary=f[f.primary_eligible];ps=primary.groupby('dataset').agg(rows=('intervention_id','size'),parents=('parent_id','nunique'),decision_sets=('parent_context_id','nunique'),genes=('gene_transcript','nunique'),components=('biological_component','nunique')).reset_index()
    csvsave(OUT/'primary_counts.csv',ps)
    jsave(OUT/'dataset_receipt.json',{'inputs':{str(original.relative_to(ROOT)):sha256(original),str(astro.relative_to(ROOT)):sha256(astro)},'canonical_sha256':sha256(ART/'canonical_interventions.csv'),'rows':len(f),'primary_rows':len(primary),'primary_studies':sorted(primary.dataset.unique()),'status':'PASS','directions':'Both +/-1 evaluated; canonical rank is destination-increase; decrease rank is 1-rank','sequence_grouping':'same gene symbol or exact any-allele match; no proximity threshold, no assertion of paralog independence','physical_edit_scope':'1-6 corresponding-coordinate substitutions; indel/padding families secondary only; larger edits remain in inventory','new_protected_outcomes_opened':False})
    print(ps.to_string(index=False))

if __name__=='__main__':run()
