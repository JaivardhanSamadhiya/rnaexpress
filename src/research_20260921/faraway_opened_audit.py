"""Post-hoc diagnostics confined to already-opened Faraway candidate outcomes."""
from .common import ROOT, sha256, write_json, write_new
from .faraway_configuration import OUT, DATA, MODELS, load_frame, read_values, regret, verify
from .faraway_8h_replication import target_metadata, read_target
from .faraway_design import STARTS, excise
import itertools, json
import numpy as np
import pandas as pd
import openpyxl
from scipy.stats import spearmanr


def directional(y, prediction, sign):
    y = np.asarray(y, float) * sign
    p = np.asarray(prediction, float) * sign
    chosen = y[p == p.max()].mean()
    return float((y.max() - chosen) / np.ptp(y)), float(chosen - y.mean())


def assemble_target(frame):
    book = openpyxl.load_workbook(DATA/'faraway2025_supptable_2.xlsx', read_only=True, data_only=True)
    fragments = {n: s.upper() for n, s in list(book['Ordered_fragments'].values)[1:] if isinstance(s, str)}
    book.close()
    pieces = {}
    for tag, i in itertools.product(['Opt', 'DeO'], range(1, 9)):
        no = fragments[f'PPIG_{tag}_NoIn_{i}']
        yes, _, _ = excise(no, fragments[f'PPIG_{tag}_In_{i}'])
        offset = 49 if i == 1 else 0
        size = STARTS[i] - STARTS[i-1]
        for bit, s in enumerate([no, yes]):
            pieces[(tag, i, bit)] = s[offset:offset+size]
    sequences = {}
    for g in frame.genotype:
        sequences[g] = ''.join(pieces[('Opt' if g[i-1] == '1' else 'DeO', i, int(g[i+7]))] for i in range(1, 9))
    for _, group in frame.groupby('panel'):
        if len({sequences[g] for g in group.genotype}) != 1:
            raise ValueError('Target insert identity failed')
    return {'target_genotypes_reconstructed': len(sequences), 'panels_with_identical_reconstructed_insert': int(frame.panel.nunique()),
            'insert_lengths': sorted({len(s) for s in sequences.values()}), 'full_transcript_identity_established': False,
            'qualification': 'Expressed 3-prime UTR barcodes differ; insert reconstruction assumes intended splicing.'}


def aggregate_mean(frame, columns):
    return frame.groupby(['ga', 'replicate', 'model', 'direction'])[columns].mean().groupby(['model', 'direction']).mean()


def diagnostics(name, metadata, pred, values):
    f = metadata.copy(); f['y'] = [values[r] for r in f.excel_row]
    agg = f.groupby(['genotype', 'replicate']).y.mean().unstack('replicate')
    joined = pred.merge(agg, left_on='genotype', right_index=True, validate='one_to_one')
    rows, repeats = [], []
    for key, g in joined.groupby('panel'):
        for rep in [1, 2, 3]:
            y = g[rep].to_numpy()
            for model in MODELS:
                for sign, direction in [(1, 'nuclear'), (-1, 'cytoplasmic')]:
                    r, gain = directional(y, g[model], sign)
                    rows.append({'panel': key, 'ga': g.ga.iloc[0], 'replicate': rep, 'model': model,
                                 'direction': direction, 'regret': r, 'log2_ratio_gain_vs_uniform': gain})
            other = g[[r for r in [1, 2, 3] if r != rep]].mean(axis=1)
            repeats.append({'panel': key, 'ga': g.ga.iloc[0], 'replicate': rep,
                            'other_replicates_selection_regret': regret(y, other)})
    d = pd.DataFrame(rows); means = aggregate_mean(d, ['regret', 'log2_ratio_gain_vs_uniform'])
    results = {m: {direction: means.loc[(m, direction)].to_dict() for direction in ['nuclear', 'cytoplasmic']} for m in MODELS}
    summary = {m: float(np.mean([v['regret'] for v in results[m].values()])) for m in MODELS}
    original = json.loads((OUT/('faraway_configuration_development.json' if name == 'development' else 'faraway_8h_replication_result.json')).read_text())
    expected = original['mean_regret']
    if any(not np.isclose(summary[m], expected[m], rtol=1e-12, atol=1e-12) for m in MODELS):
        raise ValueError('Original regret not reproduced')
    correlations = {}
    for a, b in itertools.combinations([1, 2, 3], 2):
        v = [{'ga': g.ga.iloc[0], 'rho': float(spearmanr(g[a], g[b]).statistic)} for _, g in joined.groupby('panel')]
        v = pd.DataFrame(v).groupby('ga').rho.mean()
        correlations[f'{a}-{b}'] = {'mean_GA_rho': float(v.mean()), 'median_GA_rho': float(v.median())}
    repeat = pd.DataFrame(repeats).groupby(['ga', 'replicate']).other_replicates_selection_regret.mean()
    write_new(OUT/f'faraway_{name}_direction_diagnostic.csv', d.to_csv(index=False, lineterminator='\n').encode())
    return joined, {'all_models': results, 'original_regrets_reproduced': True,
                    'within_panel_replicate_correlations': correlations,
                    'other_replicates_selection_regret': float(repeat.mean())}


