"""One distinct root-owned verifier invocation; actual input admission deferred."""
import argparse
import os
import sys
import time
import json
from . import common as c
from .monitor import observe


def command(generation_sha,run_sha,birth_sha):
    return [sys.executable,'-S','-B','-X','pycache_prefix='+str(c.CACHE_PREFIX),'-u','-m',
            'src.'+c.NS+'.worker',str(os.getpid()),c.valid_sha(generation_sha),
            c.valid_sha(run_sha),c.valid_sha(birth_sha)]


def completion_contract(value,generation_sha,run_sha,birth_sha,*,parent_pid,worker_pid):
    assert value['status']=='PASS_SECOND_METADATA_WORKER_INDEPENDENT_CONTRACT_CALLBACKS_RESTORED'
    assert value['invocation']==c.INVOCATION and value['category']=='metadata'
    assert value['generation_manifest_sha256']==generation_sha
    assert value['approved_policy_manifest_sha256']==c.POLICY_SHA
    assert value['authorization_sha256']==c.AUTH_SHA and value['approval_scope_sha256']==c.SCOPE_SHA
    assert value['run_admission_sha256']==run_sha and value['birth_sha256']==birth_sha
    assert value['parent_pid']==parent_pid and value['worker_pid']==worker_pid
    assert type(value['parent_pid']) is type(value['worker_pid']) is int and min(parent_pid,worker_pid)>0
    assert value['callbacks_restored'] is True
    assert type(value['fresh_calibrated_guard_calls']) is int and value['fresh_calibrated_guard_calls']>0
    assert value['numerical_outcomes_admitted']==value['actual_feature_reads']==value['model_fits']==0
    assert value['scientific_packages_imported'] is False
    assert value['original_3GiB_resource_guard_unchanged'] is False
    assert value['resource_policy']==c.resource_policy()
    c.valid_sha(value['independent_report_sha256'])
    assert value['independent_helper_source_manifest_sha256']==c.HELPER_MANIFEST_SHA
    c.valid_sha(value['independent_helper_result_canonical_sha256'])
    assert value['metadata_counts']==c.HELPER_COUNTS and value['row_ids_sha256']==c.HELPER_ROW_IDS_SHA
    c.valid_sha(value['metadata_sha256']);c.valid_sha(value['all_core_ids_sha256'])
    return value


