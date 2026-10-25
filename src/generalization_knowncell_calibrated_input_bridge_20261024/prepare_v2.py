"""Freeze additive V2 path compatibility, preserving the original48 pins."""
import ast
from .spec_v2 import *
from . import contracts as c

V1_SHA='f0b7e0b9dd3df91a76864e49fa352e3463418a4a9b7ea50d99a1cc73879a3af9'


def run():
    assert not any((ROOT/binding_path(stage)).exists() for stage in STAGES)
    path=OUT/'preparation_manifest.json';raw=path.read_bytes();assert c.digest(raw)==V1_SHA
    original=c.decode(raw);pins=dict(original['files']);assert len(pins)==48
    for name,want in pins.items():assert c.digest((ROOT/name).read_bytes())==want,name
    pins[path.relative_to(ROOT).as_posix()]=V1_SHA
    receipt_path=OUT/'synthetic_tests_receipt_v2.json';receipt=c.decode(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_CALIBRATED_INPUT_BRIDGE_V2_CERTIFICATE_PATH_ONLY' and receipt['tests']==14
    sources=sorted(SRC.glob('*.py'))
    assert receipt['source_files']=={p.relative_to(ROOT).as_posix():c.digest(p.read_bytes()) for p in sources}
    assert receipt['project_payloads_read']==receipt['actual_Git_calls']==receipt['actual_resource_probes']==0
    assert receipt['native_scientific_imports'] is False and receipt['actual_root_bindings_created'] is False
    own=[SRC/name for name in ('bridge_v2.py','spec_v2.py','tests_v2.py','prepare_v2.py')]
    own += [REP/'protocol_v2.md',receipt_path,OUT/'synthetic_tests_attempt_v2_01.log']
    for path in own:
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw)
        pins[path.relative_to(ROOT).as_posix()]=c.digest(raw)
    payload={'status':READY_STATUS,'files':pins,'original48pin_source_freeze_preserved':True,
        'original_source_manifest_sha256':V1_SHA,'required_bridge_module':'src.'+NS+'.bridge_v2',
        'only_operational_change':'fixed certificate path uses additive labels_execution_v2 generation',
        'label_certificate_path':LABEL_PATH,'protected_label_runtime_request_path':LABEL_REQUEST,
        'science_and_function_AST_unchanged':True,'actual_root_bindings_created':False,
        'actual_certificate_CORE_NPZ_payloads_read':False,'actual_resource_probes':0,
        'native_scientific_imports':False,'actual_sampler_pool_optimizer_or_gate_calls':0,
        'runtime_input_or_FIT_authority_granted':False,'requires_reviewed_actual_owned_caller':True}
    target=ROOT/READY
    with target.open('xb') as stream:stream.write(c.canonical(payload))
    print('CALIBRATED_INPUT_BRIDGE_V2_SOURCE_READY',len(pins),c.digest(target.read_bytes()),flush=True)


if __name__=='__main__':run()