def coherent_permutation(frame, draws=5000):
    patterns = sorted({g[8:] for g in frame.genotype})
    pindex = {p: i for i, p in enumerate(patterns)}
    groups = list(frame.groupby('panel'))
    ga_panels = frame[['ga', 'panel']].drop_duplicates().ga.value_counts()
    rng = np.random.default_rng(20260924)
    permutations = np.array([rng.permutation(len(patterns)) for _ in range(draws)])
    answer = {}
    for model in ['quadratic', 'pattern']:
        scores = []
        for pattern in patterns:
            values = frame.loc[frame.genotype.str[8:] == pattern, model].to_numpy()
            if not np.allclose(values, values[0], rtol=1e-12, atol=1e-12):
                raise ValueError('Common-pattern scores are not common')
            scores.append(values[0])
        scores = np.asarray(scores); shuffled = scores[permutations]
        null = np.zeros(draws); observed = 0.
        for _, g in groups:
            ids = np.array([pindex[x[8:]] for x in g.genotype]); p = shuffled[:, ids]
            weight = 1 / (len(ga_panels) * ga_panels[g.ga.iloc[0]] * 3)
            for rep in [1, 2, 3]:
                y = g[rep].to_numpy()
                observed += weight * regret(y, g[model])
                for sign in [1, -1]:
                    sy = sign*y; sp = sign*p
                    selected = sp == sp.max(axis=1, keepdims=True)
                    chosen = (selected*sy).sum(axis=1)/selected.sum(axis=1)
                    null += .5 * weight * (sy.max()-chosen)/np.ptp(y)
        answer[model] = {'observed_regret': observed, 'null_mean_regret': float(null.mean()),
                         'null_regret_quantiles_025_50_975': np.quantile(null, [.025, .5, .975]).tolist(),
                         'one_sided_Monte_Carlo_tail_area': float((1+(null <= observed).sum())/(draws+1))}
    return {'draws': draws, 'unique_intron_patterns': len(patterns), 'models': answer,
            'interpretation': 'Post-hoc global-pattern score randomization; not a confirmatory p-value or training-uncertainty interval.'}


def run():
    verify()
    freeze = json.loads((OUT/'faraway_8h_replication_freeze.json').read_text())
    for p, h in freeze['files'].items():
        if sha256(ROOT/p) != h: raise ValueError('8-hour frozen file changed')
    source = load_frame(); target = target_metadata()
    p8 = pd.read_csv(OUT/'faraway_8h_replication_predictions.csv', dtype={'genotype': str, 'ga': str})
    dev = source[(source.partition == 'development') & source.decision_candidate]
    pdv = pd.read_csv(OUT/'faraway_configuration_predictions.csv', dtype={'genotype': str, 'ga': str})
    pdv = pdv[pdv.partition == 'development']
    vdev, _ = read_values(DATA/'faraway2025_supptable_3.xlsx', dev.excel_row)
    jdev, rdev = diagnostics('development', dev, pdv, vdev)
    j8, r8 = diagnostics('8h', target, p8, read_target(DATA/'faraway2025_supptable_3.xlsx', target.excel_row))
    genotype_sets = {part: set(source.loc[source.partition == part, 'genotype']) for part in ['train', 'development', 'confirmation']}
    ga_sets = {part: set(source.loc[source.partition == part, 'ga']) for part in genotype_sets}
    overlap = {part: {'genotypes': len(set(p8.genotype) & gs), 'GA_patterns': len(set(p8.ga) & ga_sets[part])} for part, gs in genotype_sets.items()}
    overlap['absent_from_transfection_1'] = {'genotypes': len(set(p8.genotype)-set(source.genotype))}
    barcode_counts = target.groupby('genotype').bc_number.nunique()
    result = {'scope': 'Post-hoc diagnostics; no model fitting or new outcome access; both original verdicts unchanged.',
              'target_design': assemble_target(p8), 'target_source_overlap': overlap,
              'target_barcode_count_distribution_per_genotype': {str(k): int(v) for k, v in barcode_counts.value_counts().sort_index().items()},
              'development': rdev, '8h': r8, '8h_coherent_pattern_permutation': coherent_permutation(j8),
              'original_confirmation_outcomes_read': False, 'other_assay_outcomes_read': False}
    write_json(OUT/'faraway_opened_audit.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__': run()
