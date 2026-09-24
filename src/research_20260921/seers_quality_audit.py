"""Post-hoc sensitivity on already-open prefixes; original gate unchanged."""
from .common import ROOT,sha256,write_json,write_new
from .seers_dna_qc import records,LEFT,RIGHT
from .seers_prefix_transfer import regret,MODELS,verify
from collections import Counter
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OUT=ROOT/'results/research_20260921'
DATA=ROOT/'data/external/research_20260921'
LEVELS=(0,20,25,30)


def call(seq,qual,reverse=False):
    if reverse:
        seq=seq.translate(str.maketrans('ACGTN','TGCAN'))[::-1];qual=qual[::-1]
    a=seq.find(LEFT)
    if a<0:return None
    a+=len(LEFT);b=seq.find(RIGHT,a)
    if b<0:return None
    value=seq[a:b]
    if len(value)!=45 or set(value)-set('ACGT'):return None
    return value,min(map(ord,qual[a:b]))-33


def count(run,allowed):
    if run not in ('HRR1883393','HRR1883401'):raise PermissionError('Outside already-open scope')
    paths=[DATA/f'{run}_{m}.first16MiB.gz' for m in ['f1','r2']]
    for p in paths:
        if sha256(p)!=json.loads(p.with_name(p.name+'.receipt.json').read_text())['sha256']:
            raise ValueError('Input changed')
    first,second=[records(p.read_bytes())[0] for p in paths]
    counts={q:Counter() for q in LEVELS};discordant=0
    for a,b in zip(first,second):
        if a[0]!=b[0]:raise ValueError('Unsynchronized mates')
        x=call(a[1],a[2]);y=call(b[1],b[2],True)
        if x is None or y is None:continue
        if x[0]!=y[0]:discordant+=1;continue
        if x[0] not in allowed:continue
        for q in LEVELS:
            if min(x[1],y[1])>=q:counts[q][x[0]]+=1
    return counts,{'run':run,'paired_records':min(len(first),len(second)),'all_quality_discordant_pairs':discordant,
        'candidate_pairs_by_quality':{str(q):sum(c.values()) for q,c in counts.items()}}


def summarize(frame,level,fixed_groups=None):
    records=[]
    for group,g in frame.groupby('group'):
        if fixed_groups is None:g=g[(g[f'nucleus_Q{level}']>=10)&(g[f'cytoplasm_Q{level}']>=10)]
        elif group not in fixed_groups:continue
        if len(g)<5:continue
        y=np.log2((g[f'nucleus_Q{level}'].to_numpy()+.5)/(g[f'cytoplasm_Q{level}'].to_numpy()+.5))
        if np.ptp(y)<=0:continue
        row={'group':group,'candidates':len(g),'quality':level}
        for m in MODELS:row[m]=regret(y,g[m])
        row['random']=.5;records.append(row)
    if not records:return {'eligible_groups':0},records
    d=pd.DataFrame(records);draws=np.random.default_rng(20260923).integers(0,len(d),(5000,len(d)))
    comparisons={}
    for baseline in ['random','ccc','cctccc']:
        gain=(d[baseline]-d.srle_kmer123).to_numpy()
        comparisons[baseline]={'mean_gain':float(gain.mean()),'descriptive_group_ci95':np.quantile(gain[draws].mean(axis=1),[.025,.975]).tolist()}
    return {'eligible_groups':len(d),'eligible_sequences':int(d.candidates.sum()),
        'mean_regret':{m:float(d[m].mean()) for m in MODELS+['random']},'primary_comparisons':comparisons},records


def run():
    verify()
    f=pd.read_csv(OUT/'seers_prefix_transfer_counts.csv');allowed=set(f.sequence)
    c,cqc=count('HRR1883393',allowed);n,nqc=count('HRR1883401',allowed)
    for q in LEVELS:
        f[f'nucleus_Q{q}']=[n[q][s] for s in f.sequence]
        f[f'cytoplasm_Q{q}']=[c[q][s] for s in f.sequence]
    if not np.array_equal(f.nucleus,f.nucleus_Q30) or not np.array_equal(f.cytoplasm,f.cytoplasm_Q30):
        raise ValueError('Q30 counts failed to reproduce frozen screen')
    original_groups=set(pd.read_csv(OUT/'seers_prefix_transfer_group_metrics.csv').group)
    fixed=f[f.group.isin(original_groups)&f.eligible_counts].copy()
    if len(fixed)!=25 or len(original_groups)!=5:raise ValueError('Original cohort changed')
    summaries={};fixed_summaries={};all_rows=[]
    for q in LEVELS:
        summaries[str(q)],rows=summarize(f,q);all_rows.extend(dict(r,cohort='quality_eligible') for r in rows)
        fixed_summaries[str(q)],rows=summarize(fixed,q,original_groups);all_rows.extend(dict(r,cohort='fixed_original_25') for r in rows)
    old=json.loads((OUT/'seers_prefix_transfer_result.json').read_text())
    if any(abs(summaries['30']['mean_regret'][m]-old['mean_regret'][m])>1e-12 for m in MODELS):
        raise ValueError('Q30 metric mismatch')
    retention={}
    for fraction in ['nucleus','cytoplasm']:
        support=f[f[fraction+'_Q20']>=10]
        rates=support[fraction+'_Q30']/support[fraction+'_Q20']
        retention[fraction]={'Q20_supported_sequences':len(support),'Q30_Q20_fraction_quantiles':np.quantile(rates,[0,.25,.5,.75,1]).tolist()}
    y20=np.log2((f.nucleus_Q20+.5)/(f.cytoplasm_Q20+.5));y30=np.log2((f.nucleus_Q30+.5)/(f.cytoplasm_Q30+.5))
    r={'scope':'Post-hoc quality sensitivity; same already-open prefixes; no independent confirmation.',
       'levels':list(LEVELS),'quality_specific_cohorts':summaries,'fixed_original_cohort':fixed_summaries,
       'retention':retention,'endpoint_Q20_Q30_spearman_all_241':float(spearmanr(y20,y30).statistic),
       'fraction_QC':[cqc,nqc],'Q30_counts_and_metrics_reproduced':True,'original_screen_still_inconclusive':True,
       'files':{str(p.relative_to(ROOT)):sha256(p) for p in [ROOT/'src/research_20260921/seers_quality_audit.py',ROOT/'reports/research_20260921/seers_quality_audit_spec.md']}}
    write_new(OUT/'seers_quality_audit_counts.csv',f.to_csv(index=False,lineterminator='\n').encode())
    write_new(OUT/'seers_quality_audit_groups.csv',pd.DataFrame(all_rows).to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/'seers_quality_audit.json',r)
    print(json.dumps(r,indent=2),flush=True)


if __name__=='__main__':run()
