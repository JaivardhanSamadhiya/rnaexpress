"""One owned fixed FIT invocation; no evaluation or replay claim."""
import argparse
import faulthandler
import os
import sys
import traceback
from . import common as c,inputs,build,projection_io
from src.generalization_knowncell_joint_loader_20261022 import guard
from src.generalization_knowncell_calibrated_input_bridge_20261024 import bridge_v6_fit_roomy as bridge,contracts_v3 as bc
from src.generalization_knowncell_fit_roomy_runtime_20261025 import provider,contracts as rc
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lifecycle
from src.generalization_knowncell_joint_engine_20261023 import adapter_v2 as adapter
from src.generalization_knowncell_joint_runner_20261023.runner import run_campaign
from src.generalization_knowncell_prefit_projection_v2_20261024 import projection

def runtime_binding(request,request_sha,manifest):
    binding={'request_relative_path':c.REQUEST,'request_sha256':request_sha,
        'provider_preparation_manifest_sha256':manifest['files'][c.runtime.PREPARATION],
        'software_status_sha256':c.runtime.SOFTWARE_STATUS_SHA,'pandas_admission_sha256':c.runtime.PANDAS_ADMISSION_SHA}
    rc.binding_contract(binding)
    rc.request_contract(request,binding,manifest['files'][c.runtime.SOURCE])
    return binding

def static_contract(binding,request,admission,source,generation,manifest):
    bc.binding_contract(binding)
    assert binding['stage']==c.STAGE and binding['metadata_bundle_sha256']==c.METADATA_SHA
    assert binding['array_certificate_sha256']==c.ARRAY_CERTIFICATE_SHA and binding['array_supervisor_sha256']==c.ARRAY_SUPERVISOR_SHA
    assert binding['label_certificate_sha256']==c.LABEL_CERTIFICATE_SHA
    assert binding['reviewed_controller_source']==c.WORKER_SOURCE
    assert binding['reviewed_controller_source_sha256']==manifest['files'][c.WORKER_SOURCE]
    assert binding['reviewed_controller_admission_sha256']==admission['input_pins'][c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()]
    assert binding['bridge_readiness_sha256']==manifest['files'][c.BRIDGE_READY]
    assert request['generation_manifest_sha256']==generation
    assert request['static_root_binding_sha256']==admission['input_pins'][c.STATIC_BINDING]
    assert request['controller_source_admission_sha256']==binding['reviewed_controller_admission_sha256']
    assert request['stable_admitted_runtime_binding_sha256']==binding['runtime_binding_sha256']
    assert source['controller_source_sha256']==binding['reviewed_controller_source_sha256']
    for key,want in c.STABLE_SCIENTIFIC_BINDINGS.items():assert binding[key]==source['stable_scientific_source_bindings'][key]==want
    return binding

def current_owner_context(result,static_raw,source_sha):
    proof=result['fresh_origin_proof'];owner=result['actual_owner']
    assert owner['current_pid']==proof['current_pid']==os.getpid()
    assert owner['parent_pid']==proof['parent_pid']==os.getppid()
    assert owner['in_owned_job'] is True and owner['birth_sha256']==proof['caller_birth_sha256']
    assert proof['static_root_binding_sha256']==bc.digest(static_raw)
    assert proof['reviewed_controller_admission_sha256']==source_sha
    return {'status':'SUPPLIED_CURRENT_OWNER_CONTEXT_REQUIRES_ACTUAL_FIXED_CALLER_VERIFICATION','stage':c.STAGE,
        'current_pid':owner['current_pid'],'parent_pid':owner['parent_pid'],'caller_birth_sha256':owner['birth_sha256'],
        'current_stage_origin_proof_sha256':bc.digest(bc.canonical(proof)),
        'static_root_binding_sha256':bc.digest(static_raw),'reviewed_controller_admission_sha256':source_sha,
        'actual_parent_Job_and_native_origins_checked_by_fixed_caller':True,'runtime_and_FIT_authority_granted_here':False}


def accepted_runtime(binding,evidence,phase,*,task_key=None):
    guard.fresh_gate()
    result=provider.provide(binding,evidence,phase=phase,task_key=task_key,root_start=True)
    assert set(result)=={'np','pd','minimize','expit','actual_owner','fresh_origin_proof','fresh_origin_proof_sha256','actual_origin_receipt_sha256'}
    proof=result['fresh_origin_proof']
    assert bc.digest(bc.canonical(proof))==result['fresh_origin_proof_sha256']
    assert proof['status']==c.runtime.PROVIDER_STATUS and proof['stage']==c.STAGE and proof['provider_phase']==phase
    assert proof['request_binding']==binding and proof['checkpoint_key']==task_key
    assert proof['actual_origin_receipt_sha256']==result['actual_origin_receipt_sha256']==c.runtime.PROFILE_ORIGIN_SHA
    assert proof['fresh_current_python_and_loaded_native_origins_checked'] is True and proof['invented_only'] is False
    assert proof['current_pid']==os.getpid() and proof['parent_pid']==os.getppid()
    assert proof['caller_birth_sha256']==evidence['birth_sha256']
    assert proof['runtime_and_FIT_authority_granted_here'] is False and proof['optimizer_calls']==0
    return result


