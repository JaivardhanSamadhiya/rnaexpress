"""Pure supplied-byte validation of the fixed roomy FIT's closed journal.

This checks recorded provenance and closure claims. It does not establish
physical durability retrospectively or confer the old FIT owner's authority.
"""
import math
from . import common as c

PASS='PASS_FIXED63_CHECKPOINT84_UNIT_FIT_LIFECYCLE_PENDING_INDEPENDENT_REPLAY'
MAX_BYTES=8*2**20
MAX_LINE_BYTES=64*2**10
STATUS='VERIFIED_ROOMY_FIT_CLOSED_JOURNAL_BINDING_NOT_PHYSICAL_DURABILITY_PROOF'


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


def validate(raw,supervisor,report,completion,run):
    """No file access, native calls, resource probes or scientific arithmetic."""
    assert type(raw) is bytes and 0<len(raw)<=MAX_BYTES
    assert raw.endswith(b'\n') and b'\r' not in raw,'Expected complete LF-delimited journal'
    want=run['input_pins'][c.FIT_JOURNAL]
    assert c.sha(raw)==c.valid_sha(want)==supervisor['mandatory_journal_sha256']
    assert supervisor['mandatory_journal_closed_before_receipt'] is True
    assert run['fit_generation_manifest_sha256']==c.valid_sha(c.FIT_GENERATION_SHA)
    assert supervisor['status']==PASS and supervisor['failure'] is None
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
    assert assigned['worker_pid']==resumed['worker_pid']==worker
    returned,final=events[-2:]
    assert returned['worker_pid']==worker
    observed=supervisor['observed']
    assert c.canonical(returned['observed'])==c.canonical(observed)
    assert type(observed['exit_code']) is int and observed['exit_code']==0 and observed['failure'] is None
    samples=events[4:-2]
    assert type(observed['samples']) is int and observed['samples']>=len(samples)
    elapsed=-1
    for sample in samples:
        value=sample['elapsed_seconds']
        assert type(value) in (int,float) and math.isfinite(value) and value>=0 and value>=elapsed
        elapsed=value
        assert sample['pending_failure'] is None
        assert sample['exit_code'] is None or type(sample['exit_code']) is int
    assert samples[-1]['exit_code']==0
    assert final['intended_receipt_status']==PASS and final['failure'] is None
    return {'status':STATUS,'journal_sha256':want,'journal_lines':len(events),
        'fit_generation_manifest_sha256':c.FIT_GENERATION_SHA,
        'fit_run_admission_sha256':report['run_admission_sha256'],'fit_birth_sha256':report['birth_sha256'],
        'fit_parent_pid':parent,'fit_worker_pid':worker,'recorded_closed_before_receipt':True,
        'final_intended_receipt_status':PASS,'physical_durability_retroactively_established':False,
        'old_fit_owner_reused_as_current_replay_owner':False}
