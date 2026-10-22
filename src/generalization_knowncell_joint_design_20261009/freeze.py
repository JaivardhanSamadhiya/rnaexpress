"""Read source/summary manifests only; never open core, row tables or arrays."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from .spec import NS, ALIASES, ARMS, CONFIGS, COUNTS, GATE, POLICY, METADATA_COLUMNS

ROOT = Path(__file__).resolve().parents[2]
SRC, REP, OUT = [ROOT / folder / NS for folder in ('src', 'reports', 'results')]
REFERENCE_FILES = (
    'src/cross_assay_20260927/models.py',
    'src/generalization_20261007/route_scaling.py',
    'src/generalization_20261007/common.py',
    'src/generalization_crosscell_20261007/common.py',
    'src/generalization_crosscell_20261007/prepare.py',
    'src/generalization_crosscell_20261007/splits.py',
    'src/generalization_crosscell_20261007/engine.py',
    'src/generalization_crosscell_20261007/gate.py',
    'src/generalization_crosscell_20261007/bootstrap.py',
    'src/generalization_knowncell_20261007/common.py',
    'src/generalization_knowncell_20261007/splits.py',
    'src/generalization_knowncell_20261007/prepare.py',
    'src/generalization_rbp_cellaxis_20261007/spec.py',
    'reports/generalization_knowncell_20261007/protocol.md',
    'reports/generalization_rbp_cellaxis_20261007/protocol.md',
    'reports/generalization_model_gap_audit_20261009/audit.md',
    'reports/generalization_model_gap_audit_20261009/source_provenance_01.json',
    ALIASES['source_prefit'], ALIASES['source_metadata'], ALIASES['known_metadata'],
)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(65536), b''): h.update(block)
    return h.hexdigest()


def read(path):
    assert path.stat().st_size <= 2 * 2**20
    def pairs(items):
        result = {}
        for key, value in items:
            assert key not in result
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)


def run():
    original = {rel: sha(ROOT / rel) for rel in REFERENCE_FILES}
    receipt_path = OUT / 'synthetic_tests_receipt.json'
    receipt = read(receipt_path)
    assert receipt['status'] == 'PASS_INVENTED_STDLIB_DESIGN_CHECKS'
    assert receipt['actual_optimizer_calls'] == receipt['project_dataset_reads'] == receipt['project_feature_reads'] == receipt['project_outcome_reads'] == 0
    own_sources = sorted(SRC.glob('*.py'))
    assert receipt['source_files'] == {p.relative_to(ROOT).as_posix(): sha(p) for p in own_sources}
    for path in own_sources: ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    old = read(ROOT / ALIASES['source_prefit'])
    committed = subprocess.check_output(['git', 'show', 'HEAD:' + ALIASES['source_prefit']], cwd=ROOT)
    assert committed == (ROOT / ALIASES['source_prefit']).read_bytes()
    filemap = {}
    for rel, digest in old['files'].items():
        key = rel.replace('\\', '/')
        assert key not in filemap, 'Alias collision in original manifest'
        filemap[key] = digest
    source, known = read(ROOT / ALIASES['source_metadata']), read(ROOT / ALIASES['known_metadata'])
    assert source['status'] == known['status'] == 'PASS'
    assert source['rows'] == known['rows'] == COUNTS['all_rows']
    assert source['components'] == known['paired_components'] == COUNTS['components']
    assert known['exact_paired_menus'] == COUNTS['paired_menus'] and known['paired_rows'] == COUNTS['paired_rows']
    assert known['unmatched_contexts'] == COUNTS['unmatched_contexts'] and known['unmatched_rows'] == COUNTS['unmatched_rows']
    assert source['core_sha256'] == known['core_sha256'] == filemap[ALIASES['core']]
    assert source['row_ids_sha256'] == known['row_ids_sha256']
    assert known['source_prefit_sha256'] == original[ALIASES['source_prefit']]
    own = own_sources + [SRC / '.gitattributes', REP / '.gitattributes', REP / 'protocol.md',
                         OUT / '.gitattributes', receipt_path]
    files = {**original, **{p.relative_to(ROOT).as_posix(): sha(p) for p in own}}
    payload = {'status': 'FROZEN_STATIC_JOINT_KNOWNCELL_DESIGN_NOT_PROJECT_ADMISSION',
               'prepared_date': '2026-10-21', 'generated_utc': datetime.now(timezone.utc).isoformat(),
               'observed_git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'files': files, 'arms': ARMS, 'configs': CONFIGS, 'counts': COUNTS,
               'gate': GATE, 'policy': POLICY, 'metadata_columns': METADATA_COLUMNS,
               'declared_future_inputs_not_opened': {
                   ALIASES['core']: {'declared_sha256': filemap[ALIASES['core']], 'actual_bytes_rehashed': False},
                   ALIASES['feature']: {'declared_sha256': filemap[ALIASES['feature']], 'actual_bytes_rehashed': False}},
               'metadata_summary_row_ids_sha256': source['row_ids_sha256'],
               'project_dataset_reads': 0, 'project_feature_reads': 0, 'project_outcome_reads': 0,
               'models_fitted': 0, 'scientific_runtimes_imported': False, 'resource_overrides': 0,
               'original_reference_bytes_unchanged': True,
               'requires_separate_root_committed_metadata_and_FIT_admissions': True,
               'no_scientific_execution_entrypoint': True}
    assert original == {rel: sha(ROOT / rel) for rel in REFERENCE_FILES}
    with (OUT / 'design_manifest.json').open('xb') as handle:
        handle.write((json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())
    print('STATIC_DESIGN_ONLY', len(files), sha(OUT / 'design_manifest.json'), flush=True)


if __name__ == '__main__': run()
