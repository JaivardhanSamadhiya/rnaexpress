"""Plot anonymous fixed-choice consistency summaries; no fitting or source labels."""
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
    source = out / 'srle_fixed_choice_risk_result_20260924.json'
    data = json.loads(source.read_text())
    if sha256(out / 'srle_fixed_choice_risk_freeze.json') != data['freeze_sha256']:
        raise ValueError('Risk freeze differs')
    for path, expected in data['files'].items():
        if sha256(ROOT / path) != expected:
            raise ValueError('Risk dependency differs')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.hashsalt': 'rnaddress-srle-fixed-risk-20260924'})
    models = ['composition', 'position_additive', 'kmer123', 'position_pair']
    labels = ['Composition tie choice', 'Position additive', 'Short motifs (1-3-mers)', 'Position pairs']
    categories = [('fraction_positive_both', 'Better in both', '#2d7c77'),
                  ('fraction_opposite_signs', 'Opposite signs', '#9dabc4'),
                  ('fraction_negative_both', 'Worse in both', '#b05b50'),
                  ('fraction_involving_tie', 'Involves a tie', '#d6d6d6')]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 6), sharey=True)
    for ax, direction, title in zip(axes, ('-1', '1'), ('Requested decrease in NRS', 'Requested increase in NRS')):
        left = np.zeros(4)
        for name, label, color in categories:
            values = np.array([data['models'][model][direction]['paired_replicates'][name]['estimate'] for model in models])
            ax.barh(range(4), values, left=left, height=.58, color=color, label=label)
            for i, value in enumerate(values):
                if value > .055:
                    ax.text(left[i] + value/2, i, f'{value:.1%}', ha='center', va='center',
                            color='white' if name in ('fraction_positive_both', 'fraction_negative_both') else '#202530', fontsize=9)
            left += values
        if not np.allclose(left, 1, atol=1e-12):
            raise ValueError('Paired categories do not partition decisions')
        ax.set(title=title, xlim=(0, 1), yticks=range(4), yticklabels=labels,
               xlabel='Class-weighted fraction of fixed decisions')
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(axis='y', length=0)
    axes[0].invert_yaxis()
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc='lower center', ncol=4, frameon=False,
               bbox_to_anchor=(.56, .16), fontsize=9)
    fig.suptitle('Positive average changes coexist with frequent wrong-direction choices', y=.97, fontsize=14)
    fig.text(.025, .035,
             '592 parent neighborhoods; 60 equally weighted composition classes; two constituent experimental replicates.\n'
             'Better/worse refers only to the measured score relative to the parent, not biological safety or toxicity.\n'
             'Post hoc fixed-choice diagnostic; no retuning. Point estimates shown; descriptive intervals are in the saved result.\n'
             'Shared training experiment and overlapping neighborhoods prevent independent-validation claims.', fontsize=9)
    fig.tight_layout(rect=(0, .245, 1, .92), w_pad=2.5)
    outputs = {}
    for suffix in ('png', 'svg'):
        buffer = io.BytesIO()
        fig.savefig(buffer, format=suffix, dpi=180, metadata={'Date': None} if suffix == 'svg' else {})
        p = out / ('srle_fixed_choice_risk_20260924.' + suffix)
        write_new(p, buffer.getvalue()); outputs[p.name] = sha256(p)
    plt.close(fig)
    write_json(out / 'srle_fixed_choice_risk_figure_receipt_20260924.json', {
        'source_sha256': sha256(source), 'code_sha256': sha256(__file__),
        'matplotlib': matplotlib.__version__, 'outputs': outputs,
        'new_outcomes': False, 'fits': 0})
    print(json.dumps(outputs, indent=2))


if __name__ == '__main__':
    run()
