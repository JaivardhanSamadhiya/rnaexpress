"""Pure fixed specification and pool arithmetic; standard library only."""
import hashlib
import json
import math

TRACKS = ['base', 'raw', 'ordinary_raw', 'physical', 'combined']
SHAPES = dict(zip(TRACKS, [246, 258, 274, 260, 276]))
ELIGIBLE = ['physical', 'combined']
INCREMENTAL = {'physical': ['raw'], 'combined': ['ordinary_raw', 'physical']}
ENDPOINT_SIGNS = {'projection': 1., 'nuclear_cytoplasmic': -1.}
RAW_NAMES = ([f'delta_log1p_global_GQ_boxes_layers_{i}' for i in range(2, 8)] +
             [f'delta_log1p_changed_intersecting_GQ_boxes_layers_{i}' for i in range(2, 8)])
PHYSICS_NAMES = ['delta_G_on_minus_off_kcal_mol', 'delta_approximate_modeled_global_probability_at_least_one_GQ']
SPEC = {'version': 'global_GQ_potential_v1_observed_development', 'raw_feature_names': RAW_NAMES,
    'physics_feature_names': PHYSICS_NAMES, 'layers': [2, 3, 4, 5, 6, 7],
    'linker_lengths': [1, 15], 'boxes': 'all complete four-tract arrangements; overlapping boxes counted separately',
    'local': 'whole occupied half-open box, including linkers, intersects at least one declared changed coordinate',
    'transformation': 'log1p each allele count before mutant-minus-parent subtraction',
    'physics': 'exact reviewed backend.measure; fresh off and on PF per unique encoded allele',
    'physics_not_local_occupancy': True, 'probability_precision': 'approximate from rounded native returned ensemble energies; rare positives can round to zero',
    'ordinary_control': 'exact committed NEXT 262-column matrix; no refolding or modifications',
    'endpoint_signs': ENDPOINT_SIGNS, 'sign_application': 'supervised labels and predicted utility only; original evaluation truth unchanged',
    'shapes': SHAPES, 'eligible_tracks': ELIGIBLE, 'incremental_controls': INCREMENTAL,
    'rows': 26258, 'unique_encoded_alleles': 18220, 'lengths': [46, 150, 190, 260],
    'seed': 20261007, 'penalties': [.005, .05, .5], 'scaling': 'source-only pair RMS',
    'threads': 1, 'fresh_fits': 200, 'no_in_cell_occupancy_or_new_method_claim': True}

def spec_hash():
    return hashlib.sha256(json.dumps(SPEC, sort_keys=True, allow_nan=False).encode()).hexdigest()

def sequence_hash(sequence):
    return hashlib.sha256(sequence.encode('ascii')).hexdigest()

def positions_key(positions):
    return ','.join(str(int(p)) for p in positions)

def request_hash(requested):
    return hashlib.sha256(json.dumps([positions_key(p) for p in requested], separators=(',', ':')).encode()).hexdigest()

def request_plan(rows):
    """Exact substitution requests; no outcomes, filters or length rescaling."""
    alleles, row_positions = {}, []
    for row in rows:
        parent, mutant = row['parent_sequence'], row['mutant_sequence']
        assert len(parent) == len(mutant) and set(parent + mutant) <= set('ACGT')
        positions = tuple(i for i, (a, b) in enumerate(zip(parent, mutant)) if a != b)
        assert positions, 'Every admitted row must be an actual aligned substitution'
        row_positions.append(positions)
        for sequence in (parent, mutant):
            alleles.setdefault(sequence, set()).add(positions)
    return {s: sorted(values) for s, values in alleles.items()}, row_positions

def count_pools(patterns, length, requested):
    """Count each arrangement once globally and once per intersecting request."""
    assert all(p and tuple(sorted(set(p))) == tuple(p) and min(p) >= 0 and max(p) < length for p in requested)
    global_counts = [0] * 6
    local_counts = [[0] * 6 for _ in requested]
    for start, end, layers, linkers in patterns:
        assert 0 <= start < end <= length and 2 <= layers <= 7
        assert len(linkers) == 3 and all(1 <= x <= 15 for x in linkers)
        assert end - start == 4 * layers + sum(linkers)
        global_counts[layers - 2] += 1
        for index, positions in enumerate(requested):
            if any(start <= p < end for p in positions):
                local_counts[index][layers - 2] += 1
    return global_counts, local_counts

def transformed_counts(counts):
    assert len(counts) == 6 and all(isinstance(v, int) and v >= 0 for v in counts)
    return [math.log1p(v) for v in counts]

def delta_blocks(parent_global, parent_local, parent_physics, mutant_global, mutant_local, mutant_physics):
    raw = [b - a for a, b in zip(parent_global + parent_local, mutant_global + mutant_local)]
    physics = [b - a for a, b in zip(parent_physics, mutant_physics)]
    assert len(raw) == 12 and len(physics) == 2 and all(math.isfinite(v) for v in raw + physics)
    return raw, physics

def select_index(values):
    assert len(values) == 3 and all(math.isfinite(v) for v in values)
    return next(i for i, v in enumerate(values) if v <= min(values) + 1e-12)

def incremental_checks(gains):
    assert len(gains) == 4 and all(math.isfinite(v) for v in gains)
    best = max(range(4), key=lambda i: gains[i])
    return {'macro_incremental_gain_at_least_0_01': sum(gains) / 4 >= .01,
            'incremental_leave_best_assay_out_positive': sum(v for i, v in enumerate(gains) if i != best) / 3 > 0}
