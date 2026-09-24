"""DNA-only feasibility audit of existing public reporter/barcode identities."""
from .common import ROOT, sha256, write_new, write_json
from .faraway_design import STARTS
import sys
sys.path.insert(1, str(ROOT/'data/interim/research_20260921/dna_runtime'))
from Bio.Align import PairwiseAligner
import Bio
import gzip, json
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
import openpyxl

DATA = ROOT/'data/external/research_20260921'
OUT = ROOT/'results/research_20260921'
US = 'ATTACGTCTCGATCGACAAC'
DS = 'GGATCCGCAGGCCTCTGCTA'
TRANSLATE = str.maketrans('ACGTN', 'TGCAN')


def reverse_complement(s): return s.translate(TRANSLATE)[::-1]


def barcode_record(s, q):
    hits = []
    for reverse, seq, qual in [(False, s, q), (True, reverse_complement(s), q[::-1])]:
        start = seq.find(US)
        while start >= 0:
            left = start+len(US)
            for size in range(17, 24):
                if seq[left+size:left+size+len(DS)] == DS:
                    barcode = seq[left:left+size]; quality = qual[left:left+size]
                    if set(barcode) <= set('ACGT') and len(quality) == size and min(map(ord, quality))-33 >= 10:
                        hits.append({'barcode': barcode, 'reverse': reverse, 'sequence': seq[:left], 'barcode_min_Q': min(map(ord, quality))-33})
            start = seq.find(US, start+1)
    # Reject repeated or contradictory occurrences, including concatemeric reads.
    return hits[0] if len(hits) == 1 else None


def references():
    w = openpyxl.load_workbook(DATA/'faraway2025_supptable_2.xlsx', read_only=True, data_only=True)
    fragments = {n: s.upper() for n, s in list(w['Ordered_fragments'].values)[1:] if isinstance(s, str)}; w.close()
    refs = {}; owners = defaultdict(set)
    for i in range(1, 9):
        for ga, tag in [(0, 'DeO'), (1, 'Opt')]:
            no = fragments[f'PPIG_{tag}_NoIn_{i}']
            for intron, token in [(0, 'NoIn'), (1, 'In')]:
                s = fragments[f'PPIG_{tag}_{token}_{i}']
                offset = 49 if i == 1 else 0
                size = STARTS[i]-STARTS[i-1]+len(s)-len(no)
                core = s[offset:offset+size]
                refs[(i, ga, intron)] = core
                for j in range(len(core)-14): owners[core[j:j+15]].add(i)
    # Exact anchors identify a region, not a genotype. Local alignment scores all
    # four published alternatives at that position inside the same read window.
    index = {word: next(iter(pos)) for word, pos in owners.items() if len(pos) == 1}
    return refs, index


def aligner():
    return PairwiseAligner(mode='local', match_score=2, mismatch_score=-3, open_gap_score=-5, extend_gap_score=-1)


def call_construct(seq, refs, index, alignment):
    anchors = defaultdict(list)
    for j in range(len(seq)-14):
        pos = index.get(seq[j:j+15])
        if pos is not None: anchors[pos].append(j)
    bits, spans, details = [], [], []
    for i in range(1, 9):
        locations = anchors.get(i, [])
        if len(locations) < 8: return None, 'insufficient_segment_anchors'
        left = max(0, min(locations)-50); right = min(len(seq), max(locations)+65)
        window = seq[left:right]
        if len(window) > 1200: return None, 'dispersed_segment_anchors'
        candidates = []
        for ga in [0, 1]:
            for intron in [0, 1]:
                ref = refs[(i, ga, intron)]
                a = alignment.align(window, ref)[0]
                coords = a.coordinates
                coverage = (coords[1, -1]-coords[1, 0])/len(ref)
                candidates.append((a.score, ga, intron, coverage, len(ref),
                                   left+int(coords[0, 0]), left+int(coords[0, -1])))
        candidates.sort(reverse=True); best, second = candidates[:2]
        score, ga, intron, coverage, length, start, end = best
        if score-second[0] < 20: return None, 'ambiguous_segment_score'
        if coverage < .95 or score/length < 1.3: return None, 'low_segment_alignment_quality'
        if spans and start < spans[-1][1]-20: return None, 'segment_order_or_overlap'
        spans.append((start, end)); bits.append((ga, intron))
        details.append({'position': i, 'start': start, 'end': end, 'coverage': float(coverage),
                        'score_per_reference_base': float(score/length), 'runner_up_margin': float(score-second[0])})
    genotype = ''.join(str(x[0]) for x in bits)+''.join(str(x[1]) for x in bits)
    return {'genotype': genotype, 'details': details}, None


