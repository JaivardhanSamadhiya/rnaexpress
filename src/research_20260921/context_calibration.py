"""Frozen, retrospective low-budget context calibration; isolated new-data study."""
from .common import ROOT, sha256, write_json, write_new
import hashlib, itertools, json, re, subprocess, sys, zipfile
import xml.etree.ElementTree as ET
from collections import Counter
import numpy as np
import pandas as pd
import openpyxl
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

OUT = ROOT/'results/research_20260921'
DATA = ROOT/'data/external/research_20260921'
PREFIX = 'context_calibration'
CONTEXTS = ['Spliced', 'Unspliced', 'Circular', 'SCRCircular']
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
VOCAB = [''.join(p) for k in (1,2,3) for p in itertools.product('ACGT',repeat=k)]

def key(value):
    return hashlib.sha256(('context-budget-20260922|'+str(value)).encode()).hexdigest()

def features(sequences):
    output=[]
    for sequence in sequences:
        counts=Counter(sequence[j:j+k] for k in (1,2,3) for j in range(len(sequence)-k+1))
        output.append([counts[w]/(len(sequence)-len(w)+1) for w in VOCAB])
    return np.asarray(output,float)

def aliases():
    w=openpyxl.load_workbook(DATA/'context2022_data1.xlsx',read_only=True,data_only=True)
    mapping={}
    for row in w['Summary'].iter_rows(min_row=2,values_only=True):
        name=row[2]
        if isinstance(name,str) and name.startswith('circRNA:'):
            stem=name.split(':',1)[1]
            mapping['circ'+stem.replace('_','')]=re.sub(r'_\d+$','',stem).upper()
    w.close()
    mapping.update({'Ccnl2-v2':'CCNL2','Gcgr-v2':'GCGR','HotairM1':'HOTAIR',
                    **{s:'MALAT1' for s in ['MALAT1','mMalat1','zfMalat1','acMalat1','gaMalat1']}})
    return mapping

def prepare():
    f=pd.read_csv(OUT/'context2022_sequence_metadata.csv')
    f['excel_row']=np.arange(len(f))+2
    f=f[f.valid_sequence & f.gene.notna() & f.library.notna()].copy()
    mapping=aliases()
    unknown=[g for g in f.gene.unique() if g.startswith('circ') and g not in mapping]
    if unknown: raise ValueError(('Unmapped circular gene labels',unknown))
    f['family']=[mapping.get(g,g.upper()) for g in f.gene]
    excluded=f.overlap_old | f.overlap_sirloin | f.family.isin(['JPX','NICN1','PVT1'])
    excluded_count=int(excluded.sum())
    f=f[~excluded].reset_index(drop=True)
    parent={g:g for g in f.family.unique()}
    def root(g):
        while parent[g]!=g:
            parent[g]=parent[parent[g]]; g=parent[g]
        return g
    def merge(a,b):
        a,b=root(a),root(b)
        if a!=b: parent[max(a,b)]=min(a,b)
    # Conservative exact shared tract grouping, including low-complexity tracts.
    words={}
    for row in f.itertuples():
        for j in range(len(row.sequence)-39):
            word=row.sequence[j:j+40]
            if word in words: merge(row.family,words[word])
            else: words[word]=row.family
    sequences=f.sequence.tolist(); families=f.family.tolist()
    near_pairs=0
    # Exhaustive all-pairs 95% normalized global Levenshtein similarity.
    for start in range(0,len(f),256):
        scores=process.cdist(sequences[start:start+256],sequences,
                             scorer=Levenshtein.normalized_similarity,
                             score_cutoff=.95,dtype=np.float32,workers=2)
        for i,j in zip(*np.where(scores>=.95)):
            i+=start
            if j>i and families[i]!=families[j]:
                merge(families[i],families[j]); near_pairs+=1
    f['component']=[root(g) for g in families]
    components=sorted(f.component.unique(),key=key)
    ntest=max(1,len(components)//5)
    confirmation=set(components[:ntest]); development=set(components[ntest:2*ntest])
    remainder=components[2*ntest:]
    sizes=f.groupby('component').size()
    calibration=[c for c in remainder if sizes[c]>=20][:8]
    if len(calibration)!=8: raise ValueError('Too few calibration components')
    f['partition']=['confirmation' if c in confirmation else 'development' if c in development
                    else 'calibration' if c in calibration else 'source' for c in f.component]
    f['calibration_slot']=False
    for c in calibration:
        ix=sorted(f.index[f.component==c],key=lambda i:key(f.loc[i,'id']))[:8]
        f.loc[ix,'calibration_slot']=True
    write_new(OUT/(PREFIX+'_partition.csv'),f.to_csv(index=False,lineterminator='\n').encode())
    summary={'rows':len(f),'excluded_prior_or_parent_rows':excluded_count,
             'families':int(f.family.nunique()),'components':len(components),
             'cross_family_near_sequence_pairs':near_pairs,'calibration_slots':int(f.calibration_slot.sum()),
             'partition_rows':f.partition.value_counts().to_dict(),
             'partition_components':f.groupby('partition').component.nunique().to_dict(),
             'multi_family_components':{c:sorted(g.family.unique()) for c,g in f.groupby('component') if g.family.nunique()>1},
             'outcomes_read':False,'family_limit':'Explicit aliases and sequence links, not a complete paralog ontology.'}
    write_json(OUT/(PREFIX+'_inventory.json'),summary)
    print(json.dumps(summary,indent=2),flush=True)

def freeze():
    paths=[ROOT/'src/research_20260921/context_calibration.py',ROOT/'src/research_20260921/common.py',
           ROOT/'src/research_20260921/test_context_calibration.py',
           ROOT/'reports/research_20260921/context_calibration_spec.md',
           OUT/(PREFIX+'_partition.csv'),OUT/(PREFIX+'_inventory.json'),
           OUT/'context2022_sequence_metadata.csv',DATA/'context2022_data1.xlsx',DATA/'context2022_data3.xlsx']
    write_json(OUT/(PREFIX+'_freeze.json'),{'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
               'outcomes_read':False,'stage':'Pre-outcome fixed discovery and conditional confirmation'})

def verify():
    freeze_path=OUT/(PREFIX+'_freeze.json')
    for name,digest in json.loads(freeze_path.read_text())['files'].items():
        if sha256(ROOT/name)!=digest: raise ValueError(('Frozen input changed',name))
    # Require the exact freeze to be in HEAD before opening new outcomes.
    rel=freeze_path.relative_to(ROOT).as_posix()
    committed=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)
    if committed!=freeze_path.read_bytes(): raise ValueError('Freeze must be committed')

