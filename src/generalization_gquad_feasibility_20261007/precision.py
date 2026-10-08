"""Additive fixed synthetic precision check; preserves all earlier receipts."""
import json
import math
from . import backend as b


def run():
    b.environment()
    b.source_guard()
    rows = []
    # Full fixed roster, not favorable case selection: linker1 through15.
    for length in range(1, 16):
        sequence = 'GG' + ('A' * length + 'GG') * 3
        patterns = list(b.gq_patterns(sequence))
        assert patterns == [(0, len(sequence), 2, (length, length, length))]
        fc = b.RNA.fold_compound(sequence, b.model_details(1), b.RNA.OPTION_MFE | b.RNA.OPTION_PF)
        linkers = b.RNA.intArray(3)
        for index in range(3):
            linkers[index] = length
        weight = float(b.RNA.exp_E_gquad(2, linkers, fc.exp_params))
        # Exactly one admissible GQ and zero ordinary pairs: Z=1+weight.
        reference_probability = weight / (1 + weight)
        kt = float(fc.exp_params.kT) / 1000.
        reference_energy = -kt * math.log1p(weight)
        actual = b.measure(sequence)
        actual_probability = actual['modeled_at_least_one_GQ_probability']
        assert math.isclose(actual_probability, reference_probability,
            abs_tol=b.EVENT_ABS_TOL, rel_tol=b.EVENT_REL_TOL)
        assert math.isclose(actual['on']['G_kcal_mol'], reference_energy,
            abs_tol=b.EVENT_ABS_TOL, rel_tol=b.EVENT_REL_TOL)
        rows.append({'equal_linker_length': length, 'sequence': sequence,
            'reference_partition': 'exactly1+nativeGQBoltzmannWeight', 'Boltzmann_weight': weight,
            'reference_probability_stable': reference_probability,
            'native_energy_ratio_probability': actual_probability,
            'absolute_probability_error': abs(actual_probability - reference_probability),
            'reference_energy_stable': reference_energy,
            'native_on_energy': actual['on']['G_kcal_mol'],
            'native_probability_rounded_to_zero': actual_probability == 0. and reference_probability > 0.})
    receipt = {'status': 'PASS_FIXED_ABSOLUTE_PRECISION', 'synthetic_cases': len(rows),
        'fixed_roster': 'one2layerGQ,all15equal-linker-lengths1..15; A/G-only; no ordinary pairs',
        'same_declared_tolerances': {'absolute': b.EVENT_ABS_TOL, 'relative': b.EVENT_REL_TOL},
        'rows': rows, 'maximum_absolute_probability_error': max(row['absolute_probability_error'] for row in rows),
        'rounded_to_zero_cases': sum(row['native_probability_rounded_to_zero'] for row in rows),
        'relative_precision_for_very_rare_events_not_certified': True,
        'scope': 'Returned energy contrasts can round tiny event masses to0; do not claim exact local or rare-event occupancy',
        'files': {path.relative_to(b.ROOT).as_posix(): b.sha256(path) for path in
            (b.SRC / 'backend.py', b.SRC / 'precision.py', b.REP / 'feasibility_protocol.md', b.OUT / 'backend_feasibility_receipt.json')},
        'project_alleles_folded': 0, 'labels_read': False, 'models_read': False,
        'models_fit': 0, 'project_production_authorized': False}
    b.save_json(b.OUT / 'single_event_precision_receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'cases': len(rows),
        'max_absolute_error': receipt['maximum_absolute_probability_error'],
        'rounded_to_zero_cases': receipt['rounded_to_zero_cases']}))


if __name__ == '__main__':
    run()
