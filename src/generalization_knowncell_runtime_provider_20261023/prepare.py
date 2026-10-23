"""Hash source and existing software evidence only; no provider invocation."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from .spec import *


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):value.update(block)
    return value.hexdigest()


def run():
    pins = {}
    def add(name,expected=None):
        assert static_allowed(name),name
        path = ROOT/name
        assert path.is_file()
        actual = sha(path)
        assert expected is None or actual==expected,name
        assert name not in pins or pins[name]==actual,'Conflicting software/source pin'
        pins[name] = actual
    add(PROFILE_MANIFEST,PROFILE_MANIFEST_SHA)
    profile = json.loads((ROOT/PROFILE_MANIFEST).read_bytes())
    for name,expected in profile['files'].items():add(name,expected)
    add(SOFTWARE_STATUS,SOFTWARE_STATUS_SHA);add(PANDAS_ADMISSION,PANDAS_ADMISSION_SHA)
    status = json.loads((ROOT/SOFTWARE_STATUS).read_bytes())
    for name,expected in status['verified_files'].items():add(PROFILE_OUT+name,expected)
    assert pins[PROFILE_ORIGIN]==PROFILE_ORIGIN_SHA
    for name in ('src/generalization_knowncell_joint_loader_20261022/guard.py',
                 'src/generalization_knowncell_joint_implementation_20261022/admission.py',
                 'src/generalization_knowncell_joint_implementation_20261022/prepare.py',
                 'src/generalization_knowncell_parser_profile_v4_20261023/certify.py'):
        add(name)
    # Explicit parent package files are software too; namespace packages need
    # no fabricated __init__ pin. Existing regular parent bytes are retained.
    for name in list(pins):
        if not name.startswith('src/') or not name.endswith('.py'):continue
        parent = (ROOT/name).parent
        while parent.is_relative_to(ROOT/'src'):
            init = parent/'__init__.py'
            if init.is_file():add(init.relative_to(ROOT).as_posix())
            parent = parent.parent
    source = ROOT/'src'/NS
    sources = sorted(source.glob('*.py'))
    receipt_path = ROOT/'results'/NS/'synthetic_tests_receipt.json'
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['status']=='PASS_MOCKED_REAL_RUNTIME_PROVIDER_SOURCE_NOT_NATIVE_OR_PROJECT_ADMISSION'
    assert receipt['sources']=={path.relative_to(ROOT).as_posix():sha(path) for path in sources}
    assert receipt['scientific_imports'] is False and receipt['actual_resource_guard_or_native_bootstrap_invoked'] is False
    assert receipt['project_payload_reads']==receipt['actual_optimizer_calls']==0
    for path in sources:
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path));add(path.relative_to(ROOT).as_posix())
    for folder in ('src','reports','results','artifacts'):
        name=folder+'/'+NS+'/.gitattributes'
        if folder=='artifacts':
            pins[name]=sha(ROOT/name) # Own empty artifact namespace marker, never a project-data pin.
        else:add(name)
    add('reports/'+NS+'/protocol.md');add(receipt_path.relative_to(ROOT).as_posix())
    manifest = {'status':PREPARATION_STATUS,'UTC':datetime.now(timezone.utc).isoformat(),'files':pins,
                'runtime_provider_module':MODULE,'runtime_provider_qualname':'provide',
                'shared_cache_prefix':str(CACHE_PREFIX),'supported_request':REQUEST,'phases':list(PHASES),
                'software_status_sha256':SOFTWARE_STATUS_SHA,'pandas_admission_sha256':PANDAS_ADMISSION_SHA,
                'admitted_v4_profile_origin_sha256':PROFILE_ORIGIN_SHA,
                'data_access_authorized':False,'actual_runtime_provider_invoked':False,
                'scientific_imports':False,'actual_native_calls':0,'project_payload_reads':0,
                'actual_provider_origin_acceptance_pending':True,'original_resource_guards_unchanged':True}
    path = ROOT/PREPARATION
    with path.open('xb') as stream:
        stream.write((json.dumps(manifest,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
    print('REAL_RUNTIME_PROVIDER_SOURCE_READY',len(pins),sha(path),flush=True)


if __name__=='__main__':run()
