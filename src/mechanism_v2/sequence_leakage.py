"""Exact thresholded all-allele near-duplicate audit using pigeonhole seeds.

No approximate nearest-neighbor retrieval: a sequence within t edits must retain
one of t+1 disjoint query blocks. Candidate pairs are verified by global native
Levenshtein similarity. This checks mutants too, unlike parent-only sensitivities.
"""
from __future__ import annotations
from collections import defaultdict
import math
import numpy as np
import pandas as pd
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
from .groups import component_groups,assert_partition_disjoint
from .splits import balanced_group_folds
from .io import load_development,write_json,ROOT,sha256
from .forensics import csv


def exact_near_components(sequences,initial_groups,threshold=0.95,progress=False):
    if not 0<threshold<=1 or len(sequences)!=len(initial_groups):raise ValueError('Invalid sequence audit inputs')
    parents={str(g):str(g) for g in initial_groups}
    def find(g):
        g=str(g)
        while parents[g]!=g:parents[g]=parents[parents[g]];g=parents[g]
        return g
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parents[max(a,b)]=min(a,b)
    lookup={}
    for seq,group in zip(sequences,initial_groups):
        if not seq or set(seq)-set('ACGT'):raise ValueError('Invalid sequence')
        if seq in lookup:union(lookup[seq],group)
        else:lookup[seq]=str(group)
    unique=sorted(lookup);lengths=np.array(list(map(len,unique)))
    seeds=defaultdict(set);seed_lengths=set()
    for idx,seq in enumerate(unique):
        # Use the largest possible eligible partner length, not just len(seq),
        # to retain the pigeonhole guarantee at an indel/rounding boundary.
        maximum_length=int(math.floor(len(seq)/threshold+1e-9))
        edits=int(math.floor((1-threshold)*maximum_length+1e-9))
        blocks=min(len(seq),edits+1)
        boundaries=[i*len(seq)//blocks for i in range(blocks+1)]
        for a,b in zip(boundaries[:-1],boundaries[1:]):
            seeds[seq[a:b]].add(idx);seed_lengths.add(b-a)
    edges=[];candidate_comparisons=0
    for i,seq in enumerate(unique):
        candidates=set()
        for size in seed_lengths:
            for start in range(len(seq)-size+1):candidates.update(seeds.get(seq[start:start+size],()))
        candidates={j for j in candidates if j<i and
            abs(len(seq)-lengths[j])<=(1-threshold)*max(len(seq),lengths[j])+1e-9}
        while True:
            choices={j:unique[j] for j in sorted(candidates) if find(lookup[unique[j]])!=find(lookup[seq])}
            if not choices:break
            candidate_comparisons+=len(choices)
            hit=process.extractOne(seq,choices,scorer=Levenshtein.normalized_similarity,score_cutoff=threshold-1e-12)
            if hit is None:break
            other,similarity,j=hit
            distance=Levenshtein.distance(seq,other)
            if distance>(1-threshold)*max(len(seq),len(other))+1e-9:raise AssertionError('Native similarity threshold mismatch')
            edges.append({'left_group':find(lookup[seq]),'right_group':find(lookup[other]),
                'left_sequence_index':i,'right_sequence_index':int(j),'distance':int(distance),'similarity':float(similarity)})
            union(lookup[seq],lookup[other])
        if progress and (i+1)%2048==0:
            print(f'All-allele near audit: {i+1}/{len(unique)} sequences, {len(edges)} cross-component edges',flush=True)
    mapping={g:find(g) for g in parents}
    return np.array([mapping[str(g)] for g in initial_groups]),{'threshold':threshold,'unique_sequences':len(unique),
        'initial_components':len(set(map(str,initial_groups))),'final_components':len(set(mapping.values())),
        'component_mapping':mapping,'cross_component_edges':edges,'candidate_comparisons':candidate_comparisons,
        'retrieval':'exact pigeonhole t+1 disjoint blocks with indel-aware maximum eligible length',
        'verification':'global Levenshtein normalized by maximum length','sequence_order':'lexically sorted unique ACGT strings'}


def audit_all_alleles():
    rows=load_development();groups,old=component_groups(rows)
    allele_rows=pd.concat([pd.DataFrame({'sequence':rows.parent_sequence,'component':groups}),
                          pd.DataFrame({'sequence':rows.mutant_sequence,'component':groups})]).drop_duplicates()
    _,audit=exact_near_components(allele_rows.sequence.tolist(),allele_rows.component.tolist(),progress=True)
    final=np.array([audit['component_mapping'][str(g)] for g in groups])
    folds=balanced_group_folds(rows,final)
    result=rows[['dataset','biological_unit','decision_set_id','candidate_id','feature_row']].copy()
    result['component']=final;result['outer_fold']=folds
    inner={}
    for fold in range(5):
        mask=folds!=fold
        assignments=balanced_group_folds(rows.loc[mask],final[mask],3,20260910+fold)
        mapping=pd.DataFrame({'component':final[mask],'fold':assignments}).drop_duplicates()
        inner[str(fold)]={r.component:int(r.fold) for r in mapping.itertuples(index=False)}
    path='results/mechanism_v2/splits/all_alleles95.csv'
    csv(path,result)
    write_json('results/mechanism_v2/manifests/splits_all_alleles95.json',
        {'audit':audit,'outer':path,'outer_sha256':sha256(ROOT/path),'inner_component_folds':inner,
         'outcomes_used_for_assignment':False,'prior_parent_only_splits':'preserved development inventories, superseded before any localization model evaluation'})
    print(f'All-allele audit complete: {audit["final_components"]} independent components',flush=True)
