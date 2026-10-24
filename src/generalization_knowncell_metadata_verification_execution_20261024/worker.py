"""No work at import; actual committed inputs only in the separately owned Job."""
import argparse
import os
import sys
import traceback
from . import common as c
from .inputs import verify_acquisition

HELPER_STATUS=c.HELPER_STATUS


def _bounded(binary,maximum):
    raw=binary.read(maximum+1);assert len(raw)<=maximum,'Bounded metadata/provenance input required'
    return raw


def _assemble_payload(session,operational,independent):
    # Pure scientific-verifier flags are not legacy resource claims. Keep the
    # entire independent result outside operational annotation and bind its
    # exact canonical JSON representation after assembly.
    protected=c.canonical(independent)
    result=session.annotate(c.json_normalized(operational))
    assert 'independent_verification' not in result
    result['independent_verification']=c.json_normalized(independent)
    assert c.canonical(result['independent_verification'])==protected
    result['independent_verifier_canonical_sha256']=c.sha(protected)
    return result


def run(parent_pid,generation_sha,run_sha,birth_sha):
    evidence={'parent_pid':parent_pid,'birth_sha256':birth_sha,'run_admission_sha256':run_sha}
    c.admit_authorization(generation_sha);c.verify_owner('metadata',generation_sha,evidence)
    admission=c.read_run(generation_sha,run_sha,check_commit=True)
    assert not os.path.lexists(c.REPORT) and not os.path.lexists(c.COMPLETION)
    from .calibration import calibrated
    from src.generalization_pum_process_probe_20261021 import headless
    with calibrated('metadata',generation_sha,evidence) as session:
        from src.generalization_knowncell_joint_loader_20261022 import guard
        from src.generalization_knowncell_metadata_independent_20261023.source_verify import verify_bundle_and_core
        raw_inputs={};read_proofs={}
        for key,path in c.INPUT_PATHS.items():
            maximum=64*2**20 if key=='bundle' else 16*2**20
            raw,proof=guard.guarded_payload(c.relative(path),admission['input_pins'][path],
                                           lambda stream:_bounded(stream,maximum))
            guard.fresh_gate();c.committed(c.relative(path),raw)
            raw_inputs[key]=raw;read_proofs[key]=proof
        bundle=verify_acquisition(raw_inputs,admission)
        result,core_proof=guard.guarded_payload(c.relative(c.CORE),c.CORE_SHA,
                          lambda stream:verify_bundle_and_core(bundle,stream),text=True)
        assert result['status']==HELPER_STATUS and result['parsed_outcome_values']==result['model_fits']==0
        assert result['source_CSV_metadata_derivation_independently_verified'] is True
        assert result['original_core_position_alignment_independently_verified'] is True
        assert result['nonMikl_full_core_ID_roster_independently_verified'] is True
        assert result['raw_CORE_byte_SHA_proven_here'] is False
        assert core_proof['actual_sha256']==c.CORE_SHA
        assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','openvino','sklearn') for name in sys.modules)
        payload={'status':'PASS_INDEPENDENT_METADATA_DERIVATION_AND_CONTRACT_WITH_OWNED_RAW_READ_PROOF',
            'invocation':c.INVOCATION,'category':'metadata','generation_manifest_sha256':generation_sha,
            'parent_pid':parent_pid,'worker_pid':os.getpid(),
            'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,
            'approval_scope_sha256':c.SCOPE_SHA,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
            'acquisition_input_hashes':dict(admission['input_pins']),
            'acquisition_source_generation_sha256':admission['acquisition_generation_manifest_sha256'],
            'independent_helper_source_manifest_sha256':c.HELPER_MANIFEST_SHA,
            'each_acquisition_input_committed_bytes_checked':True,
            'payload_reads':read_proofs,'core_read':core_proof,
            'outer_raw_CORE_SHA_verified_against_frozen_admission':True,'canonical_scientific_values_preserved':True,
            'array_label_or_FIT_permission_granted':False,'numerical_outcomes_admitted':0,'actual_feature_reads':0,'model_fits':0}
        # JSON boundary normalization preserves canonical tuple/list meaning;
        # the unchanged receipt adapter only accepts actual JSON data.
        payload=_assemble_payload(session,payload,result)
        c.verify_sources(generation_sha);c.read_run(generation_sha,run_sha)
        assert c.resource_failure(headless.memory(),0) is None
        report_sha=c.save_new(c.REPORT,payload)
    assert session.restored is True and session.calls>0
    c.verify_sources(generation_sha);c.verify_owner('metadata',generation_sha,evidence)
    assert c.resource_failure(headless.memory(),0) is None
    c.save_new(c.COMPLETION,{
        'status':'PASS_SECOND_METADATA_WORKER_INDEPENDENT_CONTRACT_CALLBACKS_RESTORED',
        'invocation':c.INVOCATION,'category':'metadata','generation_manifest_sha256':generation_sha,
        'parent_pid':parent_pid,'worker_pid':os.getpid(),
        'approved_policy_manifest_sha256':c.POLICY_SHA,'authorization_sha256':c.AUTH_SHA,
        'approval_scope_sha256':c.SCOPE_SHA,'run_admission_sha256':run_sha,'birth_sha256':birth_sha,
        'independent_report_sha256':report_sha,'callbacks_restored':True,'fresh_calibrated_guard_calls':session.calls,
        'independent_helper_source_manifest_sha256':c.HELPER_MANIFEST_SHA,
        'independent_helper_result_canonical_sha256':payload['independent_verifier_canonical_sha256'],
        'metadata_counts':result['counts'],'row_ids_sha256':result['row_ids_sha256'],
        'metadata_sha256':result['metadata_sha256'],'all_core_ids_sha256':result['all_core_ids_sha256'],
        'numerical_outcomes_admitted':0,'actual_feature_reads':0,'model_fits':0,'scientific_packages_imported':False,
        'original_3GiB_resource_guard_unchanged':False,'source_mode':c.source_mode(),'resource_policy':c.resource_policy()})
    c.verify_sources(generation_sha)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('parent_pid',type=int)
    parser.add_argument('generation_sha');parser.add_argument('run_sha');parser.add_argument('birth_sha')
    args=parser.parse_args();assert os.getppid()==args.parent_pid
    evidence={'parent_pid':args.parent_pid,'birth_sha256':args.birth_sha,'run_admission_sha256':args.run_sha}
    c.admit_authorization(args.generation_sha);c.verify_owner('metadata',args.generation_sha,evidence)
    with c.WORKER_LOG.open('x',encoding='utf8') as log:
        sys.stdout=sys.stderr=log
        try:run(args.parent_pid,args.generation_sha,args.run_sha,args.birth_sha)
        except BaseException:traceback.print_exc();raise


if __name__=='__main__':main()
