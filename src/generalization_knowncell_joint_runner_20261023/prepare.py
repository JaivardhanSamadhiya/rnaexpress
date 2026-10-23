"""Source/test-only freeze of finite orchestration and unchanged dependencies."""
import ast
from pathlib import Path
import sys
from src.generalization_knowncell_joint_campaign_20261023.contracts import canonical_bytes,digest,strict_json

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_knowncell_joint_runner_20261023'
SRC,REP,OUT=[ROOT/part/NS for part in ('src','reports','results')]
DEPENDENCIES=(
 'results/generalization_knowncell_joint_campaign_20261023/preparation_manifest_v2.json',
 'results/generalization_knowncell_joint_engine_20261023/preparation_manifest_v2.json',
)


def run():
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    pins={}
    for name in DEPENDENCIES:
        path=ROOT/name;raw=path.read_bytes();document=strict_json(raw)
        for relative,want in document['files'].items():
            assert digest((ROOT/relative).read_bytes())==want,relative
            assert relative not in pins or pins[relative]==want
            pins[relative]=want
        pins[name]=digest(raw)
    receipt_path=OUT/'synthetic_tests_receipt_reviewed.json';receipt=strict_json(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_FINITE_RUNNER_STUBS_NOT_NATIVE_OR_PROJECT_CAMPAIGN' and receipt['tests']==11
    sources=sorted(SRC.glob('*.py'))
    assert receipt['source_files']=={path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in sources}
    for path in sources:ast.parse(path.read_text(encoding='utf-8'))
    own=sources+[SRC/'.gitattributes',REP/'.gitattributes',REP/'protocol.md',OUT/'.gitattributes',
        receipt_path,OUT/'synthetic_tests_attempt_01.log',OUT/'synthetic_tests_attempt_02.log',
        OUT/'synthetic_tests_receipt.json',OUT/'draft_source_01.json',
        ROOT/'reports/generalization_knowncell_parser_profile_v4_20261023/independent_review_01.md']
    pins.update({path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in own})
    payload={'status':'SOURCE_FROZEN_FINITE63_RUNNER_NOT_EXECUTION_ADMISSION_REPLAY_OR_GATE',
        'files':pins,'checkpoint_count':63,'inner_checkpoints':54,'outer_checkpoints':9,'optimizer_units':84,
        'same_task_order_and_science':True,'mandatory_integrity_hook_before_each_checkpoint':True,
        'new_run_container_with_unchanged_campaign_child':True,'resume_or_refit_implemented':False,
        'actual_native_optimizer_calls':0,'project_dataset_or_checkpoint_reads':0,
        'independent63_numerical_reselection_gate_complete':False,
        'all_original3GiB_1GiB_one_thread_guards_unchanged':True,
        'separate_root_review_commit_and_actual_execution_admission_required':True}
    path=OUT/'preparation_manifest.json'
    with path.open('xb') as stream:stream.write(canonical_bytes(payload))
    print('FINITE_RUNNER_SOURCE_READY',len(pins),digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
