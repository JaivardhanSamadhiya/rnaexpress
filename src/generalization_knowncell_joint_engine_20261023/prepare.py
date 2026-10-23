"""Source-only preparation, never execute domain functions on real inputs."""
import ast
from datetime import datetime,timezone
from pathlib import Path
from .adapter import NS
from src.generalization_knowncell_joint_campaign_20261023.contracts import strict_json,digest,canonical_bytes

ROOT=Path(__file__).resolve().parents[2]
SRC,REP,OUT=[ROOT/name/NS for name in ('src','reports','results')]
LIFECYCLE='results/generalization_knowncell_joint_campaign_20261023/preparation_manifest_v2.json'


def run():
    prior=strict_json((ROOT/LIFECYCLE).read_bytes())
    assert prior['status']=='PROSPECTIVE_FAIL_CLOSED_WRITER_V2_SOURCE_NOT_PROJECT_EXECUTION_ADMISSION'
    pins={}
    for name,want in prior['files'].items():
        assert name==name.replace('\\','/') and not name.startswith('/') and ':' not in name and '..' not in name.split('/')
        if name.startswith('results/'):
            assert name.split('/')[1] in {'generalization_knowncell_joint_design_20261009','generalization_knowncell_joint_implementation_20261022',
                'generalization_knowncell_joint_numeric_20261022','generalization_knowncell_joint_campaign_20261023'}
        assert digest((ROOT/name).read_bytes())==want,name
        pins[name]=want
    pins[LIFECYCLE]=digest((ROOT/LIFECYCLE).read_bytes())
    receipt_path=OUT/'synthetic_tests_receipt.json';receipt=strict_json(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_DEFERRED_DOMAIN_ADAPTER_NOT_NATIVE_OR_PROJECT_ADMISSION'
    assert receipt['scientific_imports'] is False and receipt['native_optimizer_calls']==receipt['models_fitted']==0
    assert receipt['project_metadata_reads']==receipt['project_feature_reads']==receipt['project_outcome_reads']==0
    sources=sorted(SRC.glob('*.py'))
    assert receipt['source_files']=={path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in sources}
    for path in sources:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    own=sources+[SRC/'.gitattributes',REP/'.gitattributes',REP/'protocol.md',OUT/'.gitattributes',receipt_path]
    pins.update({path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in own})
    result={'status':'DEFERRED_DOMAIN_ADAPTER_SOURCE_NOT_NATIVE_PROFILE_PROJECT_PREFIT_OR_EXECUTION_ADMISSION',
            'generated_utc':datetime.now(timezone.utc).isoformat(),'files':pins,'shared_source_pools':9,
            'inner_checkpoints':54,'outer_checkpoints':9,'optimizer_units':84,'required_writer':'writer_v2.Campaign',
            'scientific_imports':False,'native_optimizer_calls':0,'models_fitted':0,
            'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,
            'actual_native_or_full_cohort_parity_certified':False,'all_original_3GiB_guards_unchanged':True,
            'resource_exception_applies':False,'full_campaign_cli_checkpoint_loop_replay_or_gate_implemented':False,
            'root_commit_and_separate_admission_required':True}
    path=OUT/'preparation_manifest.json'
    with path.open('xb') as stream:stream.write(canonical_bytes(result))
    print('DEFERRED_ENGINE_SOURCE_READY',len(pins),digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
