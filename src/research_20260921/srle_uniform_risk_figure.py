"""Plot completed anonymous summaries and their matched uniform contrasts."""
from .common import ROOT, sha256, write_new, write_json
import io
import json
import sys
sys.path.insert(1, str(ROOT / 'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np


def run():
    out = ROOT / 'results/research_20260921'
    source = out / 'srle_uniform_risk_result_20260924.json'
    previous = out / 'srle_fixed_choice_risk_result_20260924.json'
    data = json.loads(source.read_text())
    freeze_path = out / 'srle_uniform_risk_freeze.json'
    if sha256(freeze_path) != data['freeze_sha256']:
        raise ValueError('Uniform reference freeze differs')
    for path, expected in {**json.loads(freeze_path.read_text())['files'], **data['outputs']}.items():
        if sha256(ROOT / path) != expected:
            raise ValueError('Uniform reference dependency or output differs: ' + path)
    old = json.loads(previous.read_text())
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.hashsalt': 'srle-uniform-risk-20260924'})
    models = ['composition', 'position_additive', 'kmer123', 'position_pair']
    labels = ['Composition tie choice', 'Position additive', 'Short motifs (1-3-mers)', 'Position pairs']
    categories = [('fraction_positive_both', 'Better in both', '#2d7c77'),
                  ('fraction_opposite_signs', 'Opposite signs', '#9dabc4'),
                  ('fraction_negative_both', 'Worse in both', '#b05b50'),
                  ('fraction_involving_tie', 'Involves a tie', '#d6d6d6')]
    fig, axes = plt.subplots(2, 2, figsize=(13.8, 9.5), sharey='row',
                             gridspec_kw={'height_ratios': [1.25, 1]})
    for col, direction, title in ((0, '-1', 'Requested decrease in NRS'),
                                  (1, '1', 'Requested increase in NRS')):
        ax = axes[0, col]
        summaries = [data['comparisons']['uniform'][direction]['paired_replicates']]
        summaries += [old['models'][m][direction]['paired_replicates'] for m in models]
        left = np.zeros(5)
        for name, label, color in categories:
            values = np.array([s[name]['estimate'] for s in summaries])
            ax.barh(range(5), values, left=left, height=.61, color=color, label=label)
            for row, value in enumerate(values):
                if value > .055:
                    ax.text(left[row] + value / 2, row, f'{value:.1%}', ha='center', va='center',
                            color='white' if name in ('fraction_positive_both', 'fraction_negative_both')
                            else '#202530', fontsize=9)
            left += values
        if not np.allclose(left, 1, atol=1e-12):
            raise ValueError('Paired categories fail to partition the decisions')
        ax.set(title=title, xlim=(0, 1), yticks=range(5),
               yticklabels=['Exact uniform expectation'] + labels,
               xlabel='Class-weighted fraction of decisions')
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(axis='y', length=0)

        ax = axes[1, col]
        for row, model in enumerate(models):
            metric = data['comparisons']['model_minus_uniform'][model][direction]['paired_replicates']['fraction_positive_both']
            point = 100 * metric['estimate']
            lower, upper = [100 * x for x in metric['descriptive_ci95']]
            ax.errorbar(point, row, xerr=[[point - lower], [upper - point]],
                        fmt='o', color='#2d7c77', capsize=4, markersize=6, elinewidth=1.8)
        ax.axvline(0, color='#667085', linestyle='--', linewidth=1)
        ax.set(title='Gain in decisions better in both replicates', xlim=(-12, 25),
               xticks=[-10, 0, 10, 20], yticks=range(4), yticklabels=labels,
               xlabel='Model minus uniform (percentage points)')
        ax.grid(axis='x', alpha=.15)
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(axis='y', length=0)
    axes[0, 0].invert_yaxis()
    axes[1, 0].invert_yaxis()
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc='lower center', ncol=4, frameon=False,
               bbox_to_anchor=(.58, .145), fontsize=10)
    fig.suptitle('Fixed choices improve on a matched random baseline, with frequent failures', y=.98, fontsize=15)
    fig.text(.5, .94, 'Same candidate identity across two constituent experimental replicates; all original models retained',
             ha='center', fontsize=10, color='#475467')
    fig.text(.025, .028,
             '592 parent neighborhoods in 60 equally weighted composition classes. Uniform choice averages original candidates within each parent.\n'
             'Top: point estimates; no numerical ties. Bottom: paired class-bootstrap descriptive 95% intervals (2,000 draws; fixed models).\n'
             'Better/worse describes the measured log2 localization score relative to the parent, not biological safety or toxicity.\n'
             'Post hoc audit of existing choices. Shared training experiment; no independent validation or established pair-model superiority.',
             fontsize=10, linespacing=1.55)
    fig.subplots_adjust(left=.205, right=.978, top=.886, bottom=.245, hspace=.49, wspace=.20)
    outputs = {}
    for suffix in ('png', 'svg'):
        buffer = io.BytesIO()
        fig.savefig(buffer, format=suffix, dpi=180, metadata={'Date': None} if suffix == 'svg' else {})
        path = out / ('srle_uniform_risk_20260924.' + suffix)
        write_new(path, buffer.getvalue())
        outputs[path.name] = sha256(path)
    plt.close(fig)
    write_json(out / 'srle_uniform_risk_figure_receipt_20260924.json', {
        'source_sha256': sha256(source), 'previous_result_sha256': sha256(previous),
        'code_sha256': sha256(__file__), 'matplotlib': matplotlib.__version__,
        'outputs': outputs, 'new_outcomes': False, 'fits': 0})
    print(json.dumps(outputs, indent=2))


if __name__ == '__main__':
    run()
