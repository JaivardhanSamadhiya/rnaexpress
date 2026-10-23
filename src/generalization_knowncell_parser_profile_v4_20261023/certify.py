"""Post-run receipt verification only; no scientific imports or project data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'results/generalization_knowncell_parser_profile_v4_20261023'
EXPECTED = '61781e1ef932a2eb36a368279d96bd52b35bf0eaf286dc8f80021e42fd5a2daa'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((OUT/name).read_bytes())


def run():
    manifest = read('preparation_manifest.json')
    assert sha(OUT/'preparation_manifest.json') == EXPECTED
    for name, want in manifest['files'].items():
        assert sha(ROOT/name) == want, name
    supervisor, completion = read('supervisor_receipt.json'), read('invented_profile_receipt.json')
    origin, candidate = read('actual_origin_receipt.json'), read('pandas_admission_candidate.json')
    assert supervisor['status'] == 'PASS_BOUNDED_ONE_THREAD_INVENTED_PANDAS_SCIPY_PROFILE_V4'
    assert completion['status'] == 'PASS_INVENTED_PANDAS_SCIPY_PROFILE_CURRENT_PYTHON_V4'
    assert supervisor['exit_code'] == 0 and supervisor['failure'] is None
    assert supervisor['frozen_sources_unchanged'] is supervisor['initially_verified_manifest_unchanged'] is True
    assert supervisor['manifest_observed_final_sha256'] == EXPECTED
    assert all(item['preparation_manifest_sha256'] == EXPECTED for item in (supervisor,completion,origin,candidate))
    assert supervisor['invented_completion_sha256'] == sha(OUT/'invented_profile_receipt.json')
    assert completion['actual_origin_receipt_sha256'] == candidate['actual_origin_receipt_sha256'] == sha(OUT/'actual_origin_receipt.json')
    assert completion['pandas_admission_candidate_sha256'] == sha(OUT/'pandas_admission_candidate.json')
    assert supervisor['elapsed_seconds'] <= 120 and supervisor['numerical_threads'] == 1
    assert supervisor['peak_worker_private_commit_bytes'] <= 768*2**20
    assert supervisor['job_accounting']['peak_job_memory_used'] <= 896*2**20
    assert supervisor['memory_before']['physical_available'] >= 512*2**20
    assert supervisor['minimum_sampled_physical_available'] >= 256*2**20
    assert supervisor['minimum_sampled_system_commit_headroom'] >= 2**30
    assert supervisor['biological_inputs_read'] is False and supervisor['biological_model_fits'] == 0
    for state in (origin['initial'],origin['final']):
        pools = state['actually_loaded_threadpools']
        assert pools and all(pool['num_threads'] == 1 for pool in pools)
        assert state['old_exact_runtime_identity_passes'] is False
        assert state['old_interpreter_bitwise_parity_established'] is False
    assert completion['parser']['status'] == 'PASS_INVENTED_EXACT_DEFERRED_PARSER'
    assert len(completion['parser']['checks']) == 8
    assert len(completion['parser']['rejected_cases']) == 12
    optimizer = completion['optimizer']
    assert optimizer['status'] == 'PASS_INVENTED_SCIPY_SOLVER_REFERENCE_AND_SCORER'
    assert optimizer['scipy_optimizer_units'] == len(optimizer['optimizer_calls']) == 12
    assert len(optimizer['checks']) == 9
    assert {(v['arm'],v['config']) for v in optimizer['checks']} == {
        (arm,config) for arm in ('pooled','independent','joint_shrink10')
        for config in ('pair_005','pair_05','pair_5')}
    fields = ('objective_difference','gradient_max_abs_difference',
              'finite_difference_max_abs_difference','fitted_objective_difference',
              'canonical_scalar_score_max_abs_difference')
    maxima = {field:max(item[field] for item in optimizer['checks']) for field in fields}
    assert maxima['objective_difference'] < 1e-11 and maxima['gradient_max_abs_difference'] < 1e-11
    assert maxima['finite_difference_max_abs_difference'] < 2e-7
    assert maxima['fitted_objective_difference'] < 1e-10
    assert maxima['canonical_scalar_score_max_abs_difference'] < 1e-10
    extras = completion['extra_deferred_native_contracts']
    assert extras['array_contract']['status'] == 'PASS_INVENTED_SUPPLIED_NUMPY_NPZ_AND_ASTYPE_FLOAT_BITS'
    assert extras['shared_bootstrap']['status'] == 'PASS_INVENTED_NATIVE_SHARED_BOOTSTRAP_EXACT_CURRENT_RUNTIME_REPLAY'
    assert extras['shared_bootstrap']['draws'] == 5000 and extras['shared_bootstrap']['components'] == 187
    assert not (OUT/'never_created_source_cache').exists()
    # This copies the SOFTWARE certificate only. The immutable label loader
    # still requires separate committed metadata, array, FIT-label admission,
    # a real pinned runtime provider and fresh original three-GiB gates.
    from src.generalization_knowncell_joint_loader_20261022.loader import pandas_certificate_contract
    assert pandas_certificate_contract(candidate)
    pandas_path = ROOT/'results/generalization_knowncell_joint_loader_20261022/pandas_admission.json'
    raw = (OUT/'pandas_admission_candidate.json').read_bytes()
    with pandas_path.open('xb') as handle:
        handle.write(raw)
    status = {'status':'VERIFIED_CURRENT_RUNTIME_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION',
              'UTC':datetime.now(timezone.utc).isoformat(),'initial_manifest_sha256':EXPECTED,
              'verified_files':{name:sha(OUT/name) for name in (
                  'preparation_manifest.json','supervisor_receipt.json','invented_profile_receipt.json',
                  'actual_origin_receipt.json','pandas_admission_candidate.json')},
              'future_loader_software_certificate':pandas_path.relative_to(ROOT).as_posix(),
              'future_loader_certificate_sha256':sha(pandas_path),
              'elapsed_seconds':supervisor['elapsed_seconds'],
              'peak_private_job_bytes':supervisor['job_accounting']['peak_job_memory_used'],
              'numerical_maxima':maxima,'native_optimizer_units':12,'project_rows_read':0,
              'biological_model_fits':0,'old_interpreter_bitwise_parity_established':False,
              'actual_project_dataset_memory_unmeasured':True,
              'metadata_array_label_and_fit_admissions_granted_here':False,
              'original_three_GiB_project_guards_unchanged':True,
              'verification_source_sha256':sha(__file__)}
    with (OUT/'verified_native_status.json').open('x',encoding='utf-8',newline='\n') as handle:
        handle.write(json.dumps(status,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print('VERIFIED_INVENTED_NATIVE_COMPATIBILITY_ONLY',sha(OUT/'verified_native_status.json'),flush=True)


if __name__ == '__main__':run()
