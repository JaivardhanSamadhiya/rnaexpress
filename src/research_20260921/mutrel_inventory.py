"""Inspect mutation identifiers only; compartment counts stay unexamined."""
from .common import ROOT,sha256,write_new,write_json
import tarfile,gzip,io,json,re
from collections import Counter,defaultdict

def run():
    p=ROOT/'data/external/research_20260921/mutrel_processed.tar'
    if sha256(p)!='e471289500a09a80b9a85c161d7365a7cc92b7de330dfcd7b308708d7775a721':
        raise ValueError('Source archive changed')
    with tarfile.open(p) as archive:
        members=archive.getmembers()
        if len(members)!=1 or members[0].name!='GSM2861600_mutRSLP_reads_count.txt.gz':
            raise ValueError('Unexpected processed archive')
        with io.TextIOWrapper(gzip.GzipFile(fileobj=archive.extractfile(members[0])),encoding='utf-8') as stream:
            header=stream.readline().rstrip().split('\t')
            if header!=['Name','site','mutation','cell_count','cyto_count','nuc_count','chr_count']:
                raise ValueError('Unexpected schema')
            metadata=[line.rstrip('\n').split('\t')[:3] for line in stream]
    bases=defaultdict(set); mutations=Counter(); substitutions=0;deletions=0
    for name,site,mutation in metadata:
        if not mutation: continue
        bases[int(site)].add(mutation[0]); mutations[mutation]+=1
        substitutions+=bool(re.fullmatch('[ACGT]>[ACGT]',mutation))
        deletions+=bool(re.fullmatch(r'[ACGT]-\.',mutation))
    result={'rows':len(metadata),'substitution_entries':substitutions,'deletion_entries':deletions,
            'WT_entries':sum(not r[2] for r in metadata),'sites':len(bases),
            'site_range':[min(bases),max(bases)],'conflicting_reference_bases':{str(k):sorted(v) for k,v in bases.items() if len(v)>1},
            'sequence_available_in_table':False,'replicate_specific_columns':False,
            'numeric_compartment_values_read':False,'source_sha256':sha256(p),
            'source':'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE107131',
            'admission':'Not yet admitted for intervention scoring: resolve full WT sequence, strand/coordinate convention, mutation co-occurrence and normalization from primary methods/raw reads. One NXF1 element cannot support broad gene generalization.'}
    out=ROOT/'results/research_20260921'
    write_new(out/'mutrel_sequence_metadata.tsv',('Name\tsite\tmutation\n'+'\n'.join('\t'.join(r) for r in metadata)+'\n').encode())
    write_json(out/'mutrel_inventory.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':run()
