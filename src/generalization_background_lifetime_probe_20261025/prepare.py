"""Raw source/native fingerprint preparation; no native or scientific imports."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
NS=Path(__file__).parent.name
OUT=ROOT/'results'/NS
NATIVE={
    'python.exe':'4623dc531b0883c3e714da5cb30e9b73e12aa5145f0d92c7b191ab1dcf699dfe',
    'python3.dll':'f0d65efd7e2bc8f036d428de0db1b4743e5ebe51f133b7a6afd10d6913b7ce60',
    'python312.dll':'9930d881ee11a91f7fd43ab28d5305194fbd2f88ea4a07661453c6885f409afd'}


def run():
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    home=Path(sys.executable).resolve().parent
    assert str(home)=='C:\\Users\\jaisa\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python'
    natives={str(home/name):want for name,want in NATIVE.items()}
    for name,want in natives.items():assert sha(name)==want
    files={}
    own=list(Path(__file__).parent.iterdir())
    own+=[ROOT/'reports'/NS/'protocol.md',ROOT/'reports'/NS/'.gitattributes',
        ROOT/'results'/NS/'.gitattributes',ROOT/'artifacts'/NS/'.gitattributes',
        OUT/'synthetic_tests_receipt.json',
        OUT/'synthetic_tests_receipt_draft.json',OUT/'probe_before_source_review.txt',
        OUT/'synthetic_tests_receipt_before_namespace_fix.json',
        ROOT/'src/generalization_pum_process_probe_20261021/headless.py',
        ROOT/'src/generalization_pum_resource_calibration_20261009/winjob.py',
        ROOT/'src/generalization_owned_workingset_probe_v2_20261025/working_set.py',
        ROOT/'src/generalization_owned_workingset_probe_v2_20261025/__init__.py',ROOT/'src/__init__.py']
    for path in own:
        assert path.is_file() and not path.is_symlink()
        files[path.relative_to(ROOT).as_posix()]=sha(path)
    tested=json.loads((OUT/'synthetic_tests_receipt.json').read_bytes())
    assert tested['status']=='PASS_INVENTED_LIFETIME_AND_RESERVE_CONTRADICTIONS'
    assert tested['tests']==1 and tested['actual_jobs_native_probes_payload_reads_or_fits']==0
    assert tested['sources']=={p.relative_to(ROOT).as_posix():sha(p) for p in Path(__file__).parent.glob('*.py')}
    assert not any(n.split('.')[0] in ('numpy','pandas','scipy') for n in sys.modules)
    absent=['src/generalization_pum_process_probe_20261021/__init__.py',
        'src/generalization_pum_resource_calibration_20261009/__init__.py']
    assert all(not (ROOT/name).exists() for name in absent)
    value={'status':'FROZEN_INVENTED_BACKGROUND_LIFETIME_PROBE_NOT_SCIENTIFIC_ADMISSION','files':files,
        'required_absent_namespace_inits':absent,
        'python_executable':str(Path(sys.executable).resolve()),'python_version':sys.version,
        'python_native_files':natives,'new_native_fingerprints_for_this_stdlib_toy_only':True,
        'scientific_runtime_admission_granted':False,'biological_attempts':0,
        'duration_seconds':1080,'total_deadline_seconds':1140,'automatic_retry':False}
    with (OUT/'preparation_manifest.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n')
    print('FROZEN_BACKGROUND_TOY',len(files),sha(OUT/'preparation_manifest.json'))


if __name__=='__main__':run()
