"""C-only immutable source/attempt and bounded read-only output contracts."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from .spec import *
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lifecycle


def digest(raw): return hashlib.sha256(raw).hexdigest()


def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')


def decode(raw):
    def unique(items):
        value={}
        for key,item in items:
            assert key not in value,'Duplicate JSON key'; value[key]=item
        return value
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))
    assert isinstance(value,dict);return value


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):value.update(block)
    return value.hexdigest()


def relative(name):
    assert isinstance(name,str) and name and '\\' not in name and ':' not in name
    path=Path(name);assert not path.is_absolute() and '..' not in path.parts
    result=ROOT/path;assert result.resolve().is_relative_to(ROOT.resolve())
    return result


def source_mode():
    if sys.flags.optimize:raise RuntimeError('Assertions must remain enabled')
    assert ROOT.resolve()==EXPECTED_ROOT.resolve() and sys.flags.no_site==1 and sys.dont_write_bytecode
    assert sys.pycache_prefix==str(SOURCE_CACHE) and not SOURCE_CACHE.exists() and not SOURCE_CACHE.is_symlink()
    assert all(os.environ.get(key)==value for key,value in THREAD_ENV.items())


def resource_failure(value,elapsed,*,startup=False):
    assert math.isfinite(elapsed) and elapsed>=0
    if value['physical_available']<(512 if startup else 256)*2**20:return 'physical reserve'
    if value['commit_headroom']<(1920*2**20 if startup else 2**30):return 'commit reserve'
    if value['disk_available']<2**30:return 'disk reserve'
    if elapsed>DEADLINE:return '1800-second total forensic deadline'


def save_new(path,value):
    path=Path(path);assert path.parent==OUT
    raw=canonical(value)+b'\n'
    with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return digest(raw)


def write(stream,value):
    stream.write(canonical(value).decode('utf8')+'\n');stream.flush();os.fsync(stream.fileno())


def sources(generation,*,committed=False):
    source_mode();raw=MANIFEST.read_bytes();assert digest(raw)==generation
    value=decode(raw);assert value['status']==STATUS and value['read_only'] is True
    assert value['model_fitting_authorized'] is value['evaluation_or_gate_authorized'] is False
    for name,want in value['files'].items():
        path=relative(name);assert not path.is_symlink() and sha(path)==want,name
    if committed:
        from src.generalization_pum_process_probe_20261021 import headless
        assert headless.GitFacade(subprocess).check_output(['git','show','HEAD:'+MANIFEST.relative_to(ROOT).as_posix()],cwd=ROOT)==raw
    return value


def old_absences():
    assert all(not os.path.lexists(path) for path in OLD_MISSING),'Old campaign closure must remain absent'
    return [path.relative_to(ROOT).as_posix() for path in OLD_MISSING]


def declared_pins():
    from . import inputs
    result=dict(inputs.declared_data_pins())
    for name,want in inputs.checkpoint_pins().items():
        assert name not in result or result[name]==want;result[name]=want
    for name,want in result.items():
        relative(name);assert isinstance(want,str) and len(want)==64
    assert len(inputs.checkpoint_pins())==190
    return result


def bind_read_set(manifest):
    assert manifest['readonly_input_pins']==declared_pins(),'Declared forensic read set changed'
    return dict(manifest['readonly_input_pins'])


def rehash_read_set(manifest,*,fresh):
    for name,want in bind_read_set(manifest).items():read_exact(name,want,fresh=fresh,maximum=64*2**20)
    old_absences()


def read_exact(name,want,*,fresh,maximum=32*2**20):
    fresh();path=relative(name)
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<=maximum
    with path.open('rb') as stream:raw=stream.read(maximum+1)
    assert len(raw)<=maximum and digest(raw)==want,name
    fresh();return raw


def terminal(report,completion,generation,birth_sha,identity_sha,owner_sha,parent_pid,child_pid):
    for value in (report,completion):
        assert value['generation_manifest_sha256']==generation and value['birth_sha256']==birth_sha
        assert value['owned_child_identity_sha256']==identity_sha
        assert value['current_child_record_sha256']==owner_sha
        assert value['parent_pid']==parent_pid and value['worker_pid']==child_pid
        assert value['biological_inputs_read'] is True and value['biological_rows_read']==13781
        assert value['new_optimizer_calls']==0 and value['original_formal_replay_still_ineligible'] is True
        assert value['outer_performance_computed_or_published'] is value['evaluation_or_gate_run'] is False
    assert report['status']==REPORT_STATUS and completion['status']==WORKER_PASS
    saved=report['saved_declarations']
    assert saved['status']=='PASS190_SAVED_DECLARATIONS_NOT_CAMPAIGN_OR_CURRENT_OWNER'
    assert saved['saved_checkpoints']==63 and saved['recorded_completed_optimizer_units']==84
    assert len(saved['saved_filename_sha256'])==190 and saved['old_campaign_complete_missing'] is True
    assert saved['current_owner_or_runtime_admission_granted'] is False
    result=report['forensic_numeric_diagnostics']
    assert result['status']=='PASS_FORENSIC_SAVED63_NUMERIC_CONSISTENCY_NOT_CLOSED_CAMPAIGN'
    assert result['verified_checkpoints']==63 and result['recorded_optimizer_units_not_refitted']==84
    assert result['source_only_reselections_equal']==9 and len(result['checkpoint_numeric_diagnostics'])==63
    assert result['old_campaign_completion_missing'] is result['old_supervisor_completion_missing'] is True
    assert result['original_formal_replay_still_ineligible'] is True
    assert result['outer_performance_computed_or_published'] is result['evaluation_or_gate_run'] is False
    assert 'canonical_outer_records' not in result
    keys={lifecycle.task_key(task) for task in lifecycle.task_roster()}
    assert set(result['checkpoint_numeric_diagnostics'])==keys
    for diagnostic in result['checkpoint_numeric_diagnostics'].values():
        assert diagnostic['status']=='PASS_READONLY_SAVED_CHECKPOINT_NUMERIC_CONSISTENCY_NOT_CAMPAIGN'
        assert diagnostic['exact_canonical_scores_equal'] is True and diagnostic['new_optimizer_calls']==0
        assert diagnostic['outer_performance_computed'] is diagnostic['old_campaign_closure_or_current_owner_certified'] is False
        assert diagnostic['tolerance_strictly_below']==1e-9
        for field in ('maximum_scaling_difference','maximum_objective_difference','maximum_recorded_gradient_norm_difference','maximum_scalar_score_difference'):
            assert math.isfinite(diagnostic[field]) and 0<=diagnostic[field]<1e-9
    assert completion['report_sha256']==digest(canonical(report)+b'\n')
    assert set(report['checkpoint_current_runtime_proof_sha256'])==keys
    for phase in ('runtime_before_inputs','runtime_after_forensics'):
        proof=report[phase]
        assert proof['stage']==STAGE and proof['current_pid']==child_pid and proof['parent_pid']==parent_pid
        assert proof['generation_manifest_sha256']==generation and proof['birth_sha256']==birth_sha
        assert proof['owned_child_identity_sha256']==identity_sha and proof['in_owned_job_now'] is True
        assert proof['current_child_record_sha256']==owner_sha
        assert proof['actual_old_campaign_owner_claimed'] is False
    return True
