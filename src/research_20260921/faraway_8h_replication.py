"""Secondary fixed-policy assessment on a separately scoped 8-hour experiment."""
from .faraway_configuration import (ROOT,OUT,DATA,MODELS,NS,load_frame,verify,read_values,matrix,fit,regret)
from .faraway_design import panel
from .common import sha256,write_json,write_new
import json,sys,subprocess,zipfile,xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

NAME='faraway_8h_replication'


def target_metadata():
    f=pd.read_csv(OUT/'faraway2025_construct_metadata.csv',dtype={'genotype':str,'bc_number':str})
    original=load_frame();closed=set(original[original.partition=='confirmation'].ga)
    f=f[(f.sheet=='transfection_2')&(f.time=='8 hr')].copy();f['ga']=f.genotype.str[:8]
    f=f[~f.ga.isin(closed)&f.n_introns.eq(4)].copy();f['panel']=f.genotype.map(panel)
    sizes=f.drop_duplicates('genotype').groupby('panel').size();panels=set(sizes[sizes>=5].index)
    f=f[f.panel.isin(panels)].copy()
    if f.ga.nunique()!=28 or f.panel.nunique()!=28:raise ValueError('8-hour metadata boundary changed')
    return f


def read_target(path,allowed):
    scope=set(map(int,target_metadata().excel_row));allowed=set(map(int,allowed))
    if not allowed or not allowed<=scope:raise PermissionError('Outside frozen 8-hour non-confirmation scope')
    values={}
    with zipfile.ZipFile(path) as z,z.open('xl/worksheets/sheet3.xml') as stream:
        for _,row in ET.iterparse(stream,events=['end']):
            if row.tag!='{'+NS['m']+'}row':continue
            number=int(row.get('r'))
            if number in allowed:
                cells={}
                for c in row:
                    col=''.join(x for x in c.get('r','') if x.isalpha())
                    if col not in {'F','G','H'}:continue
                    v=c.find('m:v',NS)
                    if v is not None:
                        if c.get('t') not in (None,'n'):raise ValueError('Invalid outcome type')
                        cells[col]=float(v.text)
                if set(cells)!={'F','G','H'} or not all(np.isfinite(v) and v>0 for v in cells.values()):raise ValueError('Invalid positive CPMs')
                if not np.isclose(cells['H'],cells['G']/cells['F'],rtol=1e-8,atol=1e-10):raise ValueError('CPM ratio mismatch')
                values[number]=np.log2(cells['G']/cells['F'])
            row.clear()
    if set(values)!=allowed:raise ValueError('Missing admitted rows')
    return values


