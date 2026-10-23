"""Additive source-only selector freeze; preserve the entire original66-pin layer."""
import ast
from datetime import datetime, timezone
from pathlib import Path
from .adapter import NS
from src.generalization_knowncell_joint_campaign_20261023.contracts import strict_json, digest, canonical_bytes

ROOT = Path(__file__).resolve().parents[2]
SRC, REP, OUT = [ROOT/name/NS for name in ('src','reports','results')]
ORIGINAL_SHA = '2873fa9db964ceba0bae0baff2352ab8d0cbb19b1520374b7d767286b27fdae6'


def run():
    old_path = OUT/'preparation_manifest.json'; old_raw = old_path.read_bytes()
    assert digest(old_raw) == ORIGINAL_SHA, 'Preserve original engine preparation manifest'
    old = strict_json(old_raw)
    assert old['status'] == 'DEFERRED_DOMAIN_ADAPTER_SOURCE_NOT_NATIVE_PROFILE_PROJECT_PREFIT_OR_EXECUTION_ADMISSION'
    pins = {}
    allowed_results = {'generalization_knowncell_joint_design_20261009','generalization_knowncell_joint_implementation_20261022',
                       'generalization_knowncell_joint_numeric_20261022','generalization_knowncell_joint_campaign_20261023',
                       'generalization_knowncell_joint_engine_20261023'}
    for name, expected in old['files'].items():
        assert name == name.replace('\\','/') and not name.startswith('/') and ':' not in name and '..' not in name.split('/')
        assert name.startswith(('src/','reports/','results/'))
        if name.startswith('results/'): assert name.split('/')[1] in allowed_results
        assert digest((ROOT/name).read_bytes()) == expected, name
        pins[name] = expected
    assert len(pins) == 66
    pins[old_path.relative_to(ROOT).as_posix()] = ORIGINAL_SHA
    receipt_path = OUT/'synthetic_tests_receipt_v2.json'; receipt = strict_json(receipt_path.read_bytes())
    assert receipt['status'] == 'PASS_INVENTED_IMMUTABLE_PLAN_SELECTOR_V2_NOT_PROJECT_ADMISSION'
    assert receipt['scientific_imports'] is False
    for name in ('native_optimizer_calls','models_fitted','project_metadata_reads','project_feature_reads','project_outcome_reads','actual_checkpoint_reads'):
        assert receipt[name] == 0
    sources = sorted(SRC.glob('*.py'))
    assert receipt['source_files'] == {p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sources}
    for path in sources: ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    own = [SRC/name for name in ('adapter_v2.py','tests_v2.py','prepare_v2.py')]
    own += [REP/'prospective_selector_v2.md',receipt_path]
    pins.update({path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in own})
    payload = {'status':'PROSPECTIVE_IMMUTABLE_PLAN_SELECTOR_V2_SOURCE_NOT_NATIVE_OR_PROJECT_ADMISSION',
               'generated_utc':datetime.now(timezone.utc).isoformat(),'files':pins,
               'original66pins_preserved':True,'original_manifest_sha256':ORIGINAL_SHA,
               'required_selector':'src.generalization_knowncell_joint_engine_20261023.adapter_v2.select_outer',
               'prepare_pools_and_make_fit_callback_are_unchanged_original_objects':True,
               'source_selection_bound_to_immutable_prefit_pool_before_checkpoint_read':True,
               'shared_source_pools':9,'inner_checkpoints':54,'outer_checkpoints':9,'optimizer_units':84,
               'scientific_imports':False,'native_optimizer_calls':0,'models_fitted':0,
               'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,'actual_checkpoint_reads':0,
               'all_original_3GiB_guards_unchanged':True,'resource_exception_applies':False,
               'full_campaign_cli_checkpoint_loop_replay_or_gate_implemented':False,
               'root_review_commit_and_separate_admission_required':True}
    path = OUT/'preparation_manifest_v2.json'
    with path.open('xb') as handle: handle.write(canonical_bytes(payload))
    print('IMMUTABLE_SELECTOR_V2_SOURCE_READY', len(pins), digest(path.read_bytes()), flush=True)


if __name__ == '__main__': run()
