"""Prespecified longer synthetic global-equivalence checks, unchanged tolerance."""
from .common import *
from .feasibility import benchmark_sequences, joint_probabilities, constrained_probability, ABS_TOL, REL_TOL

def run():
    records = []
    for length, index, sequence in benchmark_sequences():
        if index != 0:
            continue
        table = joint_probabilities(sequence)
        for width in (4, 6, 12, 25):
            for start in (0, (length - width) // 2, length - width):
                candidate = float(table[start, width]); reference = constrained_probability(sequence, start, width)
                records.append({'length': length, 'width': width, 'start0': start, 'candidate': candidate,
                    'reference': reference, 'absolute_error': abs(candidate - reference),
                    'pass': bool(np.isclose(candidate, reference, atol=ABS_TOL, rtol=REL_TOL))})
    assert len(records) == 48
    status = 'PASS' if all(record['pass'] for record in records) else 'FAIL'
    jsave(OUT / 'synthetic_long_interval_validation.json', {'status': status, 'interval_checks': records,
        'absolute_tolerance': ABS_TOL, 'relative_tolerance': REL_TOL,
        'maximum_absolute_error': max(row['absolute_error'] for row in records),
        'project_alleles_read': False, 'project_outcomes_read': False, 'models_fit': 0,
        'source_sha256': sha256(Path(__file__)), 'short_validation_sha256': sha256(OUT / 'synthetic_feasibility_receipt.json')})
    print('Long synthetic global-equivalence', status, '48 checks', flush=True)
    assert status == 'PASS', 'Stop: do not relax tolerance or silently change the ensemble'

if __name__ == '__main__':
    run()
