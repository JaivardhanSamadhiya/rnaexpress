"""Only previously certified outcome-free designs and method/sample filenames."""
from .common import *
import re,tarfile,html,subprocess

def run():
    from src.pairing.audit_astrocyte import audit
    frame,_=audit()
    frame=frame.drop(columns=['delta_g_kcal_per_mol','rg4_prediction'])
    assert len(frame)==4553 and frame.parent_id.nunique()==8
    frame['prefit_qc_status']=np.where(frame.parent_id.eq(EXCLUDED),'EXCLUDED_BY_PREFIT_RULE','VERIFIED')
    frame['prefit_qc_reason']=np.where(frame.parent_id.eq(EXCLUDED),'Author excluded poorly cloned group; metadata-only rule','Exact single substitution and certified design mapping')
    parents=frame.groupby('parent_id').agg(gene=('gene','first'),parent_sequence=('parent_sequence','first'),variants=('element','size'),utr_start=('genomic_or_utr_position','min'),utr_end=('genomic_or_utr_position','max')).reset_index()
    parents['sequence_length']=parents.parent_sequence.str.len();parents['missing_substitutions']=570-parents.variants
    parents['prefit_eligible']=parents.parent_id.ne(EXCLUDED)
    parents['coordinate_type']='source 3UTR-relative; genomic assembly mm10, exact chromosome mapping not reconstructed'
    parents['reporter']='GFAP-driven tdTomato 3UTR insert in AAV9; in-vivo mouse astrocytes'
    # Connected overlap components from authoritative design coordinates, within gene.
    ids=parents.parent_id.tolist();parent={s:s for s in ids}
    def root(s):
        while parent[s]!=s:s=parent[s]
        return s
    for a in parents.itertuples():
        for b in parents.itertuples():
            if a.gene==b.gene and max(a.utr_start,b.utr_start)<=min(a.utr_end,b.utr_end):parent[root(b.parent_id)]=root(a.parent_id)
    roots=sorted({root(s) for s in ids});mapping={s:'overlap_'+str(roots.index(root(s))+1) for s in ids}
    parents['overlap_component']=parents.parent_id.map(mapping);frame['overlap_component']=frame.parent_id.map(mapping)
    csvsave(ART/'GSE330741_design_without_outcomes.csv',frame);csvsave(OUT/'parent_inventory.csv',parents)
    missing=[]
    for p,g in frame.groupby('parent_id'):
        seq=g.parent_sequence.iloc[0];observed=set(zip(g.edit_position_1based,g.alternate_nt))
        for i,ref in enumerate(seq,1):
            for alt in 'ACGT':
                if alt!=ref and (i,alt) not in observed:missing.append({'parent':p,'position':i,'ref':ref,'alt':alt,'status':'Absent from original design; never imputed'})
    assert len(missing)==7;csvsave(OUT/'missing_design_substitutions.csv',pd.DataFrame(missing))
    names=tarfile.open(SOURCE/'GSE330741_RAW.tar').getnames();samples=[]
    for name in names:
        m=re.fullmatch(r'(GSM\d+)_(aav|ctxin|snin|ctxtrap|sntrap)_(\d+)([ab])\.txt\.gz',name)
        if m:
            accession,fraction,rep,lane=m.groups();excluded=rep=='16' or (fraction=='snin' and rep=='10') or (fraction=='sntrap' and rep in ('3','4'))
            samples.append({'filename':name,'accession':accession,'fraction':fraction,'replicate':int(rep),'technical_lane':lane,'author_qc_excluded':excluded,'url':'https://ftp.ncbi.nlm.nih.gov/geo/samples/'+accession[:-3]+'nnn/'+accession+'/suppl/'+name})
    samples=pd.DataFrame(samples);assert len(samples)==106;csvsave(OUT/'mutation_sample_metadata.csv',samples)
    counts=samples.drop_duplicates(['fraction','replicate']).groupby('fraction').agg(before_qc=('replicate','size'),after_qc=('author_qc_excluded',lambda v:int((~v).sum()))).reset_index();csvsave(OUT/'replicate_design_counts.csv',counts)
    p=SOURCE/'PMC13142395.html';text=p.read_text(encoding='utf-8');start=text.index('Materials and Methods</h2>');end=text.index('Supplementary Material</h2>',start)
    excerpt=html.unescape(re.sub('<[^>]+>',' ',text[start:end]));save(OUT/'methods_only_extraction.txt',excerpt.encode())
    config_data={
      'study':'GSE330741','exposure':'PARTIALLY EXPOSED','source_commit':'4bd5154','seed':SEED,'bootstrap_draws':10000,
      'test_a_primary_model':'srle_2mer_full','test_a_source_partition':{'scheme':'sequence_holdout','held_group':'original_hash'},
      'test_a_models':['no_change','srle_composition','srle_delta_AU','srle_substitution','srle_2mer_order_only','srle_2mer_full','srle_3mer_full','srle_kmer123_full'],
      'test_a_primary_metric':'mean parent Spearman signed rank correlation','source_to_target_sign':1,
      'test_a_required_baselines':['no_change','srle_composition','srle_delta_AU','srle_substitution'],
      'strong_success':{'positive_mean_rho':True,'positive_cluster_bootstrap_lower_bound':True,'paired_advantage_over_each_required_baseline_lower_bound':0,'one_sided_overlap_block_signflip_p_max':.05,'candidate_regret_gain_vs_uniform_min':.02,'candidate_regret_gain_lower_bound':0,'majority_parents_improved':True,'wrong_direction_not_increased':True,'qualification':'not pristine untouched; 7 elements, 5 overlap components, 2 genes; no breadth claim'},
      'target':{'sheet':'S8_lib2_results_summary','column':'snin_ctxin_logFC','effect':'mutant processed normalized logFC minus matched exact 190nt WT processed normalized logFC','normalization':'log2(CPM+1) minus per-element-group fraction/replicate median; author REML mixed model fraction contrast','positive':'SNP increases synaptoneurosome input relative to cortical input versus its WT','negative':'SNP decreases that enrichment versus WT','magnitude_transfer_calibrated':False},
      'qc':{'exclude_parent':EXCLUDED,'min_eligible_parents':5,'min_overlap_components':4,'min_candidates_per_parent':100,'min_matched_positive_cpm_replicates':2,'finite_mutant_and_wt_score_required':True,'author_drop_all_replicate':16,'author_drop_snin_replicate':10,'fdr_filter':False,'effect_size_filter':False,'no_repair_of_ambiguous_mapping':True},
      'test_b_models':['no_change','training_mean','delta_AU','delta1','substitution','position','substitution_composition','substitution_position','simple_full','delta2','delta3','kmer123','simple_full_delta2','simple_full_delta2_delta3'],
      'test_b_primary_model':'simple_full_delta2','test_b_primary_comparator':'simple_full','test_b_primary_metric':'paired mean parent Spearman advantage',
      'test_b_ridge_alphas':[1.,10.,100.],'test_b_inner_selection':'mean parent MSE; ties prefer larger alpha','test_b_intercept':True,
      'test_b_outer':'leave-one-parent-out, purge all overlapping same-gene parent intervals from training','test_b_inner':'same parent/overlap exclusion within outer training only',
      'test_b_secondary_outer':'leave-one-gene-out for simple_full and simple_full_delta2 only; fixed alpha10; two genes descriptive',
      'parent_nuisance':'centered training-parent indicators for all learned B feature models; unseen parent has all-zero nuisance features',
      'position_features':['(position_1based-1)/189','normalized_position_squared','first_or_last_position'],
      'candidate_set':'all prefit-admitted mapped SNPs with finite mutant/WT effects and >=2 matched positive CPM replicate pairs; no outcome sign/range filtering','directions':[-1,1],'candidate_tie':'lexical element ID','top_k':5,'no_abstention':True,
      'constant_prediction_spearman':'operational no-ranking skill = 0, flagged not mathematical correlation','constant_target':'stop parent ranking branch; keep status, never drop silently',
      'coefficient_comparison':{'model_b':'delta2','gauge':'subtract grand mean; secondary remove row/column additive terms','permutations':4096,'seed':SEED,'scope':'descriptive feature-label permutations; no causal or independent-context p-value'},
      'stop_after':'one A evaluation, locked B evaluation and prespecified diagnostics; no rescue or GSE334718 outcomes'
    }
    jsave(OUT/'evaluation_config.json',config_data)
    manifest=readj(ROOT/'data/frozen/external_manifest.json')
    for entry in manifest['files']:assert sha256(ROOT/entry['path'])==entry['sha256']
    inputs=[ROOT/'data/frozen/external_manifest.json',ROOT/'data/frozen/astrocyte_external_features.csv.gz',ROOT/'data/frozen/astrocyte_pairing_audit.json',p,SOURCE/'code/SN_MPRA_followup_manuscript_code.Rmd',SOURCE/'code/localization_mpra_functions.R',ROOT/'results/srle_prediction_20260926/fitted_parameters.json',ROOT/'results/srle_prediction_20260926/sequence_inventory.csv']
    jsave(OUT/'metadata_receipt.json',{'status':'PASS','variant_outcomes_opened_this_phase':False,'workbook_read_this_phase':False,'raw_archive_names_only':len(names),'mutation_lane_files':len(samples),'parents':8,'genes':2,'eligible_parents':7,'eligible_snvs_before_outcomes':3984,'eligible_overlap_components':int(parents.loc[parents.prefit_eligible,'overlap_component'].nunique()),'source_inputs':{p.relative_to(ROOT).as_posix():sha256(p) for p in inputs},'historical_exposure':'3 source result rows before 2026-08-26T11:52:44Z; September23/24 literature excerpts; source workbook previously loaded for mapping/completeness; no documented outcome-driven fitting','new_incidental_exposure':'During metadata filtering of cached paper, a tiling-library aggregate CDF p-value sentence was returned; no mutation outcome value or quantitative heatmap opened; not used in model choices','original_data_files_unchanged':True})
    print(parents[['parent_id','variants','prefit_eligible','overlap_component']].to_string(index=False));print(counts.to_string(index=False))

if __name__=='__main__':run()
