"""Freeze complete production source imports; never open admitted data/pools."""
import ast
import importlib
from pathlib import Path
import sys
from . import common as c

DEPENDENCIES=(
    ('results/generalization_knowncell_fit_retry_execution_20261025/preparation_manifest.json','8f30e3684125044dc1db3c9b66d05c8633fda4f4201cf1b91cf7c5c5e3c8a738'),
    ('results/generalization_knowncell_prefit_execution_20261024/preparation_manifest.json','d934fc04f562b5c07ea1ca6fad7ee86ee57635d7167ec42219dd19b2d012f8a1'),
    ('results/generalization_knowncell_labels_execution_v2_20261024/preparation_manifest.json','168409af1f862fbd46a81311c7ce58b1fade5e8e6227e8e0e371de5acf8dfe50'),
    ('results/generalization_knowncell_joint_engine_20261023/preparation_manifest_v2.json',c.STABLE_SCIENTIFIC_BINDINGS['fit_source_manifest_sha256']),
    ('results/generalization_knowncell_joint_numeric_20261022/preparation_manifest.json',c.STABLE_SCIENTIFIC_BINDINGS['numeric_source_manifest_sha256']),
    ('results/generalization_knowncell_joint_campaign_20261023/preparation_manifest_v2.json',c.STABLE_SCIENTIFIC_BINDINGS['lifecycle_v2_manifest_sha256']),
    ('results/generalization_knowncell_joint_input_bridge_20261023/preparation_manifest.json','1e02f7ed6993513f9147aa6703b6d52d99c04a8f1d8e2f39bb829e8a8a47f851'),
    (c.PROJECTION_READY,c.PROJECTION_READY_SHA),('results/generalization_knowncell_joint_runner_20261023/preparation_manifest.json','ba130fda7006228da14dd93def1f27c6bb57a5d04fbe5150932b64c79b227897'),(c.BRIDGE_READY,None),(c.runtime.PREPARATION,None))
PRODUCTION=('common','inputs','build','calibration','monitor','projection_io','worker','terminal','journal','supervise')


def run():
    assert not c.RUN_ADMISSION.exists() and not c.SOURCE_ADMISSION.exists() and not (c.ROOT/c.REQUEST).exists()
    forbidden=('numpy','pandas','scipy','torch','sklearn','openvino')
    def no_science():return not any(name.split('.')[0] in forbidden for name in sys.modules)
    assert no_science();pins={}
    def add(name,want=None):
        assert name not in set(c.INPUT_PINS)|{c.NPZ,c.prior.CORE,c.PREFIT,c.PREFIT_COMPLETION,c.PREFIT_SUPERVISOR,c.PROJECTION_ADMISSION},'Actual biological inputs excluded from source freeze'
        raw=c.relative(name).read_bytes();actual=c.sha(raw)
        assert want is None or actual==want,name
        assert name not in pins or pins[name]==actual,'Conflicting source pin'
        pins[name]=actual;return raw
    for name,want in DEPENDENCIES:
        document=c.decode(add(name,want))
        for path,expected in document['files'].items():add(path,expected)
    for suffix in PRODUCTION:importlib.import_module('src.'+c.NS+'.'+suffix)
    importlib.import_module('src.generalization_knowncell_fit_managed_runtime_20261025.provider')
    assert no_science();loaded={}
    for name,module in sorted(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if filename is None:continue
        path=Path(filename).resolve()
        if path.is_relative_to(c.ROOT.resolve()):
            assert path.suffix=='.py'
            relative=path.relative_to(c.ROOT).as_posix();add(relative)
            loaded[name]={'path':relative,'sha256':pins[relative]}
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    test_path=c.OUT/'synthetic_tests_receipt.json';test=c.decode(add(test_path.relative_to(c.ROOT).as_posix()))
    assert test['status']=='PASS_INVENTED_FIXED_FIT_EXECUTION_NOT_ACTUAL_FIT' and test['tests']>=12
    assert test['sources']=={path.relative_to(c.ROOT).as_posix():c.sha(path.read_bytes()) for path in sources}
    for key in ('actual_jobs','actual_resource_probes','actual_provider_invocations','project_payload_reads','actual_pools_prepared','optimizer_calls'):
        assert test[key]==0
    for path in sources:ast.parse(path.read_text(encoding='utf8'));add(path.relative_to(c.ROOT).as_posix())
    for folder in ('src','reports','results','artifacts'):add(folder+'/'+c.NS+'/.gitattributes')
    add('reports/'+c.NS+'/protocol.md');add(c.RETRY_SCOPE)
    add('artifacts/'+c.NS+'/source_copy_origins.json')
    add('results/generalization_knowncell_interruption_audit_20261025/interrupted_fit_audit.json',c.INTERRUPTED_AUDIT_SHA)
    parents={}
    for name in list(pins):
        if name.startswith('src/') and name.endswith('.py'):
            parent=c.relative(name).parent
            while parent.is_relative_to(c.ROOT/'src'):
                init=parent/'__init__.py'
                if init.is_file():
                    relative=init.relative_to(c.ROOT).as_posix();add(relative);parents[relative]=pins[relative]
                parent=parent.parent
    assert all(pins[item['path']]==item['sha256'] for item in loaded.values()) and no_science()
    original=c.decode(c.policy.MANIFEST.read_bytes())
    for path,want in original['python_native_files'].items():assert c.sha(Path(path).read_bytes())==want
    c.save_new(c.MANIFEST,{'status':c.STATUS,'invocation':c.INVOCATION,'files':pins,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'resource_policy':c.resource_policy(),
        'python_executable':original['python_executable'],'python_native_files':original['python_native_files'],
        'runtime_provider_preparation_sha256':pins[c.runtime.PREPARATION],'stable_scientific_source_bindings':c.STABLE_SCIENTIFIC_BINDINGS,
        'loaded_workspace_source_modules':loaded,'regular_parent_init_pins':parents,'missing_import_pins':{},
        'source_admission_runtime_request_run_admission_not_created':True,'actual_source_preparation_payload_reads':0,
        'actual_provider_invocations':0,'actual_jobs':0,'actual_resource_probes':0,'actual_pools_prepared':0,'optimizer_calls':0,
        'additional_root_startup_physical_floor':c.RETRY_STARTUP_PHYSICAL,'actual_prefit_resource_exception_required_true':True,'original_scientific_fields_and_pool_bindings_unchanged':True,
        'original_AST_sampler_and_adapter_v2_prepare_pools_reused':True,'CORE_reread':False,'FIT_authority_granted':False,
        'projection_binder_and_campaign_not_invoked_during_preparation':True,'current_owner_and_proof_hashes_not_in_static_inputs':True})
    print('FIXED_FIT_EXECUTION_SOURCE_READY',len(pins),c.sha(c.MANIFEST.read_bytes()),flush=True)


if __name__=='__main__':run()