def run(limit=5000):
    if limit != 5000: raise ValueError('This diagnostic is fixed to the first 5000 FASTQ records')
    path = DATA/'ERR12019311.fastq.gz'; receipt = json.loads((DATA/(path.name+'.receipt.json')).read_text())
    if sha256(path) != receipt['sha256'] or receipt['reads'] != 231531: raise ValueError('Verified DNA file changed')
    published = set((DATA/'faraway2025_plasmid_barcodes').read_text().splitlines())
    refs, index = references(); alignment = aligner()
    counts = Counter(); barcode_counts = Counter(); rows = []; alignment_rows = []
    with gzip.open(path, 'rt', encoding='ascii') as stream:
        for n in range(1, receipt['reads']+1):
            header = stream.readline().rstrip(); seq = stream.readline().strip(); stream.readline(); q = stream.readline().strip()
            counts['DNA_reads'] += 1
            b = barcode_record(seq, q)
            if b is not None:
                counts['exact_flank_unique_barcode_Q10_reads'] += 1; barcode_counts[b['barcode']] += 1
                counts['extracted_barcode_exactly_in_published_list_reads'] += int(b['barcode'] in published)
                if n <= limit:
                    result, error = call_construct(b['sequence'], refs, index, alignment)
                    if result is None: counts['pilot_'+error] += 1
                    else:
                        counts['pilot_complete_genotype_reads'] += 1
                        rows.append({'read_number': n, 'read_id': header.split()[0][1:], 'barcode': b['barcode'],
                                     'genotype': result['genotype'], 'barcode_in_published_list': b['barcode'] in published,
                                     'reverse_complemented': b['reverse'], 'barcode_min_Q': b['barcode_min_Q']})
                        for d in result['details']: alignment_rows.append({'read_number': n, **d})
                if n <= limit: counts['pilot_barcode_reads'] += 1
            if n == limit: print(json.dumps({'pilot_complete': dict(counts)}), flush=True)
            if n%50000 == 0: print('DNA barcode inventory reads', n, flush=True)
        if stream.readline(): raise ValueError('More reads than verified archive count')
    f = pd.DataFrame(rows, columns=['read_number','read_id','barcode','genotype','barcode_in_published_list','reverse_complemented','barcode_min_Q'])
    summary = {'scope': 'DNA-only provenance feasibility audit. Exact barcode flanks/Q10; first 5000 records for genotype alignment; no RNA outcome access.',
               'counts': dict(counts), 'distinct_extracted_barcodes': len(barcode_counts), 'published_barcode_list_unique': len(published),
               'distinct_extracted_barcodes_in_published_list': len(set(barcode_counts)&published),
               'pilot_distinct_complete_genotypes': int(f.genotype.nunique()),
               'pilot_distinct_complete_barcodes': int(f.barcode.nunique()),
               'pilot_barcodes_with_multiple_called_genotypes': int((f.groupby('barcode').genotype.nunique()>1).sum()),
               'published_numeric_barcode_IDs_reconstructed': False,
               'versions': {'biopython': Bio.__version__, 'numpy': np.__version__},
               'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in [path, DATA/'faraway2025_supptable_2.xlsx',
                         DATA/'faraway2025_plasmid_barcodes', ROOT/'src/research_20260921/faraway_dna_audit.py']}}
    write_new(OUT/'faraway_dna_pilot_calls.csv', f.to_csv(index=False, lineterminator='\n').encode())
    write_new(OUT/'faraway_dna_pilot_alignments.csv', pd.DataFrame(alignment_rows).to_csv(index=False, lineterminator='\n').encode())
    inventory = pd.DataFrame([{'barcode': b, 'reads': n, 'in_published_list': b in published} for b, n in sorted(barcode_counts.items())])
    write_new(OUT/'faraway_dna_barcode_inventory.csv', inventory.to_csv(index=False, lineterminator='\n').encode())
    write_json(OUT/'faraway_dna_audit.json', summary); print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__': run()
