"""Trace the admitted Table 5 and repeat only the archived count arithmetic.

No model fitting, new outcomes, raw recount, strand search or pooling estimates.
Run --freeze once before run; immutable files make accidental replacement fail.
"""
from .evidence_io_20260925 import ROOT, ART, sha256, save_json, save_csv, read_json
import argparse
from datetime import datetime, timezone
import hashlib
import io
import itertools
import math
from pathlib import Path
import zipfile
import numpy as np
import openpyxl
import pandas as pd

OUT = ROOT / 'results/research_20260921'
DATA = ROOT / 'data/external/research_20260921'
RUNS = {'Cyto1': 'HRR3059160', 'Cyto2': 'HRR3059161', 'Cyto3': 'HRR3059162',
        'Nuc1': 'HRR3059163', 'Nuc2': 'HRR3059164', 'Nuc3': 'HRR3059165'}
PINNED = {
 'data/external/research_20260921/srle_epmc_supplement': 'ff42cc9b5d7f0bb703369370cfc29c1d51614bca677294a2ffbb3bbec61344a9',
 'data/external/research_20260921/srle_gsa_runs_all': 'c102edb0bac484c019b828f9c216e75419f9c78e723d3587571af7e3f9ff27de',
 'results/research_20260921/raw_sixmer_counts.csv': '22655b4c911522adb9e11e5e45ddb4abe9d5be72d370df14f0b15fa3967c5b00',
 'results/research_20260921/raw_replication_scores.csv': 'facfcc7b9a286911b965c63c0c0c0c7d730275459c7abaa16c2d0752222f08b5',
 'results/research_20260921/pilot_a_predictions.csv': '569f070dee200c0bc71663335d2cffef4de3406e91beef59ceecd73bc38a053e',
 'results/research_20260921/robustness_predictions.csv': '8b337f7d7d4910c10049e33b780d97ee5a8982bf3335305626ed58d1baadf362',
 'results/research_20260921/raw_counts_qc.json': 'f88bfaadd6734f72ac8425831b725fcb06f5519490947de0ee8fc900c3bb07f4',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fixed_nrs(nuc, cyto, nuc_depth, cyto_depth):
    require(min(nuc, cyto, nuc_depth, cyto_depth) >= 0, 'Negative count')
    require(all(math.isfinite(x) for x in (nuc, cyto, nuc_depth, cyto_depth)), 'Nonfinite count')
    return math.log2((nuc + .5) / (nuc_depth + 2048)) - math.log2((cyto + .5) / (cyto_depth + 2048))


def exhaustive(frame):
    require(len(frame) == 4096 and not frame.kmer.duplicated().any(), 'Missing/duplicate six-mer')
    require(set(frame.kmer) == {''.join(x) for x in itertools.product('ACGT', repeat=6)}, 'Alphabet mismatch')


def freeze():
    for path, expected in PINNED.items():
        require(sha256(ROOT / path) == expected, 'Historical input changed: ' + path)
    extra = [Path(__file__), Path(__file__).with_name('evidence_io_20260925.py'),
             Path(__file__).with_name('raw_counts.py'), Path(__file__).with_name('pilots.py'),
             ROOT / 'reports/research_20260921/provenance_work_scope_20260925.md']
    extra += sorted((DATA / 'srle_reads').glob('HRR*.fq.gz.receipt.json'))
    files = dict(PINNED)
    files.update({p.relative_to(ROOT).as_posix(): sha256(p) for p in extra})
    return save_json('lineage_config.json', {'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'posthoc measurement audit, no biological gate or optimization',
        'inputs': files, 'runs': RUNS, 'tolerance': 1e-12, 'pseudocount': .5,
        'count_eligibility': 'all four admitted libraries >=20; unchanged',
        'normalization': 'per-library accepted depth plus 4096*0.5',
        'missing_rep3': 'no score/count inference', 'seed': None})


def run():
    config = read_json(ART / 'lineage_config.json')
    for name, expected in config['inputs'].items():
        require(sha256(ROOT / name) == expected, 'Frozen audit input changed: ' + name)
    with zipfile.ZipFile(DATA / 'srle_epmc_supplement') as outer:
        with zipfile.ZipFile(io.BytesIO(outer.read('csbj.0107.f1.zip'))) as inner:
            payload = inner.read('Supplement Table5.xlsx')
    wb = openpyxl.load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
    sheet = wb.active
    require(sheet.title == 'Table S5', 'Unexpected worksheet')
    values = list(sheet.values)
    require(values[1][0] == 'kmer' and values[1][6] == 'NRS(log2FC)', 'Unexpected table schema')
    table = pd.DataFrame([{'excel_row': n, 'original_sequence': row[0],
        'kmer': row[0].upper().replace('U', 'T'), 'published': float(row[6])}
        for n, row in enumerate(values[2:], 3)])
    wb.close()
    exhaustive(table)
    table = table.sort_values('kmer').reset_index(drop=True)
    require(np.isfinite(table.published).all(), 'Nonfinite published score')
    names = ['raw_sixmer_counts.csv', 'raw_replication_scores.csv', 'pilot_a_predictions.csv', 'robustness_predictions.csv']
    frames = [pd.read_csv(OUT / n, float_precision='round_trip').sort_values('kmer').reset_index(drop=True) for n in names]
    for frame in frames:
        exhaustive(frame)
        require(list(frame.kmer) == list(table.kmer), 'Join mismatch')
    counts, scores, pilot, robust = frames
    for sample in ('Cyto1', 'Cyto2', 'Nuc1', 'Nuc2'):
        require(np.array_equal(counts[sample], scores[sample]), 'Count copies differ')
        require(((counts[sample] >= 0) & (counts[sample] % 1 == 0)).all(), 'Invalid integer count')
    eligible = (counts[['Cyto1', 'Cyto2', 'Nuc1', 'Nuc2']] >= 20).all(axis=1)
    require(np.array_equal(eligible, scores.eligible), 'Eligibility changed')
    expected_test = [int(hashlib.sha256(('srle-order-20260921|' + s).encode()).hexdigest(), 16) % 5 == 0 for s in table.kmer]
    require(np.array_equal(expected_test, pilot.test) and np.array_equal(pilot.test, robust.test), 'Frozen split mismatch')
    differences = {n: float(np.max(np.abs(table.published - frame[column]))) for n, frame, column in
        [('pilot', pilot, 'nrs'), ('robustness', robust, 'nrs'), ('archived_raw_score_published', scores, 'published_forward')]}
    require(max(differences.values()) <= 1e-12, 'Published benchmark identity failed')
    qc = read_json(OUT / 'raw_counts_qc.json')
    metadata = read_json(DATA / 'srle_gsa_runs_all')['runViews']
    sample_rows, files = [], {}
    for sample, accession in RUNS.items():
        entries = [r for r in metadata if r['runAcc'] == accession]
        require(len(entries) == 2, 'Expected two archived mates')
        require(len({r['sampleAcc'] for r in entries}) == 1, 'Ambiguous archive sample')
        require(all(r['runTitle'] == '6mer_' + sample[:-1] + '_Sample' + sample[-1] for r in entries), 'Label mismatch')
        records = []
        for entry in sorted(entries, key=lambda r: r['runFileName']):
            raw = DATA / 'srle_reads' / entry['runFileName']
            if sample[-1] != '3':
                receipt = read_json(raw.with_name(raw.name + '.receipt.json'))
                require(raw.stat().st_size == receipt['bytes'] and sha256(raw) == receipt['sha256'], 'Raw file integrity failed')
                require(receipt['sample_accession'] == entry['sampleAcc'], 'Receipt sample mismatch')
                records.append({'file': raw.relative_to(ROOT).as_posix(), 'sha256': receipt['sha256']})
            else:
                records.append({'file': entry['runFileName'], 'sha256': ''})
        files[sample] = records
        depth = int(counts[sample].sum()) if sample in counts else ''
        if depth != '':
            require(depth == qc[accession]['accepted'], 'Count denominator differs from QC')
        sample_rows.append({'sample': sample, 'run_accession': accession,
            'experimental_sample_id': entries[0]['sampleAcc'], 'biosample': entries[0]['biosampleAcc'],
            'experiment': entries[0]['expName'], 'archive_label': entries[0]['runTitle'],
            'accepted_fragments': depth, 'raw_files': '|'.join(x['file'] for x in records),
            'raw_sha256': '|'.join(x['sha256'] for x in records), 'metadata_mapping_status': 'VERIFIED',
            'biological_identity_status': 'AMBIGUOUS' if sample[-1] == '3' else 'STRONGLY_SUPPORTED',
            'issue': 'Replicate-3 prefixes match differently labeled MALAT1 runs; full identity unresolved' if sample[-1] == '3' else 'Archive label is not independent experimental identity verification'})
    nrs = {rep: np.array([fixed_nrs(n, c, int(counts['Nuc'+rep].sum()), int(counts['Cyto'+rep].sum()))
        for n, c in zip(counts['Nuc'+rep], counts['Cyto'+rep])]) for rep in ('1', '2')}
    errors = {rep: float(np.max(np.abs(nrs[rep] - scores['NRS'+rep]))) for rep in nrs}
    require(max(errors.values()) <= 1e-12, 'Archived NRS arithmetic failed')
    lineage = []
    for i, row in table.iterrows():
        for manifest in sample_rows:
            sample, rep = manifest['sample'], manifest['sample'][-1]
            measured = rep in nrs
            local_score = float(nrs[rep][i]) if measured else ''
            lineage.append({'benchmark_row_id': int(i), 'sequence': row.kmer,
                'original_table_sequence': row.original_sequence,
                'parent_context': 'HBB 3prime UTR six-mer reporter; study-level context',
                'context_status': 'STRONGLY_SUPPORTED', 'construct_id': '', 'construct_status': 'UNRESOLVED',
                'experimental_sample_id': manifest['experimental_sample_id'], 'sample': sample, 'replicate_label': rep,
                'raw_accession': manifest['run_accession'], 'raw_files': manifest['raw_files'], 'raw_sha256': manifest['raw_sha256'],
                'count_source': 'results/research_20260921/raw_sixmer_counts.csv' if measured else '',
                'raw_fragment_count': int(counts.loc[i, sample]) if measured else '',
                'accepted_depth': manifest['accepted_fragments'],
                'preprocessing_script': 'src/research_20260921/raw_counts.py' if measured else '',
                'counting_rule': 'one concordant fragment; exact flanks; insert Q20; orientation normalized' if measured else '',
                'normalization': 'log2((Nuc+0.5)/(sumNuc+2048))-log2((Cyto+0.5)/(sumCyto+2048))' if measured else '',
                'published_table_row': 'Supplement Table5.xlsx|Table S5|' + str(row.excel_row),
                'reconstructed_replicate_value': local_score, 'published_aggregate_value': float(row.published),
                'absolute_difference_replicate_vs_aggregate': abs(local_score - row.published) if measured else '',
                'difference_interpretation': 'different quantities; not a Table5 reconstruction error',
                'archived_arithmetic_absolute_error': abs(local_score - scores.loc[i, 'NRS'+rep]) if measured else '',
                'benchmark_table_absolute_error': abs(float(pilot.loc[i, 'nrs']) - row.published),
                'benchmark_partition': 'test' if expected_test[i] else 'train',
                'raw_count_eligible': bool(eligible[i]), 'table_mapping_confidence': 'VERIFIED',
                'sample_identity_confidence': manifest['biological_identity_status'],
                'published_production_chain': 'UNRESOLVED',
                'unresolved_issue': 'Author replicate count matrix, pooling/DESeq2 coefficient, filtering, zero policy and Table5 export absent; construct identifier unknown' + ('; replicate3 count/identity unresolved' if not measured else '')})
    save_csv('srle_samples.csv', sample_rows)
    save_csv('srle_measurement_lineage.csv', lineage)
    summary = {'determination': 'PARTIAL', 'published_table_mapping': 'PASS', 'local_saved_count_arithmetic': 'PASS',
        'author_raw_to_Table5_reconstruction': 'UNRESOLVED', 'sequences': 4096, 'lineage_rows': len(lineage),
        'quantified_libraries': 4, 'unquantified_libraries': 2, 'raw_files_rehashed': 8,
        'accepted_fragments': sum(q['accepted'] for q in qc.values()), 'read_pairs': sum(q['pairs'] for q in qc.values()),
        'count_eligible_sequences': int(eligible.sum()), 'test_sequences': int(sum(expected_test)),
        'table_mapping_max_absolute_errors': differences, 'replicate_arithmetic_max_absolute_errors': errors,
        'replicate_vs_published_aggregate': {rep: {'mean_absolute_difference': float(np.mean(np.abs(nrs[rep]-table.published))),
            'max_absolute_difference': float(np.max(np.abs(nrs[rep]-table.published))),
            'interpretation': 'Different quantities; no equality expected or normalization selected'} for rep in nrs},
        'workbook_sha256': hashlib.sha256(payload).hexdigest(), 'config_sha256': sha256(ART / 'lineage_config.json'),
        'outputs': {n: sha256(ART / n) for n in ('srle_samples.csv', 'srle_measurement_lineage.csv')},
        'scope': 'Fresh calculation from saved counts; raw files integrity-checked, not recounted; not independent biology'}
    save_json('srle_lineage_result.json', summary)
    print(__import__('json').dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    args = parser.parse_args()
    print(freeze()) if args.freeze else run()
