"""Parent acceptance binds real current owner and exact closed-stage outputs."""
import math
from . import common as c


def terminal(stage,report,complete,run,generation,run_sha,birth_sha,identity_sha,owner_sha,parent_pid,child_pid,*,fresh):
    for value in (report,complete):
        assert value['stage']==stage.name and value['source_manifest_sha256']==generation
        assert value['run_admission_sha256']==run_sha and value['birth_sha256']==birth_sha
        assert value['owned_child_identity_sha256']==identity_sha and value['current_child_record_sha256']==owner_sha
        assert value['parent_pid']==parent_pid and value['worker_pid']==child_pid
        assert value['old_or_forensic_stage_authority_reused'] is False and value['actual_in_owned_job_now'] is True
        assert value['new_optimizer_calls']==0
        assert value['evaluation_or_gate_run']==(stage.name=='evaluate')
    assert report['status']=='ACTUAL_CURRENT_READONLY_VERIFICATION_WORKER_RESULT'
    assert complete['status']=='CURRENT_READONLY_WORKER_CLOSED'
    assert complete['report_sha256']==c.digest(c.canonical(report)+b'\n')
    assert report['read_only_authority_sha256']==run['read_only_authority_sha256']
    assert report['biological_inputs_read'] is True and report['biological_rows_read']==13781
    assert report['old_missing_paths']==c.old_absences() and report['old_missing_completion_synthesized'] is False
    for proof in (report['runtime_before_inputs'],report['runtime_after_work']):
        assert proof['worker_pid']==child_pid and proof['parent_pid']==parent_pid
        assert proof['birth_sha256']==birth_sha and proof['current_child_record_sha256']==owner_sha
        assert proof['actual_in_owned_job_now'] is True and proof['optimizer_callable_exposed'] is False
        assert proof['actual_current_native_origins']['old_exact_runtime_identity_passes'] is False
    value=report['result']
    if stage.name=='replay':
        assert value['status']=='PASS_CURRENT_CLOSED63_ARITHMETIC_AND_SOURCE_RESELECTION'
        assert value['verified_checkpoints']==63 and value['recorded_optimizer_units_not_refitted']==84
        assert len(value['canonical_outer_records'])==len(value['source_only_outer_reselections'])==9
        assert len(value['checkpoint_numeric_diagnostics'])==len(report['checkpoint_current_runtime_proof_sha256'])==63
        assert value['prefit_sha256']==run['current_prefit_sha256']
        assert value['campaign_complete_sha256']==run['checkpoint_pins']['campaign_complete.json']
        for row in value['checkpoint_numeric_diagnostics'].values():
            assert row['exact_canonical_scores_equal'] is True and row['new_optimizer_calls']==0
            for key in ('maximum_scaling_difference','maximum_objective_difference','maximum_recorded_gradient_norm_difference','maximum_scalar_score_difference'):
                assert math.isfinite(row[key]) and 0<=row[key]<1e-9
        for key,want in report['checkpoint_current_runtime_proof_sha256'].items():
            fresh();assert c.sha(stage.path('runtime_'+key+'.json'))==want
    else:
        from src.generalization_knowncell_joint_gate_20261023 import gate
        assert value['status'] in ('NO-GO','JOINT_KNOWN_CELL_DEVELOPMENT_GO')
        assert value['model_fits_or_refits']==0 and value['novelty_certified'] is False
        expected=gate.thresholds(value['primary_summaries']['joint_shrink10'],value['comparisons'],value['bootstrap']['intervals'])
        assert value['gate']==expected and value['status']==expected['status']
        assert value['coverage']['rows_per_arm']==13781 and value['bootstrap']['draws']==5000 and len(value['bootstrap']['components'])==187
    return {'verified_stage':stage.name,'result_status':value['status'],'model_fits_or_refits':0}
