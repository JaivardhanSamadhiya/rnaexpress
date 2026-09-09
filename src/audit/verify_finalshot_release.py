"""Verify and inventory the completed release without changing scientific results."""
import argparse
import json
import re
import subprocess
from pathlib import Path
import numpy as np
from src.analysis.run_finalshot_direct_models import sha256

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/finalshot'
DESTINATION = OUT / 'release_verification_manifest.json'
REQUIRED_REPORTS = (
    'resource_audit', 'protocol', 'rbp_representation', 'trans_context',
    'stability_prior', 'latent_measurement_model', 'mikl_matched_mechanism',
    'transfer_results', 'small_edit_results', 'controls', 'novelty_audit', 'final_verdict',
)


def verify_prediction_archive(path):
    with np.load(path, allow_pickle=False) as archive:
        inspected = []
        for name in ('prediction', 'latent_prediction', 'calibrated_prediction', 'seed_predictions'):
            if name in archive:
                values = archive[name]
                assert np.isfinite(values).all(), (path, name, 'nonfinite')
                if 'test_indices' in archive:
                    assert values.shape[-1] == len(archive['test_indices']), (path, name, 'row count')
                inspected.append(name)
        if 'seed_predictions' in archive and 'prediction' in archive:
            assert np.array_equal(archive['prediction'], archive['seed_predictions'].mean(axis=0)), (path, 'seed mean')
        if 'test_indices' in archive:
            assert len(np.unique(archive['test_indices'])) == len(archive['test_indices']), (path, 'duplicate row indices')
    return inspected


def verify_inventory(manifest):
    for record in manifest['artifacts']:
        path = ROOT / record['path']
        assert path.stat().st_size == record['bytes'], path
        assert sha256(path) == record['sha256'], path


def main(check_only=False):
    if check_only:
        manifest = json.loads(DESTINATION.read_text(encoding='utf-8'))
        verify_inventory(manifest)
        print(f"Verified all {len(manifest['artifacts'])} release artifact hashes", flush=True)
        return
    status = json.loads((OUT / 'submission_status.json').read_text())
    assert status['release_complete'] and not status['pending']
    assert status['tests']['tests'] >= 36 and status['tests']['failures'] == status['tests']['errors'] == 0
    assert status['scientific_verdict'] == 'NO-GO — END ZERO-SHOT RNADDRESS'
    assert status['integrity_gate_unqualified_pass'] is False
    for name in REQUIRED_REPORTS:
        assert (ROOT / f'reports/finalshot_{name}.md').is_file()
    report = (ROOT / 'reports/finalshot_final_verdict.md').read_text(encoding='utf-8')
    assert [int(n) for n in re.findall(r'^## (\d+)\.', report, flags=re.M)] == list(range(1, 61))
    assert 'DRAFT' not in report and 'PENDING' not in report
    cell = json.loads((OUT / 'cell_context_control_summary.json').read_text())
    assert cell['rows'] == 93208 and len(cell['selected_families']) == 5
    assert len(cell['archive_audit']) == 15
    assert {(a['family'], a['fold']) for a in cell['archive_audit']} == {(f, n) for f in ('M1','M2','M3') for n in range(5)}
    for record in cell['archive_audit']:
        assert sha256(ROOT / record['path']) == record['sha256']
    frozen_paths = ['results/finalshot', 'results/v4_phaseB/model_candidate_rows.csv.gz',
        'results/v4_phaseB/model_interventions.csv.gz', 'reports/finalshot_protocol.md',
        'src/modeling/finalshot_models.py', 'src/modeling/finalshot_controls.py',
        'src/analysis/run_finalshot_direct_models.py', 'src/analysis/run_finalshot_m3.py',
        'src/analysis/summarize_finalshot_m3.py', 'src/analysis/analyze_finalshot_grouped_gates.py']
    changed = subprocess.check_output(['git','diff','--name-only','--diff-filter=MD','5910dd7','--',*frozen_paths], cwd=ROOT, text=True).splitlines()
    assert not changed, ('Previously archived results/frozen implementation modified', changed)
    archive_audit = []
    for path in sorted(OUT.rglob('*.npz')):
        archive_audit.append({'path': path.relative_to(ROOT).as_posix(),
                              'prediction_arrays_checked': verify_prediction_archive(path)})
    paths = set(p for p in OUT.rglob('*') if p.is_file() and p != DESTINATION)
    paths.update((ROOT/'reports').glob('finalshot*.md'))
    for directory in ('src/analysis', 'src/modeling', 'src/features', 'src/audit', 'tests'):
        paths.update((ROOT/directory).glob('*finalshot*.py'))
    artifacts = [{'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
                  'sha256': sha256(path)} for path in sorted(paths)]
    result = {'release_status': 'complete with scientific integrity qualifications',
        'scientific_verdict': status['scientific_verdict'], 'tests': status['tests'],
        'required_report_count': len(REQUIRED_REPORTS), 'required_return_items': 60,
        'cell_outer_folds': 5, 'prior_result_preservation_reference': '5910dd7',
        'prior_result_modifications': changed, 'prediction_archive_count': len(archive_audit),
        'prediction_archive_checks': archive_audit, 'artifacts': artifacts,
        'scope': 'Release artifact hashes, required report/return completeness, finite aligned prediction arrays, seed means, and preservation of previously archived results. Not certification of Gate L or a replay of training.',
        'external_cache_audit': 'results/finalshot/reconstruction_reverification_20260909.json',
        'nzip_outcomes_accessed': False, 'astrocyte_data_accessed': False}
    verify_inventory(result)
    DESTINATION.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(f'Verified {len(artifacts)} release artifacts and {len(archive_audit)} prediction archives', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-only', action='store_true')
    main(parser.parse_args().check_only)
