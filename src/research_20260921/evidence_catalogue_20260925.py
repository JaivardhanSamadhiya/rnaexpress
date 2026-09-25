"""Compile an explicitly curated claim ledger and existing-resource inventory.

This is evidence synthesis, not a search, experiment, metric pooling or meta-analysis.
Historical values are transcribed from named reports; SRLE risk rows are extracted
directly from saved JSON. Hashes identify exactly which evidence was summarized.
"""
from .evidence_io_20260925 import ROOT, sha256, read_json, save_json, save_csv, save
from pathlib import Path

R = 'reports/research_20260921/'
O = 'results/research_20260921/'


def compile_claims():
    rows = []
    def add(claim, dataset, metric, estimate, uncertainty, baseline, status, protocol, independence, caveat, source):
        path = ROOT / source
        if not path.is_file():
            raise FileNotFoundError(source)
        rows.append({'claim_id': 'C%03d' % (len(rows)+1), 'claim': claim, 'dataset': dataset,
            'analysis': source, 'metric': metric, 'estimate': estimate, 'uncertainty': uncertainty,
            'baseline': baseline, 'protocol_status': protocol, 'independent': independence,
            'confirmatory_exploratory': 'historical frozen evaluation' if protocol == 'frozen gate' else 'exploratory/descriptive or provenance',
            'support_category': status, 'supports_claim': {'strongly_supported':'yes, stated scope','bounded_supportive':'yes, bounded','unsupported':'no','unresolved':'unknown'}[status],
            'caveat': caveat, 'artifact_path': source, 'artifact_sha256': sha256(path)})
    historical = [
      ('Original pairwise selector improves intervention ranking','N-zip','rank percentile','.566 vs .624','not reported here','forward ExtraTrees','unsupported','reports/v2_failure_analysis.md','Linear pairwise differences cancel unchanged parent features; exposed three-parent lock cannot be reused.'),
      ('Parent-by-edit correction transfers reliably','historical development','rank percentile','fixed .662; nested .588','fold-dependent','forward/context controls','unsupported','reports/v2_nested_development_results.md','Initial fixed-center screen overstated robustness; nested evaluation did not sustain it.'),
      ('Structure features rescue selection','historical development','rank percentile','.539','see source','existing simple controls','unsupported','reports/v2_structure_screen.md','Predicted equilibrium structure did not supply reliable incremental selection benefit.'),
      ('TDP auxiliary learning rescues selection','historical development','rank percentile','.504','see source','no auxiliary training','unsupported','reports/v2_tdp_aux_screen.md','Auxiliary labels did not reliably transfer to the primary selection task.'),
      ('SpliceBERT rescues selection','historical development','rank percentile','.617','see source','simple sequence models','unsupported','reports/v2_2_splicebert_results.md','A richer pretrained representation did not establish required advantage.'),
      ('Extreme-contrast training rescues selection','historical development','rank percentile','.581','see source','original pairwise training','unsupported','reports/v2_3_extreme_contrast_results.md','Changing training contrast did not solve the decision/generalization problem.'),
      ('External neural pretraining rescues transfer','historical development','rank percentile','.562','see source','forward selector','unsupported','reports/v2_4_external_transfer_results.md','External pretraining did not pass transfer requirements.'),
      ('XGBoost external transfer rescues selection','historical development','rank percentile','direct .492; calibrated .621','see source','forward selector','unsupported','reports/v2_5_mikl_xgboost_transfer_results.md','Calibration improved a weak direct transfer but did not establish the intended gate.'),
      ('Nested context stack passes independent TDP decision gate','TDP historical lock','rank / regret','.6749 rank vs .6197; .3766 regret vs .2938','leave-best-gene rank advantage -.0269','forward predictor','unsupported','reports/tdp43_v2_locked_gate_results.md','Average rank improved while decision regret worsened and benefit depended on genes.'),
      ('Historical N-zip truth is sufficiently reconstructed','N-zip','coverage / effect discrepancy','5787 vs published 5679; SNV delta MAE .406972; max 9.349905','not an uncertainty interval','historical workbook','unresolved','reports/v3_5r_truth_reconstruction_verdict.md','Raw reads reconstructed but historical truth semantics failed certification; no further modeling authorized.'),
      ('Certified broad intervention selector beats metadata','v4 Phase B','regret','.4265 vs .4218; 46.95% units improved','see source','metadata','unsupported','reports/v4_phaseB_final_verdict.md','More rows did not remove source/position shortcuts or establish unseen-source transfer.'),
      ('Context-aware v4B2 clears required margins','v4 Phase B2','rank / regret gain','.0191 / .0011; 44.6% units improved','see source','strong simple controls','unsupported','reports/v4_phaseB2_final_verdict.md','Gains below .02/.01 margins; transfer and small edits remained weak.'),
      ('FinalShot mechanism model provides robust small-edit selection','FinalShot','rank / regret gain','.04229 / .04009; 54.46% units improved; small-edit regret gain -.0305','see source','direct and shuffled controls','unsupported','reports/finalshot_final_verdict.md','55% unit gate failed; small edits harmed; cell 1/4 and reporter 2/4 transfer; shuffled features retained gains.'),
      ('Mechanism-v2 adds biological specificity','certified three-source data','rank / regret gain','.0250 / .0252; random kmer rank gain .0286','regret CI [-.0076,.0592]','random and direct controls','unsupported','reports/mechanism_v2/final_verdict.md','No Holm-significant feature block, negative seed result and substantial worst-decile harm.'),
      ('Mechanism-v3 grammar/nonlinear rescue works','certified three-source data','coverage / rank / variability','grammar coverage 3.6%; untied rank .5029; best nonlinear rank gain .0693; seed SD .026','required seed SD <=.01','direct/simple controls','unsupported','reports/mechanism_v3/final_verdict.md','Sparse grammar and unstable nonlinear gains failed gates; estimated reliability is not proof of an absolute ceiling.'),
      ('Sequence predicts localization within represented reporter contexts','Moffatt','auROC / Spearman','.9503 / .799; composition .9306','seeds .9503/.9506/.9504','composition and shuffled labels','bounded_supportive','reports/mechanism_v4/final_verdict.md','Known-parent absolute prediction, not reliable selection of small edits or independent contexts.'),
      ('Rich sequence representation improves unseen-gene transfer','Moffatt','auROC','.6980 vs composition .7529; worst .5758','seed SD .0282','composition','unsupported','reports/mechanism_v4/final_verdict.md','Ten genes/eight parents; development exposure; failure cannot prove biological impossibility.'),
      ('Edit direction has predictive sequence signal across genes','Mikl','auROC','.7051; AU delta .6942; random projection .7094','worst fold .6423; 166 held-out genes across folds','AU and random projections','bounded_supportive','reports/mechanism_v5/final_verdict.md','Cross-validation in an exposed source; above-chance direction does not establish biological mechanism or pairwise decision advantage.'),
      ('Moffatt sequence rule transfers to Mikl','Moffatt to Mikl','Spearman / direction auROC','.0298 / .5407','Spearman p .0012','AU delta Spearman -.1044','unsupported','reports/mechanism_v5/final_verdict.md','Absolute transfer gates failed; beating a negatively correlated control is insufficient.'),
      ('Secondary TDP association confirms general transfer','Moffatt to TDP localization','Spearman','.2844','fold range -.039 to .568','frozen primary Mikl transfer','unsupported','reports/mechanism_v5/final_verdict.md','Secondary descriptive association exists, but no usable effect uncertainty and only 16 genes; not the primary confirmation test.'),
      ('SRLE order models improve over composition','SRLE','relative squared-error reduction','pair .2704287; short kmer .2736629; additive .0761770','pair [.20631,.33779]; conditional permutation p=.001','composition','bounded_supportive',R+'srle_evidence_ledger_20260924.md','855 eligible held-out six-mers in 70 composition classes; same reporter experiment.'),
      ('SRLE pair model outperforms short kmer prediction','SRLE','relative error reduction','-.00445276','[-.0553844,.0467641]','1-3-mer model','unsupported',O+'robustness_result.json','No clear predictive advantage over the simpler representation.'),
      ('SRLE fixed swaps beat exact uniform regret in each constituent replicate','SRLE','regret gain','pair .231026/.253421; kmer .219908/.221285','pair [.163987,.289416]/[.196425,.307351]','matched uniform candidate selection','bounded_supportive',O+'raw_swap_result.json','592 parents/60 classes; overlapping candidates; repeats contributed to source aggregate; posthoc.'),
      ('SRLE pair model outperforms short kmer decisions','SRLE','paired regret gain','.011118/.032136','[-.043523,.068476]/[-.023785,.093971]','1-3-mer model','unsupported',O+'raw_swap_result.json','Intervals include zero in both constituent replicates.'),
      ('SRLE raw replicate measurements are consistent','SRLE','Pearson r','.8201358','descriptive; no formal ceiling estimated','replicate 1 vs 2','bounded_supportive',O+'raw_replication_result.json','Repeatability of scores does not prove reliability of small differences or independent replication.'),
      ('SRLE lookup rule transfers to neuronal reporters','Arora','regret gain','-.146','[-.232,-.060]','A/G score','unsupported',R+'srle_evidence_ledger_20260924.md','All four cell/reporter contexts negative; endpoint differs from nuclear/cytoplasmic fractionation.'),
      ('SRLE short kmer selector passes single-substitution transfer','SIRLOIN','regret','.44733 vs CCC .52521 and CCTCCC .49092','positive margins in both parents/replicates','CCC and CCTCCC','unsupported',R+'continuation_public_data.md','Gain .04360 against CCTCCC missed frozen .05 margin; only two parents; a small positive is not a passed gate.'),
      ('Target calibration passes original development gate','Ron/Ulitsky context study','regret gain','.04446','[-.00891,.09265]','target-only sequence','unsupported',R+'srle_evidence_ledger_20260924.md','20 development groups; 22 confirmation groups remain closed; circular-context deterioration.'),
      ('Source context information can help target prediction','Ron/Ulitsky source-only diagnostic','regret gain','.04525','[.02282,.06626]','tuned target-only','bounded_supportive',R+'srle_evidence_ledger_20260924.md','Reused source data; versus sibling-source gain .01112 [-.00320,.02617], so calibration necessity unestablished.'),
      ('Worst-context optimization improves over simple averaging','Ron/Ulitsky source-only diagnostic','regret','.40564 vs .37745; uniform .49218','gain vs averaging -.02819 [-.06382,.00537]','mean predicted ranks','unsupported',R+'faraway_and_robust_context_checkpoint.md','Beats uniform but fails all-comparator criterion; average performance is not all-context control.'),
      ('Sequence interaction improves intron configuration selection','Faraway','regret','.43639 vs quadratic .41780 / categorical .41928','see source','intron-pattern controls','unsupported',R+'faraway_and_robust_context_checkpoint.md','Primary gate failed; barcode and intron identity/length confounding limit causal attribution.'),
      ('Fixed simple intron selectors beat random at 8 hours','Faraway','regret gain','quadratic .07159; categorical .05814','[.00461,.13916]/[.00986,.10752]','uniform; additive regret .42484 is competitive','bounded_supportive',R+'faraway_and_robust_context_checkpoint.md','Secondary frozen gate passed; all 207 genotypes previously measured, one protein context; not new-genotype or SRLE confirmation.'),
      ('SRLE model transfers to HeLa fragment selection','Shukla','regret','.56930 vs composition .51826 / CCC .48303 / random .5','11 families below required 12','composition and CCC','unsupported',R+'checkpoint_20260923.md','205 fragments; repeatability Spearman -.00417 and raw/processed mapping unresolved, so no clean biological failure inference.'),
      ('Shukla raw counts reproduce processed endpoint','Shukla Total1','correspondence','31 processed zeros have 157-22579 exact reads; Spearman .13114','full 9603871 reads inspected','published Total1 table','unresolved',R+'checkpoint_20260923.md','Disagreement does not identify the cause or prove author error; reserved outcomes remain closed.'),
      ('Old SEERS RNA prefix validates transfer','SEERS Method1','regret gain','.05051; pair regret .50789','[-.14354,.28447]','exact random .5','unresolved',R+'checkpoint_20260923.md','Only 5 eligible groups/25 candidates vs required20; one biological sample; incomplete archive; primary screen did not pass.'),
      ('Relaxed SEERS quality restores transfer','SEERS Method1 exploratory','regret','.5918','20 groups/104 sequences; see source','uniform .5','unsupported',R+'dna_provenance_checkpoint_20260924.md','Posthoc Q20 sensitivity cannot rescue primary Q30 screen and was not promoted.'),
      ('mutREL rows are clean single-mutant measurements','mutREL','mutation-event inventory','401 substitution; 96 deletion; 1 WT','read-level multiple-mutation rule unknown','author event table','unresolved',R+'mutrel_provenance_review_20260924.md','Event aggregation may differ from isolated genotypes; no numerical outcomes admitted.'),
      ('Wen sequences support an admitted export-selection test','Wen speckle study','sequence metadata','81 plasmids verified','transcript boundaries/mapping unresolved','nuclear/cytoplasmic endpoint','unresolved',R+'checkpoint_20260922.md','Speckle partition is a different endpoint; outcomes remain closed; previously inspected resource.'),
      ('Complete SRLE author count-to-Table5 pipeline reconstructed','SRLE','provenance status','PARTIAL','third replicate, normalization, pooling and export unresolved','authoritative raw-to-table reconstruction','unresolved','artifacts/research_20260925/srle_lineage_result.json','Exact benchmark-table agreement does not resolve measurement-production lineage.'),
      ('SRLE benchmark faithfully uses Table5 and archived arithmetic','SRLE','maximum absolute difference','0 for 4096 table values and both replicate score vectors','deterministic computation check','published table / archived scores','strongly_supported','artifacts/research_20260925/srle_lineage_result.json','Eight raw files rehashed; raw extraction not rerun this turn; not validation of source biology.'),
    ]
    for claim,dataset,metric,value,ci,base,status,source,caveat in historical:
        protocol = 'frozen gate' if status == 'unsupported' and ('mechanism_' in source or 'final_verdict' in source or 'locked_gate' in source) else 'see original protocol; status preserved'
        add(claim,dataset,metric,value,ci,base,status,protocol,'No new independent confirmation; see caveat',caveat,source)
    fixed = read_json(ROOT / (O+'srle_fixed_choice_risk_result_20260924.json'))
    for model in ('composition','position_additive','kmer123','position_pair'):
        for direction in ('-1','1'):
            for metric in ('fraction_positive_both','fraction_negative_both'):
                item = fixed['models'][model][direction]['paired_replicates'][metric]
                add('Observed paired-replicate '+metric, 'SRLE', model+'; direction='+direction,
                    item['estimate'], str(item['descriptive_ci95']), 'exact matched uniform reported separately',
                    'bounded_supportive','posthoc frozen arithmetic','No; constituents of shared source aggregate',
                    'Equal-class average; 592 parents/60 classes; no abstention; overlapping neighborhoods; wrong direction is not toxicity.',
                    O+'srle_fixed_choice_risk_result_20260924.json')
    add('Existing evidence establishes a transferable biological mechanism','all sources','specificity/generalization','not established','independent compatible test missing','composition, short motifs and random representations','unsupported','synthesis; no new gate','No','Predictive signal and a benchmark contribution do not establish causality, complete novelty or universal control.',R+'srle_claim_evidence_map_20260924.md')
    save_csv('claim_evidence_ledger.csv', rows)
    save_json('claim_evidence_ledger.json', rows)
    lines = ['# Complete major-claim ledger', '', 'AI-authored evidence synthesis. Preserve original gates; no new model or pooled cross-assay metric.', '',
             '| ID | Approach / claim | Result | Interpretation / limitation |', '|---|---|---|---|']
    for row in rows:
        lines.append('| {claim_id} | {claim} | {estimate}; uncertainty: {uncertainty} | **{support_category}**. {caveat} [Evidence]({artifact_path}) |'.format(**{k:str(v).replace('|','/') for k,v in row.items()}))
    # Links resolve from the project root in the companion report; CSV paths are project-relative.
    save('claim_evidence_ledger.md', ('\n'.join(lines)+'\n').encode())
    return rows


