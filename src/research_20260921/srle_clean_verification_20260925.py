"""Clean replay of existing predictions and portable aggregates; no fitting."""
from .evidence_io_20260925 import ROOT, ART, sha256, read_json, save_json, save_csv
from pathlib import Path
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
import numpy as np
import pandas as pd

OUT = ROOT / 'results/research_20260921'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def regret(y, pred, ids):
    return np.mean([(max(sign*y) - sign*y[np.lexsort((ids, -sign*pred))[0]]) / np.ptp(y) for sign in (1, -1)])


def replay_predictions():
    inputs = ['robustness_predictions.csv', 'robustness_result.json', 'pilot_a_predictions.csv', 'pilot_a_result.json']
    receipt = read_json(OUT / 'checkpoint_receipt.json')['artifact_hashes']
    for name in inputs:
        rel = 'results/research_20260921/' + name
        require(sha256(OUT / name) == receipt[rel], 'Historical predictions/result changed')
    frame = pd.read_csv(OUT / inputs[0], float_precision='round_trip')
    expected = read_json(OUT / inputs[1])
    require(len(frame) == 4096 and frame.kmer.nunique() == 4096, 'Prediction identity')
    keys = [tuple(s.count(b) for b in 'ACGT') for s in frame.kmer]
    y, seq, test = frame.nrs.to_numpy(), frame.kmer.to_numpy(), frame.test.to_numpy()
    indices = [np.array([i for i,k in enumerate(keys) if k == group and test[i]]) for group in sorted(set(keys))
               if sum(k == group and test[i] for i,k in enumerate(keys)) >= 2
               and sum(k == group and not test[i] for i,k in enumerate(keys)) >= 2]
    require(len(indices) == 70 and sum(map(len, indices)) == 855, 'Prediction cohort changed')
    models = ('composition', 'position_additive', 'position_pair', 'kmer123')
    sse = {m: np.array([np.sum((y[ix]-frame[m].to_numpy()[ix])**2) for ix in indices]) for m in models}
    rng = np.random.default_rng(20260921)
    draws = rng.integers(0, 70, (2000, 70))
    errors, reconstructed, rows = [], {}, []
    def check(actual, target):
        diff = float(np.max(np.abs(np.array(actual)-np.array(target))))
        require(np.isfinite(diff) and diff <= 1e-12, 'Prediction metric replay failed')
        errors.append(diff)
    for model in models:
        gains = np.array([regret(y[ix], frame.composition.to_numpy()[ix], seq[ix]) -
                          regret(y[ix], frame[model].to_numpy()[ix], seq[ix]) for ix in indices])
        actual = {'error_reduction_vs_composition': float(1-sse[model].sum()/sse['composition'].sum()),
            'error_reduction_ci': np.quantile(1-sse[model][draws].sum(1)/sse['composition'][draws].sum(1), [.025,.975]).tolist(),
            'regret_gain': float(gains.mean())}
        for metric in actual:
            check(actual[metric], expected['models'][model][metric])
        reconstructed[model] = actual
        rows += [{'anonymous_class': c, 'model': model, 'test_rows': len(indices[c]), 'squared_error_sum': float(sse[model][c]),
                  'regret_gain_over_composition': float(gains[c])} for c in range(70)]
    for model in ('position_additive', 'kmer123'):
        ratio = 1-sse['position_pair'].sum()/sse[model].sum()
        ci = np.quantile(1-sse['position_pair'][draws].sum(1)/sse[model][draws].sum(1), [.025,.975])
        check(ratio, expected['pair_vs_baselines'][model]['relative_error_reduction'])
        check(ci, expected['pair_vs_baselines'][model]['ci'])
    # Restore the original permutation-before-bootstrap RNG stream, without refitting.
    pilot = pd.read_csv(OUT / 'pilot_a_predictions.csv', float_precision='round_trip')
    require(np.array_equal(pilot.kmer, seq) and np.array_equal(pilot.nrs, y), 'Pilot alignment')
    require(np.max(np.abs(pilot.order_prediction-frame.position_pair)) <= 1e-12, 'Pair predictions changed')
    rng = np.random.default_rng(20260921)
    perm = []
    pred, base = pilot.order_prediction.to_numpy(), pilot.composition_prediction.to_numpy()
    for _ in range(999):
        numerator = denominator = 0.
        for ix in indices:
            shuffled = rng.permutation(y[ix])
            numerator += float(np.sum((shuffled-pred[ix])**2))
            denominator += float(np.sum((shuffled-base[ix])**2))
        perm.append(1-numerator/denominator)
    draw = rng.integers(0, 70, (2000, 70))
    pilot_expected = read_json(OUT / 'pilot_a_result.json')
    check((1+sum(v >= reconstructed['position_pair']['error_reduction_vs_composition'] for v in perm))/1000,
          pilot_expected['conditional_test_permutation_p'])
    check(np.quantile(1-sse['position_pair'][draw].sum(1)/sse['composition'][draw].sum(1), [.025,.975]),
          pilot_expected['residual_squared_error_reduction_ci'])
    gains = np.array([r['regret_gain_over_composition'] for r in rows if r['model'] == 'position_pair'])
    check(np.quantile(gains[draw].mean(1), [.025,.975]), pilot_expected['regret_gain_ci'])
    save_csv('srle_prediction_class_metrics.csv', rows)
    return {'status': 'PASS', 'cohort_classes': 70, 'cohort_rows': 855, 'models': reconstructed,
        'max_absolute_difference': max(errors), 'checked_scalar_or_array_fields': len(errors),
        'scope': 'Saved prediction and split replay, including original RNG stream; no refitting',
        'inputs': {name: sha256(OUT / name) for name in inputs}}


