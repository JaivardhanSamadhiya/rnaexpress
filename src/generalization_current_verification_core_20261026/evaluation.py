"""Original evaluation mathematics with a new explicitly supplied real guard.

No old resource function or global is patched. The original public evaluator
retains its three-GiB contract. This library grants no actual stage authority.
"""
from collections import Counter
import math
from src.generalization_knowncell_joint_design_20261009.spec import ARMS,CELLS,FOLDS,COUNTS,GATE
from src.generalization_knowncell_joint_implementation_20261022 import contracts,selection
from src.generalization_knowncell_joint_gate_20261023 import gate
from src.generalization_knowncell_joint_evaluation_20261023.evaluation import collect_outer,secondary_summary,FULL_DECISIONS_PER_ARM

def evaluate(np, metadata_rows, effects, outer_records, *, fresh):
    """Finite supplied-input evaluation, never an input-admission certificate.

    np must be supplied only after separate accepted runtime/bootstrap-parity
    admission. There is no CLI, import/bootstrap hook or optimizer callback.
    """
    fresh()
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
    fresh()
    bootstrap = gate.native_shared_bootstrap(np, comparisons)
    assert bootstrap['components'] == genes
    assert bootstrap['draws'] == GATE['bootstrap_draws'] == 5000 and bootstrap['seed'] == GATE['bootstrap_seed'] == 20261007
    assert bootstrap['fixed_predictions_only'] is True and bootstrap['std_random_or_refits_used'] is False
    assert set(bootstrap['intervals']) == {'pooled','independent'}
    fresh()
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
