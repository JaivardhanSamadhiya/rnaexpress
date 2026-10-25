"""Managed supervisor/owned toy child with durable evidence and fixed caps."""
import argparse
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from src.generalization_pum_process_probe_20261021 import headless

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/generalization_managed_job_probe_20261025'
DURATION = 360


def line(stream, value):
    stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + '\n')
    stream.flush()
    os.fsync(stream.fileno())


def reserve(snapshot):
    return (snapshot['physical_available'] >= 256 * 2**20
        and snapshot['commit_headroom'] >= 2**30 and snapshot['disk_available'] >= 2**30)


def child(parent):
    assert os.getppid() == parent
    with (OUT / 'toy_child.jsonl').open('x', encoding='utf8', newline='\n') as stream:
        faulthandler.enable(stream)
        start = time.monotonic()
        while time.monotonic() - start < DURATION:
            snapshot = headless.memory()
            assert reserve(snapshot), 'Toy diagnostic live reserve failed'
            line(stream, {'elapsed_seconds': time.monotonic()-start, 'pid': os.getpid(),
                'parent_pid': os.getppid(), 'memory': snapshot})
            time.sleep(1)
        line(stream, {'status': 'TOY_CHILD_COMPLETE', 'pid': os.getpid()})


def parent():
    before = headless.memory()
    assert before['physical_available'] >= 512*2**20
    assert before['commit_headroom'] >= 1920*2**20 and reserve(before)
    sources = {str(p.relative_to(ROOT)).replace('\\', '/'):
        hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    assert all(os.environ.get(k) == '1' for k in
        ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'))
    with (OUT / 'supervisor.jsonl').open('x', encoding='utf8', newline='\n') as stream:
        faulthandler.enable(stream)
        line(stream, {'status': 'TOY_MANAGED_PROBE_STARTED', 'parent_pid': os.getpid(),
            'duration_seconds': DURATION, 'sources': sources, 'memory': before,
            'project_payload_reads': 0, 'optimizer_calls': 0, 'scientific_attempts': 0})
        started = time.monotonic()
        owned = None
        with headless.Job() as job:
            try:
                line(stream, {'status':'EXACT_JOB_LIMITS', 'limits':job.limits()})
                command = [sys.executable, '-S', '-B', '-u', '-m',
                    'src.generalization_managed_job_probe_20261025.probe', '--child', str(os.getpid())]
                owned = job.spawn(command, str(ROOT))
                line(stream, {'status':'TOY_CHILD_ASSIGNED', 'child_pid':owned.pid})
                owned.resume()
                last = -10
                while True:
                    elapsed = time.monotonic()-started
                    snapshot = headless.memory()
                    sample = headless.process_memory(owned.process_handle)
                    accounting = job.accounting()
                    code = owned.exit_code()
                    assert reserve(snapshot), 'Toy diagnostic live reserve failed'
                    assert elapsed < DURATION+60, 'Toy diagnostic deadline'
                    assert accounting['active_processes'] <= 2
                    if elapsed-last >= 1 or code is not None:
                        line(stream, {'elapsed_seconds': elapsed, 'memory':snapshot,
                            'child_memory':sample, 'accounting':accounting, 'exit_code':code})
                        last=elapsed
                    if code is not None:
                        assert code == 0, 'Toy child exit '+str(code)
                        break
                    time.sleep(.1)
            except BaseException as error:
                line(stream, {'status':'TOY_PROBE_FAILED', 'error_type':type(error).__name__,
                    'error':str(error), 'elapsed_seconds':time.monotonic()-started})
                job.terminate()
                raise
            finally:
                if owned is not None:
                    owned.close()
        line(stream, {'status':'PASS_MANAGED_TOY_LIFETIME_ONLY', 'elapsed_seconds':time.monotonic()-started,
            'project_payload_reads':0, 'optimizer_calls':0, 'scientific_attempts':0,
            'does_not_prove_historical_termination_cause_or_full_fit_success':True})
    print('PASS_MANAGED_TOY_LIFETIME_ONLY', flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--child', type=int)
    args=parser.parse_args()
    if args.child is None:
        parent()
    else:
        child(args.child)