def read_outcomes(path,allowed_rows):
    """Parse numeric I:L cells only for explicitly admitted row numbers.

    XML for other cells is traversed, but their text is never converted, returned,
    logged or used. Numeric shared strings are deliberately rejected.
    """
    result={}; allowed=set(map(int,allowed_rows)); accessed=[]
    with zipfile.ZipFile(path) as z:
        # Verified workbook contains exactly this data sheet; relationship checked.
        workbook=ET.fromstring(z.read('xl/workbook.xml'))
        sheets=workbook.find(NS+'sheets')
        if len(sheets)!=1 or sheets[0].attrib['name']!='finalTab_230221':
            raise ValueError('Unexpected workbook sheets')
        with z.open('xl/worksheets/sheet1.xml') as stream:
            for event,element in ET.iterparse(stream,events=('end',)):
                if element.tag!=NS+'row': continue
                row=int(element.attrib['r'])
                if row in allowed:
                    values=[float('nan')]*4
                    for cell in element:
                        col=re.sub(r'\d','',cell.attrib.get('r',''))
                        if col not in ['I','J','K','L']: continue
                        v=cell.find(NS+'v'); t=cell.attrib.get('t','n')
                        if v is not None and t=='n':
                            values[['I','J','K','L'].index(col)]=float(v.text)
                            accessed.append(cell.attrib['r'])
                        elif t not in ['s','inlineStr','e','n']: raise ValueError('Unexpected outcome type')
                    result[row]=values
                element.clear()
    if set(result)!=allowed: raise ValueError('Missing admitted rows')
    return result,accessed

def fit_predict(x,y,train,predict,alpha=10):
    train=np.asarray(train)&np.isfinite(y)
    if train.sum()<10: raise ValueError('Insufficient training outcomes')
    scaler=StandardScaler().fit(x[train])
    model=Ridge(alpha=alpha).fit(scaler.transform(x[train]),y[train])
    return model.predict(scaler.transform(x[predict]))

def decision_regret(y,p,ids):
    if len(y)<10 or np.ptp(y)<=0: raise ValueError('Ineligible decision set')
    values=[]
    for sign in [1,-1]:
        chosen=np.lexsort((ids,-sign*p))[0]
        values.append((np.max(sign*y)-sign*y[chosen])/np.ptp(y))
    return float(np.mean(values))

