"""Whitelisted held-out-GA-pattern intron configuration selection."""
from .common import ROOT,sha256,write_json,write_new
from .faraway_design import panel
from .seers_prefix_transfer import regret
import json,sys,subprocess,hashlib,itertools,zipfile,xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

OUT=ROOT/'results/research_20260921';DATA=ROOT/'data/external/research_20260921'
NAME='faraway_configuration';MODELS=['interaction','additive','quadratic','pattern']
ALPHAS=[.1,1,10,100,1000]
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def ordered(values,prefix):return sorted(values,key=lambda x:hashlib.sha256((prefix+x).encode()).hexdigest())


def read_values(path,allowed):
    allowed={int(x) for x in allowed}
    if not allowed or min(allowed)<2:raise PermissionError('Empty or invalid row whitelist')
    values={};accessed=[]
    with zipfile.ZipFile(path) as z, z.open('xl/worksheets/sheet2.xml') as stream:
        for _,row in ET.iterparse(stream,events=['end']):
            if row.tag!='{'+NS['m']+'}row':continue
            number=int(row.get('r'))
            if number in allowed:
                cells={}
                for c in row:
                    col=''.join(x for x in c.get('r','') if x.isalpha())
                    if col not in {'E','F','G'}:continue
                    v=c.find('m:v',NS)
                    if v is not None:
                        if c.get('t') not in (None,'n'):raise ValueError('Non-numeric admitted outcome')
                        cells[col]=float(v.text);accessed.append(f'{number}:{col}')
                if set(cells)!={'E','F','G'} or not all(np.isfinite(v) and v>0 for v in cells.values()):
                    raise ValueError('Missing/nonpositive/nonfinite publisher outcome')
                if not np.isclose(cells['G'],cells['F']/cells['E'],rtol=1e-8,atol=1e-10):
                    raise ValueError('Publisher ratio does not match CPMs')
                values[number]=np.log2(cells['F']/cells['E'])
            row.clear()
    if set(values)!=allowed:raise ValueError('Missing whitelisted rows')
    return values,accessed


def matrix(genotypes,model):
    bits=np.array([[int(b) for b in g] for g in genotypes],float);ga=bits[:,:8];introns=bits[:,8:]
    if model=='additive':return introns
    if model=='pattern':
        indices=np.array([int(g[8:],2) for g in genotypes]);return np.eye(256)[indices]
    pairs=np.column_stack([introns[:,i]*introns[:,j] for i,j in itertools.combinations(range(8),2)])
    x=np.column_stack([introns,pairs])
    if model=='quadratic':return x
    if model=='interaction':return np.column_stack([x,*[ga[:,i]*introns[:,j] for i in range(8) for j in range(8)]])
    raise ValueError(model)


def center(x,groups):
    x=np.asarray(x,float).copy()
    for key in np.unique(groups):
        ix=groups==key;x[ix]-=x[ix].mean(axis=0)
    return x


def fit(x,y,groups,ga,alpha):
    xx=center(x,groups);yy=center(y,groups)
    scaler=StandardScaler(with_mean=False).fit(xx)
    sizes=pd.Series(ga).value_counts();weights=np.array([1/sizes[g] for g in ga])
    weights*=len(weights)/weights.sum()
    model=Ridge(alpha=alpha,fit_intercept=False).fit(scaler.transform(xx),yy,sample_weight=weights)
    return scaler,model


def select_alpha(x,y,groups,ga):
    parents=ordered(set(ga),'faraway-inner-20260923|');mapping={p:i%5 for i,p in enumerate(parents)}
    fold=np.array([mapping[g] for g in ga]);scores={a:[] for a in ALPHAS}
    for k in range(5):
        train=fold!=k;test=~train
        truth=center(y[test],groups[test])
        for a in ALPHAS:
            scaler,model=fit(x[train],y[train],groups[train],ga[train],a)
            pred=center(model.predict(scaler.transform(x[test])),groups[test])
            errors=(truth-pred)**2
            scores[a].extend(float(errors[ga[test]==g].mean()) for g in set(ga[test]))
    means={a:float(np.mean(v)) for a,v in scores.items()}
    return min(ALPHAS,key=lambda a:(means[a],-a)),means


