"""Outcome-free paired delta features with hash-checked, resumable folding caches."""
from __future__ import annotations
import hashlib
import importlib.metadata
import io
import json
import sqlite3
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from .io import ROOT,canonical_json,cache_key,load_development,output_path,sha256,write_json,write_once
from .primitives import align

FOLD_CONFIG={'version':'2.7.2','temperature_c':37.0,'dangles':2,'noLP':False,
             'parameters':'RNA_Turner2004','radii':[20,50,100],
             'features':['mfe_per_nt','ensemble_free_energy_per_nt','mean_unpaired_probability',
                         'mean_partner_entropy','mean_bp_distance_per_nt','mfe_paired_fraction']}


def fold_sequence(sequence):
    import RNA
    if RNA.__version__ != FOLD_CONFIG['version']:
        raise ValueError('Unexpected ViennaRNA version')
    sequence=sequence.upper().replace('T','U')
    if not sequence or set(sequence)-set('ACGU'):
        raise ValueError('Unsupported folding input')
    RNA.params_load_RNA_Turner2004()
    md=RNA.md();md.temperature=37.;md.dangles=2;md.noLP=0
    fc=RNA.fold_compound(sequence,md)
    structure,mfe=fc.mfe()
    fc.exp_params_rescale(mfe)
    _,ensemble=fc.pf()
    upper=np.asarray(fc.bpp(),dtype=np.float64)[1:,1:]
    probability=upper+upper.T
    unpaired=1-probability.sum(axis=1)
    if unpaired.min() < -1e-6 or unpaired.max()>1+1e-6:
        raise ValueError('Invalid base-pair probability normalization')
    unpaired=np.clip(unpaired,0,1)
    entropy=-(probability*np.log(np.maximum(probability,1e-300))).sum(axis=1)
    entropy-=unpaired*np.log(np.maximum(unpaired,1e-300))
    n=len(sequence)
    values=np.asarray([mfe/n,ensemble/n,unpaired.mean(),entropy.mean(),
                       fc.mean_bp_distance()/n,1-structure.count('.')/n],dtype=np.float64)
    if not np.isfinite(values).all():raise ValueError('Nonfinite structure output')
    return values.tolist()


def native_fold_hash():
    import RNA
    binaries=list(Path(RNA.__file__).parent.glob('_RNA*.pyd'))
    if not binaries:
        binaries=list(Path(RNA.__file__).parent.glob('_RNA*.so'))
    if len(binaries)!=1:raise ValueError('Cannot uniquely identify folding runtime binary')
    return sha256(binaries[0])


def array_file(relative,values):
    stream=io.BytesIO();np.save(stream,values,allow_pickle=False)
    path=write_once(relative,stream.getvalue())
    return {'path':relative,'shape':list(values.shape),'sha256':sha256(path),'dtype':str(values.dtype)}


def build_delta_caches():
    """Extract declared signed deltas; no geometry/absolute parent in primary block."""
    interventions=load_development('results/v4_phaseB/model_interventions.csv.gz')
    if not np.array_equal(interventions.feature_row,np.arange(len(interventions))):
        raise ValueError('Intervention indices not contiguous')
    old=ROOT/'data/interim/finalshot_rbpnet_features.npy'
    if sha256(old)!='3857bc47510828ff6e45134e0429d760f424b20fed4dcae3675fb40abbf77abc':
        raise ValueError('Archived RBP matrix changed')
    x=np.load(old,mmap_mode='r')
    if x.shape!=(len(interventions),927) or not np.isfinite(x).all():
        raise ValueError('RBP matrix shape/finite invariant failed')
    columns=np.array([g*9+j for g in range(103) for j in [0,1,2,8]])
    record=array_file('data/interim/mechanism_v2/rbp_signed_delta.npy',np.asarray(x[:,columns]))
    record.update({'source_sha256':sha256(old),'source_columns':columns.tolist(),
        'per_rbp':['delta_mass_radius10','delta_mass_radius25','delta_mass_radius50','delta_mixing_coefficient'],
        'excluded':['absolute parent','geometry','max_abs_delta','global_gain','global_loss'],
        'interpretation':'human HepG2 RBPNet signed profile summaries; no TARDBP checkpoint',
        'checkpoint_provenance':'results/finalshot/rbp_signature_manifest.json',
        'status':'cached independently pretrained fallback; not a paper-matching Parnet admission'})
    write_json('results/mechanism_v2/features/rbp_signed_delta_manifest.json',record)
    bert=ROOT/'data/interim/v4_phaseB_3utrbert_full_features.npy'
    if sha256(bert)!='51912767e74dc19a06dadf6bab9f3022f11939f1cc537f024af148cc18f948d9':
        raise ValueError('Archived 3UTRBERT matrix changed')
    b=np.load(bert,mmap_mode='r')
    if b.shape!=(len(interventions),384):raise ValueError('3UTRBERT schema mismatch')
    brecord=array_file('data/interim/mechanism_v2/bert_contextual_delta.npy',np.asarray(b[:,256:384]))
    brecord.update({'source_sha256':sha256(bert),'source_columns':[256,384],
        'interpretation':'128-dimensional fixed projected contextual token deltas, not mutant absolute block',
        'source_code':'src/modeling/v4_embeddings.py','source_code_sha256':sha256(ROOT/'src/modeling/v4_embeddings.py'),
        'metadata_sha256':sha256(ROOT/'data/interim/v4_phaseB_3utrbert_full_features.json'),
        'status':'separate sequence-prior comparator; admission/configuration not yet frozen'})
    write_json('results/mechanism_v2/features/bert_delta_manifest.json',brecord)
    print('Cached signed RBP deltas (412 columns) and contextual BERT deltas (128 columns)',flush=True)


