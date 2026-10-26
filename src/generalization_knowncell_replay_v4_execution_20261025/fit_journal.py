"""Independent supplied-byte validation of the paged FIT's closed journal.

This checks recorded provenance and closure claims. It does not establish
physical durability retrospectively or confer the old FIT owner's authority.
"""
import math
from . import common as c

PASS='PASS_FIXED63_CHECKPOINT84_UNIT_FIT_LIFECYCLE_PENDING_INDEPENDENT_REPLAY'
MAX_BYTES=8*2**20
MAX_LINE_BYTES=64*2**10
STATUS='VERIFIED_PAGED_FIT_JOURNAL_RESOURCES_AND_CLOSURE_NOT_PHYSICAL_DURABILITY_PROOF'


def _finite(value):
    if type(value) is float:assert math.isfinite(value),'Nonfinite journal number'
    elif isinstance(value,dict):
        for item in value.values():_finite(item)
    elif isinstance(value,list):
        for item in value:_finite(item)


def decode_input_objects(raw):
    """Keep the mandatory raw JSONL input out of object-JSON decoding."""
    assert c.FIT_JOURNAL in raw
    return {name:c.decode(value) for name,value in raw.items() if name!=c.FIT_JOURNAL}


def _elapsed(value):
    assert type(value) in (int,float) and math.isfinite(value) and 0<=value<=1800,'Fixed total FIT deadline'
    return value


def _memory(value,*,startup=False):
    for name,floor in (('physical_available',c.FIT_STARTUP_PHYSICAL if startup else 256*2**20),
            ('commit_headroom',1920*2**20 if startup else 2**30),('disk_available',2**30)):
        assert type(value[name]) is int and value[name]>=floor,'Saved FIT resource reserve: '+name


def _process(value):
    for name,ceiling in (('working_set',192*2**20),('peak_working_set',192*2**20),
            ('private_commit',c.PROCESS_CAP),('peak_private_commit',c.PROCESS_CAP)):
        assert type(value[name]) is int and 0<=value[name]<=ceiling,'Saved FIT process counter: '+name
    assert value['working_set']<=value['peak_working_set'] and value['private_commit']<=value['peak_private_commit']


def _job(value):
    for name,ceiling in (('active_processes',2),('peak_process_memory_used',c.PROCESS_CAP),('peak_job_memory_used',c.JOB_CAP)):
        assert type(value[name]) is int and 0<=value[name]<=ceiling,'Saved FIT job counter: '+name


def _installed(value):
    assert set(value)=={'before','after','only_suspended_owned_child_changed','private_and_job_caps_or_live_guards_changed'}
    assert value['only_suspended_owned_child_changed'] is True and value['private_and_job_caps_or_live_guards_changed'] is False
    before,after=value['before'],value['after']
    assert set(before)==set(after)=={'minimum','maximum','flags'}
    assert all(type(x) is int and x>=0 for item in (before,after) for x in item.values())
    assert 0<before['minimum']<=190*2**20
    assert before['flags']&~15==0 and (before['flags']&3) in (0,1,2)
    assert after=={'minimum':before['minimum'],'maximum':190*2**20,'flags':(before['flags']&3)|4}


