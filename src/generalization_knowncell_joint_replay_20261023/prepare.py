"""Pin source-only replay and its existing reference dependency closure."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_knowncell_joint_replay_20261023'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    prior_path = ROOT/'results/generalization_knowncell_joint_engine_20261023/preparation_manifest.json'
    prior = json.loads(prior_path.read_bytes())
    assert sha(prior_path) == '2873fa9db964ceba0bae0baff2352ab8d0cbb19b1520374b7d767286b27fdae6'
    pins = dict(prior['files'])
    for name, expected in pins.items():
        assert sha(ROOT/name) == expected, name
    pins[prior_path.relative_to(ROOT).as_posix()] = sha(prior_path)
    source, report, output = [ROOT/name/NS for name in ('src','reports','results')]
    receipt_path = output/'synthetic_tests_receipt.json'
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['status'] == 'PASS_INVENTED_DEFERRED_CHECKPOINT_ARITHMETIC_REPLAY'
    sources = sorted(source.glob('*.py'))
    assert receipt['sources'] == {p.relative_to(ROOT).as_posix():sha(p) for p in sources}
    for path in sources:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    own = sources+[source/'.gitattributes', report/'.gitattributes', report/'protocol.md', output/'.gitattributes', receipt_path, ROOT/'src/__init__.py']
    pins.update({p.relative_to(ROOT).as_posix():sha(p) for p in own})
    value = {'status':'DEFERRED_CHECKPOINT_ARITHMETIC_SOURCE_NOT_CAMPAIGN_REPLAY_OR_EXECUTION_ADMISSION',
             'UTC':datetime.now(timezone.utc).isoformat(), 'files':pins,
             'scientific_imports':False, 'project_payload_reads':0, 'actual_optimizer_calls':0,
             'scalar_bound_strictly_below':1e-9, 'canonical_score_equality':'exact',
             'original_resource_guards_unchanged':True,
             'full_63_checkpoint_replay_source_selection_bootstrap_and_gates_pending':True}
    path = output/'preparation_manifest.json'
    with path.open('xb') as handle:
        handle.write((json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode())
    print('REPLAY_ARITHMETIC_SOURCE_READY', len(pins), sha(path), flush=True)


if __name__ == '__main__':
    run()
