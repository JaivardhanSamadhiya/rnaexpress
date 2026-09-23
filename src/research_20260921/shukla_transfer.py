"""Fixed external fragment-selection pilot; target counts accessed by replicate."""
from .common import ROOT,sha256,write_json,write_new
from .context_calibration import OUT,DATA,features,read_outcomes
from .shukla_sequence_recovery import HEADER
import csv,gzip,hashlib,io,json,subprocess,sys
import numpy as np
import pandas as pd
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

NAME='shukla_transfer'
MODELS=['source_kmer','source_composition','ccc']


def family(name):
    return {'ANCR':'DANCR','FIRRE(HG)':'FIRRE','FIRRE(MM)':'FIRRE',
            'lincFOXF1':'FENDRR'}.get(name,name.upper())


def prepare():
    target=pd.read_csv(OUT/'shukla2018_reference_admitted_sequences.csv')
    target['component']=[family(g) for g in target.gene]
    source=pd.read_csv(OUT/'context_calibration_partition.csv')
    source=source[source.partition=='source'].copy().reset_index(drop=True)
    if len(source)!=3235 or source.component.nunique()!=61:raise ValueError('Source boundary changed')
    metadata=list(csv.DictReader((DATA/'shukla2018_oligoMeta.tsv').open(),delimiter='\t'))
    target_families={family(m['name1']) for m in metadata}|{m['name2'].upper() for m in metadata}
    reasons={}
    for row in source.itertuples():
        if row.component in target_families:reasons.setdefault(row.component,set()).add('named_target_family')
    # Check all admitted target sequences, including small decision sets.
    words={s[i:i+40] for s in target.sequence for i in range(len(s)-39)}
    for row in source.itertuples():
        if any(row.sequence[i:i+40] in words for i in range(len(row.sequence)-39)):
            reasons.setdefault(row.component,set()).add('shared_40nt_tract')
    scores=process.cdist(source.sequence.tolist(),target.sequence.tolist(),
                        scorer=Levenshtein.normalized_similarity,score_cutoff=.95,
                        dtype=np.float32,workers=2)
    for i in np.flatnonzero(np.any(scores>=.95,axis=1)):
        reasons.setdefault(source.iloc[i].component,set()).add('95pct_global_sequence_similarity')
    source=source[~source.component.isin(reasons)].copy()
    # A target family is kept together for uncertainty; no target outcome fitting.
    values,accessed=read_outcomes(DATA/'context2022_data3.xlsx',source.excel_row)
    y=np.asarray([values[int(row)][1] for row in source.excel_row]) # Unspliced only.
    good=np.isfinite(y);source=source.loc[good].copy();y=y[good]
    if source.component.nunique()<20 or len(source)<500:raise ValueError('Insufficient source support')
    x=features(source.sequence);xt=features(target.sequence)
    for name,columns in [('source_kmer',84),('source_composition',4)]:
        scaler=StandardScaler().fit(x[:,:columns])
        model=Ridge(alpha=100).fit(scaler.transform(x[:,:columns]),y)
        target[name]=model.predict(scaler.transform(xt[:,:columns]))
    target['ccc']=[sum(s[i:i+3]=='CCC' for i in range(len(s)-2)) for s in target.sequence]
    write_new(OUT/(NAME+'_predictions.csv'),target.to_csv(index=False,lineterminator='\n').encode())
    write_new(OUT/(NAME+'_source_rows.csv'),source[['id','excel_row','component']].to_csv(index=False,lineterminator='\n').encode())
    result={'source_rows':len(source),'source_components':int(source.component.nunique()),
            'excluded_source_components':{k:sorted(v) for k,v in sorted(reasons.items())},
            'target_rows':len(target),'target_gene_sets':int(target.accession.nunique()),
            'target_families_with_10_candidate_gene_set':int(target.groupby('accession').filter(lambda g:len(g)>=10).component.nunique()),
            'target_numeric_outcomes_read':False,
            'source_accessed_numeric_cells':len(accessed),
            'source_accessed_hash':hashlib.sha256('\n'.join(accessed).encode()).hexdigest(),
            'source_context':'Unspliced HBB, MCF7; existing source groups only',
            'target_context':'fsSox2, HeLa; nuclear/whole-cell abundance',
            'scope':'External study pilot of fragment selection; not minimal edits, novel mechanism, or same-assay confirmation.'}
    write_json(OUT/(NAME+'_inventory.json'),result)
    print(json.dumps(result,indent=2),flush=True)


def freeze():
    paths=[ROOT/'src/research_20260921'/n for n in ['shukla_transfer.py','shukla_reference_admission.py',
        'shukla_sequence_recovery.py','test_shukla_transfer.py','test_shukla_recovery.py','common.py','context_calibration.py']]
    paths += [ROOT/'reports/research_20260921/shukla_transfer_spec.md',
              DATA/'shukla2018_counts.tsv.gz',DATA/'context2022_data3.xlsx',DATA/'shukla2018_oligoMeta.tsv',
              DATA/'shukla2018_refseq_v1.fasta',DATA/'SRR5528987.first16MiB.gz',
              OUT/'context_calibration_partition.csv',OUT/'shukla2018_reference_admitted_sequences.csv',
              OUT/'shukla2018_reference_admission.json',OUT/(NAME+'_predictions.csv'),
              OUT/(NAME+'_source_rows.csv'),OUT/(NAME+'_inventory.json')]
    write_json(OUT/(NAME+'_freeze.json'),{'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
        'target_numeric_outcomes_read':False,'reserved_replicates':[4,5,6],
        'status':'Fixed external-study pilot; literature findings and previous transfer failures known'})


