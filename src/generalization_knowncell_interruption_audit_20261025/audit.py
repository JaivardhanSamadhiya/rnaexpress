"""Preserve saved lifecycle declarations without numeric replay or evaluation."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from src.generalization_knowncell_fit_retry_execution_20261025 import common as c
from src.generalization_knowncell_fit_retry_execution_20261025.terminal import ReadOnlySavedCampaign
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_github_publication_20261009.publish import protect

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/generalization_knowncell_interruption_audit_20261025'
GENERATION = '8f30e3684125044dc1db3c9b66d05c8633fda4f4201cf1b91cf7c5c5e3c8a738'
RUN_SHA = '7655c467bca636a39460662d9e5ed67345aabea35df6b64d7f0452f7611ea5d4'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    assert path.is_file() and not path.is_symlink()
    assert path.stat().st_size <= 16 * 2**20
    return path.read_bytes()


def main():
    assert protect() == 33
    c.verify_sources(GENERATION)
    run_raw = read(c.RUN_ADMISSION)
    assert sha(run_raw) == RUN_SHA
    run = c.run_contract(lc.strict_json(run_raw), GENERATION)
    assert sha(read(c.RETRY_AUTH)) == run['retry_authorization_sha256']
    c.retry_authorization_contract(lc.strict_json(read(c.RETRY_AUTH)), GENERATION,
        sha(read(ROOT / c.RETRY_SCOPE)))
    for name, want in run['input_pins'].items():
        assert sha(read(ROOT / name)) == want, name
    birth_raw = read(c.BIRTH)
    birth = lc.strict_json(birth_raw)
    assert birth['generation_manifest_sha256'] == GENERATION
    assert birth['run_admission_sha256'] == RUN_SHA
    assert birth['parent_pid'] == 200304 and birth['automatic_retry'] is False
    absent = [c.OUTPUT, c.COMPLETION, c.SUPERVISOR,
              c.CAMPAIGN / 'checkpoints/campaign_complete.json']
    assert all(not os.path.lexists(path) for path in absent)
    directory = c.CAMPAIGN / 'checkpoints'
    campaign_raw = read(directory / 'campaign_birth.json')
    old_birth = ROOT / 'results/generalization_knowncell_fit_execution_20261024/campaign/checkpoints/campaign_birth.json'
    assert campaign_raw == read(old_birth), 'Stable prefit campaign identity differs'
    identity = lc.strict_json(campaign_raw)
    assert identity.pop('status') == 'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS'
    prefit_raw = read(ROOT / c.PREFIT)
    assert sha(prefit_raw) == identity['prefit_sha256'] == run['input_pins'][c.PREFIT]
    document = lc.strict_json(prefit_raw)
    assert document['resource_exception_applies'] is True
    document['resource_exception_applies'] = False
    lc.validate_prefit(document)  # Transient legacy declaration check only.
    assert identity['source_pool_sha256'] == {
        key: lc.hash_value(value) for key, value in document['source_pools'].items()}
    assert identity['checkpoint_roster'] == lc.task_roster()
    assert identity['prefit_commit'] == run['actual_prefit_commit']
    assert identity['runtime_binding_sha256'] == document['runtime_binding_sha256']
    # This object only checks SAVED declarations. It is never a current context,
    # native runtime admission, scientific binder, replay, or execution permit.
    plan = SimpleNamespace(identity=lambda: identity,
        prefit_sha256=sha(prefit_raw), prefit_commit=identity['prefit_commit'],
        runtime_binding_sha256=identity['runtime_binding_sha256'],
        pool=lambda task: document['source_pools'][lc.pool_key(task['outer_fold'], task['inner_fold'])])
    reader = ReadOnlySavedCampaign(directory, plan, sha(campaign_raw))
    roster = lc.task_roster()
    complete = {path.name.removesuffix('.complete.json') for path in directory.glob('*.complete.json')}
    ordered = [lc.task_key(task) for task in roster]
    assert complete == set(ordered[:len(complete)]), 'Completed keys must be exact frozen prefix'
    receipts = [reader.check_saved(key) for key in ordered[:len(complete)]]
    expected_names = {'campaign_birth.json'} | {
        key + suffix for key in complete for suffix in ('.birth.json', '.model.json', '.complete.json')}
    actual_names = {path.name for path in directory.iterdir()}
    partial_names = sorted(actual_names - expected_names)
    assert set(partial_names) <= {ordered[len(complete)] + suffix
        for suffix in ('.birth.json', '.model.json', '.failure.json')} | {'campaign_failure_v2.json'}
    proofs = sorted(c.CHECKPOINT_PROOFS.glob('*.json'))
    assert {p.stem for p in proofs} in (set(ordered[:len(complete)]), set(ordered[:len(complete)+1]))
    for index, key in enumerate(ordered[:len(proofs)], 1):
        proof = lc.strict_json(read(c.CHECKPOINT_PROOFS / (key + '.json')))
        assert proof['current_pid'] == 9928 and proof['parent_pid'] == birth['parent_pid']
        assert proof['caller_birth_sha256'] == sha(birth_raw)
        assert proof['checkpoint_key'] == key and proof['checkpoint_refresh_count'] == index
        assert proof['stage'] == 'fit' and proof['provider_phase'] == 'checkpoint'
        assert proof['static_root_binding_sha256'] == run['input_pins'][c.STATIC_BINDING]
        assert proof['request_binding']['request_sha256'] == run['input_pins'][c.REQUEST]
        assert proof['runtime_and_FIT_authority_granted_here'] is False
    paths = sorted(p for p in c.OUT.rglob('*') if p.is_file())
    hashes = {p.relative_to(ROOT).as_posix(): sha(read(p)) for p in paths}
    logs = {name: len(read(c.OUT / name)) for name in
            ('fit_launch.stdout.log', 'fit_launch.stderr.log', 'fit_worker.log')}
    result = {
        'status': 'INTERRUPTED_ATTEMPT_SAVED_DECLARATIONS_VERIFIED_NO_SCIENTIFIC_VERDICT',
        'UTC': datetime.now(timezone.utc).isoformat(),
        'generation_manifest_sha256': GENERATION, 'run_admission_sha256': RUN_SHA,
        'birth_sha256': sha(birth_raw), 'source_and_input_pins_verified': True,
        'completed_checkpoints': len(complete),
        'completed_inner_checkpoints': sum(t['phase'] == 'inner' for t in roster[:len(complete)]),
        'completed_outer_checkpoints': sum(t['phase'] == 'outer' for t in roster[:len(complete)]),
        'recorded_completed_optimizer_units': sum(r['optimizer_units'] for r in receipts),
        'completed_keys': ordered[:len(complete)], 'partial_checkpoint_files': partial_names,
        'runtime_proofs': len(proofs), 'log_bytes': logs,
        'absent_terminal_files': [p.relative_to(ROOT).as_posix() for p in absent],
        'files_sha256': hashes,
        'termination_cause': 'UNKNOWN_NO_TERMINAL_RECEIPT',
        'saved_declaration_checks_are_not_current_authority_or_independent_numeric_replay': True,
        'model_performance_or_selected_configuration_values_reported': False,
        'scientific_settings_changed': False, 'evaluation_or_gate_run': False,
        'automatic_retry_or_resume': False, 'biological_conclusion_available': False,
        'protected_user_files': protect(),
    }
    for name, want in hashes.items():
        assert sha(read(ROOT / name)) == want, 'Saved bytes changed during audit'
    assert not any(name.startswith(('numpy', 'pandas', 'scipy')) for name in __import__('sys').modules)
    OUT.mkdir(exist_ok=True)
    with (OUT / 'interrupted_fit_audit.json').open('x', encoding='utf8', newline='\n') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({key: result[key] for key in ('status', 'completed_checkpoints',
        'completed_inner_checkpoints', 'completed_outer_checkpoints',
        'recorded_completed_optimizer_units', 'runtime_proofs', 'partial_checkpoint_files')}))


if __name__ == '__main__':
    main()
