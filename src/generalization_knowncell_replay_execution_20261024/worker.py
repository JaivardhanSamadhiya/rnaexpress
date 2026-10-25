"""One independent complete campaign replay; never refit or evaluate."""
import argparse
import os
import sys
import traceback
from . import common as c,inputs,build,projection_io
from src.generalization_knowncell_joint_loader_20261022 import guard
from src.generalization_knowncell_calibrated_input_bridge_20261024 import bridge_v3 as bridge,contracts_v3 as bc
from src.generalization_knowncell_replay_runtime_20261024 import provider,contracts as rc
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lifecycle
from src.generalization_knowncell_prefit_projection_v2_20261024 import projection
from src.generalization_knowncell_campaign_replay_20261023.replay import verify_campaign

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


def fit_contract(report,completion,supervisor,run,plan):
    assert report['status']=='ACTUAL_ONE_OWNED_FIXED_FIT_LIFECYCLE_NOT_REPLAY_OR_EVALUATION'
    assert completion['status']=='PASS_FIXED_FIT_WORKER_CALLBACKS_RESTORED_LIFECYCLE_ONLY'
    assert supervisor['status']=='PASS_FIXED63_CHECKPOINT84_UNIT_FIT_LIFECYCLE_PENDING_INDEPENDENT_REPLAY'
    assert supervisor['failure'] is None and supervisor['report_sha256']==run['input_pins'][c.FIT_REPORT]
    assert completion['report_sha256']==run['input_pins'][c.FIT_REPORT]
    assert supervisor['worker_completion_sha256']==run['input_pins'][c.FIT_COMPLETION]
    for key in ('generation_manifest_sha256','run_admission_sha256','birth_sha256'):
        assert report[key]==completion[key]==supervisor[key]
    assert report['plan_identity']==plan.identity()
    assert report['actual_prefit_sha256']==completion['actual_prefit_sha256']==plan.prefit_sha256
    assert report['projection_root_admission_sha256']==run['input_pins'][c.PROJECTION_ADMISSION]
    assert report['checkpoints']==completion['checkpoints']==63 and report['optimizer_units']==completion['optimizer_units']==84
    assert completion['callbacks_restored'] is True
    assert report['CORE_reread'] is report['independent_replay_complete'] is report['evaluation_or_gate_run'] is False
    assert supervisor['observed']['exit_code']==0 and supervisor['observed']['failure'] is None
    hashes=supervisor['parent_terminal_lifecycle_validation']['files_sha256']
    assert run['campaign_pins']=={(c.FIT_CAMPAIGN/'checkpoints'/name).relative_to(c.ROOT).as_posix():want for name,want in hashes.items()}
    return report


def read_campaign(run):
    directory=c.FIT_CAMPAIGN/'checkpoints'
    expected={c.relative(name) for name in run['campaign_pins']}
    assert {path for path in directory.iterdir()}==expected and len(expected)==191
    raw={name:inputs.read_bound(name,want) for name,want in run['campaign_pins'].items()}
    def saved(name):return raw[(directory/name).relative_to(c.ROOT).as_posix()]
    records=[{'task_key':lifecycle.task_key(task),'birth_raw':saved(lifecycle.task_key(task)+'.birth.json'),
        'checkpoint_raw':saved(lifecycle.task_key(task)+'.model.json'),
        'completion_raw':saved(lifecycle.task_key(task)+'.complete.json')} for task in lifecycle.task_roster()]
    return saved('campaign_birth.json'),records,saved('campaign_complete.json')


