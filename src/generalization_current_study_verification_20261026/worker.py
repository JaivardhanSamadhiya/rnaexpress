"""Independent new-process read-only replay or fixed evaluation, no fitting."""
import argparse
import faulthandler
import os
from pathlib import Path
import sys
if __name__=='__main__':
    cache=Path(__file__).resolve().parents[2]/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
    if sys.flags.optimize or sys.flags.no_site!=1 or not sys.dont_write_bytecode or sys.pycache_prefix!=str(cache) or os.path.lexists(cache):raise RuntimeError('Require fixed source-only flags')
from . import common as c
from .owned import Owner,Runtime


def analyze(owner,manifest,run):
    from src.generalization_current_study_execution_v2_20261026 import inputs
    from src.generalization_cdrive_forensic_execution_20261026 import pools
    from src.generalization_current_fixed_fit_core_20261026 import plan as plans
    from src.generalization_current_verification_core_20261026 import replay,evaluation
    from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
    runtime=Runtime(owner,manifest)
    inp=inputs.load(runtime.np,fresh=owner.fresh)
    plan=inputs.new_plan(run,inp,fresh=owner.fresh)
    if owner.stage.name=='replay':
        original=pools.build_pools(runtime.np,runtime.pd,inp,fresh=owner.fresh)
        prepared=plans.rebind_prepared(plan,original)
        prefix=(c.PRODUCER/'fit/campaign/checkpoints').relative_to(c.ROOT).as_posix()+'/'
        def read(name):return c.read_exact(prefix+name,run['checkpoint_pins'][name],fresh=owner.fresh,maximum=16*2**20)
        birth,complete=read('campaign_birth.json'),read('campaign_complete.json');records=[]
        for task in lc.task_roster():
            key=lc.task_key(task)
            records.append({'task_key':key,'birth_raw':read(key+'.birth.json'),
                'checkpoint_raw':read(key+'.model.json'),'completion_raw':read(key+'.complete.json')})
        def before(key,task):
            owner.fresh();c.sources(owner.generation);runtime.proof(key);return True
        result=replay.replay(runtime.np,prepared,plan,birth,records,complete,
            fresh=owner.fresh,before_checkpoint=before)
        assert len(runtime.proofs)==63
    else:
        name=c.Stage('replay').path('worker_report.json').relative_to(c.ROOT).as_posix()
        report=c.decode(c.read_exact(name,run['replay_report_sha256'],fresh=owner.fresh,maximum=32*2**20))
        previous=report['result']
        assert previous['status']=='PASS_CURRENT_CLOSED63_ARITHMETIC_AND_SOURCE_RESELECTION'
        assert previous['prefit_sha256']==plan.prefit_sha256 and previous['verified_checkpoints']==63
        result=evaluation.evaluate(runtime.np,inp.metadata,inp.effects,previous['canonical_outer_records'],fresh=owner.fresh)
    after=runtime.proof()
    for name,want in run['input_pins'].items():c.read_exact(name,want,fresh=owner.fresh)
    for name,want in run['checkpoint_pins'].items():
        c.read_exact((c.PRODUCER/'fit/campaign/checkpoints'/name).relative_to(c.ROOT).as_posix(),want,fresh=owner.fresh,maximum=16*2**20)
    c.sources(owner.generation);owner.fresh();c.old_absences()
    return {**owner.descriptor(),'status':'ACTUAL_CURRENT_READONLY_VERIFICATION_WORKER_RESULT',
        'read_only_authority_sha256':run['read_only_authority_sha256'],
        'biological_inputs_read':True,'biological_rows_read':13781,'new_optimizer_calls':0,
        'evaluation_or_gate_run':owner.stage.name=='evaluate','result':result,
        'runtime_before_inputs':runtime.before,'runtime_after_work':after,
        'checkpoint_current_runtime_proof_sha256':dict(runtime.proofs),
        'old_missing_paths':c.old_absences(),'old_missing_completion_synthesized':False,
        'independent_confirmation':False,'unknown_cell_generalization':False,'novelty_certified':False}


def run(stage,generation,run_sha,birth_sha,identity_sha,parent_pid,started):
    manifest=c.sources(generation);raw,admitted=c.admission(stage,generation);assert c.digest(raw)==run_sha
    owner=Owner(stage,generation,run_sha,birth_sha,identity_sha,parent_pid,started)
    report=analyze(owner,manifest,admitted);report_sha=c.save_new(stage.path('worker_report.json'),report)
    c.sources(generation);owner.fresh()
    c.save_new(stage.path('worker_completion.json'),{**owner.descriptor(),
        'status':'CURRENT_READONLY_WORKER_CLOSED','report_sha256':report_sha,
        'new_optimizer_calls':0,'evaluation_or_gate_run':stage.name=='evaluate'})
    owner.closed=True


if __name__=='__main__':
    c.source_mode();parser=argparse.ArgumentParser();parser.add_argument('stage',choices=c.STAGES)
    for name in ('generation','run_sha','birth_sha','identity_sha'):parser.add_argument(name)
    parser.add_argument('parent_pid',type=int);parser.add_argument('started',type=float);args=parser.parse_args()
    stage=c.Stage(args.stage)
    with stage.path('worker_fault.log').open('x',encoding='utf8',buffering=1) as log:
        sys.stdout=sys.stderr=log;faulthandler.enable(log)
        try:run(stage,args.generation,args.run_sha,args.birth_sha,args.identity_sha,args.parent_pid,args.started)
        except BaseException:
            import traceback
            traceback.print_exc();log.flush();os.fsync(log.fileno());raise
        finally:faulthandler.disable()
