"""Operational JSON admission builder; requires a real committed new answer.

No worker, provider, data array, pool or optimizer is invoked. This script
never creates human approval and cannot authorize an additional attempt.
"""
from pathlib import Path
from src.generalization_knowncell_fit_roomy_execution_20261025 import common as c,worker
from src.generalization_knowncell_fit_roomy_runtime_20261025 import contracts as runtime_contracts
from src.generalization_knowncell_calibrated_input_bridge_20261024 import contracts_v3 as bridge_contracts
from src.generalization_github_publication_20261009.publish import protect

GENERATION='f9ece623e5ddff75f069832fe6c389fa1e6e2ddaf6cbf3fed57aaa730483a12f'
OLD=c.ROOT/'results/generalization_knowncell_fit_retry_execution_20261025'


def main():
    assert protect()==33
    c.admit_authorization(GENERATION)  # Exact NEW actual answer, scope and committed bytes.
    manifest=c.verify_sources(GENERATION)
    for path in (c.SOURCE_ADMISSION,c.ROOT/c.STATIC_BINDING,c.ROOT/c.REQUEST,c.RUN_ADMISSION):
        assert not path.exists(),path
    c.require_new_outputs()
    actual_auth_sha=c.sha(c.RETRY_AUTH.read_bytes())
    source=c.decode((OLD/'controller_source_admission.json').read_bytes())
    source.update(generation_manifest_sha256=GENERATION,controller_source=c.WORKER_SOURCE,
        controller_source_sha256=manifest['files'][c.WORKER_SOURCE],
        runtime_provider_preparation_sha256=manifest['files'][c.runtime.PREPARATION],
        bridge_readiness_sha256=manifest['files'][c.BRIDGE_READY])
    c.source_admission_contract(source,GENERATION,manifest)
    source_sha=c.sha(c.canonical(source))
    static=c.decode((c.ROOT/'results/generalization_knowncell_calibrated_input_bridge_20261024/root_bindings_v4_fit_retry_20261025.json').read_bytes())
    static.update(reviewed_controller_source=c.WORKER_SOURCE,
        reviewed_controller_source_sha256=manifest['files'][c.WORKER_SOURCE],
        reviewed_controller_admission_sha256=source_sha,
        bridge_readiness_sha256=manifest['files'][c.BRIDGE_READY])
    bridge_contracts.binding_contract(static)
    static_sha=c.sha(c.canonical(static))
    request=c.decode((OLD/'fit_runtime_request.json').read_bytes())
    request.update(namespace=c.NS,generation_manifest_sha256=GENERATION,
        provider_preparation_manifest_sha256=manifest['files'][c.runtime.PREPARATION],
        controller_source_admission_sha256=source_sha,static_root_binding_sha256=static_sha,
        retry_authorization_sha256=actual_auth_sha)
    request['provider_binding'].update(module=c.runtime.MODULE,source_path=c.runtime.SOURCE,
        source_sha256=manifest['files'][c.runtime.SOURCE])
    binding=worker.runtime_binding(request,c.sha(c.canonical(request)),manifest)
    runtime_contracts.request_contract(request,binding,manifest['files'][c.runtime.SOURCE])
    run=c.decode((OLD/'run_admission.json').read_bytes())
    run.pop('failed_supervisor_sha256')
    old_paths={
        (OLD/'controller_source_admission.json').relative_to(c.ROOT).as_posix(),
        (OLD/'fit_runtime_request.json').relative_to(c.ROOT).as_posix(),
        'results/generalization_knowncell_calibrated_input_bridge_20261024/root_bindings_v4_fit_retry_20261025.json',
    }
    run['input_pins']={name:want for name,want in run['input_pins'].items() if name not in old_paths}
    run['input_pins'].update({c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix():source_sha,
        c.STATIC_BINDING:static_sha,c.REQUEST:c.sha(c.canonical(request))})
    run.update(generation_manifest_sha256=GENERATION,retry_authorization_sha256=actual_auth_sha,
        interrupted_attempt_audit_sha256=c.INTERRUPTED_AUDIT_SHA,managed_supervisor_required=True,
        minimum_startup_physical_available=c.RETRY_STARTUP_PHYSICAL)
    c.run_contract(run,GENERATION)
    worker.static_contract(static,request,run,source,GENERATION,manifest)
    for name,want in run['input_pins'].items():
        if name in (c.SOURCE_ADMISSION.relative_to(c.ROOT).as_posix(),c.STATIC_BINDING,c.REQUEST):continue
        assert c.sha((c.ROOT/name).read_bytes())==want,name
    assert c.save_new(c.SOURCE_ADMISSION,source)==source_sha
    assert c.save_new(c.ROOT/c.STATIC_BINDING,static)==static_sha
    request_sha=c.save_new(c.ROOT/c.REQUEST,request)
    assert request_sha==run['input_pins'][c.REQUEST]
    run_sha=c.save_new(c.RUN_ADMISSION,run)
    assert c.read_run(GENERATION,run_sha)==run
    assert protect()==33
    print('EXACT_ADMISSIONS_CREATED_NO_PROVIDER_OR_FIT',run_sha,flush=True)


if __name__=='__main__':main()
