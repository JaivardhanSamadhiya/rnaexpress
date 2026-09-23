"""Metadata-only paired DNA QC; concatenated, possibly truncated gzip prefixes."""
from .common import ROOT, sha256, write_json, write_new
from collections import Counter
import zlib

LEFT = 'GCATGGACGAGCTGTACAAGTAA'
RIGHT = 'TCTGTGCCTTCTAGTTGCCAG'


def decode_prefix(payload):
    blocks = []
    members = 0
    complete = False
    while payload:
        decoder = zlib.decompressobj(31)
        blocks.append(decoder.decompress(payload))
        members += 1
        complete = decoder.eof
        if not complete:
            break
        payload = decoder.unused_data
    return b''.join(blocks), members, complete


def records(payload):
    decoded, members, complete = decode_prefix(payload)
    lines = decoded.split(b'\n')
    result = []
    for i in range(0, ((len(lines)-1)//4)*4, 4):
        header, seq, plus, qual = [x.decode('ascii').rstrip('\r') for x in lines[i:i+4]]
        if not header.startswith('@') or not plus.startswith('+') or len(seq) != len(qual):
            raise ValueError('Invalid complete FASTQ record')
        result.append((header.split()[0], seq, qual))
    return result, members, complete


def insert(seq, qual, reverse=False):
    if reverse:
        seq = seq.translate(str.maketrans('ACGTN', 'TGCAN'))[::-1]
        qual = qual[::-1]
    a = seq.find(LEFT)
    if a < 0:
        return None
    a += len(LEFT)
    b = seq.find(RIGHT, a)
    if b < 0:
        return None
    value = seq[a:b]
    if len(value) != 45 or set(value)-set('ACGT') or min(map(ord, qual[a:b])) < 63:
        return None
    return value


def run():
    data = ROOT/'data/external/research_20260921'
    paths = [data/f'HRR1883397_{mate}.first2MiB.gz' for mate in ['f1','r2']]
    decoded = [records(p.read_bytes()) for p in paths]
    counts = Counter()
    discordant = both = 0
    for first, second in zip(decoded[0][0], decoded[1][0]):
        if first[0] != second[0]:
            raise ValueError('Mates not synchronized')
        a = insert(first[1], first[2])
        b = insert(second[1], second[2], True)
        if a is not None and b is not None:
            both += 1
            if a == b:
                counts[a] += 1
            else:
                discordant += 1
    result = {
        'scope': 'DNA sequence QC only; no localization outcomes accessed.',
        'run': 'HRR1883397',
        'source_files': {p.name:sha256(p) for p in paths},
        'complete_records_by_mate': [len(x[0]) for x in decoded],
        'gzip_members_by_mate': [x[1] for x in decoded],
        'last_gzip_member_complete': [x[2] for x in decoded],
        'synchronized_pairs': min(len(x[0]) for x in decoded),
        'both_mates_45nt_Q30_with_exact_anchors': both,
        'discordant_high_quality_pairs': discordant,
        'concordant_pairs': sum(counts.values()),
        'unique_concordant_inserts': len(counts),
        'unique_inserts_with_at_least_5_pairs': sum(v >= 5 for v in counts.values()),
        'full_archive_md5_verified': False,
        'limitations': ['Partial DNA run only; sequence counts are exploratory QC.',
            'R1-R4 biological independence and original versus revised RT method unresolved.',
            'No endpoint experiment admitted or independent novelty established.'],
        'code_sha256': sha256(__file__)}
    out = ROOT/'results/research_20260921'
    write_new(out/'seers_dna_prefix_inserts.tsv', ('sequence\tconcordant_Q30_pairs\n'+''.join(f'{s}\t{n}\n' for s,n in sorted(counts.items()))).encode())
    write_json(out/'seers_dna_prefix_qc.json', result)
    print(result)


if __name__ == '__main__':
    run()
