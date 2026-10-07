"""Describe the frozen results without changing experiments or acceptance rules."""
from .common import *
from .route_coverage import pairs_for
import sys, io

def table(frame):
    columns=list(frame.columns)
    rows=['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
    for values in frame.itertuples(index=False,name=None):
        rows.append('| '+' | '.join(f'{v:.6f}' if isinstance(v,float) else str(v) for v in values)+' |')
    return '\n'.join(rows)

def run():
    prefit=freeze_check()
    verdict=readj(OUT/'gate_verdict.json')
    verification=readj(OUT/'verification_receipt.json')
    assert verification['status']=='PASS'
    comp=pd.read_csv(ART/'model_comparison.csv')
    macro=comp.groupby('model')[['regret','avoidable_wrong','wrong_direction']].mean().reset_index()
    old=pd.read_csv(ROOT/'artifacts/cross_assay_20260927/model_comparison.csv')
    old=old[old.stage.eq('held_assay')&old.model.eq('interaction_3')]
    macro=pd.concat([pd.DataFrame([{'model':'historical_H0','regret':old.regret.mean(),
        'avoidable_wrong':old.avoidable_wrong.mean(),'wrong_direction':old.wrong_direction.mean()}]),macro],ignore_index=True)
    csvsave(ART/'macro_comparison.csv',macro)
    frame,_=load();coverage=[]
    for policy in ('historical','connected'):
        a,b,y,w,study=pairs_for(frame,policy)
        used=set(a)|set(b)
        for context,g in frame.groupby('parent_context_id',sort=True):
            count=sum(i in used for i in g.index)
            coverage.append({'policy':policy,'dataset':g.dataset.iloc[0],
                'biological_component':g.biological_component.iloc[0],'parent_context_id':context,
                'candidate_rows':len(g),'directly_supervised_candidates':count,'fraction':count/len(g)})
    cv=pd.DataFrame(coverage);csvsave(OUT/'pair_coverage.csv',cv)
    csm=cv.groupby(['policy','dataset'])[['candidate_rows','directly_supervised_candidates']].sum().reset_index()
    csm['fraction']=csm.directly_supervised_candidates/csm.candidate_rows
    csvsave(ART/'pair_coverage.csv',csm)
    selections=[]
    for track in TRACKS:
        for fold in readj(OUT/track/'folds.json'):
            selections.append({'track':track,'held_assay':fold['held'],'selected_configuration':fold['selected_configuration']['id'],
                'inner_macro_regret':fold['inner_macro_regret']})
    csvsave(ART/'source_selected_configurations.csv',pd.DataFrame(selections))
    per=comp.pivot(index='dataset',columns='model',values='regret').reset_index()
    per['historical_H0']=per.dataset.map(old.set_index('dataset').regret)
    per=per[['dataset','historical_H0']+TRACKS]
    text='# Parallel generalization results, 7 October 2026\n\n'
    text+=f"**{verdict['status']} under the unchanged strict development gate.** These are repeatedly exposed development experiments, not independent confirmation.\n\n"
    text+='## Macro decisions\n\n'+table(macro)+'\n\n## Held assay regret\n\n'+table(per)+'\n\n'
    text+='## Why settings are not target-selected\n\nEach of the twenty outer track/assay models uses a configuration selected only by the three source-assay holdouts. Their input and biological exclusion hashes, inner scores and exact coefficients are retained. Four of the tracks use the same source observations; the endpoint track additionally uses 223 previously exposed SIRLOIN C1/C2 measurements for nuclear training only. Its gain, if any, cannot be assigned solely to endpoint conditioning. No target sign, motif, loss, penalty or window was chosen after outer results.\n\n'
    if (OUT/'matched_control/run_complete.json').exists():
        matched=pd.read_csv(OUT/'matched_control/comparison_vs_enriched.csv')
        text+='## Matched representation diagnostic\n\nThe scaling track chooses between two normalizations, so an additional pair-only short-feature comparator reuses the existing 36 inner fit scores and source-selects among exactly the three frozen pair-RMS penalties. Its four outer fits were separately frozen at `5a5e038` after the first results; this is a postfit descriptive control and cannot rescue or change the primary gate.\n\n'+table(matched)+'\n\n'
    text+='## Context and annotation audit\n\nThe outcome-free reporter audit verifies 20-base flanks on each side of the SRLE six-mer (a 46-nt local synthesis template), while full mature reporter RNA remains uncertified. Published SRLE methods identify HEK293T; the historical canonical cell field says MCF7. That annotation is preserved as historical evidence and must not be used as a factual cell descriptor in future contextual models. None of the five current utilities uses that cell field, so the mismatch does not numerically invalidate their rankings. See reporter_context_audit.md.\n\nExact paired-context diagnostics cover 6,880 Mikl edits across 187 genes and 2,586 Moffatt edits across six genes. Gene-macro pair-order agreement is approximately .5343 and .5492. Some Mikl preferences oppose despite the fixed replicate-support diagnostic; this identifies ambiguity for identical sequence inputs, but cannot distinguish biological context from measurement/provenance artifacts. These postfit diagnostics do not choose a model or relax its gate. See context_diagnostic.md.\n\n'
    text+='## Pair supervision coverage\n\n'+table(csm)+'\n\nThe coverage-oriented roster is sampled without labels; exact training ties are then omitted. The table reports actual non-tied training participation, not a guarantee of a connected labeled graph. Increased coverage is not proof that a learned predictor transfers.\n\n'
    text+='## Verification and limits\n\n'+f"{verification['models']} fit checkpoints; {verification['candidate_scores_replayed']:,} scores replayed (maximum error {verification['maximum_score_error']:.3g}); {verification['selected_decisions_checked']:,} selections/regrets/wrong-direction decisions independently reconstructed. The historical {verification['historical_H0_decisions_reproduced']:,} H0 choices/regrets reproduced. All {len(prefit['files'])} unique prefit hashes, prior bundles and {verification['unrelated_modified_files_unchanged']} pre-existing modified files remain unchanged. Twenty-eight new scoped tests and nine prior scoped tests passed. The freeze command's initial path count included two repeated entries; the authoritative manifest contains 45 unique paths, all verified.\n\n"
    text+='Mikl contains most independent genes; Astrocyte contains two, Moffatt six, SRLE one reporter. All four are spent development sources; auxiliary nuclear diversity is only two parents. SRLE has no admitted full HBB reporter sequence in these inputs. Ratio endpoints and processing differ, source raw-to-author reconstruction is incomplete, and no new biological experiment was created. A failure is evidence about these fixed methods, not an impossibility theorem. A passing gate is a development filter, not a calibrated probability, causal mechanism, novelty claim or successful independent test.\n'
    save(REP/'results.md',text.encode())
    gate='# Frozen generalization gate\n\n'+f"Verdict: **{verdict['status']}**. Numeric conditions are exactly those frozen at `53553f2`; none was changed after results.\n\n"
    for r in verdict['tracks']:
        gate+=f"## {r['track']}\n\nMacro regret {r['macro_regret']:.6f}; helped {r['assays_helped_vs_H0']}/4, harmed {r['assays_harmed_vs_H0']}/4 vs H0. Pass: {r['passes']}. Descriptive gain interval {r['gain_ci']}.\n\n"
        gate+=table(pd.DataFrame([{'criterion':k,'passes':v} for k,v in r['checks'].items()]))+'\n\n'
    save(REP/'gate_verdict.md',(gate.rstrip()+'\n').encode())
    status='# Current generalization status\n\n'+f"**{verdict['status']} for five newly frozen routes.** The broad research goal remains unconfirmed by an independent compatible biological experiment.\n\n"
    status+=table(macro[['model','regret']])+'\n\n'
    status+='Completed: independent review of all 73 prior ledger claims; code/metric/scaling/pair-coverage audit; primary literature and availability review; five source-selected experiments; biological exclusion checks, exact score/choice replay, and evidence preservation. The old negative results remain archived, while overstatements of impossibility and biological independence are explicitly corrected in historical_review.md.\n\n'
    status+='New factual findings: the SRLE cell annotation conflicts with the published HEK293T methods; a 46-nt local synthesis context is now sequence-certified; identical paired-cell/reporter sequences show substantial ordering disagreement. The original cell annotation did not enter these five utilities. Additional four-fit pair-scaled controls also failed to establish distributed value from the longer or literature-defined motifs. These findings motivate separate context/ensemble/encoder experiments rather than further retuning this grid. Preparation is proceeding in the independent generalization_next_20261007 namespace.\n\n'
    status+='Next falsifiable work remains: restore authoritative full reporter context and mutation/measurement lineage; test complete-context accessibility or a consistently audited frozen encoder with matched controls; establish context-dependent directions on gene/allele-excluded paired cell assays. A genuinely independent compatible edit experiment is needed for confirmation; transcript-localization accuracy alone cannot validate an edit selector. These are concrete remaining hypotheses, not guaranteed rescue paths. The five-track grid and its gates must not be varied after seeing the results.\n\n'
    status+='No money, scheduled tasks, external messages, reserved outcomes or unfiltered pytest were used. See protocol.md, results.md, gate_verdict.md, literature_routes.md, historical_review.md and the verification/delivery receipts.\n'
    save(REP/'final_status.md',status.encode())
    reproduction='# Reproduce and preserve\n\nPrefit commit `53553f2` pins 45 unique files, exact four-assay rows and five route definitions. Use bundled Codex Python from the project root with PYTHONDONTWRITEBYTECODE=1, PYTHONIOENCODING=utf-8 and OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=2. Scientific dependencies are the existing isolated Mechanism-v2 runtime.\n\n'
    reproduction+='Commands: `-u -m src.generalization_20261007.tests`; original prefit preparation/freeze is already completed and must not replace old files. Each track was run once through `-u -m src.generalization_20261007.engine <track>` (scaling, representation, mechanism, coverage, endpoint), then gate, verify, report and package. Completed tracks refuse another run; saved fold models permit an interrupted run to resume without refitting differing coefficients. No unfiltered pytest.\n\n'
    reproduction+='The source-only inner scores select each outer configuration. All model JSONs include exact coefficient/scaling values, row hashes and the training study/component inventory; endpoint models additionally include auxiliary purge ledgers. Predictions and decision metrics are deterministic gzip/CSV artifacts. Saved feature NPZs and row index reproduce input joins; the prior immutable archives supply canonical data provenance. The archive is not a standalone Python environment or a replacement for original protected data. Old plots/verdicts and user edits remain unchanged.\n'
    save(REP/'reproducibility.md',reproduction.encode())
    # Scientific comparison figure; standalone PNG/SVG, no generative image model.
    plot_runtime=ROOT/'data/interim/research_20260921/plot_runtime'
    if plot_runtime.exists():sys.path.insert(0,str(plot_runtime))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels={'astrocyte_gse330741':'Astrocyte (2 components)','mikl_gse173098':'Mikl (187 components)',
        'moffatt_gse334718':'Moffatt (6 components)','srle':'SRLE (1 reporter)'}
    fig,ax=plt.subplots(figsize=(11,5.4),layout='constrained')
    values=per.set_index('dataset').loc[STUDIES,['historical_H0']+TRACKS].to_numpy()
    im=ax.imshow(values,vmin=.35,vmax=.65,cmap='RdYlGn_r',aspect='auto')
    ax.set_xticks(range(6),['Historical H0','Scaling','Ordered 4–6mers','Motif architecture','Coverage/robust','Endpoint + nuclear source'],rotation=18,ha='right')
    ax.set_yticks(range(4),[labels[s] for s in STUDIES])
    for i in range(4):
        for j in range(6):ax.text(j,i,f'{values[i,j]:.4f}',ha='center',va='center',color='black')
    ax.set_title('Held-assay normalized selection regret — lower is better\nSource-only settings; repeatedly exposed development data',pad=14)
    fig.colorbar(im,ax=ax,label='Normalized regret',shrink=.85)
    for suffix in ('png','svg'):
        b=io.BytesIO();fig.savefig(b,format=suffix,dpi=180)
        payload=b.getvalue()
        if suffix=='svg':
            payload=('\n'.join(line.rstrip() for line in payload.decode().splitlines())+'\n').encode()
        save(ART/('held_assay_regret.'+suffix),payload)
    plt.close(fig)
    print('Reports and figure complete',flush=True)

if __name__=='__main__':run()
