"""One original frozen evaluation after accepted complete independent replay."""
import argparse
import os
import sys
import traceback
from . import common as c,inputs,results_io
from src.generalization_knowncell_evaluation_v2_runtime_20261025 import provider,contracts as rc
from src.generalization_knowncell_joint_loader_20261022 import guard
from src.generalization_knowncell_joint_implementation_20261022 import contracts as reference
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_joint_input_bridge_20261023.contracts import runtime_contract
from src.generalization_knowncell_joint_evaluation_20261023.evaluation import evaluate
from src.generalization_knowncell_replay_v4_execution_20261025.terminal import PROTECTED as REPLAY_PROTECTED
from src.generalization_knowncell_replay_v4_execution_20261025.fit_journal import STATUS as JOURNAL_STATUS


def runtime_binding(request,request_sha,manifest):
    binding={'request_relative_path':c.REQUEST,'request_sha256':request_sha,
        'provider_preparation_manifest_sha256':manifest['files'][c.runtime.PREPARATION],
        'software_status_sha256':c.runtime.SOFTWARE_STATUS_SHA,'pandas_admission_sha256':c.runtime.PANDAS_ADMISSION_SHA}
    rc.binding_contract(binding);rc.request_contract(request,binding,manifest['files'][c.runtime.SOURCE]);return binding


def static_contract(value,request,run,generation,manifest):
    fields={'status','stage','generation_manifest_sha256','controller_source','controller_source_sha256',
        'controller_source_admission_sha256','metadata_bundle_sha256','label_certificate_sha256','replay_report_sha256',
        'actual_prefit_sha256','projection_root_admission_sha256','stable_admitted_runtime_binding_sha256',
        'original_evaluation_source_manifest_sha256','approved_policy_manifest_sha256','authorization_sha256',
        'approval_scope_sha256','no_new_fit_array_or_pool_authority','independent_replay_generation_manifest_sha256'}
    assert set(value)==fields and value['status']=='FROZEN_COMPLETE_REPLAY_AND_ORIGINAL_EVALUATION_INPUTS_NO_FIT'
    assert value['stage']==c.STAGE and value['generation_manifest_sha256']==generation
    assert value['independent_replay_generation_manifest_sha256']==run['independent_replay_generation_manifest_sha256']==c.REPLAY_EXECUTION_GENERATION_SHA
    assert value['controller_source']==c.WORKER_SOURCE and value['controller_source_sha256']==manifest['files'][c.WORKER_SOURCE]
    assert value['controller_source_admission_sha256']==run['input_pins'][c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()]
    for key,path in (('metadata_bundle_sha256',c.METADATA_BUNDLE),('label_certificate_sha256',c.LABEL_CERTIFICATE),
        ('replay_report_sha256',c.REPLAY_REPORT),('actual_prefit_sha256',c.PREFIT),('projection_root_admission_sha256',c.PROJECTION_ADMISSION)):
        assert value[key]==run['input_pins'][path]
    assert value['stable_admitted_runtime_binding_sha256']==c.ARRAY_RUNTIME_ANCHOR_SHA==request['stable_admitted_runtime_binding_sha256']
    assert value['original_evaluation_source_manifest_sha256']==c.EVALUATION_READY_SHA
    assert value['approved_policy_manifest_sha256']==c.POLICY_SHA and value['authorization_sha256']==c.AUTH_SHA
    assert value['approval_scope_sha256']==c.SCOPE_SHA and value['no_new_fit_array_or_pool_authority'] is True
    assert request['static_root_binding_sha256']==run['input_pins'][c.STATIC_BINDING]
    assert request['generation_manifest_sha256']==generation
    assert request['controller_source_admission_sha256']==value['controller_source_admission_sha256']
    assert request['actual_prefit_sha256']==value['actual_prefit_sha256'] and request['projection_root_admission_sha256']==value['projection_root_admission_sha256']
    return value


