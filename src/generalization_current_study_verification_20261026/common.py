"""Source-bound read-only authority; never a new human FIT authorization."""
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from src.generalization_current_study_execution_v2_20261026 import common as prior
ROOT=prior.ROOT
NS='generalization_current_study_verification_20261026'
OUT=ROOT/'results'/NS
MANIFEST=OUT/'execution_manifest.json'
AUTH=OUT/'root_readonly_authority.json'
SCOPE=ROOT/'reports'/NS/'protocol.md'
CACHE=prior.CACHE
STAGES=('replay','evaluate')
CAPS,PRIVATE,RESIDENT,CEILING,DEADLINE=prior.CAPS,prior.PRIVATE,prior.RESIDENT,prior.CEILING,prior.DEADLINE
canonical,decode,digest,sha,relative=prior.canonical,prior.decode,prior.digest,prior.sha,prior.relative
source_mode,resource_failure,write=prior.source_mode,prior.resource_failure,prior.write
read_exact,original_inputs,old_absences=prior.read_exact,prior.original_inputs,prior.old_absences
PRODUCER=ROOT/'results/generalization_current_study_execution_v2_20261026'
PREFIT_COMMIT='e9e8a185f169e6479ec4ec20c3cca81f6b1a8019'
FIT_COMMIT='c76ace84b752e2601e68563ef66b8d8a7b64a880'


@dataclass(frozen=True)
class Stage:
    name:str
    def __post_init__(self):assert self.name in STAGES
    @property
    def directory(self):return OUT/self.name
    def path(self,name):
        assert Path(name).name==name and '/' not in name and '\\' not in name
        return self.directory/name


def save_new(path,value):
    path=Path(path);assert path.resolve().is_relative_to(OUT.resolve())
    raw=canonical(value)+b'\n'
    with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return digest(raw)


def committed(name):
    from src.generalization_pum_process_probe_20261021 import headless
    allowed={OUT.relative_to(ROOT).as_posix()+'/'+suffix for suffix in (
        'execution_manifest.json','root_readonly_authority.json','replay/run_admission.json',
        'evaluate/run_admission.json','replay/worker_report.json','replay/worker_completion.json','replay/supervisor_receipt.json')}
    assert name in allowed
    raw=headless.GitFacade(subprocess).check_output(['git','show','HEAD:'+name],cwd=ROOT,timeout=30)
    assert len(raw)<=32*2**20
    return raw


def sources(generation,*,check_commit=False):
    source_mode();raw=MANIFEST.read_bytes();assert digest(raw)==generation
    value=decode(raw)
    assert value['status']=='FROZEN_CURRENT_READONLY_VERIFICATION_NO_FIT_OR_RETUNING'
    assert value['stages']==list(STAGES) and value['model_fitting_authorized'] is False
    for name,want in value['files'].items():assert sha(relative(name))==want,name
    if check_commit:assert committed(MANIFEST.relative_to(ROOT).as_posix())==raw
    return value


def authorization(generation):
    source_mode();raw=AUTH.read_bytes();value=decode(raw)
    assert value['status']=='ROOT_INITIATED_READONLY_VERIFICATION_UNDER_STANDING_RESEARCH_REQUEST'
    assert value['source_manifest_sha256']==generation and value['protocol_sha256']==sha(SCOPE)
    assert value['stages']==list(STAGES)
    assert value['new_human_approval_claimed'] is value['FIT_authority_reused'] is value['model_fitting_authorized'] is False
    assert value['automatic_retry'] is value['spending_authorized'] is False
    return raw,value


def producer_metadata():
    raw=(PRODUCER/'fit/supervisor_receipt.json').read_bytes();parent=decode(raw)
    assert parent['status']=='PASS_NEW_CURRENT_STUDY_STAGE_NOT_REPLAY_OR_GATE' and parent['failure'] is None
    assert parent['stage']=='fit' and parent['source_manifest_sha256']=='9da990f95a33b3b9cef65efac864c1b36b72cdb4873239b6b5db5a3502296268'
    assert sha(PRODUCER/'fit/worker_report.json')==parent['validated_report_sha256']
    assert sha(PRODUCER/'fit/worker_completion.json')==parent['validated_completion_sha256']
    assert sha(PRODUCER/'fit/parent.jsonl')==parent['closed_journal_sha256']
    pins=parent['validated_stage_outputs']['saved_checkpoint_files_sha256'];assert len(pins)==191
    from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
    expected={'campaign_birth.json','campaign_complete.json'}|{lc.task_key(task)+suffix for task in lc.task_roster() for suffix in ('.birth.json','.model.json','.complete.json')}
    assert set(pins)==expected
    return raw,parent,pins


def admission(stage,generation):
    auth_raw,_=authorization(generation);raw=stage.path('run_admission.json').read_bytes();value=decode(raw)
    assert committed(AUTH.relative_to(ROOT).as_posix())==auth_raw
    assert committed(stage.path('run_admission.json').relative_to(ROOT).as_posix())==raw
    assert value['stage']==stage.name and value['source_manifest_sha256']==generation
    assert value['read_only_authority_sha256']==digest(auth_raw)
    assert value['input_pins']==sources(generation)['original_input_pins']
    assert value['attempts_authorized']==1 and value['automatic_retry'] is False
    producer_raw,parent,pins=producer_metadata()
    assert value['producer_supervisor_sha256']==digest(producer_raw)
    assert value['checkpoint_pins']==pins and value['current_prefit_commit']==PREFIT_COMMIT
    assert value['current_prefit_relative_path']==(PRODUCER/'prefit/current_prefit.json').relative_to(ROOT).as_posix()
    assert value['current_prefit_sha256']==parent['validated_stage_outputs']['current_prefit_sha256']
    if stage.name=='evaluate':
        replay=Stage('replay');receipt_raw=replay.path('supervisor_receipt.json').read_bytes();receipt=decode(receipt_raw)
        assert receipt['status']=='PASS_CURRENT_READONLY_VERIFICATION_STAGE' and receipt['failure'] is None
        assert value['replay_supervisor_sha256']==digest(receipt_raw)
        assert value['replay_report_sha256']==receipt['validated_report_sha256']==sha(replay.path('worker_report.json'))
        assert receipt['source_manifest_sha256']==generation
        assert receipt['read_only_authority_sha256']==digest(auth_raw)
    return raw,value
