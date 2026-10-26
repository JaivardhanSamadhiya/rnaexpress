"""Independent stdlib-only closed-record check, never another biological run."""
import hashlib
import json
import math
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_cdrive_forensic_execution_20261026'
OUT=ROOT/'results'/NS
GENERATION='bd005dedf3f3dd32f61e82b6b68b560571b8ce348dfa17736254c2f6b9d8d617'
ERRORS=('maximum_scaling_difference','maximum_objective_difference',
        'maximum_recorded_gradient_norm_difference','maximum_scalar_score_difference')
CAPS={'process_memory_limit':768*2**20,'job_memory_limit':896*2**20,'active_process_limit':2,'limit_flags':8968}


def digest(raw):return hashlib.sha256(raw).hexdigest()
def decode(raw):
    def unique(items):
        value={}
        for key,item in items:
            assert key not in value,'Duplicate saved JSON key';value[key]=item
        return value
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
    json.dumps(value,allow_nan=False)
    return value


def run():
    captured={}
    def read(name):
        path=ROOT/name
        assert path.resolve().is_relative_to(ROOT.resolve()) and not path.is_symlink()
        raw=path.read_bytes();captured[name]=raw;return raw
    def record(name):return decode(read('results/'+NS+'/'+name))
    manifest=record('execution_manifest.json')
    assert digest(captured['results/'+NS+'/execution_manifest.json'])==GENERATION
    assert manifest['read_only'] is True and manifest['model_fitting_authorized'] is manifest['evaluation_or_gate_authorized'] is False
    for name,want in manifest['files'].items():assert digest(read(name))==want,name
    parent=record('forensic_supervisor_receipt.json')
    assert parent['status']=='PASS_NEW_READONLY_FORENSIC_JOB_NOT_FORMAL_REPLAY_OR_GATE' and parent['failure'] is None
    report=record('forensic_report.json');complete=record('forensic_worker_completion.json')
    birth=record('forensic_attempt_birth.json');identity=record('owned_child_identity.json');owner=record('owned_child_started.json')
    hashes={name:digest(captured['results/'+NS+'/'+name]) for name in (
        'forensic_report.json','forensic_worker_completion.json','forensic_attempt_birth.json',
        'owned_child_identity.json','owned_child_started.json')}
    assert parent['validated_report_sha256']==complete['report_sha256']==hashes['forensic_report.json']
    assert parent['validated_completion_sha256']==hashes['forensic_worker_completion.json']
    for value in (parent,report,complete):
        assert value['generation_manifest_sha256']==GENERATION
        assert value['birth_sha256']==hashes['forensic_attempt_birth.json']
        assert value['owned_child_identity_sha256']==hashes['owned_child_identity.json']
        assert value['current_child_record_sha256']==hashes['owned_child_started.json']
        assert value['parent_pid']==birth['parent_pid']==identity['parent_pid']==owner['parent_pid']
        assert value['worker_pid']==owner['worker_pid']
        assert value['new_optimizer_calls']==0
        assert value['original_formal_replay_still_ineligible'] is True
        assert value['outer_performance_computed_or_published'] is value['evaluation_or_gate_run'] is False
    assert birth['status']=='NEW_EXCLUSIVE_READONLY_FORENSIC_ATTEMPT_NOT_FIT_RETRY' and birth['automatic_retry'] is False
    assert birth['model_fitting_authorized'] is False
    pinned_map=json.dumps(manifest['readonly_input_pins'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    assert birth['input_pin_map_sha256']==digest(pinned_map)
    for value in (identity,owner):
        assert value['generation_manifest_sha256']==GENERATION
        assert value['birth_sha256']==hashes['forensic_attempt_birth.json']
    assert owner['owned_child_identity_sha256']==hashes['owned_child_identity.json']
    assert identity['prospective_job_limits']==owner['job_limits']==CAPS
    assert owner['exact_parent_owned_Job_membership_checked_before_resume'] is True
    assert identity['resident_request']==owner['resident_cap']['after']['maximum']==190*2**20
    assert report['status']=='ACTUAL_SEPARATE_READONLY63_FORENSICS_NOT_ACCEPTED_CAMPAIGN'
    assert complete['status']=='PASS_NEW_FORENSIC_WORKER_NOT_OLD_CAMPAIGN_CLOSURE'
    assert report['biological_inputs_read'] is complete['biological_inputs_read'] is True
    assert report['biological_rows_read']==complete['biological_rows_read']==13781
    assert report['read_only_input_pins']==manifest['readonly_input_pins']
    diagnostics=report['forensic_numeric_diagnostics']
    assert diagnostics['status']=='PASS_FORENSIC_SAVED63_NUMERIC_CONSISTENCY_NOT_CLOSED_CAMPAIGN'
    assert diagnostics['verified_checkpoints']==63 and diagnostics['verified_inner_checkpoints']==54 and diagnostics['verified_outer_checkpoints']==9
    assert diagnostics['recorded_optimizer_units_not_refitted']==84 and diagnostics['source_only_reselections_equal']==9
    assert len(diagnostics['source_selection_declaration_sha256'])==9
    assert diagnostics['old_campaign_completion_missing'] is diagnostics['old_supervisor_completion_missing'] is diagnostics['original_formal_replay_still_ineligible'] is True
    assert diagnostics['outer_performance_computed_or_published'] is diagnostics['evaluation_or_gate_run'] is diagnostics['biological_or_generalization_claim'] is False
    results=diagnostics['checkpoint_numeric_diagnostics'];assert len(results)==63
    assert set(results)==set(report['checkpoint_current_runtime_proof_sha256'])
    assert sum(value['recorded_optimizer_units_not_refitted'] for value in results.values())==84
    for key,value in results.items():
        assert value['status']=='PASS_READONLY_SAVED_CHECKPOINT_NUMERIC_CONSISTENCY_NOT_CAMPAIGN'
        assert value['exact_canonical_scores_equal'] is True and value['new_optimizer_calls']==0
        assert value['outer_performance_computed'] is value['old_campaign_closure_or_current_owner_certified'] is False
        assert value['tolerance_strictly_below']==1e-9
        for field in ERRORS:assert math.isfinite(value[field]) and 0<=value[field]<1e-9
        raw=read('results/'+NS+'/runtime_'+key+'.json')
        assert digest(raw)==report['checkpoint_current_runtime_proof_sha256'][key]
        proof=decode(raw)
        assert proof['checkpoint_key']==key and proof['optimizer_calls']==0
        assert proof['current_pid']==owner['worker_pid'] and proof['parent_pid']==owner['parent_pid']
        assert proof['current_child_record_sha256']==hashes['owned_child_started.json']
        assert proof['owned_child_identity_sha256']==hashes['owned_child_identity.json']
        assert proof['birth_sha256']==hashes['forensic_attempt_birth.json'] and proof['generation_manifest_sha256']==GENERATION
        assert proof['in_owned_job_now'] is True and proof['actual_old_campaign_owner_claimed'] is False
        assert proof['native_origins']['old_exact_runtime_identity_passes'] is False
    for proof in (report['runtime_before_inputs'],report['runtime_after_forensics']):
        assert proof['current_pid']==owner['worker_pid'] and proof['parent_pid']==owner['parent_pid']
        assert proof['current_child_record_sha256']==hashes['owned_child_started.json']
        assert proof['birth_sha256']==hashes['forensic_attempt_birth.json'] and proof['generation_manifest_sha256']==GENERATION
        assert proof['in_owned_job_now'] is True and proof['actual_old_campaign_owner_claimed'] is False
        assert proof['native_origins']['old_exact_runtime_identity_passes'] is False
    for field in ERRORS:assert diagnostics['maximum_arithmetic_differences'][field]==max(value[field] for value in results.values())
    declared=report['saved_declarations']
    assert declared['status']=='PASS190_SAVED_DECLARATIONS_NOT_CAMPAIGN_OR_CURRENT_OWNER'
    assert declared['saved_checkpoints']==63 and declared['recorded_completed_optimizer_units']==84
    assert declared['current_owner_or_runtime_admission_granted'] is False and declared['old_campaign_complete_missing'] is True
    assert len(declared['saved_filename_sha256'])==190
    prefix='results/generalization_knowncell_fit_paged_execution_20261025/campaign/checkpoints/'
    assert {prefix+name:want for name,want in declared['saved_filename_sha256'].items()}=={
        name:want for name,want in manifest['readonly_input_pins'].items() if name.startswith(prefix)}
    missing={prefix+'campaign_complete.json'} | {
        'results/generalization_knowncell_fit_paged_execution_20261025/'+name
        for name in ('fit_lifecycle_report.json','fit_worker_completion.json','fit_supervisor_receipt.json')}
    assert set(report['old_missing_terminal_paths'])==missing
    for name in missing:assert not os.path.lexists(ROOT/name)
    raw=read('results/'+NS+'/parent.jsonl');assert raw.endswith(b'\n') and digest(raw)==parent['closed_journal_sha256']
    journal=[decode(line) for line in raw.splitlines()]
    assert journal[-1]=={'status':'MANDATORY_PARENT_TELEMETRY_COMPLETE','failure':None}
    assert journal[-2]['status']=='FINAL_LIFETIME_COUNTERS' and journal[-2]['job']['active_processes']==0
    samples=[value for value in journal if value['status']=='OWNED_READONLY_SAMPLE']
    assert len(samples)>0 and samples[-1]['exit_code']==0
    assert [v['elapsed_seconds'] for v in samples]==sorted(v['elapsed_seconds'] for v in samples)
    for value in samples:
        assert value['failure'] is None and value['elapsed_seconds']<=1800
        assert value['process']['peak_private_commit']<=768*2**20
        assert value['process']['working_set']<=value['process']['peak_working_set']<=192*2**20
        assert value['job']['peak_job_memory_used']<=896*2**20 and value['job']['active_processes']<=2
        assert value['memory']['physical_available']>=256*2**20
        assert min(value['memory']['commit_headroom'],value['memory']['disk_available'])>=2**30
    assert parent['elapsed_seconds']<=1800 and parent['minimum_sampled_physical_available']>=256*2**20
    assert parent['peak_private_commit']<=768*2**20 and parent['peak_working_set']<=192*2**20
    assert parent['minimum_sampled_physical_available']<=min(v['memory']['physical_available'] for v in samples)
    assert parent['final_memory']['physical_available']>=256*2**20
    assert min(parent['final_memory']['commit_headroom'],parent['final_memory']['disk_available'])>=2**30
    for name,raw in captured.items():assert (ROOT/name).read_bytes()==raw,name
    result={'status':'VERIFIED_SEPARATE_READONLY63_ARITHMETIC_NOT_FORMAL_REPLAY_OR_GATE',
        'verified_files_sha256':{name:digest(raw) for name,raw in captured.items()},
        'verifier_sha256':digest(Path(__file__).read_bytes()),'generation_manifest_sha256':GENERATION,
        'verified_checkpoints':63,'recorded_optimizer_units_not_refitted':84,'source_only_reselections_equal':9,
        'maximum_arithmetic_differences':diagnostics['maximum_arithmetic_differences'],
        'elapsed_seconds':parent['elapsed_seconds'],'peak_private_commit':parent['peak_private_commit'],
        'peak_working_set':parent['peak_working_set'],'persisted_samples_verified':len(samples),
        'original_formal_replay_still_ineligible':True,'biological_or_generalization_claim':False,
        'new_native_jobs':0,'original_biological_payloads_reopened_here':False,
        'saved_runtime_proofs_checked_not_new_current_runtime_admission':True}
    with (OUT/'independent_saved_verification.json').open('xb') as stream:
        stream.write((json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n').encode());stream.flush();os.fsync(stream.fileno())
    print(result['status'],digest((OUT/'independent_saved_verification.json').read_bytes()),parent['elapsed_seconds'])


if __name__=='__main__':run()
