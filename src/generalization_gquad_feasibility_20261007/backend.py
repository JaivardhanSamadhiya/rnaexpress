"""Invented-sequence global-PF audit; deliberately no project data loader."""
from functools import lru_cache
from pathlib import Path
import base64
import csv
import hashlib
import io
import json
import math
import os
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'data/interim/mechanism_v2/runtime'
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
import RNA
from src.generalization_next_20261007.route_structure import model_details as next_model_details
from src.generalization_next_20261007.route_structure import partition as next_partition

NS = 'generalization_gquad_feasibility_20261007'
SRC, OUT, REP, ART = [ROOT / base / NS for base in ('src', 'results', 'reports', 'artifacts')]
ENERGY_ABS_TOL = 1e-6
API_REL_TOL = 1e-6
EVENT_ABS_TOL = 2e-6
EVENT_REL_TOL = 2e-5
LENGTHS = (46, 150, 190, 260)
SEED = 20261007
ALLELE_COUNTS = {46: 742, 150: 9318, 190: 3991, 260: 4169}  # prior metadata counts, not data reads
PARAM_NAMES = (
    'stack', 'hairpin', 'bulge', 'internal_loop', 'mismatchExt', 'mismatchI',
    'mismatchH', 'mismatchM', 'mismatch1nI', 'mismatch23I', 'dangle5', 'dangle3',
    'int11', 'int21', 'int22', 'ninio', 'MLbase', 'MLintern', 'MLclosing',
    'TerminalAU', 'DuplexInit', 'Tetraloop_E', 'Triloop_E', 'Hexaloop_E',
    'SaltStack', 'SaltLoop', 'SaltMLbase', 'SaltMLclosing', 'SaltDPXInit', 'lxc',
)
SPEC = {
    'version': 'synthetic_global_gquad_nesting_audit_v1', 'ViennaRNA': '2.7.2',
    'temperature_C': 37., 'parameters': 'explicit RNA Turner2004', 'dangles': 2,
    'min_loop_size': 3, 'GU_pairs': True, 'GU_closures': True, 'circular': False,
    'salt_M': 1.021, 'max_bp_span': -1, 'betaScale': 1.,
    'only_ensemble_difference': 'md.gquad=0 vs1',
    'event': 'at least one modeled intramolecular GQ anywhere in exact input',
    'event_formula_requires_unchanged_weight_nesting': True,
    'event_formula': '-expm1((G_on-G_off)/(native_exp_params.kT/1000))',
    'local_occupancy_from_bpp': False, 'in_cell_occupancy_claim': False,
    'energy_absolute_tolerance': ENERGY_ABS_TOL,
    'API_relative_tolerance': API_REL_TOL,
    'event_absolute_tolerance': EVENT_ABS_TOL,
    'event_relative_tolerance': EVENT_REL_TOL,
    'synthetic_lengths': LENGTHS, 'random_seed': SEED, 'threads': 1,
    'project_production_authorized': False, 'supervised_fitting_authorized': False,
}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save_json(path, obj):
    path = Path(path).resolve()
    if not any(path.is_relative_to(folder) for folder in (OUT, ART, REP)):
        raise PermissionError('Only new feasibility outputs may be written')
    payload = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError('Preserving prior feasibility receipt')
    else:
        path.write_bytes(payload)


def environment():
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        if os.environ.get(name) != '1':
            raise RuntimeError('One-thread feasibility environment required: ' + name)
    if RNA.__version__ != '2.7.2':
        raise RuntimeError('Existing ViennaRNA2.7.2 required')


def normalize(sequence):
    value = str(sequence).upper().replace('T', 'U')
    if not value or set(value) - set('ACGU'):
        raise ValueError('Nonempty exact RNA sequence required')
    return value


def model_details(gquad, compute_bpp=0):
    if gquad not in (0, 1) or compute_bpp not in (0, 1):
        raise ValueError('Exactly gquad0/1 and compute_bpp0/1 required')
    md = next_model_details()
    # The original NEXT model has GQ disabled; do not silently inherit a changed default.
    if md.gquad != 0:
        raise RuntimeError('Original NEXT ordinary-structure default changed')
    md.gquad, md.compute_bpp = int(gquad), int(compute_bpp)
    return md


