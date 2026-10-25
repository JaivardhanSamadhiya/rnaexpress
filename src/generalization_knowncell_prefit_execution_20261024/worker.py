"""One admitted-input reload and nine-pool prefit; never invoke an optimizer."""
import argparse
import os
import sys
import traceback
from . import common as c,inputs,build
from src.generalization_knowncell_joint_loader_20261022 import guard
from src.generalization_knowncell_calibrated_input_bridge_20261024 import bridge_v3 as bridge,contracts_v3 as bc
from src.generalization_knowncell_prefit_runtime_20261024 import provider,contracts as rc


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


def accepted_runtime(binding,evidence,phase):
    guard.fresh_gate();result=provider.provide(binding,evidence,phase=phase,root_start=True)
    assert set(result)=={'np','pd','actual_owner','fresh_origin_proof','fresh_origin_proof_sha256','actual_origin_receipt_sha256'}
    proof=result['fresh_origin_proof']
    assert bc.digest(bc.canonical(proof))==result['fresh_origin_proof_sha256']
    assert proof['status']==c.runtime.PROVIDER_STATUS and proof['stage']==c.STAGE and proof['provider_phase']==phase
    assert proof['request_binding']==binding
    assert proof['phase']==('before_supplied_input_bridge' if phase=='before_prefit' else 'after_pool_preparation')
    assert proof['actual_origin_receipt_sha256']==result['actual_origin_receipt_sha256']==c.runtime.PROFILE_ORIGIN_SHA
    assert proof['fresh_current_python_and_loaded_native_origins_checked'] is True and proof['invented_only'] is False
    assert proof['current_pid']==os.getpid() and proof['parent_pid']==os.getppid()
    assert proof['caller_birth_sha256']==evidence['birth_sha256']
    assert proof['runtime_and_FIT_authority_granted_here'] is False and proof['optimizer_calls']==0
    return result


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


def prepare(session,generation,run_sha,birth_sha,evidence):
    admission=c.read_run(generation,run_sha,check_commit=True);manifest=c.verify_sources(generation)
    raw={name:inputs.read_bound(name,want) for name,want in admission['input_pins'].items()}
    obj={name:c.decode(value) for name,value in raw.items()}
    source_name=c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()
    source=c.source_admission_contract(obj[source_name],generation,manifest)
    request=obj[c.REQUEST];binding=runtime_binding(request,admission['input_pins'][c.REQUEST],manifest)
    static_contract(obj[c.STATIC_BINDING],request,admission,source,generation,manifest)
    inputs.persisted_label_contract(obj[c.METADATA_BUNDLE],obj[c.LABEL_CERTIFICATE],obj[c.LABEL_SUPERVISOR])
    array=obj[c.ARRAY_CERTIFICATE];array_supervisor=obj[c.ARRAY_SUPERVISOR]
    assert array_supervisor['status']=='PASS_EXACT_ARRAY_EXECUTION_PENDING_ROOT_REVIEW_AND_COMMIT'
    assert array_supervisor['failure'] is None and array_supervisor['certificate_sha256']==c.ARRAY_CERTIFICATE_SHA
    before=accepted_runtime(binding,evidence,'before_prefit');np,pd=before['np'],before['pd']
    context=current_owner_context(before,raw[c.STATIC_BINDING],request['controller_source_admission_sha256'])
    matrix,npz_read=inputs.reload_matrix(np,array)
    supplied=bridge.bridge_inputs(np,raw[c.METADATA_BUNDLE],matrix,raw[c.ARRAY_CERTIFICATE],raw[c.LABEL_CERTIFICATE],
        raw[c.STATIC_BINDING],before['fresh_origin_proof'],context,root_start=True)
    assert supplied['features'] is matrix
    prepared,sampler_identity=build.prepare_original_pools(np,pd,supplied,array)
    after=accepted_runtime(binding,evidence,'after_prefit')
    assert after['np'] is np and after['pd'] is pd and after['actual_owner']==before['actual_owner']
    assert after['fresh_origin_proof']['static_root_binding_sha256']==before['fresh_origin_proof']['static_root_binding_sha256']
    operational={'status':'ACTUAL_ONE_OWNED_NINE_POOL_PREFIT_WITHOUT_FIT_AUTHORITY','stage':c.STAGE,'invocation':c.INVOCATION,
        'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'parent_pid':os.getppid(),'worker_pid':os.getpid(),'source_npz_read':npz_read,
        'metadata_bundle_sha256':c.METADATA_SHA,'array_certificate_sha256':c.ARRAY_CERTIFICATE_SHA,
        'label_certificate_sha256':c.LABEL_CERTIFICATE_SHA,'saved_label_bits_sha256':c.LABEL_BITS_SHA,
        'controller_source_admission_sha256':request['controller_source_admission_sha256'],
        'static_root_binding_sha256':request['static_root_binding_sha256'],'runtime_request_sha256':admission['input_pins'][c.REQUEST],
        'stable_admitted_runtime_binding_sha256':supplied['admissions']['runtime_binding_sha256'],
        'sampler_identity':sampler_identity,'bridge_report':supplied['bridge_report'],'source_pools_prepared':9,
        'original_scientific_settings_changed':False,'CORE_reread':False,'label_reparse_recast_or_recomputation':False,
        'optimizer_calls':0,'campaign_started':False,'runtime_and_FIT_authority_granted_here':False}
    # Operational IO fields alone are annotated. Fresh origin/context objects
    # remain exact compact-hashed payloads attached after annotation.
    annotated=session.annotate(operational)
    assert annotated['source_npz_read']['fresh_original_resource_gate_before_open'] is False
    protected={'runtime_acceptance':before['fresh_origin_proof'],'runtime_acceptance_after_prefit':after['fresh_origin_proof'],
               'current_owner_context':context}
    annotated.update(protected);annotated['protected_current_provenance_sha256']=c.sha(c.canonical(protected))
    actual=build.actual_prefit_document(prepared.prefit_document,annotated)
    validate_prefit(actual,generation,run_sha,birth_sha)
    return actual


