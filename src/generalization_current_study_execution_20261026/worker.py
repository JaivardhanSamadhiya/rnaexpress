"""New actual prefit/FIT stages, gated by separate current human authority."""
import argparse
import faulthandler
import os
import sys
from pathlib import Path
if __name__=='__main__':
    _cache=Path(__file__).resolve().parents[2]/'results/generalization_knowncell_runtime_provider_20261023/source_cache_must_remain_absent'
    if sys.flags.optimize or sys.flags.no_site!=1 or not sys.dont_write_bytecode or sys.pycache_prefix!=str(_cache) or os.path.lexists(_cache):
        raise RuntimeError('Require nonoptimized source-only Python and the absent fixed cache prefix')
from . import common as c
from .owned import Owner,Runtime


def analyze(owner,manifest,run):
    from . import inputs
    from src.generalization_cdrive_forensic_execution_20261026 import pools
    from src.generalization_current_fixed_fit_core_20261026 import plan as current
    from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
    from src.generalization_knowncell_joint_engine_20261023 import adapter
    runtime=Runtime(owner,manifest)
    inp=inputs.load(runtime.np,fresh=owner.fresh)
    original=pools.build_pools(runtime.np,runtime.pd,inp,fresh=owner.fresh)
    current_prefit_sha=campaign_result=None
    optimizer_units=checkpoints=0
    if owner.stage.name=='prefit':
        after=runtime.proof()
        provenance={**owner.descriptor(),
            'status':'ACTUAL_NEW_CURRENT_PREFIT_CREATOR_NOT_OLD_PREFIT_OR_FIT',
            'new_manual_authorization_sha256':run['new_manual_authorization_sha256'],
            'runtime_before_inputs_sha256':c.digest(c.canonical(runtime.before)),
            'runtime_after_pools_sha256':c.digest(c.canonical(after)),
            'original_input_pins':dict(run['input_pins']),
            'all_nine_scientific_pool_bindings_equal':True,
            'models_fitted':0,'resource_exception_applies':True,
            'resource_policy':{'job_limits':c.CAPS,'resident_request':c.RESIDENT,
                'resident_measured_ceiling':c.CEILING,'startup_physical':512*2**20,
                'startup_commit':1920*2**20,'live_physical':256*2**20,
                'live_commit_and_disk':2**30,'total_seconds':1800,'numerical_threads':1}}
        document=current.make_current_prefit(inp.historical_plan,provenance)
        current_prefit_sha=c.save_new(owner.stage.path('current_prefit.json'),document)
        assert document['resource_exception_applies'] is True
    else:
        from src.generalization_current_fixed_fit_core_20261026.driver import run_fixed_campaign
        plan=inputs.new_plan(run,inp,fresh=owner.fresh)
        prepared=current.rebind_prepared(plan,original)
        def integrity(*,task_key,task,plan,prepared,campaign):
            owner.fresh();c.sources(owner.generation)
            pool=prepared.pools[lc.pool_key(task['outer_fold'],task['inner_fold'])]
            assert adapter.pool_binding(runtime.np,pool)==pool['binding']==plan.pool(task)
            runtime.proof(task_key);owner.fresh()
            return True
        campaign_result=run_fixed_campaign(runtime.np,runtime.minimize,runtime.expit,prepared,plan,
            fresh=owner.fresh,before_checkpoint_integrity=integrity,directory=owner.stage.path('campaign'))
        expected={lc.task_key(task) for task in lc.task_roster()}
        assert set(runtime.proofs)==expected and len(expected)==63
        assert campaign_result['checkpoint_count']==63 and campaign_result['optimizer_units']==84
        checkpoints,optimizer_units=63,84
        current_prefit_sha=plan.prefit_sha256
        after=runtime.proof()
    for name,want in run['input_pins'].items():c.read_exact(name,want,fresh=owner.fresh)
    c.sources(owner.generation);c.old_absences();owner.fresh()
    return {**owner.descriptor(),'status':'ACTUAL_NEW_CURRENT_STUDY_STAGE_COMPLETE_NOT_REPLAY_OR_GATE',
        'new_manual_authorization_sha256':run['new_manual_authorization_sha256'],
        'biological_inputs_read':True,'biological_rows_read':13781,
        'all_nine_scientific_pool_bindings_equal':True,
        'historical_prefit_sha256':inp.historical_plan.prefit_sha256,
        'current_prefit_sha256':current_prefit_sha,
        'prefit_creator_provenance':provenance if owner.stage.name=='prefit' else None,
        'runtime_before_inputs':runtime.before,'runtime_after_work':after,
        'checkpoint_current_runtime_proof_sha256':dict(runtime.proofs),
        'checkpoints_fitted':checkpoints,'optimizer_units_executed':optimizer_units,
        'campaign_lifecycle':campaign_result,'evaluation_or_gate_run':False,
        'outer_performance_computed_or_published':False,'old_missing_paths':c.old_absences(),
        'old_missing_completion_synthesized':False,'current_fit_is_not_old_attempt_resume':True}


def run(stage,generation,run_sha,birth_sha,identity_sha,parent_pid,started):
    manifest=c.sources(generation)
    run_raw,admitted=c.admission(stage,generation);assert c.digest(run_raw)==run_sha
    owner=Owner(stage,generation,run_sha,birth_sha,identity_sha,parent_pid,started)
    report=analyze(owner,manifest,admitted)
    report_sha=c.save_new(stage.path('worker_report.json'),report)
    c.sources(generation);owner.fresh()
    c.save_new(stage.path('worker_completion.json'),{**owner.descriptor(),
        'status':'NEW_CURRENT_STUDY_WORKER_CLOSED_NOT_REPLAY_OR_GATE',
        'report_sha256':report_sha,'evaluation_or_gate_run':False})
    owner.closed=True


if __name__=='__main__':
    c.source_mode()
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=c.STAGES)
    parser.add_argument('generation');parser.add_argument('run_sha');parser.add_argument('birth_sha')
    parser.add_argument('identity_sha');parser.add_argument('parent_pid',type=int);parser.add_argument('started',type=float)
    args=parser.parse_args();stage=c.Stage(args.stage)
    with stage.path('worker_fault.log').open('x',encoding='utf8',buffering=1) as log:
        sys.stdout=sys.stderr=log;faulthandler.enable(log)
        try:run(stage,args.generation,args.run_sha,args.birth_sha,args.identity_sha,args.parent_pid,args.started)
        except BaseException:
            import traceback
            traceback.print_exc();log.flush();os.fsync(log.fileno());raise
        finally:faulthandler.disable()
