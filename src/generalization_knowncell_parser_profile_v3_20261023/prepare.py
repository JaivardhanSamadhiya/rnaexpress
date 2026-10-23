"""Metadata/opaque byte inventory only; no native retry or cache execution."""
import json
from .common import *


def run():
    assert sha(BASE_MANIFEST)==BASE_MANIFEST_SHA
    base_manifest=json.loads(BASE_MANIFEST.read_bytes())
    for name,want in base_manifest['files'].items():assert sha(ROOT/name)==want,name
    old=json.loads(RUNTIME.read_bytes());base=json.loads(BASE_INVENTORY.read_bytes())
    assert len(base['files'])==7996 and base['old_runtime_receipt_sha256']==sha(RUNTIME)
    evidence=[]
    for name,want in ADDITIONAL_CACHES.items():
        path=PREFIX/name
        assert name not in base['files'] and old['files'][name]==want
        assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(PREFIX.resolve())
        assert sha(path)==want,name
        evidence.append({'relative_path':name,'size_bytes':path.stat().st_size,'sha256':want,
                         'old_full_receipt_match':True,'omitted_by_original_subset':True})
    inventory=dict(base)
    inventory.update(status='INVENTORIED_OLD_PAYLOAD_PLUS_TWO_OLD_ROOT_CACHES_NATIVE_RETRY_PENDING',
        files=expanded_files(base['files'],old['files']),file_count=7998,
        base_inventory_sha256=sha(BASE_INVENTORY),additional_cache_files=ADDITIONAL_CACHES,
        failed_v2_preparation_manifest_sha256=sha(BASE_MANIFEST))
    jsave(INVENTORY,inventory)
    receipt_path=BASE_OUT/'supervisor_receipt.json';log_path=BASE_OUT/'invented_worker.log'
    failed=json.loads(receipt_path.read_bytes())
    assert failed['status']=='FAILED_INVENTED_PROFILE_PRESERVED' and failed['exit_code']==1
    assert failed['frozen_sources_unchanged'] is True
    jsave(OUT/'failure_diagnosis.json',{
        'status':'VERIFIED_TWO_OLD_ROOT_CACHE_INVENTORY_OMISSIONS_NO_NATIVE_RETRY',
        'failure_supervisor_sha256':sha(receipt_path),'failure_worker_log_sha256':sha(log_path),
        'failed_v2_elapsed_seconds':failed['elapsed_seconds'],
        'first_offending_module_identified_by_v2_log':False,
        'stage':'initial cache proof before parser/optimizer/array/bootstrap cases',
        'cache_evidence':evidence,
        'unselected_py_cache_admitted':False,'scientific_packages_imported':False,
        'cache_payloads_executed':False,'project_biological_inputs_read':False,
        'native_retry_started':False})
    print('V3_TWO_CACHE_INVENTORY',len(inventory['files']),sha(INVENTORY),flush=True)


if __name__=='__main__':run()
