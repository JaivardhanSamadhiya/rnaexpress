"""Recover tiled insert sequence from public total-RNA reads, without scoring outcomes.

The first 20 insert bases are not sequenced. They are inferred from overlapping
tiles, not claimed to be directly observed on that construct. Ambiguous barcodes,
terminal tiles, unsupported bases and disagreeing tile consensuses are excluded.
"""
from .common import ROOT, sha256, write_json, write_new
import collections, csv, gzip, io, json, zlib
import numpy as np

DATA = ROOT/'data/external/research_20260921'
OUT = ROOT/'results/research_20260921'
HEADER = ['Transcript']+[f'Nuclei{i}' for i in range(1,7)]+[f'Total{i}' for i in range(1,7)]


def rc(s):
    return s.translate(str.maketrans('ACGTN','TGCAN'))[::-1]


def prefix_records(payload):
    # A partial gzip member may end in the middle of any FASTQ line. Only
    # newline-terminated lines and complete four-line records are admitted.
    lines=zlib.decompressobj(31).decompress(payload).split(b'\n')[:-1]
    for i in range(0,len(lines)-3,4):
        h,s,p,q=lines[i:i+4]
        if not h.startswith(b'@') or not p.startswith(b'+') or len(s)!=len(q):
            raise ValueError('Malformed complete FASTQ record')
        yield s.decode('ascii'),q.decode('ascii')


def identifiers():
    with gzip.open(DATA/'shukla2018_counts.tsv.gz','rt') as stream:
        if stream.readline().rstrip().split('\t')!=HEADER:
            raise ValueError('Unexpected count schema')
        # Numeric fields are never converted, returned, logged or used here.
        ids=[line.split('\t',1)[0] for line in stream]
    if len(ids)!=11969 or len(ids)!=len(set(ids)):
        raise ValueError('Unexpected identifiers')
    return ids


def consensus(counts, minimum=5, fraction=.95):
    total=counts.sum(axis=-1);best=counts.max(axis=-1)
    good=(total>=minimum)&(best>=fraction*total)
    calls=np.full(total.shape,-1,dtype=np.int8)
    calls[good]=counts.argmax(axis=-1)[good]
    return calls


def assemble(calls, placements, length):
    """A coordinate is valid only if all confident contributing tiles agree."""
    supports=np.zeros((length,4),dtype=np.uint16)
    for index,start in placements:
        c=calls[index];valid=np.flatnonzero(c>=0)
        supports[start+20+valid,c[valid]]+=1
    known=(supports>0).sum(axis=1)
    sequence=np.full(length,-1,dtype=np.int8)
    accepted=known==1
    sequence[accepted]=supports[accepted].argmax(axis=1)
    return sequence, int((known>1).sum())