def prepare():
    verify();f=load_frame();train=f[f.partition=='train'].copy()
    values,_=read_values(DATA/'faraway2025_supptable_3.xlsx',train.excel_row);train['y']=[values[r] for r in train.excel_row]
    agg=train.groupby(['genotype','ga','panel','replicate']).y.mean().unstack('replicate')
    y=agg.mean(axis=1).to_numpy();t=agg.reset_index()[['genotype','ga','panel']]
    target=target_metadata();p=target.drop_duplicates('genotype')[['genotype','ga','panel']].copy()
    settings=json.loads((OUT/'faraway_configuration_training.json').read_text())['selection']
    original=pd.read_csv(OUT/'faraway_configuration_predictions.csv',dtype={'genotype':str})
    for name in MODELS:
        x=matrix(t.genotype,name);scaler,model=fit(x,y,t.panel.to_numpy(),t.ga.to_numpy(),settings[name]['alpha'])
        check=model.predict(scaler.transform(matrix(original.genotype,name)))
        if not np.allclose(check,original[name],rtol=1e-10,atol=1e-10):raise ValueError('Original model did not reproduce')
        p[name]=model.predict(scaler.transform(matrix(p.genotype,name)))
    write_new(OUT/(NAME+'_predictions.csv'),p.to_csv(index=False,lineterminator='\n').encode())
    write_new(OUT/(NAME+'_target_rows.csv'),target.to_csv(index=False,lineterminator='\n').encode())
    paths=[ROOT/'src/research_20260921/faraway_8h_replication.py',ROOT/'src/research_20260921/faraway_configuration.py',
        ROOT/'reports/research_20260921/faraway_8h_replication_spec.md',OUT/(NAME+'_predictions.csv'),OUT/(NAME+'_target_rows.csv'),
        OUT/'faraway_configuration_training.json',OUT/'faraway2025_partition.csv',OUT/'faraway2025_construct_metadata.csv',DATA/'faraway2025_supptable_3.xlsx']
    write_json(OUT/(NAME+'_freeze.json'),{'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},'new_8h_outcomes_read':False,'original_models_reproduced':True})
    print('Fixed 8-hour predictions prepared; all original models reproduced; no new target outcomes.',flush=True)


def evaluate():
    verify();p=OUT/(NAME+'_freeze.json')
    for name,h in json.loads(p.read_text())['files'].items():
        if sha256(ROOT/name)!=h:raise ValueError('Frozen file changed '+name)
    if subprocess.check_output(['git','show','HEAD:'+p.relative_to(ROOT).as_posix()],cwd=ROOT)!=p.read_bytes():raise ValueError('Commit first')
    f=target_metadata();values=read_target(DATA/'faraway2025_supptable_3.xlsx',f.excel_row);f['y']=[values[x] for x in f.excel_row]
    agg=f.groupby(['genotype','replicate']).y.mean().unstack('replicate')
    p=pd.read_csv(OUT/(NAME+'_predictions.csv'),dtype={'genotype':str,'ga':str}).merge(agg,left_on='genotype',right_index=True,validate='one_to_one')
    rows=[]
    for key,g in p.groupby('panel'):
        if len(g)<5 or g[[1,2,3]].isna().any().any() or (g[[1,2,3]].max()-g[[1,2,3]].min()).eq(0).any():raise ValueError('Unexpected ineligible panel')
        for rep in [1,2,3]:
            row={'panel':key,'ga':g.ga.iloc[0],'replicate':rep,'candidates':len(g)}
            for name in MODELS:row[name]=regret(g[rep],g[name])
            rows.append(row)
    d=pd.DataFrame(rows);m=d.groupby(['ga','replicate'])[MODELS].mean();parents=sorted(set(m.index.get_level_values('ga')))
    draws=np.random.default_rng(20260923).integers(0,len(parents),(5000,len(parents)))
    comparisons={};supported=len(parents)>=20
    for name in MODELS:
        a=(.5-m[name]).unstack('replicate').reindex(parents).to_numpy();ci=np.quantile(a.mean(axis=1)[draws].mean(axis=1),[.025,.975]);mean=float(a.mean());reps=a.mean(axis=0)
        comparisons[name]={'gain_over_random':mean,'descriptive_GA_ci95':ci.tolist(),'replicate_gains':reps.tolist()}
        if name in ['quadratic','pattern']:supported=supported and mean>=.05 and ci[0]>0 and np.all(reps>0)
    result={'scope':'Secondary hypothesis selected after development; fixed models on separate 8-hour collection; one protein context, possibly overlapping genotypes.',
        'eligible_GA_patterns':len(parents),'eligible_genotypes':len(p),'mean_regret':m.mean().to_dict(),'comparisons':comparisons,
        'secondary_hypothesis_supported':bool(supported),'original_interaction_gate_still_failed':True,
        'original_confirmation_GA_outcomes_read':False,'other_condition_or_assay_outcomes_read':False,'numeric_cells_read':3*len(values)}
    write_new(OUT/(NAME+'_metrics.csv'),d.to_csv(index=False,lineterminator='\n').encode());write_json(OUT/(NAME+'_result.json'),result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':{'prepare':prepare,'evaluate':evaluate}[sys.argv[1]]()
