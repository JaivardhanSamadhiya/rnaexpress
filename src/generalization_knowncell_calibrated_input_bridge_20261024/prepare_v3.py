"""Freeze reviewed static/live binding separation and complete source closure."""
import ast
from pathlib import Path
import sys
from .spec_v3 import *
from . import contracts_v3 as c,bridge_v3

V2_SHA='7b92ce1154c3abc208f96c0c8bc9b0129ef97d59df8273aa0f87db6cf83d4040'


def run():
    assert not any((ROOT/binding_path(stage)).exists() for stage in STAGES)
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for name in sys.modules)
    previous=OUT/'preparation_manifest_v2.json';raw=previous.read_bytes();assert c.digest(raw)==V2_SHA
    old=c.decode(raw);pins=dict(old['files']);assert len(pins)==56
    for name,want in pins.items():assert c.digest((ROOT/name).read_bytes())==want,name
    pins[previous.relative_to(ROOT).as_posix()]=V2_SHA
    receipt_path=OUT/'synthetic_tests_receipt_v3_reviewed.json';receipt=c.decode(receipt_path.read_bytes())
    sources=sorted(SRC.glob('*.py'))
    assert receipt['status']=='PASS_INVENTED_STATIC_DYNAMIC_INPUT_BRIDGE_V3_NOT_ACTUAL_EXECUTION' and receipt['tests']==19
    assert receipt['source_files']=={p.relative_to(ROOT).as_posix():c.digest(p.read_bytes()) for p in sources}
    assert receipt['same_static_binding_two_distinct_current_contexts_PASS'] is True
    assert receipt['scientific_validation_AST_unchanged_from_v2'] is True
    assert receipt['actual_project_payloads_Git_resource_probe_scientific_native_sampler_pool_fit_calls']==0
    assert receipt['scientific_imports'] is False and receipt['actual_root_bindings_created'] is False
    historic=c.decode((OUT/'synthetic_tests_receipt_v3.json').read_bytes())
    draft=c.decode((OUT/'draft_source_v3_01.json').read_bytes())
    assert historic['source_files']=={name:item['sha256'] for name,item in draft['files'].items()}
    for name,item in draft['files'].items():assert c.digest(item['source'].encode('utf8'))==item['sha256'],name
    closure_path=OUT/'source_import_receipt_v3.json';closure=c.decode(closure_path.read_bytes())
    assert closure['status']=='PASS_CLEAN_V3_PRODUCTION_SOURCE_IMPORT_CLOSURE'
    assert closure['missing_pins']==closure['mismatched_pins']=={}
    assert closure['scientific_modules_imported']==[] and closure['source_cache_prefix_remained_absent'] is True
    assert closure['project_payloads_read'] is False and closure['resource_probes_or_production_calls']==0
    own=[SRC/name for name in ('spec_v3.py','contracts_v3.py','bridge_v3.py','tests_v3.py','prepare_v3.py')]
    own += [REP/'protocol_v3.md',receipt_path,closure_path,OUT/'synthetic_tests_receipt_v3.json',
        OUT/'draft_source_v3_01.json',OUT/'synthetic_tests_attempt_v3_01.log',OUT/'synthetic_tests_attempt_v3_02.log']
    for module in tuple(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            path=Path(name).resolve()
            if path.is_relative_to(ROOT/'src'):assert path.suffix=='.py';own.append(path)
    for path in set(own):
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw)
        name=path.relative_to(ROOT).as_posix();actual=c.digest(raw)
        assert name not in pins or pins[name]==actual,name
        pins[name]=actual
    for module,item in closure['loaded_workspace_modules'].items():
        assert item['path'] in pins and pins[item['path']]==item['sha256'],module
        assert c.digest((ROOT/item['path']).read_bytes())==item['sha256'],module
    payload={'status':READY_STATUS,'files':pins,'required_bridge_module':'src.'+NS+'.bridge_v3',
        'original_v1_v2_frozen_files_preserved':True,'previous_v2_manifest_sha256':V2_SHA,
        'static_root_binding_status':BINDING_STATUS,'static_root_binding_hash_fields':list(HASH_FIELDS),
        'current_owner_context_status':OWNER_STATUS,'current_owner_context_fields':sorted(OWNER_FIELDS),
        'static_binding_has_no_birth_or_current_origin_proof_hash':True,
        'same_static_binding_two_current_contexts_tested':True,'scientific_validation_AST_unchanged_from_v2':True,
        'clean_production_source_import_and_package_init_closure_checked':True,
        'actual_root_bindings_created':False,'actual_certificate_CORE_NPZ_payloads_read':False,
        'actual_resource_Git_native_sampler_pool_fit_or_gate_calls':0,
        'runtime_input_or_FIT_authority_granted':False,'requires_genuine_reviewed_owned_caller':True}
    path=ROOT/READY
    with path.open('xb') as stream:stream.write(c.canonical(payload))
    print('STATIC_DYNAMIC_INPUT_BRIDGE_V3_SOURCE_READY',len(pins),c.digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
