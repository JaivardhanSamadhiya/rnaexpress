"""Deferred source-pool, fitting-callback and source-only selection functions.

Scientific libraries, the original sampler and real fresh probes are explicit
arguments. No library bootstrap, project reader, campaign CLI or gate exists.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import math
from src.generalization_knowncell_joint_implementation_20261022 import contracts as reference
from src.generalization_knowncell_joint_implementation_20261022 import selection
from src.generalization_knowncell_joint_implementation_20261022.admission import require_resources
from src.generalization_knowncell_joint_implementation_20261022.spec import CONFIGS,METADATA_COLUMNS
from src.generalization_knowncell_joint_numeric_20261022 import numeric
from src.generalization_knowncell_joint_numeric_20261022.spec import METHOD,OPTIONS,SCORER
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lifecycle
from src.generalization_knowncell_joint_campaign_20261023.writer import unit_spec,read_object
from src.generalization_knowncell_joint_campaign_20261023.writer_v2 import Campaign
from src.generalization_knowncell_joint_campaign_20261023.spec import PREFIT_STATUS,COUNTS,ARMS

NS='generalization_knowncell_joint_engine_20261023'
ROOT=Path(__file__).resolve().parents[2]
SAMPLER_SOURCE=ROOT/'src/cross_assay_20260927/models.py'
ADMISSION_HASHES=('runtime_binding_sha256','metadata_admission_sha256','feature_admission_sha256',
                  'label_admission_sha256','fit_source_manifest_sha256','native_profile_receipt_sha256',
                  'original_sampler_source_sha256','numeric_source_manifest_sha256','lifecycle_v2_manifest_sha256',
                  'input_row_ids_sha256','input_metadata_sha256','input_features_sha256','input_effects_sha256')


def gate(probe,environment):
    assert callable(probe)
    return require_resources(probe(),environment)


def array_hash(np,value):
    """C-order float64 hash with an unambiguous shape/type header."""
    array=np.array(value,dtype=np.float64,order='C',copy=True)
    assert np.isfinite(array).all()
    header=lifecycle.canonical_bytes({'shape':list(array.shape),'dtype':'float64','order':'C'})
    return hashlib.sha256(header+array.tobytes(order='C')).hexdigest()


def pool_binding(np,pool):
    prepared=pool['prepared'];rows=pool['rows'];targets=pool['validation_metadata']
    binding={'training_ids':[row['intervention_id'] for row in rows],
             'validation_ids':[row['intervention_id'] for row in targets],
             'training_rows':len(rows),'validation_rows':len(targets),
             'training_pairs':len(pool['left']),'both_cells_confirmed':True,
             'full_original_menus_confirmed':True,'gene_component_allele_contradictions':0,
             'training_metadata_sha256':reference.metadata_sha(rows),
             'validation_metadata_sha256':reference.metadata_sha(targets),
             'training_features_sha256':array_hash(np,pool['features']),
             'validation_features_sha256':array_hash(np,pool['validation_features']),
             'training_effects_sha256':array_hash(np,pool['effects']),
             'training_effects_json_sha256':lifecycle.hash_value(pool['effects']),
             'validation_effects_sha256':array_hash(np,pool['validation_effects']),
             'original_pair_roster_sha256':lifecycle.hash_value({'left':pool['left'],'right':pool['right'],'labels':pool['labels']}),
             'pair_weights_sha256':array_hash(np,prepared['weights']),
             'common_scaling_sha256':lifecycle.hash_value(prepared['scaling']),
             'prepared_z_sha256':array_hash(np,prepared['z']),
             'prepared_labels_sha256':array_hash(np,prepared['labels']),
             'prepared_cell_signs_sha256':array_hash(np,prepared['signs'])}
    for field in ('training','validation'):binding[field+'_ids_sha256']=reference.ids_sha(rows if field=='training' else targets)
    return binding


def one_pool(np,pd,pair_indices,metadata,matrix,effects,train,target,probe,environment):
    """Finite pool builder; caller supplies the independently validated masks."""
    gate(probe,environment)
    rows=[dict(metadata[i]) for i in train];targets=[dict(metadata[i]) for i in target]
    truths={row['intervention_id']:effects[row['intervention_id']] for row in rows}
    source_values=[truths[row['intervention_id']] for row in rows]
    frame=pd.DataFrame([{**row,'measured_delta':value} for row,value in zip(rows,source_values)],
                       columns=[*METADATA_COLUMNS,'measured_delta']).reset_index(drop=True)
    assert list(frame.index)==list(range(len(rows))),'Original sampler requires reset source indices'
    left,right,labels,old_weights,studies=pair_indices(frame)
    left,right=left.tolist(),right.tolist();raw_labels=labels.tolist()
    assert all(value in (-1,1) for value in raw_labels)
    labels=[int(value) for value in raw_labels]
    assert len(left)==len(labels)==len(old_weights)==len(studies)
    assert all(value=='mikl_gse173098' for value in studies.tolist())
    weights=reference.preference_contract(rows,truths,left,right,labels)
    # Old pooled-study weights are deliberately unused after roster validation.
    features=np.array(matrix[np.asarray(train)],dtype=np.float64,order='C',copy=True)
    validation=np.array(matrix[np.asarray(target)],dtype=np.float64,order='C',copy=True)
    cells=[rows[i]['cell_type'] for i in left]
    prepared=numeric.prepare_training(np,features,left,right,labels,weights,cells)
    pool={'rows':rows,'validation_metadata':targets,'features':features,'validation_features':validation,
          'effects':list(source_values),'validation_effects':[effects[row['intervention_id']] for row in targets],
          'left':left,'right':right,'labels':labels,'prepared':prepared}
    pool['binding']=pool_binding(np,pool)
    return pool


@dataclass
class PreparedPools:
    metadata:list
    pools:dict
    prefit_document:dict


def source_specs(contract):
    result=[]
    for outer in contract['splits']:
        fold=outer['outer_fold']
        for inner in outer['inner']:
            result.append((lifecycle.pool_key(fold,inner['validation_fold']),inner['training_indices'],inner['validation_indices']))
        result.append((lifecycle.pool_key(fold,None),outer['training_indices'],outer['target_indices']))
    expected={lifecycle.pool_key(outer,inner) for outer in (0,1,2) for inner in (None,*[f for f in (0,1,2) if f!=outer])}
    assert len(result)==9 and {key for key,_,_ in result}==expected
    return result


def prepare_pools(np,pd,pair_indices,metadata,features,effects,*,probe,environment,admissions):
    """Prepare exactly9 shared pools; returned prefit is NOT committed/admitted.

    A separately reviewed loader/controller must verify actual input/runtime
    receipt origins and authorization before calling this deferred function.
    """
    gate(probe,environment)
    assert admissions['status']=='ADMITTED_MIKL_METADATA_SIMPLE102_ORIGINAL_EFFECTS'
    for name in ADMISSION_HASHES:lifecycle.valid_hash(admissions[name])
    assert callable(pair_indices) and pair_indices.__name__=='pair_indices'
    assert pair_indices.__module__=='src.cross_assay_20260927.models'
    assert hashlib.sha256(SAMPLER_SOURCE.read_bytes()).hexdigest()==admissions['original_sampler_source_sha256']
    # Callable identity/source declarations are additionally bound by the future
    # native controller; this does not inspect or execute its global namespace.
    metadata=[dict(row) for row in metadata]
    contract=reference.full_metadata_contract(metadata)
    assert reference.ids_sha(metadata)==admissions['input_row_ids_sha256']
    assert reference.metadata_sha(metadata)==admissions['input_metadata_sha256']
    ids=[row['intervention_id'] for row in metadata]
    assert set(effects)==set(ids) and all(type(effects[key]) in (int,float) and math.isfinite(effects[key]) for key in ids)
    matrix=np.array(features,dtype=np.float64,order='C',copy=True)
    assert matrix.shape==(COUNTS['all_rows'],102) and np.isfinite(matrix).all()
    assert array_hash(np,matrix)==admissions['input_features_sha256']
    assert array_hash(np,[effects[key] for key in ids])==admissions['input_effects_sha256']
    pools={}
    for key,train,target in source_specs(contract):
        pools[key]=one_pool(np,pd,pair_indices,metadata,matrix,effects,train,target,probe,environment)
    assert len(pools)==9
    document={'status':PREFIT_STATUS,'counts':dict(COUNTS),'arms':list(ARMS),'configs':list(CONFIGS),
              'numerical_threads':1,'resource_exception_applies':False,
              'all_row_ids':ids,'all_row_folds':[row['held_parent_fold'] for row in metadata],
              'source_pools':{key:pool['binding'] for key,pool in pools.items()},
              'input_admission_bindings':dict(admissions),
              **{key:admissions[key] for key in ('runtime_binding_sha256','metadata_admission_sha256',
                    'feature_admission_sha256','label_admission_sha256','fit_source_manifest_sha256')}}
    lifecycle.validate_prefit(document)
    return PreparedPools(metadata,pools,document)


def check_pool(np,prepared,plan,task):
    assert prepared.prefit_document==plan.document(),'Prepared pools differ from committed prefit'
    pool=prepared.pools[lifecycle.pool_key(task['outer_fold'],task['inner_fold'])]
    assert pool_binding(np,pool)==pool['binding']==plan.pool(task),'Native pool mutated after prefit'
    return pool


def make_fit_callback(np,minimize,expit,prepared,plan,*,probe,environment):
    """Create lifecycle callback; this function itself executes no optimizer."""
    gate(probe,environment)
    assert callable(minimize) and callable(expit)
    assert prepared.prefit_document==plan.document()
    def callback(task,birth,units):
        gate(probe,environment);pool=check_pool(np,prepared,plan,task)
        assert birth['identity']['prefit_sha256']==plan.prefit_sha256
        assert birth['identity']['runtime_binding_sha256']==plan.runtime_binding_sha256
        assert birth['source_pool_sha256']==lifecycle.hash_value(pool['binding'])
        expected=unit_spec(task['arm']);calls=[]
        def guarded_minimize(fun,initial,**kwargs):
            gate(probe,environment);check_pool(np,prepared,plan,task)
            assert kwargs=={'jac':True,'method':METHOD,'options':OPTIONS}
            assert len(calls)<len(expected)
            name,width=expected[len(calls)];assert initial.shape==(width,)
            calls.append(name)
            return units.invoke(name,width,minimize,fun,initial,**kwargs)
        model=numeric.fit_prepared(np,guarded_minimize,expit,pool['prepared'],task['arm'],birth['identity']['configuration'])
        assert len(calls)==task['optimizer_units']
        gate(probe,environment)
        scores=numeric.canonical_scores(np,model,pool['validation_features'],[row['cell_type'] for row in pool['validation_metadata']])
        assert scores.shape==(pool['binding']['validation_rows'],)
        assert scores.dtype.kind=='f' and scores.dtype.itemsize==8 and np.isfinite(scores).all()
        return {'model':model,'predictions':{'row_ids':list(pool['binding']['validation_ids']),'scores':scores.tolist(),
                 'canonical_shape':[pool['binding']['validation_rows'],102],'canonical_dtype':'float64',
                 'canonical_order':'C','canonical_scorer':SCORER}}
    return callback


def select_outer(prepared,campaign,arm,outer_fold,*,probe,environment):
    """Use only six source OOF predictions and outer-training mean effects."""
    gate(probe,environment)
    assert isinstance(campaign,Campaign) and prepared.prefit_document==campaign.plan.document()
    admissions=prepared.prefit_document['input_admission_bindings']
    assert reference.ids_sha(prepared.metadata)==admissions['input_row_ids_sha256']
    assert reference.metadata_sha(prepared.metadata)==admissions['input_metadata_sha256']
    task=next(task for task in campaign.tasks.values() if task['arm']==arm and task['outer_fold']==outer_fold and task['phase']=='outer')
    pool=prepared.pools[lifecycle.pool_key(outer_fold,None)]
    assert reference.metadata_sha(pool['rows'])==pool['binding']['training_metadata_sha256']
    assert lifecycle.hash_value(pool['effects'])==pool['binding']['training_effects_json_sha256']
    source_truths={row['intervention_id']:value for row,value in zip(pool['rows'],pool['effects'])}
    assert set(source_truths)==set(pool['binding']['training_ids'])
    assert not set(source_truths)&set(pool['binding']['validation_ids'])
    batches={config['id']:{} for config in CONFIGS};inner_hashes={}
    for key,inner in campaign.tasks.items():
        if inner['arm']!=arm or inner['outer_fold']!=outer_fold or inner['phase']!='inner':continue
        gate(probe,environment)
        receipt=campaign.check_saved(key);saved=read_object(campaign.paths(key)[1])
        prediction=saved['predictions']
        batches[inner['configuration_id']][inner['inner_fold']]=dict(zip(prediction['row_ids'],prediction['scores']))
        inner_hashes[key]=receipt['model_sha256']
    assert len(inner_hashes)==6
    chosen=selection.select_source_config(prepared.metadata,outer_fold,source_truths,batches)
    return {'arm':arm,'outer_fold':outer_fold,'selected_config':chosen['selected_config'],
            'source_only':True,'primary_paired_only':True,
            'selection_rule':'concatenated_paired_OOF_equal_cell_component_context_direction_regret',
            'prefit_sha256':campaign.plan.prefit_sha256,'runtime_binding_sha256':campaign.plan.runtime_binding_sha256,
            'source_training_ids_sha256':pool['binding']['training_ids_sha256'],
            'configuration_metrics_sha256':lifecycle.hash_value(chosen['configuration_metrics']),
            'inner_checkpoint_sha256':inner_hashes}
