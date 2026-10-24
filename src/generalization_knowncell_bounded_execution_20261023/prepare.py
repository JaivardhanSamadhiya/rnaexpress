"""Reviewable PROPOSAL freeze; no authorization file or project data access."""
import ast
from pathlib import Path
import sys
from . import common as c

DEPENDENCIES = {
    'results/generalization_knowncell_metadata_execution_v2_20261023/execution_manifest.json':
        'dccab5219dcc6a82e015a31e248748cef160ee2e0408105ddfd8e2a0c86e35f7',
    'results/generalization_knowncell_runtime_provider_20261023/preparation_manifest.json':
        'c10fd9e8f52095e2b8a5eae8b533ed4f66814090ab8844928af7c7392a18694f',
    'results/generalization_knowncell_joint_runner_20261023/preparation_manifest.json':
        'ba130fda7006228da14dd93def1f27c6bb57a5d04fbe5150932b64c79b227897',
    'results/generalization_knowncell_joint_evaluation_20261023/preparation_manifest.json':
        '0176b26b12e73afbd7b810adb6bff5837f2e62e0ff749e501c8e88cdbae3bd5f',
    'results/generalization_knowncell_array_admission_20261023/readiness_manifest.json':
        '19c9d099ec4a052221bd39d993239bd401fc3aa767775c347a198b9259a5687f',
}


def static_name(name):
    name = name.replace('\\','/')
    c.relative(name)
    allowed = name.endswith(('.py','.md','.json','.log','/.gitattributes'))
    assert allowed and name.split('/')[0] in ('src','reports','results','artifacts'), 'Non-source payload excluded: '+name
    return name


def run():
    assert not c.AUTH.exists(), 'Never create/rewrite approval during preparation'
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch') for name in sys.modules)
    pins={}
    def add(name,want=None):
        name=static_name(name);raw=(c.ROOT/name).read_bytes();actual=c.sha(raw)
        assert want is None or actual==want,name
        assert name not in pins or pins[name]==actual,'Conflicting fixed source pin'
        pins[name]=actual
    for name,want in DEPENDENCIES.items():
        add(name,want)
        manifest=c.decode((c.ROOT/name).read_bytes())
        for relative,expected in manifest['files'].items():add(relative,expected)
    # Include regular parent packages in addition to dependency manifests.
    for name in list(pins):
        if name.startswith('src/') and name.endswith('.py'):
            parent=(c.ROOT/name).parent
            while parent.is_relative_to(c.ROOT/'src'):
                init=parent/'__init__.py'
                if init.is_file():add(init.relative_to(c.ROOT).as_posix())
                parent=parent.parent
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    for path in sources:
        ast.parse(path.read_text(encoding='utf-8'));add(path.relative_to(c.ROOT).as_posix())
    for name in ('controller_tests_receipt.json','calibration_tests_receipt.json'):
        path=c.OUT/name;receipt=c.decode(path.read_bytes());assert receipt['tests']>0
        assert receipt['sources']=={p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources}
        assert receipt['actual_workers']==receipt['project_payloads']==receipt['model_fits']==0
        add(path.relative_to(c.ROOT).as_posix())
    for folder in ('src','reports','results'):add(folder+'/'+c.NS+'/.gitattributes')
    for name in ('protocol.md','plan.md'):add('reports/'+c.NS+'/'+name)
    old=c.decode((c.ROOT/next(iter(DEPENDENCIES))).read_bytes())
    for name,want in old['python_native_files'].items():assert c.sha(Path(name).read_bytes())==want,name
    c.save_new(c.MANIFEST,{'status':c.STATUS,'UTC':c.datetime.now(c.timezone.utc).isoformat(),
        'files':pins,'python_executable':old['python_executable'],'python_native_files':old['python_native_files'],
        'stages':list(c.STAGES),'implemented_entrypoints':list(c.IMPLEMENTED_STAGES),
        'resource_policy':c.resource_policy(),'cache_prefix':str(c.CACHE_PREFIX),
        'explicit_knowncell_human_approval_required':True,'authorization_exists_at_preparation':False,
        'scientific_grid_targets_features_rows_splits_tolerances_gates_changed':False,
        'biological_metadata_array_labels_or_models_read_during_preparation':False,
        'model_checkpoints_planned':63,'actual_optimizer_units_planned':84,
        'only_metadata_entrypoint_implemented_here':True,
        'later_frozen_stage_admissions_and_committed_FIT_prefit_still_required':True})
    print('KNOWNCELL_RESOURCE_PROPOSAL_READY',len(pins),c.sha(c.MANIFEST.read_bytes()),flush=True)


if __name__=='__main__':run()