def fold(sequence, gquad, compute_bpp=0):
    sequence = normalize(sequence)
    fc = RNA.fold_compound(sequence, model_details(gquad, compute_bpp), RNA.OPTION_MFE | RNA.OPTION_PF)
    mfe_structure, mfe_energy = fc.mfe()
    fc.exp_params_rescale(mfe_energy)
    pf_structure, ensemble_energy = fc.pf()
    energy, kt = float(ensemble_energy), float(fc.exp_params.kT) / 1000.
    if not math.isfinite(energy) or not math.isfinite(kt) or kt <= 0:
        raise ArithmeticError('Invalid native partition energy/kT')
    return fc, {'G_kcal_mol': energy, 'kT_kcal_mol': kt,
        'mfe_structure': mfe_structure, 'mfe_kcal_mol': float(mfe_energy),
        'pf_structure_annotation': pf_structure, 'pf_scale': float(fc.exp_params.pf_scale)}


def event_probability(g_on, g_off, kt):
    values = tuple(map(float, (g_on, g_off, kt)))
    if not all(math.isfinite(value) for value in values) or values[2] <= 0:
        raise ValueError('Finite energies and positive native kT required')
    value = -math.expm1((values[0] - values[1]) / values[2])
    if not -EVENT_ABS_TOL <= value <= 1 + EVENT_ABS_TOL:
        raise ArithmeticError('Nested-ensemble event out of fixed numerical bounds')
    # Only numerical roundoff is clipped. Source proof is required separately.
    return min(1., max(0., value))


def measure(sequence):
    off_fc, off = fold(sequence, 0)
    on_fc, on = fold(sequence, 1)
    if off['kT_kcal_mol'] != on['kT_kcal_mol']:
        raise AssertionError('Ensembles changed thermodynamic temperature')
    probability = event_probability(on['G_kcal_mol'], off['G_kcal_mol'], on['kT_kcal_mol'])
    return {'off': off, 'on': on, 'G_on_minus_off': on['G_kcal_mol'] - off['G_kcal_mol'],
        'modeled_at_least_one_GQ_probability': probability}


def delta(parent, mutant):
    parent, mutant = normalize(parent), normalize(mutant)
    if len(parent) != len(mutant):
        raise ValueError('Only corresponding-coordinate substitutions audited')
    if parent == mutant:
        return [0., 0.]
    a, b = measure(parent), measure(mutant)
    return [b['G_on_minus_off'] - a['G_on_minus_off'],
        b['modeled_at_least_one_GQ_probability'] - a['modeled_at_least_one_GQ_probability']]


def gq_patterns(sequence):
    """Independently enumerate all complete 4-tract GQ patterns in this model.

    Each pattern is an atomic, contiguous occupied box: its linkers have no
    recursively folded substructure in the Vienna model. This routine reads no
    native GQ dynamic-programming matrix.
    """
    sequence = normalize(sequence)
    n = len(sequence)
    for start in range(n - 10):
        for layers in range(2, 8):
            if start + 4 * layers + 3 > n or sequence[start:start + layers] != 'G' * layers:
                continue
            for a in range(1, 16):
                second = start + layers + a
                if second + 3 * layers + 2 > n or sequence[second:second + layers] != 'G' * layers:
                    continue
                for b in range(1, 16):
                    third = second + layers + b
                    if third + 2 * layers + 1 > n or sequence[third:third + layers] != 'G' * layers:
                        continue
                    for c in range(1, 16):
                        fourth = third + layers + c
                        end = fourth + layers
                        if end <= n and sequence[fourth:end] == 'G' * layers:
                            yield start, end, layers, (a, b, c)


