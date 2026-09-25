"""Add omitted historical controls and exact uniform references to the ledger.

Preserves the initial catalogue. Corrects its SEERS citation to the primary
quality-audit report; no metric, interpretation or original result is changed.
"""
from .evidence_io_20260925 import ROOT, ART, sha256, read_json, save_json, save_csv, save
from pathlib import Path


def run():
    rows = read_json(ART / 'claim_evidence_ledger.json')
    corrections = []
    for row in rows:
        if row['claim'] == 'Relaxed SEERS quality restores transfer':
            corrections.append({'claim_id': row['claim_id'], 'change': 'Direct evidence citation corrected; estimate unchanged',
                'previous_source': row['artifact_path']})
            path = 'reports/research_20260921/measurement_followup_20260923.md'
            row.update(analysis=path, artifact_path=path, artifact_sha256=sha256(ROOT/path))
    def add(claim, dataset, metric, estimate, uncertainty, baseline, category, caveat, path, protocol='frozen gate'):
        rows.append({'claim_id': 'C%03d'%(len(rows)+1), 'claim': claim, 'dataset': dataset, 'analysis': path,
            'metric': metric, 'estimate': estimate, 'uncertainty': uncertainty, 'baseline': baseline,
            'protocol_status': protocol, 'independent': 'No new independent confirmation; see caveat',
            'confirmatory_exploratory': 'historical frozen evaluation' if protocol=='frozen gate' else 'exploratory/descriptive',
            'support_category': category, 'supports_claim': 'yes, bounded' if category=='bounded_supportive' else 'no',
            'caveat': caveat, 'artifact_path': path, 'artifact_sha256': sha256(ROOT/path)})
    add('Seed averaging rescues factorized ranking','historical N-zip','rank percentile','.575 vs original .662; metadata .612',
        'seven frozen seeds ranged .551-.662','metadata and forward','unsupported',
        'Averaging removed the favorable-seed appearance; correlation improvement did not fix top-choice regret. Historical labels later uncertified.',
        'reports/v2_1_stability_results.md')
    add('Magnitude and extreme heads find the best interventions','historical v3','regret / oracle recovery',
        '.409814 regret; .017438 gain; top5 0/30','required gain .03; near-oracle 3/30 vs required6/30',
        'v2.6 ranker','unsupported','Better rank did not recover best edits; shuffled null and robustness gates failed; N-zip truth later uncertified.',
        'reports/v3_phase3_model_selection.md')
    add('Confidence-based abstention controls recommendation error','historical v3','confidence-regret association / selective gain',
        'rho -.117961; 60% coverage regret gain .004970','required rho <=-.20 and gain >=.03',
        'all recommendations','unsupported','Coverage-regret curve was not monotonic; no threshold promoted; later N-zip truth caveat applies.',
        'reports/v3_selective_prediction_results.md')
    add('Independent external stability prediction is usable as a localization feature','Su/Wang RNA decay',
        'OOF Spearman / MSE improvement','SH .03672/-3.295%; HEK -.02707/-4.754%',
        'SH rho [-.04454,.11936]; HEK [-.09265,.03977]', 'training mean and zero-delta', 'unsupported',
        'Both admission gates failed on independent RNA-decay data; no final model exported. This is not evidence that stability is biologically irrelevant.',
        'reports/mechanism_v2/stability_external_model.md')
    source = 'results/research_20260921/srle_uniform_risk_result_20260924.json'
    result = read_json(ROOT/source)['comparisons']
    table = []
    fixed = read_json(ROOT/'results/research_20260921/srle_fixed_choice_risk_result_20260924.json')
    for model in ('uniform','composition','position_additive','kmer123','position_pair'):
        for direction in ('-1','1'):
            vals = result['uniform'][direction]['paired_replicates'] if model=='uniform' else fixed['models'][model][direction]['paired_replicates']
            row = {'model': model, 'direction': 'decrease' if direction=='-1' else 'increase'}
            for metric in ('fraction_positive_both','fraction_negative_both'):
                row[metric] = vals[metric]['estimate']
                row[metric+'_ci_low'],row[metric+'_ci_high'] = vals[metric]['descriptive_ci95']
            table.append(row)
            if model=='uniform':
                for metric in ('fraction_positive_both','fraction_negative_both'):
                    add('Matched uniform reference '+metric,'SRLE',metric+'; direction='+direction,vals[metric]['estimate'],
                        str(vals[metric]['descriptive_ci95']),'exact per-parent candidate enumeration','bounded_supportive',
                        'One candidate identity retained across two replicates; nonlinear metric evaluated before averaging; class-balanced.',source,'posthoc frozen arithmetic')
            elif model in ('position_pair','kmer123'):
                for metric in ('fraction_positive_both','fraction_negative_both'):
                    value = result['model_minus_uniform'][model][direction]['paired_replicates'][metric]
                    add('Learned selector changes '+metric+' relative to matched uniform','SRLE',model+'; '+metric+'; direction='+direction,
                        value['estimate'],str(value['descriptive_ci95']),'exact matched uniform','bounded_supportive',
                        'Model minus uniform; lower negative-both and higher positive-both are favorable. Descriptive paired-class CI, shared experiment.',
                        source,'posthoc frozen arithmetic')
    save_csv('claim_evidence_ledger_final.csv', rows)
    save_json('claim_evidence_ledger_final.json', rows)
    save_csv('srle_comparator_table.csv', table)
    lines = ['# Final major-claim evidence ledger', '',
        'AI-authored audit, not student submission prose. Historical labels and protocols require the caveats in each row. No cross-assay averaging.', '',
        '| ID | Approach / claim | Estimate and uncertainty | Status and limitation |','|---|---|---|---|']
    for r in rows:
        vals = {k:str(v).replace('|','/') for k,v in r.items()}
        vals['link'] = (ROOT/r['artifact_path']).as_posix()
        lines.append('| {claim_id} | {claim} | {estimate}; {uncertainty} | **{support_category}**. {caveat} [Source]({link}) |'.format(**vals))
    save('claim_evidence_ledger_final.md', ('\n'.join(lines)+'\n').encode())
    save_json('final_ledger_receipt.json', {'claims':len(rows), 'corrections': corrections,
        'initial_ledger_sha256':sha256(ART/'claim_evidence_ledger.json'), 'script_sha256':sha256(Path(__file__)),
        'outputs':{n:sha256(ART/n) for n in ('claim_evidence_ledger_final.csv','claim_evidence_ledger_final.json','claim_evidence_ledger_final.md','srle_comparator_table.csv')}})
    print('Final ledger:',len(rows),'claims')


if __name__ == '__main__':
    run()
