"""Freeze no authority: source/import/hash readiness for the finite prototype."""
import ast
import importlib
from pathlib import Path
import sys
from . import contracts as c,spec


def run():
    assert spec.ROOT.resolve()==spec.EXPECTED_ROOT.resolve() and spec.ROOT.drive.casefold()=='c:'
    blocked=('numpy','pandas','scipy','torch','openvino','sklearn')
    clean=lambda:not any(name.split('.')[0] in blocked for name in sys.modules)
    assert clean()
    for name in ('context','current','inputs','plan','sampler','science'):importlib.import_module('src.'+spec.NS+'.'+name)
    assert clean();pins={};loaded={}
    def add(path,want=None):
        path=Path(path);assert path.resolve().is_relative_to(spec.ROOT.resolve())
        raw=path.read_bytes();actual=c.digest(raw)
        assert want is None or actual==want
        relative=path.relative_to(spec.ROOT).as_posix()
        assert relative not in pins or pins[relative]==actual;pins[relative]=actual
        if path.suffix=='.py':ast.parse(raw.decode('utf8'))
        return raw
    for path in (spec.ROOT/'src'/spec.NS).glob('*.py'):add(path)
    receipt_path=spec.OUT/'synthetic_tests_receipt_reviewed.json';receipt=c.decode(add(receipt_path))
    own_sources={p.relative_to(spec.ROOT).as_posix():c.digest(p.read_bytes()) for p in (spec.ROOT/'src'/spec.NS).glob('*.py')}
    assert receipt['sources']==own_sources and receipt['tests']>=13
    for name,module in sorted(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(spec.ROOT.resolve()):
                assert path.suffix=='.py';add(path);loaded[name]=path.relative_to(spec.ROOT).as_posix()
    for folder in ('src','reports','results','artifacts'):add(spec.ROOT/folder/spec.NS/'.gitattributes')
    add(spec.ROOT/'reports'/spec.NS/'protocol.md')
    for name,want in ((spec.INVENTORY,spec.INVENTORY_SHA),(spec.PROFILE_MANIFEST,spec.PROFILE_MANIFEST_SHA),
            (spec.PROFILE_RECEIPT,spec.PROFILE_RECEIPT_SHA),(spec.PROFILE_CERTIFICATE,spec.PROFILE_CERTIFICATE_SHA)):
        add(spec.ROOT/name,want) # Software metadata only; no native/payload scan.
    for name in list(pins):
        if name.startswith('src/') and name.endswith('.py'):
            parent=(spec.ROOT/name).parent
            while parent.is_relative_to(spec.ROOT/'src'):
                if (parent/'__init__.py').is_file():add(parent/'__init__.py')
                parent=parent.parent
    assert clean()
    value={'status':'DRAFT_CURRENT_CONTEXT_PORTABILITY_SOURCE_NOT_RUNTIME_OWNER_OR_FIT_ADMISSION','files':pins,
        'loaded_source_modules':loaded,'invented_tests':receipt['tests'],'actual_jobs_or_authority_records':0,
        'scientific_imports':False,'actual_project_rows_or_model_values_read':False,'actual_native_or_resource_probes':0,
        'final_manifest_created':False,'full_current_owned_pipeline_implemented':False,
        'remaining_integration':['real_current_provider','fixed_owned_controller_and_new_manual_authorization',
            'guarded_C_input_loading_and_current_prefit','exact_five_alias_transaction','actual_fit_replay_evaluation']}
    out=spec.OUT/'draft_readiness.json'
    with out.open('xb') as stream:stream.write(c.canonical(value))
    print('DRAFT_SOURCE_READY',len(pins),c.digest(out.read_bytes()),flush=True)


if __name__=='__main__':run()
