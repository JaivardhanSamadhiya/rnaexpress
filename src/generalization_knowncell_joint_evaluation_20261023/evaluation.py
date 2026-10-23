"""Evaluate already-admitted outer predictions using the frozen reference gate.

This module opens no files, imports no scientific package and fits nothing.
The future controller must independently admit inputs, all checkpoint replay,
source selection, runtime/native-bootstrap parity and committed provenance.
"""
from collections import Counter, defaultdict
import math

from src.generalization_knowncell_joint_design_20261009.spec import ARMS, CELLS, FOLDS, COUNTS, GATE
from src.generalization_knowncell_joint_implementation_20261022 import contracts, selection
from src.generalization_knowncell_joint_implementation_20261022.admission import require_resources
from src.generalization_knowncell_joint_campaign_20261023.writer import check_predictions
from src.generalization_knowncell_joint_gate_20261023 import gate

FULL_DECISIONS_PER_ARM = 9650


def fresh(probe, environment):
    assert callable(probe)
    return require_resources(probe(), environment)


def collect_outer(metadata_rows, outer_records):
    """Check exact complete inherited-fold order, not an ID intersection.

    This lower-level roster helper is also usable on invented complete menus.
    Only evaluate() applies the fixed full-project counts and primary gate.
    Record schema: arm, outer_fold, predictions (the frozen six-field schema).
    Models/checkpoints and verification receipts remain with the future caller.
    """
    contracts.validate_rows(metadata_rows)
    ids = [row['intervention_id'] for row in metadata_rows]
    assert len(ids) == len(set(ids)) and {row['held_parent_fold'] for row in metadata_rows} == set(FOLDS)
    assert isinstance(outer_records, (list, tuple)) and len(outer_records) == len(ARMS)*len(FOLDS)
    expected = {(arm, fold) for arm in ARMS for fold in FOLDS}
    seen, scores, fold_counts = set(), {arm:{} for arm in ARMS}, {arm:{} for arm in ARMS}
    for record in outer_records:
        assert isinstance(record, dict) and set(record) == {'arm', 'outer_fold', 'predictions'}
        arm, fold = record['arm'], record['outer_fold']
        assert arm in ARMS and type(fold) is int and fold in FOLDS
        key = (arm, fold)
        assert key in expected and key not in seen, 'Duplicate or unsupported outer checkpoint'
        seen.add(key)
        target = [row for row in metadata_rows if row['held_parent_fold'] == fold]
        target_ids = [row['intervention_id'] for row in target]
        assert target_ids
        predictions = record['predictions']
        binding = {'validation_ids':target_ids, 'validation_ids_sha256':contracts.ids_sha(target),
                   'validation_rows':len(target)}
        check_predictions(predictions, binding)
        assert all(type(value) is float and math.isfinite(value) for value in predictions['scores']), 'Canonical finite float scores required'
        assert not set(scores[arm]) & set(target_ids), 'An arm predicts a target more than once'
        scores[arm].update(zip(target_ids, predictions['scores']))
        fold_counts[arm][fold] = len(target_ids)
    assert seen == expected
    for arm in ARMS:
        assert len(scores[arm]) == len(ids) and set(scores[arm]) == set(ids), 'Incomplete full target coverage'
        # Retain the original global metadata order for the downstream mapping.
        scores[arm] = {identifier:scores[arm][identifier] for identifier in ids}
    coverage = {'arms':list(ARMS), 'outer_records':len(seen), 'rows_per_arm':len(ids),
                'fold_rows_per_arm':fold_counts, 'full_metadata_order_sha256':contracts.ids_sha(metadata_rows),
                'each_row_once_per_arm':True, 'unmatched_predictions_retained':True,
                'canonical_order':'exact_inherited_fold_target_order',
                'canonical_ties':'exact_score_then_original_intervention_id'}
    return scores, coverage


def secondary_summary(records, label):
    """Nongating summaries; missing cells remain explicit, never intersected."""
    columns = ('regret', 'wrong_direction', 'avoidable_wrong', 'no_feasible_candidate',
               'unavoidable_wrong', 'neutral_only_alternative_wrong')
    grouped = defaultdict(list)
    for row in records:
        assert row['cell_type'] in CELLS
        grouped[row['cell_type'],row['biological_component']].append(row)
    per_cell = {}
    for cell in CELLS:
        genes = sorted(gene for actual_cell,gene in grouped if actual_cell == cell)
        selected = [row for row in records if row['cell_type'] == cell]
        means = {column:(math.fsum(math.fsum(row[column] for row in grouped[cell,gene]) /
                                  len(grouped[cell,gene]) for gene in genes) / len(genes) if genes else None)
                 for column in columns}
        per_cell[cell] = {'decisions':len(selected), 'contexts':len({row['parent_context_id'] for row in selected}),
                          'components':len(genes), **means}
    macro = {column:(math.fsum(per_cell[cell][column] for cell in CELLS)/len(CELLS)
                     if all(per_cell[cell][column] is not None for cell in CELLS) else None)
             for column in columns}
    return {'scope':label, 'nongating':True, 'decisions':len(records), 'per_cell':per_cell,
            'macro':macro, 'weighting':'equal_cell_component_context_direction_within_declared_secondary_set',
            'missing_cell_macro_is_none':True}


