"""Build the required 60-item report from frozen outputs; never fit or reselect."""
import json
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/finalshot'
REPORTS = ROOT / 'reports'
FULL = 'M1_M2_M3_nested_selected'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def table(frame):
    def value(x):
        return f'{x:.6f}' if isinstance(x, float) else str(x).replace('|', '/')
    return '\n'.join(['| ' + ' | '.join(frame.columns) + ' |',
                      '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |'] +
                     ['| ' + ' | '.join(value(v) for v in row) + ' |' for row in frame.itertuples(index=False, name=None)])


def main():
    primary, grouped, transfer = read('m0_m3_summary.json'), read('grouped_gate_summary.json'), read('transfer_summary.json')
    gate_g, gate_h = read('gate_g_summary.json'), read('gate_h_summary.json')
    parent, heads = read('parent_binding_summary.json'), read('measurement_head_randomization_summary.json')
    reproduction = read('deterministic_reproducibility_threads_default.json')
    reconstruction = read('reconstruction_reverification_20260909.json')
    tdp = read('tdp_exact_geometry_summary.json')
    cell = read('cell_context_control_summary.json') if (OUT / 'cell_context_control_summary.json').exists() else None
    pending = [] if cell else ['Complete remaining M3 cell-context outer folds, validate archives, and summarize the control.']
    test_path = OUT / 'submission_tests.xml'
    if test_path.exists():
        root = ET.parse(test_path).getroot()
        suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
        test_counts = {name: sum(int(s.get(name, 0)) for s in suites) for name in ('tests', 'failures', 'errors', 'skipped')}
        if test_counts['failures'] or test_counts['errors']:
            pending.append('Resolve failing software checks without changing the scientific protocol.')
    else:
        test_counts = None
        pending.append('Record the release test run.')
    assert reconstruction['status'] == 'pass'
    source = pd.read_csv(OUT / 'm0_m3_source_metrics.csv')
    source = source[source.model.eq(FULL)]
    context = pd.read_csv(OUT / 'm0_m3_context_values.csv')
    context = context[context.model.eq(FULL)]
    unit = pd.read_csv(OUT / 'grouped_unit_context_values.csv')
    transfers = pd.read_csv(OUT / 'transfer_context_values.csv')
    transfers = transfers[transfers.model.eq(FULL)]
    bands = pd.read_csv(OUT / 'small_edit_metrics.csv').set_index('edit_band')
    directional_bands = pd.read_csv(OUT / 'directional_source_diagnostics.csv')
    directional_bands = directional_bands[directional_bands.diagnostic.eq('band:2-10')]
    directions = []
    for direction in ('increase', 'decrease'):
        src = context[context.requested_direction.eq(direction)]
        tr = transfers[transfers.requested_direction.eq(direction) & transfers.task.str.startswith('leave_')]
        small = directional_bands[directional_bands.requested_direction.eq(direction)]
        units = unit[unit.requested_direction.eq(direction)]
        record = {'direction': direction, 'within_source_rank_gain': float(src.rank_context_value.mean()),
            'within_source_regret_gain': float(src.regret_context_value.mean()),
            'leave_source_regret_gain': float(tr.regret_context_value.mean()),
            'small_2_10_regret_gain': float(small.regret_context_value.mean()),
            'unit_improvement_fraction': float(units.regret_context_value.gt(0).mean())}
        record['direction_mean_conditions_met'] = all(record[k] > 0 for k in ('within_source_rank_gain', 'within_source_regret_gain', 'leave_source_regret_gain', 'small_2_10_regret_gain')) and record['unit_improvement_fraction'] >= .55
        directions.append(record)
    # This tabulation cannot rescue a direction after failed mechanism controls.
    pd.DataFrame(directions).to_csv(OUT / 'directional_verdict_diagnostics.csv', index=False)
    selected = next(r for r in primary['summary'] if r['model'] == FULL)
    distributed = grouped['gate_B_distributed_units']
    answers = []
    def add(title, answer):
        answers.append((title, answer.strip()))
    def ctx(frame):
        return table(frame[['requested_direction', 'rank_context_value', 'regret_context_value']])
    add('FinalShot verdict', 'NO-GO — END ZERO-SHOT RNADDRESS. ' + ('Release preparation remains incomplete: ' + ' '.join(pending) if pending else 'Required result consolidation is complete, with the integrity qualifications below.'))
    add('Exact resource-audit findings', 'Parnet paper-matching weights were unavailable at freeze. RBPNet was the explicitly allowed reproducible fallback. BRIDGE and DeepLocRNA were not used as predictors; no stability model passed audit. Exact versions, hashes, licenses, coverage, and exclusions are in finalshot_resource_audit.md and the resource manifests.')
    add('Was Parnet reproducibly usable?', 'No: the executable development checkpoint did not match the preprint architecture. This is not evidence that RBPNet is the same model.')
    add('Exact Parnet version/checkpoint/hash', 'No paper-matching checkpoint/version/hash is available from the frozen audit. Package 0.5.0 commit 2f0570cf47d8bb927415a71f853a97eb7e94005c; executable but excluded development artifact 0.5.0_RBPNet-11M.pt, SHA-256 2620a1c9b838fd28fcefb3c8cc695fa7a4889fb18a67c21694c097248aa64869. It has 11,736,799 parameters, not the paper-reported 21 million.')
    add('Parnet RBP count represented', 'Zero modeled Parnet channels. The preprint reports 150 unique human RBPs across 223 experiments. The actual fallback comprises 103 RBPNet HepG2 checkpoint groups and 927 summaries.')
    add('Localization-RBP coverage', 'RBPNet covers 12 of 26 prespecified localization-related human symbols. TARDBP, ELAVL, MBNL, PUM, FMR1, FXR1, and IGF2BP2 are absent. Mouse inference is cross-species, not a validated mouse binding model; see rbp_coverage.csv.')
    add('BRIDGE usability', 'Methodology-only; its human-cell modalities and input requirements were incompatible with this frozen dataset. No zero-filled surrogate or new representation was introduced.')
    add('External cell-context datasets', 'GSE67828: equal-compartment averages of soma/neurite replicate medians of log1p(FPKM), CAD and N2A; 98 mapped RBP channels. No localization intervention outcomes supplied the expression proxy.')
    add('Stability prior', 'None. Excluded prospectively after the resource audit.')
    add('GSE249405 contribution', 'Resource assessment and biological context only; no derived feature, coefficient, target, or mutant score.')
    add('Strongest geometry baseline', 'Frozen M0: 28 geometry/class/tier features, training-fold StandardScaler, weighted Ridge alpha=100, shared within-decision-set rank target. It is the fixed comparator, not a retrospectively chosen weak baseline.')
    add('3UTRBERT result', 'Matched Ridge R1 versus geometry: rank ContextValue +0.033165, regret ContextValue +0.031141. Frozen encoder and cache; not a successful universal compiler by itself.')
    add('Parnet output-space result', 'Not evaluated. Actual RBPNet matched-Ridge fallback: rank ContextValue +0.043792, regret ContextValue +0.025140. Do not label these Parnet results.')
    add('Parnet hidden-embedding result', 'Not evaluated; excluded representation.')
    add('Selected architecture', 'Primary nested family choices in outer folds 0–4: ' + ', '.join(primary['outer_fold_selected_family']) + '. M1 adds RBP summaries to geometry; M2 adds expression interactions; M3 fits a shared sparse latent score and assay heads. These are evaluated choices, not an endorsed final deployment model.')
    add('Latent measurement-process result', 'M3 versus M2 on leave-source transfers improves mean rank by +0.033135 and regret by +0.022382, but harms regret by >0.020 in both TDP direction tasks. Gate J fails; M3 is not retained as a validated measurement solution.')
    for number, metric in [(17, 'directional_rank_percentile'), (18, 'normalized_regret')]:
        add('Overall rank' if number == 17 else 'Overall regret', f'{source[metric].mean():.9f}, equal-source/direction average of held-biological-unit predictions.')
    add('Rank ContextValue over geometry', f"{selected['rank_context_value']:+.9f}.")
    add('Regret ContextValue over geometry', f"{selected['regret_context_value']:+.9f}; positive denotes reduced regret.")
    add('GoodSelection@3', f"{source.good_selection_at_3.mean():.9f}; gain over M0 {context.good3_context_value.mean():+.9f}.")
    add('GoodSelection@5', f"{source.good_selection_at_5.mean():.9f}; gain over M0 {context.good5_context_value.mean():+.9f}.")
    add('Biological-unit improvement fraction', f"{distributed['unit_improvement_fraction']:.9f} (54.46%), below the frozen 55% threshold; 213 units, both directions averaged per unit.")
    add('Median biological-unit ContextValue', f"Regret {distributed['positive_median_unit_regret_context_value']:+.9f}.")
    add('Leave-best-one-out', f"Equal-source mean regret ContextValue {distributed['leave_best_one_out_equal_source_mean']:+.9f}.")
    add('Bootstrap interval', 'Paired biological-unit bootstrap, 10,000 draws within source, both directions preserved: 95% interval ' + str(distributed['bootstrap_95_interval']) + '. Not a row bootstrap.')
    add('Mikl matched mechanism', 'Implemented uncapped analysis: +0.015818 rank, +0.017845 regret; 120 held genes. Its recorded Gate C pass is qualified: the written two-per-gene cap was omitted and conflicts with the minimum-four within-gene subset rule. Literal protocol compliance and RBP-specific mechanism are not established.')
    add('TDP mechanism', 'All TDP rows carry the TDP-43 UG-rich motif label, but no TARDBP channel exists. Exact-geometry descriptive audit: ' + str(tdp['usable_rows']) + ' usable rows, 150 two-candidate comparisons in six parents. This September 9 diagnostic is not a newly frozen success gate. Geometry predictions tie within these pairs; favorable performance in one direction is not a separately validated biological discovery. No direct TDP-43 binding claim is supported.\n\n' + table(pd.DataFrame(tdp['metrics'])))
    add('Moffatt held-parent result', 'Eight biological parents, held together regardless of row count.\n\n' + ctx(context[context.dataset.eq('moffatt_gse334718')]))
    for title, task in [('CAD→N2A', 'CAD_to_N2A'), ('N2A→CAD', 'N2A_to_CAD'), ('Firefly→GFP', 'Firefly_to_GFP'), ('GFP→Firefly', 'GFP_to_Firefly'), ('Leave Mikl out', 'leave_Mikl'), ('Leave TDP out', 'leave_TDP'), ('Leave Moffatt out', 'leave_Moffatt')]:
        add(title, 'Nested-selected transfer versus geometry:\n\n' + ctx(transfers[transfers.task.eq(task)]))
    for title, band in [('2–5 nt', '2-5'), ('6–10 nt', '6-10'), ('2–10 nt', '2-10'), ('Exact-SNV descriptive result', 'exact_1')]:
        row = bands.loc[band]
        add(title, f"Rank ContextValue {row.rank_context_value:+.9f}; regret ContextValue {row.regret_context_value:+.9f}; {int(row.candidate_rows)} candidate rows and {int(row.biological_units)} evaluable units. " + ('Descriptive only; cannot pass the small-edit gate.' if band == 'exact_1' else 'Frozen band boundaries were not changed.'))
    for title, result in zip(['RBP-permutation control', 'Delta-RBP shuffle control'], gate_g['controls']):
        add(title, f"Retained rank gain {100*result['rank_retained_fraction']:.2f}%, regret gain {100*result['regret_retained_fraction']:.2f}%; control still meets both Gate A thresholds. Necessity fails. " + ('The delta donor construction cycles unequal-size units and is not a bijective row shuffle.' if result['control'] == 'delta_rbp_shuffle' else ''))
    add('Cell-context-shuffle control', 'PENDING; no partial result is treated as final.' if cell is None else table(pd.DataFrame(cell['metrics'])) + '\n\nM1 is reused unchanged because it contains no expression features.')
    add('Parent-binding ablation', f"Knockout gain: rank {parent['knockout_rank_gain']:+.9f}, regret {parent['knockout_regret_gain']:+.9f}. Rank improves and roughly 89.36% of regret gain survives; aggregate necessity is not established.")
    add('Trans-interaction ablation', 'Gate H fails. M3 minus trans-knockout crossed-cell gain: rank +0.003888, regret +0.001199; insufficient for the frozen thresholds. Trans context is not supported for retention.')
    add('Stability ablation', 'Not applicable: no stability block was admitted. Gate I is neither pass nor fail.')
    add('Measurement-head ablation', 'Head randomization worsens pooled MSE 1.232723→1.789378 and Spearman 0.317235→0.068879. Equal-head MSE worsens but Spearman improves 0.155036→0.204898. Pre-head scores are unchanged by head reassignment. The added pooled-plus-macro conjunction was not an original frozen criterion; report the mixed evidence.')
    add('Evidence against edit-size shortcuts', 'Not established sufficiently for the compiler claim. Delta-RBP edit-size R-squared is 0.652844 in Moffatt and 0.864634 in TDP; Mikl is -0.341258. Matched Mikl estimates have a protocol qualification and identity/delta necessity fails. Predictive gain alone is not mechanistic evidence.')
    add('Direction-specific performance', table(pd.DataFrame(directions)) + '\n\nThese are equal-source descriptive means and the explicit unit-improvement fraction. Mechanism failures preclude claiming a validated directional compiler even if a mean-based condition were favorable.')
    add('Source robustness', 'Leave-source Gate D passes: 6/6 positive regret tasks, mean rank +0.093964, regret +0.069215; largest source share of positive regret 68.11%. Cell/reporter Gate E fails: 1/4 and 2/4 tasks respectively improve both metrics, and their mean regret gains are negative. Full task tables remain archived.')
    add('Seed stability', 'M3 equal-source rank SD 0.009394 and regret SD 0.004400; all three seeds agree that Gate J fails. M0–M2 repeated outer-fold-0 fits agree exactly in the tested runtime. Sparse-model archive reproduction differs at ~1e-6–1e-5, so do not claim cross-run archive equality at 1e-8.')
    add('Integrity deviations', 'See finalshot_integrity_review.md: Mikl cap contradiction/omission, selection tie-order ambiguity, non-bijective delta donors, head-control aggregation ambiguity, and sparse-model numerical reproduction limits. Gate L is not certified as an unqualified pass. Original outputs and protocol text were preserved.')
    add('Tests passed', str(test_counts) + '; recorded in submission_tests.xml. Software tests are not substitutes for scientific protocol fidelity.')
    add('Files created', 'Required reports: finalshot_resource_audit.md, finalshot_protocol.md, finalshot_rbp_representation.md, finalshot_trans_context.md, finalshot_stability_prior.md, finalshot_latent_measurement_model.md, finalshot_mikl_matched_mechanism.md, finalshot_transfer_results.md, finalshot_small_edit_results.md, finalshot_controls.md, finalshot_novelty_audit.md, finalshot_final_verdict.md. Supplemental integrity/shortcut reports and machine-readable predictions, metrics, coefficients, and audits are under reports/ and results/finalshot/.')
    commits = subprocess.check_output(['git', 'log', '-15', '--format=%h %s'], cwd=ROOT, text=True).strip()
    add('Commits', 'Key earlier checkpoints: 30c89a3 (protocol freeze), cbfc964 (completed RBP reconstruction). Recent checkpoint history at report generation (the report commit itself follows this snapshot):\n\n```text\n' + commits + '\n```')
    add('Astrocyte status', 'Sealed. No Astrocyte data and no N-zip outcomes were accessed in this work. No holdout opening is authorized by this report.')
    add('Is Phase C justified?', 'No. FULL GO requirements fail, and integrity qualifications remain.')
    add('Does original zero-shot RNAddress survive?', 'Not under the frozen evidentiary standards. Favorable average prediction scores do not meet distributed, transfer, small-edit, and mechanism requirements together.')
    add('Must the next hypothesis be RNAddress-Adapt?', 'If research continues, the protocol points to the separately defined few-shot active-design hypothesis RNAddress-Adapt, not another zero-shot cycle. No Adapt experiment is started or claimed validated here.')
    add('PV-CARE-level path for the original project?', 'No evidence-backed path to that success claim is established by this FinalShot. A transparent benchmark and negative-mechanism result may still be a useful research submission, but its acceptance, importance, or equivalence to PV-CARE is not guaranteed. Do not rename a failed universal compiler as a validated one.')
    assert len(answers) == 60
    status = 'DRAFT — COMPUTATIONAL RELEASE INCOMPLETE' if pending else 'FINAL RESULT CONSOLIDATION — WITH INTEGRITY QUALIFICATIONS'
    text = '# RNAddress FinalShot — required final return\n\n' + status + '\n\n'
    text += 'Scientific conclusion: **NO-GO — END ZERO-SHOT RNADDRESS**. This is not a claim that RNA localization cannot be engineered; it is a rejection of this tested universal zero-shot path under its own standards.\n\n'
    text += 'Novelty and primary-source comparisons: [fresh literature audit](finalshot_novelty_audit.md). Protocol fidelity: [integrity review](finalshot_integrity_review.md).\n\n'
    text += '## Gate overview\n\n' + table(pd.DataFrame([
        ('A', 'Pass numerically', 'Overall rank and regret thresholds met'),
        ('B', 'Fail', '54.46% of units improve; requires 55%'),
        ('C', 'Qualified / not certified', 'Recorded pass omits contradictory per-gene cap'),
        ('D', 'Pass numerically', 'Leave-source threshold met'),
        ('E', 'Fail', 'Cell and reporter transfer fail'),
        ('F', 'Fail', 'Small-edit bridge and 6–10 nt harm limit fail'),
        ('G', 'Fail', 'Identity and delta controls retain gains'),
        ('H', 'Fail', 'Trans context adds insufficient crossed-cell benefit'),
        ('I', 'Not applicable', 'Stability was excluded before evaluation'),
        ('J', 'Fail', 'Two source-direction tasks exceed harm limit'),
        ('K', 'Repeated-smoke/seed conditions met', 'Cross-run sparse-model archive equality remains limited'),
        ('L', 'Not certified', 'Protocol/implementation discrepancies disclosed'),
    ], columns=['Gate', 'Status', 'Reason'])) + '\n\n'
    text += '\n\n'.join(f'## {i}. {title}\n\n{answer}' for i, (title, answer) in enumerate(answers, 1)) + '\n'
    (REPORTS / 'finalshot_final_verdict.md').write_text(text, encoding='utf-8')
    controls = '# FinalShot controls — consolidated status\n\n' + status + '\n\n'
    controls += '\n\n'.join(f'## {title}\n\n{answer}' for title, answer in answers[40:48])
    controls += '\n\nSee finalshot_integrity_review.md for limitations of the control implementations. No threshold was changed after results.\n'
    (REPORTS / 'finalshot_controls.md').write_text(controls, encoding='utf-8')
    (OUT / 'submission_status.json').write_text(json.dumps({'scientific_verdict': 'NO-GO — END ZERO-SHOT RNADDRESS',
        'release_complete': not pending, 'pending': pending, 'integrity_gate_unqualified_pass': False,
        'required_return_items': len(answers), 'tests': test_counts}, indent=2)+'\n', encoding='utf-8')
    print(status, flush=True)


if __name__ == '__main__':
    main()
