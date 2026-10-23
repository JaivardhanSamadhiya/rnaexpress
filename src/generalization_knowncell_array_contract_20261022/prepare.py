"""Source-only readiness. Never follows any project-array/input-receipt alias."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from .spec import NS, ROOT, SRC, REP, OUT, SHAPE, MAX_NPZ_BYTES, MAX_NPY_BYTES, MAX_HEADER_BYTES, STATUS

PARTIAL_PINS = {
    '__init__.py': 'c2ab7c11216b9c8a0566df32ecb32d9e790c062dcfdcbceacc1d13f379d5a080',
    'spec.py': '161e630fac14250ccda8daf40409e7105e0bade24626e5879210cd7c02917c8e',
    'inspect_bytes.py': 'c6058886025051d3247d6757beeae86f8c5d3d08f30fe41f8d93e8b1d4e05f7d',
}
REFERENCE_SOURCE = (
    'src/generalization_knowncell_joint_design_20261009/spec.py',
    'src/generalization_knowncell_joint_implementation_20261022/spec.py',
    'src/generalization_knowncell_joint_implementation_20261022/contracts.py',
    'src/generalization_knowncell_joint_implementation_20261022/admission.py',
    'src/generalization_crosscell_20261007/prepare.py',
    'src/generalization_crosscell_20261007/common.py',
    'src/generalization_knowncell_20261007/evaluate.py',
)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def run():
    for name, expected in PARTIAL_PINS.items(): assert sha((SRC/name).read_bytes()) == expected, 'Preserve original partial source'
    receipt_path=OUT/'synthetic_tests_receipt.json'; receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    assert receipt['status']=='PASS_INVENTED_STDLIB_SUPPLIED_ARRAY_CONTRACT_TESTS'
    for key in ('actual_NumPy_calls','actual_native_resource_probes','project_array_reads','project_metadata_reads','project_outcome_reads','models_fitted'):
        assert receipt[key]==0
    assert receipt['scientific_runtimes_imported'] is False and receipt['project_admission_granted'] is False
    sources=sorted(SRC.glob('*.py'))
    assert receipt['source_files']=={path.relative_to(ROOT).as_posix():sha(path.read_bytes()) for path in sources}
    for path in sources: ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    files=sources+[SRC/'.gitattributes',REP/'.gitattributes',REP/'protocol.md',OUT/'.gitattributes',receipt_path]
    pins={path.relative_to(ROOT).as_posix():sha(path.read_bytes()) for path in files}
    for name in REFERENCE_SOURCE:
        assert name.startswith('src/') and name.endswith('.py')
        raw=(ROOT/name).read_bytes(); ast.parse(raw.decode('utf-8'),filename=name); pins[name]=sha(raw)
    payload={'status':'SOURCE_ONLY_SUPPLIED_ARRAY_CONTRACT_NOT_PROJECT_ADMISSION',
             'generated_utc':datetime.now(timezone.utc).isoformat(),'files':pins,
             'original_partial_files_unchanged':PARTIAL_PINS,'public_result_status':STATUS,
             'fixed_project_shape':SHAPE,'compressed_byte_cap':MAX_NPZ_BYTES,
             'expanded_NPY_byte_cap':MAX_NPY_BYTES,'NPY_header_byte_cap':MAX_HEADER_BYTES,
             'project_array_reads':0,'project_metadata_reads':0,'project_outcome_reads':0,'models_fitted':0,
             'scientific_runtimes_imported':False,'actual_NumPy_calls':0,'actual_native_resource_probes':0,
             'full_shape_positive_validation_NOT_run':True,
             'source_preparation_reads_only_own_receipt_and_source_text':True,
             'project_aliases_input_receipt_bytes_original_pin_values_NOT_read_or_certified':True,
             'source_metadata_array_or_FIT_admission_GRANTED':False,
             'accepted_runtime_currentPython_actual_origins_NOT_established_here':True,
             'future_caller_must_prove_runtime_and_supply_real_fresh_resource_probe':True,
             'fresh_resource_RAM_floor':3*2**30,'fresh_resource_disk_floor':2**30,
             'numerical_threads':1,'PUM_resource_exception_applies':False,
             'project_wrapper_and_actual_Git_pin_admission_implemented':False,
             'no_automatic_worker_queue_download_or_fitting':True}
    target=OUT/'readiness_manifest.json'
    with target.open('xb') as handle: handle.write((json.dumps(payload,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
    print('SOURCE_ONLY_ARRAY_CONTRACT_READY',len(pins),sha(target.read_bytes()),flush=True)


if __name__=='__main__': run()
