"""Exact, outcome-blind mapping of recovered amplicons to external variant IDs.

Coordinates alone do not establish genome build. Pilot both candidate builds;
require transcript-oriented allele, both observed sequences and published GC
fractions to agree. Never use half-life or significance to resolve an identity.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import hashlib
import json
import time
import threading
import numpy as np
import pandas as pd
from .io import ROOT,sha256,write_json
from .resources import fetch
from .stability_resources import validated_resource
from .stability_recovery import reverse_complement,FORWARD,REVERSE
from .forensics import csv

IDENTITY_COLUMNS=['Mutant','GeneSymbol','Chromosome','Start','Stop','UTR_Group',
    'ReferenceAllele','AlternateAllele','GCcontent_WT','GCcontent_mt']


def variant_inventory():
    # Read the hash-verified raw supplement anew; the earlier extracted table is
    # convenient for inspection, but does not become an unverified model input.
    from openpyxl import load_workbook
    import io
    path,receipt=validated_resource('stability_supp1')
    book=load_workbook(io.BytesIO(path.read_bytes()),read_only=True,data_only=False)
    values=list(book['Sup_T2_metaTable'].values)
    table=pd.DataFrame(values[1:],columns=values[0])[IDENTITY_COLUMNS]
    table=table[table.UTR_Group.eq("3'UTR")].copy()
    table['strand']=table.Mutant.str.split('_').str[-3]
    if not set(table.strand)<=set('+-'):raise ValueError('Unknown external transcript strand')
    return table.sort_values('Mutant').reset_index(drop=True),receipt


def fetch_windows(limit=32,assemblies=('hg38','hg19')):
    table,_=variant_inventory()
    regions=table[['Chromosome','Start','Stop']].drop_duplicates()
    if limit is not None:
        # Evenly spaced genomic inventory, not the most significant variants.
        regions=regions.iloc[np.unique(np.linspace(0,len(regions)-1,min(limit,len(regions))).astype(int))]
    jobs=[(assembly,str(row.Chromosome),max(0,int(row.Start)-200),int(row.Stop)+200)
        for assembly in assemblies for row in regions.itertuples(index=False) if int(row.Stop)-int(row.Start)<=200]
    limiter=threading.Lock();next_time=[0.]
    def job(args):
        assembly,chrom,start,end=args
        if not chrom.startswith('chr') or end<=start:raise ValueError('Invalid genomic coordinates')
        with limiter:
            wait=max(0,next_time[0]-time.monotonic())
            if wait:time.sleep(wait)
            next_time[0]=time.monotonic()+0.3
        url=f'https://api.genome.ucsc.edu/getData/sequence?genome={assembly};chrom={chrom};start={start};end={end}'
        label=f'stability_reference_{assembly}_{chrom}_{start}_{end}'
        try:
            receipt=fetch(url,label)
            obj=json.loads((ROOT/receipt['path']).read_text())
            if (obj.get('genome'),obj.get('chrom'),obj.get('start'),obj.get('end'))!=args or len(obj.get('dna',''))!=end-start:
                raise ValueError('UCSC sequence response coordinate/length mismatch')
            return {'assembly':assembly,'chromosome':chrom,'start':start,'end':end,'receipt':receipt}
        except Exception as error:return {'assembly':assembly,'chromosome':chrom,'start':start,'end':end,'error':repr(error)}
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(job,jobs))
    key='all' if limit is None else str(limit)
    result={'selection':'Outcome-blind unique variant positions, evenly spaced for pilot',
        'requested_assemblies':list(assemblies),'records':results,'limit':limit}
    write_json(f'results/mechanism_v2/manifests/stability_reference_windows_{key}_{"_".join(assemblies)}.json',result)
    print(f'Reference windows: {sum("receipt" in r for r in results)}/{len(results)} verified',flush=True)
    return result


def sequence_index(sequences):
    index=defaultdict(list)
    for sequence in sorted(set(sequences)):
        if len(sequence)>=21:index[sequence[:21]].append(sequence)
    return index


def gc(sequence):
    return sum(sequence.count(base) for base in 'GC')/len(sequence)


def map_variant(row,genomic,start,index,supported):
    """Return all exact observed ref/mut matches; caller rejects ambiguity."""
    strand=row['strand'];gstart=int(row['Start']);gstop=int(row['Stop'])
    if not start<=gstart<=gstop<=start+len(genomic):return [],'outside_window'
    ref=str(row['ReferenceAllele']).replace('-','').upper()
    alt=str(row['AlternateAllele']).replace('-','').upper()
    if set(ref+alt)-set('ACGT'):return [],'ambiguous_allele'
    genomic=genomic.upper()
    if strand=='+':sequence=genomic;position=gstart-start
    else:sequence=reverse_complement(genomic);position=start+len(genomic)-gstop
    if sequence[position:position+len(ref)]!=ref:return [],'reference_allele_mismatch'
    matches=set()
    for offset in range(len(sequence)-20):
        for wt in index.get(sequence[offset:offset+21],[]):
            if not sequence.startswith(wt,offset):continue
            position_in_insert=position-offset
            if not 0<=position_in_insert<=len(wt)-len(ref):continue
            mutant=wt[:position_in_insert]+alt+wt[position_in_insert+len(ref):]
            if mutant not in supported:continue
            if abs(gc(FORWARD+wt+REVERSE)-float(row['GCcontent_WT']))>1e-8:continue
            if abs(gc(FORWARD+mutant+REVERSE)-float(row['GCcontent_mt']))>1e-8:continue
            matches.add((wt,mutant,position_in_insert))
    return sorted(matches),'matched' if matches else 'no_exact_observed_pair_with_matching_gc'


def map_library(pilot=True):
    discovery=json.loads((ROOT/'results/mechanism_v2/manifests/stability_sequence_discovery_full.json').read_text())
    path=ROOT/discovery['output']
    if sha256(path)!=discovery['output_sha256']:raise ValueError('Recovered library hash mismatch')
    library=pd.read_csv(path)
    supported=set(library.loc[library.passes_support_threshold,'variable_sequence'])
    index=sequence_index(supported)
    table,_=variant_inventory();records=[]
    manifest='stability_reference_windows_32_hg38_hg19.json' if pilot else 'stability_reference_windows_all_hg38.json'
    windows=json.loads((ROOT/'results/mechanism_v2/manifests'/manifest).read_text())
    for item in windows['records']:
        if 'receipt' not in item:continue
        receipt=item['receipt'];path=ROOT/receipt['path']
        if sha256(path)!=receipt['sha256']:raise ValueError('Reference sequence hash mismatch')
        obj=json.loads(path.read_text())
        candidates=table[table.Chromosome.eq(item['chromosome'])&table.Start.ge(item['start'])&table.Stop.le(item['end'])]
        for _,row in candidates.iterrows():
            matches,reason=map_variant(row,obj['dna'],item['start'],index,supported)
            record={'variant':row.Mutant,'gene':row.GeneSymbol,'assembly':item['assembly'],
                'window_sha256':receipt['sha256'],'match_count':len(matches),'reason':reason}
            if len(matches)==1:
                record.update({'reference_sequence':matches[0][0],'mutant_sequence':matches[0][1],
                    'position_in_reference_insert':matches[0][2]})
            records.append(record)
    frame=pd.DataFrame(records).drop_duplicates()
    name='pilot' if pilot else 'full'
    csv(f'results/mechanism_v2/stability/sequence_mapping_{name}.csv',frame)
    summary=frame.groupby(['assembly','reason']).variant.nunique().to_dict()
    print({str(k):int(v) for k,v in summary.items()},flush=True)
    return frame
