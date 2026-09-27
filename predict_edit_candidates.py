"""Bounded, outcomes-free replay of frozen SRLE held-out candidate predictions.

This interface does not infer effects for new RNAs. Use complete admitted six-mer
candidate sets. Generalization to other genes, reporters, cells or assays is untested.
"""
import argparse
import csv
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DEFAULT_BUNDLE=ROOT/'artifacts/srle_synthesis_20260926/prototype_bundle.json'
DOMAIN=('Evaluated only in the SRLE-derived composition-preserving two-position '
        'edit task, one HBB reporter context; exploratory held-out replay. '
        'Generalization to other genes, reporters, cell types or assays is not established.')

def normalize(sequence):
    s=sequence.strip().upper().replace('U','T')
    if len(s)!=6 or any(c not in 'ACGT' for c in s):
        raise ValueError('Each local sequence must contain exactly six A/C/G/U or A/C/G/T bases.')
    return s

def validate_edit(parent,candidate):
    changed=[i for i,(a,b) in enumerate(zip(parent,candidate)) if a!=b]
    if len(changed)!=2 or Counter(parent)!=Counter(candidate):
        raise ValueError('Candidates must exchange two unequal bases and preserve composition.')
    i,j=changed
    if parent[i]!=candidate[j] or parent[j]!=candidate[i]:raise ValueError('Not a two-position swap.')
    return [i+1,j+1]

def counts(sequence,model):
    lengths=(2,) if model=='2mer' else (1,2,3)
    return [sum(sequence[i:i+k]==''.join(word) for i in range(7-k))
            for k in lengths for word in itertools.product('ACGT',repeat=k)]

def load_bundle(path=DEFAULT_BUNDLE):
    path=Path(path);manifest=json.loads(path.with_name('prototype_manifest.json').read_text(encoding='utf-8'))
    payload=path.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=manifest['bundle_sha256']:raise ValueError('Prototype bundle integrity check failed.')
    return json.loads(payload)

def predict(parent,candidates,direction='increase',model='kmer123',bundle=None):
    if direction not in ('increase','decrease'):raise ValueError('Direction must be increase or decrease.')
    if model not in ('2mer','kmer123'):raise ValueError('Model must be 2mer or kmer123.')
    bundle=load_bundle() if bundle is None else bundle
    parent=normalize(parent);candidates=[normalize(s) for s in candidates]
    if len(candidates)!=len(set(candidates)):raise ValueError('Duplicate candidates after U/T normalization.')
    if parent not in bundle['parents']:raise ValueError('Parent outside the frozen measured decision catalog.')
    info=bundle['parents'][parent]
    for candidate in candidates:validate_edit(parent,candidate)
    if sorted(candidates)!=info['candidates']:
        raise ValueError('Supply the complete frozen candidate set; new candidates and subsets are outside this replay domain.')
    fold=bundle['folds'][info['group']][model];parent_counts=counts(parent,model)
    scores=bundle['scores'][model];sense=1 if direction=='increase' else -1
    rows=[]
    for candidate in sorted(candidates):
        effect=scores[candidate]-scores[parent]
        coefficient_effect=sum((a-b)*w for a,b,w in zip(counts(candidate,model),parent_counts,fold))
        if abs(effect-coefficient_effect)>1e-12:raise ValueError('Saved prediction and coefficient reconstruction disagree.')
        rows.append({'candidate':candidate,'changed_positions':validate_edit(parent,candidate),'predicted_effect':effect,
            'model':model,'direction':direction,'domain_status':'IN_FROZEN_SRLE_CATALOG','uncertainty':'Not individually calibrated',
            'cohort_wrong_both_rate':bundle['cohort_risk'][model]['wrong_both'],
            'risk_scope':'Class-balanced historical SRLE cohort rate; not this candidate probability'})
    rows.sort(key=lambda r:(-sense*r['predicted_effect'],r['candidate']))
    for rank,row in enumerate(rows,1):row['predicted_rank']=rank;row['recommended']=rank==1
    return {'parent':parent,'domain_statement':DOMAIN,'mode':'frozen_heldout_prediction_replay',
            'experimental_outcomes_used_for_ranking':False,'candidates':rows}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',required=True);parser.add_argument('--candidates',type=Path,required=True,help='One six-mer per line, or CSV with candidate/sequence column')
    parser.add_argument('--direction',choices=['increase','decrease'],required=True)
    parser.add_argument('--model',choices=['2mer','kmer123'],default='kmer123');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        with args.candidates.open(encoding='utf-8-sig',newline='') as handle:
            first=handle.readline().strip();handle.seek(0)
            if first in ('candidate','sequence') or ',' in first:
                rows=list(csv.DictReader(handle));seq=[row.get('candidate',row.get('sequence','')) for row in rows]
            else:seq=[line.strip() for line in handle if line.strip()]
        result=predict(args.parent,seq,args.direction,args.model)
        payload=json.dumps(result,indent=2,allow_nan=False)+'\n'
        if args.output:
            with args.output.open('x',encoding='utf-8') as handle:handle.write(payload)
        else:print(payload,end='')
    except (ValueError,OSError,KeyError) as exc:parser.error(str(exc))

if __name__=='__main__':main()
