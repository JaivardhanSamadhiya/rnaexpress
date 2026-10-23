"""Prepare source/summary bindings only; never read an actual campaign prefit."""
import ast
from datetime import datetime,timezone
from pathlib import Path
from .contracts import canonical_bytes,digest,strict_json,task_roster
from .spec import NS,SOURCE_MANIFESTS

ROOT=Path(__file__).resolve().parents[2]
SRC,REP,OUT=[ROOT/name/NS for name in ('src','reports','results')]


def run():
    pins={}
    numeric_path=ROOT/SOURCE_MANIFESTS[-1]
    prior=strict_json(numeric_path.read_bytes())
    assert prior['status']=='FROZEN_DEFERRED_NUMERIC_SOURCE_NOT_NATIVE_OR_PROJECT_ADMISSION'
    assert prior['native_scientific_imports'] is False and prior['native_optimizer_calls']==0
    allowed_results={'generalization_knowncell_joint_design_20261009',
                     'generalization_knowncell_joint_implementation_20261022',
                     'generalization_knowncell_joint_numeric_20261022'}
    for name,want in prior['files'].items():
        assert name==name.replace('\\','/') and not name.startswith('/') and ':' not in name
        assert '..' not in name.split('/') and name.split('/')[0] in ('src','reports','results')
        if name.startswith('results/'):assert name.split('/')[1] in allowed_results
        assert digest((ROOT/name).read_bytes())==want,name
        pins[name]=want
    for name in SOURCE_MANIFESTS:
        raw=(ROOT/name).read_bytes();assert isinstance(strict_json(raw),dict)
        if name in pins:assert digest(raw)==pins[name]
        pins[name]=digest(raw)
    receipt_path=OUT/'synthetic_tests_receipt.json';receipt=strict_json(receipt_path.read_bytes())
    assert receipt['status']=='PASS_INVENTED_STDLIB_LIFECYCLE_NOT_SCIENTIFIC_CAMPAIGN'
    assert receipt['scientific_imports'] is False and receipt['native_optimizer_calls']==0
    assert receipt['project_metadata_reads']==receipt['project_feature_reads']==receipt['project_outcome_reads']==receipt['models_fitted']==0
    sources=sorted(SRC.glob('*.py'))
    assert receipt['source_files']=={path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in sources}
    for path in sources:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    own=sources+[SRC/'.gitattributes',REP/'.gitattributes',REP/'protocol.md',OUT/'.gitattributes',receipt_path]
    pins.update({path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in own})
    payload={'status':'SOURCE_FROZEN_LIFECYCLE_INFRASTRUCTURE_NOT_PROJECT_PREFIT_OR_EXECUTION_AUTHORIZATION',
             'generated_utc':datetime.now(timezone.utc).isoformat(),'files':pins,
             'checkpoint_roster':task_roster(),'checkpoints':63,'inner_checkpoints':54,'outer_checkpoints':9,
             'optimizer_units':84,'shared_training_pools':9,
             'scientific_imports':False,'native_optimizer_calls':0,'models_fitted':0,
             'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,
             'project_prefit_opened':False,'actual_campaign_executed':False,
             'all_old_resource_guards_unchanged':True,'resource_exception_applies':False,
             'source_only_selection_arithmetic_implemented':False,'numerical_replay_or_gate_implemented':False,
             'root_commit_and_separate_project_runtime_prefit_execution_admission_required':True,
             'remaining':['guarded selective metadata/array/label loader and independent certificates',
                          'native invented profile PASS and actual runtime provenance binding',
                          'reviewed exact-commit reader and fresh3GiB/1GiB one-thread controller',
                          'source-frozen adapter around each actual minimize invocation',
                          'independent paired-OOF selector arithmetic,full model/score/selection replay and original gates']}
    path=OUT/'preparation_manifest.json'
    with path.open('xb') as handle:handle.write(canonical_bytes(payload))
    print('LIFECYCLE_SOURCE_READY',len(pins),digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
