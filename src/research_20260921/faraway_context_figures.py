"""Plot recorded evaluations and descriptive intervals; no label access or fits."""
from .common import ROOT, write_new, write_json, sha256
import sys, io, json
sys.path.insert(1, str(ROOT/'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def run():
    out = ROOT/'results/research_20260921'
    eight = json.loads((out/'faraway_8h_replication_result.json').read_text())
    robust = json.loads((out/'context_robust_selection_result.json').read_text())
    d = pd.read_csv(out/'context_robust_selection_decisions.csv')
    means = d.groupby(['component', 'policy']).regret.mean().unstack('policy')
    draws = np.random.default_rng(20260924).integers(0, len(means), (5000, len(means)))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.hashsalt': 'rnaddress-20260923-faraway'})
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 6.4))
    models = ['interaction', 'additive', 'quadratic', 'pattern']
    for i, name in enumerate(models):
        v = eight['comparisons'][name]; low, high = v['descriptive_GA_ci95']; gain = v['gain_over_random']
        axes[0].errorbar(gain, i, xerr=[[gain-low], [high-gain]], fmt='o', capsize=4,
                         color='#146b80' if name in ['quadratic', 'pattern'] else '#777777')
    axes[0].set(yticks=range(4), yticklabels=['Sequence interaction', 'Additive introns', 'Quadratic introns*', 'Categorical pattern*'],
                xlabel='Regret improvement over uniform selection', title='Faraway: fixed 8-hour secondary assessment')
    axes[0].invert_yaxis(); axes[0].axvline(0, color='#777777', linewidth=1); axes[0].grid(axis='x', alpha=.2)
    policies = ['maximin', 'average', 'composition_maximin', 'Spliced', 'Unspliced', 'Circular', 'SCRCircular']
    labels = ['Worst predicted context*', 'Average predicted ranks', 'Composition maximin', 'Spliced only', 'Unspliced only', 'Circular only', 'SCR-circular only']
    posthoc = {}
    for i, policy in enumerate(policies):
        a = (means.uniform-means[policy]).to_numpy(); gain = a.mean(); low, high = np.quantile(a[draws].mean(axis=1), [.025, .975])
        axes[1].errorbar(gain, i, xerr=[[gain-low], [high-gain]], fmt='o', capsize=4, color='#146b80' if policy == 'maximin' else '#777777')
        posthoc[policy] = {'gain_over_uniform': float(gain), 'descriptive_component_ci95': [float(low), float(high)]}
    axes[1].set(yticks=range(len(policies)), yticklabels=labels, xlabel='Worst-context regret improvement over uniform',
                title='Ron–Ulitsky: source-only exploratory test')
    axes[1].invert_yaxis(); axes[1].axvline(0, color='#777777', linewidth=1); axes[1].grid(axis='x', alpha=.2)
    fig.suptitle('Two bounded selection tests: a secondary signal and a failed superiority claim', fontsize=14)
    fig.text(.025, .07, 'Left: 28 engineered GA panels; 207 overlapping constructs; three replicates. *Both fixed policies met secondary criteria.\n'
             'Right: 52 source components; four reporter contexts. *Maximin did not beat every baseline; its criterion FAILED.\n'
             'All intervals are descriptive. Different expressed barcodes, one protein context (left), reused source data (right).\n'
             'No independent biological replication, novel mechanism, or universal RNA-control claim is established.', fontsize=9)
    fig.tight_layout(rect=[0, .19, 1, .93])
    hashes = {}
    for suffix in ['png', 'svg']:
        buf = io.BytesIO(); fig.savefig(buf, format=suffix, dpi=180, metadata={'Date': None} if suffix == 'svg' else {})
        p = out/('faraway_context_summary.'+suffix); write_new(p, buf.getvalue()); hashes[p.name] = sha256(p)
    plt.close(fig)
    write_json(out/'faraway_context_figure_receipt.json', {'files': hashes, 'context_posthoc_uniform_comparisons': posthoc,
               'source_numeric_outcomes_read': False, 'fits_performed': False, 'matplotlib': matplotlib.__version__})


if __name__ == '__main__': run()