def validate_prefit(value,generation,run_sha,birth_sha):
    from src.generalization_knowncell_joint_campaign_20261023 import contracts as lifecycle
    assert value['resource_exception_applies'] is True
    transient=dict(value);transient['resource_exception_applies']=False
    lifecycle.validate_prefit(transient)
    assert len(value['source_pools'])==9 and lifecycle.id_hash(value['all_row_ids'])==c.ROW_IDS_SHA
    assert value['metadata_admission_sha256']==c.METADATA_ADMISSION_SHA
    assert value['feature_admission_sha256']==c.ARRAY_CERTIFICATE_SHA and value['label_admission_sha256']==c.LABEL_CERTIFICATE_SHA
    for key,want in c.STABLE_SCIENTIFIC_BINDINGS.items():assert value['input_admission_bindings'][key]==want
    assert value['fit_source_manifest_sha256']==c.STABLE_SCIENTIFIC_BINDINGS['fit_source_manifest_sha256']
    detail=value['prefit_execution']
    admission=c.read_run(generation,run_sha)
    assert detail['stage']==c.STAGE and detail['invocation']==c.INVOCATION
    assert detail['generation_manifest_sha256']==generation and detail['run_admission_sha256']==run_sha and detail['birth_sha256']==birth_sha
    for key,want in (('approved_policy_manifest_sha256',c.POLICY_SHA),('authorization_sha256',c.AUTH_SHA),('approval_scope_sha256',c.SCOPE_SHA),
                     ('metadata_bundle_sha256',c.METADATA_SHA),('array_certificate_sha256',c.ARRAY_CERTIFICATE_SHA),
                     ('label_certificate_sha256',c.LABEL_CERTIFICATE_SHA),('saved_label_bits_sha256',c.LABEL_BITS_SHA)):
        assert detail[key]==want
    assert detail['original_resource_guards_unchanged'] is False and detail['source_pools_prepared']==9
    assert detail['source_npz_read']['actual_sha256']==c.NPZ_SHA
    assert detail['source_npz_read']['fresh_original_resource_gate_before_open'] is False
    assert detail['CORE_reread'] is detail['label_reparse_recast_or_recomputation'] is False
    assert detail['optimizer_calls']==0 and detail['campaign_started'] is detail['runtime_and_FIT_authority_granted_here'] is False
    assert detail['stable_admitted_runtime_binding_sha256']==value['runtime_binding_sha256']
    for key,path in (('static_root_binding_sha256',c.STATIC_BINDING),('controller_source_admission_sha256',c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()),
                     ('runtime_request_sha256',c.REQUEST)):
        assert detail[key]==admission['input_pins'][path]
    protected={name:detail[name] for name in ('runtime_acceptance','runtime_acceptance_after_prefit','current_owner_context')}
    assert c.sha(c.canonical(protected))==detail['protected_current_provenance_sha256']
    for name,phase in (('runtime_acceptance','before_supplied_input_bridge'),('runtime_acceptance_after_prefit','after_pool_preparation')):
        proof=detail[name]
        assert proof['status']==c.runtime.PROVIDER_STATUS and proof['stage']==c.STAGE and proof['phase']==phase
        assert proof['current_pid']==detail['worker_pid'] and proof['parent_pid']==detail['parent_pid']
        assert proof['caller_birth_sha256']==birth_sha and proof['static_root_binding_sha256']==detail['static_root_binding_sha256']
        assert proof['reviewed_controller_admission_sha256']==detail['controller_source_admission_sha256']
        assert proof['stable_admitted_runtime_binding_sha256']==value['runtime_binding_sha256']
        assert proof['request_binding']['request_sha256']==detail['runtime_request_sha256']
        assert proof['request_binding']['request_relative_path']==c.REQUEST
        assert proof['software_status_sha256']==c.runtime.SOFTWARE_STATUS_SHA and proof['software_certificate_sha256']==c.runtime.PANDAS_ADMISSION_SHA
        assert proof['actual_origin_receipt_sha256']==c.runtime.PROFILE_ORIGIN_SHA
        assert proof['numerical_threads']==1 and proof['source_cache_remained_absent'] is True
        assert proof['numpy_version']=='1.26.4' and proof['pandas_version']=='2.2.3' and proof['scipy_version']=='1.14.1'
        assert proof['old_interpreter_bitwise_parity_established'] is False
        assert proof['invented_only'] is False and proof['fresh_current_python_and_loaded_native_origins_checked'] is True
        assert proof['optimizer_calls']==0 and proof['runtime_and_FIT_authority_granted_here'] is False
    assert detail['runtime_acceptance']['request_binding']==detail['runtime_acceptance_after_prefit']['request_binding']
    context=detail['current_owner_context']
    assert set(context)==bc.OWNER_FIELDS and context['status']=='SUPPLIED_CURRENT_OWNER_CONTEXT_REQUIRES_ACTUAL_FIXED_CALLER_VERIFICATION'
    assert context['stage']==c.STAGE and context['actual_parent_Job_and_native_origins_checked_by_fixed_caller'] is True
    assert context['runtime_and_FIT_authority_granted_here'] is False
    assert context['static_root_binding_sha256']==detail['static_root_binding_sha256']
    assert context['reviewed_controller_admission_sha256']==detail['controller_source_admission_sha256']
    assert context['current_stage_origin_proof_sha256']==bc.digest(bc.canonical(detail['runtime_acceptance']))
    assert context['caller_birth_sha256']==birth_sha and context['current_pid']==detail['worker_pid'] and context['parent_pid']==detail['parent_pid']
    calibration=detail['resource_calibration']
    assert calibration['stage']==c.STAGE and calibration['execution_manifest_sha256']==generation
    assert calibration['birth_sha256']==birth_sha and calibration['authorization_sha256']==c.AUTH_SHA
    assert calibration['current_pid']==detail['worker_pid'] and calibration['parent_pid']==detail['parent_pid']
    assert calibration['invocation']==c.INVOCATION and calibration['scientific_protocol_settings_changed'] is False
    assert calibration['approved_policy_manifest_sha256']==c.POLICY_SHA and calibration['approval_scope_sha256']==c.SCOPE_SHA
    return value


