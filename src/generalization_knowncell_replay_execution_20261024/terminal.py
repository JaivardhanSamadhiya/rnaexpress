"""Parent validation of saved replay evidence; no runtime authority or refit."""
import math
import time
from . import common as c
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_joint_campaign_20261023.writer import check_predictions
from src.generalization_knowncell_prefit_projection_v2_20261024.projection import CalibratedBoundPlan
from src.generalization_knowncell_campaign_replay_20261023.replay import ERROR_FIELDS

PROTECTED=('runtime_acceptance','runtime_acceptance_after_replay','current_owner_context','projection_current_owner_receipt',
    'projection_context_raw','plan_identity','plan_operational_context','sampler_identity','bridge_report',
    'independent_replay','campaign_files_sha256')


def fresh(started):
    from src.generalization_pum_process_probe_20261021 import headless
    assert c.resource_failure(headless.memory(),time.monotonic()-started) is None


def bound_read(name,want,started):
    fresh(started);path=c.relative(name)
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<=64*2**20
    raw=path.read_bytes();assert c.sha(raw)==want
    return raw


def result_contract(result,plan,run):
    assert result['status']=='PASS_SUPPLIED63_CHECKPOINT84_UNIT_ARITHMETIC_AND_SOURCE_RESELECTION'
    assert result['prefit_sha256']==plan.prefit_sha256 and result['runtime_binding_sha256']==plan.runtime_binding_sha256
    assert result['verified_checkpoints']==63 and result['verified_optimizer_units_not_refitted']==84
    assert result['verified_inner_checkpoints']==54 and result['new_optimizer_calls']==0 and result['gate_or_evaluation_run'] is False
    assert result['independent_confirmation'] is result['unknown_cell_generalization'] is result['novelty_certified'] is False
    tasks={lc.task_key(task):task for task in lc.task_roster()}
    assert set(result['arithmetic_receipts'])==set(tasks)
    outer={key:task for key,task in tasks.items() if task['phase']=='outer'}
    assert set(result['source_only_outer_reselections'])==set(outer)
    for key,task in tasks.items():
        receipt=result['arithmetic_receipts'][key];pool=plan.pool(task)
        assert receipt['status']=='PASS_SUPPLIED_CHECKPOINT_SCALAR_AND_CANONICAL_ARITHMETIC_ONLY'
        assert receipt['arm']==task['arm'] and receipt['optimizer_units_not_refitted']==task['optimizer_units']
        assert receipt['source_rows']==pool['training_rows'] and receipt['source_pairs']==pool['training_pairs']
        assert receipt['target_rows']==pool['validation_rows'] and receipt['new_optimizer_calls']==0
        assert receipt['exact_canonical_scores_equal'] is True and receipt['tolerance']==1e-9
        for name in ERROR_FIELDS:
            value=receipt[name];assert type(value) in (int,float) and math.isfinite(value) and 0<=value<1e-9
    for name in ERROR_FIELDS:
        assert result['maximum_arithmetic_differences'][name]==max(item[name] for item in result['arithmetic_receipts'].values())
    records=result['canonical_outer_records'];assert len(records)==9
    seen=set()
    for record in records:
        assert set(record)=={'arm','outer_fold','predictions'}
        matches=[task for task in outer.values() if task['arm']==record['arm'] and task['outer_fold']==record['outer_fold']]
        assert len(matches)==1
        task=matches[0];key=lc.task_key(task);assert key not in seen;seen.add(key)
        check_predictions(record['predictions'],plan.pool(task))
        assert all(type(v) is float and math.isfinite(v) for v in record['predictions']['scores'])
        selection=result['source_only_outer_reselections'][key]['selection']
        assert selection['arm']==task['arm'] and selection['outer_fold']==task['outer_fold']
        assert selection['source_only'] is selection['primary_paired_only'] is True
        assert selection['prefit_sha256']==plan.prefit_sha256 and selection['runtime_binding_sha256']==plan.runtime_binding_sha256
    assert seen==set(outer)
    base=(c.FIT_CAMPAIGN/'checkpoints').relative_to(c.ROOT).as_posix()+'/'
    assert result['campaign_birth_sha256']==run['campaign_pins'][base+'campaign_birth.json']
    assert result['campaign_complete_sha256']==run['campaign_pins'][base+'campaign_complete.json']
    return result


