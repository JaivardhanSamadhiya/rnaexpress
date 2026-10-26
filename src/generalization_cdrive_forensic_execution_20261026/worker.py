"""One actual-new-owner read-only worker; no optimizer or performance path."""
import argparse
import faulthandler
import os
import sys
from . import common as c
from .runtime_or_owner import CurrentOwner,Runtime


def analyze(owner,manifest):
    from . import inputs,pools
    from src.generalization_cdrive_checkpoint_forensics_20261026 import supplied,arithmetic,declarations
    from src.generalization_knowncell_joint_implementation_20261022 import contracts as metadata
    from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
    from src.generalization_knowncell_joint_engine_20261023 import adapter
    owner.fresh();c.bind_read_set(manifest);c.old_absences()
    runtime=Runtime(owner,manifest) # Actual fresh origins BEFORE biological reads.
    initial=runtime.first
    inp=inputs.read_inputs(runtime.np,fresh=owner.fresh)
    prepared=pools.build_pools(runtime.np,runtime.pd,inp,fresh=owner.fresh)
    records=inputs.load_records(inp,fresh=owner.fresh)
    filename_pins={c.relative(name).name:want for name,want in inp.checkpoint_hashes.items()}
    assert len(filename_pins)==190
    saved_declarations=declarations.check_saved_declarations(c.ROOT/c.CHECKPOINT_PREFIX,inp.historical_plan,
        inp.campaign_birth_raw,filename_pins,fresh=owner.fresh)
    # Same public-core preconditions; the fixed numeric hook adds one NEW actual
    # owner/native proof before each checkpoint, without changing its arithmetic.
    plan=inp.historical_plan
    document=lc.validate_prefit(plan.document())
    contract=metadata.full_metadata_contract(prepared.metadata)
    assert prepared.prefit_document==document and len(prepared.pools)==9
    assert set(prepared.pools)==set(document['source_pools'])
    assert [row['intervention_id'] for row in prepared.metadata]==document['all_row_ids']
    assert [row['held_parent_fold'] for row in prepared.metadata]==document['all_row_folds']
    admission=document['input_admission_bindings']
    assert contract['row_ids_sha256']==admission['input_row_ids_sha256']
    assert contract['metadata_sha256']==admission['input_metadata_sha256']
    by_id={row['intervention_id']:row for row in prepared.metadata}
    tasks=lc.task_roster();task_keys={lc.task_key(task) for task in tasks}
    def check_pool(task):
        owner.fresh()
        pool=prepared.pools[lc.pool_key(task['outer_fold'],task['inner_fold'])]
        assert adapter.pool_binding(runtime.np,pool)==pool['binding']==plan.pool(task)
        assert pool['rows']==[by_id[key] for key in pool['binding']['training_ids']]
        assert pool['validation_metadata']==[by_id[key] for key in pool['binding']['validation_ids']]
        return pool
    def check_numeric(pool,task,model,predictions):
        runtime.proof(lc.task_key(task))
        return arithmetic.inspect_checkpoint(runtime.np,pool,task,model,predictions,fresh=owner.fresh)
    diagnostics=supplied._inspect(runtime.np,prepared,plan,inp.campaign_birth_raw,records,
        fresh=owner.fresh,pool_check=check_pool,numeric_check=check_numeric)
    assert set(runtime.proofs)==task_keys and len(runtime.proofs)==63
    final=runtime.proof()
    c.rehash_read_set(manifest,fresh=owner.fresh)
    c.sources(owner.generation);owner.fresh()
    return {'status':c.REPORT_STATUS,'stage':c.STAGE,'generation_manifest_sha256':owner.generation,
        'birth_sha256':owner.birth_sha,'owned_child_identity_sha256':owner.identity_sha,
        'current_child_record_sha256':owner.owner_record_sha,
        'parent_pid':owner.parent_pid,'worker_pid':os.getpid(),
        'biological_inputs_read':True,'biological_rows_read':13781,'new_optimizer_calls':0,
        'original_formal_replay_still_ineligible':True,'outer_performance_computed_or_published':False,
        'evaluation_or_gate_run':False,'old_missing_terminal_paths':c.old_absences(),
        'runtime_before_inputs':initial,'runtime_after_forensics':final,
        'checkpoint_current_runtime_proof_sha256':dict(runtime.proofs),
        'forensic_numeric_diagnostics':diagnostics,
        'saved_declarations':saved_declarations,
        'historical_plan_is_saved_declarations_only':True,
        'read_only_input_pins':dict(manifest['readonly_input_pins'])}


def run(parent_pid,generation,birth_sha,identity_sha,started):
    manifest=c.sources(generation)
    owner=CurrentOwner(parent_pid,generation,birth_sha,identity_sha,started,manifest)
    report=analyze(owner,manifest)
    report_sha=c.save_new(c.REPORT,report)
    c.sources(generation);owner.fresh();c.old_absences()
    c.save_new(c.COMPLETION,{'status':c.WORKER_PASS,'generation_manifest_sha256':generation,
        'birth_sha256':birth_sha,'owned_child_identity_sha256':identity_sha,
        'current_child_record_sha256':owner.owner_record_sha,
        'parent_pid':parent_pid,'worker_pid':os.getpid(),'report_sha256':report_sha,
        'biological_inputs_read':True,'biological_rows_read':13781,'new_optimizer_calls':0,
        'original_formal_replay_still_ineligible':True,'outer_performance_computed_or_published':False,
        'evaluation_or_gate_run':False})
    owner.closed=True


if __name__=='__main__':
    c.source_mode()
    parser=argparse.ArgumentParser();parser.add_argument('parent_pid',type=int)
    parser.add_argument('generation');parser.add_argument('birth_sha');parser.add_argument('identity_sha');parser.add_argument('started',type=float)
    args=parser.parse_args()
    with c.FAULT_LOG.open('x',encoding='utf8',buffering=1) as log:
        sys.stdout=sys.stderr=log;faulthandler.enable(file=log)
        try:run(args.parent_pid,args.generation,args.birth_sha,args.identity_sha,args.started)
        except BaseException:
            import traceback
            traceback.print_exc();log.flush();os.fsync(log.fileno());raise
        finally:faulthandler.disable()
