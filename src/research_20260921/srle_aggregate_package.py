"""Package only existing SRLE aggregate metrics for standalone arithmetic replay."""
from .common import ROOT, sha256, write_new, write_json
from .srle_aggregate_replay import replay, MEMBERS
from pathlib import Path
import io
import json
import zipfile
import numpy as np
import pandas as pd

OUT = ROOT / 'results/research_20260921'
REPORT = ROOT / 'reports/research_20260921'
RELEASE = OUT / 'srle_aggregate_replay_20260924'
CHECKPOINT_HASH = 'bc35263bda2d97cf27d7e2eca0f2902fbb76d7afba0d531a85a25335124c4e12'


def run():
    checkpoint = OUT / 'checkpoint_receipt.json'
    if sha256(checkpoint) != CHECKPOINT_HASH:
        raise ValueError('Historical checkpoint changed')
    hashes = json.loads(checkpoint.read_text())['artifact_hashes']
    files = [OUT / n for n in ('raw_swap_evaluation.csv', 'raw_swap_result.json',
                               'raw_swap_freeze.json', 'robustness_predictions.csv')]
    for p in files:
        if sha256(p) != hashes[p.relative_to(ROOT).as_posix()]:
            raise ValueError('Archived input changed: ' + p.name)
    fields = ['composition', 'replicate', 'model', 'direction',
              'regret_gain', 'oriented_nrs_change']
    # Do not load parent or selected-sequence columns; only saved evaluation metrics.
    frame = pd.read_csv(OUT / 'raw_swap_evaluation.csv', usecols=fields)
    classes = sorted(frame.composition.unique())
    if len(classes) != 60:
        raise ValueError('Unexpected composition-class count')
    frame['class_id'] = frame.composition.map({k: i for i, k in enumerate(classes)})
    group = frame.groupby(['class_id', 'replicate', 'model', 'direction'], sort=True)
    aggregate = group.agg(record_count=('regret_gain', 'size'),
                          mean_regret_gain=('regret_gain', 'mean'),
                          mean_oriented_nrs_change=('oriented_nrs_change', 'mean')).reset_index()
    write_new(RELEASE / 'group_metrics.csv', aggregate.to_csv(index=False, lineterminator='\n').encode())
    # Exactly the archived RNG, seed, shape and ordering. Store draws so replay
    # requires only Python's standard library and preserves pairing across models.
    draws = np.random.default_rng(20260921).integers(0, 60, (2000, 60))
    buffer = io.StringIO()
    np.savetxt(buffer, draws, fmt='%d', delimiter=',', newline='\n')
    write_new(RELEASE / 'bootstrap_indices.csv', buffer.getvalue().encode())
    expected = json.loads((OUT / 'raw_swap_result.json').read_text())
    expected['removed_low_count_parent_count'] = len(expected.pop('removed_low_count_parents'))
    write_json(RELEASE / 'expected_summary.json', expected)
    for source, destination in [(REPORT / 'srle_replay_readme_20260924.md', 'README.md'),
                                (REPORT / 'srle_evidence_ledger_20260924.md', 'evidence_ledger.md'),
                                (ROOT / 'src/research_20260921/srle_aggregate_replay.py', 'replay.py')]:
        write_new(RELEASE / destination, source.read_bytes())
    provenance = {'date': '2026-09-24', 'kind': 'anonymized aggregate arithmetic replay',
                  'original_checkpoint_sha256': CHECKPOINT_HASH,
                  'original_artifacts': {p.relative_to(ROOT).as_posix(): sha256(p) for p in files},
                  'builder_sha256': sha256(Path(__file__)),
                  'aggregation': 'One row per original composition class, replicate, model and direction; classes retain original sorted order; sequence identifiers omitted.',
                  'bootstrap': {'generator': 'numpy.random.default_rng / PCG64',
                                'numpy_version': np.__version__, 'seed': 20260921,
                                'draws': 2000, 'classes_per_draw': 60,
                                'pairing': 'Identical indices across models and replicates'},
                  'historical_freeze_gap': 'raw_swap_freeze.json omitted robustness_predictions.csv and imported modules. The later checkpoint hash includes the former; this cannot retroactively expand the prospective freeze.',
                  'no_new_outcomes': True, 'models_fit': 0, 'downloads': 0,
                  'scope_limit': 'Reproduces aggregate arithmetic, not training, candidate construction, raw counts, or independent biological validation.'}
    write_json(RELEASE / 'provenance.json', provenance)
    write_json(RELEASE / 'integrity.json', {'files': {n: sha256(RELEASE / n) for n in MEMBERS},
                                          'note': 'Integrity detects changed package files, not authenticity against replacement of both data and manifest.'})
    result = replay(RELEASE)
    write_json(OUT / 'srle_aggregate_replay_result_20260924.json', result)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted((*MEMBERS, 'integrity.json')):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 24, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (RELEASE / name).read_bytes())
    bundle = OUT / 'srle_aggregate_replay_20260924.zip'
    write_new(bundle, payload.getvalue())
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != 8:
            raise ValueError('Release archive failed integrity')
    write_json(OUT / 'srle_aggregate_package_receipt_20260924.json', {
        'zip_sha256': sha256(bundle), 'bytes': bundle.stat().st_size,
        'member_hashes': {n: sha256(RELEASE / n) for n in (*MEMBERS, 'integrity.json')},
        'replay_result_sha256': sha256(OUT / 'srle_aggregate_replay_result_20260924.json'),
        'status': result['status'], 'scope': provenance['scope_limit']})
    print(json.dumps({k: v for k, v in result.items() if k != 'summary'}, indent=2))
    print(str(bundle), bundle.stat().st_size, sha256(bundle))


if __name__ == '__main__':
    run()