def validate_report(raw,generation_sha,run_sha,birth_sha,completion,admission,*,parent_pid,worker_pid):
    """Actual terminal JSON semantic/identity binding, independent of worker IO."""
    value=c.decode(raw);assert c.canonical(value)==raw,'Canonical terminal verifier JSON required'
    assert value['status']=='PASS_INDEPENDENT_METADATA_DERIVATION_AND_CONTRACT_WITH_OWNED_RAW_READ_PROOF'
    assert value['invocation']==c.INVOCATION and value['category']=='metadata'
    assert value['generation_manifest_sha256']==generation_sha
    assert value['approved_policy_manifest_sha256']==c.POLICY_SHA
    assert value['authorization_sha256']==c.AUTH_SHA and value['approval_scope_sha256']==c.SCOPE_SHA
    assert value['run_admission_sha256']==run_sha and value['birth_sha256']==birth_sha
    assert value['parent_pid']==parent_pid and value['worker_pid']==worker_pid
    assert value['independent_helper_source_manifest_sha256']==completion['independent_helper_source_manifest_sha256']==c.HELPER_MANIFEST_SHA
    assert value['acquisition_input_hashes']==admission['input_pins']
    assert value['acquisition_source_generation_sha256']==admission['acquisition_generation_manifest_sha256']==c.ACQ_GENERATION_SHA
    assert value['each_acquisition_input_committed_bytes_checked'] is True
    assert value['array_label_or_FIT_permission_granted'] is False
    assert value['numerical_outcomes_admitted']==value['actual_feature_reads']==value['model_fits']==0
    assert value['canonical_scientific_values_preserved'] is True
    assert value['outer_raw_CORE_SHA_verified_against_frozen_admission'] is True
    assert set(value['payload_reads'])==set(c.INPUT_PATHS)
    for key,proof in value['payload_reads'].items():
        assert proof['actual_sha256']==admission['input_pins'][c.INPUT_PATHS[key]]
        assert type(proof['raw_bytes_traversed']) is int and proof['raw_bytes_traversed']>0
        assert proof['fresh_original_resource_gate_before_open'] is False
    core=value['core_read'];assert core['actual_sha256']==c.CORE_SHA
    assert type(core['raw_bytes_traversed']) is int and core['raw_bytes_traversed']>0
    assert core['fresh_original_resource_gate_before_open'] is False
    calibration=value['resource_calibration']
    assert calibration['execution_manifest_sha256']==generation_sha
    assert calibration['approved_policy_manifest_sha256']==c.POLICY_SHA
    assert calibration['authorization_sha256']==c.AUTH_SHA and calibration['approval_scope_sha256']==c.SCOPE_SHA
    assert calibration['invocation']==c.INVOCATION and calibration['stage']=='metadata'
    assert calibration['birth_sha256']==birth_sha
    assert calibration['parent_pid']==parent_pid and calibration['current_pid']==worker_pid
    assert calibration['callbacks_restored_at_annotation'] is False
    assert calibration['fresh_calibrated_guard_calls']==completion['fresh_calibrated_guard_calls']
    assert calibration['startup_physical_floor']==512*2**20 and calibration['live_physical_floor']==256*2**20
    assert calibration['disk_floor']==calibration['live_global_commit_reserve']==2**30
    assert calibration['scientific_protocol_settings_changed'] is False
    assert calibration['scientific_metadata_and_contracts_unchanged'] is True
    assert value['original_resource_guards_unchanged'] is False
    independent=value['independent_verification']
    assert independent['status']==c.HELPER_STATUS
    assert independent['counts']==completion['metadata_counts']==c.HELPER_COUNTS
    assert independent['row_ids_sha256']==completion['row_ids_sha256']==c.HELPER_ROW_IDS_SHA
    assert independent['metadata_sha256']==completion['metadata_sha256']
    assert independent['all_core_ids_sha256']==completion['all_core_ids_sha256']
    assert independent['all_core_rows_independently_parsed']==26258
    assert independent['outer_masks_rebuilt']==3 and independent['inner_masks_rebuilt']==6
    for key in ('source_CSV_metadata_derivation_independently_verified',
                'original_core_position_alignment_independently_verified','nonMikl_full_core_ID_roster_independently_verified',
                'both_cells_used_for_every_purge','source_and_target_full_menus_preserved','original_row_order_preserved'):
        assert independent[key] is True,key
    for key in ('raw_CORE_byte_SHA_proven_here','author_biological_lineage_independently_verified',
                'reference_builder_or_parser_called','metadata_rows_normalized_or_modified',
                'extra_filtering_or_gene_alias_repair','array_label_or_FIT_permission_granted',
                'unused_outcome_fields_numerically_converted'):
        assert independent[key] is False,key
    assert independent['parsed_outcome_values']==independent['model_fits']==0
    assert independent['requires_guarded_original_CORE_SHA_and_Git_ownership_from_caller'] is True
    contract=independent['reconstructed_contract']
    assert contract['row_ids_sha256']==independent['row_ids_sha256'] and contract['metadata_sha256']==independent['metadata_sha256']
    compact=(json.dumps(contract,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
    assert independent['canonical_contract_sha256']==c.sha(compact)
    protected=c.sha(c.canonical(independent))
    assert value['independent_verifier_canonical_sha256']==completion['independent_helper_result_canonical_sha256']==protected
    return value


def run(generation_sha,run_sha,*,root_start=False):
    assert root_start is True,'Only an explicit root-owned invocation is admitted'
    started=time.monotonic()
    authorization=c.admit_authorization(generation_sha)
    admission=c.read_run(generation_sha,run_sha,check_commit=True)
    c.require_new_outputs()
    birth_sha=c.save_new(c.BIRTH,{
        'status':'ONE_OWNED_INDEPENDENT_METADATA_INVOCATION_CONSUMED','category':'metadata',
        'invocation':c.INVOCATION,'parent_pid':os.getpid(),'generation_manifest_sha256':generation_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,
        'approval_scope_sha256':c.SCOPE_SHA,'run_admission_sha256':run_sha,
        'resource_policy':c.resource_policy(),'source_mode':c.source_mode(),'automatic_retry':False})
    from src.generalization_pum_process_probe_20261021 import headless
    before=headless.memory();failure=c.resource_failure(before,time.monotonic()-started,startup=True)
    observed={};child=None
    if failure is None:
        with headless.Job() as job:
            try:
                assert job.limits()=={'process_memory_limit':c.PROCESS_CAP,'job_memory_limit':c.JOB_CAP,
                                     'active_process_limit':2,'limit_flags':headless.original.LIMIT_FLAGS}
                c.verify_sources(generation_sha)
                assert c.read_run(generation_sha,run_sha)==admission
                failure=c.resource_failure(headless.memory(),time.monotonic()-started,startup=True)
                assert failure is None,failure
                child=job.spawn(command(generation_sha,run_sha,birth_sha),str(c.ROOT));child.resume()
                observed=observe(job,child,headless.memory,headless.process_memory,time.monotonic,time.sleep)
                failure=observed['failure']
            except BaseException as error:
                failure=failure or type(error).__name__+': '+str(error);job.terminate()
                if child is not None and 'final_process_handle_peak_sample' not in observed:
                    try:observed['final_process_handle_peak_sample']=headless.process_memory(child.process_handle)
                    except BaseException as peak_error:observed['peak_sampling_error']=str(peak_error)
            finally:
                if child is not None:child.close()
    completion_sha=report_sha=None
    try:
        c.verify_sources(generation_sha)
        assert failure is None,failure
        assert observed.get('exit_code')==0,'Independent verifier did not complete successfully'
        assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
        raw=c.COMPLETION.read_bytes();completion=completion_contract(c.decode(raw),generation_sha,run_sha,birth_sha,
                                                                   parent_pid=os.getpid(),worker_pid=child.pid)
        assert completion['source_mode']==c.source_mode()
        completion_sha=c.sha(raw)
        assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
        report_raw=c.REPORT.read_bytes();report_sha=c.sha(report_raw);assert report_sha==completion['independent_report_sha256']
        validate_report(report_raw,generation_sha,run_sha,birth_sha,completion,admission,
                        parent_pid=os.getpid(),worker_pid=child.pid)
    except BaseException as error:
        failure=failure or type(error).__name__+': '+str(error)
    try:
        assert c.admit_authorization(generation_sha)==authorization
        assert c.read_run(generation_sha,run_sha,check_commit=True)==admission
        assert c.sha(c.BIRTH.read_bytes())==birth_sha
        if completion_sha is not None:
            assert c.sha(c.COMPLETION.read_bytes())==completion_sha
            assert c.resource_failure(headless.memory(),time.monotonic()-started) is None
            assert c.sha(c.REPORT.read_bytes())==report_sha
        c.verify_sources(generation_sha)
    except BaseException as error:
        failure=failure or type(error).__name__+': '+str(error)
    after=headless.memory();elapsed=time.monotonic()-started
    failure=failure or c.resource_failure(after,elapsed)
    receipt={'status':'PASS_SECOND_METADATA_EXECUTION_REQUIRES_REVIEW_AND_COMMIT' if failure is None else
                     'FAILED_OR_BLOCKED_SECOND_METADATA_INVOCATION_PRESERVED',
        'failure':failure,'invocation':c.INVOCATION,'category':'metadata',
        'generation_manifest_sha256':generation_sha,'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'independent_report_sha256':report_sha,'worker_completion_sha256':completion_sha,
        'worker_started':child is not None,'observed':observed,'memory_before':before,'memory_after':after,
        'elapsed_seconds':elapsed,'resource_policy':c.resource_policy(),'automatic_retry':False,
        'original_3GiB_resource_guard_unchanged':False,'scientific_protocol_settings_changed':False,
        'numerical_outcomes_admitted':0,'actual_feature_reads':0,'model_fits':0}
    c.save_new(c.SUPERVISOR,receipt)
    print(receipt['status'],failure,flush=True)
    assert failure is None,failure
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--generation-sha',required=True)
    parser.add_argument('--run-admission-sha',required=True);parser.add_argument('--root-start',action='store_true')
    args=parser.parse_args();run(args.generation_sha,args.run_admission_sha,root_start=args.root_start)