def replay_contract(report,completion,supervisor,run,prefit,root):
    assert report['status']=='ACTUAL_ONE_OWNED_INDEPENDENT63_CHECKPOINT_REPLAY_NO_EVALUATION'
    assert completion['status']=='PASS_INDEPENDENT_REPLAY_WORKER_CALLBACKS_RESTORED_NO_EVALUATION'
    assert supervisor['status']=='PASS_INDEPENDENT63_CHECKPOINT_REPLAY_PENDING_ROOT_ACCEPTANCE' and supervisor['failure'] is None
    assert completion['report_sha256']==supervisor['report_sha256']==run['input_pins'][c.REPLAY_REPORT]
    assert supervisor['worker_completion_sha256']==run['input_pins'][c.REPLAY_COMPLETION]
    for key in ('generation_manifest_sha256','run_admission_sha256','birth_sha256','invocation'):
        assert report[key]==completion[key]==supervisor[key]
    assert report['generation_manifest_sha256']==run['independent_replay_generation_manifest_sha256']==c.REPLAY_EXECUTION_GENERATION_SHA
    assert c.sha(c.canonical({key:report[key] for key in REPLAY_PROTECTED}))==report['protected_provenance_sha256']
    journal=report['fit_journal_validation']
    assert journal['status']==JOURNAL_STATUS and journal['fit_generation_manifest_sha256']==c.FIT_GENERATION_SHA
    assert journal['journal_sha256']==report['fit_journal_sha256']
    for key in ('recorded_closed_before_receipt','saved_resource_predicates_independently_checked',
            'all_saved_current_lifetime_resident_private_and_job_bounds_checked',
            'installed_resident_policy_and_readback_checked','only_last_sample_has_zero_exit'):
        assert journal[key] is True
    assert journal['physical_durability_retroactively_established'] is journal['old_fit_owner_reused_as_current_replay_owner'] is False
    for key,want in (('verified_checkpoints',63),('verified_recorded_optimizer_units',84),('new_optimizer_calls',0)):
        assert report[key]==completion[key]==supervisor[key]==want
    assert report['evaluation_or_gate_run'] is completion['evaluation_or_gate_run'] is supervisor['evaluation_or_gate_run'] is False
    assert report['CORE_reread'] is False and completion['callbacks_restored'] is True
    assert supervisor['observed']['exit_code']==0 and supervisor['observed']['failure'] is None
    assert report['actual_prefit_sha256']==run['input_pins'][c.PREFIT]==root['prefit_sha256']
    assert report['projection_root_admission_sha256']==run['input_pins'][c.PROJECTION_ADMISSION]
    identity=report['plan_identity'];assert identity['prefit_sha256']==root['prefit_sha256'] and identity['prefit_commit']==run['actual_prefit_commit']
    assert identity['runtime_binding_sha256']==prefit['runtime_binding_sha256']==c.ARRAY_RUNTIME_ANCHOR_SHA
    assert identity['source_pool_sha256']=={key:lc.hash_value(value) for key,value in prefit['source_pools'].items()}
    detail=identity['calibrated_resource_compatibility_view']
    assert detail['root_admission_sha256']==run['input_pins'][c.PROJECTION_ADMISSION] and detail['root_admission_commit']==run['projection_root_admission_commit']
    result=report['independent_replay']
    assert result['status']=='PASS_SUPPLIED63_CHECKPOINT84_UNIT_ARITHMETIC_AND_SOURCE_RESELECTION'
    assert result['verified_checkpoints']==63 and result['verified_optimizer_units_not_refitted']==84 and result['verified_inner_checkpoints']==54
    assert result['new_optimizer_calls']==0 and result['gate_or_evaluation_run'] is False
    assert len(result['canonical_outer_records'])==9 and len(result['source_only_outer_reselections'])==9
    from src.generalization_knowncell_campaign_replay_20261023.replay import ERROR_FIELDS
    for key in ERROR_FIELDS:assert 0<=result['maximum_arithmetic_differences'][key]<1e-9
    assert result['independent_confirmation'] is result['unknown_cell_generalization'] is result['novelty_certified'] is False
    return result['canonical_outer_records']


def accepted_runtime(binding,evidence,phase):
    guard.fresh_gate();answer=provider.provide(binding,evidence,phase=phase,root_start=True)
    assert set(answer)=={'np','pd','minimize','expit','actual_owner','fresh_origin_proof','fresh_origin_proof_sha256','actual_origin_receipt_sha256'}
    proof=answer['fresh_origin_proof'];assert rc.digest(rc.canonical(proof))==answer['fresh_origin_proof_sha256']
    assert proof['status']==c.runtime.PROVIDER_STATUS and proof['stage']==c.STAGE and proof['provider_phase']==phase
    assert proof['current_pid']==os.getpid() and proof['parent_pid']==os.getppid() and proof['caller_birth_sha256']==evidence['birth_sha256']
    assert proof['request_binding']==binding and proof['fresh_current_python_and_loaded_native_origins_checked'] is True
    assert proof['invented_only'] is False and proof['optimizer_calls']==0 and proof['runtime_and_FIT_authority_granted_here'] is False
    return answer


