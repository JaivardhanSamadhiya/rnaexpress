"""Only source and existing static readiness summaries are read."""
import ast
from datetime import datetime,timezone
import sys
from .spec import *
from . import contracts as c,sampler,bridge


SUMMARIES=(
    'results/generalization_knowncell_array_admission_20261023/readiness_manifest.json',
    'results/generalization_knowncell_runtime_provider_20261023/preparation_manifest.json',
    'results/generalization_knowncell_joint_numeric_20261022/preparation_manifest.json',
    'results/generalization_knowncell_joint_campaign_20261023/preparation_manifest_v2.json',
    'results/generalization_knowncell_joint_engine_20261023/preparation_manifest_v2.json',
)


def run():
    pins={}
    for name,want in ((MODEL_SOURCE,MODEL_SHA),(COMMON_SOURCE,COMMON_SHA)):
        raw=(ROOT/name).read_bytes();assert c.digest(raw)==want;pins[name]=want
    node,identity=sampler.extract_function((ROOT/MODEL_SOURCE).read_bytes(),(ROOT/COMMON_SOURCE).read_bytes())
    assert node.name=='pair_indices'
    for name in SUMMARIES:
        raw=(ROOT/name).read_bytes();c.decode(raw);pins[name]=c.digest(raw)
    sources=sorted(SRC.glob('*.py'))
    test_path=OUT/'synthetic_tests_receipt.json';test=c.decode(test_path.read_bytes())
    assert test['status']=='PASS_INVENTED_STDLIB_EXACT_SAMPLER_AND_INPUT_BRIDGE'
    assert test['scientific_imports'] is False and test['project_payload_reads']==test['actual_NumPy_calls']==test['optimizer_calls']==0
    assert test['sources']=={path.relative_to(ROOT).as_posix():c.digest(path.read_bytes()) for path in sources}
    # Source dependencies imported by this stdlib-only preparation are pinned.
    for module in tuple(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            path=Path(name).resolve()
            if path.is_relative_to((ROOT/'src').resolve()):assert path.suffix=='.py';sources.append(path)
    sources+=[ROOT/folder/NS/'.gitattributes' for folder in ('src','reports','results','artifacts')]
    sources+=[REP/'protocol.md',test_path]
    for path in set(sources):
        raw=path.read_bytes();name=path.relative_to(ROOT).as_posix()
        if path.suffix=='.py':ast.parse(raw.decode('utf-8'),filename=name)
        pins[name]=c.digest(raw)
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    assert ORIGINAL_MODULE not in sys.modules and 'src.cross_assay_20260927.common' not in sys.modules
    payload={'status':'SOURCE_ONLY_EXACT_SAMPLER_AND_SUPPLIED_INPUT_BRIDGE_NOT_PROJECT_OR_FIT_ADMISSION',
        'UTC':datetime.now(timezone.utc).isoformat(),'files':pins,'sampler_source_identity':identity,
        'original_full_source_seed_and_function_AST_pinned':True,'original_wrapper_identity_is_transparent':True,
        'runtime_proof_required':'existing actual provider after_array proof, not invented compatibility PASS',
        'root_binding_hash_fields':list(BINDING_HASHES),'actual_native_resource_probes':0,'project_payload_reads':0,
        'actual_NumPy_calls':0,'actual_provider_calls':0,'optimizer_calls':0,'models_fitted':0,'scientific_imports':False,
        'guard_RAM_floor':3*2**30,'guard_disk_floor':2**30,'numerical_threads':1,'resource_exception_applies':False,
        'actual_sampler_native_parity_or_full_input_bridge_run':False,
        'actual_label_provider_and_FIT_stage_admission_NOT_implemented_here':True,
        'committed_prefit_or_training_permission_created':False,'automatic_CLI_or_writer_implemented':False}
    target=ROOT/READY
    with target.open('xb') as handle:handle.write(c.canonical(payload))
    print('SOURCE_ONLY_INPUT_BRIDGE_READY',len(pins),c.digest(target.read_bytes()),flush=True)


if __name__=='__main__':run()
