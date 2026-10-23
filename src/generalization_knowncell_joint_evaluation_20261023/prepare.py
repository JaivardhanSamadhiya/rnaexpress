"""Source-only dependency freeze, without project or scientific input reads."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_knowncell_joint_evaluation_20261023'
PRIOR = {
    'results/generalization_knowncell_joint_engine_20261023/preparation_manifest_v2.json':
        '109a2bd1cd7e1b62f5a7607d67b3cd5da75192e4dfb9af46b1e5cb8b0fc7436e',
    'results/generalization_knowncell_joint_replay_20261023/preparation_manifest.json':
        'cc529a521fe3b91f83431c81119d786d13ad9d2ebf271a2a615031eb3278175d',
    'results/generalization_knowncell_joint_gate_20261023/preparation_manifest.json':
        'c3d7c632507e6ebeb3c99da4004f28dc7202889b80c24b58b7c76f368467f28b',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    pins = {}
    def add(name,expected):
        path = ROOT/name
        assert path.is_file() and sha(path) == expected,name
        assert name not in pins or pins[name] == expected,'Conflicting source dependency pin'
        pins[name] = expected
    for name,expected in PRIOR.items():
        add(name,expected)
        manifest = json.loads((ROOT/name).read_bytes())
        for rel,digest in manifest['files'].items():
            add(rel,digest)
    source = ROOT/'src'/NS
    sources = sorted(source.glob('*.py'))
    receipt_path = ROOT/'results'/NS/'synthetic_tests_receipt.json'
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['status'] == 'PASS_INVENTED_SUPPLIED_OUTER_EVALUATION_NOT_PROJECT_ADMISSION'
    assert receipt['sources'] == {path.relative_to(ROOT).as_posix():sha(path) for path in sources}
    assert receipt['project_payload_reads'] == receipt['actual_optimizer_calls'] == 0
    assert receipt['scientific_imports'] is False and receipt['native_bootstrap_run'] is False
    for path in sources:
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    paths = sources+[ROOT/folder/NS/'.gitattributes' for folder in ('src','reports','results','artifacts')]
    paths += [ROOT/'reports'/NS/'protocol.md',receipt_path,
              ROOT/'reports/generalization_knowncell_joint_replay_20261023/independent_source_review.md']
    for path in paths:
        add(path.relative_to(ROOT).as_posix(),sha(path))
    manifest = {'status':'DEFERRED_SUPPLIED_OUTER_EVALUATION_SOURCE_NOT_PROJECT_ADMISSION',
                'UTC':datetime.now(timezone.utc).isoformat(),'files':pins,
                'project_rows_not_read_here':13781,'outer_prediction_records_required':9,
                'all_directional_decisions_per_arm':9650,'primary_directional_decisions_per_arm':9632,
                'unmatched_rows_preserved':21,'bootstrap_components':187,
                'bootstrap_draws':5000,'bootstrap_seed':20261007,
                'project_payload_reads':0,'scientific_imports':False,'native_bootstrap_run':False,
                'actual_optimizer_calls':0,'input_provenance_certified':False,
                'all_63_84_and_source_reselection_certified':False,
                'requires_root_review_commit_and_separate_runtime_input_campaign_admission':True,
                'original_resource_guards_unchanged':True}
    output = ROOT/'results'/NS/'preparation_manifest.json'
    with output.open('xb') as stream:
        stream.write((json.dumps(manifest,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
    print('DEFERRED_OUTER_EVALUATION_SOURCE_READY',len(pins),sha(output),flush=True)


if __name__ == '__main__':
    run()
