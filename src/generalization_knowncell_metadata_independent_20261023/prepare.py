"""Own-source freeze; reads definitions/source only, never actual metadata."""
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
from .spec import *
from .source_verify import STATUS_CORE

ROOT=Path(__file__).resolve().parents[2]
DEFINITIONS=('src/generalization_knowncell_joint_design_20261009/spec.py',
    'src/generalization_knowncell_joint_implementation_20261022/contracts.py',
    'src/generalization_knowncell_joint_loader_20261022/parsers.py')


def run():
    def sha(raw):return hashlib.sha256(raw).hexdigest()
    pins={}
    for name in DEFINITIONS:
        raw=(ROOT/name).read_bytes();ast.parse(raw.decode('utf-8'));pins[name]=sha(raw)
    design=ast.parse((ROOT/DEFINITIONS[0]).read_text(encoding='utf-8'))
    literals={node.targets[0].id:ast.literal_eval(node.value) for node in design.body
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
        and node.targets[0].id in ('METADATA_COLUMNS','CELLS','FOLDS','COUNTS')}
    assert literals['METADATA_COLUMNS']==COLUMNS and literals['CELLS']==CELLS and literals['FOLDS']==FOLDS
    assert {key:literals['COUNTS'][key] for key in COUNTS}==COUNTS
    src=ROOT/'src'/NS;out=ROOT/'results'/NS;rep=ROOT/'reports'/NS
    sources=sorted(src.glob('*.py'));test_path=out/'synthetic_tests_receipt.json';test=json.loads(test_path.read_bytes())
    assert test['status']=='PASS_INVENTED_PURE_INDEPENDENT_METADATA_TESTS_NOT_ACTUAL_ADMISSION'
    assert test['sources']=={path.relative_to(ROOT).as_posix():sha(path.read_bytes()) for path in sources}
    assert test['project_payloads_read']==test['actual_metadata_verifications']==test['actual_workers']==test['actual_resource_probes']==test['model_fits']==0
    assert test['scientific_imports'] is False and test['reference_builders_or_parsers_called'] is False
    files=sources+[ROOT/folder/NS/'.gitattributes' for folder in ('src','reports','results','artifacts')]
    files+=[rep/'protocol.md',test_path]
    for path in files:
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw.decode('utf-8'),filename=str(path))
        pins[path.relative_to(ROOT).as_posix()]=sha(raw)
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
    manifest={'status':'SOURCE_FROZEN_PURE_INDEPENDENT_METADATA_VERIFIER_NOT_ACTUAL_VERIFICATION_OR_EXECUTION_ADMISSION',
        'UTC':datetime.now(timezone.utc).isoformat(),'files':pins,'counts':COUNTS,'original_row_ID_order_sha256':ROW_IDS_SHA,
        'public_verifier_status':STATUS,'public_API':'verify_bundle(supplied_JSON_bytes_or_dict)',
        'public_source_verifier_status':STATUS_CORE,
        'public_source_API':'verify_bundle_and_core(supplied_bundle,supplied_CORE_text_or_text_stream)',
        'actual_metadata_verifications':0,'project_payloads_read':0,'actual_workers':0,'actual_resource_probes':0,
        'actual_provider_calls':0,'scientific_imports':False,'model_fits':0,
        'reference_builders_or_parsers_imported_or_called':False,
        'existing_metadata_source_and_contract_semantics_used_only_as_definitions':True,
        'independent_owned_worker_controller_and_source_admission_implemented':False,
        'actual_metadata_reconstruction_and_committed_result_REQUIRED':True,
        'source_CSV_derivation_NOT_verified_from_bundle_alone':True,
        'supplied_CORE_parser_implemented_but_actual_source_verification_NOT_run':True,
        'author_biological_lineage_NOT_verified_by_either_API':True,
        'resource_guards_changed':False,'authorization_created':False}
    path=out/'preparation_manifest.json'
    with path.open('xb') as stream:stream.write((json.dumps(manifest,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
    print('PURE_INDEPENDENT_METADATA_SOURCE_READY',len(pins),sha(path.read_bytes()),flush=True)


if __name__=='__main__':run()
