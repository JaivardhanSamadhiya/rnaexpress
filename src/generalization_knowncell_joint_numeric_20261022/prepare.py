"""Freeze only this deferred source layer and prior source/summary identities."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from .spec import (NS, ARMS, CONFIGS, FEATURE_WIDTH, SCORER, METHOD, OPTIONS,
                   REFERENCE_READINESS, DESIGN_MANIFEST, HISTORICAL_SOLVER_SOURCE)

ROOT=Path(__file__).resolve().parents[2]
SRC,REP,OUT=[ROOT/name/NS for name in ('src','reports','results')]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def readj(path):
    assert path.stat().st_size<=2*2**20
    def unique(pairs):
        result={}
        for key,value in pairs:
            assert key not in result
            result[key]=value
        return result
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique)


def historical_optimizer_contract(source):
    """Read source text, never import the broad historical scientific module."""
    tree=ast.parse(source)
    function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='optimize')
    calls=[node for node in ast.walk(function) if isinstance(node,ast.Call)
           and isinstance(node.func,ast.Name) and node.func.id=='minimize']
    assert len(calls)==1
    keywords={node.arg:node.value for node in calls[0].keywords}
    assert ast.literal_eval(keywords['jac']) is True
    assert ast.literal_eval(keywords['method'])==METHOD
    assert ast.literal_eval(keywords['options'])==OPTIONS
    return {'method':METHOD,'options':dict(OPTIONS),'jac':True,'source_imported':False}


def run():
    readiness_path=ROOT/REFERENCE_READINESS
    readiness=readj(readiness_path)
    assert readiness['status']=='TESTED_REFERENCE_IMPLEMENTATION_NOT_METADATA_OR_FIT_ADMISSION'
    assert readiness['scientific_runtimes_imported'] is False
    assert readiness['project_dataset_reads']==readiness['project_feature_reads']==readiness['project_outcome_reads']==readiness['models_fitted']==0
    pins={}
    allowed=('src/generalization_knowncell_joint_design_20261009/',
             'reports/generalization_knowncell_joint_design_20261009/',
             'results/generalization_knowncell_joint_design_20261009/',
             'src/generalization_knowncell_joint_implementation_20261022/',
             'reports/generalization_knowncell_joint_implementation_20261022/',
             'results/generalization_knowncell_joint_implementation_20261022/')
    seen=set()
    for name,digest in readiness['files'].items():
        normalized=name.replace('\\','/')
        assert normalized not in seen and not normalized.startswith('/') and ':' not in normalized and '..' not in normalized.split('/')
        seen.add(normalized)
        assert normalized.startswith(allowed), 'Source/summary preparation may not follow project input declarations'
        raw=(ROOT/normalized).read_bytes();assert sha(raw)==digest,normalized
        pins[normalized]=digest
    assert DESIGN_MANIFEST in pins
    pins[REFERENCE_READINESS]=sha(readiness_path.read_bytes())
    old_source=(ROOT/HISTORICAL_SOLVER_SOURCE).read_bytes()
    solver=historical_optimizer_contract(old_source.decode('utf-8'))
    pins[HISTORICAL_SOLVER_SOURCE]=sha(old_source)
    receipt_path=OUT/'synthetic_tests_receipt.json';receipt=readj(receipt_path)
    assert receipt['status']=='PASS_INVENTED_STDLIB_DEFERRED_NUMERIC_CONTRACTS_NOT_NATIVE_PARITY'
    assert receipt['scientific_runtime_imports'] is False and receipt['actual_native_optimizer_calls']==0
    assert receipt['project_metadata_reads']==receipt['project_feature_reads']==receipt['project_outcome_reads']==receipt['models_fitted']==0
    sources=sorted(SRC.glob('*.py'))
    assert receipt['source_files']=={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sources}
    own=sources+[SRC/'.gitattributes',REP/'.gitattributes',REP/'protocol.md',OUT/'.gitattributes',receipt_path]
    for path in sources:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    pins.update({p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in own})
    payload={'status':'FROZEN_DEFERRED_NUMERIC_SOURCE_NOT_NATIVE_OR_PROJECT_ADMISSION',
             'generated_utc':datetime.now(timezone.utc).isoformat(),'files':pins,
             'arms':ARMS,'configs':CONFIGS,'feature_width':FEATURE_WIDTH,
             'canonical_scorer':SCORER,'historical_optimizer_source_contract':solver,
             'shared_mean':[0.]*FEATURE_WIDTH,'coefficient_dimensions':{'pooled':102,'independent':[102,102],'joint_shrink10':204},
             'inactive_columns':'zeroed pair inputs, zero start, exact-zero result required; never clipped',
             'native_scientific_imports':False,'native_optimizer_calls':0,
             'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,'models_fitted':0,
             'actual_native_parity_certified':False,'separate_committed_native_profile_required':True,
             'project_loader_sampler_selector_checkpoint_writer_campaign_or_gate_implemented':False,
             'old_namespaces_modified':False,'all_original_3GiB_resource_guards_unchanged':True,
             'resource_exception_applies':False,'root_commit_verification_required':True,
             'remaining':['separate admitted scientific runtime and invented native parity profile',
                          'guarded project metadata/array/label admission',
                          'independently bound original pair sampler and common source scaling',
                          'immutable checkpoint/source-only nested campaign and full independent replay/gate']}
    target=OUT/'preparation_manifest.json'
    with target.open('xb') as handle:handle.write((json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
    print('DEFERRED_NUMERIC_SOURCE_READY',len(pins),sha(target.read_bytes()),flush=True)


if __name__=='__main__':run()
