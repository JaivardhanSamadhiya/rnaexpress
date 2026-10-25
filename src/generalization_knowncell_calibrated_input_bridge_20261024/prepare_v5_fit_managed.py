"""Source-only closure for the separate immutable fresh-FIT binding path."""
import ast
from pathlib import Path
import sys
from . import spec_v5_fit_managed as s,bridge_v5_fit_managed
from src.generalization_knowncell_metadata_verification_execution_20261024 import common as saved


def run():
    assert not (saved.ROOT/s.binding_path('fit')).exists()
    assert not any(n.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for n in sys.modules)
    path=saved.ROOT/'results'/s.NS/'preparation_manifest_v3.json';raw=path.read_bytes()
    assert saved.sha(raw)=='67d7660c759b3aa4269640ea19b7bfb55be407a0746b57d1ac670b03ffb7cdf8'
    old=saved.decode(raw);pins=dict(old['files']);pins[path.relative_to(saved.ROOT).as_posix()]=saved.sha(raw)
    for name,want in pins.items():assert saved.sha((saved.ROOT/name).read_bytes())==want,name
    folder=Path(__file__).parent
    def fn(name):return next(n for n in ast.parse((folder/name).read_text()).body if isinstance(n,ast.FunctionDef))
    assert ast.dump(fn('bridge_v3.py'),include_attributes=False)==ast.dump(fn('bridge_v5_fit_managed.py'),include_attributes=False)
    receipt=saved.ROOT/'results'/s.NS/'synthetic_tests_receipt_v5_fit_managed_20261025.json'
    test=saved.decode(receipt.read_bytes());assert test['tests']==3 and test['actual_jobs_native_probes_payload_reads_or_fits']==0
    for name,want in test['sources'].items():assert saved.sha((saved.ROOT/name).read_bytes())==want; pins[name]=want
    own=[Path(__file__),receipt,saved.ROOT/'reports'/s.NS/'protocol_v5_fit_managed_20261025.md']
    loaded={}
    for name,module in list(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        p=Path(filename).resolve()
        if p.is_relative_to(saved.ROOT):
            assert p.suffix=='.py';own.append(p)
            loaded[name]={'path':p.relative_to(saved.ROOT).as_posix(),'sha256':saved.sha(p.read_bytes())}
    for p in own:
        name=p.relative_to(saved.ROOT).as_posix();want=saved.sha(p.read_bytes())
        assert name not in pins or pins[name]==want; pins[name]=want
        if p.suffix=='.py':ast.parse(p.read_bytes())
    assert all(pins[item['path']]==item['sha256'] for item in loaded.values())
    result={'status':'SOURCE_READY_V5_MANAGED_FRESH_FIT_BINDING_PATH_NO_RETRY_OR_FIT_AUTHORITY','files':pins,
        'previous_V3_manifest_sha256':saved.sha(raw),'required_bridge_module':'src.'+s.NS+'.bridge_v5_fit_managed',
        'loaded_workspace_source_modules':loaded,'complete_scientific_function_AST_identical_to_V3':True,
        'only_new_binding_path':s.binding_path('fit'),'old_bindings_preserved':True,
        'actual_jobs_native_probes_payload_reads_or_fits':0,'retry_or_runtime_or_FIT_authority_granted':False}
    print('V5_MANAGED_FRESH_FIT_BRIDGE_SOURCE_READY',len(pins),saved.save_new(saved.ROOT/s.READY,result),flush=True)


if __name__=='__main__':run()