def make_integrity_hook(generation,run_sha,evidence,binding,objects,prepared,plan):
    """Fixed source-owned hook, not a production caller-injected True stub."""
    keys=list(c.runtime.CHECKPOINT_KEYS);saved={};initial_identity=lifecycle.hash_value(plan.identity())
    fixed_plan,fixed_prepared=plan,prepared
    assert not c.CHECKPOINT_PROOFS.exists();c.CHECKPOINT_PROOFS.mkdir()
    def hook(*,task_key,task,plan:object,prepared:object,campaign):
        assert len(saved)<63 and task_key==keys[len(saved)]
        expected=lifecycle.task_roster()[len(saved)]
        assert task==expected and lifecycle.task_key(task)==task_key
        assert plan is fixed_plan and prepared is fixed_prepared
        assert campaign.plan is plan and campaign.plan.prefit_sha256==plan.prefit_sha256
        assert lifecycle.hash_value(plan.identity())==initial_identity
        assert prepared.prefit_document==plan.document()
        c.admit_authorization(generation);c.verify_owner(c.STAGE,generation,evidence)
        c.check_live_inputs(generation,run_sha)
        answer=accepted_runtime(binding,evidence,'checkpoint',task_key=task_key)
        for key,obj in zip(('np','pd','minimize','expit'),objects):assert answer[key] is obj
        assert answer['fresh_origin_proof']['checkpoint_refresh_count']==len(saved)+1
        adapter.original.check_pool(objects[0],prepared,plan,task)
        c.verify_sources(generation);c.read_run(generation,run_sha)
        guard.fresh_gate()
        path=c.CHECKPOINT_PROOFS/(task_key+'.json')
        saved[task_key]=c.save_new(path,answer['fresh_origin_proof'])
        return True
    return hook,saved


def fit(session,generation,run_sha,birth_sha,evidence):
    admission=c.read_run(generation,run_sha,check_commit=True);manifest=c.verify_sources(generation)
    raw={name:inputs.read_bound(name,want) for name,want in admission['input_pins'].items()}
    obj={name:c.decode(value) for name,value in raw.items()}
    source_name=c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()
    source=c.source_admission_contract(obj[source_name],generation,manifest)
    request=obj[c.REQUEST];binding=runtime_binding(request,admission['input_pins'][c.REQUEST],manifest)
    static_contract(obj[c.STATIC_BINDING],request,admission,source,generation,manifest)
    assert request['actual_prefit_sha256']==admission['input_pins'][c.PREFIT]
    assert request['projection_root_admission_sha256']==admission['input_pins'][c.PROJECTION_ADMISSION]
    actual,_=projection_io.input_contract(raw[c.PREFIT],raw[c.PROJECTION_ADMISSION],obj[c.PREFIT_COMPLETION],obj[c.PREFIT_SUPERVISOR],admission)
    inputs.persisted_label_contract(obj[c.METADATA_BUNDLE],obj[c.LABEL_CERTIFICATE],obj[c.LABEL_SUPERVISOR])
    array=obj[c.ARRAY_CERTIFICATE]
    assert obj[c.ARRAY_SUPERVISOR]['status']=='PASS_EXACT_ARRAY_EXECUTION_PENDING_ROOT_REVIEW_AND_COMMIT'
    assert obj[c.ARRAY_SUPERVISOR]['failure'] is None and obj[c.ARRAY_SUPERVISOR]['certificate_sha256']==c.ARRAY_CERTIFICATE_SHA
    before=accepted_runtime(binding,evidence,'before_fit')
    np,pd,minimize,expit=objects=tuple(before[key] for key in ('np','pd','minimize','expit'))
    context=current_owner_context(before,raw[c.STATIC_BINDING],request['controller_source_admission_sha256'])
    matrix,npz_read=inputs.reload_matrix(np,array)
    supplied=bridge.bridge_inputs(np,raw[c.METADATA_BUNDLE],matrix,raw[c.ARRAY_CERTIFICATE],raw[c.LABEL_CERTIFICATE],
        raw[c.STATIC_BINDING],before['fresh_origin_proof'],context,root_start=True)
    assert lifecycle.canonical_bytes(supplied['admissions'])==lifecycle.canonical_bytes(actual['input_admission_bindings'])
    prepared,sampler_identity=build.prepare_original_pools(np,pd,supplied,array)
    plan,owner_receipt=projection_io.bind_actual_plan(raw[c.PREFIT],raw[c.PROJECTION_ADMISSION],admission,
        generation,run_sha,evidence,binding,objects)
    prepared=projection.rebind_prepared(plan,prepared)
    hook,proof_hashes=make_integrity_hook(generation,run_sha,evidence,binding,objects,prepared,plan)
    result=run_campaign(prepared,plan,np,minimize,expit,probe=guard.live_resources,environment=os.environ,
        directory=c.CAMPAIGN,before_checkpoint_integrity=hook)
    assert result['status']=='COMPLETE63_CHECKPOINT84_UNIT_LIFECYCLE_NOT_SCIENTIFIC_REPLAY_OR_GATE'
    assert list(proof_hashes)==list(c.runtime.CHECKPOINT_KEYS)
    after=accepted_runtime(binding,evidence,'after_fit')
    for key,obj_value in zip(('np','pd','minimize','expit'),objects):assert after[key] is obj_value
    assert after['fresh_origin_proof']['checkpoint_refresh_count']==63
    operational={'status':'ACTUAL_ONE_OWNED_FIXED_FIT_LIFECYCLE_NOT_REPLAY_OR_EVALUATION',
        'stage':c.STAGE,'invocation':c.INVOCATION,'generation_manifest_sha256':generation,
        'run_admission_sha256':run_sha,'birth_sha256':birth_sha,'parent_pid':os.getppid(),'worker_pid':os.getpid(),
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'actual_prefit_sha256':plan.prefit_sha256,'projection_root_admission_sha256':c.sha(raw[c.PROJECTION_ADMISSION]),
        'source_npz_read':npz_read,'CORE_reread':False,'label_reparse_recast_or_recomputation':False,
        'saved_label_bits_sha256':c.LABEL_BITS_SHA,'all_row_ids_sha256':c.ROW_IDS_SHA,
        'source_pools_rebuilt':9,'checkpoints':63,'optimizer_units':84,
        'checkpoint_runtime_refreshes':63,'original_scientific_settings_changed':False,
        'independent_replay_complete':False,'evaluation_or_gate_run':False,'biological_or_generalization_claim':False}
    report=session.annotate(operational)
    protected={'runtime_acceptance':before['fresh_origin_proof'],'runtime_acceptance_after_fit':after['fresh_origin_proof'],
        'current_owner_context':context,'projection_current_owner_receipt':owner_receipt,
        'projection_context_raw':plan.verified_context_raw.decode('utf8'),'plan_identity':plan.identity(),
        'plan_operational_context':plan.operational_context(),'checkpoint_runtime_proof_sha256':proof_hashes,
        'sampler_identity':sampler_identity,'bridge_report':supplied['bridge_report'],'campaign_lifecycle':result}
    report.update(protected);report['protected_provenance_sha256']=c.sha(c.canonical(protected))
    c.verify_sources(generation);c.read_run(generation,run_sha);guard.fresh_gate()
    return report


