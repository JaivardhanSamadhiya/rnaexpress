"""Source/import closure only. No data, runtime, probes or actual FIT."""
import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_current_fixed_fit_core_20261026'
OUT=ROOT/'results'/NS


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    assert sys.flags.no_site==1 and sys.dont_write_bytecode
    cache=ROOT/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
    assert sys.pycache_prefix==str(cache) and not cache.exists()
    receipt_path=OUT/'synthetic_tests_receipt.json';receipt=json.loads(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_CURRENT_FIXED_FIT_CORE_NOT_NATIVE_OR_ACTUAL_AUTHORITY'
    assert receipt['tests']==7 and receipt['failures']==receipt['errors']==0
    assert receipt['actual_scientific_imports']==receipt['actual_data_reads']==receipt['actual_native_jobs']==receipt['actual_optimizer_calls']==0
    for name,want in receipt['source_sha256'].items():assert sha(ROOT/name)==want,name
    for suffix in ('plan','driver','tests'):importlib.import_module('src.'+NS+'.'+suffix)
    files={};imported={}
    for name,module in tuple(sys.modules.items()):
        source=getattr(module,'__file__',None)
        if not source:continue
        path=Path(source).resolve()
        if path.is_relative_to(ROOT/'src') and path.suffix=='.py':
            key=path.relative_to(ROOT).as_posix();files[key]=sha(path);imported[name]=key
            parent=path.parent
            while parent.is_relative_to(ROOT/'src'):
                init=parent/'__init__.py'
                if init.exists():files[init.relative_to(ROOT).as_posix()]=sha(init)
                parent=parent.parent
    for kind in ('src','artifacts','reports','results'):
        for path in (ROOT/kind/NS).rglob('*'):
            if path.is_file():files[path.relative_to(ROOT).as_posix()]=sha(path)
    for name in files:
        if name.endswith('.py'):ast.parse((ROOT/name).read_text(encoding='utf8'),filename=name)
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    value={'status':'FROZEN_PURE_CURRENT_FIXED_FIT_CORE_NOT_ACTUAL_AUTHORITY',
        'files':dict(sorted(files.items())),'file_count':len(files),'source_import_closure':imported,
        'actual_data_or_model_reads':0,'actual_numerical_imports_or_optimizer_calls':0,
        'actual_owned_controller_or_authorization_supplied':False}
    path=OUT/'source_preparation_manifest.json'
    with path.open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
    print('PURE_CORE_SOURCE_ONLY',len(files),sha(path),flush=True)


if __name__=='__main__':run()
