"""Exact identical-menu descriptive bound. No fitted predictor or protected labels."""
from pathlib import Path
from collections import Counter
import hashlib, json, sys
import numpy as np
import pandas as pd

ROOT=Path('D:/rnaexpress')
NS='context_conflict_audit_20261007'
OUT=ROOT/'results'/NS
CORE=ROOT/'results/probabilistic_ranking_20260928/candidate_index.csv'
CORE_SHA='773d6145bbe4b17ff50597e47eba13f0b2977a3ddf541a1b238adcb7ff433e3d'
TOL=1e-12
META=['intervention_id','dataset','cell_type','reporter','parent_context_id','parent_sequence','mutant_sequence','biological_component']
TASKS={'mikl_gse173098':('cell_type',['CAD','Neuro-2a']), 'moffatt_gse334718':('reporter',['GFP','Firefly'])}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def stable_hash(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def save(path,payload):
    path=Path(path).resolve()
    assert path.is_relative_to(OUT.resolve())
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): assert path.read_bytes()==payload, 'Preserve '+str(path)
    else: path.write_bytes(payload)


def jsave(path,value):
    save(path,(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())


def metadata():
    assert sha(CORE)==CORE_SHA
    frame=pd.read_csv(CORE,usecols=META,low_memory=False)
    assert len(frame)==26258 and frame.intervention_id.is_unique
    frame['row0']=np.arange(len(frame))
    assert set(frame.dataset)=={'astrocyte_gse330741','mikl_gse173098','moffatt_gse334718','srle'}
    return frame


def match_menus(frame):
    matched,excluded,coverage=[],[],{}
    for dataset,(axis,levels) in TASKS.items():
        subset=frame[frame.dataset.eq(dataset)]
        assert set(subset[axis])==set(levels)
        grouped={}
        for context,g in subset.groupby('parent_context_id',sort=True):
            assert g.parent_sequence.nunique()==g.biological_component.nunique()==g[axis].nunique()==1
            seqs=tuple(sorted(g.mutant_sequence))
            record={'dataset':dataset,'axis':axis,'level':g[axis].iloc[0],'context':context,
                    'component':g.biological_component.iloc[0],'parent':g.parent_sequence.iloc[0],
                    'sequences':seqs,'row_by_sequence':dict(zip(g.mutant_sequence,g.row0)), 'rows':len(g)}
            if len(seqs)!=len(set(seqs)) or len(seqs)<2:
                excluded.append({'dataset':dataset,'context':context,'rows':len(g),'reason':'duplicate_sequence_or_small_menu'})
                continue
            grouped.setdefault((record['parent'],seqs),[]).append(record)
        for key,records in sorted(grouped.items()):
            if len(records)!=2 or Counter(r['level'] for r in records)!=Counter(levels):
                reason='nonmatching_menu' if len(records)==1 else 'ambiguous_same_signature'
                excluded.extend({'dataset':dataset,'context':r['context'],'rows':r['rows'],'reason':reason} for r in records)
                continue
            ordered=[next(r for r in records if r['level']==level) for level in levels]
            if len({r['component'] for r in ordered})!=1:
                excluded.extend({'dataset':dataset,'context':r['context'],'rows':r['rows'],'reason':'different_component'} for r in ordered)
                continue
            matched.append({'dataset':dataset,'menu_id':stable_hash([dataset,key[0],key[1]]),
                            'parent':key[0],'sequences':key[1],'component':ordered[0]['component'],'records':ordered})
        local=[m for m in matched if m['dataset']==dataset]
        coverage[dataset]={'core_rows':len(subset),'core_contexts':int(subset.parent_context_id.nunique()),
                           'core_components':int(subset.biological_component.nunique()),'exact_shared_menus':len(local),
                           'matched_rows':sum(2*len(m['sequences']) for m in local),
                           'matched_contexts':2*len(local),'matched_components':len({m['component'] for m in local}),
                           'excluded_contexts':sum(e['dataset']==dataset for e in excluded),
                           'excluded_rows':sum(e['rows'] for e in excluded if e['dataset']==dataset)}
        assert coverage[dataset]['matched_rows']+coverage[dataset]['excluded_rows']==len(subset)
    return matched,excluded,coverage


def selected_labels(frame,menus):
    selected=sorted({row for m in menus for r in m['records'] for row in r['row_by_sequence'].values()})
    if not selected: return {}
    with CORE.open('rb') as f: assert sum(line.count(b'\n') for line in f)==len(frame)+1, 'Multiline source requires scoped reader'
    wanted={i+1 for i in selected}
    labels=pd.read_csv(CORE,usecols=['intervention_id','measured_delta'],skiprows=lambda i:i!=0 and i not in wanted,float_precision='round_trip')
    assert len(labels)==len(selected)
    labels.index=selected
    assert labels.intervention_id.tolist()==frame.loc[selected,'intervention_id'].tolist()
    return labels.measured_delta.to_dict()


def optimal(y):
    """O(n^2) vector loss minimization; lexical order is input order."""
    y=np.asarray(y,dtype=np.float64)
    assert y.ndim==2 and y.shape[0]==2 and y.shape[1]>=2 and np.isfinite(y).all()
    spans=np.ptp(y,axis=1)
    assert (spans>0).all()
    up=(y.max(axis=1)[:,None]-y)/spans[:,None]
    down=(y-y.min(axis=1)[:,None])/spans[:,None]
    costs=(up.mean(axis=0)[:,None]+down.mean(axis=0)[None,:])/2
    np.fill_diagonal(costs,np.inf)
    index=int(np.argmin(costs)); j,k=np.unravel_index(index,costs.shape)
    loss=float(costs[j,k])
    assert -TOL<=loss<=.5+TOL
    # The all-constant shared score can select any lexical ID, but every context's
    # mean of its two directional regrets is exactly0.5 up to arithmetic error.
    constant=float((up[:,0]+down[:,0]).mean()/2)
    assert abs(constant-.5)<=TOL
    maximum_sets=[set(np.flatnonzero(row==row.max())) for row in y]
    minimum_sets=[set(np.flatnonzero(row==row.min())) for row in y]
    common_max=maximum_sets[0]&maximum_sets[1]; common_min=minimum_sets[0]&minimum_sets[1]
    exact_zero=any(a!=b for a in common_max for b in common_min)
    return {'j':int(j),'k':int(k),'minimum_pooled_regret':loss,'constant_score_regret':constant,
            'r0_up':float(up[0,j]),'r0_down':float(down[0,k]),'r1_up':float(up[1,j]),'r1_down':float(down[1,k]),
            'span0':float(spans[0]),'span1':float(spans[1]),'common_exact_max_count':len(common_max),
            'common_exact_min_count':len(common_min),'exact_zero_feasible':exact_zero,'numerical_conflict':loss>TOL}


def compute(frame,menus,labels):
    rows,invalid=[],[]
    for m in menus:
        y=np.asarray([[labels[r['row_by_sequence'][s]] for s in m['sequences']] for r in m['records']],dtype=float)
        if not np.isfinite(y).all() or (np.ptp(y,axis=1)<=0).any():
            invalid.append({'dataset':m['dataset'],'menu_id':m['menu_id'],'reason':'nonfinite_or_uninformative_span'})
            continue
        detail=optimal(y);j,k=detail.pop('j'),detail.pop('k')
        rows.append({'dataset':m['dataset'],'menu_id':m['menu_id'],'biological_component':m['component'],
                     'parent_sha256':stable_hash(m['parent']),'candidate_menu_sha256':stable_hash(m['sequences']),
                     'candidates':len(m['sequences']),'context0':m['records'][0]['context'],'context1':m['records'][1]['context'],
                     'level0':m['records'][0]['level'],'level1':m['records'][1]['level'],
                     'increase_sequence':m['sequences'][j],'decrease_sequence':m['sequences'][k],**detail})
    return pd.DataFrame(rows),invalid


def summarize(table,coverage,menus,invalid):
    result={'scope':'exposed identical menus only; relaxed menu-wise empirical lower bound, not noise/Bayes/causal ceiling',
            'tolerance':TOL,'weights':'directions and contexts equal per menu; menus equal within component; components equal within study',
            'coverage':coverage,'invalid_matched_menus':invalid,'studies':{},'cross_menu_allele_repetition':{}}
    for dataset in TASKS:
        g=table[table.dataset.eq(dataset)] if len(table) else pd.DataFrame()
        local=[m for m in menus if m['dataset']==dataset]
        allele_counts=Counter(seq for m in local for seq in m['sequences'])
        pair_counts=Counter((m['parent'],seq) for m in local for seq in m['sequences'])
        result['cross_menu_allele_repetition'][dataset]={'candidate_occurrences':sum(allele_counts.values()),
                    'unique_mutant_sequences':len(allele_counts),'mutant_sequences_in_multiple_menus':sum(n>1 for n in allele_counts.values()),
                    'unique_parent_mutant_pairs':len(pair_counts),'parent_mutant_pairs_in_multiple_menus':sum(n>1 for n in pair_counts.values())}
        if not len(g):
            result['studies'][dataset]={'status':'NO EXACT IDENTICAL MENUS: no outcome arithmetic','menus':0}
            continue
        component=g.groupby('biological_component')[['minimum_pooled_regret','constant_score_regret','exact_zero_feasible','numerical_conflict']].mean()
        result['studies'][dataset]={'status':'DESCRIPTIVE ONLY','menus':len(g),'components':len(component),
                'component_weighted_minimum_pooled_regret':float(component.minimum_pooled_regret.mean()),
                'component_weighted_constant_score_regret':float(component.constant_score_regret.mean()),
                'exact_zero_feasible_menus':int(g.exact_zero_feasible.sum()),'numerical_conflict_menus':int(g.numerical_conflict.sum()),
                'component_weighted_numerical_conflict_fraction':float(component.numerical_conflict.mean()),
                'components_with_any_numerical_conflict':int(g.groupby('biological_component').numerical_conflict.any().sum()),
                'max_menu_minimum_regret':float(g.minimum_pooled_regret.max()),
                'per_context_regret_at_selected_shared_pair':{g.level0.iloc[0]:float(g.assign(r=(g.r0_up+g.r0_down)/2).groupby('biological_component').r.mean().mean()),
                                                           g.level1.iloc[0]:float(g.assign(r=(g.r1_up+g.r1_down)/2).groupby('biological_component').r.mean().mean())}}
    return result


def freeze():
    sources=[CORE,ROOT/'reports'/NS/'protocol.md',ROOT/'src'/NS/'audit.py',ROOT/'src'/NS/'test_audit.py']
    jsave(OUT/'plan_manifest.json',{'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},'outcome_arithmetic_before_this_manifest':False})


def check_plan():
    manifest=json.loads((OUT/'plan_manifest.json').read_text(encoding='utf8'))
    for name,digest in manifest['source_sha256'].items(): assert sha(ROOT/name)==digest,name


def run():
    check_plan();frame=metadata();menus,excluded,coverage=match_menus(frame);labels=selected_labels(frame,menus)
    table,invalid=compute(frame,menus,labels);summary=summarize(table,coverage,menus,invalid)
    save(OUT/'menus.csv',table.to_csv(index=False,lineterminator='\n').encode())
    save(OUT/'excluded_contexts.csv',pd.DataFrame(excluded).to_csv(index=False,lineterminator='\n').encode())
    jsave(OUT/'summary.json',summary)
    print(json.dumps(summary['studies'],indent=2))


def verify():
    check_plan();frame=metadata();menus,excluded,coverage=match_menus(frame);labels=selected_labels(frame,menus)
    saved=pd.read_csv(OUT/'menus.csv',float_precision='round_trip')
    good=0; maximum_error=0.; rebuilt=[]
    for m in menus:
        data=[[float(labels[r['row_by_sequence'][s]]) for s in m['sequences']] for r in m['records']]
        if any(not np.isfinite(row).all() or max(row)<=min(row) for row in data): continue
        costs=[]
        for j in range(len(m['sequences'])):
            for k in range(len(m['sequences'])):
                if j==k: continue
                terms=[]
                for values in data:
                    spread=max(values)-min(values)
                    terms.extend([(max(values)-values[j])/spread,(values[k]-min(values))/spread])
                costs.append((sum(terms)/4,j,k,terms))
        best=min(costs,key=lambda item:(item[0],item[1],item[2]))
        row=saved[saved.menu_id.eq(m['menu_id'])];assert len(row)==1
        row=row.iloc[0];assert row.biological_component==m['component']
        assert row.context0==m['records'][0]['context'] and row.context1==m['records'][1]['context']
        assert row.parent_sha256==stable_hash(m['parent']) and row.candidate_menu_sha256==stable_hash(m['sequences'])
        j=m['sequences'].index(row.increase_sequence);k=m['sequences'].index(row.decrease_sequence);assert j!=k
        chosen=next(item for item in costs if item[1:3]==(j,k))
        # Vector and scalar summation can differ at machine epsilon; selections
        # among numerically equal minima are acceptable, never change the metric.
        assert chosen[0]-best[0]<=TOL
        actual=[float(row.minimum_pooled_regret),float(row.r0_up),float(row.r0_down),float(row.r1_up),float(row.r1_down)]
        expected=[chosen[0],*chosen[3]]
        error=max(abs(a-b) for a,b in zip(actual,expected));maximum_error=max(maximum_error,error);assert error<=TOL
        assert abs(float(row.constant_score_regret)-.5)<=TOL
        amax=set(i for i,v in enumerate(data[0]) if v==max(data[0]));bmax=set(i for i,v in enumerate(data[1]) if v==max(data[1]))
        amin=set(i for i,v in enumerate(data[0]) if v==min(data[0]));bmin=set(i for i,v in enumerate(data[1]) if v==min(data[1]))
        zero=any(a!=b for a in amax&bmax for b in amin&bmin)
        assert bool(row.exact_zero_feasible)==zero and bool(row.numerical_conflict)==(chosen[0]>TOL)
        rebuilt.append(row.to_dict());good+=1
    assert good==len(saved) and saved.menu_id.is_unique
    expected=summarize(pd.DataFrame(rebuilt),coverage,menus,[])
    original=json.loads((OUT/'summary.json').read_text(encoding='utf8'))
    def check(a,b):
        if isinstance(a,dict): assert set(a)==set(b);[check(a[k],b[k]) for k in a]
        elif isinstance(a,list): assert len(a)==len(b);[check(x,y) for x,y in zip(a,b)]
        elif isinstance(a,float): assert abs(a-float(b))<=TOL
        else: assert a==b,(a,b)
    check(original,expected)
    receipt={'status':'PASS independent scalar brute-force replay','menus':good,'maximum_arithmetic_error':maximum_error,
             'source_sha256':sha(CORE),'saved_menu_sha256':sha(OUT/'menus.csv'),'summary_sha256':sha(OUT/'summary.json'),
             'model_fits':False,'protected_outcomes_read':False}
    jsave(OUT/'replay.json',receipt);print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    {'freeze':freeze,'audit':run,'verify':verify}[sys.argv[1]]()