def evaluate(np, metadata_rows, effects, outer_records, *, probe, environment):
    """Finite supplied-input evaluation, never an input-admission certificate.

    np must be supplied only after separate accepted runtime/bootstrap-parity
    admission. There is no CLI, import/bootstrap hook or optimizer callback.
    """
    fresh(probe, environment)
    metadata = [dict(row) for row in metadata_rows]
    contract = contracts.full_metadata_contract(metadata)
    ids = [row['intervention_id'] for row in metadata]
    assert isinstance(effects, dict) and set(effects) == set(ids), 'Full original effects required'
    truths = dict(effects)
    assert all(type(value) in (int,float) and math.isfinite(value) for value in truths.values())
    scores, coverage = collect_outer(metadata, outer_records)
    assert coverage['rows_per_arm'] == COUNTS['all_rows']
    paired_contexts = {context for pair in contract['pairs'] for context in pair['contexts'].values()}
    unmatched_contexts = set(contract['unmatched_contexts'])
    all_contexts = {row['parent_context_id'] for row in metadata}
    assert paired_contexts.isdisjoint(unmatched_contexts) and paired_contexts | unmatched_contexts == all_contexts
    assert len(paired_contexts) == COUNTS['paired_contexts'] and len(unmatched_contexts) == COUNTS['unmatched_contexts']
    assert sum(row['parent_context_id'] in unmatched_contexts for row in metadata) == COUNTS['unmatched_rows']
    all_decisions, primary_decisions, unmatched_decisions, secondary = {}, {}, {}, {}
    expected_full = {(context,direction) for context in all_contexts for direction in (-1,1)}
    for arm in ARMS:
        records = selection.decisions(metadata, scores[arm], truths)
        assert len(records) == FULL_DECISIONS_PER_ARM == 2*len(all_contexts)
        assert Counter((row['parent_context_id'],row['direction']) for row in records) == Counter({key:1 for key in expected_full})
        primary = [row for row in records if row['parent_context_id'] in paired_contexts]
        unmatched = [row for row in records if row['parent_context_id'] in unmatched_contexts]
        assert len(primary) == COUNTS['paired_directional_decisions']
        assert len(unmatched) == 2*COUNTS['unmatched_contexts'] and len(primary)+len(unmatched) == len(records)
        all_decisions[arm], primary_decisions[arm], unmatched_decisions[arm] = records, primary, unmatched
        secondary[arm] = {'all_contexts':secondary_summary(records, 'all_original_contexts_including_unmatched'),
                          'unmatched':secondary_summary(unmatched, 'all_original_unmatched_contexts_only')}
    primary_summaries, comparisons = gate.prepare_primary(metadata, primary_decisions)
    genes = sorted({row['biological_component'] for row in metadata})
    assert len(genes) == COUNTS['components']
    fresh(probe, environment)
    bootstrap = gate.native_shared_bootstrap(np, comparisons)
    assert bootstrap['components'] == genes
    assert bootstrap['draws'] == GATE['bootstrap_draws'] == 5000 and bootstrap['seed'] == GATE['bootstrap_seed'] == 20261007
    assert bootstrap['fixed_predictions_only'] is True and bootstrap['std_random_or_refits_used'] is False
    assert set(bootstrap['intervals']) == {'pooled','independent'}
    fresh(probe, environment)
    verdict = gate.thresholds(primary_summaries['joint_shrink10'], comparisons, bootstrap['intervals'])
    assert verdict['status'] in ('JOINT_KNOWN_CELL_DEVELOPMENT_GO','NO-GO')
    assert verdict['claim_eligible_arm'] == 'joint_shrink10'
    return {'status':verdict['status'], 'scope':'represented_known_cells_unseen_genes_exposed_development',
            'coverage':coverage, 'all_decisions':all_decisions, 'primary_decisions':primary_decisions,
            'unmatched_decisions':unmatched_decisions, 'primary_summaries':primary_summaries,
            'secondary_summaries_nongating':secondary, 'comparisons':comparisons, 'bootstrap':bootstrap,
            'gate':verdict, 'model_fits_or_refits':0, 'new_configuration_selection':False,
            'input_provenance_or_full_campaign_replay_certified_here':False,
            'requires_separate_accepted_runtime_and_native_bootstrap_parity':True,
            'independent_confirmation':False, 'unknown_cell_generalization':False,
            'novelty_certified':False, 'localization_generalization_pass':False}
