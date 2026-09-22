"""Independent paired-read counter and fixed reconstruction diagnostics."""
from .common import ROOT, sha256, write_json, write_new
from .pilots import BASES, comp_key, read_sixmers
from collections import Counter
from datetime import datetime, timezone
from itertools import product, zip_longest
import gzip
import json
import re
import sys
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

DATA = ROOT / 'data/external/research_20260921/srle_reads'
OUT = ROOT / 'results/research_20260921'
RUNS = {'HRR3059160': 'Cyto1', 'HRR3059161': 'Cyto2',
        'HRR3059163': 'Nuc1', 'HRR3059164': 'Nuc2'}
PATTERNS = (re.compile(b'ATCACTAAGC([ACGT]{6})ATCATAATCA'),
            re.compile(b'TGATTATGAT([ACGT]{6})GCTTAGTGAT'))
COMPLEMENT = bytes.maketrans(b'ACGT', b'TGCA')


def reverse_complement(sequence):
    return sequence.translate(COMPLEMENT)[::-1]


def extract(sequence, quality):
    hits = []
    for orientation, pattern in enumerate(PATTERNS):
        for match in pattern.finditer(sequence):
            start, end = match.span(1)
            if min(quality[start:end]) < 53:
                continue
            kmer = match.group(1)
            hits.append(reverse_complement(kmer) if orientation else kmer)
    return hits[0] if len(hits) == 1 else None


def records(path):
    with gzip.open(path, 'rb') as stream:
        while True:
            name = stream.readline().rstrip()
            if not name:
                return
            sequence = stream.readline().rstrip()
            plus = stream.readline().rstrip()
            quality = stream.readline().rstrip()
            if not name.startswith(b'@') or not plus.startswith(b'+') or len(sequence) != len(quality) or not sequence:
                raise ValueError('Invalid FASTQ: ' + str(path))
            yield name.split()[0].removesuffix(b'/1').removesuffix(b'/2'), sequence, quality


def count_pair(forward, reverse):
    counts, qc = Counter(), Counter()
    for left, right in zip_longest(records(forward), records(reverse)):
        if left is None or right is None or left[0] != right[0]:
            raise ValueError('Paired read identity or length mismatch')
        qc['pairs'] += 1
        a, b = extract(left[1], left[2]), extract(right[1], right[2])
        if a is not None:
            qc['mate1_valid'] += 1
        if b is not None:
            qc['mate2_valid'] += 1
        if a is not None and b is not None:
            if a != b:
                qc['discordant'] += 1
                continue
            qc['both_agree'] += 1
        chosen = a if a is not None else b
        if chosen is None:
            qc['no_valid_insert'] += 1
        else:
            counts[chosen.decode()] += 1
            qc['accepted'] += 1
    return counts, dict(qc)


def count_all():
    paths = [ROOT / 'src/research_20260921/raw_counts.py',
             ROOT / 'reports/research_20260921/raw_replication_spec.md']
    write_json(OUT / 'raw_counts_freeze.json', {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in paths},
        'status': 'No count outcome associations yet computed'})
    kmers = [''.join(s) for s in product(BASES, repeat=6)]
    result = pd.DataFrame({'kmer': kmers}).set_index('kmer')
    quality = {}
    for run, label in RUNS.items():
        paths = [DATA / f'{run}_{mate}.fq.gz' for mate in ('f1', 'r2')]
        for path in paths:
            receipt = json.loads(path.with_suffix('.gz.receipt.json').read_text())
            if sha256(path) != receipt['sha256']:
                raise ValueError('Raw file differs: ' + str(path))
        counts, qc = count_pair(*paths)
        result[label] = [counts[k] for k in kmers]
        quality[run] = dict(sample=label, **qc)
        print(json.dumps({run: quality[run]}), flush=True)
    write_new(OUT / 'raw_sixmer_counts.csv', result.to_csv(lineterminator='\n').encode())
    write_json(OUT / 'raw_counts_qc.json', quality)


def correlation(x, y):
    return {'pearson': float(pearsonr(x, y).statistic), 'spearman': float(spearmanr(x, y).statistic)}


def diagnose():
    frame = pd.read_csv(OUT / 'raw_sixmer_counts.csv').set_index('kmer')
    for rep in (1, 2):
        nuc, cyto = frame[f'Nuc{rep}'], frame[f'Cyto{rep}']
        frame[f'NRS{rep}'] = np.log2((nuc+.5)/(nuc.sum()+2048)) - np.log2((cyto+.5)/(cyto.sum()+2048))
    keep = (frame[['Nuc1','Nuc2','Cyto1','Cyto2']] >= 20).all(axis=1)
    frame['eligible'] = keep
    published = read_sixmers().set_index('kmer').score
    predictions = pd.read_csv(OUT / 'robustness_predictions.csv').set_index('kmer')
    frame['published_forward'] = published
    frame['published_reverse'] = [published[reverse_complement(k.encode()).decode()] for k in frame.index]
    result = {'eligible_sequences': int(keep.sum()), 'total_sequences': len(frame),
              'scope': 'same experimental replicates as published table; technical reconstruction only',
              'replicate_correlation': correlation(frame.loc[keep,'NRS1'],frame.loc[keep,'NRS2']),
              'orientations': {}}
    for orientation in ('forward', 'reverse'):
        ids = list(frame.index) if orientation == 'forward' else [reverse_complement(k.encode()).decode() for k in frame.index]
        mapped = predictions.loc[ids].reset_index(drop=True)
        selected = keep.to_numpy() & mapped.test.to_numpy(bool)
        groups = pd.Series([str(comp_key(k)) for k in frame.index], index=frame.index)
        diagnostics = {}
        for rep in (1, 2):
            y = frame[f'NRS{rep}']
            p = frame['published_'+orientation]
            centered_y = y - y[keep].groupby(groups[keep]).mean().reindex(groups).set_axis(frame.index)
            centered_p = p - p[keep].groupby(groups[keep]).mean().reindex(groups).set_axis(frame.index)
            entry = {'published_raw': correlation(y[keep], p[keep]),
                     'published_composition_centered': correlation(centered_y[keep], centered_p[keep]),
                     'heldout_prediction_correlations': {}}
            for model in ('position_additive','position_pair','kmer123'):
                pred = pd.Series(mapped[model].to_numpy(), index=frame.index)
                pred = pred - pred[selected].groupby(groups[selected]).mean().reindex(groups).set_axis(frame.index)
                target = y-y[selected].groupby(groups[selected]).mean().reindex(groups).set_axis(frame.index)
                entry['heldout_prediction_correlations'][model] = correlation(target[selected],pred[selected])
            diagnostics[f'rep{rep}'] = entry
        result['orientations'][orientation] = diagnostics
    write_new(OUT / 'raw_replication_scores.csv', frame.to_csv(lineterminator='\n').encode())
    write_json(OUT / 'raw_replication_result.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    if sys.argv[1:] == ['count']:
        count_all()
    elif sys.argv[1:] == ['diagnose']:
        diagnose()
    else:
        raise SystemExit('Use count or diagnose')
