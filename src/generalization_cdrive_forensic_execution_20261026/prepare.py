"""Reviewed-source freeze only. Never a biological read, probe or worker run."""
import argparse
import ast
import importlib
from pathlib import Path
import sys
from . import common as c


def merge(files,key,want):
    c.relative(key);assert key not in files or files[key]==want,key;files[key]=want


def run(*,freeze_reviewed=False):
    assert freeze_reviewed is True,'Root source review required before final source freeze'
    c.source_mode();assert not c.MANIFEST.exists()
    files={}
    for path,want in ((c.CORE_MANIFEST,c.CORE_MANIFEST_SHA),(c.PROFILE_MANIFEST,c.PROFILE_MANIFEST_SHA)):
        assert c.sha(path)==want
        value=c.decode(path.read_bytes())
        for key,pin in value['files'].items():
            assert c.sha(c.relative(key))==pin,key;merge(files,key,pin)
        merge(files,path.relative_to(c.ROOT).as_posix(),want)
    assert c.sha(c.PROFILE_CERTIFICATE)==c.PROFILE_CERTIFICATE_SHA
    cert=c.decode(c.PROFILE_CERTIFICATE.read_bytes())
    assert cert['status']=='VERIFIED_CDRIVE_CURRENT42_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION'
    for key,want in cert['verified_files'].items():
        assert c.sha(c.relative(key))==want;merge(files,key,want)
    for path,want in ((c.PROFILE_CERTIFICATE,c.PROFILE_CERTIFICATE_SHA),(c.PROFILE_RECEIPT,c.PROFILE_RECEIPT_SHA),
                      (c.INVENTORY,c.INVENTORY_SHA),(c.SAVED_AUDIT,c.SAVED_AUDIT_SHA)):
        assert c.sha(path)==want;merge(files,path.relative_to(c.ROOT).as_posix(),want)
    for suffix in ('inputs','pools','runtime_or_owner','worker','supervise','tests_controller','tests_inputspools'):
        importlib.import_module('src.'+c.NS+'.'+suffix)
    receipts=(c.OUT/'controller_tests_receipt_reviewed.json',c.OUT/'inputs_pools_tests_receipt.json')
    for path in receipts:
        receipt=c.decode(path.read_bytes())
        assert receipt['failures']==receipt['errors']==0 and receipt['actual_data_reads']==receipt['actual_native_jobs']==0
        for key,want in receipt['source_sha256'].items():assert c.sha(c.relative(key))==want,key
    from src.generalization_knowncell_joint_input_bridge_20261023 import spec as original_sampler
    for key,want in ((original_sampler.MODEL_SOURCE,original_sampler.MODEL_SHA),
                     (original_sampler.COMMON_SOURCE,original_sampler.COMMON_SHA)):
        assert c.sha(c.relative(key))==want;merge(files,key,want)
    imported={}
    for name,module in tuple(sys.modules.items()):
        source=getattr(module,'__file__',None)
        if not source:continue
        path=Path(source).resolve()
        if path.is_relative_to(c.ROOT/'src') and path.suffix=='.py':
            key=path.relative_to(c.ROOT).as_posix();merge(files,key,c.sha(path));imported[name]=key
            parent=path.parent
            while parent.is_relative_to(c.ROOT/'src'):
                init=parent/'__init__.py'
                if init.exists():merge(files,init.relative_to(c.ROOT).as_posix(),c.sha(init))
                parent=parent.parent
    for kind in ('src','reports','results','artifacts'):
        for path in (c.ROOT/kind/c.NS).rglob('*'):
            if path.is_file():merge(files,path.relative_to(c.ROOT).as_posix(),c.sha(path))
    for key in files:
        if key.endswith('.py'):ast.parse(c.relative(key).read_text(encoding='utf8'),filename=key)
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    readonly=c.declared_pins() # Literal/source-bound hash metadata only; no payload bytes.
    value={'status':c.STATUS,'files':dict(sorted(files.items())),'file_count':len(files),
        'readonly_input_pins':dict(sorted(readonly.items())),'source_import_closure':imported,
        'read_only':True,'model_fitting_authorized':False,'evaluation_or_gate_authorized':False,
        'old_formal_replay_authorized':False,'original_closure_missing':True,
        'source_preparation_biological_payload_reads':0,'source_preparation_native_jobs':0,
        'root_start_flag_required':'--root-start-readonly','actual_stage_started':False}
    c.save_new(c.MANIFEST,value)
    print(c.STATUS,len(files),c.sha(c.MANIFEST),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze-reviewed',action='store_true',required=True)
    run(freeze_reviewed=parser.parse_args().freeze_reviewed)
