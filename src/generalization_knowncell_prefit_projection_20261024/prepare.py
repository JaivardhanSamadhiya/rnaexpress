"""Freeze only source/static evidence, never a project prefit or admission."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from .spec import NS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'results'/NS
DEPENDENCIES = {
    'results/generalization_knowncell_joint_engine_20261023/preparation_manifest_v2.json':
        '109a2bd1cd7e1b62f5a7607d67b3cd5da75192e4dfb9af46b1e5cb8b0fc7436e',
    'results/generalization_knowncell_campaign_replay_20261023/preparation_manifest.json':
        '24080719eb17269b1924fc63cf5ce6ae75f11b64916d0bcfcbb390679fdaf9ed',
}


def run():
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    files = {}
    def add(name, expected=None):
        assert name == name.replace('\\', '/') and ':' not in name
        assert name.split('/')[0] in ('src', 'reports', 'results', 'artifacts')
        if name.startswith('artifacts/'):
            assert name.endswith('/.gitattributes'), 'Only existing pinned static artifact markers are dependencies'
        assert all(part not in ('', '.', '..') for part in name.split('/'))
        assert name.endswith(('.py', '.json', '.md', '.log', '/.gitattributes'))
        path = ROOT/name; assert path.resolve().is_relative_to(ROOT.resolve())
        raw = path.read_bytes(); actual = sha(raw)
        assert expected is None or actual == expected, name
        assert name not in files or files[name] == actual
        files[name] = actual
        return raw
    for name, expected in DEPENDENCIES.items():
        doc = json.loads(add(name, expected))
        for rel, want in doc['files'].items(): add(rel, want)
    sources = sorted((ROOT/'src'/NS).glob('*.py'))
    receipt = json.loads(add('results/'+NS+'/synthetic_tests_receipt_reviewed.json'))
    assert receipt['status'] == 'PASS_INVENTED_CALIBRATED_PREFIT_PROJECTION_NOT_ACTUAL_ADMISSION'
    assert receipt['source_files'] == {path.relative_to(ROOT).as_posix(): sha(path.read_bytes()) for path in sources}
    assert receipt['project_payload_reads'] == receipt['actual_resource_probes'] == receipt['actual_optimizer_calls'] == 0
    assert receipt['actual_owner_contexts_verified'] == receipt['actual_Git_calls'] == 0
    assert receipt['native_or_scientific_imports'] is False
    for path in sources:
        ast.parse(path.read_bytes()); add(path.relative_to(ROOT).as_posix())
    add('results/'+NS+'/synthetic_tests_attempt_01.log')
    add('results/'+NS+'/synthetic_tests_attempt_02.log')
    add('results/'+NS+'/synthetic_tests_receipt.json')
    add('results/'+NS+'/preparation_attempt_01_incident.json')
    add('reports/'+NS+'/protocol.md')
    for folder in ('src', 'reports', 'results'): add(folder+'/'+NS+'/.gitattributes')
    for name in list(files):
        if name.startswith('src/') and name.endswith('.py'):
            parent = (ROOT/name).parent
            while parent.is_relative_to(ROOT/'src'):
                init = parent/'__init__.py'
                if init.is_file(): add(init.relative_to(ROOT).as_posix())
                parent = parent.parent
    doc = {'status': 'SOURCE_FROZEN_CALIBRATED_PREFIT_VIEW_NOT_ACTUAL_PREFIT_OR_STAGE_AUTHORITY',
        'UTC': datetime.now(timezone.utc).isoformat(), 'files': files,
        'sole_projected_top_level_field': 'resource_exception_applies',
        'actual_persisted_value': True, 'transient_legacy_view_value': False,
        'raw_bytes_SHA_commit_runtime_and_all_other_fields_preserved': True,
        'new_PreparedPools_retains_metadata_and_pool_objects': True,
        'actual_prefit_or_root_admission_or_context_verified': False,
        'actual_scientific_data_or_runtime_reads': 0, 'native_calls_or_probes_or_fits': 0,
        'resource_aliases_added_or_old_code_modified': False,
        'reviewed_fixed_real_root_reader_and_context_verifier_required': True,
        'stage_authority_granted': False}
    raw = (json.dumps(doc, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    with (OUT/'preparation_manifest.json').open('xb') as stream: stream.write(raw)
    print('CALIBRATED_PREFIT_PROJECTION_SOURCE_READY', len(files), sha(raw), flush=True)


if __name__ == '__main__': run()
