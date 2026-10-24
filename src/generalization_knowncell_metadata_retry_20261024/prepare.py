"""Freeze static retry design only. Does not create approval or read payloads."""
import ast
from pathlib import Path
import sys
from . import common as c


def run():
    assert not c.AUTH.exists(), 'New one-attempt human authorization must not exist during preparation'
    assert not c.METADATA_BUNDLE.exists(), 'Never overwrite any admitted or partial target'
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    pins={}
    def add(name,want=None):
        assert name==name.replace('\\','/') and name.split('/')[0] in ('src','reports','results','artifacts')
        assert name.endswith(('.py','.md','.json','.log','/.gitattributes')), 'No biological payload allowed in source freeze'
        raw=c.relative(name).read_bytes();actual=c.sha(raw)
        assert want is None or actual==want,name
        assert name not in pins or pins[name]==actual, 'Conflicting source hash'
        pins[name]=actual
        return raw
    original_raw=add(c.ORIGINAL_MANIFEST,c.ORIGINAL_MANIFEST_SHA)
    original=c.decode(original_raw)
    assert original['resource_policy']==c.resource_policy()
    for name,want in original['files'].items():add(name,want)
    add(c.ORIGINAL_AUTH,c.ORIGINAL_AUTH_SHA);add(c.ORIGINAL_SCOPE,c.ORIGINAL_SCOPE_SHA)
    for name,want in c.PRESERVED_FAILURE.items():add(name,want)
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    source_hashes={}
    for path in sources:
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
        name=path.relative_to(c.ROOT).as_posix();add(name);source_hashes[name]=pins[name]
    receipt_path='results/'+c.NS+'/synthetic_tests_receipt.json'
    receipt=c.decode(add(receipt_path))
    assert receipt['status']=='PASS_INVENTED_CORRECTED_METADATA_JSON_REGRESSION_NOT_RETRY_AUTHORIZATION'
    assert receipt['tests']>=10 and receipt['sources']==source_hashes
    for key in ('actual_workers','actual_resource_probes','project_metadata_reads','project_array_reads',
                'project_label_reads','model_fits','production_alias_patches'):
        assert receipt[key]==0
    assert receipt['actual_approval_created'] is False
    for folder in ('src','reports','results','artifacts'):add(folder+'/'+c.NS+'/.gitattributes')
    add('reports/'+c.NS+'/protocol.md')
    for name in list(pins):
        if name.startswith('src/') and name.endswith('.py'):
            parent=c.relative(name).parent
            while parent.is_relative_to(c.ROOT/'src'):
                init=parent/'__init__.py'
                if init.is_file():add(init.relative_to(c.ROOT).as_posix())
                parent=parent.parent
    for name,want in original['python_native_files'].items():
        assert c.sha(Path(name).read_bytes())==want,name
    manifest={'status':c.STATUS,'UTC':c.datetime.now(c.timezone.utc).isoformat(),'files':pins,
        'python_executable':original['python_executable'],'python_native_files':original['python_native_files'],
        'stages':list(c.STAGES),'implemented_entrypoints':list(c.IMPLEMENTED_STAGES),
        'resource_policy':c.resource_policy(),'cache_prefix':str(c.CACHE_PREFIX),
        'original_resource_manifest_sha256':c.ORIGINAL_MANIFEST_SHA,
        'original_resource_authorization_sha256':c.ORIGINAL_AUTH_SHA,
        'original_resource_scope_sha256':c.ORIGINAL_SCOPE_SHA,'preserved_failed_attempt':c.PRESERVED_FAILURE,
        'new_additional_owned_invocations_requested':1,
        'new_human_answer_required':'Approve one corrected metadata acquisition',
        'new_authorization_path':c.AUTH.relative_to(c.ROOT).as_posix(),
        'new_authorization_exists_at_preparation':False,'original_admitted_metadata_target_absent_at_preparation':True,
        'actual_retry_performed':False,'approval_created':False,'project_payload_or_numeric_package_read':False,
        'metadata_JSON_normalization_only':True,'calibration_function_and_class_AST_parity':True,
        'all_scientific_rows_contracts_features_labels_splits_tolerances_gates_unchanged':True,
        'only_metadata_one_attempt_eligible':True,'label_or_array_or_model_permission':False,
        'future_Git_HEAD_exact_bytes_and_real_owned_job_checks_still_required':True,
        'independent_metadata_reconstruction_still_required_after_success':True,
        'full_size_corrected_serialization_not_tested_or_executed':True}
    c.save_new(c.MANIFEST,manifest)
    print('CORRECTED_METADATA_RETRY_SOURCE_READY',len(pins),c.sha(c.MANIFEST.read_bytes()),flush=True)


if __name__=='__main__':run()