def replay(session,generation,run_sha,birth_sha,evidence):
    admission=c.read_run(generation,run_sha,check_commit=True);manifest=c.verify_sources(generation)
    raw={name:inputs.read_bound(name,want) for name,want in admission['input_pins'].items()}
    obj={name:c.decode(value) for name,value in raw.items()}
    source=c.source_admission_contract(obj[c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()],generation,manifest)
    request=obj[c.REQUEST];binding=runtime_binding(request,admission['input_pins'][c.REQUEST],manifest)
    static_contract(obj[c.STATIC_BINDING],request,admission,source,generation,manifest)
    assert request['actual_prefit_sha256']==admission['input_pins'][c.PREFIT]
    assert request['projection_root_admission_sha256']==admission['input_pins'][c.PROJECTION_ADMISSION]
    actual,_=projection_io.input_contract(raw[c.PREFIT],raw[c.PROJECTION_ADMISSION],obj[c.PREFIT_COMPLETION],obj[c.PREFIT_SUPERVISOR],admission)
    inputs.persisted_label_contract(obj[c.METADATA_BUNDLE],obj[c.LABEL_CERTIFICATE],obj[c.LABEL_SUPERVISOR])
    before=accepted_runtime(binding,evidence,'before_replay')
    np,pd,minimize,expit=objects=tuple(before[key] for key in ('np','pd','minimize','expit'))
    context=current_owner_context(before,raw[c.STATIC_BINDING],request['controller_source_admission_sha256'])
    matrix,npz_read=inputs.reload_matrix(np,obj[c.ARRAY_CERTIFICATE])
    supplied=bridge.bridge_inputs(np,raw[c.METADATA_BUNDLE],matrix,raw[c.ARRAY_CERTIFICATE],raw[c.LABEL_CERTIFICATE],
        raw[c.STATIC_BINDING],before['fresh_origin_proof'],context,root_start=True)
    assert lifecycle.canonical_bytes(supplied['admissions'])==lifecycle.canonical_bytes(actual['input_admission_bindings'])
    prepared,sampler_identity=build.prepare_original_pools(np,pd,supplied,obj[c.ARRAY_CERTIFICATE])
    plan,owner_receipt=projection_io.bind_actual_plan(raw[c.PREFIT],raw[c.PROJECTION_ADMISSION],admission,
        generation,run_sha,evidence,binding,objects)
    prepared=projection.rebind_prepared(plan,prepared)
    fit_contract(obj[c.FIT_REPORT],obj[c.FIT_COMPLETION],obj[c.FIT_SUPERVISOR],admission,plan)
    campaign_birth,records,campaign_complete=read_campaign(admission)
    result=verify_campaign(np,prepared,plan,campaign_birth,records,campaign_complete)
    assert result['status']=='PASS_SUPPLIED63_CHECKPOINT84_UNIT_ARITHMETIC_AND_SOURCE_RESELECTION'
    assert result['verified_checkpoints']==63 and result['verified_optimizer_units_not_refitted']==84
    assert result['new_optimizer_calls']==0 and len(result['canonical_outer_records'])==9
    after=accepted_runtime(binding,evidence,'after_replay')
    for name,value in zip(('np','pd','minimize','expit'),objects):assert after[name] is value
    c.check_live_inputs(generation,run_sha)
    operational={'status':'ACTUAL_ONE_OWNED_INDEPENDENT63_CHECKPOINT_REPLAY_NO_EVALUATION','stage':c.STAGE,
        'invocation':c.INVOCATION,'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'parent_pid':os.getppid(),'worker_pid':os.getpid(),'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,'actual_prefit_sha256':plan.prefit_sha256,
        'fit_report_sha256':admission['input_pins'][c.FIT_REPORT],'fit_supervisor_sha256':admission['input_pins'][c.FIT_SUPERVISOR],
        'projection_root_admission_sha256':c.sha(raw[c.PROJECTION_ADMISSION]),'source_npz_read':npz_read,
        'saved_label_bits_sha256':c.LABEL_BITS_SHA,'CORE_reread':False,'new_optimizer_calls':0,
        'source_pools_rebuilt':9,'verified_checkpoints':63,'verified_recorded_optimizer_units':84,
        'source_selections_replayed':9,'evaluation_or_gate_run':False,'biological_or_generalization_claim':False}
    report=session.annotate(operational)
    protected={'runtime_acceptance':before['fresh_origin_proof'],'runtime_acceptance_after_replay':after['fresh_origin_proof'],
        'current_owner_context':context,'projection_current_owner_receipt':owner_receipt,
        'projection_context_raw':plan.verified_context_raw.decode('utf8'),'plan_identity':plan.identity(),
        'plan_operational_context':plan.operational_context(),'sampler_identity':sampler_identity,
        'bridge_report':supplied['bridge_report'],'independent_replay':result,'campaign_files_sha256':admission['campaign_pins']}
    report.update(protected);report['protected_provenance_sha256']=c.sha(c.canonical(protected))
    return report


def run(parent_pid,generation,run_sha,birth_sha):
    evidence={'parent_pid':parent_pid,'birth_sha256':birth_sha,'run_admission_sha256':run_sha}
    c.admit_authorization(generation);c.verify_owner(c.STAGE,generation,evidence)
    c.read_run(generation,run_sha,check_commit=True)
    assert not os.path.lexists(c.OUTPUT) and not os.path.lexists(c.COMPLETION)
    from .calibration import calibrated
    from src.generalization_pum_process_probe_20261021 import headless
    with calibrated(c.STAGE,generation,evidence) as session:
        report=replay(session,generation,run_sha,birth_sha,evidence)
        c.verify_sources(generation);c.read_run(generation,run_sha);guard.fresh_gate()
        output_sha=c.save_new(c.OUTPUT,report)
    assert session.restored is True and session.calls>0
    c.verify_sources(generation);c.verify_owner(c.STAGE,generation,evidence)
    assert c.resource_failure(headless.memory(),0) is None
    c.save_new(c.COMPLETION,{'status':'PASS_INDEPENDENT_REPLAY_WORKER_CALLBACKS_RESTORED_NO_EVALUATION',
        'invocation':c.INVOCATION,'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'parent_pid':parent_pid,'worker_pid':os.getpid(),'report_sha256':output_sha,'callbacks_restored':True,
        'fresh_calibrated_guard_calls':session.calls,'source_mode':c.source_mode(),'resource_policy':c.resource_policy(),
        'actual_prefit_sha256':report['actual_prefit_sha256'],'verified_checkpoints':63,
        'verified_recorded_optimizer_units':84,'new_optimizer_calls':0,'CORE_reread':False,'evaluation_or_gate_run':False})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('parent_pid',type=int)
    parser.add_argument('generation');parser.add_argument('run_sha');parser.add_argument('birth_sha')
    args=parser.parse_args();assert os.getppid()==args.parent_pid
    with c.WORKER_LOG.open('x',encoding='utf8') as log:
        sys.stdout=sys.stderr=log
        try:run(args.parent_pid,args.generation,args.run_sha,args.birth_sha)
        except BaseException:traceback.print_exc();raise


if __name__=='__main__':main()