def compile_inventory():
    # Unknown quantities intentionally stay unknown: no sealed worksheet is read for completeness.
    entries = [
      ('SRLE','10.34133/csbj.0107; HRA016642','six-mer reporter fractionation','HBB reporter; human cells','nuclear/cytoplasmic NRS','1 reporter','4096','composition-preserving two-position swaps','3 labels; two reconstructed; third ambiguous','exhaustive Table5','published aggregate + four reconstructed libraries','exact table join; production incomplete','trained/scored/features/hypotheses','benchmark only','fully exposed; not independent',R+'srle_measurement_provenance_review_20260924.md'),
      ('N-zip','N-zip historical source; see truth report','3UTR reporter','neuronal reporter','neurite/soma','15 historical;13 partial reconstruction','3453 uncertified SNVs','SNV and other edits','3 source replicates','reconstructed design','historical outcomes quarantined','failed truth certification','historical training and lock exposure','ineligible','uncertified historical truth; exposed', 'reports/v3_5r_truth_reconstruction_verdict.md'),
      ('Mikl','GSE173098','3UTR reporter MPRA','neuronal cells','localization','166 genes in v5','see certified manifest','mixed edits/150nt fragments','source-dependent','certified development table','already analyzed','certified scope only','extensive model/feature development','development only','exposed; not new confirmation','reports/mechanism_v5/final_verdict.md'),
      ('Moffatt','GSE334718','neuronal reporter MPRA','neuronal cells','neurite localization','10 genes/8 parents','46291','mixed 260nt alternatives','source-dependent','certified development table','already analyzed','certified scope only','v2-v5 training/evaluation','development only','exposed; small context count','reports/mechanism_v4/final_verdict.md'),
      ('TDP localization','GSE288185','3UTR reporter','TDP study cells','localization','16 genes in v5 secondary','4566 secondary rows','multibase/260nt','effect uncertainty unavailable','certified development table','already analyzed; EV5 stability closed','localization only','historical lock then development','development only','exposed; stability quarantine distinct','reports/mechanism_v5/final_verdict.md'),
      ('Astrocyte','SN-MPRA; existing protected inventory','SNV reporter','astrocyte','protected endpoint','not inspected','not inspected','SNV','not inspected','protected','closed','not newly inspected','schema rows/legacy worksheet and unsolicited literature exposure; no new evaluation','sealed, not certified pristine','strict requested no-prior-influence criterion not established',R+'literature_scope_followup_20260924.md'),
      ('Arora','neuronal reporter study; existing pilot','reporter fractionation','CAD/N2A; FF/GFP','neurite/soma','13 eligible genes x4 assay settings','260nt alternatives; see pilot','fragments/mixed changes','1/2 used;3/4 reserved','downloaded design','discovery open','admitted','external pilot already failed','not new','endpoint change; exposed outcomes',R+'srle_evidence_ledger_20260924.md'),
      ('SIRLOIN','10.15252/embj.2020106357','NucLibC reporter','human reporter cells','nuclear enrichment','2 SNV parents','227 SNVs;4205 mapped designs','single substitution','1/2 used;3/4 +NucLibB closed','exact FASTA/workbook match','discovery open','verified design join','source-only transfer gate evaluated','not new','failed margin; only2 parents; prior exposure',R+'continuation_public_data.md'),
      ('RNA-context','10.1038/s41467-022-30183-0','context-varying reporter','human reporter cells','nuclear/cytoplasmic across4 contexts','133 metadata genes;20 dev/22 held groups','8158 valid sequence metadata rows','109/141nt fragments','see original admitted protocol','available','source/dev open; confirmation closed','admitted with exclusions','calibration/learning curves/robustness tested','development only','prior hypothesis/model influence; reserved subsets are not new resources',R+'checkpoint_20260922.md'),
      ('Shukla','10.15252/embj.201798452','fragment reporter fractionation','HeLa','nuclear/total','12 genes/11 families','205 eligible fragments','fragment alternatives','1-3 open;4-6 closed','277 opened identifiers','open subset; Total1 raw inspected','raw/processed relation unresolved','transfer and reliability evaluated','unsuitable now','mapping ambiguity and inadequate units',R+'checkpoint_20260923.md'),
      ('SEERS','HRA008408; 10.1101/2025.06.09.658412','random insert reporter','L6 sample in archive','nuclear/cytoplasmic','5 eligible composition groups;one bio sample','25 Q30 candidates','six-mers grouped by composition','numbered runs not independent biology','DNA prefixes','RNA R1 prefix open','old/new protocol correspondence unresolved','Q30 screen and Q20 sensitivity evaluated','not new; primary inconclusive','too few groups; partial reads; Method2 processed absent in inspected tree',R+'checkpoint_20260923.md'),
      ('Faraway','10.1038/s41586-025-09568-w; E-MTAB-13329','intron configuration reporter','single protein reporter context','nuclear/cytoplasmic','26 original dev panels;28 at8h','207 genotypes at8h','intron position/identity and synonymous pattern','3 labels at8h','reconstructed insert, variable barcodes','original dev +8h open; confirmation closed','processed ratios verified; barcode map incomplete','primary failed; secondary passed','bounded repeat collection','all target genotypes already measured; not SRLE small-edit replication',R+'faraway_and_robust_context_checkpoint.md'),
      ('mutREL','10.1038/s41586-020-2105-3; GSE107131','random mutagenesis/event counting','NXF1 reporter','compartment localization','1 reference','401sub+96del+WT events','event not isolated-genotype semantics','unresolved','162nt reference recovered','numeric outcomes closed','multi-mutation handling unresolved','metadata/provenance/hypothesis review already','unadmitted','one context and event-to-genotype ambiguity',R+'mutrel_provenance_review_20260924.md'),
      ('Wen speckle','PMC12962856','speckle-localization reporters','see existing paper','nuclear-speckle partition','not established as eligible units','81 plasmids','varied constructs','not established','plasmids verified; RNA boundaries unresolved','numeric outcomes closed','transcript/outcome mapping unresolved','metadata and hypothesis review','unadmitted','different endpoint; not previously unseen resource',R+'checkpoint_20260922.md'),
      ('External stability','GSE217518; Su/Wang eLife2025','RNA decay MPRA','HEK293T/SH-SY5Y','stability, not localization','see source','6555 designed;1022 retained pairs','155nt ref/mut pairs','time-course','mapped retained cohort','external fitting already failed','admitted stability scope','feature development/admission attempted','incompatible validation endpoint','not localization; exposed; predictor gate failed','reports/mechanism_v2/external_resource_audit.md'),
      ('Pretrained model resources','RBPNet/3UTRBERT/Parnet/BRIDGE; existing audits','external feature models','varied','not measured edit choice dataset','not applicable','not applicable','not applicable','not applicable','models/metadata','no matched validation cohort','Parnet checkpoint and BRIDGE compatibility unresolved','feature/resource development','not a validation dataset','weights or embeddings do not supply independent measured alternatives','reports/mechanism_v2/external_resource_audit.md'),
    ]
    fields = ['resource','citation_resource','assay','organism_cell_system','localization_endpoint','contexts','variants','edit_sizes','replicates','sequence_availability','measurement_availability','mapping_quality','previous_exposure','suitability','fatal_limitations','evidence_path']
    rows = [dict(zip(fields, e)) for e in entries]
    for row in rows:
        row['evidence_sha256'] = sha256(ROOT / row['evidence_path'])
        row['qualifies_as_genuinely_unexposed'] = False
        row['inventory_scope'] = 'existing project resources only; new discovery blocked; not exhaustive globally'
    save_csv('validation_resource_inventory.csv', rows)
    save_json('independent_validation_decision.json', {
        'decision': 'NO QUALIFIED RESOURCE IN REVIEWED EXISTING INVENTORY', 'inventory_rows': len(rows),
        'new_discovery': 'BLOCKED BY PRIOR AUTOMATIC REVIEW; NOT RETRIED',
        'global_search_exhaustive': False, 'external_protocol_frozen': False, 'external_evaluation_run': False,
        'reason': 'All reviewed resources have prior exposure, unresolved mapping, incompatible endpoint or inadequate units. Closed subsets do not establish a genuinely new resource.',
        'future_admission': 'Requires authoritative measured-variant mapping, matching endpoint, enough independent contexts and a documented no-development-exposure scope before freezing an evaluation.'})
    return rows


if __name__ == '__main__':
    claims = compile_claims()
    inventory = compile_inventory()
    save_json('catalogue_receipt.json', {'claims': len(claims), 'resources': len(inventory),
        'compiler_sha256': sha256(Path(__file__)), 'basis': 'Explicitly curated historical synthesis; exact saved JSON for risk; no new biological calculation',
        'category_counts': {k: sum(r['support_category']==k for r in claims) for k in sorted({r['support_category'] for r in claims})}})
    print('Compiled', len(claims), 'claims and', len(inventory), 'existing resources')
