"""Frozen exploratory old-archive, single-biological-sample transfer screen."""
from .common import ROOT,sha256,write_json,write_new
from .seers_dna_qc import records,insert
from .mutrel_read_qc import prefix
from .sirloin_transfer import window_mean,motif_count
import json,sys
from datetime import datetime,timezone
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OUT=ROOT/'results/research_20260921'
DATA=ROOT/'data/external/research_20260921'
NAME='seers_prefix_transfer'
MODELS=['srle_kmer123','srle_pair','ccc','cctccc']


def regret(y,p):
    y=np.asarray(y);p=np.asarray(p)
    if len(y)<5 or np.ptp(y)<=0:raise ValueError('Ineligible group')
    return float(np.mean([(np.max(sign*y)-np.mean(sign*y[sign*p==np.max(sign*p)]))/np.ptp(y) for sign in [1,-1]]))


def prepare():
    f=pd.read_csv(OUT/'seers_dna_16MiB_inserts.tsv',sep='\t')
    f=f[f.concordant_Q30_pairs>=5].copy()
    f['group']=['_'.join(str(s.count(b)) for b in 'ACGT') for s in f.sequence]
    f=f.groupby('group',group_keys=False).filter(lambda g:len(g)>=5).reset_index(drop=True)
    if len(f)!=241 or f.group.nunique()!=45:raise ValueError('DNA candidate boundary changed')
    source=pd.read_csv(OUT/'robustness_predictions.csv').set_index('kmer')
    for name,column in [('srle_kmer123','kmer123'),('srle_pair','position_pair')]:
        lookup=source[column].to_dict()
        f[name]=[window_mean(s,lookup) for s in f.sequence]
    for name,motif in [('ccc','CCC'),('cctccc','CCTCCC')]:
        f[name]=[motif_count(s,motif) for s in f.sequence]
    write_new(OUT/(NAME+'_predictions.csv'),f.to_csv(index=False,lineterminator='\n').encode())
    paths=[ROOT/'src/research_20260921'/n for n in ['seers_prefix_transfer.py','seers_dna_qc.py','seers_dna_expand.py','common.py','mutrel_read_qc.py','sirloin_transfer.py','test_seers_dna_qc.py','test_seers_prefix_transfer.py']]
    paths += [ROOT/'reports/research_20260921/seers_prefix_transfer_spec.md',OUT/(NAME+'_predictions.csv'),OUT/'robustness_predictions.csv',OUT/'seers_dna_16MiB_qc.json',OUT/'seers_dna_16MiB_inserts.tsv']
    paths += [DATA/n for n in ['seers_gsa_runs','seers_L6_biosample','seers_raw_checksums','HRR1883397_f1.first16MiB.gz','HRR1883397_r2.first16MiB.gz']]
    write_json(OUT/(NAME+'_freeze.json'),{'created_utc':datetime.now(timezone.utc).isoformat(),'RNA_outcomes_read':False,'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths}})
    print('Frozen 241 candidate predictions in 45 composition groups; RNA outcomes unexamined.',flush=True)


def verify():
    for path,h in json.loads((OUT/(NAME+'_freeze.json')).read_text())['files'].items():
        if sha256(ROOT/path)!=h:raise ValueError('Frozen file changed: '+path)


def count_run(run,allowed):
    if run not in ['HRR1883393','HRR1883401']:raise PermissionError('Run outside frozen RNA scope')
    def fetch(mate):
        name=f'{run}_{mate}.first16MiB.gz'
        url=f'https://download.cncb.ac.cn/gsa-human/HRA008408/{run}/{run}_{mate}.fq.gz'
        return records(prefix(url,name,16*1024**2)),name
    with ThreadPoolExecutor(max_workers=2) as pool:
        data=list(pool.map(fetch,['f1','r2']))
    counts=Counter();both=discordant=0
    for a,b in zip(data[0][0][0],data[1][0][0]):
        if a[0]!=b[0]:raise ValueError('Mates not synchronized')
        x=insert(a[1],a[2]);y=insert(b[1],b[2],True)
        if x is not None and y is not None:
            both+=1
            if x!=y:discordant+=1
            elif x in allowed:counts[x]+=1
    return counts,{'run':run,'paired_records':min(len(x[0][0]) for x in data),'both_Q30':both,'discordant':discordant,'candidate_reads':sum(counts.values()),'prefix_sha256':{n:sha256(DATA/n) for _,n in data},'full_archive_MD5_verified':False,'purpose':'Exploratory localization counts under frozen screen; generic prefix receipt purpose is superseded by this record.'}


def evaluate():
    verify()
    f=pd.read_csv(OUT/(NAME+'_predictions.csv'));allowed=set(f.sequence)
    # Fractions processed sequentially to bound memory; mate retrieval parallel.
    c,cqc=count_run('HRR1883393',allowed)
    n,nqc=count_run('HRR1883401',allowed)
    f['cytoplasm']=[c[s] for s in f.sequence];f['nucleus']=[n[s] for s in f.sequence]
    f['eligible_counts']=(f.cytoplasm>=10)&(f.nucleus>=10)
    f['log2_nuclear_cytoplasmic']=np.log2((f.nucleus+.5)/(f.cytoplasm+.5))
    rows=[];excluded=[]
    for key,g in f.groupby('group'):
        g=g[g.eligible_counts]
        if len(g)<5 or np.ptp(g.log2_nuclear_cytoplasmic.to_numpy())<=0:
            excluded.append({'group':key,'remaining_candidates':len(g)});continue
        row={'group':key,'candidates':len(g)}
        for model in MODELS:row[model]=regret(g.log2_nuclear_cytoplasmic,g[model])
        row['random']=.5;rows.append(row)
    result={'scope':'Exploratory old-protocol archive, one biological sample, partial RNA files. Not biological confirmation.',
        'eligible_groups':len(rows),'excluded_groups':excluded,'fraction_QC':[cqc,nqc],
        'biological_confirmation':False,'sealed_data_accessed':False,'exploratory_signal':False}
    if rows:
        d=pd.DataFrame(rows);draws=np.random.default_rng(20260923).integers(0,len(d),(5000,len(d)))
        result['mean_regret']={m:float(d[m].mean()) for m in MODELS+['random']}
        comparisons={}
        passed=len(d)>=20
        for baseline in ['random','ccc','cctccc']:
            gain=(d[baseline]-d.srle_kmer123).to_numpy();ci=np.quantile(gain[draws].mean(axis=1),[.025,.975])
            comparisons[baseline]={'mean_gain':float(gain.mean()),'descriptive_group_ci95':ci.tolist()}
            passed=passed and gain.mean()>=.05 and ci[0]>0
        result['primary_comparisons']=comparisons;result['exploratory_signal']=bool(passed)
        eligible=f[f.group.isin(d.group)&f.eligible_counts]
        result['eligible_sequences']=len(eligible)
        result['descriptive_overall_spearman']={m:float(spearmanr(eligible[m],eligible.log2_nuclear_cytoplasmic).statistic) for m in MODELS if eligible[m].nunique()>1}
        write_new(OUT/(NAME+'_group_metrics.csv'),d.to_csv(index=False,lineterminator='\n').encode())
    write_new(OUT/(NAME+'_counts.csv'),f.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/(NAME+'_result.json'),result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':{'prepare':prepare,'evaluate':evaluate}[sys.argv[1]]()
