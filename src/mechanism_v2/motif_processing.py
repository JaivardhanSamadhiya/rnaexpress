"""External-consensus nuisance features and site-marginal accessibility deltas."""
from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import sqlite3
import numpy as np
from .io import ROOT,load_development,cache_key,canonical_json,sha256,write_json,output_path
from .features import array_file,native_fold_hash

DESIGN_PATH=ROOT/'configs/mechanism_v2/motif_processing_design.json'
DESIGN=json.loads(DESIGN_PATH.read_text())


def normalize(sequence):
    sequence=sequence.upper().replace('U','T')
    if not sequence or set(sequence)-set('ACGT'):raise ValueError('Only certified ACGT/U input accepted')
    return sequence


def motif_spans(sequence,pattern):
    return [(m.start(),m.start()+len(m.group(1))) for m in re.finditer(f'(?=({pattern}))',sequence)]


def max_fraction(sequence,bases,width):
    width=min(width,len(sequence))
    return max(sum(c in bases for c in sequence[i:i+width])/width for i in range(len(sequence)-width+1))


def processing_values(sequence):
    sequence=normalize(sequence)
    values=[100*len(motif_spans(sequence,pattern))/len(sequence)
        for pattern in DESIGN['processing_patterns'].values()]
    values += [max_fraction(sequence,'CT',12),max_fraction(sequence,'T',8),sequence.count('T')/len(sequence)]
    return np.asarray(values,float)


def motif_values(sequence):
    import RNA
    sequence=normalize(sequence)
    if RNA.__version__!=DESIGN['structure']['version']:raise ValueError('ViennaRNA version mismatch')
    spans=[motif_spans(sequence,m['regex']) for m in DESIGN['motifs']]
    counts=np.asarray(list(map(len,spans)),float)
    if not counts.any():return [0.]*8  # Actual absence of all declared motifs, not an unsupported RBP channel.
    RNA.params_load_RNA_Turner2004()
    md=RNA.md();md.temperature=37.;md.dangles=2;md.noLP=0
    fc=RNA.fold_compound(sequence.replace('T','U'),md)
    _,mfe=fc.mfe();fc.exp_params_rescale(mfe);fc.pf()
    upper=np.asarray(fc.bpp(),float)[1:,1:]
    unpaired=1-(upper+upper.T).sum(axis=1)
    if unpaired.min() < -1e-6 or unpaired.max()>1+1e-6:raise ValueError('Invalid pairing probabilities')
    unpaired=np.clip(unpaired,0,1)
    exposure=np.array([sum(float(unpaired[a:b].mean()) for a,b in hits) for hits in spans])
    result=np.r_[counts,exposure]*100/len(sequence)
    if not np.isfinite(result).all() or np.any(result[4:]>result[:4]+1e-8):
        raise ValueError('Invalid marginal motif exposure')
    return result.tolist()


def build_processing():
    interventions=load_development('results/v4_phaseB/model_interventions.csv.gz')
    sequences=sorted(set(interventions.parent_sequence)|set(interventions.mutant_sequence))
    values={s:processing_values(s) for s in sequences}
    deltas=np.asarray([values[r.mutant_sequence]-values[r.parent_sequence] for r in interventions.itertuples(index=False)],np.float32)
    record=array_file('data/interim/mechanism_v2/processing_nuisance_delta.npy',deltas)
    record.update({'configuration_sha256':sha256(DESIGN_PATH),'code_sha256':sha256(Path(__file__)),
        'features':[f'delta_{s}' for s in [*DESIGN['processing_patterns'],*DESIGN['processing_additional_summaries']]],
        'interpretation':DESIGN['processing_interpretation'],'observations_excluded':0,
        'intervention_sha256':sha256(ROOT/'results/v4_phaseB/model_interventions.csv.gz')})
    write_json('results/mechanism_v2/features/processing_nuisance_delta_manifest.json',record)
    print(f'Processing nuisance deltas completed: {deltas.shape}',flush=True)
    return record


def build_motif_accessibility(limit=None,workers=3):
    rows=load_development('results/v4_phaseB/model_interventions.csv.gz')
    if limit is not None:rows=rows.iloc[:limit].copy()
    binary_hash=native_fold_hash();config_hash=sha256(DESIGN_PATH)
    sequence_set=sorted(set(rows.parent_sequence)|set(rows.mutant_sequence))
    sequences={cache_key(s,binary_hash,DESIGN):s for s in sequence_set}
    dbpath=output_path(f'data/interim/mechanism_v2/motif_accessibility_{binary_hash[:12]}_{config_hash[:12]}.sqlite')
    db=sqlite3.connect(dbpath);db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY,payload TEXT NOT NULL,sha256 TEXT NOT NULL)')
    cached={}
    for key,payload,digest in db.execute('SELECT key,payload,sha256 FROM cache'):
        if hashlib.sha256(payload.encode()).hexdigest()!=digest:raise ValueError('Motif cache payload hash mismatch')
        if key in sequences:cached[key]=json.loads(payload)
    pending=sorted(set(sequences)-set(cached))
    print(f'Motif accessibility: {len(cached)}/{len(sequences)} verified cached',flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i,(key,values) in enumerate(zip(pending,pool.map(motif_values,(sequences[k] for k in pending),chunksize=32))):
            payload=json.dumps(values,separators=(',',':'),allow_nan=False)
            db.execute('INSERT INTO cache VALUES (?,?,?)',(key,payload,hashlib.sha256(payload.encode()).hexdigest()))
            cached[key]=values
            if (i+1)%512==0:db.commit()
            if (i+1)%2048==0 or i+1==len(pending):
                db.commit();print(f'Motif accessibility cached {len(cached)}/{len(sequences)}',flush=True)
    db.commit();db.close()
    by_sequence={s:np.asarray(cached[key]) for key,s in sequences.items()}
    deltas=np.asarray([by_sequence[r.mutant_sequence]-by_sequence[r.parent_sequence] for r in rows.itertuples(index=False)],np.float32)
    name='full' if limit is None else f'pilot_{limit}'
    record=array_file(f'data/interim/mechanism_v2/motif_accessibility_delta_{name}.npy',deltas)
    record.update({'configuration_sha256':config_hash,'configuration':DESIGN,'native_binary_sha256':binary_hash,
        'code_sha256':sha256(Path(__file__)),'unique_sequences':len(sequences),
        'feature_order':'four motif density deltas, followed by four site-marginal exposure density deltas',
        'intervention_sha256':sha256(ROOT/'results/v4_phaseB/model_interventions.csv.gz')})
    write_json(f'results/mechanism_v2/features/motif_accessibility_delta_{name}_manifest.json',record)
    return record
