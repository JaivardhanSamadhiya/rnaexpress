"""Additive v2 birth binding; preserve and verify the original52-pin manifest."""
import ast
import json
import sys
from .common_v2 import *
from .freeze import committed

EXTRA=(
 'src/generalization_knowncell_array_contract_20261022/envelope.py',
 'src/generalization_knowncell_array_contract_20261022/inspect_bytes.py',
 'src/generalization_knowncell_array_contract_20261022/spec.py',
 'src/generalization_knowncell_joint_gate_20261023/gate.py',
 'src/generalization_knowncell_joint_implementation_20261022/selection.py',
 'src/generalization_crosscell_20261007/bootstrap.py',
 'results/generalization_knowncell_array_contract_20261022/readiness_manifest.json',
 'results/generalization_knowncell_joint_gate_20261023/preparation_manifest.json',
)


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    original=OUT/'preparation_manifest.json';old=json.loads(original.read_bytes())
    assert len(old['files'])==52 and sha(original)=='a14f9650f63132a75e45babbda98bc00af691f0e17071977612f27540a4ea3dc'
    for name,want in old['files'].items():assert sha(ROOT/name)==want,name
    for name in EXTRA:committed(ROOT/name)
    receipt_path=OUT/'stdlib_test_receipt_cache_v2.json';receipt=json.loads(receipt_path.read_bytes())
    assert receipt['status']=='PASS_STDLIB_MOCK_CACHE_V2_PREPARATION_ONLY' and receipt['tests_run']==34
    for name,want in receipt['source_sha256'].items():assert sha(ROOT/name)==want,name
    sources=sorted(SRC.glob('*.py'))
    for path in sources:ast.parse(path.read_text(encoding='utf-8'))
    files=dict(old['files']);files[original.relative_to(ROOT).as_posix()]=sha(original)
    additions=sources+[ROOT/name for name in EXTRA]+[receipt_path,
        REP/'reviewed_v2.md',OUT/'stdlib_tests_attempt_03.log']
    for path in tuple(additions):
        if path.suffix=='.py' and path.is_relative_to(ROOT/'src'):
            initializer=path.parent/'__init__.py'
            if initializer.is_file():additions.append(initializer)
    root_initializer=ROOT/'src/__init__.py'
    if root_initializer.is_file():additions.append(root_initializer)
    files.update({path.relative_to(ROOT).as_posix():sha(path) for path in additions})
    result={key:value for key,value in old.items() if key!='files'}
    result.update(status=STATUS,files=files,preserved_v1_manifest_sha256=sha(original),
        existing_cache_scope='Each actually imported pinned module existing __cached__ file is additionally path/hash-bound before and after cases; possible bytecode payload only, execution not established',
        additive_invented_native_checks={'npz_shape':[2,3],'npz_allow_pickle':False,
            'original_astype_float_bits':True,'bootstrap_components':187,'bootstrap_draws':5000,
            'bootstrap_controls':['pooled','independent'],'bootstrap_seed':20261007,
            'bootstrap_reference':'exact pinned old shared_bootstrap function only, no broad import'},
        actual_native_execution=False,all_original_sources_and_receipts_preserved=True)
    jsave(MANIFEST,result)
    print('INVENTED_PROFILE_REVIEWED_V2_FROZEN',len(files),sha(MANIFEST),flush=True)


if __name__=='__main__':run()
