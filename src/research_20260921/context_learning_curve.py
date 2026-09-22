"""Exploratory learning curves restricted to already-open source groups."""
from .context_calibration import (ROOT, OUT, DATA, CONTEXTS, features, key,
                                 read_outcomes, fit_predict, decision_regret)
from .common import sha256, write_new, write_json
import json,sys,subprocess
import numpy as np
import pandas as pd

NAME='context_learning_curve'

def freeze():
    paths=[ROOT/'src/research_20260921/context_learning_curve.py',
           ROOT/'src/research_20260921/context_calibration.py',ROOT/'src/research_20260921/common.py',
           ROOT/'reports/research_20260921/context_learning_curve_spec.md',
           OUT/'context_calibration_partition.csv',DATA/'context2022_data3.xlsx']
    write_json(OUT/(NAME+'_freeze.json'),{'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
               'status':'Exploratory source-only diagnostic specified after original development result'})

def run():
    fp=OUT/(NAME+'_freeze.json')
    for name,digest in json.loads(fp.read_text())['files'].items():
        if sha256(ROOT/name)!=digest: raise ValueError(name)
    if subprocess.check_output(['git','show','HEAD:'+fp.relative_to(ROOT).as_posix()],cwd=ROOT)!=fp.read_bytes():
        raise ValueError('Commit diagnostic specification first')
    f=pd.read_csv(OUT/'context_calibration_partition.csv')
    f=f[f.partition=='source'].reset_index(drop=True)
    assert len(f)==3235 and f.component.nunique()==61
    values,accessed=read_outcomes(DATA/'context2022_data3.xlsx',f.excel_row)
    y=np.asarray([values[row] for row in f.excel_row]); x=features(f.sequence)
    components=sorted(f.component.unique(),key=lambda c:key('curve-fold|'+c))
    folds={c:i%5 for i,c in enumerate(components)}
    sizes=f.groupby('component').size()
    records=[]; budgets=[]
    for fold in range(5):
        test=f.component.map(folds).eq(fold).to_numpy()
        for repeat in range(3):
            eligible=sorted([c for c in components if folds[c]!=fold and sizes[c]>=32],
                            key=lambda c:key(f'curve-cal-{repeat}|'+c))[:8]
            if len(eligible)!=8: raise ValueError('Insufficient source-only calibration groups')
            source=~test&~f.component.isin(eligible).to_numpy()
            allrows=np.ones(len(f),bool)
            source_predictions=np.column_stack([fit_predict(x,y[:,s],source,allrows,100) for s in range(4)])
            for budget in [16,64,256]:
                cal=np.zeros(len(f),bool)
                for c in eligible:
                    ix=sorted(f.index[f.component==c],key=lambda i:key(f'curve-slot-{repeat}|'+f.loc[i,'id']))[:budget//8]
                    cal[ix]=True
                for t,context in enumerate(CONTEXTS):
                    valid=cal&np.isfinite(y[:,t])
                    count=int(valid.sum()); units=int(f.loc[valid,'component'].nunique())
                    budgets.append({'fold':fold,'repeat':repeat,'context':context,'budget':budget,'finite':count,'components':units})
                    if count<max(10,budget//2) or units<6: continue
                    other=[s for s in range(4) if s!=t]
                    # Sibling context was established by the 2022 source paper.
                    sibling={0:1,1:0,2:3,3:2}[t]
                    preds={
                        'stack':fit_predict(source_predictions[:,other],y[:,t],cal,test),
                        'target_kmer':fit_predict(x,y[:,t],cal,test),
                        'composition':fit_predict(x[:,:4],y[:,t],cal,test),
                        'sibling_uncalibrated':source_predictions[test,sibling],
                        'sibling_calibrated':fit_predict(source_predictions[:,[sibling]],y[:,t],cal,test)}
                    g=f[test].copy();g['truth']=y[test,t]
                    for name,pred in preds.items():g[name]=pred
                    g=g[np.isfinite(g.truth)]
                    for (component,gene,library),group in g.groupby(['component','gene','library']):
                        if len(group)<10 or np.ptp(group.truth.to_numpy())<=0: continue
                        for name in preds:
                            records.append({'fold':fold,'repeat':repeat,'budget':budget,'context':context,
                                            'component':component,'gene':gene,'library':library,'model':name,
                                            'candidates':len(group),'regret':decision_regret(group.truth.to_numpy(),group[name].to_numpy(),group.id.to_numpy())})
            print(f'Completed fold {fold+1}/5, calibration panel {repeat+1}/3',flush=True)
    d=pd.DataFrame(records); summary={}
    for budget,gb in d.groupby('budget'):
        # Collapse repeated calibration panels and original gene decisions before bootstrapping.
        means=gb.groupby(['component','context','model']).regret.mean().unstack('model')
        units=sorted(means.index.get_level_values('component').unique())
        draw=np.random.default_rng(20260922).integers(0,len(units),(5000,len(units)))
        comparisons={}
        for baseline in ['target_kmer','composition','sibling_uncalibrated','sibling_calibrated']:
            a=(means[baseline]-means['stack']).unstack('context').reindex(index=units,columns=CONTEXTS).to_numpy()
            boot=np.nanmean(np.nanmean(a[draw],axis=1),axis=1)
            comparisons[baseline]={'gain':float(np.nanmean(np.nanmean(a,axis=0))),
                 'descriptive_component_ci95':np.quantile(boot,[.025,.975]).tolist(),
                 'by_context':dict(zip(CONTEXTS,map(float,np.nanmean(a,axis=0))))}
        summary[str(budget)]={'components':len(units),'comparisons':comparisons,
                             'regret':means.groupby('context').mean().to_dict()}
    write_new(OUT/(NAME+'_decisions.csv'),d.to_csv(index=False,lineterminator='\n').encode())
    write_new(OUT/(NAME+'_budgets.csv'),pd.DataFrame(budgets).to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/(NAME+'.json'),{'scope':'Exploratory reused-source diagnostic, no promotion or confirmation claim; intervals omit training-sample uncertainty.',
                                 'source_only':True,'rows':len(f),'numeric_cells':len(accessed),'budgets':summary})
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__': {'freeze':freeze,'run':run}[sys.argv[1]]()