def summarize(decisions):
    means=decisions.groupby(['component','context','model']).regret.mean().unstack('model')
    result={'regret':means.groupby('context').mean().to_dict(), 'comparisons':{}}
    components=sorted(means.index.get_level_values('component').unique())
    rng=np.random.default_rng(20260922)
    draws=rng.integers(0,len(components),(5000,len(components)))
    passes=[]
    for baseline in ['target_kmer','composition','random3']:
        gain=(means[baseline]-means['source_stack']).unstack('context').reindex(components)
        arr=gain.reindex(columns=CONTEXTS).to_numpy()
        point=float(np.nanmean(np.nanmean(arr,axis=0)))
        boot=np.nanmean(np.nanmean(arr[draws],axis=1),axis=1)
        ci=np.quantile(boot,[.025,.975]).tolist()
        by_context={c:float(v) for c,v in zip(CONTEXTS,np.nanmean(arr,axis=0))}
        counts={c:int(v) for c,v in zip(CONTEXTS,np.isfinite(arr).sum(0))}
        passed=(len(components)>=15 and min(counts.values())>=10 and point>=(.03 if baseline!='random3' else 0)
                and ci[0]>0 and sum(v>0 for v in by_context.values())>=3 and min(by_context.values())>=-.05)
        passes.append(passed)
        result['comparisons'][baseline]={'gain':point,'paired_component_ci95':ci,'by_context':by_context,
                                        'eligible_components':counts,'passes':bool(passed)}
    result['components']=len(components)
    result['discovery_pass']=all(passes)
    return result

def run(stage):
    verify()
    if stage=='confirmation':
        prior=json.loads((OUT/(PREFIX+'_development.json')).read_text())
        if not prior['discovery_pass']: raise PermissionError('Discovery gate failed: confirmation remains closed')
    f=pd.read_csv(OUT/(PREFIX+'_partition.csv'))
    source=(f.partition=='source').to_numpy()
    cal=f.calibration_slot.to_numpy(bool)
    test=(f.partition==stage).to_numpy()
    admitted=source|cal|test
    values,accessed=read_outcomes(DATA/'context2022_data3.xlsx',f.loc[admitted,'excel_row'])
    y=np.full((len(f),4),np.nan)
    for i,row in enumerate(f.excel_row):
        if row in values: y[i]=values[row]
    x=features(f.sequence)
    random=StandardScaler().fit(x[source]).transform(x) @ np.random.default_rng(20260922).normal(size=(84,3))/np.sqrt(84)
    predictions=[]; decisions=[]; calibration_counts={}
    for t,context in enumerate(CONTEXTS):
        validcal=cal&np.isfinite(y[:,t]); count=int(validcal.sum())
        nfamilies=int(f.loc[validcal,'component'].nunique())
        calibration_counts[context]={'observed_target_labels':count,'components':nfamilies}
        if count<32 or nfamilies<6: raise ValueError(('Calibration budget eligibility failed',context,count,nfamilies))
        source_predictions=np.column_stack([fit_predict(x,y[:,s],source,np.ones(len(f),bool),100) for s in range(4) if s!=t])
        preds={
            'source_stack':fit_predict(source_predictions,y[:,t],cal,test),
            'target_kmer':fit_predict(x,y[:,t],cal,test),
            'composition':fit_predict(x[:,:4],y[:,t],cal,test),
            'random3':fit_predict(random,y[:,t],cal,test)}
        evaluation=f[test].copy(); evaluation['truth']=y[test,t]
        for name,p in preds.items(): evaluation[name]=p
        for row in evaluation.itertuples():
            for name in preds:
                predictions.append({'id':row.id,'component':row.component,'context':context,
                                    'model':name,'prediction':float(getattr(row,name))})
        evaluation=evaluation[np.isfinite(evaluation.truth)]
        for (component,gene,library),g in evaluation.groupby(['component','gene','library']):
            if len(g)<10 or np.ptp(g.truth.to_numpy())<=0: continue
            for name in preds:
                decisions.append({'component':component,'gene':gene,'library':library,'context':context,
                                  'model':name,'candidates':len(g),
                                  'regret':decision_regret(g.truth.to_numpy(),g[name].to_numpy(),g.id.to_numpy())})
    d=pd.DataFrame(decisions)
    summary=summarize(d)
    summary.update({'stage':stage,'calibration':calibration_counts,'accessed_numeric_cells':len(accessed),
                    'accessed_cell_hash':hashlib.sha256('\n'.join(accessed).encode()).hexdigest(),
                    'confirmation_opened':stage=='confirmation','source_training_rows':int(source.sum()),
                    'scope':'Retrospective budget simulation, fragment selection, one MCF7 reporter study; not minimal-edit or independent-study validation.'})
    write_new(OUT/(PREFIX+'_'+stage+'_predictions.csv'),pd.DataFrame(predictions).to_csv(index=False,lineterminator='\n').encode())
    write_new(OUT/(PREFIX+'_'+stage+'_decisions.csv'),d.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/(PREFIX+'_'+stage+'.json'),summary)
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    command=sys.argv[1]
    if command=='prepare': prepare()
    elif command=='freeze': freeze()
    elif command in ['development','confirmation']: run(command)
    else: raise ValueError(command)
