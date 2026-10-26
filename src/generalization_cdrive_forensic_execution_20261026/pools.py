"""Reconstruct fixed mathematical pools with the NEW forensic fresh guard.

Original admission/factory/fit entrypoints are never called or patched. The
body below reproduces original one_pool operations, checked against all nine
historical complete bindings. There is no optimizer or result evaluator.
"""
import ast
import hashlib
import itertools
from . import common as c
from src.generalization_knowncell_joint_input_bridge_20261023 import sampler
from src.generalization_knowncell_joint_input_bridge_20261023 import spec as ss
from src.generalization_knowncell_joint_implementation_20261022 import contracts as reference
from src.generalization_knowncell_joint_implementation_20261022.spec import METADATA_COLUMNS
from src.generalization_knowncell_joint_engine_20261023 import adapter
from src.generalization_knowncell_joint_numeric_20261022 import numeric
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc


def original_function(np,*,fresh):
    source=c.read_exact(ss.MODEL_SOURCE,ss.MODEL_SHA,fresh=fresh)
    common=c.read_exact(ss.COMMON_SOURCE,ss.COMMON_SHA,fresh=fresh)
    node,identity=sampler.extract_function(source,common)
    assert identity['original_model_source_sha256']==ss.MODEL_SHA
    assert identity['original_common_source_sha256']==ss.COMMON_SHA
    module=ast.Module(body=[node],type_ignores=[])
    scope={'__name__':ss.ORIGINAL_MODULE,'np':np,'hashlib':hashlib,
           'itertools':itertools,'PAIR_CACHE':{},'SEED':ss.SEED}
    fresh();exec(compile(module,str(c.ROOT/ss.MODEL_SOURCE),'exec'),scope)
    assert set(scope)=={'__name__','np','hashlib','itertools','PAIR_CACHE','SEED','__builtins__','pair_indices'}
    function=scope['pair_indices']
    assert function.__module__==ss.ORIGINAL_MODULE and function.__name__=='pair_indices'
    fresh();return function


def one_pool(np,pd,pair_indices,inp,train,target,*,fresh):
    fresh()
    rows=[dict(inp.metadata[i]) for i in train];targets=[dict(inp.metadata[i]) for i in target]
    truths={row['intervention_id']:inp.effects[row['intervention_id']] for row in rows}
    source_values=[truths[row['intervention_id']] for row in rows]
    frame=pd.DataFrame([{**row,'measured_delta':value} for row,value in zip(rows,source_values)],
        columns=[*METADATA_COLUMNS,'measured_delta']).reset_index(drop=True)
    assert list(frame.index)==list(range(len(rows)))
    fresh();left,right,labels,old_weights,studies=pair_indices(frame);fresh()
    left,right=left.tolist(),right.tolist();raw_labels=labels.tolist()
    assert all(value in (-1,1) for value in raw_labels)
    labels=[int(value) for value in raw_labels]
    assert len(left)==len(labels)==len(old_weights)==len(studies)
    assert all(value=='mikl_gse173098' for value in studies.tolist())
    weights=reference.preference_contract(rows,truths,left,right,labels)
    features=np.array(inp.matrix[np.asarray(train)],dtype=np.float64,order='C',copy=True)
    validation=np.array(inp.matrix[np.asarray(target)],dtype=np.float64,order='C',copy=True)
    cells=[rows[i]['cell_type'] for i in left]
    fresh();prepared=numeric.prepare_training(np,features,left,right,labels,weights,cells);fresh()
    pool={'rows':rows,'validation_metadata':targets,'features':features,'validation_features':validation,
        'effects':list(source_values),'validation_effects':[inp.effects[row['intervention_id']] for row in targets],
        'left':left,'right':right,'labels':labels,'prepared':prepared}
    pool['binding']=adapter.pool_binding(np,pool)
    fresh();return pool


def build_pools(np,pd,inp,*,fresh):
    fresh();contract=reference.full_metadata_contract(inp.metadata)
    document=lc.validate_prefit(inp.historical_plan.document())
    assert [row['intervention_id'] for row in inp.metadata]==document['all_row_ids']
    assert [row['held_parent_fold'] for row in inp.metadata]==document['all_row_folds']
    admissions=document['input_admission_bindings']
    assert contract['row_ids_sha256']==admissions['input_row_ids_sha256']
    assert contract['metadata_sha256']==admissions['input_metadata_sha256']
    assert adapter.array_hash(np,inp.matrix)==admissions['input_features_sha256']
    assert adapter.array_hash(np,[inp.effects[row['intervention_id']] for row in inp.metadata])==admissions['input_effects_sha256']
    pair_indices=original_function(np,fresh=fresh);result={}
    for key,train,target in adapter.source_specs(contract):
        result[key]=one_pool(np,pd,pair_indices,inp,train,target,fresh=fresh)
        assert result[key]['binding']==document['source_pools'][key],key
    assert len(result)==9 and set(result)==set(document['source_pools'])
    fresh();return adapter.PreparedPools(inp.metadata,result,document)
