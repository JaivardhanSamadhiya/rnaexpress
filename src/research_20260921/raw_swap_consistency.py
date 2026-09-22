"""Evaluate previously fixed edit choices in both reconstructed replicates."""
from .common import ROOT, sha256, write_new, write_json
from .robustness import swaps
from .pilots import comp_key
from datetime import datetime, timezone
import json
import numpy as np
import pandas as pd

OUT = ROOT / 'results/research_20260921'


def run():
    files = [ROOT / 'src/research_20260921/raw_swap_consistency.py',
             ROOT / 'reports/research_20260921/raw_swap_spec.md',
             OUT / 'robustness_swap_predictions.csv', OUT / 'raw_replication_scores.csv']
    write_json(OUT / 'raw_swap_freeze.json', {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in files},
        'status': 'after raw correlation diagnostics; before fixed-edit replicate evaluation'})
    choices = pd.read_csv(OUT / 'robustness_swap_predictions.csv')
    raw = pd.read_csv(OUT / 'raw_replication_scores.csv').set_index('kmer')
    pred = pd.read_csv(OUT / 'robustness_predictions.csv').set_index('kmer')
    groups = {}
    for sequence in pred.index:
        groups.setdefault(comp_key(sequence), []).append(sequence)
    eligible_test = set()
    for sequences in groups.values():
        mask = pred.loc[sequences, 'test']
        if mask.sum() >= 2 and (~mask).sum() >= 2:
            eligible_test.update(mask.index[mask])
    records = []
    removed = []
    for parent, group in choices.groupby('parent'):
        candidates = [s for s in swaps(parent) if s in eligible_test]
        if not (group.candidates == len(candidates)).all() or not group.selected.isin(candidates).all():
            raise ValueError('Original edit candidate set differs')
        if not raw.loc[[parent]+candidates, 'eligible'].all():
            removed.append(parent)
            continue
        for rep in (1,2):
            y = raw.loc[candidates, f'NRS{rep}']
            if np.ptp(y) == 0:
                raise ValueError('Zero-range replicate edit neighborhood')
            for row in group.itertuples():
                oriented = row.direction*y
                uniform_regret = (oriented.max()-oriented.mean())/np.ptp(oriented)
                selected_y = raw.loc[row.selected, f'NRS{rep}']
                selected_regret = (oriented.max()-row.direction*selected_y)/np.ptp(oriented)
                records.append(dict(parent=parent, composition=str(comp_key(parent)),
                    replicate=rep, model=row.model, direction=row.direction, selected=row.selected,
                    regret_gain=uniform_regret-selected_regret,
                    oriented_nrs_change=row.direction*(selected_y-raw.loc[parent, f'NRS{rep}'])))
    results = pd.DataFrame(records)
    compositions = sorted(results.composition.unique())
    rng = np.random.default_rng(20260921)
    draws = rng.integers(0,len(compositions),(2000,len(compositions)))
    summary = {'scope': 'post hoc consistency of aggregate-derived choices in constituent replicates',
               'parents': int(results.parent.nunique()), 'composition_classes': len(compositions),
               'removed_low_count_parents': removed, 'replicates': {}}
    for rep in (1,2):
        table = results[results.replicate == rep]
        values = {}
        models = {}
        for name, group in table.groupby('model'):
            means = group.groupby('composition')[['regret_gain','oriented_nrs_change']].mean().reindex(compositions)
            values[name] = means.regret_gain.to_numpy()
            models[name] = {'regret_gain_over_uniform': float(means.regret_gain.mean()),
                'gain_ci': np.quantile(values[name][draws].mean(1),[.025,.975]).tolist(),
                'oriented_nrs_change': float(means.oriented_nrs_change.mean()),
                'by_direction': {str(direction): float(g.groupby('composition').regret_gain.mean().mean())
                                 for direction,g in group.groupby('direction')}}
        delta = values['position_pair']-values['kmer123']
        summary['replicates'][str(rep)] = {'models':models,
            'pair_minus_kmer123_gain': float(delta.mean()),
            'pair_minus_kmer123_ci': np.quantile(delta[draws].mean(1),[.025,.975]).tolist()}
    write_new(OUT / 'raw_swap_evaluation.csv', results.to_csv(index=False,lineterminator='\n').encode())
    write_json(OUT / 'raw_swap_result.json', summary)
    print(json.dumps(summary,indent=2),flush=True)


if __name__ == '__main__':
    run()
