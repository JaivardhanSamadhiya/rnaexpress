"""Plot verified aggregate-only replay; no fits, raw counts or sequence inputs."""
from .common import ROOT, sha256, write_new, write_json
import io
import json
import sys
sys.path.insert(1, str(ROOT / 'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def run():
    out = ROOT / 'results/research_20260921'
    source = out / 'srle_aggregate_replay_result_20260924.json'
    receipt = json.loads((out / 'srle_aggregate_package_receipt_20260924.json').read_text())
    if sha256(source) != receipt['replay_result_sha256']:
        raise ValueError('Replay result differs from package receipt')
    data = json.loads(source.read_text())['summary']['replicates']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.hashsalt': 'rnaddress-srle-aggregate-20260924'})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), gridspec_kw={'width_ratios': [1.25, 1]})
    models = ['composition', 'position_additive', 'kmer123', 'position_pair']
    colors = ['#147d92', '#c16b32']
    for rep, color in zip(('1', '2'), colors):
        offset = -.11 if rep == '1' else .11
        for i, model in enumerate(models):
            v = data[rep]['models'][model]
            x = v['regret_gain_over_uniform']; lo, hi = v['gain_ci']
            axes[0].errorbar(x, i + offset, xerr=[[max(0, x-lo)], [max(0, hi-x)]],
                             fmt='o', markersize=5, capsize=3, color=color,
                             label='Constituent replicate ' + rep if i == 0 else None)
        x = data[rep]['pair_minus_kmer123_gain']; lo, hi = data[rep]['pair_minus_kmer123_ci']
        axes[1].errorbar(x, int(rep)-1, xerr=[[x-lo], [hi-x]], fmt='o',
                         markersize=6, capsize=4, color=color)
    axes[0].set(yticks=range(4), yticklabels=['Composition', 'Position additive', 'Short motifs (1â€“3-mers)', 'Position pairs'],
                xlabel='Regret gain over uniform choice', xlim=(-.035, .34),
                title='A   Useful within-assay selection')
    axes[0].invert_yaxis()
    axes[0].legend(loc='upper right', fontsize=8.5, frameon=False)
    axes[1].set(yticks=[0, 1], yticklabels=['Replicate 1', 'Replicate 2'],
                xlabel='Pair-model gain minus short-motif gain', xlim=(-.065, .11),
                ylim=(1.6, -.6), title='B   Pair-model superiority is uncertain')
    for axis in axes:
        axis.axvline(0, color='#666666', linewidth=1)
        axis.grid(axis='x', alpha=.18)
        axis.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Measured six-mer choices: positive assay-specific result, competitive simple baseline',
                 fontsize=13, y=.97)
    fig.text(.025, .06,
             '592 parent neighborhoods in 60 composition classes; equal class weights; archived 2,000-draw descriptive bootstrap.\n'
             'Choices were fixed before raw-count evaluation. Training aggregates already used these constituent experiments.\n'
             'Neighborhoods overlap. Intervals omit full training uncertainty. This is not independent biological validation.',
             fontsize=9, color='#333333')
    fig.tight_layout(rect=(0, .20, 1, .93), w_pad=3)
    outputs = {}
    for suffix in ('png', 'svg'):
        buffer = io.BytesIO()
        fig.savefig(buffer, format=suffix, dpi=180,
                    metadata={'Date': None} if suffix == 'svg' else {})
        path = out / ('srle_aggregate_summary_20260924_v2.' + suffix)
        write_new(path, buffer.getvalue()); outputs[path.name] = sha256(path)
    plt.close(fig)
    write_json(out / 'srle_aggregate_figure_receipt_20260924_v2.json', {
        'source_sha256': sha256(source), 'code_sha256': sha256(__file__),
        'matplotlib_version': matplotlib.__version__, 'outputs': outputs,
        'new_outcomes': False, 'fits': 0})
    print(json.dumps(outputs, indent=2))


if __name__ == '__main__':
    run()
