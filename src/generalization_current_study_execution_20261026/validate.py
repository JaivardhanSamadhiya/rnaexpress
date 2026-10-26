"""Parent-side saved-current-stage semantic checks, no fitting or gate."""
from . import common as c


def terminal(stage,report,complete,run,generation,run_sha,birth_sha,identity_sha,owner_sha,parent_pid,child_pid,*,fresh):
    for value in (report,complete):
        assert value['stage']==stage.name and value['source_manifest_sha256']==generation
        assert value['run_admission_sha256']==run_sha and value['birth_sha256']==birth_sha
        assert value['owned_child_identity_sha256']==identity_sha and value['current_child_record_sha256']==owner_sha
        assert value['parent_pid']==parent_pid and value['worker_pid']==child_pid
        assert value['old_or_forensic_stage_authority_reused'] is False and value['actual_in_owned_job_now'] is True
        assert value['evaluation_or_gate_run'] is False
    assert report['status']=='ACTUAL_NEW_CURRENT_STUDY_STAGE_COMPLETE_NOT_REPLAY_OR_GATE'
    assert complete['status']=='NEW_CURRENT_STUDY_WORKER_CLOSED_NOT_REPLAY_OR_GATE'
    assert complete['report_sha256']==c.digest(c.canonical(report)+b'\n')
    assert report['new_manual_authorization_sha256']==run['new_manual_authorization_sha256']
    assert report['biological_inputs_read'] is True and report['biological_rows_read']==13781
    assert report['all_nine_scientific_pool_bindings_equal'] is True
    assert report['outer_performance_computed_or_published'] is report['old_missing_completion_synthesized'] is False
    assert report['current_fit_is_not_old_attempt_resume'] is True
    assert report['old_missing_paths']==c.old_absences()
    for proof in (report['runtime_before_inputs'],report['runtime_after_work']):
        assert proof['worker_pid']==child_pid and proof['parent_pid']==parent_pid
        assert proof['source_manifest_sha256']==generation and proof['birth_sha256']==birth_sha
        assert proof['current_child_record_sha256']==owner_sha
        assert proof['actual_in_owned_job_now'] is True and proof['old_or_forensic_stage_authority_reused'] is False
        assert proof['actual_current_native_origins']['old_exact_runtime_identity_passes'] is False
    from src.generalization_current_execution_context_20261025.plan import from_supplied
    from src.generalization_current_execution_context_20261025 import contracts as hc
    from src.generalization_cdrive_forensic_execution_20261026 import inputs as historical
    prefit_raw=c.read_exact(historical.spec.HISTORICAL_PREFIT,historical.spec.HISTORICAL_PREFIT_SHA,fresh=fresh)
    projection_raw=c.read_exact(historical.spec.HISTORICAL_PROJECTION,historical.spec.HISTORICAL_PROJECTION_SHA,fresh=fresh)
    old_plan=from_supplied(prefit_raw,projection_raw,hc.canonical(historical.historical_reference()))
    if stage.name=='prefit':
        assert report['optimizer_units_executed']==report['checkpoints_fitted']==0
        assert report['campaign_lifecycle'] is None and report['checkpoint_current_runtime_proof_sha256']=={}
        raw=stage.path('current_prefit.json').read_bytes();assert c.digest(raw)==report['current_prefit_sha256']
        document=c.decode(raw);assert document['resource_exception_applies'] is True
        provenance=report['prefit_creator_provenance']
        for key in ('stage','parent_pid','worker_pid','source_manifest_sha256','run_admission_sha256',
                    'birth_sha256','owned_child_identity_sha256','current_child_record_sha256',
                    'actual_in_owned_job_now','old_or_forensic_stage_authority_reused'):
            assert provenance[key]==report[key]
        assert provenance['new_manual_authorization_sha256']==run['new_manual_authorization_sha256']
        assert provenance['runtime_before_inputs_sha256']==c.digest(c.canonical(report['runtime_before_inputs']))
        assert provenance['runtime_after_pools_sha256']==c.digest(c.canonical(report['runtime_after_work']))
        assert provenance['original_input_pins']==run['input_pins']
        from src.generalization_current_fixed_fit_core_20261026.plan import make_current_prefit
        assert document==make_current_prefit(old_plan,provenance)
        return {'current_prefit_sha256':c.digest(raw),'saved_checkpoint_files_sha256':{}}
    from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
    from src.generalization_knowncell_fit_paged_execution_20261025.terminal import ReadOnlySavedCampaign
    from . import inputs
    # Supplied historical plan only; no parser, array or library is needed here.
    class Input:
        historical_plan=old_plan
    plan=inputs.new_plan(run,Input(),fresh=fresh)
    assert report['current_prefit_sha256']==plan.prefit_sha256
    directory=stage.path('campaign')/'checkpoints'
    tasks={lc.task_key(task):task for task in lc.task_roster()}
    expected={'campaign_birth.json','campaign_complete.json'}|{key+suffix for key in tasks for suffix in ('.birth.json','.model.json','.complete.json')}
    assert {path.name for path in directory.iterdir()}==expected and len(expected)==191
    pins={}
    for name in sorted(expected):
        fresh();path=directory/name;assert path.is_file() and not path.is_symlink() and path.stat().st_size<=16*2**20
        pins[name]=c.sha(path)
    birth=c.decode((directory/'campaign_birth.json').read_bytes())
    assert birth=={'status':'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS',**plan.identity()}
    checker=ReadOnlySavedCampaign(directory,plan,pins['campaign_birth.json'])
    units=0
    for key in tasks:
        fresh();units+=checker.check_saved(key)['optimizer_units'];fresh()
    assert units==84
    lifecycle=c.decode((directory/'campaign_complete.json').read_bytes())
    assert lifecycle==report['campaign_lifecycle']
    assert lifecycle['status']=='COMPLETE63_CHECKPOINT84_UNIT_LIFECYCLE_NOT_SCIENTIFIC_REPLAY_OR_GATE'
    assert lifecycle['checkpoint_count']==report['checkpoints_fitted']==63
    assert lifecycle['optimizer_units']==report['optimizer_units_executed']==84
    assert lifecycle['campaign_birth_sha256']==pins['campaign_birth.json']
    assert lifecycle['checkpoint_receipt_sha256']=={key:pins[key+'.complete.json'] for key in tasks}
    for key,want in plan.identity().items():assert lifecycle[key]==want
    assert set(report['checkpoint_current_runtime_proof_sha256'])==set(tasks)
    for key,want in report['checkpoint_current_runtime_proof_sha256'].items():assert c.sha(stage.path('runtime_'+key+'.json'))==want
    for name,want in pins.items():fresh();assert c.sha(directory/name)==want
    return {'current_prefit_sha256':plan.prefit_sha256,'saved_checkpoint_files_sha256':pins}
