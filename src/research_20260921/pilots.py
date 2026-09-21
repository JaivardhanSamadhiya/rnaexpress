"""Two fixed, exploratory new-data pilots. See pilot_execution_spec.md."""
from .common import ROOT, sha256, write_json, write_new, load_certified
from .inspect_assets import nested_zip
from .sequence_inventory import arora_sequences
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import io
import itertools
import json
import re
import subprocess
import sys
import tarfile

import numpy as np
import openpyxl
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

OUT = ROOT / 'results/research_20260921'
DATA = ROOT / 'data/external/research_20260921'
BASES = 'ACGT'

def read_sixmers():
    z = nested_zip('srle_epmc_supplement', 'csbj.0107.f1.zip')
    content = z.read('Supplement Table5.xlsx')
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    rows = list(wb.active.values)
    frame = pd.DataFrame(rows[2:], columns=rows[1]).dropna(subset=['kmer'])
    wb.close()
    frame['kmer'] = frame.kmer.str.upper().str.replace('U', 'T')
    if set(frame.kmer) != {''.join(p) for p in itertools.product(BASES, repeat=6)} or len(frame) != 4096:
        raise ValueError('Six-mer library is not a unique exhaustive alphabet')
    frame['score'] = pd.to_numeric(frame['NRS(log2FC)'], errors='raise')
    if not np.isfinite(frame.score).all():
        raise ValueError('Missing NRS')
    return frame.sort_values('kmer').reset_index(drop=True)

def comp_key(sequence):
    return tuple(sequence.count(b) for b in BASES)

def test_bucket(sequence):
    return int(hashlib.sha256(('srle-order-20260921|' + sequence).encode()).hexdigest(), 16) % 5 == 0

def position_features(sequences):
    encoded = np.array([[BASES.index(b) for b in s] for s in sequences])
    if encoded.shape[1] != 6:
        raise ValueError('Six bases required')
    onehot = np.eye(4)[encoded]
    blocks = [onehot.reshape(len(encoded), -1)]
    blocks += [(onehot[:, i, :, None] * onehot[:, j, None, :]).reshape(len(encoded), 16)
               for i in range(6) for j in range(i + 1, 6)]
    return np.column_stack(blocks)

def regret(y, scores, ids):
    y, scores, ids = np.asarray(y), np.asarray(scores), np.asarray(ids)
    spread = np.ptp(y)
    if spread <= 0 or len(y) < 2:
        return np.nan
    values = []
    for sign in (1, -1):
        chosen = np.lexsort((ids, -sign * scores))[0]
        values.append((np.max(sign * y) - sign * y[chosen]) / spread)
    return float(np.mean(values))

def fit_order(sequences, y):
    sequences, y = np.asarray(sequences), np.asarray(y, float)
    keys = [comp_key(s) for s in sequences]
    test = np.array([test_bucket(s) for s in sequences])
    groups = sorted(set(keys))
    means = {k: float(np.mean(y[[i for i in range(len(y)) if keys[i] == k and not test[i]]]))
             for k in groups if any(keys[i] == k and not test[i] for i in range(len(y)))}
    baseline = np.array([means.get(k, 0.0) for k in keys])
    x = position_features(sequences)
    scaler = StandardScaler().fit(x[~test])
    model = Ridge(alpha=10.0).fit(scaler.transform(x[~test]), (y - baseline)[~test])
    prediction = baseline + model.predict(scaler.transform(x))
    eligible = [k for k in groups if sum(keys[i] == k and test[i] for i in range(len(y))) >= 2
                and sum(keys[i] == k and not test[i] for i in range(len(y))) >= 2]
    indices = [np.array([i for i in range(len(y)) if test[i] and keys[i] == k]) for k in eligible]
    return test, keys, baseline, prediction, indices

