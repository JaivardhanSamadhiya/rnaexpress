"""Synthetic-only certification of whole-interval opening on the existing model.

No project candidate/feature/outcome reader or supervised estimator is exposed.
"""

from pathlib import Path
import argparse
import hashlib
import json
import math
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'data/interim/mechanism_v2/runtime'
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
import numpy as np
import RNA
from src.generalization_next_20261007.route_structure import model_details, partition

NS = 'generalization_joint_accessibility_20261007'
SRC, OUT, REP, ART = [ROOT / folder / NS for folder in ('src', 'results', 'reports', 'artifacts')]
ABS_TOL = 1e-6
REL_TOL = 1e-5
MAX_INTERVAL = 25
GAS_CONSTANT_KCAL = .00198717
SEED = 20261007
SPEC = {
    'version': 'synthetic_global_joint_accessibility_feasibility_v1',
    'runtime': 'ViennaRNA2.7.2 already cached; no installs/downloads',
    'global_model': 'exact frozen NEXT model_details and partition helper',
    'candidate_algorithm': 'probs_window OPTION_WINDOW, window_size=n, max_bp_span=n, PROBS_WINDOW_UP, max_length25',
    'candidate_coordinate': 'callback i is 1-based interval end; vector[k] represents i-k+1..i; save at zero-based start i-k',
    'reference': 'fresh constrained and unconstrained global PF with each requested site forced unpaired in every loop',
    'reference_probability': 'exp(-(Gconstrained-Gfree)/(R*T)), R=.00198717 kcal/mol/K,T310.15K',
    'absolute_tolerance': ABS_TOL, 'relative_tolerance': REL_TOL,
    'acceptance': 'all fixed synthetic intervals pass both finite bounds and numpy.isclose(abs1e-6,rel1e-5); no outcome-selected tolerance',
    'production_authorized': False, 'fitting_authorized': False,
    'probability_is_occupancy': False, 'threads': 1,
}
SYNTHETIC_CASES = (
    ('allA32', 'A' * 32),
    ('hairpin9', 'GGGAAACCC'),
    ('hairpin32', 'GGGGGGGGGG' + 'A' * 12 + 'CCCCCCCCCC'),
    ('alternating32', 'GCGCAU' * 5 + 'GC'),
    ('mixed32', 'ACGUGCAUGCAGGGAAACCCUACGUAACGUGCA'),
)
ALLELE_COUNTS = {46: 742, 150: 9318, 190: 3991, 260: 4169}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_json(path, obj):
    path = Path(path).resolve()
    if not any(path.is_relative_to(root) for root in (OUT, REP, ART)):
        raise PermissionError('Only this additive feasibility namespace may be written')
    payload = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n').encode('utf8')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError('Preserving earlier result ' + str(path))
    else:
        path.write_bytes(payload)


def normalize(sequence):
    text = str(sequence).upper().replace('T', 'U')
    if not text or set(text) - set('ACGU'):
        raise ValueError('Exact nonempty RNA sequence required')
    return text


def joint_probabilities(sequence, maximum=MAX_INTERVAL):
    """Array[start,width]; impossible intervals stay NaN, never zero padding."""
    sequence = normalize(sequence)
    n = len(sequence)
    maximum = min(int(maximum), n)
    if not 1 <= maximum <= MAX_INTERVAL:
        raise ValueError('Feasibility interval lengths are1..25 only')
    md = model_details()
    md.window_size = n
    md.max_bp_span = n
    compound = RNA.fold_compound(sequence, md, RNA.OPTION_WINDOW)
    matrix = np.full((n, maximum + 1), np.nan, dtype=np.float64)
    ends = set()

    def collect(values, size, end1, maximum_arg, flags, data):
        if not (flags & RNA.PROBS_WINDOW_UP) or end1 in ends or not 1 <= end1 <= n:
            raise AssertionError('Unexpected callback or repeated interval end')
        ends.add(end1)
        for width in range(1, min(end1, maximum) + 1):
            value = float(values[width])
            if not math.isfinite(value) or not -1e-10 <= value <= 1 + 1e-10:
                raise ArithmeticError('Invalid interval opening probability')
            matrix[end1 - width, width] = value

    if compound.probs_window(maximum, RNA.PROBS_WINDOW_UP, collect) != 1:
        raise RuntimeError('ViennaRNA interval callback failed')
    if ends != set(range(1, n + 1)):
        raise AssertionError('Callback omitted interval ends')
    for width in range(1, maximum + 1):
        if not np.isfinite(matrix[:n - width + 1, width]).all():
            raise AssertionError('Valid interval missing')
    return matrix


def constrained_probability(sequence, start, width):
    sequence = normalize(sequence)
    if not 0 <= start < len(sequence) or not 1 <= width <= len(sequence) - start:
        raise ValueError('Valid contiguous interval required')
    _, free_energy = partition(sequence)
    _, constrained_energy = partition(sequence, range(start, start + width))
    return math.exp(-(constrained_energy - free_energy) /
                    (GAS_CONSTANT_KCAL * (273.15 + 37.)))


