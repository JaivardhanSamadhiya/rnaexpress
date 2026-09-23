"""Conservative reference-assisted admission after failed ungapped assembly QC."""
from .shukla_sequence_recovery import DATA, OUT, ROOT, rc, prefix_records, identifiers
from .common import sha256, write_json, write_new
import collections,csv,io,json


def fasta(path):
    result={};name=None
    for line in path.read_text().splitlines():
        if line.startswith('>'):
            name=line[1:].split()[0]
            if name in result:raise ValueError('Duplicate reference')
            result[name]=''
        elif line.strip():result[name]+=line.strip().upper()
    if any(set(s)-set('ACGTN') for s in result.values()):raise ValueError('Invalid reference alphabet')
    return result


def reference_candidate(sequence,length):
    if len(sequence)==length:return sequence,'exact_metadata_length'
    if len(sequence)>length and set(sequence[length:])=={'A'}:
        return sequence[:length],'terminal_polyA_only_trim_to_metadata_length'
    return None,'reference_length_not_resolved'


def run():
    references=fasta(DATA/'shukla2018_refseq_v1.fasta')
    meta=list(csv.DictReader((DATA/'shukla2018_oligoMeta.tsv').open(),delimiter='\t'))
    ids=identifiers();parts=[s.rsplit('_',2) for s in ids]
    multiplicity=collections.Counter(p[2] for p in parts)
    mapping={p[2]:(i,p) for i,p in zip(ids,parts) if multiplicity[p[2]]==1}
    candidates={};genes={}
    for m in meta:
        accession=m['name2'];raw=references.get(accession+'.1')
        if raw is None:
            genes[accession]={'status':'no_version1_reference','name':m['name1']};continue
        sequence,method=reference_candidate(raw,int(m['seqLen']))
        genes[accession]={'status':method,'name':m['name1'],'metadata_length':int(m['seqLen']),
                          'reference_length':len(raw)}
        if sequence is None:continue
        for identifier,p in zip(ids,parts):
            if p[0]!=accession or multiplicity[p[2]]!=1:continue
            tile=int(p[1]);start=tile*int(m['window'])
            # The original terminal-tile design is unresolved. Never guess it.
            if tile>=int(m['numOfOligos'])-1:continue
            insert=sequence[start:start+110]
            if len(insert)!=110 or set(insert)-set('ACGT'):continue
            candidates[identifier]={'id':identifier,'accession':accession,'gene':m['name1'],
                'tile':tile,'start_zero_based':start,'sequence':insert,
                'reference_accession':accession+'.1','reference_method':method,
                'barcode':p[2],'qc_quality_reads':0,'qc_exact_suffix90':0}
    records=0
    for s,q in prefix_records((DATA/'SRR5528987.first16MiB.gz').read_bytes()):
        records+=1
        if len(s)!=100 or min(map(ord,q[:10]))<63 or min(map(ord,q[10:]))<53:continue
        mapped=mapping.get(rc(s[:10]))
        if mapped is None or mapped[0] not in candidates:continue
        row=candidates[mapped[0]];row['qc_quality_reads']+=1
        row['qc_exact_suffix90']+=int(rc(s[10:])==row['sequence'][20:])
    admitted=[]
    for row in candidates.values():
        # These fixed QC thresholds use total-RNA sequence identity only.
        if row['qc_exact_suffix90']>=5 and row['qc_exact_suffix90']>=.5*row['qc_quality_reads']:
            admitted.append(row)
    if not admitted:raise ValueError('No admitted sequences')
    for accession,g in genes.items():
        cs=[r for r in candidates.values() if r['accession']==accession]
        ars=[r for r in admitted if r['accession']==accession]
        g.update(candidate_tiles=len(cs),admitted_tiles=len(ars),
                 exact_suffix90_reads=sum(r['qc_exact_suffix90'] for r in cs),
                 quality_reads=sum(r['qc_quality_reads'] for r in cs))
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(admitted[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(admitted)
    write_new(OUT/'shukla2018_reference_admitted_sequences.csv',stream.getvalue().encode())
    result={'metadata_genes':len(meta),'candidate_genes':sum(g['candidate_tiles']>0 for g in genes.values()),
            'admitted_tiles':len(admitted),'admitted_genes':len(set(r['accession'] for r in admitted)),
            'genes_with_at_least_20_admitted_tiles':sum(g['admitted_tiles']>=20 for g in genes.values()),
            'genes':genes,'complete_prefix_reads':records,'numeric_localization_outcomes_read':False,
            'admission_rule':'RefSeq v1 length exact, or only trailing As removed to metadata length. Nonterminal unique barcode. At least five Q20 insert/Q30 barcode reads exactly match last90, comprising >=50% of such reads.',
            'limitations':['First20 bases reference-derived, not directly verified on each barcode.',
               'Selection favors constructs sufficiently represented in one total-RNA prefix.',
               'Read counts are QC support, not independent molecules or biological replicates.',
               'Published outcome counts may include synthesis/sequence variants sharing a barcode.',
               'Not all original genes admitted. Original full oligo map remains unavailable.'],
            'files':{str(p.relative_to(ROOT)).replace('\\','/'):sha256(p) for p in
                [DATA/'shukla2018_refseq_v1.fasta',DATA/'shukla2018_oligoMeta.tsv',
                 DATA/'shukla2018_counts.tsv.gz',DATA/'SRR5528987.first16MiB.gz']},
            'code_sha256':sha256(__file__)}
    write_json(OUT/'shukla2018_reference_admission.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':run()