def run():
    names=['shukla2018_counts.tsv.gz','shukla2018_oligoMeta.tsv',
           'shukla2018_testRegions.fa','SRR5528987.first16MiB.gz']
    for name in names:
        receipt=json.loads((DATA/(name+'.receipt.json')).read_text())
        if sha256(DATA/name)!=receipt['sha256']:raise ValueError(('Changed input',name))
    ids=identifiers();parts=[s.rsplit('_',2) for s in ids]
    barcount=collections.Counter(p[2] for p in parts)
    barcode_to_index={p[2]:i for i,p in enumerate(parts) if barcount[p[2]]==1}
    meta={r['name2']:r for r in csv.DictReader((DATA/'shukla2018_oligoMeta.tsv').open(),delimiter='\t')}
    if set(p[0] for p in parts)!=set(meta):raise ValueError('Metadata does not cover identifiers')
    counts=np.zeros((len(ids),90,4),dtype=np.uint32)
    lookup=np.full(256,-1,dtype=np.int8)
    for i,b in enumerate(b'ACGT'):lookup[b]=i
    records=accepted=0
    for s,q in prefix_records((DATA/'SRR5528987.first16MiB.gz').read_bytes()):
        records+=1
        if len(s)!=100:raise ValueError('Unexpected read length')
        if min(map(ord,q[:10]))<63:continue
        index=barcode_to_index.get(rc(s[:10]))
        if index is None:continue
        accepted+=1
        bases=lookup[np.frombuffer(rc(s[10:]).encode(),dtype=np.uint8)]
        quality=np.frombuffer(q[10:][::-1].encode(),dtype=np.uint8)
        good=np.flatnonzero((quality>=63)&(bases>=0))
        counts[index,good,bases[good]]+=1
    calls=consensus(counts)
    tile_output=io.StringIO(newline='')
    writer=csv.writer(tile_output,lineterminator='\n');writer.writerow(['id','consensus_90nt','Q30_consensus_bases'])
    for identifier,call in zip(ids,calls):
        writer.writerow([identifier,''.join('ACGT'[v] if v>=0 else 'N' for v in call),int((call>=0).sum())])
    write_new(OUT/'shukla2018_tile90_consensus.csv',tile_output.getvalue().encode())
    # Validate the coordinate/orientation inference against author-provided
    # reference sequences. Do not execute downloaded Python source.
    references={};name=None
    for line in (DATA/'shukla2018_testRegions.fa').read_text().splitlines():
        if line.startswith('>'):name=line[1:];references[name]=''
        else:references[name]+=line.strip().upper()
    reference_alias={'NR_001564':'XIST','NR_026975':'FIRRE','NR_024031':'DANCR'}
    rows=[];genes={};reference_checks={}
    alphabet=np.array(list('ACGT'))
    for gene,m in meta.items():
        length,step,n=int(m['seqLen']),int(m['window']),int(m['numOfOligos'])
        candidates=[(i,int(p[1])*step) for i,p in enumerate(parts)
                    if p[0]==gene and int(p[1])<n-1 and barcount[p[2]]==1]
        assembled,conflicts=assemble(calls,candidates,length)
        if gene in reference_alias:
            reference=references[reference_alias[gene]]
            idx=np.flatnonzero(assembled>=0)
            if len(reference)!=length:
                reference_checks[gene]={'status':'demo_reference_length_mismatch_not_used',
                                       'demo_length':len(reference),'metadata_length':length}
            else:
                mismatches=sum(reference[i]!=alphabet[assembled[i]] for i in idx)
                reference_checks[gene]={'status':'compared','positions_compared':len(idx),
                                       'mismatches':mismatches,'length':length}
        before=len(rows)
        for i,start in candidates:
            segment=assembled[start:start+110]
            if len(segment)!=110 or np.any(segment<0) or np.any(calls[i]<0):continue
            if not np.array_equal(segment[20:],calls[i]):raise ValueError('Own-tile inconsistency')
            sequence=''.join(alphabet[segment])
            rows.append({'id':ids[i],'accession':gene,'gene':m['name1'],'tile':int(parts[i][1]),
                         'start_zero_based':start,'sequence':sequence,
                         'first_20_bases':'inferred_from_overlapping_tiles',
                         'directly_observed_Q30_consensus_bases':90})
        genes[gene]={'name':m['name1'],'metadata_tiles':n,'recovered_tiles':len(rows)-before,
                     'conflicting_transcript_positions_excluded':conflicts}
    check=reference_checks['NR_026975']
    if not (check['status']=='compared' and check['positions_compared']>=.8*check['length']
            and check['mismatches']==0):
        print(json.dumps({'reference_checks':reference_checks,'genes':genes},indent=2),flush=True)
        raise ValueError(('Coordinate/reference validation failed',reference_checks))
    out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    write_new(OUT/'shukla2018_recovered_sequences.csv',out.getvalue().encode())
    summary={'raw_run':'SRR5528987','sample':'HeLa_BR_1_TR_1_Total',
             'complete_prefix_records':records,'unique_barcode_Q30_records':accepted,
             'identifier_rows':len(ids),'nonunique_barcodes_excluded':sum(v>1 for v in barcount.values()),
             'recovered_tiles':len(rows),'recovered_genes':sum(v['recovered_tiles']>0 for v in genes.values()),
             'genes':genes,'author_reference_checks':reference_checks,
             'numeric_localization_counts_read':False,'full_raw_file_md5_verified':False,
             'limitations':['Convenience prefix, not unbiased library coverage.',
                 'PCR duplicates are not independent observations.',
                 'Only last 90 of 110 insert bases directly observed; first 20 inferred from tiling design.',
                 'No indel correction; conflicting positions, terminal tiles and ambiguous barcodes excluded.',
                 'Reference agreement checks FIRRE only. Author demo DANCR/XIST lengths differ from experimental metadata and are not used.'],
             'files':{str((DATA/n).relative_to(ROOT)).replace('\\','/'):sha256(DATA/n) for n in names},
             'code_sha256':sha256(__file__)}
    write_json(OUT/'shukla2018_sequence_recovery.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['genes','files']},indent=2),flush=True)


if __name__=='__main__':run()
