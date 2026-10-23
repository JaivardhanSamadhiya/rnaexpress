"""Additive prospective source freeze preserving the original 50-pin layer."""
import ast
from datetime import datetime,timezone
from pathlib import Path
from .contracts import canonical_bytes,digest,strict_json
from .spec import NS

ROOT=Path(__file__).resolve().parents[2]
SRC,REP,OUT=[ROOT/name/NS for name in ('src','reports','results')]


def run():
    old_path=OUT/'preparation_manifest.json';old=strict_json(old_path.read_bytes())
    assert old['status']=='SOURCE_FROZEN_LIFECYCLE_INFRASTRUCTURE_NOT_PROJECT_PREFIT_OR_EXECUTION_AUTHORIZATION'
    pins={}
    for name,want in old['files'].items():
        assert digest((ROOT/name).read_bytes())==want,name
        pins[name]=want
    assert len(pins)==50
    pins[old_path.relative_to(ROOT).as_posix()]=digest(old_path.read_bytes())
    receipt_path=OUT/'synthetic_tests_receipt_v2.json';receipt=strict_json(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_FAIL_CLOSED_LIFECYCLE_V2_NOT_SCIENTIFIC_CAMPAIGN'
    assert receipt['scientific_imports'] is False and receipt['native_optimizer_calls']==receipt['models_fitted']==0
    assert receipt['project_metadata_reads']==receipt['project_feature_reads']==receipt['project_outcome_reads']==0
    sources=sorted(SRC.glob('*.py'))
    assert receipt['source_files']=={path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in sources}
    for path in sources:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    own=[SRC/name for name in ('writer_v2.py','tests_v2.py','prepare_v2.py')]+[REP/'prospective_writer_v2.md',receipt_path]
    pins.update({path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in own})
    payload={'status':'PROSPECTIVE_FAIL_CLOSED_WRITER_V2_SOURCE_NOT_PROJECT_EXECUTION_ADMISSION',
             'generated_utc':datetime.now(timezone.utc).isoformat(),'files':pins,
             'original50pins_preserved':True,'original_manifest_sha256':digest(old_path.read_bytes()),
             'required_campaign_class':'src.generalization_knowncell_joint_campaign_20261023.writer_v2.Campaign',
             'any_write_checkpoint_exception_poisons_run':True,'campaign_birth_checked_before_new_callback':True,
             'checkpoint_count':63,'optimizer_units':84,'source_pool_count':9,
             'scientific_imports':False,'native_optimizer_calls':0,'models_fitted':0,
             'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,
             'all_old_resource_guards_unchanged':True,'resource_exception_applies':False,
             'project_trainer_numerical_replay_or_gate_claim':False,
             'root_commit_and_separate_execution_admission_required':True}
    path=OUT/'preparation_manifest_v2.json'
    with path.open('xb') as stream:stream.write(canonical_bytes(payload))
    print('PROSPECTIVE_WRITER_V2_READY',len(pins),digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
