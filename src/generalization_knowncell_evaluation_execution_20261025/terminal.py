"""Parent consistency checks on complete saved evaluator evidence."""
import time
from . import common as c,results_io
from src.generalization_knowncell_joint_gate_20261023 import gate
from src.generalization_knowncell_joint_design_20261009.spec import ARMS,CELLS,COUNTS,GATE

PROTECTED=('runtime_acceptance','runtime_acceptance_after_evaluation','evaluation_summary',
    'complete_evaluation_storage','original_evaluation_source_manifest_sha256')


def fresh(started):
    from src.generalization_pum_process_probe_20261021 import headless
    assert c.resource_failure(headless.memory(),time.monotonic()-started) is None


def result_contract(value):
    assert value['scope']=='represented_known_cells_unseen_genes_exposed_development'
    assert value['status'] in ('JOINT_KNOWN_CELL_DEVELOPMENT_GO','NO-GO')
    assert value['model_fits_or_refits']==0 and value['new_configuration_selection'] is False
    assert value['independent_confirmation'] is value['unknown_cell_generalization'] is value['novelty_certified'] is value['localization_generalization_pass'] is False
    coverage=value['coverage'];assert coverage['rows_per_arm']==COUNTS['all_rows'] and coverage['outer_records']==9
    assert coverage['each_row_once_per_arm'] is coverage['unmatched_predictions_retained'] is True
    assert set(value['all_decisions'])==set(value['primary_decisions'])==set(value['unmatched_decisions'])==set(ARMS)
    for arm in ARMS:
        assert len(value['all_decisions'][arm])==9650 and len(value['primary_decisions'][arm])==9632 and len(value['unmatched_decisions'][arm])==18
        assert value['primary_summaries'][arm]['components']==COUNTS['components']==187
    bootstrap=value['bootstrap'];assert bootstrap['draws']==5000 and bootstrap['seed']==20261007
    assert len(bootstrap['components'])==len(set(bootstrap['components']))==187
    assert bootstrap['fixed_predictions_only'] is True and bootstrap['std_random_or_refits_used'] is False
    assert set(bootstrap['intervals'])=={'pooled','independent'}
    expected=gate.thresholds(value['primary_summaries']['joint_shrink10'],value['comparisons'],bootstrap['intervals'])
    assert value['gate']==expected and value['status']==expected['status']
    return value


def validate_report(report,completion,run,generation,run_sha,birth_sha,parent_pid,worker_pid,started):
    assert report['status']=='ACTUAL_ONE_OWNED_COMPLETE_FROZEN_EVALUATION'
    assert completion['status']=='PASS_COMPLETE_FROZEN_EVALUATION_WORKER_CALLBACKS_RESTORED'
    for key,want in (('generation_manifest_sha256',generation),('run_admission_sha256',run_sha),('birth_sha256',birth_sha),
        ('parent_pid',parent_pid),('worker_pid',worker_pid),('approved_policy_manifest_sha256',c.POLICY_SHA),
        ('authorization_sha256',c.AUTH_SHA),('approval_scope_sha256',c.SCOPE_SHA),('invocation',c.INVOCATION)):
        assert report[key]==completion[key]==want,key
    assert completion['callbacks_restored'] is True and completion['fresh_calibrated_guard_calls']>0
    assert completion['source_mode']==c.source_mode() and completion['resource_policy']==c.resource_policy()
    assert report['new_optimizer_calls']==completion['new_optimizer_calls']==report['actual_feature_reads']==report['new_pools']==0
    assert report['CORE_reread'] is completion['CORE_reread'] is report['new_configuration_selection'] is False
    assert report['replay_report_sha256']==run['input_pins'][c.REPLAY_REPORT]
    assert report['actual_prefit_sha256']==run['input_pins'][c.PREFIT] and report['saved_label_bits_sha256']==c.LABEL_BITS_SHA
    assert c.sha(c.canonical({key:report[key] for key in PROTECTED}))==report['protected_provenance_sha256']
    assert report['original_evaluation_source_manifest_sha256']==c.EVALUATION_READY_SHA
    assert completion['complete_evaluation_gzip_sha256']==report['complete_evaluation_storage']['gzip_sha256']
    for key,phase in (('runtime_acceptance','before_evaluation'),('runtime_acceptance_after_evaluation','after_evaluation')):
        proof=report[key]
        assert proof['status']==c.runtime.PROVIDER_STATUS and proof['stage']==c.STAGE and proof['provider_phase']==phase
        assert proof['current_pid']==worker_pid and proof['parent_pid']==parent_pid and proof['caller_birth_sha256']==birth_sha
        assert proof['static_root_binding_sha256']==run['input_pins'][c.STATIC_BINDING]
        assert proof['reviewed_controller_admission_sha256']==run['input_pins'][c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()]
        assert proof['stable_admitted_runtime_binding_sha256']==c.ARRAY_RUNTIME_ANCHOR_SHA
        assert proof['request_binding']['request_relative_path']==c.REQUEST and proof['request_binding']['request_sha256']==run['input_pins'][c.REQUEST]
        assert proof['fresh_current_python_and_loaded_native_origins_checked'] is True and proof['invented_only'] is False
        assert proof['actual_origin_receipt_sha256']==c.runtime.PROFILE_ORIGIN_SHA
        assert proof['software_status_sha256']==c.runtime.SOFTWARE_STATUS_SHA and proof['software_certificate_sha256']==c.runtime.PANDAS_ADMISSION_SHA
        assert proof['numerical_threads']==1 and proof['source_cache_remained_absent'] is True
    calibration=report['resource_calibration'];assert calibration['stage']==c.STAGE and calibration['execution_manifest_sha256']==generation
    assert calibration['birth_sha256']==birth_sha and calibration['current_pid']==worker_pid and calibration['parent_pid']==parent_pid
    assert calibration['authorization_sha256']==c.AUTH_SHA and calibration['scientific_protocol_settings_changed'] is False
    fresh(started);assert c.EVALUATION_DATA.stat().st_size<=results_io.MAX_GZIP
    compressed=c.EVALUATION_DATA.read_bytes();full=results_io.decode(compressed,report['complete_evaluation_storage'])
    result_contract(full);assert results_io.summary(full)==report['evaluation_summary']
    assert full['status']==completion['scientific_verdict']
    fresh(started)
    return {'status':'PASS_PARENT_COMPLETE_ORIGINAL_EVALUATION_EVIDENCE','scientific_verdict':full['status'],
        'full_original_result_preserved':True,'gate_recomputed_from_saved_fixed_summaries':True,
        'bootstrap_random_draws_not_rerun_by_parent':True,'new_optimizer_calls':0}
