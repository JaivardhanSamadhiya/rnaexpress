"""Synthetic benchmark or metadata-only exhaustive graph; never fitting."""
from .common import *
from .graph import runtime_binding,distance_matrix,build_graph
from .splits import attach_groups,outer_masks,inner_masks
from src.generalization_crosscell_20261007.splits import outer_masks as old_outer,strict_purge as old_purge
import argparse,os,time

def assert_threads():
    for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):assert os.environ.get(name)=='1',name

def source_hashes():
    return {path.relative_to(ROOT).as_posix():sha256(path) for path in sorted(SRC.glob('*.py'))}

def benchmark():
    assert_threads();rng=np.random.default_rng(SEED)
    sequences=[]
    for _ in range(100):
        parent=''.join(rng.choice(list('ACGT'),LENGTH))
        for nedit in range(10):
            sequence=list(parent)
            for site in rng.choice(LENGTH,nedit,replace=False):sequence[site]=rng.choice([base for base in 'ACGT' if base!=sequence[site]])
            sequences.append(''.join(sequence))
    started=time.perf_counter();elements=0;maximum=0
    for start in range(0,len(sequences),BLOCK):
        matrix=distance_matrix(sequences[start:start+BLOCK],sequences[start:])
        maximum=max(maximum,matrix.nbytes);elements+=matrix.size
    elapsed=time.perf_counter()-started
    project_elements=sum(min(BLOCK,9318-start)*(9318-start) for start in range(0,9318,BLOCK))
    receipt={'status':'PASS','synthetic_sequences':len(sequences),'distance_elements':elements,
             'elapsed_seconds':elapsed,'maximum_distance_buffer_bytes':maximum,
             'project_distance_elements':project_elements,'extrapolated_distance_seconds':elapsed*project_elements/elements,
             'extrapolation_limit':'Excludes graph bookkeeping and project sequence composition differences; not a runtime guarantee.',
             'runtime':runtime_binding(),'source_hashes':source_hashes()}
    jsave(OUT/'synthetic_benchmark.json',receipt);print(json.dumps(clean(receipt),indent=2))

def support(frame,mask):
    selected=frame.loc[mask]
    return {'rows':len(selected),'contexts':selected.parent_context_id.nunique(),
            'genes':selected.gene_transcript.nunique(),'components':selected.biological_component.nunique(),
            'similarity_families':selected.similarity_component.nunique()}

def audit():
    assert_threads();frame,_=load(False)
    protocol=REP/'protocol.md';tests=json.loads((OUT/'synthetic_tests_receipt.json').read_text())
    assert tests['status']=='PASS' and tests['source_hashes']==source_hashes()
    preanalysis={'scope':'metadata-only graph and split feasibility; not supervised prefit',
                 'primary_distance':'global unit-cost Levenshtein','cutoff':CUTOFF,'length':LENGTH,
                 'weights':[1,1,1],'source_hashes':source_hashes(),
                 'protocol_sha256':sha256(protocol),'core_metadata_sha256':metadata_hash(frame),'runtime':runtime_binding()}
    jsave(OUT/'preanalysis_manifest.json',preanalysis)
    roster,groups,edges,receipt=build_graph(frame,lambda n,total,elapsed:print(json.dumps({'alleles_completed':n,'total':total,'elapsed_seconds':round(elapsed,3)}),flush=True) if n%1024==0 or n==total else None)
    grouped=attach_groups(frame,groups);audits=[]
    for task in TASKS:
        for fold in FOLDS:
            train,test=outer_masks(grouped,task,fold);baseline,_=old_outer(frame,task,fold)
            assert np.array_equal(test,old_outer(frame,task,fold)[1])
            record={'scope':'outer','task':task,'outer_fold':fold,'inner_fold':None,
                    'before_rows':int(baseline.sum()),'target':support(grouped,test),'after':support(grouped,train),
                    'removed_rows':int(baseline.sum()-train.sum()),'viable':bool(train.any())}
            audits.append(record)
            source=grouped.loc[train].reset_index(drop=True)
            for inner_fold in [value for value in FOLDS if value!=fold]:
                itr,iva=inner_masks(source,int(inner_fold));old_itr=old_purge(source,~iva,iva)
                audits.append({'scope':'inner','task':task,'outer_fold':fold,'inner_fold':int(inner_fold),
                               'before_rows':int(old_itr.sum()),'target':support(source,iva),'after':support(source,itr),
                               'removed_rows':int(old_itr.sum()-itr.sum()),'viable':bool(itr.any() and iva.any())})
    flat=[]
    for row in audits:
        item={name:value for name,value in row.items() if name not in {'target','after'}}
        for prefix in ('target','after'):
            item.update({prefix+'_'+name:value for name,value in row[prefix].items()})
        flat.append(item)
    paths=[ART/'original_allele_inventory.csv.gz',ART/'similarity_components.csv',ART/'direct_gene_edges.csv',OUT/'split_support.csv']
    csvsave(paths[0],roster,True);csvsave(paths[1],groups);csvsave(paths[2],edges);csvsave(paths[3],pd.DataFrame(flat))
    receipt.update({'status':'PASS','metadata_rows':len(frame),'cutoff':CUTOFF,'length':LENGTH,
                    'preanalysis_manifest_sha256':sha256(OUT/'preanalysis_manifest.json'),
                    'output_hashes':{path.relative_to(ROOT).as_posix():sha256(path) for path in paths},
                    'all_outer_inner_support_nonempty':all(row['viable'] for row in audits),
                    'split_audits':audits,'source_hashes':source_hashes(),'no_outcomes_read':True,'fits':0})
    jsave(OUT/'metadata_graph_receipt.json',receipt);print(json.dumps(clean(receipt),indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['benchmark','audit']);args=parser.parse_args()
    (benchmark if args.action=='benchmark' else audit)()