def build_structure(limit=None,workers=3):
    rows=load_development('results/v4_phaseB/model_interventions.csv.gz')
    if limit is not None:rows=rows.iloc[:limit].copy()
    model_hash=native_fold_hash()
    config_hash=hashlib.sha256(canonical_json(FOLD_CONFIG)).hexdigest()
    sequences={};pairs=[]
    for row in rows.itertuples(index=False):
        alignment=align(row.parent_sequence,row.mutant_sequence)
        for radius in FOLD_CONFIG['radii']:
            ref_interval,mut_interval=alignment.windows(radius)
            ref=alignment.reference[slice(*ref_interval)];mut=alignment.mutant[slice(*mut_interval)]
            keys=[]
            for seq in (ref,mut):
                key=cache_key(seq,model_hash,FOLD_CONFIG)
                sequences[key]=seq;keys.append(key)
            pairs.append(keys)
    db_path=output_path(f'data/interim/mechanism_v2/structure_cache_{model_hash[:12]}_{config_hash[:12]}.sqlite')
    db_path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(db_path)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL)')
    cached={}
    for key,payload,digest in db.execute('SELECT key,payload,sha256 FROM cache'):
        if hashlib.sha256(payload.encode()).hexdigest()!=digest:
            raise ValueError('Structure cache hash mismatch')
        if key in sequences:cached[key]=json.loads(payload)
    pending=sorted(set(sequences)-set(cached))
    print(f'Structure: {len(rows)} pairs, {len(sequences)} unique windows, {len(cached)} verified cached',flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i,(key,values) in enumerate(zip(pending,pool.map(fold_sequence,(sequences[k] for k in pending),chunksize=32))):
            payload=json.dumps(values,separators=(',',':'),allow_nan=False)
            digest=hashlib.sha256(payload.encode()).hexdigest()
            db.execute('INSERT INTO cache VALUES (?,?,?)',(key,payload,digest))
            cached[key]=values
            if (i+1)%512==0:
                db.commit()
            if (i+1)%2048==0 or i+1==len(pending):
                db.commit()
                print(f'Structure cached {len(cached)}/{len(sequences)}',flush=True)
    db.commit();db.close()
    values=np.asarray([np.asarray(cached[mut])-np.asarray(cached[ref]) for ref,mut in pairs],dtype=np.float32)
    values=values.reshape(len(rows),-1)
    if not np.isfinite(values).all():raise ValueError('Nonfinite structure deltas')
    suffix='full' if limit is None else f'pilot_{limit}'
    record=array_file(f'data/interim/mechanism_v2/structure_delta_{suffix}.npy',values)
    record.update({'config':FOLD_CONFIG,'native_binary_sha256':model_hash,'config_sha256':config_hash,
        'feature_order':'radius-major, summary-minor; all mutant minus reference',
        'intervention_sha256':sha256(ROOT/'results/v4_phaseB/model_interventions.csv.gz'),
        'code_sha256':sha256(Path(__file__)),'unique_windows':len(sequences),
        'input_scope':'outcome-free certified intervention table; no outcome columns',
        'caveat':'marginal unpaired probability, not joint motif accessibility; equilibrium local folding, not in-cell measurement'})
    write_json(f'results/mechanism_v2/features/structure_delta_{suffix}_manifest.json',record)
    return record
