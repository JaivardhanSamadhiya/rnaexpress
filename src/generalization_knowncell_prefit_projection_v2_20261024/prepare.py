"""Source-only V2 closure, including all preserved V1 evidence and imports."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from .spec import NS, V1_MANIFEST, V1_MANIFEST_SHA

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'results'/NS


def run():
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    pins = {}
    def add(name, want=None):
        assert name == name.replace('\\', '/') and ':' not in name
        assert all(part not in ('', '.', '..') for part in name.split('/'))
        assert name.split('/')[0] in ('src', 'reports', 'results', 'artifacts')
        assert name.endswith(('.py', '.json', '.md', '.log', '/.gitattributes'))
        if name.startswith('artifacts/'): assert name.endswith('/.gitattributes')
        path = ROOT/name; assert path.resolve().is_relative_to(ROOT.resolve())
        raw = path.read_bytes(); actual = sha(raw)
        assert want is None or actual == want, name
        assert name not in pins or pins[name] == actual
        pins[name] = actual
        return raw
    prior = json.loads(add(V1_MANIFEST, V1_MANIFEST_SHA))
    assert len(prior['files']) == 115
    for name, want in prior['files'].items(): add(name, want)
    sources = sorted((ROOT/'src'/NS).glob('*.py'))
    test_name = 'results/'+NS+'/synthetic_tests_receipt.json'
    receipt = json.loads(add(test_name))
    assert receipt['status'] == 'PASS_INVENTED_REPLAY_STABLE_PREFIT_IDENTITY_NOT_ACTUAL_STAGE_AUTHORITY'
    assert receipt['source_files'] == {path.relative_to(ROOT).as_posix(): sha(path.read_bytes()) for path in sources}
    assert receipt['actual_models_or_checkpoints_created'] == receipt['project_payload_reads'] == receipt['actual_optimizer_calls'] == 0
    assert receipt['actual_resource_probes'] == receipt['actual_owner_contexts_verified'] == receipt['actual_Git_calls'] == 0
    assert receipt['native_or_scientific_imports'] is False
    for path in sources:
        ast.parse(path.read_bytes()); add(path.relative_to(ROOT).as_posix())
    add('results/'+NS+'/synthetic_tests_attempt_01.log')
    add('reports/'+NS+'/protocol.md')
    for folder in ('src', 'reports', 'results'): add(folder+'/'+NS+'/.gitattributes')
    for name in list(pins):
        if name.startswith('src/') and name.endswith('.py'):
            parent = (ROOT/name).parent
            while parent.is_relative_to(ROOT/'src'):
                init = parent/'__init__.py'
                if init.is_file(): add(init.relative_to(ROOT).as_posix())
                parent = parent.parent
    document = {'status': 'SOURCE_FROZEN_REPLAY_STABLE_PREFIT_PROJECTION_NOT_ACTUAL_STAGE_AUTHORITY',
        'UTC': datetime.now(timezone.utc).isoformat(), 'files': pins,
        'preserved_V1_manifest_sha256': V1_MANIFEST_SHA, 'all115V1pins_unchanged': True,
        'stable_campaign_identity_excludes_current_context_and_owner': True,
        'current_context_retained_and_explicitly_separately_described': True,
        'mandatory_real_context_verifier_still_required_each_stage': True,
        'actual_raw_true_prefit_and_sole_flag_projection_unchanged': True,
        'no_original_science_numerical_lifecycle_or_resource_monkeypatch': True,
        'actual_prefit_or_stage_context_or_data_verified': False,
        'actual_native_probe_model_or_optimizer_calls': 0, 'stage_authority_granted': False}
    raw = (json.dumps(document, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    with (OUT/'preparation_manifest.json').open('xb') as stream: stream.write(raw)
    print('REPLAY_STABLE_PREFIT_PROJECTION_SOURCE_READY', len(pins), sha(raw), flush=True)


if __name__ == '__main__': run()
