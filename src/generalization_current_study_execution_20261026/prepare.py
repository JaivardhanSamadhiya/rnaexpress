"""Source freeze or newly authorized stage admission; never launch a worker."""
import argparse
import ast
import importlib
from pathlib import Path
import sys
import time
import os
if __name__=='__main__':
    _cache=Path(__file__).resolve().parents[2]/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
    if sys.flags.optimize or sys.flags.no_site!=1 or not sys.dont_write_bytecode or sys.pycache_prefix!=str(_cache) or os.path.lexists(_cache):
        raise RuntimeError('Require nonoptimized source-only Python and the absent fixed cache prefix')
from . import common as c


def freeze(*,reviewed=False):
    assert reviewed is True;c.source_mode();assert not c.MANIFEST.exists()
    assert not os.path.lexists(c.AUTH),'Never freeze a fabricated pre-existing human approval'
    for name in c.STAGES:
        stage=c.Stage(name)
        assert all(not os.path.lexists(stage.path(marker)) for marker in (
            'run_admission.json','attempt_birth.json','current_prefit.json','campaign','supervisor_receipt.json'))
    files={}
    def add(path,want=None):
        path=Path(path);raw=path.read_bytes();actual=c.digest(raw)
        assert want is None or actual==want
        name=path.relative_to(c.ROOT).as_posix()
        assert name not in files or files[name]==actual;files[name]=actual
        if path.suffix=='.py':ast.parse(raw,filename=name)
        return raw
    base=c.ROOT/'results/generalization_cdrive_forensic_execution_20261026/execution_manifest.json'
    assert c.sha(base)=='bd005dedf3f3dd32f61e82b6b68b560571b8ce348dfa17736254c2f6b9d8d617'
    previous=c.decode(add(base))
    for name,want in previous['files'].items():add(c.relative(name),want)
    for module in ('inputs','owned','worker','validate','supervise','tests'):
        importlib.import_module('src.'+c.NS+'.'+module)
    for module in ('plan','driver','tests'):
        importlib.import_module('src.generalization_current_fixed_fit_core_20261026.'+module)
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(c.ROOT/'src') and path.suffix=='.py':
                add(path);parent=path.parent
                while parent.is_relative_to(c.ROOT/'src'):
                    init=parent/'__init__.py'
                    if init.exists():add(init)
                    parent=parent.parent
    for ns in (c.NS,'generalization_current_fixed_fit_core_20261026'):
        for kind in ('src','artifacts','reports','results'):
            for path in (c.ROOT/kind/ns).rglob('*'):
                if path.is_file():add(path)
    # Receipts bind actual final sources, rather than merely counting tests.
    core=c.ROOT/'results/generalization_current_fixed_fit_core_20261026/source_preparation_manifest.json'
    assert c.sha(core)=='1041ce0d2b1307273b79d5c26352300b8b566f9aa2bc30386d873e95a40806f8'
    for name,want in c.decode(core.read_bytes())['files'].items():assert c.sha(c.relative(name))==want,name
    for path in (c.OUT/'invented_tests_receipt_final.json',c.ROOT/'results/generalization_current_fixed_fit_core_20261026/synthetic_tests_receipt.json'):
        value=c.decode(path.read_bytes())
        assert value['failures']==value['errors']==value['actual_data_reads']==value['actual_native_jobs']==0
        for name,want in value['source_sha256'].items():assert c.sha(c.relative(name))==want,name
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    pins=c.original_inputs()
    assert len(pins)==8
    value={'status':'FROZEN_CURRENT_STUDY_SOURCE_REQUIRES_NEW_MANUAL_AUTHORIZATION',
        'files':dict(sorted(files.items())),'original_input_pins':pins,'stages':list(c.STAGES),
        'attempts_per_stage':1,'automatic_retry':False,'resume_authorized':False,
        'source_preparation_actual_biological_reads':0,'actual_jobs_launched':0,
        'actual_human_authorization_exists':False,'evaluation_or_gate_authorized':False}
    c.save_new(c.MANIFEST,value)
    print(value['status'],len(files),c.sha(c.MANIFEST),flush=True)


