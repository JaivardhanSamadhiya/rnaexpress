"""Original fixed-prediction gate applied to complete supplied paired records."""
import hashlib
import math

from src.generalization_knowncell_joint_design_20261009.spec import ARMS, CELLS, FOLDS, COUNTS, GATE
from src.generalization_knowncell_joint_implementation_20261022 import contracts, selection


def components(records):
    grouped = {}
    folds = {}
    for row in records:
        cell, gene, fold = row['cell_type'], row['biological_component'], row['gene_fold']
        assert cell in CELLS and fold in FOLDS
        assert gene not in folds or folds[gene] == fold
        folds[gene] = fold
        assert math.isfinite(row['regret']) and 0 <= row['regret'] <= 1
        assert row['wrong_direction'] in (0., 1.)
        grouped.setdefault((cell, gene), []).append(row)
    genes = sorted(folds)
    assert genes and {gene for cell, gene in grouped if cell == CELLS[0]} == set(genes)
    assert {gene for cell, gene in grouped if cell == CELLS[1]} == set(genes)
    result = {}
    for column in ('regret', 'wrong_direction'):
        result[column] = {cell: {gene: math.fsum(row[column] for row in grouped[cell, gene]) / len(grouped[cell, gene])
                                for gene in genes} for cell in CELLS}
    return result, folds


def compare_components(candidate, control, foldmap):
    genes = sorted(foldmap)
    assert genes and set(foldmap.values()) == set(FOLDS)
    assert set(candidate) == set(control) == {'regret', 'wrong_direction'}
    for value in (candidate, control):
        for column in value:
            assert set(value[column]) == set(CELLS)
            for cell in CELLS:
                assert set(value[column][cell]) == set(genes)
                assert all(math.isfinite(v) for v in value[column][cell].values())
    gains = {cell: {gene: control['regret'][cell][gene] - candidate['regret'][cell][gene]
                    for gene in genes} for cell in CELLS}
    means = {cell: math.fsum(gains[cell].values()) / len(genes) for cell in CELLS}
    fold_gains = {}
    for fold in FOLDS:
        members = [gene for gene in genes if foldmap[gene] == fold]
        assert members
        fold_gains[fold] = math.fsum(math.fsum(gains[cell][g] for g in members) / len(members)
                                      for cell in CELLS) / len(CELLS)
    best = max(FOLDS, key=lambda fold: (fold_gains[fold], -fold))
    remaining = [gene for gene in genes if foldmap[gene] != best]
    assert remaining
    leave = math.fsum(math.fsum(gains[cell][g] for g in remaining) / len(remaining)
                     for cell in CELLS) / len(CELLS)
    harm = {cell: math.fsum(candidate['wrong_direction'][cell][g] - control['wrong_direction'][cell][g]
                            for g in genes) / len(genes) for cell in CELLS}
    return {'mean_gain': math.fsum(means.values()) / len(CELLS), 'per_cell_gain': means,
            'component_gains': gains, 'removed_best_gene_fold': best, 'fold_gains': fold_gains,
            'remaining_gain': leave, 'wrong_direction_harm': harm,
            'macro_wrong_direction_harm': math.fsum(harm.values()) / len(CELLS)}


def native_shared_bootstrap(np, comparisons):
    """Deferred ORIGINAL exponential algorithm; one draw matrix for both controls.

    The caller must admit NumPy origins, one thread and resources first. The
    original source algorithm is bootstrap.shared_bootstrap, not stdlib random.
    No data reader, runtime import, refit or resampled model selection occurs.
    """
    assert set(comparisons) == {'pooled', 'independent'}
    genes = sorted(comparisons['pooled']['component_gains'][CELLS[0]])
    assert genes
    for comparison in comparisons.values():
        assert set(comparison['component_gains']) == set(CELLS)
        for values in comparison['component_gains'].values():
            assert set(values) == set(genes) and all(math.isfinite(v) for v in values.values())
    weights = np.random.default_rng(GATE['bootstrap_seed']).exponential(1, size=(GATE['bootstrap_draws'], len(genes)))
    assert weights.shape == (5000, len(genes)) and np.isfinite(weights).all() and np.all(weights >= 0)
    assert np.all(weights.sum(1) > 0)
    draw_sha = hashlib.sha256(weights.tobytes(order='C')).hexdigest()
    intervals = {}
    for name, comparison in comparisons.items():
        samples = np.zeros(GATE['bootstrap_draws'])
        for cell in sorted(CELLS):
            # Match original component ordering, row normalization, matrix
            # multiplication and incremental /number-of-cells accumulation.
            selected = weights[:, list(range(len(genes)))]
            selected = selected / selected.sum(1, keepdims=True)
            values = np.asarray([comparison['component_gains'][cell][gene] for gene in genes], dtype=np.float64)
            samples += selected @ values / len(CELLS)
        assert np.isfinite(samples).all()
        intervals[name] = [float(np.quantile(samples, .025)), float(np.quantile(samples, .975))]
    return {'intervals': intervals, 'shared_original_exponential_draws_sha256': draw_sha,
            'draws': GATE['bootstrap_draws'], 'seed': GATE['bootstrap_seed'], 'components': genes,
            'fixed_predictions_only': True, 'std_random_or_refits_used': False}