def run(parent_pid,generation,run_sha,birth_sha):
    evidence={'parent_pid':parent_pid,'birth_sha256':birth_sha,'run_admission_sha256':run_sha}
    c.admit_authorization(generation);c.verify_owner(c.STAGE,generation,evidence)
    c.read_run(generation,run_sha,check_commit=True)
    assert not os.path.lexists(c.OUTPUT) and not os.path.lexists(c.COMPLETION)
    from .calibration import calibrated
    from src.generalization_pum_process_probe_20261021 import headless
    with calibrated(c.STAGE,generation,evidence) as session:
        report=fit(session,generation,run_sha,birth_sha,evidence)
        c.verify_sources(generation);c.read_run(generation,run_sha);guard.fresh_gate()
        output_sha=c.save_new(c.OUTPUT,report)
    assert session.restored is True and session.calls>0
    c.verify_sources(generation);c.verify_owner(c.STAGE,generation,evidence)
    assert c.resource_failure(headless.memory(),0) is None
    c.save_new(c.COMPLETION,{'status':'PASS_FIXED_FIT_WORKER_CALLBACKS_RESTORED_LIFECYCLE_ONLY',
        'invocation':c.INVOCATION,'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'parent_pid':parent_pid,'worker_pid':os.getpid(),'report_sha256':output_sha,'callbacks_restored':True,
        'fresh_calibrated_guard_calls':session.calls,'source_mode':c.source_mode(),'resource_policy':c.resource_policy(),
        'actual_prefit_sha256':report['actual_prefit_sha256'],'checkpoints':63,'optimizer_units':84,'checkpoint_runtime_refreshes':63,
        'CORE_reread':False,'independent_replay_complete':False,'evaluation_or_gate_run':False})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('parent_pid',type=int)
    parser.add_argument('generation');parser.add_argument('run_sha');parser.add_argument('birth_sha')
    args=parser.parse_args();assert os.getppid()==args.parent_pid
    c.admit_authorization(args.generation)
    c.verify_owner(c.STAGE,args.generation,{'parent_pid':args.parent_pid,'birth_sha256':args.birth_sha,'run_admission_sha256':args.run_sha})
    with c.WORKER_LOG.open('x',encoding='utf8') as log:
        sys.stdout=sys.stderr=log
        faulthandler.enable(log)
        print('FIXED_FIT_WORKER_ENTERED',os.getpid(),os.getppid(),flush=True)
        try:run(args.parent_pid,args.generation,args.run_sha,args.birth_sha)
        except BaseException:traceback.print_exc();raise
        finally:faulthandler.disable()


if __name__=='__main__':main()