def standalone_replays():
    output = {}
    for filename, expected in {
        'srle_aggregate_replay_20260924.zip': 'd81cdcd9f6ecdbbd9d98806514de5931bfec0b0f8bcbbaea808af06cd3c1a7f3',
        'srle_risk_replay_20260924.zip': 'b4f79a6d3483dcdf4f56e0bfdb9bf5f8899c2337c07bcdc663c3dd00d6a179bd',
    }.items():
        require(sha256(OUT / filename) == expected, 'Replay archive changed')
        parent = ROOT / 'data/interim/research_20260921'
        with tempfile.TemporaryDirectory(prefix='verified_replay_20260925_', dir=parent) as fresh:
            with zipfile.ZipFile(OUT / filename) as zipped:
                require(len(set(zipped.namelist())) == len(zipped.namelist()), 'Duplicate archive member')
                require(zipped.testzip() is None, 'Archive CRC')
                for member in zipped.infolist():
                    require(Path(member.filename).name == member.filename and not member.is_dir(), 'Unsafe member')
                    require(member.file_size < 2_000_000, 'Oversized member')
                    (Path(fresh) / member.filename).write_bytes(zipped.read(member))
            proc = subprocess.run([sys.executable, '-I', '-S', '-B', 'replay.py'], cwd=fresh,
                capture_output=True, text=True, encoding='utf-8', check=True, timeout=60)
            require(not proc.stderr, 'Unexpected replay stderr')
            output[filename] = json.loads(proc.stdout)
    return output


def preservation():
    results = {}
    for manifest in sorted(OUT.glob('*freeze.json')) + [OUT / 'tracked_source_snapshot.json']:
        obj = read_json(manifest)
        files = obj.get('files', {})
        require(files, 'Empty preservation manifest')
        changed = [p for p,h in files.items() if sha256(ROOT / p) != h]
        require(not changed, 'Frozen source changed: ' + str(changed))
        results[manifest.name] = {'checked': len(files), 'changed': changed}
    return results


def run():
    predictions = replay_predictions()
    replays = standalone_replays()
    preserved = preservation()
    suite = unittest.TestSuite()
    modules = sorted(p.stem for p in Path(__file__).parent.glob('test_*.py'))
    for name in modules:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module('src.research_20260921.' + name)))
    import io
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=1).run(suite)
    from .evidence_io_20260925 import save
    save('scoped_tests.txt', log.getvalue().encode())
    require(result.wasSuccessful(), log.getvalue())
    receipt = {'status': 'PASS', 'prediction_replay': predictions, 'portable_replays': replays,
               'preservation': preserved, 'tests': result.testsRun, 'test_modules': modules,
               'python': sys.version, 'numpy': np.__version__, 'pandas': pd.__version__,
               'models_fit': 0, 'new_outcomes': 0, 'script_sha256': sha256(Path(__file__)),
               'scope': 'Computation verification, not an independent experiment or training reproduction'}
    save_json('clean_verification.json', receipt)
    print(json.dumps({'status': 'PASS', 'tests': result.testsRun, 'prediction_max_error': predictions['max_absolute_difference'],
        'replays': {k:{x:v[x] for x in v if x not in ('summary','inputs')} for k,v in replays.items()},
        'preservation_manifests': len(preserved)}, indent=2))


if __name__ == '__main__':
    run()