def gq_only_partition(sequence):
    """Independent nonoverlapping-event grammar for A/G-only synthetic RNA."""
    sequence = normalize(sequence)
    if set(sequence) - set('AG'):
        raise ValueError('Reference excludes every ordinary canonical/GU pair')
    md = model_details(1)
    fc = RNA.fold_compound(sequence, md, RNA.OPTION_MFE | RNA.OPTION_PF)
    groups = [[] for _ in sequence]
    array = RNA.intArray(3)
    patterns = list(gq_patterns(sequence))
    native_rule_max_error = 0.
    for start, end, layers, linkers in patterns:
        for index, value in enumerate(linkers):
            array[index] = value
        weight = float(RNA.exp_E_gquad(layers, array, fc.exp_params))
        energy = float(RNA.E_gquad(layers, array, fc.params)) / 100.
        expected = math.exp(-energy / (float(fc.exp_params.kT) / 1000.))
        native_rule_max_error = max(native_rule_max_error, abs(weight - expected) / max(1., expected))
        if not math.isclose(weight, expected, abs_tol=EVENT_ABS_TOL, rel_tol=EVENT_REL_TOL):
            raise ArithmeticError('Native GQ energy/Boltzmann API mismatch')
        groups[start].append((end, weight))
    # Sum every admissible nonoverlapping set, including the empty (GQ-free) set.
    q = [0.] * (len(sequence) + 1)
    count = [0.] * (len(sequence) + 1)
    q[-1] = 1.
    for start in range(len(sequence) - 1, -1, -1):
        q[start], count[start] = q[start + 1], count[start + 1]
        for end, weight in groups[start]:
            q[start] += weight * q[end]
            count[start] += weight * (count[end] + q[end])
    kt = float(fc.exp_params.kT) / 1000.
    return {'Z': q[0], 'G_kcal_mol': -kt * math.log(q[0]),
        'probability_at_least_one': 1 - 1 / q[0],
        'expected_GQ_count': count[0] / q[0], 'admissible_patterns': len(patterns),
        'native_rule_max_relative_error': native_rule_max_error}


def ordinary_structures(sequence):
    """Enumerate ordinary noncrossing structures; loops >=3 and GU allowed."""
    sequence = normalize(sequence)
    valid = {'AU', 'UA', 'CG', 'GC', 'GU', 'UG'}

    @lru_cache(None)
    def visit(start, end):
        if start >= end:
            return ('',)
        values = ['.' + rest for rest in visit(start + 1, end)]
        for right in range(start + 4, end):
            if sequence[start] + sequence[right] in valid:
                for inside in visit(start + 1, right):
                    for rest in visit(right + 1, end):
                        values.append('(' + inside + ')' + rest)
        return tuple(values)

    return visit(0, len(sequence))


def source_guard():
    receipts = ('official_source_receipt.json', 'official_recurrence_source_receipt.json',
        'official_parameter_header_receipt.json')
    files = {}
    for name in receipts:
        receipt = json.loads((OUT / name).read_text())
        assert receipt['status'] == 'PASS'
        assert receipt['official_tree_sha'] == '1ffec79f5e258896160f7362ced8263450f371dc'
        for filename, item in receipt['source_files'].items():
            assert sha256(ROOT / filename) == item['sha256'], filename
            files[filename] = item['sha256']
    official = ART / 'official_source/src/ViennaRNA'
    ext = (official / 'partfunc/pf_exterior.c').read_text()
    internal = (official / 'partfunc/pf_internal.c').read_text()
    multibranch = (official / 'partfunc/pf_multibranch.c').read_text()
    assert 'qbt1  += vrna_smx_csr_get(q_gq, i, j, 0.)' in ext
    assert 'qbt1 += vrna_gq_int_loop_pf(fc, i, j)' in internal
    assert 'qqm[i]  += q_temp *' in multibranch
    params = (official / 'params/params.c').read_text()
    # Apart from the copied model_details, no flag-conditioned parameter rewrite.
    assert 'md->gquad' not in params
    for name in ('exp_eval_exterior.c', 'exp_eval_hairpin.c', 'exp_eval_internal.c', 'exp_eval_multibranch.c'):
        assert 'md->gquad' not in (official / 'eval' / name).read_text()
    return files


def runtime_identity():
    package = Path(RNA.__file__).resolve().parent
    if package != RUNTIME / 'RNA':
        raise RuntimeError('Wrong native package origin')
    dist = RUNTIME / 'viennarna-2.7.2.dist-info'
    record = list(csv.reader(io.StringIO((dist / 'RECORD').read_text())))
    rows = {row[0]: row for row in record}
    names = ['RNA/__init__.py', 'RNA/RNA.py']
    natives = list(package.glob('_RNA*.pyd'))
    assert len(natives) == 1
    names += [natives[0].relative_to(RUNTIME).as_posix()]
    names += ['viennarna-2.7.2.dist-info/' + name for name in ('METADATA', 'WHEEL', 'licenses/COPYING', 'licenses/AUTHORS')]
    identities = {}
    for name in names:
        path = RUNTIME / name
        digest = sha256(path)
        encoded = base64.urlsafe_b64encode(bytes.fromhex(digest)).decode().rstrip('=')
        assert rows[name][1] == 'sha256=' + encoded and int(rows[name][2]) == path.stat().st_size, name
        identities[path.relative_to(ROOT).as_posix()] = digest
    for path in (dist / 'RECORD', ROOT / 'src/generalization_next_20261007/route_structure.py',
                 ROOT / 'src/modeling/v2_features.py', ROOT / 'reports/v2_rescue_preregistration.md'):
        identities[path.relative_to(ROOT).as_posix()] = sha256(path)
    return {'version': RNA.__version__, 'pf_native_uses_float32': bool(RNA.pf_float_precision()),
        'installed_RECORD_matches_selected_files': True, 'files': identities,
        'binary_recompiled_from_inspected_source': False,
        'source_native_parity_scope': 'version/package RECORD plus independent synthetic API/grammar parity; not a reproducible binary build'}


