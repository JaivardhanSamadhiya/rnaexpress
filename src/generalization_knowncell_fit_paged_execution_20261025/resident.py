"""Pure resident-cap and supplied invented-profile predicates; no OS calls."""
import json
import math
from . import common as c


def installed_contract(receipt):
    assert set(receipt)=={'before','after','only_suspended_owned_child_changed','private_and_job_caps_or_live_guards_changed'}
    assert receipt['only_suspended_owned_child_changed'] is True
    assert receipt['private_and_job_caps_or_live_guards_changed'] is False
    before,after=receipt['before'],receipt['after']
    assert set(before)==set(after)=={'minimum','maximum','flags'}
    assert all(type(value) is int and value>=0 for values in (before,after) for value in values.values())
    assert 0<before['minimum']<=c.RESIDENT_CONFIGURED_LIMIT
    assert before['flags']&~15==0 and (before['flags']&3) in (0,1,2)
    assert after=={'minimum':before['minimum'],'maximum':c.RESIDENT_CONFIGURED_LIMIT,'flags':(before['flags']&3)|4}
    return receipt


def counters(sample):
    for name in ('working_set','peak_working_set'):
        value=sample[name]
        assert type(value) is int and 0<=value<=c.RESIDENT_MEASURED_CEILING,'Owned worker current/lifetime resident ceiling exceeded'
    assert sample['working_set']<=sample['peak_working_set']
    return sample


def observed_contract(value,installed):
    installed_contract(installed)
    assert value['owned_working_set_cap']==installed
    assert value['measured_resident_ceiling']==c.RESIDENT_MEASURED_CEILING
    assert type(value['resident_configuration_checks']) is int and value['resident_configuration_checks']>=0
    assert value['final_lifetime_resident_counters_checked'] is True
    assert 0<value['peak_working_set']<=c.RESIDENT_MEASURED_CEILING
    counters(value['final_process_handle_peak_sample'])
    assert value['peak_working_set']>=value['final_process_handle_peak_sample']['peak_working_set']
    return value


def numeric_profile_contract(value,child,baseline,certificate):
    """Recorded invented evidence only; no full-study/runtime authority."""
    assert value['status']==c.NUMERIC_PAGING_REQUIRED_STATUS and value['failure'] is None
    assert value['preparation_manifest_sha256']==child['preparation_manifest_sha256']==c.NUMERIC_PAGING_MANIFEST_SHA
    assert value['child_completion_sha256']==c.NUMERIC_PAGING_CHILD_SHA
    assert value['closed_parent_log_sha256']==c.NUMERIC_PAGING_JOURNAL_SHA
    assert value['requested_resident_maximum']==c.RESIDENT_CONFIGURED_LIMIT and value['measured_resident_ceiling']==c.RESIDENT_MEASURED_CEILING
    assert 0<value['peak_working_set']<=c.RESIDENT_MEASURED_CEILING and 0<value['peak_private_commit']<=c.PROCESS_CAP
    assert type(value['elapsed_seconds']) in (int,float) and math.isfinite(value['elapsed_seconds']) and 0<=value['elapsed_seconds']<=150
    assert value['minimum_sampled_physical_available']>=256*2**20
    assert c.resource_failure(value['memory_after'],value['elapsed_seconds']) is None
    installed_contract(value['additional_resident_cap'])
    assert value['unchanged_job_caps']=={'process_memory_limit':c.PROCESS_CAP,'job_memory_limit':c.JOB_CAP,'active_process_limit':2,'limit_flags':8968}
    assert value['invented_optimizer_units']==child['invented_optimizer_units']==12
    assert value['biological_rows_read']==value['scientific_attempts']==child['biological_rows_read']==child['biological_model_fits']==0
    assert value['full_FIT_or_old_interpreter_parity_established'] is False
    assert child['status']=='PASS_INVENTED_PAGED_NATIVE_NUMERICAL_PROFILE' and child['bytes']==384*2**20
    assert len(child['hashes'])==3 and len(set(child['hashes']))==1
    for digest in child['hashes']:c.valid_sha(digest)
    assert baseline['status']=='PASS_INVENTED_PANDAS_SCIPY_PROFILE_CURRENT_PYTHON_V4'
    optimizer=child['optimizer']
    assert optimizer['status']=='PASS_INVENTED_SCIPY_SOLVER_REFERENCE_AND_SCORER'
    assert optimizer['scipy_optimizer_units']==12 and optimizer['biological_model_fits']==0
    compact=lambda obj:json.dumps(obj,sort_keys=True,allow_nan=False,separators=(',',':')).encode('utf8')
    assert compact(optimizer)==compact(baseline['optimizer'])
    assert c.sha(compact(optimizer))==child['canonical_optimizer_sha256']
    for proof in (child['initial_native_proof'],child['final_native_proof']):
        assert proof['fresh_full_NumPy_payload_check'] is True and proof['old_interpreter_bitwise_parity_established'] is False
        for key in ('actually_loaded_current_python_native_files','actually_loaded_scientific_native_files','actually_loaded_scientific_modules'):
            assert isinstance(proof[key],dict) and proof[key]
    assert certificate['status']=='VERIFIED_INVENTED_NATIVE_PAGING_NUMERICAL_PROFILE_NOT_BIOLOGICAL_ADMISSION'
    for key,want in (('source_generation_sha256',c.NUMERIC_PAGING_MANIFEST_SHA),('supervisor_receipt_sha256',c.NUMERIC_PAGING_PROFILE_SHA),
            ('child_completion_sha256',c.NUMERIC_PAGING_CHILD_SHA),('closed_parent_journal_sha256',c.NUMERIC_PAGING_JOURNAL_SHA),
            ('verification_source_sha256',c.NUMERIC_PAGING_CERTIFY_SOURCE_SHA)):
        assert certificate[key]==want
    assert certificate['original_twelve_invented_optimizer_results_exact'] is certificate['three_full_buffer_hashes_independently_recomputed'] is True
    assert certificate['full_study_runtime_or_biological_generalization_established'] is False
    assert certificate['biological_rows_read']==certificate['biological_fits_or_attempts']==0
    return {'recorded_invented_numerical_profile_and_certificate_checked':True,'invented_optimizer_units':12,
        'full_study_or_old_interpreter_parity_established':False}
