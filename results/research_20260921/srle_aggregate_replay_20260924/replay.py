"""Standard-library arithmetic replay of existing anonymized SRLE aggregates.

This module fits no models, reads no sequence-level measurements and generates
no interventions. The release copies this file as replay.py beside its inputs.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math

MODELS = ('composition', 'kmer123', 'position_additive', 'position_pair')
MEMBERS = ('README.md', 'group_metrics.csv', 'bootstrap_indices.csv',
           'expected_summary.json', 'provenance.json', 'evidence_ledger.md',
           'replay.py')
TOLERANCE = 1e-12


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_integrity(directory):
    manifest = json.loads((directory / 'integrity.json').read_text())
    if set(manifest['files']) != set(MEMBERS):
        raise ValueError('Unexpected package manifest members')
    for name, expected in manifest['files'].items():
        if sha256(directory / name) != expected:
            raise ValueError('Package hash mismatch: ' + name)
    return manifest


def quantile(values, q):
    """Linear interpolation, matching the archived numpy quantile convention."""
    ordered = sorted(values)
    location = (len(ordered) - 1) * q
    lower = math.floor(location)
    upper = math.ceil(location)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (location - lower)


def mean(values):
    values = list(values)
    return math.fsum(values) / len(values)


def read_groups(path):
    groups = {}
    fields = ['class_id', 'replicate', 'model', 'direction', 'record_count',
              'mean_regret_gain', 'mean_oriented_nrs_change']
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != fields:
            raise ValueError('Unexpected aggregate schema')
        for row in reader:
            key = (int(row['class_id']), int(row['replicate']), row['model'],
                   int(row['direction']))
            if (key in groups or key[0] not in range(60) or key[1] not in (1, 2)
                    or key[2] not in MODELS or key[3] not in (-1, 1)):
                raise ValueError('Duplicate or invalid aggregate key')
            count = int(row['record_count'])
            gain = float(row['mean_regret_gain'])
            change = float(row['mean_oriented_nrs_change'])
            if count < 1 or not all(math.isfinite(v) for v in (gain, change)):
                raise ValueError('Invalid aggregate values')
            if not -1 - TOLERANCE <= gain <= 1 + TOLERANCE:
                raise ValueError('Normalized regret gain outside range')
            groups[key] = (count, gain, change)
    if len(groups) != 60 * 2 * 4 * 2:
        raise ValueError('Incomplete aggregate coverage')
    for class_id in range(60):
        counts = {groups[class_id, rep, model, direction][0]
                  for rep in (1, 2) for model in MODELS for direction in (-1, 1)}
        if len(counts) != 1:
            raise ValueError('Models, replicates or directions have different cohorts')
    parents = sum(groups[c, 1, 'composition', 1][0] for c in range(60))
    if parents != 592:
        raise ValueError('Archived parent count differs')
    return groups


def read_draws(path):
    with path.open(newline='', encoding='utf-8') as stream:
        draws = [[int(v) for v in row] for row in csv.reader(stream)]
    if (len(draws) != 2000 or any(len(row) != 60 for row in draws)
            or any(v not in range(60) for row in draws for v in row)):
        raise ValueError('Invalid archived bootstrap indices')
    return draws


def interval(values, draws):
    boot = [mean(values[i] for i in row) for row in draws]
    return [quantile(boot, .025), quantile(boot, .975)]


def calculate(groups, draws):
    result = {'composition_classes': 60, 'parents': 592,
              'removed_low_count_parent_count': 17,
              'scope': 'post hoc consistency of aggregate-derived choices in constituent replicates',
              'replicates': {}}
    for rep in (1, 2):
        vectors, models = {}, {}
        for model in MODELS:
            gains, changes = [], []
            for class_id in range(60):
                rows = [groups[class_id, rep, model, d] for d in (-1, 1)]
                total = sum(row[0] for row in rows)
                gains.append(math.fsum(row[0] * row[1] for row in rows) / total)
                changes.append(math.fsum(row[0] * row[2] for row in rows) / total)
            vectors[model] = gains
            models[model] = {'regret_gain_over_uniform': mean(gains),
                             'gain_ci': interval(gains, draws),
                             'oriented_nrs_change': mean(changes),
                             'by_direction': {str(d): mean(groups[c, rep, model, d][1]
                                                          for c in range(60))
                                              for d in (-1, 1)}}
        delta = [a - b for a, b in zip(vectors['position_pair'], vectors['kmer123'])]
        result['replicates'][str(rep)] = {
            'models': models, 'pair_minus_kmer123_gain': mean(delta),
            'pair_minus_kmer123_ci': interval(delta, draws)}
    return result


def compare(actual, expected, path='root'):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError('Summary schema differs at ' + path)
        return [v for k in expected for v in compare(actual[k], expected[k], path + '.' + k)]
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError('Summary length differs at ' + path)
        return [v for i, e in enumerate(expected) for v in compare(actual[i], e, path + '.' + str(i))]
    if isinstance(expected, (int, float)):
        difference = abs(actual - expected)
        if not math.isfinite(difference) or difference > TOLERANCE:
            raise ValueError('Arithmetic differs at ' + path)
        return [difference]
    if actual != expected:
        raise ValueError('Summary label differs at ' + path)
    return []


def replay(directory):
    directory = Path(directory).resolve()
    verify_integrity(directory)
    groups = read_groups(directory / 'group_metrics.csv')
    draws = read_draws(directory / 'bootstrap_indices.csv')
    actual = calculate(groups, draws)
    expected = json.loads((directory / 'expected_summary.json').read_text())
    differences = compare(actual, expected)
    return {'status': 'PASS', 'aggregate_rows': len(groups),
            'bootstrap_draws': len(draws), 'numeric_values_compared': len(differences),
            'max_absolute_difference': max(differences), 'tolerance': TOLERANCE,
            'scope': 'Arithmetic replay only; no new experiment or model fitting.',
            'summary': actual}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path, default=Path(__file__).resolve().parent)
    print(json.dumps(replay(parser.parse_args().directory), indent=2, allow_nan=False))
