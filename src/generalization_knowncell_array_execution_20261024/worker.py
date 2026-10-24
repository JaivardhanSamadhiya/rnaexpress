"""Run the unchanged array API/provider inside one owned resource session."""
import argparse
import os
import sys
import traceback
from . import common as c
from src.generalization_knowncell_array_admission_20261023 import admit as a


def metadata_prerequisite(report,supervisor):
    assert report['status']=='PASS_INDEPENDENT_METADATA_DERIVATION_AND_CONTRACT_WITH_OWNED_RAW_READ_PROOF'
    assert supervisor['status']=='PASS_SECOND_METADATA_EXECUTION_REQUIRES_REVIEW_AND_COMMIT'
    assert supervisor['failure'] is None
    assert supervisor['independent_report_sha256']==c.INDEPENDENT_REPORT_SHA
    assert report['generation_manifest_sha256']==supervisor['generation_manifest_sha256']==c.INDEPENDENT_GENERATION_SHA
    assert report['run_admission_sha256']==supervisor['run_admission_sha256']
    assert report['birth_sha256']==supervisor['birth_sha256']
    assert report['outer_raw_CORE_SHA_verified_against_frozen_admission'] is True
    assert report['each_acquisition_input_committed_bytes_checked'] is True
    assert report['array_label_or_FIT_permission_granted'] is False
    assert report['numerical_outcomes_admitted']==report['actual_feature_reads']==report['model_fits']==0
    assert report['acquisition_input_hashes'][a.METADATA_BUNDLE]==c.METADATA_BUNDLE_SHA
    independent=report['independent_verification']
    assert independent['status']==c.prior.HELPER_STATUS
    assert independent['counts']==c.prior.HELPER_COUNTS
    assert independent['row_ids_sha256']==a.ROW_IDS_SHA
    assert independent['outer_masks_rebuilt']==3 and independent['inner_masks_rebuilt']==6
    for key in ('source_CSV_metadata_derivation_independently_verified',
        'original_core_position_alignment_independently_verified','nonMikl_full_core_ID_roster_independently_verified',
        'both_cells_used_for_every_purge','source_and_target_full_menus_preserved','original_row_order_preserved'):
        assert independent[key] is True,key


def assemble(session,result,generation,run_sha,birth_sha):
    # Protect exact fresh runtime proof hashes and the validator's report.
    # Annotate only actual IO resource provenance, not immutable proof objects.
    normalized=c.decode(c.canonical(result))
    assert c.canonical(normalized)==c.canonical(result)
    protected={name:normalized.pop(name) for name in ('runtime_acceptance','runtime_acceptance_after_array')}
    original_report_sha=c.sha(c.canonical(normalized['underlying_report']))
    assert normalized['resource_exception_applies'] is False
    normalized['resource_exception_applies']=True
    annotated=session.annotate(normalized)
    annotated.update(protected)
    annotated['underlying_report_before_resource_annotation_sha256']=original_report_sha
    annotated['invocation']=c.INVOCATION
    annotated['generation_manifest_sha256']=generation
    annotated['run_admission_sha256']=run_sha
    annotated['birth_sha256']=birth_sha
    annotated['approved_policy_manifest_sha256']=c.POLICY_SHA
    annotated['authorization_sha256']=c.AUTH_SHA
    annotated['approval_scope_sha256']=c.SCOPE_SHA
    annotated['parent_pid']=os.getppid()
    annotated['worker_pid']=os.getpid()
    annotated['independent_metadata_report_sha256']=c.INDEPENDENT_REPORT_SHA
    annotated['protected_runtime_payloads_sha256']=c.sha(c.canonical(protected))
    return annotated


