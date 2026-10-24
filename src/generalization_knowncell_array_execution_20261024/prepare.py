"""Freeze reviewed source closure without opening actual biological payloads."""
import ast
import sys
from pathlib import Path
from . import common as c


def run():
    assert not c.RUN_ADMISSION.exists() and not (c.ROOT/c.REQUEST).exists()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn') for name in sys.modules)
    pins={}
    dependencies=[(c.prior.MANIFEST.relative_to(c.ROOT).as_posix(),c.INDEPENDENT_GENERATION_SHA),
        (c.array.READY,c.ARRAY_READY_SHA),(c.PROVIDER_PREPARATION,c.PROVIDER_PREPARATION_SHA)]
    for name,want in dependencies:
        raw=c.relative(name).read_bytes();assert c.sha(raw)==want
        document=c.decode(raw)
        for path,expected in document['files'].items():
            assert c.sha(c.relative(path).read_bytes())==expected,path
            assert path not in pins or pins[path]==expected
            pins[path]=expected
        pins[name]=want
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    test_path=c.OUT/'synthetic_tests_receipt.json'
    tests=c.decode(test_path.read_bytes())
    assert tests['status']=='PASS_INVENTED_ARRAY_EXECUTION_CONTRACT_TESTS'
    assert tests['source_files']=={p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources}
    assert tests['actual_jobs']==tests['actual_resource_probes']==tests['project_payload_reads']==tests['models_fitted']==0
    assert tests['scientific_runtimes_imported'] is False
    own=sources+[c.ROOT/folder/c.NS/'.gitattributes' for folder in ('src','reports','results')]
    own += [test_path,c.OUT/'synthetic_tests_attempt_01.log',c.OUT/'synthetic_tests_attempt_02.log',
        c.OUT/'draft_source_attempt_01.json',c.ROOT/'reports'/c.NS/'protocol.md']
    for path in own:
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw.decode('utf8'))
        pins[path.relative_to(c.ROOT).as_posix()]=c.sha(raw)
    original=c.decode(c.policy.MANIFEST.read_bytes())
    for name,want in original['python_native_files'].items():assert c.sha(Path(name).read_bytes())==want
    c.save_new(c.MANIFEST,{'status':c.STATUS,'invocation':c.INVOCATION,'files':pins,
        'approved_policy_manifest_sha256':c.POLICY_SHA,'resource_policy':c.resource_policy(),
        'python_executable':original['python_executable'],'python_native_files':original['python_native_files'],
        'actual_project_payloads_opened':0,'actual_resource_probes':0,'actual_jobs':0,'models_fitted':0,
        'actual_array_request_created':False,'actual_input_admission_created':False,
        'source_generation_distinct_from_human_approved_resource_policy':True})
    print('ARRAY_EXECUTION_SOURCE_FROZEN',len(pins),c.sha(c.MANIFEST.read_bytes()),flush=True)


if __name__=='__main__':run()
