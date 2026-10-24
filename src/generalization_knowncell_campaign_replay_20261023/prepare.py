"""Source/static predecessor freeze only; never invokes supplied-data replay."""
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_knowncell_campaign_replay_20261023'
PRIOR={
    'results/generalization_knowncell_joint_engine_20261023/preparation_manifest_v2.json':
        '109a2bd1cd7e1b62f5a7607d67b3cd5da75192e4dfb9af46b1e5cb8b0fc7436e',
    'results/generalization_knowncell_joint_replay_20261023/preparation_manifest.json':
        'cc529a521fe3b91f83431c81119d786d13ad9d2ebf271a2a615031eb3278175d',
}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    pins={}
    def add(name,expected=None):
        assert name==name.replace('\\','/') and not name.startswith('/') and ':' not in name and '..' not in name.split('/')
        assert name.startswith(('src/','reports/','results/','artifacts/')) and name.endswith(('.py','.md','.json','/.gitattributes'))
        actual=sha(ROOT/name)
        assert expected is None or actual==expected,name
        assert name not in pins or pins[name]==actual,'Conflicting frozen dependency'
        pins[name]=actual
    for name,expected in PRIOR.items():
        add(name,expected)
        for rel,want in json.loads((ROOT/name).read_bytes())['files'].items():add(rel,want)
    for name in ('src/generalization_knowncell_joint_loader_20261022/guard.py',
                 'src/generalization_knowncell_joint_loader_20261022/spec.py'):
        add(name)
    # Parent files are imported software, not fabricated namespace-package pins.
    for name in list(pins):
        if name.startswith('src/') and name.endswith('.py'):
            parent=(ROOT/name).parent
            while parent.is_relative_to(ROOT/'src'):
                init=parent/'__init__.py'
                if init.is_file():add(init.relative_to(ROOT).as_posix())
                parent=parent.parent
    source=ROOT/'src'/NS
    sources=sorted(source.glob('*.py'))
    receipt_path=ROOT/'results'/NS/'synthetic_tests_receipt.json'
    receipt=json.loads(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_SUPPLIED63_REPLAY_CONTRACTS_WITH_PRIVATE_ARITHMETIC_STUBS_NOT_PROJECT_REPLAY'
    assert receipt['sources']=={path.relative_to(ROOT).as_posix():sha(path) for path in sources}
    assert receipt['scientific_imports'] is False
    assert receipt['actual_resource_probes']==receipt['project_payload_reads']==receipt['actual_optimizer_calls']==0
    assert receipt['actual63_native_arithmetic_replays']==receipt['actual_provider_or_worker_calls']==0
    for path in sources:
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path));add(path.relative_to(ROOT).as_posix())
    add(receipt_path.relative_to(ROOT).as_posix());add('reports/'+NS+'/protocol.md')
    for top in ('src','reports','results','artifacts'):add(top+'/'+NS+'/.gitattributes')
    manifest={'status':'DEFERRED_FULL_SUPPLIED63_REPLAY_SOURCE_NOT_ACTUAL_REPLAY_OR_INPUT_FIT_ADMISSION',
              'UTC':datetime.now(timezone.utc).isoformat(),'files':pins,
              'logical_checkpoint_roster':63,'logical_recorded_optimizer_units':84,
              'inner_checkpoints':54,'outer_reselections':9,'actual_native_replays_run':0,
              'public_dependencies_fixed':True,'original_arithmetic_tolerance':1e-9,
              'canonical_score_equality':'exact','new_optimizer_calls':0,'project_payload_reads':0,
              'runtime_or_stage_admission_granted':False,'public_replay_invoked':False,
              'source_preparation_tests_use_private_stubs_not_native_arithmetic':True,
              'physical_durability_Git_and_input_origin_proofs_remain_external':True}
    output=ROOT/'results'/NS/'preparation_manifest.json'
    with output.open('xb') as stream:stream.write((json.dumps(manifest,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
    print('SUPPLIED63_CAMPAIGN_REPLAY_SOURCE_READY',len(pins),sha(output),flush=True)


if __name__=='__main__':run()