def evaluate_once(session,generation,run_sha,birth_sha,evidence):
    run=c.read_run(generation,run_sha,check_commit=True);manifest=c.verify_sources(generation)
    raw={name:inputs.read_bound(name,want) for name,want in run['input_pins'].items()};obj={name:c.decode(value) for name,value in raw.items()}
    c.source_admission_contract(obj[c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix()],generation,manifest)
    request=obj[c.REQUEST];binding=runtime_binding(request,run['input_pins'][c.REQUEST],manifest)
    static_contract(obj[c.STATIC_BINDING],request,run,generation,manifest)
    prefit=obj[c.PREFIT];view=dict(prefit);assert view['resource_exception_applies'] is True;view['resource_exception_applies']=False;lc.validate_prefit(view)
    for key,want in c.STABLE_SCIENTIFIC_BINDINGS.items():assert prefit['input_admission_bindings'][key]==want
    rows=obj[c.METADATA_BUNDLE]['metadata']['rows'];contract=reference.full_metadata_contract(rows)
    assert rc.canonical(contract)==rc.canonical(obj[c.METADATA_BUNDLE]['contract'])
    ids=inputs.persisted_label_contract(obj[c.METADATA_BUNDLE],obj[c.LABEL_CERTIFICATE],obj[c.LABEL_SUPERVISOR])
    effects=dict(zip(ids,obj[c.LABEL_CERTIFICATE]['labels_result']['measured_delta']))
    records=replay_contract(obj[c.REPLAY_REPORT],obj[c.REPLAY_COMPLETION],obj[c.REPLAY_SUPERVISOR],run,prefit,obj[c.PROJECTION_ADMISSION])
    before=accepted_runtime(binding,evidence,'before_evaluation')
    assert runtime_contract(before['np'],obj[c.ARRAY_CERTIFICATE]['runtime_acceptance_after_array'])==c.ARRAY_RUNTIME_ANCHOR_SHA
    c.check_live_inputs(generation,run_sha)
    result=evaluate(before['np'],rows,effects,records,probe=guard.live_resources,environment=os.environ)
    assert result['status'] in ('JOINT_KNOWN_CELL_DEVELOPMENT_GO','NO-GO') and result['model_fits_or_refits']==0
    after=accepted_runtime(binding,evidence,'after_evaluation')
    for name in ('np','pd','minimize','expit'):assert after[name] is before[name]
    assert after['actual_owner']==before['actual_owner'];c.check_live_inputs(generation,run_sha)
    guard.fresh_gate();storage=results_io.persist(result)
    report=session.annotate({'status':'ACTUAL_ONE_OWNED_COMPLETE_FROZEN_EVALUATION','stage':c.STAGE,'invocation':c.INVOCATION,
        'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'parent_pid':os.getppid(),'worker_pid':os.getpid(),'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,'replay_report_sha256':run['input_pins'][c.REPLAY_REPORT],
        'independent_replay_generation_manifest_sha256':c.REPLAY_EXECUTION_GENERATION_SHA,
        'actual_prefit_sha256':run['input_pins'][c.PREFIT],'saved_label_bits_sha256':c.LABEL_BITS_SHA,
        'CORE_reread':False,'actual_feature_reads':0,'new_pools':0,'new_optimizer_calls':0,'new_configuration_selection':False})
    protected={'runtime_acceptance':before['fresh_origin_proof'],'runtime_acceptance_after_evaluation':after['fresh_origin_proof'],
        'evaluation_summary':results_io.summary(result),'complete_evaluation_storage':storage,
        'original_evaluation_source_manifest_sha256':c.EVALUATION_READY_SHA}
    report.update(protected);report['protected_provenance_sha256']=c.sha(c.canonical(protected));return report


def run(parent_pid,generation,run_sha,birth_sha):
    evidence={'parent_pid':parent_pid,'birth_sha256':birth_sha,'run_admission_sha256':run_sha}
    c.admit_authorization(generation);c.verify_owner(c.STAGE,generation,evidence);c.read_run(generation,run_sha,check_commit=True)
    assert not c.OUTPUT.exists() and not c.COMPLETION.exists() and not c.EVALUATION_DATA.exists()
    from .calibration import calibrated
    from src.generalization_pum_process_probe_20261021 import headless
    with calibrated(c.STAGE,generation,evidence) as session:
        report=evaluate_once(session,generation,run_sha,birth_sha,evidence)
        c.verify_sources(generation);c.read_run(generation,run_sha);guard.fresh_gate();output_sha=c.save_new(c.OUTPUT,report)
    assert session.restored is True and session.calls>0
    c.verify_sources(generation);c.verify_owner(c.STAGE,generation,evidence);assert c.resource_failure(headless.memory(),0) is None
    c.save_new(c.COMPLETION,{'status':'PASS_COMPLETE_FROZEN_EVALUATION_WORKER_CALLBACKS_RESTORED',
        'invocation':c.INVOCATION,'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'parent_pid':parent_pid,'worker_pid':os.getpid(),'report_sha256':output_sha,'callbacks_restored':True,
        'fresh_calibrated_guard_calls':session.calls,'source_mode':c.source_mode(),'resource_policy':c.resource_policy(),
        'complete_evaluation_gzip_sha256':report['complete_evaluation_storage']['gzip_sha256'],
        'scientific_verdict':report['evaluation_summary']['status'],'new_optimizer_calls':0,'CORE_reread':False})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('parent_pid',type=int);parser.add_argument('generation');parser.add_argument('run_sha');parser.add_argument('birth_sha')
    args=parser.parse_args();assert os.getppid()==args.parent_pid
    with c.WORKER_LOG.open('x',encoding='utf8') as log:
        sys.stdout=sys.stderr=log
        try:run(args.parent_pid,args.generation,args.run_sha,args.birth_sha)
        except BaseException:traceback.print_exc();raise


if __name__=='__main__':main()
