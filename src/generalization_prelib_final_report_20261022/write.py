"""Summarize committed original study receipts without raw targets or refits."""
import json
import math
from pathlib import Path

from src.generalization_prelib_bounded_execution_20261022 import worker

ROOT = worker.ROOT
OUT = ROOT / 'results/generalization_prelib_final_report_20261022'
REP = ROOT / 'reports/generalization_prelib_final_report_20261022'


def read(path):
    worker.committed(path)
    return json.loads(path.read_bytes())


def run():
    manifest = read(worker.MANIFEST)
    authorization = read(worker.AUTH)
    manifest_sha = worker.sha(worker.MANIFEST)
    assert authorization['execution_manifest_sha256'] == manifest_sha
    assert authorization['spending_authorized'] is False
    for rel, want in manifest['files'].items():
        assert worker.sha(ROOT / rel) == want, rel
    pins = {worker.MANIFEST.relative_to(ROOT).as_posix(): manifest_sha,
            worker.AUTH.relative_to(ROOT).as_posix(): worker.sha(worker.AUTH)}
    stages = {}
    for phase in worker.PHASES:
        supervisor_path = worker.OUT / (phase + '_supervisor_receipt.json')
        worker_path = worker.OUT / (phase + '_worker_receipt.json')
        completion = worker.BIO / worker.COMPLETION[phase]
        supervisor, native, result = read(supervisor_path), read(worker_path), read(completion)
        worker.check_predecessor_binding(supervisor, phase, manifest_sha, worker.sha(completion), worker.sha(worker_path))
        worker.check_worker_binding(native, phase, manifest_sha, worker.sha(completion))
        for path in (supervisor_path, worker_path, completion):
            pins[path.relative_to(ROOT).as_posix()] = worker.sha(path)
        stages[phase] = {key: supervisor[key] for key in (
            'elapsed_seconds', 'peak_worker_working_set_bytes', 'peak_worker_private_commit_bytes',
            'minimum_sampled_physical_available', 'minimum_sampled_system_commit_headroom',
            'maximum_monitor_gap_seconds', 'frozen_sources_unchanged')}
    evaluation_path = worker.BIO / 'evaluation_results.json'
    evaluation = read(evaluation_path)
    pins[evaluation_path.relative_to(ROOT).as_posix()] = worker.sha(evaluation_path)
    provisional = read(worker.BIO / 'provisional_verdict.json')
    replay = read(worker.BIO / worker.COMPLETION['verify'])
    assert provisional['status'] == 'NO_GO_FOR_DECLARED_POOLED_BINDING_ROBUSTNESS_CRITERION'
    assert provisional['evaluation_sha256'] == worker.sha(evaluation_path)
    assert replay['status'] == 'PASS_ALL399_NORMAL_EQUATIONS_SCORES_TARGET_VIEWS_AND_PRIMARY_GATE_REPLAY'
    assert replay['models_verified_without_refitting'] == 399
    assert replay['evaluation_sha256'] == worker.sha(evaluation_path)
    primary = evaluation['MAE_all18_views_both_proteins']['PUM2']['pc0.5_IPmean_Inputmean']
    candidate = primary['kmer84_plus_releasedPUM2']
    comparisons = evaluation['primary_comparisons']
    checks = {}
    for control, record in comparisons.items():
        criteria = {
            'relative_gain_at_least_5percent': record['relative_MAE_gain'] >= .05,
            'at_least5of7_lineages_improve': record['improved_lineages'] >= 5,
            'positive_gain_after_removing_best_lineage': record['leave_best_lineage_out_gain'] > 0,
            'bootstrap_lower_gain_positive': record['paired_lineage_bootstrap95'][0] > 0,
            'positive_gain_in_all17_other_target_views': all(value > 0 for value in record['all17_sensitivity_MAE_gains'].values()),
        }
        assert all(criteria.values()) == record['criterion_pass'] is False
        assert len(record['lineage_gains']) == 7 and len(record['all17_sensitivity_MAE_gains']) == 17
        checks[control] = criteria
    zero = primary['zero_effect']['macro_MAE']
    difference_from_zero = candidate['macro_MAE'] - zero
    assert difference_from_zero > 0
    receipt = {
        'status': 'VERIFIED_NO_GO_FOR_DECLARED_POOLED_BINDING_ROBUSTNESS_CRITERION',
        'scope': 'Repeatedly exposed pooled binding association development, not localization',
        'rows': 4054, 'backgrounds': 16, 'nominal_lineages': 7,
        'inner_fits': 378, 'outer_fits': 21, 'models_independently_replayed_without_refitting': 399,
        'stored_predictions_compared': replay['stored_predictions_compared'],
        'maximum_prediction_difference': replay['maximum_prediction_difference'],
        'maximum_original_unit_gradient_residual': replay['maximum_original_unit_gradient_residual'],
        'primary_macro_MAE': {arm: value['macro_MAE'] for arm, value in primary.items()},
        'primary_comparisons': comparisons, 'original_criteria_rechecked_from_verified_summary': checks,
        'candidate_minus_zero_effect_MAE': difference_from_zero,
        'candidate_relative_MAE_increase_vs_zero_effect': difference_from_zero / zero,
        'stage_resources': stages, 'source_receipts_sha256': pins,
        'original_provisional_pending_field_preserved': provisional['independent_verification_pending'],
        'independent_replay_now_complete': True,
        'same_root_and_runtime_replay_not_independent_agent_execution': True,
        'raw_targets_or_model_checkpoints_read_for_this_report': False,
        'new_models_or_target_variants_or_gate_changes': False,
        'localization_generalization_pass': False, 'novelty_certified': False,
        'report_source_sha256': worker.sha(__file__),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    (OUT / '.gitattributes').write_text('* -text\n', encoding='utf-8')
    worker.save(OUT / 'verified_final_status.json', receipt)
    lines = [
        '# Verified PRELib binding result', '',
        '**NO-GO under the original pooled-binding robustness criterion.** All399 fits completed and the independent numerical/score/target/gate replay passed. This closes the frozen experiment without a localization or novelty success.', '',
        'All4054 edits,16 backgrounds and seven nominal lineages were retained. Original scientific source, three arms, weights, target definitions, nested folds, lambdas, tie policy and gates stayed unchanged. The explicitly approved operational adapter and current-Python provenance are recorded separately; no old runtime certificate was rewritten.', '',
        '| Primary pooled PUM2 arm | Equal-lineage/equal-background MAE |',
        '|---|---:|',
    ]
    for arm in ('kmer84', 'kmer84_plus_releasedPUM2', 'kmer84_plus_duplicateTGT', 'zero_effect'):
        lines.append(f"| {arm} | {primary[arm]['macro_MAE']:.12f} |")
    lines += ['', '| Control | Relative MAE improvement | Improved lineages | Paired95% gain interval | Leave-best gain | Gate |',
              '|---|---:|---:|---|---:|---|']
    for control, record in comparisons.items():
        lo, hi = record['paired_lineage_bootstrap95']
        lines.append(f"| {control} | {100*record['relative_MAE_gain']:.3f}% | {record['improved_lineages']}/7 | [{lo:.6f}, {hi:.6f}] | {record['leave_best_lineage_out_gain']:.6f} | NO-GO |")
    lines += ['',
        'The fixed PUM scalar adds feature variation outside the kmer span and modestly improves average error against both fitted controls. It helps5/7 lineages and retains positive mean gains in all17 alternative target views and after removing the best lineage. Those conditions passed, but the prespecified five-percent effect-size and positive bootstrap-lower-bound requirements failed against both controls. Target views share counts and are sensitivity analyses, not18 independent replications.', '',
        f"The descriptive zero-effect predictor is stronger on this primary MAE than the augmented model: error is higher by {difference_from_zero:.9f} ({100*difference_from_zero/zero:.3f}%). This was not substituted as a new gate; it is an existing reported control that limits practical interpretation.", '',
        '| Held lineage | Kmer MAE | Kmer+PUM MAE | Gain versus kmer |', '|---|---:|---:|---:|']
    for gene in sorted(candidate['per_lineage_MAE']):
        base = primary['kmer84']['per_lineage_MAE'][gene]
        augmented = candidate['per_lineage_MAE'][gene]
        lines.append(f'| {gene} | {base:.6f} | {augmented:.6f} | {base-augmented:.6f} |')
    lines += ['',
        'IRF2BP1 and SMARCA2 worsen, while AP1S1,HIAT1,MGEA5,NORAD and PGBD4 improve relative to both fitted controls. Seven nominal lineages, rather than4054 independent genes, determine this uncertainty. The bootstrap covers fixed predictions across those observed lineages; it does not represent biological measurement, replicate pairing, refitting or new-study uncertainty. Matched lysate pairing remains unknown.', '',
        f"Independent replay checked{replay['models_verified_without_refitting']} models and{replay['stored_predictions_compared']} stored predictions without refitting; maximum score difference{replay['maximum_prediction_difference']:.4g}, maximum original-unit stationarity residual{replay['maximum_original_unit_gradient_residual']:.4g}. All18 target views for both proteins and both primary control gates were replayed. The replay used separate arithmetic but the same root/runtime, not independent-agent execution. Within-menu ranking summaries remain descriptive and are not a localization test or a separate validated primary ranking gate.", '',
        'Every approved stage stayed within hard process768MiB/job896MiB limits. All399 fits required18.344seconds and peak private memory154320896bytes(147.17MiB); the complete five-stage owned lifetimes sum to'+f"{math.fsum(value['elapsed_seconds'] for value in stages.values()):.3f}"+'seconds. Original guard boundaries were retained with the explicitly approved lower physical floor; every other worker guard stayed unchanged.', '',
        'The original provisional verdict still carries its pending flag because that artifact is immutable. verified_final_status.json records the later completed replay and binds all stage receipts. Do not read the preserved old pending field as evidence that replay has not run.', '',
        'Do not rescue this generation by dropping negative lineages, changing pseudocounts, fitting another PUM mode, tuning weights/lambdas or lowering thresholds. Fixed PUM binding physics and its association with PRELib already have prior art. The justified result is a small, insufficiently precise binding-model increment; it does not demonstrate small-edit localization generalization.', '',
        'Next work remains the separately frozen joint known-cell implementation and its guarded selective loader/trainer. That experiment can test cell-dependent slopes under held-gene splits, while external biological-context generalization still needs an independently qualified intervention benchmark. The current literature search certified no new such benchmark.', '',
    ]
    with (REP / 'results.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(lines))
    print('VERIFIED_BINDING_NO_GO_REPORT', worker.sha(OUT / 'verified_final_status.json'), flush=True)


if __name__ == '__main__':
    run()