def pilot_a():
    table = read_sixmers()
    seq = table.kmer.to_numpy()
    y = table.score.to_numpy(float)
    test, keys, base, pred, indices = fit_order(seq, y)
    selected = np.concatenate(indices)
    base_sse = np.array([np.sum((y[ix] - base[ix]) ** 2) for ix in indices])
    full_sse = np.array([np.sum((y[ix] - pred[ix]) ** 2) for ix in indices])
    gains = np.array([regret(y[ix], base[ix], seq[ix]) - regret(y[ix], pred[ix], seq[ix]) for ix in indices])
    effect = float(1 - full_sse.sum() / base_sse.sum())
    rng = np.random.default_rng(20260921)
    perm_effect = []
    for _ in range(999):
        numerator, denominator = 0.0, 0.0
        for ix in indices:
            permuted = rng.permutation(y[ix])
            numerator += float(np.sum((permuted - pred[ix]) ** 2))
            denominator += float(np.sum((permuted - base[ix]) ** 2))
        perm_effect.append(1 - numerator / denominator)
    draw = rng.integers(0, len(indices), (2000, len(indices)))
    boot_effect = 1 - full_sse[draw].sum(axis=1) / base_sse[draw].sum(axis=1)
    boot_regret = gains[draw].mean(axis=1)
    p = (1 + sum(v >= effect for v in perm_effect)) / 1000
    table = pd.DataFrame({'kmer': seq, 'test': test, 'nrs': y, 'composition_prediction': base,
                          'order_prediction': pred, 'composition': [str(k) for k in keys]})
    write_new(OUT / 'pilot_a_predictions.csv', table.to_csv(index=False, lineterminator='\n').encode())
    result = {'train_sequences': int((~test).sum()), 'heldout_sequences': int(test.sum()),
              'eligible_heldout_sequences': len(selected), 'eligible_composition_classes': len(indices),
              'residual_squared_error_reduction': effect,
              'residual_squared_error_reduction_ci': np.quantile(boot_effect, [.025, .975]).tolist(),
              'regret_gain': float(gains.mean()),
              'regret_gain_ci': np.quantile(boot_regret, [.025, .975]).tolist(),
              'residual_pearson': float(pearsonr((y - base)[selected], (pred - base)[selected]).statistic),
              'conditional_test_permutation_p': p,
              'promising': bool(effect > .10 and gains.mean() > 0 and p <= .01),
              'scope': 'One reporter context; held-out sequences; no biological replicate validation or unseen-parent claim.'}
    write_json(OUT / 'pilot_a_result.json', result)
    print('PILOT A ' + json.dumps(result), flush=True)

def count_member_allowed(name):
    return bool(re.fullmatch(r'GSM\d+_(CAD|N2A)_(Soma|Neurite)_(FF|GFP)_Rep[12]\.umis\.txt\.gz', name))

def load_pilot_counts():
    counts = {}
    opened = []
    with tarfile.open(DATA / 'arora_counts') as archive:
        for member in archive.getmembers():
            if not count_member_allowed(member.name):
                continue
            if not member.isfile() or member.size > 1024 * 1024:
                raise ValueError('Unexpected count member')
            content = gzip.decompress(archive.extractfile(member).read())
            frame = pd.read_csv(io.BytesIO(content), sep='\t')
            if frame.oligo.duplicated().any():
                raise ValueError('Duplicate oligo in counts')
            _, cell, compartment, reporter, rep = member.name.split('_')
            rep = int(rep[3])
            counts[(cell, reporter, compartment, rep)] = frame.set_index('oligo').numuniqueumis
            opened.append(member.name)
    if len(opened) != 16:
        raise ValueError('Expected exactly 16 discovery samples; holdout samples excluded')
    return counts, opened

