"""Fixed current study source, explicit human authority and stage admissions."""
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
EXPECTED_ROOT=Path('C:/Users/jaisa/rnaexpress-recovery-20261025/material_snapshot_20261025/workspace')
NS='generalization_current_study_execution_v2_20261026'
OUT=ROOT/'results'/NS
MANIFEST=OUT/'execution_manifest.json'
AUTH=OUT/'manual_authorization.json'
SCOPE=ROOT/'reports'/NS/'approval_scope.md'
CACHE=ROOT/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
STAGES=('prefit','fit')
THREADS={key:'1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
THREADS.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
CAPS={'process_memory_limit':768*2**20,'job_memory_limit':896*2**20,'active_process_limit':2,'limit_flags':8968}
PRIVATE=768*2**20
RESIDENT=190*2**20
CEILING=192*2**20
DEADLINE=1800
GIT=Path('C:/Program Files/Git/mingw64/bin/git.exe')
GIT_SHA='51c6331aab2426ae2df187975590587b5a10042e3423f4bc0fdcb54aeb3efab7'
DETACHED_GIT_PROCESS=0x00000008


def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def decode(raw):
    def unique(items):
        value={}
        for key,item in items:
            assert key not in value;value[key]=item
        return value
    result=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
    assert isinstance(result,dict);canonical(result);return result
def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):value.update(block)
    return value.hexdigest()
def relative(name):
    assert isinstance(name,str) and name and ':' not in name and '\\' not in name
    path=Path(name);assert not path.is_absolute() and '..' not in path.parts
    result=ROOT/path;assert result.resolve().is_relative_to(ROOT.resolve());return result
def source_mode():
    if sys.flags.optimize:raise RuntimeError('Optimized Python disables scientific assertions')
    assert not sys.flags.optimize and sys.flags.no_site==1 and sys.dont_write_bytecode
    assert ROOT.resolve()==EXPECTED_ROOT.resolve()
    assert sys.pycache_prefix==str(CACHE) and not os.path.lexists(CACHE)
    assert all(os.environ.get(key)==want for key,want in THREADS.items())
def resource_failure(value,elapsed,*,startup=False):
    assert math.isfinite(elapsed) and elapsed>=0
    if value['physical_available']<(512 if startup else 256)*2**20:return 'physical reserve'
    if value['commit_headroom']<(1920*2**20 if startup else 2**30):return 'commit reserve'
    if value['disk_available']<2**30:return 'disk reserve'
    if elapsed>DEADLINE:return '1800-second total deadline'
def save_new(path,value):
    path=Path(path);assert path.resolve().is_relative_to(OUT.resolve())
    raw=canonical(value)+b'\n'
    with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return digest(raw)
def write(stream,value):stream.write(canonical(value).decode()+'\n');stream.flush();os.fsync(stream.fileno())


@dataclass(frozen=True)
class Stage:
    name:str
    def __post_init__(self):assert self.name in STAGES
    @property
    def directory(self):return OUT/self.name
    def path(self,name):
        assert Path(name).name==name and '/' not in name and '\\' not in name
        return self.directory/name


def committed(name,commit='HEAD'):
    assert commit=='HEAD' or (len(commit)==40 and all(v in '0123456789abcdef' for v in commit))
    allowed={'results/'+NS+'/'+suffix for suffix in ('execution_manifest.json','manual_authorization.json',
        'prefit/run_admission.json','fit/run_admission.json','prefit/current_prefit.json')}
    assert name in allowed;relative(name)
    assert sha(GIT)==GIT_SHA
    def invoke(args):
        return subprocess.run([str(GIT),*args],cwd=ROOT,stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True,
            creationflags=DETACHED_GIT_PROCESS).stdout
    revision=invoke(['rev-parse','--verify',commit+'^{commit}']).strip().decode('ascii')
    assert len(revision)==40 and all(v in '0123456789abcdef' for v in revision)
    if commit!='HEAD':assert revision==commit
    identifier=revision+':'+name
    size=int(invoke(['cat-file','-s',identifier]));assert 0<=size<=32*2**20
    raw=invoke(['show',identifier]);assert len(raw)==size
    assert sha(GIT)==GIT_SHA
    return raw


