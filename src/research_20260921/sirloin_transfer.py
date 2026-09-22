"""Frozen source-only transfer to independent SIRLOIN single-mutation decisions."""
from .common import ROOT,sha256,write_json,write_new
from .pilots import read_sixmers,regret
from datetime import datetime,timezone
import json
import sys
import numpy as np
import pandas as pd
import openpyxl

OUT=ROOT/'results/research_20260921'
DATA=ROOT/'data/external/research_20260921'
MODELS=('srle_kmer123','srle_pair','srle_measured','ccc','cctccc','composition')


def window_mean(sequence,lookup):
    if len(sequence)<6 or set(sequence)-set('ACGT'):
        raise ValueError('Invalid DNA sequence')
    return float(np.mean([lookup[sequence[i:i+6]] for i in range(len(sequence)-5)]))


def motif_count(sequence,motif):
    return sum(sequence[i:i+len(motif)]==motif for i in range(len(sequence)-len(motif)+1))


def predict():
    frame=pd.read_csv(OUT/'sirloin_single_mutation_sequences.csv')
    source=pd.read_csv(OUT/'robustness_predictions.csv').set_index('kmer')
    measured=read_sixmers().set_index('kmer').score.to_dict()
    lookups={'srle_kmer123':source.kmer123.to_dict(),'srle_pair':source.position_pair.to_dict(),
             'srle_measured':measured}
    for name,lookup in lookups.items():
        frame[name]=[window_mean(s,lookup) for s in frame.sequence]
    for name,motif in [('ccc','CCC'),('cctccc','CCTCCC')]:
        frame[name]=[motif_count(s,motif) for s in frame.sequence]
    frame['composition']=0.0
    write_new(OUT/'sirloin_transfer_predictions.csv',frame.to_csv(index=False,lineterminator='\n').encode())
    paths=[ROOT/'src/research_20260921/sirloin_transfer.py',
           ROOT/'reports/research_20260921/sirloin_transfer_spec.md',
           OUT/'sirloin_transfer_predictions.csv',DATA/'sirloin_dataset_ev1.xlsx',
           OUT/'robustness_predictions.csv']
    write_json(OUT/'sirloin_transfer_freeze.json',{
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
        'target_localization_outcomes_read':False,'predicted_sequences':len(frame)})
    print('Frozen external predictions for '+str(len(frame))+' single substitutions; no target outcome scoring.',flush=True)


def verify():
    frozen=json.loads((OUT/'sirloin_transfer_freeze.json').read_text())
    for p,h in frozen['files'].items():
        if sha256(ROOT/p)!=h: raise ValueError('Frozen input changed: '+p)


def load_discovery():
    # Only columns A:H, never confirmation columns I:J or the NucLibB sheet.
    w=openpyxl.load_workbook(DATA/'sirloin_dataset_ev1.xlsx',read_only=True,data_only=True)
    rows=list(w['NucLibC'].iter_rows(min_row=3,max_col=8,values_only=True))
    w.close()
    result={}
    for row in rows:
        vals=[]
        for value in row[6:8]:
            try: vals.append(float(value))
            except (ValueError,TypeError): vals.append(float('nan'))
        result[row[0]]=vals
    return result


def evaluate():
    verify()
    frame=pd.read_csv(OUT/'sirloin_transfer_predictions.csv')
    outcomes=load_discovery()
    rows,choices,exclusions=[],[],[]
    for (parent,mutation),group in frame.groupby(['parent','mutation']):
        wt=np.array(outcomes[parent])
        group=group[[np.isfinite(outcomes[row.id]).all() for row in group.itertuples()]].copy()
        if len(group)<5 or not np.isfinite(wt).all():
            exclusions.append({'parent':parent,'mutation':mutation,'finite_candidates':len(group)})
            continue
        ys=np.array([outcomes[i] for i in group.id])
        if np.any(np.ptp(ys,axis=0)==0):
            exclusions.append({'parent':parent,'mutation':mutation,'reason':'zero range'})
            continue
        for model in MODELS:
            selected={sign:int(np.lexsort((group.sequence.to_numpy(),-sign*group[model].to_numpy()))[0]) for sign in (1,-1)}
            for sign,index in selected.items():
                choices.append({'parent':parent,'mutation':mutation,'model':model,'direction':sign,
                                'selected_id':group.id.iloc[index],'candidate_ids':group.id.tolist()})
            for rep in (0,1):
                gain=np.mean([sign*(ys[index,rep]-wt[rep]) for sign,index in selected.items()])
                rows.append({'parent':parent,'mutation':mutation,'model':model,'replicate':rep+1,
                    'candidates':len(group),'regret':regret(ys[:,rep],group[model],group.sequence),
                    'oriented_change_from_wt':float(gain)})
    metrics=pd.DataFrame(rows)
    if metrics.empty: raise ValueError('No admitted decision sets')
    summaries={name:{'mean_regret':float(g.groupby(['parent','replicate']).regret.mean().groupby('parent').mean().mean()),
                     'oriented_change_from_wt':float(g.groupby(['parent','replicate']).oriented_change_from_wt.mean().groupby('parent').mean().mean())}
               for name,g in metrics.groupby('model')}
    pivot=metrics.groupby(['parent','replicate','model']).regret.mean().unstack('model')
    class_counts=metrics[metrics.model=='srle_kmer123'].groupby('parent').mutation.nunique().to_dict()
    adequate=set(class_counts)=={'Jpx_9','NICN1_53'} and min(class_counts.values())>=6
    comparisons={}
    passed=adequate
    for baseline in ('ccc','cctccc'):
        gain=pivot[baseline]-pivot['srle_kmer123']
        mean=float(gain.groupby('parent').mean().mean())
        comparisons[baseline]={'mean_regret_advantage':mean,
                              'parent_replicate_advantages':{f'{p}/rep{r}':float(v) for (p,r),v in gain.items()}}
        passed=passed and mean>=.05 and (gain>0).all()
    result={'scope':'Independent assay discovery pilot; only two parent sequence contexts',
        'decision_classes_by_parent':class_counts,'adequate':bool(adequate),'discovery_pass':bool(passed),
        'primary':'srle_kmer123','models':summaries,'primary_comparisons':comparisons,
        'excluded_classes':exclusions,'replicate_3_or_4_opened':False,'NucLibB_outcomes_opened':False}
    write_json(OUT/'sirloin_discovery_choices.json',choices)
    write_new(OUT/'sirloin_discovery_metrics.csv',metrics.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/'sirloin_discovery_result.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    {'predict':predict,'evaluate':evaluate}[sys.argv[1]]()
