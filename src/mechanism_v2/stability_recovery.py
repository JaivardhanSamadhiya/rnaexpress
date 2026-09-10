"""Recover external library amplicons without consulting stability/localization outcomes.

Conservative discovery, NOT yet an allele-to-phenotype mapping. Only exact paired
read overlaps, complete published primers, and covered high-quality bases pass.
Read-pair support is not an estimate of independent biological replicates.
"""
from __future__ import annotations
from collections import Counter
import gzip
import hashlib
import itertools
import json
import numpy as np
import pandas as pd
from .io import ROOT, sha256, write_json
from .forensics import csv

FORWARD = 'GGACGAGCTGTACAAGTAAA'
REVERSE = 'GCGGCCGCGCAATAACTAGC'  # Written in transcript orientation in the paper.
CONFIG = {'minimum_exact_overlap':35,'minimum_covered_phred':20,
          'minimum_read_pair_support':10,'maximum_leading_random_bases':3,
          'minimum_variable_length':50,'maximum_variable_length':200,
          'primers_source':'https://elifesciences.org/articles/97682#s4'}


def reverse_complement(sequence):
    return sequence.translate(str.maketrans('ACGTN','TGCAN'))[::-1]


def fastq_records(stream):
    while True:
        name=stream.readline().rstrip('\r\n')
        if not name:return
        sequence=stream.readline().rstrip('\r\n').upper()
        plus=stream.readline().rstrip('\r\n')
        quality=stream.readline().rstrip('\r\n')
        if not name.startswith('@') or not plus.startswith('+') or len(sequence)!=len(quality):
            raise ValueError('Malformed external FASTQ record')
        if not sequence or set(sequence)-set('ACGTN'):
            raise ValueError('Invalid FASTQ sequence')
        yield name,sequence,quality


def merge_exact(sequence1,quality1,sequence2,quality2,minimum_overlap=35,minimum_phred=20):
    """Unique, exact overlap only; disagreements are rejected, never arbitrated.

    Read 2 is reverse-complemented. Consensus quality is the higher covered mate
    quality, not a posterior confidence. Overlap gaps/indels are unsupported.
    """
    if len(sequence1)!=len(quality1) or len(sequence2)!=len(quality2):
        raise ValueError('Sequence/quality lengths disagree')
    if minimum_overlap<1:raise ValueError('Positive overlap required')
    tail=reverse_complement(sequence2); qtail=quality2[::-1]
    if min(len(sequence1),len(tail))<minimum_overlap:return None,'short_read'
    matches=[]
    offset=sequence1.find(tail[:minimum_overlap])
    while offset>=0:
        overlap=min(len(sequence1)-offset,len(tail))
        if sequence1[offset:offset+overlap]==tail[:overlap]:
            merged=sequence1+tail[len(sequence1)-offset:]
            if 'N' not in merged:
                quality=[ord(c)-33 for c in quality1]
                for j,c in enumerate(qtail):
                    pos=offset+j; q=ord(c)-33
                    if pos<len(quality):quality[pos]=max(quality[pos],q)
                    else:quality.append(q)
                if min(quality)>=minimum_phred:matches.append((offset,merged))
        offset=sequence1.find(tail[:minimum_overlap],offset+1)
    if not matches:return None,'no_exact_high_quality_overlap'
    if len(matches)!=1:return None,'ambiguous_overlap'
    return matches[0][1],'merged'


def extract_insert(amplicon):
    first=amplicon.find(FORWARD)
    if first<0 or first>CONFIG['maximum_leading_random_bases']:
        return None,'forward_primer'
    start=first+len(FORWARD)
    stop=amplicon.rfind(REVERSE)
    if stop<start or stop+len(REVERSE)!=len(amplicon):
        return None,'reverse_primer'
    insert=amplicon[start:stop]
    if not CONFIG['minimum_variable_length']<=len(insert)<=CONFIG['maximum_variable_length']:
        return None,'variable_length'
    return insert,'accepted'


def discover_library(limit=None):
    inputs=[]
    for mate in [1,2]:
        manifest=ROOT/f'results/mechanism_v2/manifests/SRR22227655_{mate}.fastq.gz.json'
        record=json.loads(manifest.read_text())
        path=ROOT/record['path']
        if sha256(path)!=record['sha256']:raise ValueError('Raw stability read hash mismatch')
        inputs.append((path,record))
    counts=Counter(); reasons=Counter(); total=0
    with gzip.open(inputs[0][0],'rt',encoding='ascii') as a,gzip.open(inputs[1][0],'rt',encoding='ascii') as b:
        pairs=itertools.zip_longest(fastq_records(a),fastq_records(b))
        if limit is not None:pairs=itertools.islice(pairs,limit)
        for left,right in pairs:
            if left is None or right is None:raise ValueError('Mates have different record counts')
            if left[0].split()[0]!=right[0].split()[0]:raise ValueError('Mates are not name-aligned')
            total+=1
            sequence,reason=merge_exact(left[1],left[2],right[1],right[2],
                CONFIG['minimum_exact_overlap'],CONFIG['minimum_covered_phred'])
            if sequence is not None:
                sequence,reason=extract_insert(sequence)
                if sequence is not None:counts[sequence]+=1
            reasons[reason]+=1
            if total%250000==0:print(f'External sequence discovery: {total} pairs, {reasons["accepted"]} accepted',flush=True)
    library=pd.DataFrame([{'sequence_sha256':hashlib.sha256(s.encode()).hexdigest(),
        'variable_sequence':s,'length':len(s),'read_pair_support':count,
        'passes_support_threshold':count>=CONFIG['minimum_read_pair_support'],
        'gc_fraction':sum(s.count(c) for c in 'GC')/len(s),
        'ta_per_base':s.count('TA')/len(s)} for s,count in sorted(counts.items())])
    name='full' if limit is None else f'pilot_{limit}'
    dest=f'data/interim/mechanism_v2/stability_sequence_discovery_{name}.csv'
    csv(dest,library)
    result={'inputs':[x[1] for x in inputs],'configuration':CONFIG,'code_sha256':sha256(__file_path()),
        'total_pairs':total,'reasons':dict(reasons),'unique_variable_sequences':len(library),
        'supported_sequences':int(library.passes_support_threshold.sum()) if len(library) else 0,
        'supported_length_counts':library.loc[library.passes_support_threshold,'length'].value_counts().sort_index().to_dict() if len(library) else {},
        'output':dest,'output_sha256':sha256(ROOT/dest),
        'status':'Sequence discovery only; exact allele/variant identity unresolved; not model-admitted',
        'outcomes_used':False,'limit':limit}
    write_json(f'results/mechanism_v2/manifests/stability_sequence_discovery_{name}.json',result)
    print(json.dumps(result,indent=2),flush=True)
    return result


def __file_path():
    from pathlib import Path
    return Path(__file__)