def thresholds(primary, comparisons, intervals):
    assert set(primary['per_cell_regret']) == set(CELLS)
    assert all(math.isfinite(value) and 0 <= value <= 1
               for value in [primary['macro_regret'], *primary['per_cell_regret'].values()])
    assert set(comparisons) == set(intervals) == {'pooled', 'independent'}
    checks = {
        'macro_regret_at_most_0_48': primary['macro_regret'] <= GATE['macro_regret_max'],
        'each_cell_regret_strictly_below_0_5': all(value < GATE['each_cell_regret_strict_max'] for value in primary['per_cell_regret'].values()),
    }
    for control, value in comparisons.items():
        bounds = intervals[control]
        assert len(bounds) == 2 and all(math.isfinite(x) for x in bounds) and bounds[0] <= bounds[1]
        assert set(value['per_cell_gain']) == set(value['wrong_direction_harm']) == set(CELLS)
        assert all(math.isfinite(x) for x in [value['mean_gain'], value['remaining_gain'],
                                             value['macro_wrong_direction_harm'],
                                             *value['per_cell_gain'].values(), *value['wrong_direction_harm'].values()])
        checks.update({
            control + '_macro_gain_at_least_0_01': value['mean_gain'] >= GATE['gain_macro_min'],
            control + '_each_cell_gain_at_least_0_005': min(value['per_cell_gain'].values()) >= GATE['gain_each_cell_min'],
            control + '_bootstrap_lower_strictly_positive': bounds[0] > GATE['bootstrap_lower_strict_min'],
            control + '_macro_wrong_harm_at_most_0_02': value['macro_wrong_direction_harm'] <= GATE['wrong_harm_macro_max'],
            control + '_each_cell_wrong_harm_at_most_0_05': max(value['wrong_direction_harm'].values()) <= GATE['wrong_harm_each_cell_max'],
            control + '_leave_best_fold_gain_strictly_positive': value['remaining_gain'] > GATE['leave_best_fold_gain_strict_min'],
        })
    return {'status': 'JOINT_KNOWN_CELL_DEVELOPMENT_GO' if all(checks.values()) else 'NO-GO',
            'checks': checks, 'claim_eligible_arm': 'joint_shrink10',
            'independent_confirmation': False, 'unknown_cell_generalization': False,
            'novelty_certified': False, 'localization_generalization_pass': False}


def prepare_primary(metadata_rows, decision_records):
    """Strict complete project-roster validation; no target or file is opened."""
    metadata = contracts.full_metadata_contract(metadata_rows)
    pairs = metadata['pairs']
    assert len(pairs) == COUNTS['paired_menus'] and set(decision_records) == set(ARMS)
    ids = {row['intervention_id']: row for row in metadata_rows}
    summaries = {}
    aggregate = {}
    foldmaps = []
    for arm, records in decision_records.items():
        assert len(records) == COUNTS['paired_directional_decisions']
        for row in records:
            chosen = ids[row['selected_id']]
            assert chosen['cell_type'] == row['cell_type'] and chosen['parent_context_id'] == row['parent_context_id']
            assert chosen['biological_component'] == row['biological_component']
            assert chosen['held_parent_fold'] == row['gene_fold']
            assert chosen['mutant_sequence'] == row['selected_mutant_sequence']
        summaries[arm] = selection.primary_metrics(records, pairs)
        aggregate[arm], foldmap = components(records)
        foldmaps.append(foldmap)
        assert summaries[arm]['components'] == COUNTS['components']
    assert all(value == foldmaps[0] for value in foldmaps)
    comparisons = {control: compare_components(aggregate['joint_shrink10'], aggregate[control], foldmaps[0])
                   for control in ('pooled', 'independent')}
    return summaries, comparisons