def synthetic_inputs():
    result = []
    motif = 'GGAGGAGGAGG'
    for length in LENGTHS:
        rng = random.Random(SEED + length)
        background = ''.join(rng.choice('ACGU') for _ in range(length))
        start = (length - len(motif)) // 2
        positive = background[:start] + motif + background[start + len(motif):]
        disrupted = positive[:start] + 'A' + positive[start + 1:]
        result.extend([(f'allA{length}', 'A' * length),
            (f'mixed_GQ{length}', positive), (f'mixed_disrupt{length}', disrupted)])
    return result


def ordinary_parameter_snapshot(params):
    """Compare exposed values; opaque SWIG tables are not compared by address."""
    values, opaque = {}, []
    for name in PARAM_NAMES:
        value = getattr(params, name)
        if type(value).__name__ == 'SwigPyObject':
            opaque.append(name)
        else:
            # Assert JSON serialization so another pointer wrapper cannot sneak in.
            json.dumps(value, allow_nan=False)
            values[name] = value
    expected = ['mismatchExt', 'mismatchI', 'mismatchH', 'mismatchM', 'mismatch1nI',
        'mismatch23I', 'int11', 'int21', 'int22']
    assert opaque == expected
    return values, opaque


def run():
    environment()
    started = time.perf_counter()
    source_files = source_guard()
    runtime = runtime_identity()
    ordinary_parameter_checks = []
    for gquad in (0, 1):
        fc = RNA.fold_compound('GGAGGAGGAGGCCCCC', model_details(gquad), RNA.OPTION_MFE | RNA.OPTION_PF)
        snapshot, opaque = ordinary_parameter_snapshot(fc.params)
        ordinary_parameter_checks.append(snapshot)
    assert ordinary_parameter_checks[0] == ordinary_parameter_checks[1]
    ordinary = []
    for sequence in ('GGGAAACCC', 'GGGGAAAAACCCC', 'GGAGGAGGAGGCCCCC', 'GCGCAUACGCGC'):
        a = RNA.fold_compound(sequence, model_details(0))
        b = RNA.fold_compound(sequence, model_details(1))
        errors = [abs(float(a.eval_structure(structure)) - float(b.eval_structure(structure)))
                  for structure in ordinary_structures(sequence)]
        assert max(errors) <= ENERGY_ABS_TOL
        ordinary.append({'sequence': sequence, 'ordinary_structures': len(errors), 'max_energy_weight_error_kcal': max(errors)})
    gq_only = []
    for name, sequence in (
        ('allA32', 'A' * 32), ('one2layer', 'GGAGGAGGAGG'),
        ('disrupted', 'GAAGGAGGAGG'), ('one3layer', 'GGGAGGGAGGGAGGG'),
        ('long_linker', 'GG' + ('A' * 15 + 'GG') * 3),
        ('two_disjoint', 'GGAGGAGGAGG' + 'A' + 'GGAGGAGGAGG'),
        ('allG32', 'G' * 32)):
        reference = gq_only_partition(sequence)
        actual = measure(sequence)
        assert math.isclose(actual['off']['G_kcal_mol'], 0., abs_tol=ENERGY_ABS_TOL)
        assert math.isclose(actual['on']['G_kcal_mol'], reference['G_kcal_mol'], abs_tol=EVENT_ABS_TOL, rel_tol=EVENT_REL_TOL)
        assert math.isclose(actual['modeled_at_least_one_GQ_probability'], reference['probability_at_least_one'], abs_tol=EVENT_ABS_TOL, rel_tol=EVENT_REL_TOL)
        gq_only.append({'name': name, 'sequence': sequence, 'native': actual, 'reference': reference})
    full_lengths = []
    max_api_error = max_off_error = 0.
    for name, sequence in synthetic_inputs():
        value = measure(sequence)
        _, original_off = next_partition(sequence)
        error = abs(original_off - value['off']['G_kcal_mol'])
        assert math.isclose(original_off, value['off']['G_kcal_mol'], abs_tol=ENERGY_ABS_TOL, rel_tol=API_REL_TOL)
        max_off_error = max(max_off_error, error)
        for gquad in (0, 1):
            _, with_bpp = fold(sequence, gquad, 1)
            other = value['on' if gquad else 'off']['G_kcal_mol']
            error = abs(with_bpp['G_kcal_mol'] - other)
            assert math.isclose(with_bpp['G_kcal_mol'], other, abs_tol=ENERGY_ABS_TOL, rel_tol=API_REL_TOL)
            max_api_error = max(max_api_error, error)
        full_lengths.append({'name': name, 'length': len(sequence), 'sequence': sequence, 'native': value})
    parent, mutant = 'GGAGGAGGAGG', 'GAAGGAGGAGG'
    forward, reverse = delta(parent, mutant), delta(mutant, parent)
    assert delta(parent, parent) == [0., 0.] and all(a == -b for a, b in zip(forward, reverse))
    benchmark = []
    for name, sequence in synthetic_inputs():
        if name.startswith('mixed_disrupt'):
            continue
        times = []
        for _ in range(3):
            then = time.perf_counter()
            measure(sequence)
            times.append(time.perf_counter() - then)
        benchmark.append({'name': name, 'length': len(sequence), 'two_ensemble_seconds': times,
            'mean_seconds': sum(times) / len(times)})
    bylength = {length: max(row['mean_seconds'] for row in benchmark if row['length'] == length) for length in LENGTHS}
    estimate = sum(ALLELE_COUNTS[length] * bylength[length] for length in LENGTHS)
    receipt = {'status': 'PASS', 'scope': 'SYNTHETIC_BACKEND_FEASIBILITY_ONLY', 'spec': SPEC,
        'nesting_certification': 'source-reviewed unchanged ordinary weights plus nonnegative added GQ grammar; native synthetic corroboration',
        'source_files': source_files, 'runtime': runtime,
        'ordinary_parameter_fields_equal': list(ordinary_parameter_checks[0]),
        'opaque_parameter_fields_not_compared_by_value': opaque,
        'opaque_parameter_independence_basis': 'official flag-independent generation source plus ordinary-structure energy evaluation parity; no unsafe pointer reinterpretation',
        'ordinary_weight_checks': ordinary,
        'independent_GQ_only_partition_checks': gq_only, 'all_four_lengths': full_lengths,
        'maximum_NEXT_gquad_off_API_energy_error': max_off_error,
        'maximum_compute_bpp_energy_parity_error': max_api_error,
        'synthetic_edit_forward_delta': forward, 'synthetic_edit_reverse_delta': reverse,
        'synthetic_no_edit_delta': [0., 0.], 'benchmark': benchmark,
        'prior_metadata_allele_counts_for_resource_estimate_only': ALLELE_COUNTS,
        'fold_only_extrapolation_minutes': estimate / 60.,
        'fold_only_with_50pct_margin_minutes': estimate / 40.,
        'cost_excludes_IO_cache_birth_checks_feature_assembly_and_concurrent_contention': True,
        'elapsed_seconds': time.perf_counter() - started,
        'project_alleles_folded': 0, 'labels_read': False, 'models_read': False, 'models_fit': 0,
        'future_production_authorized': False,
        'source_code_and_declared_protocol': {path.relative_to(ROOT).as_posix(): sha256(path)
            for path in list(SRC.glob('*.py')) + [REP / 'feasibility_protocol.md']}}
    save_json(OUT / 'backend_feasibility_receipt.json', receipt)
    print(json.dumps({'status': 'PASS', 'ordinary_structures_checked': sum(row['ordinary_structures'] for row in ordinary),
        'GQ_only_cases': len(gq_only), 'full_length_cases': len(full_lengths),
        'fold_only_estimate_minutes': estimate / 60., 'elapsed_seconds': receipt['elapsed_seconds']}))


if __name__ == '__main__':
    run()
