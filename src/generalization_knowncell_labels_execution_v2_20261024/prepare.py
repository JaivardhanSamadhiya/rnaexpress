"""Additive source-closure correction; no runtime, payload, probe or job."""
import ast
import importlib
from pathlib import Path
import sys
from . import common as c

ORIGINAL_PREPARATION='results/generalization_knowncell_labels_execution_20261024/preparation_manifest.json'
ORIGINAL_PREPARATION_SHA='5f0d275c53782c4ad438b3ecfcb1f082af8117797b9bb6e140b95fdc486b883c'
PRODUCTION=('common','admit','calibration','supervise','worker')


def loaded_workspace_sources():
    """Inspect already loaded source origins; never import a scientific module."""
    loaded={}
    for name,module in sorted(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if filename is None:continue
        path=Path(filename).resolve()
        if not path.is_relative_to(c.ROOT.resolve()):continue
        assert path.suffix=='.py','Unexpected native/cache workspace import'
        assert not path.is_symlink()
        loaded[name]={'path':path.relative_to(c.ROOT).as_posix(),'sha256':c.sha(path.read_bytes())}
    return loaded


def run():
    assert not c.RUN_ADMISSION.exists() and not (c.ROOT/c.REQUEST).exists()
    forbidden=('numpy','pandas','scipy','torch','sklearn','openvino')
    def no_science():return not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert no_science()
    pins={}
    def add(name,want=None):
        raw=c.relative(name).read_bytes();actual=c.sha(raw)
        assert want is None or actual==want,name
        assert name not in pins or pins[name]==actual,'Conflicting source-closure pins'
        pins[name]=actual
        return raw
    old=c.decode(add(ORIGINAL_PREPARATION,ORIGINAL_PREPARATION_SHA))
    for name,want in old['files'].items():add(name,want)
    assert old['runtime_provider_preparation_sha256']==c.RUNTIME_PREPARATION_SHA
    runtime=c.decode(add(c.runtime.PREPARATION,c.RUNTIME_PREPARATION_SHA))
    for name,want in runtime['files'].items():add(name,want)
    # Actual source-only imports are the admission audit, not a manually guessed
    # import list. They do not enter worker.run, a guard, provider or callback.
    for suffix in PRODUCTION:importlib.import_module('src.'+c.NS+'.'+suffix)
    assert no_science()
    loaded=loaded_workspace_sources()
    for item in loaded.values():add(item['path'],item['sha256'])
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    for path in sources:
        ast.parse(path.read_text(encoding='utf8'),filename=str(path))
        add(path.relative_to(c.ROOT).as_posix())
    receipt_path=c.OUT/'synthetic_tests_receipt_reviewed.json'
    receipt=c.decode(add(receipt_path.relative_to(c.ROOT).as_posix()))
    assert receipt['status']=='PASS_INVENTED_ORIGINAL_PARSER_LABEL_EXECUTION_NOT_ACTUAL_ADMISSION'
    assert receipt['tests']==12
    assert receipt['sources']=={path.relative_to(c.ROOT).as_posix():c.sha(path.read_bytes()) for path in sources}
    for key in ('actual_jobs','actual_resource_probes','actual_provider_invocations','project_payload_reads','label_rows_admitted','model_fits'):
        assert receipt[key]==0
    assert receipt['scientific_imports'] is False
    for folder in ('src','reports','results','artifacts'):add(folder+'/'+c.NS+'/.gitattributes')
    add('reports/'+c.NS+'/protocol.md')
    parents={}
    for name in list(pins):
        if name.startswith('src/') and name.endswith('.py'):
            parent=c.relative(name).parent
            while parent.is_relative_to(c.ROOT/'src'):
                init=parent/'__init__.py'
                if init.is_file():
                    relative=init.relative_to(c.ROOT).as_posix();add(relative);parents[relative]=pins[relative]
                parent=parent.parent
    # Exact same production objects remain imported; prove the completed pin
    # roster admits EVERY loaded workspace module after all preparation reads.
    final_loaded=loaded_workspace_sources()
    assert final_loaded==loaded
    missing={name:item for name,item in final_loaded.items() if pins.get(item['path'])!=item['sha256']}
    assert not missing,'Unpinned production import closure: '+repr(missing)
    required=('src/generalization_knowncell_metadata_independent_20261023/__init__.py',
              'src/generalization_knowncell_metadata_independent_20261023/spec.py')
    assert all(name in pins for name in required)
    assert all(name not in old['files'] for name in required)
    for name,want in old['python_native_files'].items():assert c.sha(Path(name).read_bytes())==want
    c.save_new(c.MANIFEST,{'status':c.STATUS,'invocation':c.INVOCATION,'files':pins,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'resource_policy':c.resource_policy(),
        'python_executable':old['python_executable'],'python_native_files':old['python_native_files'],
        'runtime_provider_preparation_sha256':c.RUNTIME_PREPARATION_SHA,
        'preserved_unexecuted_v1_preparation_sha256':ORIGINAL_PREPARATION_SHA,
        'all_365_v1_source_pins_retained':all(pins[name]==want for name,want in old['files'].items()),
        'actual_production_imports_checked':list(PRODUCTION),'loaded_workspace_modules':final_loaded,
        'regular_parent_init_pins':parents,'missing_loaded_workspace_source_pins':missing,
        'two_previously_missing_source_paths':list(required),
        'shared_runtime_and_v1_request_namespace_path_unchanged':True,
        'expected_actual_array_certificate_sha256':c.ARRAY_CERTIFICATE_SHA,
        'expected_actual_array_supervisor_sha256':c.ARRAY_SUPERVISOR_SHA,
        'expected_actual_array_generation_sha256':c.ARRAY_GENERATION_SHA,
        'actual_source_preparation_payload_reads':0,'actual_provider_invocations':0,'actual_jobs':0,
        'actual_resource_probes':0,'actual_label_rows_admitted':0,'model_fits':0,
        'actual_request_or_input_admission_created':False,'original_frozen_sources_changed':False,
        'frozen_original_parser_and_float64_hash_semantics_preserved':True,
        'labels_certificate_persists_original_vector_tolist_and_exact_bit_hash':True,
        'future_committed_request_input_admission_and_owned_controller_required':True,
        'old_original_guard_true_only_bridge_not_used_or_modified':True})
    print('LABELS_EXECUTION_V2_SOURCE_READY',len(pins),len(final_loaded),c.sha(c.MANIFEST.read_bytes()),flush=True)


if __name__=='__main__':run()
