"""Source-only closure; no actual input/certificate payload is read."""
import ast
from pathlib import Path
import sys
from src.generalization_knowncell_joint_input_bridge_20261023 import spec as old
from .spec import *
from . import contracts as c


def run():
    assert not any((ROOT/binding_path(stage)).exists() for stage in STAGES)
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    old_raw=(ROOT/old.READY).read_bytes();old_document=c.decode(old_raw)
    assert old_document['status']=='SOURCE_ONLY_EXACT_SAMPLER_AND_SUPPLIED_INPUT_BRIDGE_NOT_PROJECT_OR_FIT_ADMISSION'
    pins=dict(old_document['files'])
    for name,want in pins.items():assert c.digest((ROOT/name).read_bytes())==want,name
    pins[old.READY]=c.digest(old_raw)
    sources=sorted(SRC.glob('*.py'));receipt_path=OUT/'synthetic_tests_receipt.json'
    receipt=c.decode(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_CALIBRATED_SUPPLIED_INPUT_BRIDGE_NOT_ACTUAL_EXECUTION'
    assert receipt['tests']>=14 and receipt['source_files']=={p.relative_to(ROOT).as_posix():c.digest(p.read_bytes()) for p in sources}
    assert receipt['project_payloads_read']==receipt['actual_Git_calls']==receipt['actual_resource_probes']==0
    assert receipt['native_scientific_imports'] is False and receipt['actual_root_binding_created'] is False
    # Bind imported local source dependencies, including original real IO helpers.
    for module in tuple(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            path=Path(name).resolve()
            if path.is_relative_to((ROOT/'src').resolve()):assert path.suffix=='.py';sources.append(path)
    own=[ROOT/top/NS/'.gitattributes' for top in ('src','reports','results')]
    own += [REP/'protocol.md',receipt_path,OUT/'synthetic_tests_attempt_01.log']
    for path in set(sources+own):
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw.decode('utf8'))
        pins[path.relative_to(ROOT).as_posix()]=c.digest(raw)
    payload={'status':READY_STATUS,'files':pins,'original_bridge_and_sampler_readiness_preserved':True,
        'supplied_input_library_only':True,'requires_reviewed_actual_owned_caller':True,
        'current_parent_Job_or_native_origins_certified_here':False,'actual_root_bindings_created':False,
        'actual_certificate_OR_CORE_OR_NPZ_payloads_read':False,'actual_resource_probes':0,'native_scientific_imports':False,
        'actual_sampler_pool_optimizer_or_gate_calls':0,'runtime_input_or_FIT_authority_granted':False}
    path=ROOT/READY
    with path.open('xb') as stream:stream.write(c.canonical(payload))
    print('CALIBRATED_SUPPLIED_INPUT_BRIDGE_SOURCE_READY',len(pins),c.digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
