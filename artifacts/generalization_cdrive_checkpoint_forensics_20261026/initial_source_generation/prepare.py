"""Freeze source-only supplied kernels; never actual inputs or execution."""
import ast
import datetime
import hashlib
import importlib
import json
from pathlib import Path
import sys
from . import spec


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    assert spec.ROOT.resolve() == spec.C_WORKSPACE.resolve()
    assert sys.flags.no_site == 1 and sys.dont_write_bytecode
    cache = spec.ROOT/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
    assert sys.pycache_prefix == str(cache) and not cache.exists()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    receipt_path = spec.OUT/'synthetic_tests_receipt.json'
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['status'] == 'PASS_INVENTED_FORENSIC_KERNELS_AND_SYMBOLIC_ROSTER_NOT_ACTUAL_CHECKPOINT_ANALYSIS'
    assert receipt['tests'] == 9 and receipt['failures'] == receipt['errors'] == 0
    assert receipt['actual_biological_payload_reads'] == receipt['actual_native_operations'] == receipt['fitter_invocations_even_mocked'] == 0
    assert receipt['actual_owned_controller_or_input_admission_ready'] is False
    own = {path.relative_to(spec.ROOT).as_posix():sha(path) for path in spec.SRC.glob('*.py')}
    assert receipt['source_sha256'] == own, 'Current source must be tested before freeze'
    for name in ('arithmetic','declarations','supplied','tests'):
        importlib.import_module('src.'+spec.NS+'.'+name)
    files = dict(own)
    imported = {}
    for name,module in tuple(sys.modules.items()):
        source = getattr(module,'__file__',None)
        if not source: continue
        path = Path(source).resolve()
        if path.is_relative_to(spec.ROOT/'src') and path.suffix == '.py':
            key = path.relative_to(spec.ROOT).as_posix(); imported[name] = key; files[key] = sha(path)
            parent = path.parent
            while parent.is_relative_to(spec.ROOT/'src'):
                init = parent/'__init__.py'
                if init.exists(): files[init.relative_to(spec.ROOT).as_posix()] = sha(init)
                parent = parent.parent
    for folder in (spec.SRC,spec.REP,spec.OUT,spec.ART):
        for path in folder.iterdir():
            if path.is_file(): files[path.relative_to(spec.ROOT).as_posix()] = sha(path)
    for name in files:
        if name.endswith('.py'): ast.parse((spec.ROOT/name).read_text(encoding='utf8'),filename=name)
    value = {'status':spec.SOURCE_STATUS,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'namespace':spec.NS,'files':dict(sorted(files.items())),'file_count':len(files),
        'source_import_closure':imported,'declared_future_resource_policy':spec.RESOURCE_POLICY,
        'native_execution_or_biological_input_admission_granted':False,
        'actual_controller_provider_and_pool_reconstruction_implemented':False,
        'actual_model_or_outcome_reads':0,'actual_optimizer_calls':0,
        'old_campaign_closure_reconstructed_or_relaxed':False}
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    path = spec.OUT/'source_preparation_manifest.json'
    with path.open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False); stream.write('\n')
    print(spec.SOURCE_STATUS,len(files),sha(path),flush=True)


if __name__ == '__main__': run()