def pilot_b():
    nrs = read_sixmers().set_index('kmer').score.to_dict()
    records = arora_sequences()
    valid = [(n, s) for n, s in records if len(s) == 260 and not set(s) - set(BASES)]
    prediction = pd.DataFrame([{'oligo': n, 'gene': n.split('|')[1],
        'external': -float(np.mean([nrs[s[j:j+6]] for j in range(len(s)-5)])),
        'ag': (s.count('A') + s.count('G')) / len(s),
        'au': (s.count('A') + s.count('T')) / len(s),
        'minus_c': -s.count('C') / len(s)} for n, s in valid]).set_index('oligo')
    counts, opened = load_pilot_counts()
    old_genes = set(load_certified().gene_name.str.casefold())
    results, exclusions = [], []
    all_frames = []
    for cell, reporter in itertools.product(['CAD', 'N2A'], ['FF', 'GFP']):
        frame = prediction.copy()
        for compartment, rep in itertools.product(['Soma', 'Neurite'], [1, 2]):
            frame[f'{compartment}{rep}'] = counts[(cell, reporter, compartment, rep)]
        count_cols = ['Soma1', 'Soma2', 'Neurite1', 'Neurite2']
        keep = frame[count_cols].notna().all(axis=1) & (frame[count_cols] >= 10).all(axis=1)
        exclusions.append({'cell': cell, 'reporter': reporter, 'before': len(frame), 'after': int(keep.sum())})
        frame = frame.loc[keep].copy()
        frame['effect'] = np.mean([np.log2((frame[f'Neurite{r}'] + .5) / (frame[f'Soma{r}'] + .5)) for r in (1, 2)], axis=0)
        frame['context'] = cell + '_' + reporter
        all_frames.append(frame.reset_index())
        for gene, g in frame.groupby('gene'):
            if len(g) < 20 or np.ptp(g.effect) <= 0:
                continue
            result = {'gene': gene, 'context': cell + '_' + reporter, 'n': len(g),
                      'new_gene': gene.casefold() not in old_genes}
            for model in ('external', 'ag', 'au', 'minus_c'):
                result[model + '_regret'] = regret(g.effect, g[model], g.index.to_numpy())
                result[model + '_spearman'] = float(spearmanr(g.effect, g[model]).statistic)
            result['regret_gain_vs_ag'] = result['ag_regret'] - result['external_regret']
            results.append(result)
    per_gene = pd.DataFrame(results)
    if per_gene.empty:
        raise ValueError('No eligible genes')
    context_values = per_gene.groupby('context').regret_gain_vs_ag.mean()
    effect = float(context_values.mean())
    genes = sorted(per_gene.gene.unique())
    # Context x gene matrix. Bootstrap a gene once and retain every context.
    matrix = per_gene.pivot(index='context', columns='gene', values='regret_gain_vs_ag').reindex(columns=genes).to_numpy()
    rng = np.random.default_rng(20260921)
    samples = []
    invalid = 0
    for _ in range(2000):
        chosen = rng.integers(0, len(genes), len(genes))
        sample = matrix[:, chosen]
        if not np.isfinite(sample).any(axis=1).all():
            invalid += 1
            continue
        samples.append(float(np.nanmean(sample, axis=1).mean()))
    ci = np.quantile(samples, [.025, .975]).tolist() if samples else [None, None]
    new = per_gene[per_gene.new_gene]
    write_new(OUT / 'pilot_b_gene_metrics.csv', per_gene.to_csv(index=False, lineterminator='\n').encode())
    write_new(OUT / 'pilot_b_predictions.csv', pd.concat(all_frames).to_csv(index=False, lineterminator='\n').encode())
    result = {'genes': len(genes), 'contexts': len(context_values), 'regret_gain_vs_ag': effect,
        'gene_bootstrap_ci': ci, 'invalid_bootstrap_fraction': invalid / 2000,
        'context_regret_gain_vs_ag': context_values.to_dict(),
        'new_genes': sorted(new.gene.unique()),
        'new_gene_macro_regret_gain_vs_ag': float(new.groupby('context').regret_gain_vs_ag.mean().mean()) if len(new) else None,
        'promising': bool(effect >= .01 and (context_values > 0).sum() >= 3 and ci[0] is not None and ci[0] > 0 and invalid <= 20),
        'excluded_fasta_records': [{'id': n, 'length': len(s)} for n, s in records if len(s) != 260],
        'count_eligibility': exclusions, 'opened_samples': opened,
        'replicate_3_or_4_opened': False,
        'scope': 'External assay transfer pilot; tiled fragments, not point edits. Overlapping old genes are reported.'}
    write_json(OUT / 'pilot_b_result.json', result)
    print('PILOT B ' + json.dumps(result), flush=True)

def freeze():
    paths = list((ROOT / 'src/research_20260921').glob('*.py')) + [
        ROOT / 'reports/research_20260921/pilot_execution_spec.md',
        DATA / 'srle_epmc_supplement', DATA / 'arora_epmc_supplement', DATA / 'arora_counts']
    result = {'created_utc': datetime.now(timezone.utc).isoformat(),
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in paths},
        'specification_kind': 'AI-authored fixed exploratory execution specification',
        'old_selector_fits': 0, 'target_pilot_scores_generated': False}
    write_json(OUT / 'pilot_freeze.json', result)
    print('Pilot freeze recorded; no scores produced.', flush=True)

def verify():
    frozen = json.loads((OUT / 'pilot_freeze.json').read_text())
    for p, digest in frozen['files'].items():
        if sha256(ROOT / p) != digest:
            raise ValueError('Frozen pilot dependency differs: ' + p)

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('freeze', 'a', 'b'):
        raise SystemExit('Use freeze, a or b')
    if sys.argv[1] == 'freeze':
        freeze()
    else:
        verify()
        (pilot_a if sys.argv[1] == 'a' else pilot_b)()
