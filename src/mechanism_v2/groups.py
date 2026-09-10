"""Outcome-blind connected-component grouping, including shared derived sequences."""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd


def component_groups(rows, near_identity=None):
    units=sorted(rows.biological_unit.astype(str).unique())
    parents={u:u for u in units}
    def find(u):
        while parents[u]!=u:
            parents[u]=parents[parents[u]];u=parents[u]
        return u
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:
            parents[max(a,b)]=min(a,b)
    seen={}
    parent_sequences={}
    relevant=['biological_unit','parent_sequence','mutant_sequence','gene_id','gene_name']
    for row in rows[relevant].drop_duplicates().itertuples(index=False):
        unit=str(row.biological_unit)
        for seq in (row.parent_sequence,row.mutant_sequence):
            seq=str(seq).upper().replace('U','T')
            key='sequence:'+hashlib.sha256(seq.encode()).hexdigest()
            if key in seen:union(unit,seen[key])
            else:seen[key]=unit
        parent_sequences.setdefault(str(row.parent_sequence).upper().replace('U','T'),unit)
        for column,value in [('id',row.gene_id),('name',row.gene_name)]:
            if pd.isna(value) or str(value).strip().lower() in {
                '', 'none', 'nan', 'unknown', 'na', 'n/a', 'missing', 'not_available', '-', '.', 'null'
            }:
                continue
            key=f'gene_{column}:'+str(value).strip().lower()
            if key in seen:union(unit,seen[key])
            else:seen[key]=unit
    edges=[]
    if near_identity is not None:
        if not 0 < near_identity <= 1:raise ValueError('Identity must be in (0,1]')
        from rapidfuzz.distance import Levenshtein
        sequences=sorted(parent_sequences)
        for i,a in enumerate(sequences):
            for b in sequences[i+1:]:
                maxlen=max(len(a),len(b));cutoff=int((1-near_identity)*maxlen+1e-9)
                if abs(len(a)-len(b))>cutoff:continue
                distance=Levenshtein.distance(a,b,score_cutoff=cutoff)
                if distance<=cutoff:
                    union(parent_sequences[a],parent_sequences[b])
                    edges.append((hashlib.sha256(a.encode()).hexdigest(),hashlib.sha256(b.encode()).hexdigest(),distance))
    mapping={u:find(u) for u in units}
    components=rows.biological_unit.astype(str).map(mapping).to_numpy()
    return components, {'original_units':len(units),'components':len(set(mapping.values())),
        'unit_to_component':mapping,'near_parent_identity':near_identity,'near_parent_edges':edges,
        'near_definition':'1 - global Levenshtein distance / max length; parent sequences only',
        'exact_scope':'all reference and mutant sequences, plus available gene IDs/names'}


def assert_partition_disjoint(rows, partition, groups):
    test=pd.DataFrame({'group':groups,'partition':partition})
    if test.groupby('group').partition.nunique().max()>1:
        raise ValueError('Connected biological component crosses partitions')
    if rows.assign(_partition=partition).groupby('feature_row')._partition.nunique().max()>1:
        raise ValueError('Replicated intervention crosses partitions')
