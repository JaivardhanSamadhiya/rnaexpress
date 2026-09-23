"""Expand DNA-only coverage before deciding whether an outcome pilot is feasible."""
from .common import ROOT,sha256,write_json,write_new
from .seers_dna_qc import records,insert
from .mutrel_read_qc import prefix
from collections import Counter
from concurrent.futures import ThreadPoolExecutor


def run():
    def fetch(mate):
        name=f'HRR1883397_{mate}.first16MiB.gz'
        url=f'https://download.cncb.ac.cn/gsa-human/HRA008408/HRR1883397/HRR1883397_{mate}.fq.gz'
        return records(prefix(url,name,16*1024**2)),name
    with ThreadPoolExecutor(max_workers=2) as pool:
        inputs=list(pool.map(fetch,['f1','r2']))
    counts=Counter();discordant=both=0
    for first,second in zip(inputs[0][0][0],inputs[1][0][0]):
        if first[0]!=second[0]:raise ValueError('Mates not synchronized')
        a=insert(first[1],first[2]);b=insert(second[1],second[2],True)
        if a is not None and b is not None:
            both+=1
            if a==b:counts[a]+=1
            else:discordant+=1
    groups=Counter(tuple(s.count(b) for b in 'ACGT') for s,n in counts.items() if n>=5)
    out=ROOT/'results/research_20260921';data=ROOT/'data/external/research_20260921'
    result={'scope':'Exploratory DNA-only 16 MiB prefixes, expanded after initial 2 MiB QC; no RNA outcomes.',
        'complete_records_by_mate':[len(x[0][0]) for x in inputs],
        'gzip_members_by_mate':[x[0][1] for x in inputs],
        'high_quality_pairs':both,'discordant_pairs':discordant,
        'concordant_pairs':sum(counts.values()),'unique_inserts':len(counts),
        'inserts_supported_by_at_least_5_pairs':sum(n>=5 for n in counts.values()),
        'exact_composition_groups_with_at_least_5_supported_inserts':sum(n>=5 for n in groups.values()),
        'supported_inserts_in_those_groups':sum(n for n in groups.values() if n>=5),
        'full_archive_MD5_verified':False,
        'source_sha256':{name:sha256(data/name) for _,name in inputs},
        'code_sha256':sha256(__file__),
        'decoder_sha256':sha256(ROOT/'src/research_20260921/seers_dna_qc.py')}
    write_new(out/'seers_dna_16MiB_inserts.tsv',('sequence\tconcordant_Q30_pairs\n'+''.join(f'{s}\t{n}\n' for s,n in sorted(counts.items()))).encode())
    write_json(out/'seers_dna_16MiB_qc.json',result)
    print(result,flush=True)


if __name__=='__main__':run()