def verify():
    path=OUT/(NAME+'_freeze.json')
    for p,h in json.loads(path.read_text())['files'].items():
        if sha256(ROOT/p)!=h:raise ValueError(('Frozen artifact changed',p))
    if subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)!=path.read_bytes():
        raise ValueError('Commit exact freeze before target outcomes')


def read_target(path,allowed_ids,reps):
    if tuple(reps) not in [(1,2,3),(4,5,6)]:raise ValueError('Invalid replicate set')
    allowed=set(allowed_ids);result={};accessed=[]
    with gzip.open(path,'rt') as stream:
        if stream.readline().strip().split('\t')!=HEADER:raise ValueError('Unexpected schema')
        for line in stream:
            cells=line.rstrip('\n').split('\t')
            if cells[0] not in allowed:continue
            if len(cells)!=13:raise ValueError('Malformed target row')
            # Unselected cells are never converted, returned, logged or used.
            values=[]
            for rep in reps:
                n,t=float(cells[rep]),float(cells[rep+6])
                values.append(float(np.log2(n/t)) if np.isfinite(n) and np.isfinite(t) and n>0 and t>0 else float('nan'))
                accessed.extend([cells[0]+':'+HEADER[rep],cells[0]+':'+HEADER[rep+6]])
            result[cells[0]]=values
    if set(result)!=allowed:raise ValueError('Missing target IDs')
    return result,accessed


def tied_regret(y,p):
    if len(y)<10 or np.ptp(y)<=0:raise ValueError('Ineligible candidate set')
    # Average the measured outcome over exact predicted ties. No ID advantage.
    return float(np.mean([(np.max(sign*y)-np.mean(sign*y[sign*p==np.max(sign*p)]))/np.ptp(y)
                          for sign in [1,-1]]))


def require_confirmation(prior):
    if not prior.get('discovery_pass',False):raise PermissionError('Discovery failed: target replicates 4-6 remain closed')


def run(stage):
    verify()
    if stage not in ['discovery','confirmation']:raise ValueError(stage)
    if stage=='confirmation':require_confirmation(json.loads((OUT/(NAME+'_discovery.json')).read_text()))
    f=pd.read_csv(OUT/(NAME+'_predictions.csv'));reps=(1,2,3) if stage=='discovery' else (4,5,6)
    if stage=='confirmation':
        admitted=json.loads((OUT/(NAME+'_discovery_eligible_ids.json')).read_text())['ids']
        f=f[f.id.isin(admitted)].copy()
    # Gene sets smaller than ten are metadata-ineligible: no counts opened.
    f=f.groupby('accession',group_keys=False).filter(lambda g:len(g)>=10).copy()
    values,accessed=read_target(DATA/'shukla2018_counts.tsv.gz',f.id,reps)
    finite=f.id.map(lambda name:np.isfinite(values[name]).all())
    f=f[finite].copy();records=[];eligible=[]
    for accession,g in f.groupby('accession'):
        if len(g)<10:continue
        y=np.array([values[name] for name in g.id])
        if np.any(np.ptp(y,axis=0)<=0):continue
        eligible.extend(g.id.tolist())
        for i,rep in enumerate(reps):
            for model in MODELS:
                records.append({'accession':accession,'component':g.component.iloc[0],
                    'replicate':rep,'model':model,'candidates':len(g),
                    'regret':tied_regret(y[:,i],g[model].to_numpy())})
    if not records:raise ValueError('No eligible decisions')
    d=pd.DataFrame(records)
    # First average genes within family (FIRRE orthologs), then families equally.
    m=d.groupby(['component','replicate','model']).regret.mean().unstack('model')
    components=sorted(m.index.get_level_values(0).unique())
    draws=np.random.default_rng(20260923).integers(0,len(components),(5000,len(components)))
    comparisons={};passes=[]
    for baseline in ['source_composition','ccc','random']:
        gain=((.5 if baseline=='random' else m[baseline])-m.source_kmer).unstack('replicate').reindex(components)
        arr=gain.to_numpy();point=float(arr.mean());boot=arr.mean(axis=1)[draws].mean(axis=1)
        ci=np.quantile(boot,[.025,.975]).tolist();by_rep={str(r):float(v) for r,v in zip(reps,arr.mean(axis=0))}
        passed=len(components)>=12 and point>=.05 and ci[0]>0 and min(by_rep.values())>0
        passes.append(passed)
        comparisons[baseline]={'regret_gain':point,'descriptive_family_ci95':ci,'by_replicate':by_rep,'passes':bool(passed)}
    result={'stage':stage,'replicates_read':list(reps),'eligible_families':len(components),
            'eligible_gene_sets':int(d.accession.nunique()),'eligible_fragments':len(eligible),
            'regret':{k:float(v) for k,v in m.groupby('component').mean().mean().items()},
            'comparisons':comparisons,'discovery_pass':all(passes) if stage=='discovery' else None,
            'confirmation_pass':all(passes) if stage=='confirmation' else None,
            'accessed_numeric_cells':len(accessed),'accessed_cells_sha256':hashlib.sha256('\n'.join(accessed).encode()).hexdigest(),
            'interpretation':'External study fragment-selection pilot; QC-selected subset. Family bootstrap excludes source-fit uncertainty. No minimal-edit or new-mechanism claim.'}
    write_new(OUT/(NAME+'_'+stage+'_decisions.csv'),d.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT/(NAME+'_'+stage+'_eligible_ids.json'),{'ids':sorted(eligible)})
    write_json(OUT/(NAME+'_'+stage+'.json'),result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    command=sys.argv[1]
    if command=='prepare':prepare()
    elif command=='freeze':freeze()
    else:run(command)