def validate(raw,supervisor,report,completion,run):
    """No file access, native calls, resource probes or scientific arithmetic."""
    assert type(raw) is bytes and 0<len(raw)<=MAX_BYTES
    assert raw.endswith(b'\n') and b'\r' not in raw,'Expected complete LF-delimited journal'
    want=run['input_pins'][c.FIT_JOURNAL]
    assert c.sha(raw)==c.valid_sha(want)==supervisor['mandatory_journal_sha256']
    assert supervisor['mandatory_journal_closed_before_receipt'] is True
    assert run['fit_generation_manifest_sha256']==c.valid_sha(c.FIT_GENERATION_SHA)
    assert supervisor['status']==PASS and supervisor['failure'] is None
    assert supervisor['resource_policy']==c.resource_policy()
    assert supervisor['owned_resident_policy']==c.FIT_RESIDENT_POLICY
    assert supervisor['worker_started'] is True and supervisor['automatic_retry'] is False
    assert supervisor['checkpoints']==63 and supervisor['optimizer_units']==84
    _memory(supervisor['memory_before'],startup=True);_memory(supervisor['memory_after'])
    duration=_elapsed(supervisor['elapsed_seconds'])
    assert report['status']=='ACTUAL_ONE_OWNED_FIXED_FIT_LIFECYCLE_NOT_REPLAY_OR_EVALUATION'
    assert completion['status']=='PASS_FIXED_FIT_WORKER_CALLBACKS_RESTORED_LIFECYCLE_ONLY'
    for key in ('generation_manifest_sha256','run_admission_sha256','birth_sha256'):
        assert report[key]==completion[key]==supervisor[key]
        c.valid_sha(report[key])
    assert report['generation_manifest_sha256']==c.FIT_GENERATION_SHA
    parent,worker=report['parent_pid'],report['worker_pid']
    assert type(parent) is int and type(worker) is int and parent>0 and worker>0 and parent!=worker
    assert completion['parent_pid']==parent and completion['worker_pid']==worker
    lines=raw.split(b'\n')[:-1]
    assert all(0<len(line)+1<=MAX_LINE_BYTES for line in lines)
    events=[]
    for line in lines:
        assert line,'Empty journal line'
        event=c.decode(line)
        assert type(event) is dict and type(event.get('status')) is str
        _finite(event)
        clock=event['monotonic']
        assert type(clock) in (int,float) and math.isfinite(clock) and clock>=0
        if events:assert clock>=events[-1]['monotonic'],'Journal clock/order changed'
        events.append(event)
    statuses=[event['status'] for event in events]
    first=['MANAGED_SUPERVISOR_ENTERED','FIT_BIRTH_DURABLE','OWNED_CHILD_ASSIGNED','OWNED_CHILD_RESUMED']
    last=['OWNED_CHILD_MONITOR_RETURNED','SUPERVISOR_READY_FOR_FINAL_COMMIT']
    assert len(events)>=7 and statuses[:4]==first and statuses[-2:]==last
    assert all(status=='OWNED_WORKER_SAMPLE' for status in statuses[4:-2])
    entered,birth,assigned,resumed=events[:4]
    assert entered['parent_pid']==birth['parent_pid']==parent and entered['root_start'] is True
    assert birth['generation_manifest_sha256']==c.FIT_GENERATION_SHA
    assert birth['run_admission_sha256']==report['run_admission_sha256']
    assert birth['birth_sha256']==report['birth_sha256']
    _memory(birth['memory'],startup=True)
    assert c.canonical(birth['memory'])==c.canonical(supervisor['memory_before'])
    assert assigned['worker_pid']==resumed['worker_pid']==worker
    assert assigned['limits']=={'process_memory_limit':c.PROCESS_CAP,'job_memory_limit':c.JOB_CAP,
        'active_process_limit':2,'limit_flags':c.FIT_JOB_FLAGS}
    cap=assigned['owned_resident_cap'];_installed(cap)
    assert cap==supervisor['owned_resident_cap']
    returned,final=events[-2:]
    assert returned['worker_pid']==worker
    observed=supervisor['observed']
    assert c.canonical(returned['observed'])==c.canonical(observed)
    assert type(observed['exit_code']) is int and observed['exit_code']==0 and observed['failure'] is None
    assert observed['owned_working_set_cap']==cap and observed['measured_resident_ceiling']==192*2**20
    assert observed['final_lifetime_resident_counters_checked'] is True
    _memory(observed['final_memory_sample']);_elapsed(observed['elapsed_seconds'])
    assert observed['elapsed_seconds']<=duration
    _process(observed['last_process_handle_sample']);_process(observed['final_process_handle_peak_sample'])
    _job(observed['job_accounting'])
    assert 0<observed['peak_working_set']<=192*2**20 and 0<observed['peak_private_commit']<=c.PROCESS_CAP
    for key,floor in (('minimum_sampled_physical_available',256*2**20),('minimum_sampled_commit_headroom',2**30)):
        assert type(observed[key]) is int and observed[key]>=floor
    samples=events[4:-2]
    assert type(observed['samples']) is int and observed['samples']>=len(samples)
    elapsed=-1
    for index,sample in enumerate(samples):
        value=_elapsed(sample['elapsed_seconds'])
        assert value>=elapsed and value<=observed['elapsed_seconds']
        elapsed=value
        assert sample['pending_failure'] is None
        if index<len(samples)-1:assert sample['exit_code'] is None,'Only final saved sample can carry an exit code'
        else:assert type(sample['exit_code']) is int and sample['exit_code']==0
        _memory(sample['system_memory']);_process(sample['child_memory']);_job(sample['job_accounting'])
    assert observed['resident_configuration_checks']==observed['samples']-1
    assert type(observed['resident_configuration_checks']) is int and observed['resident_configuration_checks']>=0
    assert c.canonical(observed['last_process_handle_sample'])==c.canonical(samples[-1]['child_memory'])
    for peak in ('peak_working_set','peak_private_commit'):
        assert observed[peak]>=max([sample['child_memory'][peak] for sample in samples]+[observed['final_process_handle_peak_sample'][peak]])
    assert final['intended_receipt_status']==PASS and final['failure'] is None
    assert events[-1]['monotonic']-events[0]['monotonic']<=duration
    return {'status':STATUS,'journal_sha256':want,'journal_lines':len(events),
        'fit_generation_manifest_sha256':c.FIT_GENERATION_SHA,
        'fit_run_admission_sha256':report['run_admission_sha256'],'fit_birth_sha256':report['birth_sha256'],
        'fit_parent_pid':parent,'fit_worker_pid':worker,'recorded_closed_before_receipt':True,
        'final_intended_receipt_status':PASS,'physical_durability_retroactively_established':False,
        'old_fit_owner_reused_as_current_replay_owner':False,'saved_resource_predicates_independently_checked':True,
        'all_saved_current_lifetime_resident_private_and_job_bounds_checked':True,
        'installed_resident_policy_and_readback_checked':True,'only_last_sample_has_zero_exit':True}