def run(parent_pid,generation,run_sha,birth_sha):
    evidence={'parent_pid':parent_pid,'birth_sha256':birth_sha,'run_admission_sha256':run_sha}
    c.admit_authorization(generation);c.verify_owner(c.STAGE,generation,evidence)
    admission=c.read_run(generation,run_sha,check_commit=True)
    assert not os.path.lexists(c.OUTPUT) and not os.path.lexists(c.COMPLETION)
    from .calibration import calibrated
    from src.generalization_knowncell_joint_loader_20261022 import guard
    from src.generalization_knowncell_runtime_provider_20261023.provider import provide
    from src.generalization_pum_process_probe_20261021 import headless
    with calibrated(c.STAGE,generation,evidence) as session:
        captured={}
        for name in (c.REQUEST,c.INDEPENDENT_REPORT,c.INDEPENDENT_SUPERVISOR):
            raw=guard.guarded_bytes(c.relative(name),maximum=64*2**20)
            assert c.sha(raw)==admission['input_pins'][name]
            guard.fresh_gate();c.committed(c.relative(name),raw)
            captured[name]=c.decode(raw)
        metadata_prerequisite(captured[c.INDEPENDENT_REPORT],captured[c.INDEPENDENT_SUPERVISOR])
        matrix,result=a.admit_simple102(provide,root_start=True)
        assert matrix.shape==(13781,102) and result['models_fitted']==0
        certificate=assemble(session,result,generation,run_sha,birth_sha)
        validate_certificate(certificate,generation,run_sha,birth_sha)
        c.verify_sources(generation);c.read_run(generation,run_sha)
        guard.fresh_gate();output_sha=c.save_new(c.OUTPUT,certificate)
        del matrix
    assert session.restored is True and session.calls>0
    c.verify_sources(generation);c.verify_owner(c.STAGE,generation,evidence)
    assert c.resource_failure(headless.memory(),0) is None
    c.save_new(c.COMPLETION,{'status':'PASS_EXACT_ARRAY_WORKER_CALLBACKS_RESTORED',
        'invocation':c.INVOCATION,'generation_manifest_sha256':generation,
        'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,
        'approval_scope_sha256':c.SCOPE_SHA,'parent_pid':parent_pid,'worker_pid':os.getpid(),
        'certificate_sha256':output_sha,'callbacks_restored':True,'fresh_calibrated_guard_calls':session.calls,
        'source_mode':c.source_mode(),'resource_policy':c.resource_policy(),
        'numerical_outcomes_admitted':0,'model_fits':0,'array_reads':1})


def validate_certificate(value,generation,run_sha,birth_sha):
    assert value['status']==a.STATUS and value['invocation']==c.INVOCATION
    assert value['generation_manifest_sha256']==generation and value['run_admission_sha256']==run_sha
    assert value['birth_sha256']==birth_sha and value['approved_policy_manifest_sha256']==c.POLICY_SHA
    assert value['authorization_sha256']==c.AUTH_SHA and value['approval_scope_sha256']==c.SCOPE_SHA
    assert value['independent_metadata_report_sha256']==c.INDEPENDENT_REPORT_SHA
    assert value['actual_npz_sha256']==a.NPZ_SHA and value['metadata_bundle_sha256']==c.METADATA_BUNDLE_SHA
    assert value['rows']==13781 and value['columns']==102 and value['same_allele_feature_bytes_equal'] is True
    assert value['original_row_ids_sha256']==a.ROW_IDS_SHA
    assert value['original_resource_guards_unchanged'] is False and value['resource_exception_applies'] is True
    assert value['numeric_labels_admitted'] is value['FIT_admission_granted'] is False
    assert value['models_fitted']==0
    assert value['array_request_sha256']==c.read_run(generation,run_sha)['input_pins'][c.REQUEST]
    assert value['source_readiness_sha256']==c.ARRAY_READY_SHA
    assert value['array_acquisition']['actual_sha256']==a.NPZ_SHA
    assert value['array_acquisition']['fresh_original_resource_gate_before_open'] is False
    protected={name:value[name] for name in ('runtime_acceptance','runtime_acceptance_after_array')}
    assert c.sha(c.canonical(protected))==value['protected_runtime_payloads_sha256']
    c.valid_sha(value['underlying_report_before_resource_annotation_sha256'])
    annotated_report=dict(value['underlying_report'])
    assert annotated_report.pop('calibrated_resource_gates_checked')==2
    annotated_report['fresh_original_resource_gates_checked']=2
    assert c.sha(c.canonical(annotated_report))==value['underlying_report_before_resource_annotation_sha256']
    for phase,key in (('before_array','runtime_acceptance'),('after_array','runtime_acceptance_after_array')):
        proof=value[key]
        assert proof['status']==a.PROVIDER_STATUS and proof['phase']==phase
        assert proof['request_binding']['request_sha256']==value['array_request_sha256']
        assert proof['request_binding']['provider_preparation_manifest_sha256']==c.PROVIDER_PREPARATION_SHA
        assert proof['fresh_current_python_and_loaded_native_origins_checked'] is True
        assert proof['invented_only'] is False and proof['model_fits']==0
        assert proof['numpy_version']=='1.26.4' and proof['source_cache_remained_absent'] is True
    runtime_sha=a.sha(a.canonical(value['runtime_acceptance']))
    a.validate_report(value['underlying_report'],runtime_sha,value['underlying_report']['creation_identity']['supplied_metadata_sha256'])
    assert value['underlying_report']['creation_identity']['supplied_metadata_sha256']=='b20281b69b3360a1e60197f5c7ed01d105642a5e79c9fb0ee4cd76001d8f2795'
    calibration=value['resource_calibration']
    assert calibration['stage']==c.STAGE and calibration['execution_manifest_sha256']==generation
    assert calibration['authorization_sha256']==c.AUTH_SHA and calibration['birth_sha256']==birth_sha
    assert calibration['scientific_protocol_settings_changed'] is False
    assert calibration['current_pid']==value['worker_pid'] and calibration['parent_pid']==value['parent_pid']
    return value


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
