"""Outcome-free single-nucleotide pooling specification; no encoder import."""
from __future__ import annotations
import io
import json
import sys
from .resources import ROOT,ART,OUT,MODEL,save,jsave,digest

sys.path.insert(0,str(ROOT/'data/interim/mechanism_v2/runtime'))
import numpy as np

SEED=20261007
GLOBAL=ART/'global_projection.npy'
LOCAL=ART/'local_projection.npy'


def projection_arrays():
    rng=np.random.default_rng(SEED)
    return [(rng.standard_normal((512,128))/np.sqrt(128)).astype(np.float32) for _ in range(2)]


def normalize(sequence):
    result=str(sequence).upper().replace('U','T')
    assert result and not set(result)-set('ACGT')
    return result


def changed_positions(parent,mutant):
    parent,mutant=normalize(parent),normalize(mutant)
    assert len(parent)==len(mutant)
    return np.asarray([i for i,(p,m) in enumerate(zip(parent,mutant)) if p!=m],dtype=int)


def pooled_delta(parent,mutant,hp,hm,pglobal,plocal):
    parent,mutant=normalize(parent),normalize(mutant)
    changed=changed_positions(parent,mutant)
    assert hp.shape==hm.shape==(len(parent)+2,512)
    assert np.isfinite(hp).all() and np.isfinite(hm).all()
    if not len(changed):return np.zeros(256,dtype=np.float32)
    global_delta=(hm[1:-1].mean(0)-hp[1:-1].mean(0))@pglobal
    local_delta=(hm[changed+1]-hp[changed+1]).mean(0)@plocal
    result=np.r_[global_delta,local_delta].astype(np.float32)
    assert np.isfinite(result).all()
    return result


def lookup_delta(parent,mutant,pglobal,plocal):
    parent,mutant=normalize(parent),normalize(mutant)
    changed=changed_positions(parent,mutant)
    if not len(changed):return np.zeros(256,dtype=np.float32)
    ids={base:index for index,base in enumerate('ACGT')}
    pi=np.asarray([ids[base] for base in parent]);mi=np.asarray([ids[base] for base in mutant])
    return np.r_[pglobal[mi].mean(0)-pglobal[pi].mean(0),
                 plocal[mi[changed]].mean(0)-plocal[pi[changed]].mean(0)].astype(np.float32)


def prepare():
    for path,matrix in zip((GLOBAL,LOCAL),projection_arrays()):
        stream=io.BytesIO();np.save(stream,matrix,allow_pickle=False);save(path,stream.getvalue())
    vocabulary=(MODEL/'vocab.txt').read_text().splitlines()
    assert vocabulary[6:]==list('ACGT')
    spec={'scope':'Prospective outcome-free representation preparation only; no encoder execution',
          'checkpoint_variant':'SpliceBERT.1024nt','hidden_dimensions':512,'projected_global':128,'projected_changed_base':128,
          'projection':'default_rng(20261007), global then local float64 standard_normal((512,128))/sqrt(128), cast float32',
          'global_projection_sha256':digest(GLOBAL),'local_projection_sha256':digest(LOCAL),
          'global_pool':'last-layer mean single-base tokens only, excludes CLS/SEP/padding; mutant minus parent',
          'local_pool':'mean corresponding last-layer single-base tokens exactly at all changed nucleotide positions; mutant minus parent',
          'lookup_control':'A/C/G/T vocabulary order one-hot first4of512, same projections/pools; rank<=4 per block',
          'sequence_context':'Same original26258core IDs; exact150/190/260nt inserts and certifiedSRLE20+6+20 context46nt',
          'short_sequence_domain_gap':'Author trained64-1024nt;46ntSRLE is OOD. Do not fabricate padding or omit SRLE to claimfour-assay generalization',
          'fine_tuning':False,'PCA':False,'outcomes_used':False,
          'full_production_guard':'Require committed namespace-specific production manifest, fresh RAM/disk admission, runtime/model hashes, synthetic tokenizer/numerical/batch benchmarks',
          'comparative_fit_guard':'Separate committed prefit manifest; fixed3L2 source-only nested whole-assay selection, original allele/component purge, unchanged gate',
          'required_controls':'Correctedbase246; matched single-base noncontextuallookup256; report comparison to3UTRBERT separately without claiming corpus/tokenizationcausality'}
    jsave(OUT/'feature_proposal.json',spec)
    print('Single-base feature proposal and exact projections prepared; no model inference',flush=True)


if __name__=='__main__':prepare()
