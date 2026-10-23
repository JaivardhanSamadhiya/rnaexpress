"""Freeze reviewed invented inputs/sources, without numerical package imports."""
import ast
import json
import subprocess
import sys
from .common import *

REFERENCES = (
    'src/generalization_current_python_20261022/attest.py',
    'src/generalization_prelib_numpy_profile_v2_20261022/invented.py',
    'src/generalization_prelib_numpy_profile_20261022/invented.py',
    'src/generalization_splicebert_runtime_compatibility_20261007/common.py',
    'src/generalization_splicebert_runtime_compatibility_20261007/launcher.py',
    'src/generalization_pum_process_probe_20261021/headless.py',
    'src/generalization_pum_resource_calibration_20261009/winjob.py',
    'src/generalization_knowncell_joint_loader_20261022/parsers.py',
    'src/generalization_knowncell_joint_loader_20261022/spec.py',
    'src/generalization_knowncell_joint_loader_20261022/loader.py',
    'src/generalization_knowncell_joint_implementation_20261022/kernels.py',
    'src/generalization_knowncell_joint_implementation_20261022/contracts.py',
    'src/generalization_knowncell_joint_implementation_20261022/spec.py',
    'src/generalization_knowncell_joint_design_20261009/spec.py',
    'src/generalization_knowncell_joint_numeric_20261022/numeric.py',
    'src/generalization_knowncell_joint_numeric_20261022/spec.py',
    'src/cross_assay_20260927/models.py',
    'src/generalization_knowncell_20261007/common.py',
    'src/generalization_splicebert_20261007/backend_probe.py',
    'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json',
    'artifacts/generalization_splicebert_runtime_compatibility_20261007/numpy_official_member_parity.json',
    'results/generalization_splicebert_runtime_compatibility_20261007/preparation_manifest.json',
    'results/generalization_splicebert_20261007/backend_preparation_manifest.json',
    'results/generalization_current_python_20261022/current_python_inventory.json',
    'results/generalization_prelib_numpy_profile_v2_20261022/preparation_manifest_reviewed.json',
    'results/generalization_prelib_numpy_profile_v2_20261022/invented_numpy_receipt.json',
    'results/generalization_prelib_numpy_profile_v2_20261022/supervisor_receipt.json',
    'results/generalization_knowncell_joint_numeric_20261022/preparation_manifest.json',
    'results/generalization_knowncell_joint_numeric_20261022/synthetic_tests_receipt.json',
    'results/generalization_knowncell_joint_loader_20261022/readiness_manifest_reviewed.json',
)


def committed(path):
    from src.generalization_pum_process_probe_20261021.headless import GitFacade
    assert GitFacade(subprocess).check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT) == path.read_bytes()


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    for path in (PYTHON, RUNTIME,
                 ROOT/'results/generalization_prelib_numpy_profile_v2_20261022/preparation_manifest_reviewed.json',
                 ROOT/'results/generalization_prelib_numpy_profile_v2_20261022/invented_numpy_receipt.json',
                 ROOT/'results/generalization_prelib_numpy_profile_v2_20261022/supervisor_receipt.json',
                 ROOT/'results/generalization_knowncell_joint_numeric_20261022/preparation_manifest.json',
                 ROOT/'results/generalization_knowncell_joint_loader_20261022/readiness_manifest_reviewed.json'):
        committed(path)
    previous=json.loads((ROOT/'results/generalization_prelib_numpy_profile_v2_20261022/supervisor_receipt.json').read_bytes())
    assert previous['status']=='PASS_BOUNDED_INVENTED_NUMPY_PROFILE_V2'
    current=json.loads(PYTHON.read_bytes()); inventory=json.loads(INVENTORY.read_bytes())
    assert current['python_version']==sys.version==inventory['python_version']
    assert inventory['files']==payload_members(json.loads(RUNTIME.read_bytes())['files'])
    assert sha(PYTHON)==inventory['current_python_inventory_sha256']
    assert sha(RUNTIME)==inventory['old_runtime_receipt_sha256']
    check_payload_files(inventory['files'])
    for path,want in inventory['current_python_native_files'].items():assert sha(path)==want
    test_path=OUT/'stdlib_test_receipt_final.json'; tests=json.loads(test_path.read_bytes())
    assert tests['status']=='PASS_STDLIB_MOCK_PREPARATION_ONLY' and tests['tests_run']>=21
    for name,want in tests['source_sha256'].items():assert sha(ROOT/name)==want
    files=list(SRC.glob('*'))+list(REP.glob('*'))+[OUT/'.gitattributes',INVENTORY,test_path,
        OUT/'draft_snapshot_20261022.json',OUT/'stdlib_test_receipt.json',OUT/'stdlib_tests_attempt_01.log',
        OUT/'stdlib_test_receipt_reviewed.json',OUT/'stdlib_tests_attempt_02.log']
    files += [ROOT/name for name in REFERENCES]
    assert all(path.is_file() for path in files)
    for path in files:
        if path.suffix=='.py':ast.parse(path.read_text(encoding='utf-8'))
    assert (ROOT/'src/generalization_pum_resource_calibration_20261009/winjob.py').read_text().count('PROCESS_LIMIT = 768 * 2**20')==1
    manifest={'status':STATUS,'files':{path.relative_to(ROOT).as_posix():sha(path) for path in files},
        'python_executable':sys.executable,'python_executable_sha256':sha(sys.executable),
        'python_version':sys.version,'numerical_threads':1,'environment':THREAD_ENV,
        'worker_python_flags':['-S','-B','-u'],
        'process_memory_limit_bytes':768*2**20,'job_memory_limit_bytes':896*2**20,'active_process_limit':2,
        'startup_physical_floor_bytes':512*2**20,'stop_physical_floor_bytes':256*2**20,
        'system_commit_reserve_bytes':2**30,'deadline_seconds':120,
        'parser_options':{'usecols':['intervention_id','measured_delta'],'low_memory':False,
                          'skiprows':'number>0 and number not in set(original_core_row+1)',
                          'conversion':'measured_delta.to_numpy(float)'},
        'optimizer':{'method':'L-BFGS-B','options':OPTIONS,'penalties':list(PENALTIES),
                     'invented_rows':128,'invented_pairs':64,'feature_width':102,'optimizer_units':12},
        'biological_inputs_read':False,'native_profile_executed':False,
        'old_interpreter_bitwise_parity_established':False,'automatic_retry':False,
        'worker_fresh_payload_scope':'Full NumPy payload; every actually imported pandas/SciPy/dependency source/native before and after cases; unused files preparation-inventoried only',
        'native_execution_requires_root_commit_and_explicit_start':True}
    jsave(MANIFEST,manifest)
    print('INVENTED_ONE_THREAD_PROFILE_FROZEN',len(manifest['files']),sha(MANIFEST),flush=True)


if __name__=='__main__':run()
