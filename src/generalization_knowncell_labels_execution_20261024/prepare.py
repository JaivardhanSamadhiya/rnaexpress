"""Freeze labels execution source; never read actual metadata/array/labels."""
import ast
from pathlib import Path
import sys
from . import common as c


def run():
    assert not c.RUN_ADMISSION.exists() and not (c.ROOT/c.REQUEST).exists()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for name in sys.modules)
    pins={}
    dependencies=[(c.policy.MANIFEST.relative_to(c.ROOT).as_posix(),c.POLICY_SHA),
                  (c.runtime.PREPARATION,c.RUNTIME_PREPARATION_SHA)]
    for name,want in dependencies:
        raw=c.relative(name).read_bytes();actual=c.sha(raw)
        assert want is None or actual==want,name
        document=c.decode(raw)
        for path,expected in document['files'].items():
            assert c.sha(c.relative(path).read_bytes())==expected,path
            assert path not in pins or pins[path]==expected
            pins[path]=expected
        pins[name]=actual
    # These source-only helper imports postdate the original resource proposal.
    # Actual metadata reports, array certificates and CORE/NPZ are NOT opened.
    for namespace in ('generalization_knowncell_metadata_verification_execution_20261024',
                      'generalization_knowncell_array_admission_20261023'):
        for path in (c.ROOT/'src'/namespace).glob('*.py'):
            pins[path.relative_to(c.ROOT).as_posix()]=c.sha(path.read_bytes())
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    test_path=c.OUT/'synthetic_tests_receipt_reviewed.json';test=c.decode(test_path.read_bytes())
    assert test['status']=='PASS_INVENTED_ORIGINAL_PARSER_LABEL_EXECUTION_NOT_ACTUAL_ADMISSION'
    assert test['tests']>=12
    assert test['sources']=={path.relative_to(c.ROOT).as_posix():c.sha(path.read_bytes()) for path in sources}
    for key in ('actual_jobs','actual_resource_probes','actual_provider_invocations','project_payload_reads','label_rows_admitted','model_fits'):
        assert test[key]==0
    assert test['scientific_imports'] is False
    own=sources+[c.ROOT/folder/c.NS/'.gitattributes' for folder in ('src','reports','results','artifacts')]
    own += [test_path,c.OUT/'synthetic_tests_receipt.json',c.ROOT/'reports'/c.NS/'protocol.md']
    for path in own:
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw.decode('utf8'))
        pins[path.relative_to(c.ROOT).as_posix()]=c.sha(raw)
    for name in list(pins):
        if name.startswith('src/') and name.endswith('.py'):
            parent=c.relative(name).parent
            while parent.is_relative_to(c.ROOT/'src'):
                init=parent/'__init__.py'
                if init.is_file():pins[init.relative_to(c.ROOT).as_posix()]=c.sha(init.read_bytes())
                parent=parent.parent
    original=c.decode(c.policy.MANIFEST.read_bytes())
    for name,want in original['python_native_files'].items():assert c.sha(Path(name).read_bytes())==want
    c.save_new(c.MANIFEST,{'status':c.STATUS,'invocation':c.INVOCATION,'files':pins,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'resource_policy':c.resource_policy(),
        'python_executable':original['python_executable'],'python_native_files':original['python_native_files'],
        'runtime_provider_preparation_sha256':pins[c.runtime.PREPARATION],
        'expected_actual_array_certificate_sha256':c.ARRAY_CERTIFICATE_SHA,
        'expected_actual_array_supervisor_sha256':c.ARRAY_SUPERVISOR_SHA,
        'expected_actual_array_generation_sha256':c.ARRAY_GENERATION_SHA,
        'actual_source_preparation_payload_reads':0,'actual_provider_invocations':0,'actual_jobs':0,
        'actual_resource_probes':0,'actual_label_rows_admitted':0,'model_fits':0,
        'actual_request_or_input_admission_created':False,'original_frozen_sources_changed':False,
        'frozen_original_parser_and_float64_hash_semantics_preserved':True,
        'labels_certificate_persists_original_vector_tolist_and_exact_bit_hash':True,
        'future_committed_request_input_admission_and_owned_controller_required':True,
        'old_original_guard_true_only_bridge_not_used_or_modified':True})
    print('LABELS_EXECUTION_SOURCE_READY',len(pins),c.sha(c.MANIFEST.read_bytes()),flush=True)


if __name__=='__main__':run()