def admit(name,generation,*,prefit_commit=None):
    c.source_mode();stage=c.Stage(name);manifest=c.sources(generation,check_commit=True)
    auth_raw,_=c.authorization(generation)
    assert manifest['original_input_pins']==c.original_inputs()
    assert not stage.path('run_admission.json').exists() and not stage.path('attempt_birth.json').exists()
    stage.directory.mkdir(exist_ok=True)
    assert not stage.directory.is_symlink() and stage.directory.resolve()==stage.directory.absolute()
    value={'status':'ADMITTED_NEW_CURRENT_STUDY_STAGE_NOT_EXECUTION','stage':name,
        'source_manifest_sha256':generation,'new_manual_authorization_sha256':c.digest(auth_raw),
        'input_pins':dict(manifest['original_input_pins']),'attempts_authorized':1,'automatic_retry':False}
    if name=='prefit':assert prefit_commit is None
    else:
        from . import validate
        from src.generalization_pum_process_probe_20261021 import headless
        assert isinstance(prefit_commit,str) and len(prefit_commit)==40
        producer=c.Stage('prefit');parent_raw=producer.path('supervisor_receipt.json').read_bytes();parent=c.decode(parent_raw)
        assert parent['status']=='PASS_NEW_CURRENT_STUDY_STAGE_NOT_REPLAY_OR_GATE' and parent['failure'] is None
        assert parent['stage']=='prefit' and parent['source_manifest_sha256']==generation
        assert parent['new_manual_authorization_sha256']==c.digest(auth_raw)
        report_raw=producer.path('worker_report.json').read_bytes();complete_raw=producer.path('worker_completion.json').read_bytes()
        assert c.digest(report_raw)==parent['validated_report_sha256']
        assert c.digest(complete_raw)==parent['validated_completion_sha256']
        assert c.sha(producer.path('parent.jsonl'))==parent['closed_journal_sha256']
        old_run_raw,old_run=c.admission(producer,generation)
        assert c.digest(old_run_raw)==parent['run_admission_sha256']
        started=time.monotonic()
        def fresh():assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
        actual=validate.terminal(producer,c.decode(report_raw),c.decode(complete_raw),old_run,generation,
            parent['run_admission_sha256'],parent['birth_sha256'],parent['owned_child_identity_sha256'],
            parent['current_child_record_sha256'],parent['parent_pid'],parent['worker_pid'],fresh=fresh)
        assert actual==parent['validated_stage_outputs']
        for filename,key in (('attempt_birth.json','birth_sha256'),('owned_child_identity.json','owned_child_identity_sha256'),('owned_child_started.json','current_child_record_sha256')):
            assert c.sha(producer.path(filename))==parent[key]
        prefit_path=producer.path('current_prefit.json');prefit_raw=prefit_path.read_bytes()
        assert c.digest(prefit_raw)==actual['current_prefit_sha256']
        relative=prefit_path.relative_to(c.ROOT).as_posix()
        assert c.committed(relative,prefit_commit)==prefit_raw
        value.update(current_prefit_relative_path=relative,current_prefit_sha256=c.digest(prefit_raw),
            current_prefit_commit=prefit_commit,prefit_supervisor_sha256=c.digest(parent_raw),
            prefit_closed_journal_sha256=parent['closed_journal_sha256'])
    c.save_new(stage.path('run_admission.json'),value)
    print('ADMITTED_ONLY',name,c.sha(stage.path('run_admission.json')),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    freezer=sub.add_parser('freeze');freezer.add_argument('--reviewed',action='store_true',required=True)
    admission=sub.add_parser('admit');admission.add_argument('stage',choices=c.STAGES)
    admission.add_argument('--manifest-sha',required=True);admission.add_argument('--prefit-commit')
    args=parser.parse_args()
    if args.command=='freeze':freeze(reviewed=args.reviewed)
    else:admit(args.stage,args.manifest_sha,prefit_commit=args.prefit_commit)