def freeze():
    paths=[ROOT/'src/research_20260921'/n for n in ['faraway_configuration.py','faraway_design.py','faraway_metadata.py','test_faraway_configuration.py','common.py','seers_prefix_transfer.py']]
    paths += [ROOT/'reports/research_20260921/faraway_configuration_spec.md',DATA/'faraway2025_supptable_2.xlsx',DATA/'faraway2025_supptable_3.xlsx',DATA/'faraway2025_first_transfection_code',OUT/'faraway2025_partition.csv',OUT/'faraway2025_design_audit.json']
    write_json(OUT/(NAME+'_freeze.json'),{'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},'target_numeric_outcomes_read':False})


def verify():
    p=OUT/(NAME+'_freeze.json')
    for name,h in json.loads(p.read_text())['files'].items():
        if sha256(ROOT/name)!=h:raise ValueError('Frozen file changed: '+name)
    if subprocess.check_output(['git','show','HEAD:'+p.relative_to(ROOT).as_posix()],cwd=ROOT)!=p.read_bytes():raise ValueError('Commit freeze first')


def load_frame():return pd.read_csv(OUT/'faraway2025_partition.csv',dtype={'genotype':str,'ga':str,'bc_number':str})


def prepare():
    verify();f=load_frame();train=f[f.partition=='train'].copy()
    values,accessed=read_values(DATA/'faraway2025_supptable_3.xlsx',train.excel_row)
    train['y']=[values[r] for r in train.excel_row]
    agg=train.groupby(['genotype','ga','panel','replicate']).y.mean().unstack('replicate')
    if list(agg.columns)!=[1,2,3] or agg.isna().any().any():raise ValueError('Incomplete training replicates')
    y=agg.mean(axis=1).to_numpy();t=agg.reset_index()[['genotype','ga','panel']]
    target=f[f.decision_candidate].drop_duplicates('genotype')[['genotype','ga','panel','partition']].copy()
    selections={}
    for name in MODELS:
        x=matrix(t.genotype,name);xt=matrix(target.genotype,name)
        alpha,scores=select_alpha(x,y,t.panel.to_numpy(),t.ga.to_numpy())
        scaler,model=fit(x,y,t.panel.to_numpy(),t.ga.to_numpy(),alpha)
        target[name]=model.predict(scaler.transform(xt));selections[name]={'alpha':alpha,'inner_GA_centered_MSE':scores}
        print('Prepared',name,'alpha',alpha,flush=True)
    write_new(OUT/(NAME+'_predictions.csv'),target.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/(NAME+'_training.json'),{'training_GA_patterns':t.ga.nunique(),'training_genotypes':len(t),'accessed_cells':len(accessed),
        'accessed_cells_sha256':hashlib.sha256('\n'.join(accessed).encode()).hexdigest(),'selection':selections,'development_or_confirmation_outcomes_read':False})
    write_json(OUT/(NAME+'_prediction_receipt.json'),{'prediction_sha256':sha256(OUT/(NAME+'_predictions.csv')),'training_sha256':sha256(OUT/(NAME+'_training.json'))})


def require_confirmation(result):
    if not result.get('passed',False):raise PermissionError('Development did not pass; confirmation stays closed')


def evaluate(stage):
    verify()
    if stage not in ['development','confirmation']:raise ValueError(stage)
    if stage=='confirmation':require_confirmation(json.loads((OUT/(NAME+'_development.json')).read_text()))
    receipt=OUT/(NAME+'_prediction_receipt.json')
    if subprocess.check_output(['git','show','HEAD:'+receipt.relative_to(ROOT).as_posix()],cwd=ROOT)!=receipt.read_bytes():raise ValueError('Commit predictions first')
    p=OUT/(NAME+'_predictions.csv');r=json.loads(receipt.read_text())
    if sha256(p)!=r['prediction_sha256']:raise ValueError('Predictions changed')
    pred=pd.read_csv(p,dtype={'genotype':str,'ga':str});pred=pred[pred.partition==stage]
    f=load_frame();f=f[(f.partition==stage)&f.decision_candidate].copy()
    values,accessed=read_values(DATA/'faraway2025_supptable_3.xlsx',f.excel_row);f['y']=[values[x] for x in f.excel_row]
    agg=f.groupby(['genotype','replicate']).y.mean().unstack('replicate')
    g=pred.merge(agg,left_on='genotype',right_index=True,validate='one_to_one')
    rows=[];excluded=[]
    for key,block in g.groupby('panel'):
        if len(block)<5 or block[[1,2,3]].isna().any().any() or (block[[1,2,3]].max()-block[[1,2,3]].min()).eq(0).any():
            excluded.append(key);continue
        for rep in [1,2,3]:
            row={'panel':key,'ga':block.ga.iloc[0],'replicate':rep,'candidates':len(block),'random':.5}
            for model in MODELS:row[model]=regret(block[rep],block[model])
            rows.append(row)
    d=pd.DataFrame(rows)
    if d.empty:raise ValueError('No eligible panels')
    means=d.groupby(['ga','replicate'])[MODELS+['random']].mean();parents=sorted(set(means.index.get_level_values('ga')))
    draws=np.random.default_rng(20260923).integers(0,len(parents),(5000,len(parents)))
    comparisons={};passed=len(parents)>=20
    for baseline in ['additive','quadratic','pattern','random']:
        gains=(means[baseline]-means.interaction).unstack('replicate').reindex(parents).to_numpy()
        mean=float(gains.mean());ci=np.quantile(gains.mean(axis=1)[draws].mean(axis=1),[.025,.975]);rep=gains.mean(axis=0)
        comparisons[baseline]={'mean_gain':mean,'descriptive_GA_ci95':ci.tolist(),'replicate_gains':rep.tolist()}
        passed=passed and mean>=.03 and ci[0]>0 and np.all(rep>0)
    result={'stage':stage,'scope':'Held-out synonymous GA-patterns in one reporter protein context; design-based RNA identity; processed outcomes.',
        'eligible_GA_patterns':len(parents),'eligible_panels':d.panel.nunique(),'mean_regret':means.mean().to_dict(),
        'comparisons':comparisons,'passed':bool(passed),'excluded_panels':excluded,'accessed_numeric_cells':len(accessed),
        'confirmation_opened':stage=='confirmation','other_assay_outcomes_read':False}
    write_new(OUT/(NAME+'_'+stage+'_metrics.csv'),d.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/(NAME+'_'+stage+'.json'),result);print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    command=sys.argv[1]
    if command in ['freeze','prepare']:globals()[command]()
    else:evaluate(command)