def run(parent_pid,generation,run_sha,birth_sha):
    evidence={'parent_pid':parent_pid,'birth_sha256':birth_sha,'run_admission_sha256':run_sha}
    c.admit_authorization(generation);c.verify_owner(c.STAGE,generation,evidence)
    c.read_run(generation,run_sha,check_commit=True)
    assert not os.path.lexists(c.OUTPUT) and not os.path.lexists(c.COMPLETION)
    from .calibration import calibrated
    from src.generalization_pum_process_probe_20261021 import headless
    with calibrated(c.STAGE,generation,evidence) as session:
        actual=prepare(session,generation,run_sha,birth_sha,evidence)
        c.verify_sources(generation);c.read_run(generation,run_sha)
        guard.fresh_gate();output_sha=c.save_new(c.OUTPUT,actual)
    assert session.restored is True and session.calls>0
    c.verify_sources(generation);c.verify_owner(c.STAGE,generation,evidence)
    assert c.resource_failure(headless.memory(),0) is None
    c.save_new(c.COMPLETION,{'status':'PASS_EXACT_NINE_POOL_PREFIT_WORKER_CALLBACKS_RESTORED','invocation':c.INVOCATION,
        'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'parent_pid':parent_pid,'worker_pid':os.getpid(),'prefit_sha256':output_sha,'callbacks_restored':True,
        'fresh_calibrated_guard_calls':session.calls,'source_mode':c.source_mode(),'resource_policy':c.resource_policy(),
        'source_pools_prepared':9,'optimizer_calls':0,'campaign_started':False,'CORE_reread':False,
        'saved_label_bits_sha256':c.LABEL_BITS_SHA,'all_row_ids_sha256':c.ROW_IDS_SHA})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('parent_pid',type=int)
    parser.add_argument('generation');parser.add_argument('run_sha');parser.add_argument('birth_sha')
    args=parser.parse_args();assert os.getppid()==args.parent_pid
    c.admit_authorization(args.generation)
    c.verify_owner(c.STAGE,args.generation,{'parent_pid':args.parent_pid,'birth_sha256':args.birth_sha,'run_admission_sha256':args.run_sha})
    with c.WORKER_LOG.open('x',encoding='utf8') as log:
        sys.stdout=sys.stderr=log
        try:run(args.parent_pid,args.generation,args.run_sha,args.birth_sha)
        except BaseException:traceback.print_exc();raise


if __name__=='__main__':main()
