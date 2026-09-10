"""Outcome-independent negative-control kernels; no localization fitting."""
from __future__ import annotations
import hashlib
import json
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from .io import ROOT,load_development,sha256,write_json,canonical_json
from .primitives import bijective_map,edit_band
from .external_stability import sequence_features
from .features import array_file


def intervention_permutation(rows,partition,strata=(),seed=20260909,cross_component=False):
    """Return donor feature_row and eligibility for every repeated candidate row.

    The permutation itself acts on unique interventions. Context replication is
    restored only afterwards. A repeated intervention crossing partitions fails.
    """
    if len(partition)!=len(rows):raise ValueError('Partition length mismatch')
    work=rows[['feature_row','dataset','biological_unit','component','edit_cost']].copy()
    work['partition']=np.asarray(partition)
    work['edit_band']=edit_band(work.edit_cost.to_numpy())
    work['native_length']=rows.parent_sequence.str.len().to_numpy()
    fields=['partition','dataset','biological_unit','component','edit_band','native_length']
    if (work.groupby('feature_row')[fields].nunique(dropna=False)>1).any().any():
        raise ValueError('Repeated intervention has inconsistent partition or metadata')
    unique=work.sort_values('feature_row').drop_duplicates('feature_row').reset_index(drop=True)
    unique['intervention_id']=unique.feature_row.astype(str)
    donor,eligible,audit=bijective_map(unique,partition='partition',strata=strata,
        unit='component' if cross_component else None,seed=seed)
    donor_ids=unique.feature_row.to_numpy()[donor]
    remap=dict(zip(unique.feature_row,donor_ids));valid=dict(zip(unique.feature_row,eligible))
    return rows.feature_row.map(remap).to_numpy(int),rows.feature_row.map(valid).to_numpy(bool),{
        'unique_interventions':len(unique),'eligible_interventions':int(eligible.sum()),
        'fixed_interventions':int((donor==np.arange(len(unique))).sum()),'seed':seed,
        'strata':list(strata),'cross_component':cross_component,'stratum_audit':audit}


def permute_rbp_identities(values,intervention_ids,seed=20260909):
    """Independent whole-channel permutations; identical intervention copies agree.

    A single universal column permutation is not a meaningful retrained linear
    null. Here the same four summary roles travel together within each channel.
    """
    x=np.asarray(values)
    if x.ndim!=3 or x.shape[2]!=4 or len(intervention_ids)!=len(x):raise ValueError('Invalid channel shape')
    if not np.isfinite(x).all():raise ValueError('Non-finite RBP input')
    output=np.empty_like(x);fixed=0
    for i,identity in enumerate(intervention_ids):
        digest=hashlib.sha256(f'{seed}:rbp_identity:{identity}'.encode()).digest()
        permutation=np.random.default_rng(int.from_bytes(digest[:8],'little')).permutation(x.shape[1])
        output[i]=x[i,permutation];fixed+=int((permutation==np.arange(x.shape[1])).sum())
    return output,{'seed':seed,'fixed_channel_entries':fixed,'total_channel_entries':len(x)*x.shape[1],
        'null':'intervention-specific whole-channel identity permutation, shared across repeated contexts'}


def random_projection(input_dimensions=340,output_dimensions=540,seed=20260909):
    if min(input_dimensions,output_dimensions)<1:raise ValueError('Positive dimensions required')
    return np.random.default_rng(seed).normal(0,1/np.sqrt(input_dimensions),
        size=(input_dimensions,output_dimensions)).astype(np.float64)


def random_sequence_delta(reference,mutant,projection):
    matrix=np.asarray(projection,float)
    if matrix.ndim!=2 or matrix.shape[0]!=340:raise ValueError('Kmer projection must have 340 input channels')
    return (sequence_features(mutant)-sequence_features(reference))@matrix


def build_random_sequence_null():
    rows=load_development('results/v4_phaseB/model_interventions.csv.gz')
    sequences=sorted(set(rows.parent_sequence)|set(rows.mutant_sequence))
    counts=np.vstack([sequence_features(s) for s in sequences])
    lookup={s:i for i,s in enumerate(sequences)}
    reference=rows.parent_sequence.map(lookup).to_numpy(int);mutant=rows.mutant_sequence.map(lookup).to_numpy(int)
    projection=random_projection();result=np.empty((len(rows),540),np.float32)
    with threadpool_limits(limits=2):
        for start in range(0,len(rows),512):
            stop=min(len(rows),start+512)
            result[start:stop]=(counts[mutant[start:stop]]-counts[reference[start:stop]])@projection
    projection_record=array_file('data/interim/mechanism_v2/random_kmer_projection.npy',projection)
    record=array_file('data/interim/mechanism_v2/random_kmer_delta.npy',result)
    record.update({'code_sha256':sha256(ROOT/'src/mechanism_v2/control_kernels.py'),
        'kmer_code_sha256':sha256(ROOT/'src/mechanism_v2/external_stability.py'),
        'projection':projection_record,'seed':20260909,'input_dimensions':340,'output_dimensions':540,
        'configuration':'1-4mer counts per 100 nt, fixed Gaussian N(0,1/340) projection; mutant minus reference',
        'intervention_sha256':sha256(ROOT/'results/v4_phaseB/model_interventions.csv.gz'),
        'learned_from_localization':False,'maximum_information_rank':340,
        'interpretation':'matched-dimensional random sequence-feature null for M1, not an independent pretrained encoder'})
    write_json('results/mechanism_v2/features/random_kmer_delta_manifest.json',record)
    print(f'Random sequence null complete: {result.shape}; no outcomes used',flush=True)


if __name__=='__main__':build_random_sequence_null()
