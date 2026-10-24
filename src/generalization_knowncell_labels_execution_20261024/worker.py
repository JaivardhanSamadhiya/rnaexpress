"""One root-authorized original-pandas label admission; never an optimizer."""
import argparse
import os
import sys
import traceback
from . import common as c
from .admit import load_labels,validate_certificate


def run(parent_pid,generation,run_sha,birth_sha):
    evidence={'parent_pid':parent_pid,'birth_sha256':birth_sha,'run_admission_sha256':run_sha}
    c.admit_authorization(generation);c.verify_owner(c.STAGE,generation,evidence)
    c.read_run(generation,run_sha,check_commit=True)
    assert not os.path.lexists(c.OUTPUT) and not os.path.lexists(c.COMPLETION)
    from .calibration import calibrated
    from src.generalization_knowncell_joint_loader_20261022 import guard
    from src.generalization_pum_process_probe_20261021 import headless
    with calibrated(c.STAGE,generation,evidence) as session:
        certificate=load_labels(session,generation,run_sha,birth_sha)
        validate_certificate(certificate,generation,run_sha,birth_sha)
        c.verify_sources(generation);c.read_run(generation,run_sha)
        guard.fresh_gate();output_sha=c.save_new(c.OUTPUT,certificate)
    assert session.restored is True and session.calls>0
    c.verify_sources(generation);c.verify_owner(c.STAGE,generation,evidence)
    assert c.resource_failure(headless.memory(),0) is None
    c.save_new(c.COMPLETION,{'status':'PASS_EXACT_LABELS_WORKER_CALLBACKS_RESTORED',
        'invocation':c.INVOCATION,'generation_manifest_sha256':generation,'run_admission_sha256':run_sha,
        'birth_sha256':birth_sha,'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,
        'parent_pid':parent_pid,'worker_pid':os.getpid(),'certificate_sha256':output_sha,
        'callbacks_restored':True,'fresh_calibrated_guard_calls':session.calls,
        'source_mode':c.source_mode(),'resource_policy':c.resource_policy(),
        'numerical_outcomes_admitted':c.COUNT,'model_fits':0,'core_label_reads':1,
        'parsed_effects_float64_sha256':certificate['labels_result']['parsed_effects_float64_sha256']})


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
