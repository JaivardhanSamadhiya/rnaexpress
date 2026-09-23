"""Post-failure repeatability diagnostic on previously opened target rows only."""
from .shukla_transfer import ROOT,DATA,OUT,read_target,tied_regret
from .common import sha256,write_json,write_new
import json,subprocess,sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

NAME='shukla_reliability'


def freeze():
    paths=[ROOT/'src/research_20260921'/n for n in ['shukla_reliability.py','shukla_transfer.py','common.py']]
    paths += [ROOT/'reports/research_20260921/shukla_reliability_spec.md',
              OUT/'shukla_transfer_predictions.csv',OUT/'shukla_transfer_discovery.json',
              OUT/'shukla_transfer_discovery_eligible_ids.json',DATA/'shukla2018_counts.tsv.gz']
    write_json(OUT/(NAME+'_freeze.json'),{'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
               'scope':'Post-failure open-discovery-only diagnostic; cannot reopen any gate'})


def run():
    path=OUT/(NAME+'_freeze.json')
    for p,h in json.loads(path.read_text())['files'].items():
        if sha256(ROOT/p)!=h:raise ValueError(p)
    if subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)!=path.read_bytes():
        raise ValueError('Commit diagnostic first')
    ids=json.loads((OUT/'shukla_transfer_discovery_eligible_ids.json').read_text())['ids']
    f=pd.read_csv(OUT/'shukla_transfer_predictions.csv');f=f[f.id.isin(ids)].copy()
    y,accessed=read_target(DATA/'shukla2018_counts.tsv.gz',ids,(1,2,3))
    records=[]
    for accession,g in f.groupby('accession'):
        truth=np.array([y[name] for name in g.id])
        if len(g)<10 or not np.isfinite(truth).all():raise ValueError('Previously eligible set changed')
        for train in range(3):
            for test in range(3):
                if train==test:continue
                records.append({'accession':accession,'component':g.component.iloc[0],
                    'prediction_replicate':train+1,'evaluation_replicate':test+1,'candidates':len(g),
                    'spearman':float(spearmanr(truth[:,train],truth[:,test]).statistic),
                    'other_replicate_regret':tied_regret(truth[:,test],truth[:,train]),
                    'source_kmer_regret':tied_regret(truth[:,test],g.source_kmer.to_numpy())})
    d=pd.DataFrame(records)
    means=d.groupby('component')[['spearman','other_replicate_regret','source_kmer_regret']].mean()
    draws=np.random.default_rng(20260923).integers(0,len(means),(5000,len(means)))
    gains={}
    for name,values in [('over_random',.5-means.other_replicate_regret),
                        ('over_source_kmer',means.source_kmer_regret-means.other_replicate_regret)]:
        arr=values.to_numpy();gains[name]={'gain':float(arr.mean()),
            'descriptive_family_ci95':np.quantile(arr[draws].mean(axis=1),[.025,.975]).tolist()}
    result={'families':len(means),'gene_sets':int(d.accession.nunique()),'fragments':len(f),
        'mean_within_gene_cross_replicate_spearman':float(means.spearman.mean()),
        'mean_cross_replicate_selection_regret':float(means.other_replicate_regret.mean()),
        'mean_source_kmer_regret':float(means.source_kmer_regret.mean()),'comparisons':gains,
        'family_metrics':means.to_dict(orient='index'),'replicates_read':[1,2,3],
        'accessed_numeric_cells':len(accessed),'original_discovery_still_failed':True,
        'interpretation':'Other-replicate selection measures repeatability, not a deployable sequence predictor or formal noise ceiling. Diagnostic on already-open selected fragments only; cannot authorize confirmation.'}
    write_new(OUT/(NAME+'_decisions.csv'),d.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/(NAME+'.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k!='family_metrics'},indent=2),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='freeze':freeze()
    elif sys.argv[1]=='run':run()
    else:raise ValueError(sys.argv[1])
