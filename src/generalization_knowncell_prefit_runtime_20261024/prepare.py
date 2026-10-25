"""Source/software preparation with actual fixed-caller import closure."""
import ast
import importlib
from pathlib import Path
import sys
from .spec import *
from . import contracts as c
from src.generalization_knowncell_metadata_verification_execution_20261024 import common as saved


def run():
    assert not (ROOT/REQUEST).exists()
    forbidden=('numpy','pandas','scipy','torch','sklearn','openvino')
    assert not any(name.split('.')[0] in forbidden for name in sys.modules)
    raw=(ROOT/ORIGINAL_PROVIDER_PREPARATION).read_bytes();assert c.digest(raw)==ORIGINAL_PROVIDER_SHA
    original=c.decode(raw);pins=dict(original['files']);pins[ORIGINAL_PROVIDER_PREPARATION]=ORIGINAL_PROVIDER_SHA
    for name,want in pins.items():assert c.digest((ROOT/name).read_bytes())==want,name
    importlib.import_module(MODULE);importlib.import_module(CALLER)
    loaded={}
    for name,module in sorted(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if filename is None:continue
        path=Path(filename).resolve()
        if path.is_relative_to(ROOT.resolve()):
            assert path.suffix=='.py'
            relative=path.relative_to(ROOT).as_posix();want=c.digest(path.read_bytes())
            assert relative not in pins or pins[relative]==want
            pins[relative]=want;loaded[name]={'path':relative,'sha256':want}
    assert CALLER_SOURCE in pins
    sources=sorted((ROOT/'src'/NS).glob('*.py'))
    test_path=ROOT/'results'/NS/'synthetic_tests_receipt.json';test=c.decode(test_path.read_bytes())
    assert test['status']=='PASS_INVENTED_PREFIT_RUNTIME_NOT_ACTUAL_PROVIDER' and test['tests']>=6
    assert test['sources']=={path.relative_to(ROOT).as_posix():c.digest(path.read_bytes()) for path in sources}
    assert test['actual_runtime_invocations']==test['actual_resource_probes']==test['project_payload_reads']==test['optimizer_calls']==0
    own=sources+[ROOT/folder/NS/'.gitattributes' for folder in ('src','reports','results','artifacts')]
    own += [test_path,ROOT/'reports'/NS/'protocol.md']
    for path in own:
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw.decode('utf8'))
        pins[path.relative_to(ROOT).as_posix()]=c.digest(raw)
    parents={}
    for relative in list(pins):
        if relative.startswith('src/') and relative.endswith('.py'):
            parent=(ROOT/relative).parent
            while parent.is_relative_to(ROOT/'src'):
                init=parent/'__init__.py'
                if init.is_file():
                    name=init.relative_to(ROOT).as_posix();pins[name]=c.digest(init.read_bytes());parents[name]=pins[name]
                parent=parent.parent
    assert not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert all(pins[value['path']]==value['sha256'] for value in loaded.values())
    assert all(static_allowed(name) for name in pins)
    saved.save_new(ROOT/PREPARATION,{'status':PREPARATION_STATUS,'files':pins,'runtime_provider_module':MODULE,
        'runtime_provider_qualname':'provide','fixed_actual_owner_module':CALLER,'shared_cache_prefix':str(CACHE_PREFIX),
        'loaded_workspace_source_modules':loaded,'regular_parent_init_pins':parents,'missing_import_pins':{},
        'actual_runtime_invoked':False,'data_access_authorized':False,'scientific_imports':False,
        'only_request':REQUEST,'phases':list(PHASES),'current_proofs_and_owner_still_pending':True,
        'runtime_prep_SHA_not_embedded_in_pinned_fixed_caller_source':True,'optimizer_calls':0})
    print('PREFIT_RUNTIME_SOURCE_READY',len(pins),c.digest((ROOT/PREPARATION).read_bytes()),flush=True)


if __name__=='__main__':run()
