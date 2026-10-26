"""Finite supplied-object driver; no reader/bootstrap, guard alias or CLI."""
from pathlib import Path
from src.generalization_knowncell_joint_numeric_20261022 import numeric
from src.generalization_knowncell_joint_numeric_20261022.spec import METHOD,OPTIONS,SCORER
from src.generalization_knowncell_joint_implementation_20261022 import contracts as reference
from src.generalization_knowncell_joint_implementation_20261022.selection import select_source_config
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_joint_campaign_20261023.writer import unit_spec,read_object,write_new
from src.generalization_knowncell_joint_campaign_20261023.writer_v2 import Campaign
from src.generalization_knowncell_joint_engine_20261023.adapter import PreparedPools,check_pool
from .plan import CurrentFitPlan


def make_fit_callback(np,minimize,expit,prepared,plan,*,fresh):
    """Actual owner/resource/callable certification is a fixed caller duty."""
    assert callable(fresh) and callable(minimize) and callable(expit)
    fresh();assert prepared.prefit_document==plan.document()
    def callback(task,birth,units):
        fresh();pool=check_pool(np,prepared,plan,task)
        assert birth['identity']['prefit_sha256']==plan.prefit_sha256
        assert birth['identity']['runtime_binding_sha256']==plan.runtime_binding_sha256
        assert birth['source_pool_sha256']==lc.hash_value(pool['binding'])
        expected=unit_spec(task['arm']);calls=[]
        def guarded_minimize(function,initial,**kwargs):
            fresh();check_pool(np,prepared,plan,task)
            assert kwargs=={'jac':True,'method':METHOD,'options':OPTIONS}
            assert len(calls)<len(expected)
            name,width=expected[len(calls)];assert initial.shape==(width,)
            calls.append(name)
            return units.invoke(name,width,minimize,function,initial,**kwargs)
        model=numeric.fit_prepared(np,guarded_minimize,expit,pool['prepared'],task['arm'],birth['identity']['configuration'])
        assert len(calls)==task['optimizer_units']
        fresh();check_pool(np,prepared,plan,task)
        scores=numeric.canonical_scores(np,model,pool['validation_features'],[row['cell_type'] for row in pool['validation_metadata']])
        assert scores.shape==(pool['binding']['validation_rows'],)
        assert scores.dtype.kind=='f' and scores.dtype.itemsize==8 and np.isfinite(scores).all()
        return {'model':model,'predictions':{'row_ids':list(pool['binding']['validation_ids']),
            'scores':scores.tolist(),'canonical_shape':[pool['binding']['validation_rows'],102],
            'canonical_dtype':'float64','canonical_order':'C','canonical_scorer':SCORER}}
    return callback


def select_outer(prepared,campaign,arm,outer_fold,*,fresh):
    """Original source-only criterion on the six completed new inner models."""
    fresh();assert isinstance(campaign,Campaign)
    assert prepared.prefit_document==campaign.plan.document()
    task=next(task for task in campaign.tasks.values() if task['arm']==arm and task['outer_fold']==outer_fold and task['phase']=='outer')
    pool=prepared.pools[lc.pool_key(outer_fold,None)];bound=campaign.plan.pool(task)
    assert pool['binding']==bound
    rows,effects=pool['rows'],pool['effects']
    assert [row['intervention_id'] for row in rows]==bound['training_ids']
    assert reference.ids_sha(rows)==bound['training_ids_sha256']
    assert reference.metadata_sha(rows)==bound['training_metadata_sha256']
    assert len(rows)==len(effects)==bound['training_rows']
    assert lc.hash_value(effects)==bound['training_effects_json_sha256']
    source_truths=dict(zip(bound['training_ids'],effects))
    assert not set(source_truths)&set(bound['validation_ids'])
    batches={config['id']:{} for config in lc.CONFIGS};hashes={}
    for key,inner in campaign.tasks.items():
        if inner['arm']!=arm or inner['outer_fold']!=outer_fold or inner['phase']!='inner':continue
        fresh();receipt=campaign.check_saved(key)
        fresh();saved=read_object(campaign.paths(key)[1])
        prediction=saved['predictions']
        batches[inner['configuration_id']][inner['inner_fold']]=dict(zip(prediction['row_ids'],prediction['scores']))
        hashes[key]=receipt['model_sha256']
    assert len(hashes)==6
    chosen=select_source_config(prepared.metadata,outer_fold,source_truths,batches)
    return {'arm':arm,'outer_fold':outer_fold,'selected_config':chosen['selected_config'],
        'source_only':True,'primary_paired_only':True,
        'selection_rule':'concatenated_paired_OOF_equal_cell_component_context_direction_regret',
        'prefit_sha256':campaign.plan.prefit_sha256,'runtime_binding_sha256':campaign.plan.runtime_binding_sha256,
        'source_training_ids_sha256':bound['training_ids_sha256'],
        'configuration_metrics_sha256':lc.hash_value(chosen['configuration_metrics']),'inner_checkpoint_sha256':hashes}


