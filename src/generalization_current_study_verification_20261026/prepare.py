"""Freeze/admit the first read-only replay and evaluation, without launching."""
import argparse
import ast
import importlib
import os
from pathlib import Path
import sys
if __name__=='__main__':
    cache=Path(__file__).resolve().parents[2]/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
    if sys.flags.optimize or sys.flags.no_site!=1 or not sys.dont_write_bytecode or sys.pycache_prefix!=str(cache) or os.path.lexists(cache):raise RuntimeError('Require fixed source-only flags')
from . import common as c


def freeze(*,reviewed=False):
    assert reviewed is True;c.source_mode();assert not c.MANIFEST.exists() and not c.AUTH.exists()
    files={}
    def add(path,want=None):
        path=Path(path);raw=path.read_bytes();got=c.digest(raw);assert want is None or got==want
        key=path.relative_to(c.ROOT).as_posix();assert key not in files or files[key]==got;files[key]=got
        if path.suffix=='.py':ast.parse(raw,filename=key)
    base=c.PRODUCER/'execution_manifest.json';assert c.sha(base)=='9da990f95a33b3b9cef65efac864c1b36b72cdb4873239b6b5db5a3502296268'
    add(base)
    for name,want in c.decode(base.read_bytes())['files'].items():add(c.relative(name),want)
    for module in ('owned','worker','validate','supervise','tests'):importlib.import_module('src.'+c.NS+'.'+module)
    for module in ('replay','evaluation','tests'):importlib.import_module('src.generalization_current_verification_core_20261026.'+module)
    for module in tuple(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            path=Path(name).resolve()
            if path.is_relative_to(c.ROOT/'src') and path.suffix=='.py':
                add(path);parent=path.parent
                while parent.is_relative_to(c.ROOT/'src'):
                    init=parent/'__init__.py'
                    if init.exists():add(init)
                    parent=parent.parent
    for ns in (c.NS,'generalization_current_verification_core_20261026'):
        for kind in ('src','reports','results','artifacts'):
            for path in (c.ROOT/kind/ns).rglob('*'):
                if path.is_file():add(path)
    receipt=c.decode((c.OUT/'invented_tests_receipt.json').read_bytes())
    assert receipt['failures']==receipt['errors']==receipt['actual_biological_reads']==receipt['actual_native_jobs']==0
    for name,want in receipt['source_sha256'].items():assert c.sha(c.relative(name))==want,name
    producer_raw,producer,pins=c.producer_metadata()
    for suffix in ('supervisor_receipt.json','worker_report.json','worker_completion.json','parent.jsonl'):
        add(c.PRODUCER/'fit'/suffix)
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    for stage in c.STAGES:assert not c.Stage(stage).path('attempt_birth.json').exists()
    value={'status':'FROZEN_CURRENT_READONLY_VERIFICATION_NO_FIT_OR_RETUNING','files':files,
        'stages':list(c.STAGES),'original_input_pins':c.original_inputs(),
        'model_fitting_authorized':False,'automatic_retry':False,
        'source_preparation_biological_payload_reads':0,'producer_control_metadata_read':True,
        'actual_jobs_launched':0,'separate_human_approval_claimed':False,
        'producer_supervisor_sha256':c.digest(producer_raw),'checkpoint_pins':pins}
    c.save_new(c.MANIFEST,value);print('READONLY_SOURCE_FROZEN',len(files),c.sha(c.MANIFEST),flush=True)


def initialize_authority(generation,*,root_start_readonly=False):
    assert root_start_readonly is True;c.sources(generation,check_commit=True)
    value={'status':'ROOT_INITIATED_READONLY_VERIFICATION_UNDER_STANDING_RESEARCH_REQUEST',
        'source_manifest_sha256':generation,'protocol_sha256':c.sha(c.SCOPE),'stages':list(c.STAGES),
        'basis':'Existing user request to continue computational RNA-localization research, review results and verify the fixed study',
        'resource_basis':'Existing known-cell calibration, unchanged physical/commit/disk/private/resident/thread/deadline bounds',
        'new_human_approval_claimed':False,'FIT_authority_reused':False,'model_fitting_authorized':False,
        'automatic_retry':False,'spending_authorized':False}
    print('ROOT_READONLY_AUTHORITY',c.save_new(c.AUTH,value),flush=True)


def admit(name,generation):
    stage=c.Stage(name);manifest=c.sources(generation,check_commit=True);auth_raw,_=c.authorization(generation)
    assert not stage.path('run_admission.json').exists() and not stage.path('attempt_birth.json').exists()
    stage.directory.mkdir(exist_ok=True);assert not stage.directory.is_symlink()
    producer_raw,producer,pins=c.producer_metadata()
    assert c.digest(producer_raw)==manifest['producer_supervisor_sha256'] and pins==manifest['checkpoint_pins']
    value={'status':'ADMITTED_FIRST_READONLY_CURRENT_VERIFICATION_NOT_EXECUTION','stage':name,
        'source_manifest_sha256':generation,'read_only_authority_sha256':c.digest(auth_raw),
        'input_pins':manifest['original_input_pins'],'checkpoint_pins':pins,
        'producer_supervisor_sha256':c.digest(producer_raw),'attempts_authorized':1,'automatic_retry':False,
        'current_prefit_relative_path':(c.PRODUCER/'prefit/current_prefit.json').relative_to(c.ROOT).as_posix(),
        'current_prefit_sha256':producer['validated_stage_outputs']['current_prefit_sha256'],
        'current_prefit_commit':c.PREFIT_COMMIT}
    if name=='evaluate':
        replay=c.Stage('replay');raw=replay.path('supervisor_receipt.json').read_bytes();receipt=c.decode(raw)
        assert receipt['status']=='PASS_CURRENT_READONLY_VERIFICATION_STAGE' and receipt['failure'] is None
        report_raw=replay.path('worker_report.json').read_bytes()
        assert c.digest(report_raw)==receipt['validated_report_sha256']
        assert c.sha(replay.path('worker_completion.json'))==receipt['validated_completion_sha256']
        assert c.sha(replay.path('parent.jsonl'))==receipt['closed_journal_sha256']
        report=c.decode(report_raw);assert report['result']['status']=='PASS_CURRENT_CLOSED63_ARITHMETIC_AND_SOURCE_RESELECTION'
        assert report['result']['prefit_sha256']==value['current_prefit_sha256']
        assert c.committed(replay.path('worker_report.json').relative_to(c.ROOT).as_posix())==report_raw
        value.update(replay_supervisor_sha256=c.digest(raw),replay_report_sha256=c.digest(report_raw))
    print('READONLY_ADMISSION',name,c.save_new(stage.path('run_admission.json'),value),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--reviewed',action='store_true',required=True)
    a=sub.add_parser('initialize-readonly');a.add_argument('--root-start-readonly',action='store_true',required=True);a.add_argument('--manifest-sha',required=True)
    d=sub.add_parser('admit');d.add_argument('stage',choices=c.STAGES);d.add_argument('--manifest-sha',required=True)
    args=parser.parse_args()
    if args.command=='freeze':freeze(reviewed=args.reviewed)
    elif args.command=='initialize-readonly':initialize_authority(args.manifest_sha,root_start_readonly=args.root_start_readonly)
    else:admit(args.stage,args.manifest_sha)
