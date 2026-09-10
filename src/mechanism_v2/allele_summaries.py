"""Recover matched absolute allele summaries for fair delta/absolute controls.

No encoder is retrained. Every archived profile shard is hash-verified before
reading. New per-checkpoint outputs resume only from verified new manifests.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .io import ROOT,load_development,write_json,sha256
from .features import array_file
from .preservation import preserve


def decoded_sequence_hashes(values):
    values=np.asarray(values)
    if values.ndim!=1 or values.dtype not in (np.dtype('S64'),np.dtype('U64')):
        raise ValueError('Unexpected stored sequence-hash representation')
    decoded=values.astype('U64')
    if any(len(s)!=64 or set(s)-set('0123456789abcdef') for s in decoded):
        raise ValueError('Invalid stored sequence digest')
    return decoded


def pooled_features(profile,mixing,indices,starts,ends,lengths):
    profile=np.asarray(profile,dtype=np.float32)
    if profile.ndim!=2 or len(mixing)!=len(profile):raise ValueError('Invalid profile shapes')
    prefix=np.column_stack([np.zeros(len(profile)),np.cumsum(profile,axis=1,dtype=np.float64)])
    result=[]
    for radius in [10,25,50]:
        left=np.maximum(0,starts-radius);right=np.minimum(lengths[indices],ends+radius)
        if (right<=left).any():raise ValueError('Invalid allele pooling window')
        result.append(prefix[indices,right]-prefix[indices,left])
    result.append(np.asarray(mixing)[indices])
    values=np.column_stack(result).astype(np.float32)
    if not np.isfinite(values).all():raise ValueError('Non-finite absolute allele features')
    return values


def build_allele_summaries():
    preserve()
    rows=load_development('results/v4_phaseB/model_interventions.csv.gz')
    sequences=sorted(set(rows.parent_sequence)|set(rows.mutant_sequence),key=lambda s:hashlib.sha256(s.encode()).hexdigest())
    hashes=np.array([hashlib.sha256(s.encode()).hexdigest() for s in sequences])
    lengths=np.array(list(map(len,sequences)),dtype=int);lookup={s:i for i,s in enumerate(sequences)}
    parent_idx=np.array([lookup[s] for s in rows.parent_sequence]);mutant_idx=np.array([lookup[s] for s in rows.mutant_sequence])
    starts=[];ends=[]
    for a,b in zip(rows.parent_sequence,rows.mutant_sequence):
        if len(a)!=len(b):raise ValueError('Archived RBP profiles require equal-length pair convention')
        changed=np.flatnonzero(np.frombuffer(a.encode(),np.uint8)!=np.frombuffer(b.encode(),np.uint8))
        if not len(changed):raise ValueError('No mutation in intervention')
        starts.append(changed.min());ends.append(changed.max()+1)
    starts=np.array(starts,int);ends=np.array(ends,int)
    signature_path=ROOT/'results/finalshot/rbp_signature_manifest.json'
    manifest=json.loads(signature_path.read_text())
    entries=manifest['checkpoint_caches']
    dictionary=pd.read_csv(ROOT/'results/finalshot/rbp_feature_dictionary.csv')
    tasks=dictionary.groupby('group_index').first()['task'].tolist() if 'task' in dictionary else None
    if tasks is None:
        checkpoints=pd.read_csv(ROOT/'results/finalshot/rbpnet_checkpoint_manifest.csv')
        tasks=checkpoints.task.tolist()
    if len(entries)!=103 or set(tasks)!={e['task'] for e in entries}:raise ValueError('RBP channel inventory mismatch')
    entries={e['task']:e for e in entries}
    signed_record=json.loads((ROOT/'results/mechanism_v2/features/rbp_signed_delta_manifest.json').read_text())
    if sha256(ROOT/signed_record['path'])!=signed_record['sha256']:raise ValueError('Signed RBP matrix changed')
    signed=np.load(ROOT/signed_record['path'],mmap_mode='r')
    reference=[];mutant=[];audit=[]
    for ordinal,task in enumerate(tasks):
        entry=entries[task]
        path=(ROOT/entry['profile_file']).resolve()
        allowed=(ROOT/'data/interim/finalshot_rbpnet_cache/profiles').resolve()
        if path.parent!=allowed:raise PermissionError('Unexpected archived profile path')
        record_path=ROOT/f'results/mechanism_v2/features/allele_shards/{task}.json'
        if record_path.exists():
            record=json.loads(record_path.read_text())
            if record['source_profile_sha256']!=entry['profile_sha256']:raise ValueError('Source profile identity changed')
            for key in ['reference','mutant']:
                if sha256(ROOT/record[key]['path'])!=record[key]['sha256']:raise ValueError('Absolute allele shard hash mismatch')
        else:
            if sha256(path)!=entry['profile_sha256']:raise ValueError(f'Archived profile hash mismatch: {task}')
            with np.load(path,allow_pickle=False) as data:
                if not np.array_equal(decoded_sequence_hashes(data['sequence_sha256']),hashes) or not np.array_equal(data['lengths'],lengths):
                    raise ValueError('Profile sequence order/length changed')
                profile=data['target_profile'];mixing=data['mixing']
                a=pooled_features(profile,mixing,parent_idx,starts,ends,lengths)
                b=pooled_features(profile,mixing,mutant_idx,starts,ends,lengths)
            error=float(np.max(np.abs((b-a)-signed[:,ordinal*4:ordinal*4+4])))
            if error>1e-6:raise ValueError(f'Allele difference does not reproduce signed RBP features: {task}, {error}')
            record={'task':task,'source_profile_sha256':entry['profile_sha256'],'max_delta_reconstruction_error':error,
                'reference':array_file(f'data/interim/mechanism_v2/allele_shards/{task}_reference.npy',a),
                'mutant':array_file(f'data/interim/mechanism_v2/allele_shards/{task}_mutant.npy',b),
                'roles':['mass_radius10','mass_radius25','mass_radius50','mixing_coefficient']}
            write_json(record_path,record)
        reference.append(np.load(ROOT/record['reference']['path']))
        mutant.append(np.load(ROOT/record['mutant']['path']));audit.append(record)
        print(f'Absolute RBP allele summaries {ordinal+1}/103 verified: {task}',flush=True)
    a=np.column_stack(reference);b=np.column_stack(mutant)
    result={'reference':array_file('data/interim/mechanism_v2/rbp_reference_absolute.npy',a),
        'mutant':array_file('data/interim/mechanism_v2/rbp_mutant_absolute.npy',b),
        'task_order':tasks,'shards':audit,'max_delta_reconstruction_error':float(np.max(np.abs(b-a-signed))),
        'code_sha256':sha256(Path(__file__)),'source_signature_manifest_sha256':sha256(signature_path),
        'interpretation':'Absolute output-profile pooling at each intervention edit window; comparators only, not primary deltas'}
    write_json('results/mechanism_v2/features/rbp_absolute_allele_manifest.json',result)
    bert=ROOT/'data/interim/v4_phaseB_3utrbert_full_features.npy'
    if sha256(bert)!='51912767e74dc19a06dadf6bab9f3022f11939f1cc537f024af148cc18f948d9':
        raise ValueError('BERT source array hash mismatch')
    values=np.load(bert,mmap_mode='r')
    record=array_file('data/interim/mechanism_v2/bert_pooled_allele_delta.npy',np.asarray(values[:,128:256]-values[:,:128]))
    record.update({'source_sha256':sha256(bert),'code_sha256':sha256(Path(__file__)),
        'definition':'fixed-projection CLS+mean mutant embedding minus reference embedding; distinct from contextual delta',
        'absolute_blocks':{'reference':[0,128],'mutant':[128,256]},'primary_or_comparator':'prospective model grid must explicitly identify this block'})
    write_json('results/mechanism_v2/features/bert_pooled_allele_delta_manifest.json',record)
    return result