def sources(generation,*,check_commit=False):
    source_mode();raw=MANIFEST.read_bytes();assert digest(raw)==generation
    manifest=decode(raw)
    assert manifest['status']=='FROZEN_CURRENT_STUDY_SOURCE_REQUIRES_NEW_MANUAL_AUTHORIZATION'
    assert manifest['stages']==list(STAGES) and manifest['automatic_retry'] is False
    for name,want in manifest['files'].items():
        path=relative(name);assert not path.is_symlink() and sha(path)==want,name
    if check_commit:assert committed(MANIFEST.relative_to(ROOT).as_posix())==raw
    return manifest


def authorization(generation):
    # This file is absent until the root records a NEW actual human approval.
    source_mode();raw=AUTH.read_bytes();value=decode(raw)
    assert value['status']=='NEW_HUMAN_APPROVAL_CURRENT_PREFIT_AND_ONE_FRESH_FIXED_FIT'
    assert value['source_manifest_sha256']==generation
    assert value['approval_scope_sha256']==sha(SCOPE)
    assert value['approved_stages']==list(STAGES) and value['attempts_per_stage']==1
    assert value['automatic_retry'] is value['resume_authorized'] is value['spending_authorized'] is False
    assert value['new_manual_approval_after_old_attempt_consumed'] is True
    assert type(value['actual_user_response']) is str and value['actual_user_response'].strip()
    assert type(value['question_item_id']) is str and value['question_item_id'].strip()
    assert value['actual_user_response_recorded_verbatim'] is True
    return raw,value


def admission(stage,generation):
    auth_raw,_=authorization(generation)
    path=stage.path('run_admission.json');raw=path.read_bytes();value=decode(raw)
    assert value['status']=='ADMITTED_NEW_CURRENT_STUDY_STAGE_NOT_EXECUTION'
    assert committed(AUTH.relative_to(ROOT).as_posix())==auth_raw
    assert committed(path.relative_to(ROOT).as_posix())==raw
    assert value['stage']==stage.name and value['source_manifest_sha256']==generation
    assert value['new_manual_authorization_sha256']==digest(auth_raw)
    assert value['automatic_retry'] is False and value['attempts_authorized']==1
    assert value['input_pins']==sources(generation)['original_input_pins']
    fields={'status','stage','source_manifest_sha256','new_manual_authorization_sha256','input_pins','attempts_authorized','automatic_retry'}
    if stage.name=='fit':
        fields|={'current_prefit_relative_path','current_prefit_sha256','current_prefit_commit','prefit_supervisor_sha256','prefit_closed_journal_sha256'}
        producer=Stage('prefit');parent_raw=producer.path('supervisor_receipt.json').read_bytes();parent=decode(parent_raw)
        assert digest(parent_raw)==value['prefit_supervisor_sha256']
        assert parent['status']=='PASS_NEW_CURRENT_STUDY_STAGE_NOT_REPLAY_OR_GATE' and parent['failure'] is None
        assert parent['stage']=='prefit' and parent['source_manifest_sha256']==generation
        assert parent['new_manual_authorization_sha256']==digest(auth_raw)
        assert value['current_prefit_relative_path']==producer.path('current_prefit.json').relative_to(ROOT).as_posix()
        assert value['current_prefit_sha256']==parent['validated_stage_outputs']['current_prefit_sha256']
        assert value['prefit_closed_journal_sha256']==parent['closed_journal_sha256']==sha(producer.path('parent.jsonl'))
    assert set(value)==fields
    return raw,value


def read_exact(name,want,*,fresh,maximum=64*2**20):
    fresh();path=relative(name)
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<=maximum
    with path.open('rb') as stream:raw=stream.read(maximum+1)
    assert len(raw)<=maximum and digest(raw)==want,name
    fresh();return raw


def original_inputs():
    from src.generalization_cdrive_forensic_execution_20261026 import inputs
    pins=inputs.declared_data_pins()
    pins.pop(inputs.spec.SAVED_AUDIT.relative_to(ROOT).as_posix())
    return pins


def old_absences():
    from src.generalization_cdrive_forensic_execution_20261026.spec import OLD_MISSING
    assert all(not os.path.lexists(path) for path in OLD_MISSING)
    return [path.relative_to(ROOT).as_posix() for path in OLD_MISSING]