def run_fixed_campaign(np,minimize,expit,prepared,plan,*,fresh,before_checkpoint_integrity,directory):
    """Exactly63 new checkpoints/84 units; no admission, retry or warm start.

    Mandatory integrity hook uses the original keyword-only hook shape and
    must return singleton True. Its real implementation belongs to a future
    reviewed authorized owned controller; no Boolean alone grants authority.
    """
    assert callable(fresh) and callable(before_checkpoint_integrity)
    assert isinstance(plan,CurrentFitPlan) and isinstance(prepared,PreparedPools)
    directory=Path(directory);assert directory.is_absolute() and directory.parent.is_dir()
    directory.mkdir(parents=False,exist_ok=False)
    campaign=None;completed=[];units=0;stage='start';current=None
    try:
        fresh();assert prepared.prefit_document==plan.document()
        assert set(prepared.pools)==set(plan.document()['source_pools'])
        expected=[(lc.task_key(task),task) for task in lc.task_roster()]
        assert len(expected)==63 and sum(task['optimizer_units'] for _,task in expected)==84
        campaign=Campaign(directory/'checkpoints',plan)
        callback=make_fit_callback(np,minimize,expit,prepared,plan,fresh=fresh)
        for key,task in expected:
            current=key;stage='integrity';fresh()
            assert not campaign.failed and list(campaign.tasks.items())==expected
            result=before_checkpoint_integrity(task_key=key,task=lc.strict_json(lc.canonical_bytes(task)),
                plan=plan,prepared=prepared,campaign=campaign)
            assert result is True,'Mandatory actual integrity hook did not certify checkpoint'
            assert list(campaign.tasks.items())==expected and prepared.prefit_document==plan.document()
            fresh();check_pool(np,prepared,plan,task)
            selection=None
            if task['phase']=='outer':
                stage='selection'
                inner_keys=[k for k,t in expected if t['phase']=='inner' and t['arm']==task['arm'] and t['outer_fold']==task['outer_fold']]
                assert len(inner_keys)==6 and all(k in completed for k in inner_keys)
                selection=select_outer(prepared,campaign,task['arm'],task['outer_fold'],fresh=fresh)
            stage='checkpoint';fresh()
            receipt=campaign.write_checkpoint(key,callback,selection)
            assert receipt['optimizer_units']==task['optimizer_units']
            completed.append(key);units+=receipt['optimizer_units']
        assert completed==[key for key,_ in expected] and units==84
        stage='finish';fresh()
        return campaign.finish() # No writes or validation after successful finish.
    except BaseException as error:
        if campaign is not None:campaign.failed=True
        try:write_new(directory/'driver_failure.json',{'status':'FAILED_NEW_FIXED_RUN_NO_RESUME',
            'stage':stage,'task_key':current,'error_type':type(error).__name__,'error':str(error),
            'completed_checkpoint_keys':completed,'completed_optimizer_units':units,
            'prefit_sha256':plan.prefit_sha256,'partial_outputs_retained':True,
            'independent_replay_or_gate_complete':False})
        except BaseException as logging_error:error.add_note('Failure evidence could not be saved: '+str(logging_error))
        raise
