"""Exploratory baseline-strength audit; all choices nested inside calibration."""
from .context_learning_curve import ROOT,OUT,DATA,CONTEXTS,features,key,read_outcomes,fit_predict,decision_regret
from .common import sha256,write_json,write_new
import json,sys,subprocess
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

NAME='context_regularization_audit'
ALPHAS=[.1,1,10,100,1000,10000]

def choose_alpha(x,y,cal,components):
    finite=cal&np.isfinite(y);groups=sorted(set(components[finite]));losses={a:[] for a in ALPHAS}
    for c in groups:
        train=finite&(components!=c);test=finite&(components==c)
        if train.sum()<10:raise ValueError('Insufficient inner calibration labels')
        scaler=StandardScaler().fit(x[train]);a=scaler.transform(x[train]);b=scaler.transform(x[test])
        for alpha in ALPHAS:
            pred=Ridge(alpha=alpha).fit(a,y[train]).predict(b)
            losses[alpha].append(float(np.mean((y[test]-pred)**2)))
    averages={a:float(np.mean(v)) for a,v in losses.items()}
    winner=min(ALPHAS,key=lambda a:(averages[a],-a))
    return winner,averages

def freeze():
    paths=[ROOT/'src/research_20260921/context_regularization_audit.py',
           ROOT/'src/research_20260921/context_learning_curve.py',ROOT/'src/research_20260921/context_calibration.py',
           ROOT/'src/research_20260921/common.py',ROOT/'reports/research_20260921/context_regularization_audit_spec.md',
           OUT/'context_calibration_partition.csv',DATA/'context2022_data3.xlsx']
    write_json(OUT/(NAME+'_freeze.json'),{'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
               'scope':'Exploratory reused-source audit motivated by completed learning curve; no confirmation eligibility'})

def run():
    path=OUT/(NAME+'_freeze.json')
    for n,h in json.loads(path.read_text())['files'].items():
        if sha256(ROOT/n)!=h:raise ValueError(n)
    if subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)!=path.read_bytes():raise ValueError('Commit first')
    f=pd.read_csv(OUT/'context_calibration_partition.csv');f=f[f.partition=='source'].reset_index(drop=True)
    if len(f)!=3235 or f.component.nunique()!=61:raise ValueError('Unexpected source set')
    values,_=read_outcomes(DATA/'context2022_data3.xlsx',f.excel_row)
    y=np.array([values[r] for r in f.excel_row]);x=features(f.sequence)
    groups=f.component.to_numpy();components=sorted(f.component.unique(),key=lambda c:key('curve-fold|'+c))
    folds={c:i%5 for i,c in enumerate(components)};sizes=f.groupby('component').size()
    records=[];selections=[]
    for fold in range(5):
        test=f.component.map(folds).eq(fold).to_numpy()
        for repeat in range(3):
            eligible=sorted([c for c in components if folds[c]!=fold and sizes[c]>=32],key=lambda c:key(f'curve-cal-{repeat}|'+c))[:8]
            source=~test&~f.component.isin(eligible).to_numpy();cal=np.zeros(len(f),bool)
            for c in eligible:
                ix=sorted(f.index[f.component==c],key=lambda i:key(f'curve-slot-{repeat}|'+f.loc[i,'id']))[:8];cal[ix]=True
            sp=np.column_stack([fit_predict(x,y[:,s],source,np.ones(len(f),bool),100) for s in range(4)])
            for t,context in enumerate(CONTEXTS):
                valid=cal&np.isfinite(y[:,t])
                if valid.sum()<32 or f.loc[valid,'component'].nunique()<6:continue
                sx=sp[:,[s for s in range(4) if s!=t]]
                matrices={'tuned_kmer':x,'tuned_stack':sx,'tuned_composition':x[:,:4]}
                preds={'fixed_stack':fit_predict(sx,y[:,t],cal,test),
                       'fixed_kmer':fit_predict(x,y[:,t],cal,test),
                       'sibling':sp[test,{0:1,1:0,2:3,3:2}[t]]}
                for name,matrix in matrices.items():
                    alpha,losses=choose_alpha(matrix,y[:,t],cal,groups)
                    selections.append({'fold':fold,'repeat':repeat,'context':context,'model':name,
                                       'alpha':alpha,'inner_group_mse':losses[alpha],'labels':int(valid.sum())})
                    preds[name]=fit_predict(matrix,y[:,t],cal,test,alpha)
                g=f[test].copy();g['truth']=y[test,t]
                for name,p in preds.items():g[name]=p
                g=g[np.isfinite(g.truth)]
                for (component,gene,library),block in g.groupby(['component','gene','library']):
                    if len(block)<10 or np.ptp(block.truth.to_numpy())<=0:continue
                    for name in preds:
                        records.append({'component':component,'gene':gene,'library':library,'context':context,
                                        'repeat':repeat,'fold':fold,'model':name,'candidates':len(block),
                                        'regret':decision_regret(block.truth.to_numpy(),block[name].to_numpy(),block.id.to_numpy())})
            print(f'Nested regularization fold {fold+1}/5 panel {repeat+1}/3 complete',flush=True)
    d=pd.DataFrame(records);means=d.groupby(['component','context','model']).regret.mean().unstack('model')
    units=sorted(means.index.get_level_values('component').unique())
    draws=np.random.default_rng(20260922).integers(0,len(units),(5000,len(units)))
    comparisons={}
    for a,b in [('fixed_stack','tuned_kmer'),('tuned_stack','tuned_kmer'),('tuned_stack','tuned_composition'),('tuned_stack','sibling'),('tuned_kmer','fixed_kmer')]:
        values=(means[b]-means[a]).unstack('context').reindex(index=units,columns=CONTEXTS).to_numpy()
        boot=np.nanmean(np.nanmean(values[draws],axis=1),axis=1)
        comparisons[a+'_vs_'+b]={'gain':float(np.nanmean(np.nanmean(values,axis=0))),
                                 'descriptive_ci95':np.quantile(boot,[.025,.975]).tolist(),
                                 'by_context':dict(zip(CONTEXTS,map(float,np.nanmean(values,axis=0))))}
    selection=pd.DataFrame(selections)
    result={'scope':'Exploratory source-only nested regularization audit; reused data; intervals exclude full training-sample uncertainty.',
            'components':len(units),'comparisons':comparisons,'regret':means.groupby('context').mean().to_dict(),
            'selected_alpha_counts':{m:{str(k):int(v) for k,v in g.alpha.value_counts().items()} for m,g in selection.groupby('model')}}
    write_new(OUT/(NAME+'_decisions.csv'),d.to_csv(index=False,lineterminator='\n').encode())
    write_new(OUT/(NAME+'_selections.csv'),selection.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/(NAME+'.json'),result);print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