def validate_report(report,completion,run,generation,run_sha,birth_sha,parent_pid,worker_pid,started):
    assert report['status']=='ACTUAL_ONE_OWNED_INDEPENDENT63_CHECKPOINT_REPLAY_NO_EVALUATION'
    assert completion['status']=='PASS_INDEPENDENT_REPLAY_WORKER_CALLBACKS_RESTORED_NO_EVALUATION'
    for key,want in (('generation_manifest_sha256',generation),('run_admission_sha256',run_sha),('birth_sha256',birth_sha),
            ('parent_pid',parent_pid),('worker_pid',worker_pid),('approved_policy_manifest_sha256',c.POLICY_SHA),
            ('authorization_sha256',c.AUTH_SHA),('approval_scope_sha256',c.SCOPE_SHA),('invocation',c.INVOCATION)):
        assert report[key]==completion[key]==want,key
    assert completion['callbacks_restored'] is True and completion['fresh_calibrated_guard_calls']>0
    assert completion['source_mode']==c.source_mode() and completion['resource_policy']==c.resource_policy()
    for key,want in (('verified_checkpoints',63),('verified_recorded_optimizer_units',84),('new_optimizer_calls',0)):
        assert report[key]==completion[key]==want
    assert report['CORE_reread'] is completion['CORE_reread'] is report['evaluation_or_gate_run'] is completion['evaluation_or_gate_run'] is False
    assert report['source_pools_rebuilt']==9 and report['source_selections_replayed']==9
    assert report['saved_label_bits_sha256']==c.LABEL_BITS_SHA and report['biological_or_generalization_claim'] is False
    assert report['actual_prefit_sha256']==completion['actual_prefit_sha256']==run['input_pins'][c.PREFIT]
    assert report['fit_report_sha256']==run['input_pins'][c.FIT_REPORT] and report['fit_supervisor_sha256']==run['input_pins'][c.FIT_SUPERVISOR]
    assert report['campaign_files_sha256']==run['campaign_pins']
    assert report['source_npz_read']['actual_sha256']==c.NPZ_SHA and report['source_npz_read']['fresh_original_resource_gate_before_open'] is False
    assert c.sha(c.canonical({key:report[key] for key in PROTECTED}))==report['protected_provenance_sha256']
    prefit_raw=bound_read(c.PREFIT,run['input_pins'][c.PREFIT],started)
    root_raw=bound_read(c.PROJECTION_ADMISSION,run['input_pins'][c.PROJECTION_ADMISSION],started);root=lc.strict_json(root_raw)
    # Saved declarations only. Actual worker binder/context verification remains mandatory.
    plan=CalibratedBoundPlan(root['prefit_relative_path'],root['prefit_commit'],prefit_raw,c.sha(prefit_raw),
        root['runtime_binding_sha256'],root_raw,report['projection_context_raw'].encode('utf8'))
    assert plan.identity()==report['plan_identity'] and plan.operational_context()==report['plan_operational_context']
    assert plan.prefit_commit==run['actual_prefit_commit']
    assert plan.operational_context()['current_owner_receipt_sha256']==c.sha(c.canonical(report['projection_current_owner_receipt']))
    for key,phase in (('runtime_acceptance','before_replay'),('runtime_acceptance_after_replay','after_replay')):
        proof=report[key]
        assert proof['status']==c.runtime.PROVIDER_STATUS and proof['stage']==c.STAGE and proof['provider_phase']==phase
        assert proof['current_pid']==worker_pid and proof['parent_pid']==parent_pid and proof['caller_birth_sha256']==birth_sha
        assert proof['static_root_binding_sha256']==run['input_pins'][c.STATIC_BINDING]
        assert proof['reviewed_controller_admission_sha256']==run['input_pins'][c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()]
        assert proof['stable_admitted_runtime_binding_sha256']==plan.runtime_binding_sha256
        assert proof['request_binding']['request_relative_path']==c.REQUEST and proof['request_binding']['request_sha256']==run['input_pins'][c.REQUEST]
        assert proof['actual_origin_receipt_sha256']==c.runtime.PROFILE_ORIGIN_SHA
        assert proof['software_status_sha256']==c.runtime.SOFTWARE_STATUS_SHA and proof['software_certificate_sha256']==c.runtime.PANDAS_ADMISSION_SHA
        assert proof['fresh_current_python_and_loaded_native_origins_checked'] is True and proof['invented_only'] is False
        assert proof['optimizer_calls']==0 and proof['runtime_and_FIT_authority_granted_here'] is False
        assert proof['numerical_threads']==1 and proof['source_cache_remained_absent'] is True
    owner=report['current_owner_context'];assert owner['caller_birth_sha256']==birth_sha
    assert owner['current_pid']==worker_pid and owner['parent_pid']==parent_pid
    assert owner['current_stage_origin_proof_sha256']==lc.hash_value(report['runtime_acceptance'])
    calibration=report['resource_calibration']
    assert calibration['stage']==c.STAGE and calibration['execution_manifest_sha256']==generation
    assert calibration['birth_sha256']==birth_sha and calibration['authorization_sha256']==c.AUTH_SHA
    assert calibration['current_pid']==worker_pid and calibration['parent_pid']==parent_pid
    assert calibration['scientific_protocol_settings_changed'] is False
    result_contract(report['independent_replay'],plan,run)
    for name,want in run['campaign_pins'].items():bound_read(name,want,started)
    fresh(started)
    return {'status':'PASS_PARENT_COMPLETE_REPLAY_EVIDENCE_NOT_INDEPENDENT_BIOLOGICAL_CONFIRMATION',
        'verified_checkpoints':63,'verified_recorded_optimizer_units':84,'new_optimizer_calls':0,
        'source_only_reselections':9,'canonical_outer_records':9,'saved_plan_validation_grants_no_current_authority':True}