def check_fixed_intervals():
    records = []
    max_abs, max_rel = 0., 0.
    for case_id, sequence in SYNTHETIC_CASES:
        matrix = joint_probabilities(sequence)
        for width in range(1, min(len(sequence), MAX_INTERVAL) + 1):
            starts = sorted({0, (len(sequence) - width) // 2, len(sequence) - width})
            for start in starts:
                candidate = float(matrix[start, width])
                reference = constrained_probability(sequence, start, width)
                absolute = abs(candidate - reference)
                relative = absolute / max(reference, 1e-300)
                passed = bool(np.isclose(candidate, reference, atol=ABS_TOL, rtol=REL_TOL))
                records.append({'case': case_id, 'start0': start, 'width': width,
                                'candidate': candidate, 'reference': reference,
                                'abs_error': absolute, 'pass': passed})
                max_abs, max_rel = max(max_abs, absolute), max(max_rel, relative)
    return records, max_abs, max_rel


def benchmark_sequences():
    rng = random.Random(SEED)
    result = []
    for length in (46, 150, 190, 260):
        for index in range(4):
            text = ''.join(rng.choice('ACGU') for _ in range(length))
            if length == 46:
                text = 'GCCCACAAGUAUCACUAAGC' + text[20:26] + 'AUCAUAAUCAGCCAUACCAC'
            result.append((length, index, text))
    return result


def benchmark():
    records = []
    for length, index, sequence in benchmark_sequences():
        start = time.perf_counter()
        probabilities = joint_probabilities(sequence)
        elapsed = time.perf_counter() - start
        records.append({'length': length, 'index': index, 'sequence_sha256': hashlib.sha256(sequence.encode()).hexdigest(),
                        'elapsed_seconds': elapsed, 'table_bytes': probabilities.nbytes})
    medians = {str(length): float(np.median([row['elapsed_seconds'] for row in records if row['length'] == length]))
               for length in ALLELE_COUNTS}
    expected = sum(ALLELE_COUNTS[length] * medians[str(length)] for length in ALLELE_COUNTS)
    return {'synthetic_records': records, 'median_seconds_by_length': medians,
            'synthetic_fold_only_18220_allele_estimate_seconds': expected,
            'planning_margin_50_percent_seconds': 1.5 * expected,
            'estimate_excludes': ['PFM scanning', 'projection', 'cache hashing and IO', 'row assembly', 'concurrent load'],
            'actual_project_alleles_read': False}


def receipt_sources():
    paths = list(SRC.glob('*.py')) + [
        ROOT / 'src/generalization_next_20261007/route_structure.py',
        ROOT / 'src/generalization_rbp_20261007/scoring.py',
        ROOT / 'artifacts/generalization_rbp_20261007/direct_human_manifest.json',
        ROOT / 'reports/generalization_joint_accessibility_20261007/feasibility_protocol.md',
        Path(RNA.__file__), Path(np.__file__),
    ]
    paths.extend(Path(RNA.__file__).parent.glob('_RNA*.pyd'))
    return {str(path.relative_to(ROOT)): sha256(path) for path in sorted(set(paths))}


def run():
    if RNA.__version__ != '2.7.2':
        raise RuntimeError('Exact existing ViennaRNA2.7.2 required')
    records, abs_error, rel_error = check_fixed_intervals()
    structured = joint_probabilities('GGGAAACCC')
    joint = float(structured[0, 4])
    marginal_mean = float(structured[:4, 1].mean())
    difference_pass = joint < marginal_mean - 1e-3
    result = {'status': 'PASS' if all(row['pass'] for row in records) and difference_pass else 'FAIL',
              'spec': SPEC, 'runtime_version': RNA.__version__, 'numpy_version': np.__version__,
              'interval_checks': records, 'maximum_absolute_error': abs_error, 'maximum_relative_error': rel_error,
              'joint_vs_mean_example': {'sequence': 'GGGAAACCC', 'start0': 0, 'width': 4,
                                        'joint': joint, 'mean_marginal': marginal_mean, 'pass': difference_pass},
              'benchmark': benchmark(), 'source_sha256': receipt_sources(),
              'project_outcomes_read': False, 'project_feature_production': False, 'supervised_fit': False}
    path = OUT / 'synthetic_feasibility_receipt.json'
    save_json(path, result)
    print(json.dumps({'status': result['status'], 'interval_checks': len(records), 'max_abs_error': abs_error,
                      'joint_vs_mean': result['joint_vs_mean_example'], 'benchmark': result['benchmark']['median_seconds_by_length'],
                      'estimate_seconds': result['benchmark']['planning_margin_50_percent_seconds'], 'receipt': str(path)}), flush=True)
    if result['status'] != 'PASS':
        raise RuntimeError('Fixed whole-site equivalence test failed; no silent ensemble substitution')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['synthetic-only'])
    parser.parse_args()
    run()
