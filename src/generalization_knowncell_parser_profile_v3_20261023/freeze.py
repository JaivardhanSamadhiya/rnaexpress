"""Separate attempt birth freeze; preserve failed V2 and its full source pins."""
import ast
import json
import sys
from .common import *
from src.generalization_knowncell_parser_profile_20261022.freeze import committed


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    assert sha(BASE_MANIFEST)==BASE_MANIFEST_SHA
    committed(BASE_MANIFEST)
    base_manifest=json.loads(BASE_MANIFEST.read_bytes())
    for name,want in base_manifest['files'].items():assert sha(ROOT/name)==want,name
    inventory=json.loads(INVENTORY.read_bytes());base=json.loads(BASE_INVENTORY.read_bytes())
    old=json.loads(RUNTIME.read_bytes())
    assert inventory['files']==expanded_files(base['files'],old['files']) and len(inventory['files'])==7998
    for name,want in ADDITIONAL_CACHES.items():assert sha(PREFIX/name)==want,name
    test=OUT/'stdlib_test_receipt.json';receipt=json.loads(test.read_bytes())
    assert receipt['status']=='PASS_STDLIB_MOCK_V3_CACHE_CLOSURE_PREPARATION_ONLY' and receipt['tests_run']==38
    sources=sorted(SRC.glob('*.py'))
    assert receipt['source_sha256']=={path.relative_to(ROOT).as_posix():sha(path) for path in sources}
    for path in sources:ast.parse(path.read_text(encoding='utf-8'))
    files=dict(base_manifest['files'])
    additions=[BASE_MANIFEST,BASE_OUT/'supervisor_receipt.json',BASE_OUT/'invented_worker.log',
        *sources,*REP.glob('*'),SRC/'.gitattributes',OUT/'.gitattributes',INVENTORY,
        OUT/'failure_diagnosis.json',test,OUT/'stdlib_tests_attempt_01.log',
        OUT/'source_draft_attempt_01.json',OUT/'stdlib_tests_attempt_02.log']
    files.update({path.relative_to(ROOT).as_posix():sha(path) for path in additions if path.is_file()})
    result={key:value for key,value in base_manifest.items() if key!='files'}
    result.update(status=STATUS,files=files,failed_v2_manifest_sha256=sha(BASE_MANIFEST),
        additional_cache_files=ADDITIONAL_CACHES,payload_file_count=7998,
        separate_attempt_namespace=NS,all_v1_v2_sources_receipts_and_logs_preserved=True,
        native_retry_executed=False,first_v2_offending_module_retrospectively_identified=False,
        readable_cache_errors_include=['module','source','cache','resolved_path'])
    jsave(MANIFEST,result)
    print('V3_PREPARATION_FROZEN',len(files),sha(MANIFEST),flush=True)


if __name__=='__main__':run()
