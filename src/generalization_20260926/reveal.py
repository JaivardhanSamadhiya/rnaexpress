"""Only callable after committed protocols, prefit predictions and freeze record."""
from .common import *
from datetime import datetime,timezone
import re

def run():
    assert_frozen();assert not (OUT/'outcome_access_receipt.json').exists(),'Reveal already recorded; never repeat or replace'
    source_manifest=readj(ROOT/'data/frozen/external_manifest.json')
    for f in source_manifest['files']:assert sha256(ROOT/f['path'])==f['sha256']
    # Record the access boundary before the first mutation-level measurement is loaded.
    jsave(OUT/'outcome_access_started.json',{'started_utc':datetime.now(timezone.utc).isoformat(),'source':WORKBOOK.relative_to(ROOT).as_posix(),'sha256':sha256(WORKBOOK),'authorization':'current user request plus committed GSE330741_PREFIT_FREEZE.md','scope':'S6 exact design and S8 localization / corresponding CPM fields only'})
    frame=pd.read_csv(ART/'GSE330741_design_without_outcomes.csv')
    design=pd.read_excel(WORKBOOK,sheet_name='S6_mutagenesis_lib_seq_info',usecols=['element','element_group','gene','CRE','seq_length','original_nt','mutant_nt','position_start'])
    allowed=lambda c:c in ('element','snin_ctxin_logFC') or bool(re.fullmatch(r'avg_cpm_(ctxin|snin)_\d+',str(c)))
    outcome=pd.read_excel(WORKBOOK,sheet_name='S8_lib2_results_summary',usecols=allowed)
    assert not design.element.duplicated().any() and not outcome.element.duplicated().any(),'Ambiguous element mapping'
    design=design.set_index('element');outcome=outcome.set_index('element')
    cfg=config();reps=sorted(set(int(c.rsplit('_',1)[1]) for c in outcome if c.startswith('avg_cpm_ctxin_'))&set(int(c.rsplit('_',1)[1]) for c in outcome if c.startswith('avg_cpm_snin_')))
    reps=[r for r in reps if r not in (10,16)];assert len(reps)>=2
    rows=[];mapping_errors=[]
    for row in frame.itertuples():
        result=row._asdict();result.pop('Index',None)
        result.update(qc_status=row.prefit_qc_status,qc_reason=row.prefit_qc_reason,observed_delta=np.nan,author_mutant_normalized_localization=np.nan,author_wt_normalized_localization=np.nan,valid_paired_replicates=0)
        if row.parent_id==EXCLUDED:rows.append(result);continue
        try:
            dm=design.loc[row.element];dw=design.loc[row.parent_id]
            assert str(dm.CRE).upper().replace('U','T')==row.mutant_sequence
            assert str(dw.CRE).upper().replace('U','T')==row.parent_sequence and int(dw.seq_length)==190 and str(dw.original_nt).lower()=='wt'
            assert int(dm.position_start)-int(dw.position_start)+1==row.edit_position_1based
            assert str(dm.original_nt).upper()==row.reference_nt and str(dm.mutant_nt).upper()==row.alternate_nt
            diffs=[i+1 for i,(a,b) in enumerate(zip(row.parent_sequence,row.mutant_sequence)) if a!=b];assert diffs==[row.edit_position_1based]
            m=outcome.loc[row.element];w=outcome.loc[row.parent_id];score_m=float(m.snin_ctxin_logFC);score_w=float(w.snin_ctxin_logFC)
            if not np.isfinite([score_m,score_w]).all():
                result.update(qc_status='EXCLUDED_BY_PREFIT_RULE',qc_reason='Nonfinite mutant or WT processed localization');rows.append(result);continue
            result.update(author_mutant_normalized_localization=score_m,author_wt_normalized_localization=score_w,observed_delta=score_m-score_w)
            paired=[]
            for rep in reps:
                vals=np.array([m[f'avg_cpm_snin_{rep}'],m[f'avg_cpm_ctxin_{rep}'],w[f'avg_cpm_snin_{rep}'],w[f'avg_cpm_ctxin_{rep}']],float)
                valid=np.isfinite(vals).all() and (vals>0).all()
                effect=float(np.log2(vals[0]+1)-np.log2(vals[1]+1)-np.log2(vals[2]+1)+np.log2(vals[3]+1)) if valid else np.nan
                result['replicate_effect_'+str(rep)]=effect
                if valid:paired.append(effect)
            result['valid_paired_replicates']=len(paired)
            if len(paired)<cfg['qc']['min_matched_positive_cpm_replicates']:result.update(qc_status='EXCLUDED_BY_PREFIT_RULE',qc_reason='Fewer than two positive matched mutant/WT CPM replicate pairs')
            else:result.update(qc_status='VERIFIED',qc_reason='Exact design/WT/outcome mapping; finite paired target; fixed replicate QC',replicate_mean_delta=float(np.mean(paired)),replicate_sd_delta=float(np.std(paired,ddof=1)),replicate_fraction_positive=float(np.mean(np.array(paired)>TOL)),replicate_fraction_negative=float(np.mean(np.array(paired)<-TOL)))
        except (KeyError,AssertionError,TypeError,ValueError) as exc:
            result.update(qc_status='AMBIGUOUS',qc_reason=type(exc).__name__+': '+str(exc));mapping_errors.append(row.element)
        rows.append(result)
    result=pd.DataFrame(rows);csvsave(ART/'GSE330741_mapped_outcomes.csv',result)
    if mapping_errors:
        jsave(OUT/'mapping_stop.json',{'status':'STOP','ambiguous_elements':mapping_errors,'rule':'No silent repair or endpoint substitution'})
        raise RuntimeError('Ambiguous target mapping; branch stopped')
    keep=result[result.qc_status.eq('VERIFIED')]
    assert keep.parent_id.nunique()>=cfg['qc']['min_eligible_parents'] and keep.overlap_component.nunique()>=cfg['qc']['min_overlap_components']
    assert set(keep.parent_id)==set(frame.loc[frame.parent_id.ne(EXCLUDED),'parent_id'])
    assert keep.groupby('parent_id').size().min()>=cfg['qc']['min_candidates_per_parent']
    assert (keep.groupby('parent_id').observed_delta.agg(lambda v:np.ptp(v))>TOL).all()
    summaries=[]
    for parent,g in keep.groupby('parent_id'):
        summaries.append({'parent_id':parent,'gene':g.gene.iloc[0],'overlap_component':g.overlap_component.iloc[0],'snps':len(g),'paired_replicates_min':g.valid_paired_replicates.min(),'paired_replicates_max':g.valid_paired_replicates.max(),'observed_mean':g.observed_delta.mean(),'observed_sd':g.observed_delta.std(),'author_vs_paired_mean_pearson':np.corrcoef(g.observed_delta,g.replicate_mean_delta)[0,1],'author_vs_paired_mean_mae':np.abs(g.observed_delta-g.replicate_mean_delta).mean(),'interpretation':'paired-replicate reconstruction diagnostic, not identical to author REML coefficients'})
    csvsave(OUT/'mapping_parent_summary.csv',pd.DataFrame(summaries))
    provenance=[{'accession':'GSE330741','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC13142395/bin/media-1.xlsx','access_date_utc':datetime.now(timezone.utc).isoformat(),'filename':WORKBOOK.relative_to(ROOT).as_posix(),'sha256':sha256(WORKBOOK),'source':'official author supplement, previously downloaded and SHA-locked','role':'S6 mapping and S8 localization/CPM fields','access':'public and free; local reuse, no new download'}]
    csvsave(OUT/'source_provenance_manifest.csv',pd.DataFrame(provenance))
    jsave(OUT/'outcome_access_receipt.json',{'status':'PASS','opened_utc':datetime.now(timezone.utc).isoformat(),'eligible_snps':len(keep),'eligible_parents':keep.parent_id.nunique(),'genes':keep.gene.nunique(),'overlap_components':keep.overlap_component.nunique(),'paired_replicate_labels':reps,'all_design_rows':len(result),'qc_counts':result.qc_status.value_counts().to_dict(),'target':'author normalized localization mutant minus exact190nt WT','target_tuning':False,'other_endpoint_fields_selected':False,'exact_author_REML_reconstructed':False,'raw_to_processed_note':'Source author code traces median normalization and REML; paired CPM contrasts reconstructed diagnostically; full author coefficient production not certified exact','mapped_outcome_sha256':sha256(ART/'GSE330741_mapped_outcomes.csv')})
    print(readj(OUT/'outcome_access_receipt.json'))

if __name__=='__main__':run()
