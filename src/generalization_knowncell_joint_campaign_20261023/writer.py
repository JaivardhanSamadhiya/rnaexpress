"""Exclusive-write lifecycle only. No numerical/runtime/project loading code."""
import math
import os
from pathlib import Path
from .spec import ARMS,CELLS,CONFIGS,FEATURE_WIDTH,CANONICAL_MEAN,METHOD,OPTIONS,SCORER
from .contracts import (BoundPlan,canonical_bytes,digest,hash_value,valid_hash,strict_json,
                        task_key,task_roster,pool_key,id_hash,validate_prefit)
from src.generalization_knowncell_joint_implementation_20261022.admission import birth_identity


def write_new(path,value):
    raw=canonical_bytes(value)
    with Path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return digest(raw)


def read_object(path):return strict_json(Path(path).read_bytes())


def unit_spec(arm):
    assert arm in ARMS
    return [(cell,102) for cell in CELLS] if arm=='independent' else [('joint',204)] if arm=='joint_shrink10' else [('pooled',102)]


class UnitCalls:
    """Count actual supplied callable invocations, not a reported integer.

    A future source-frozen adapter must wrap each real minimize call here.
    This counter alone cannot prove that arbitrary callbacks implement SciPy.
    """
    def __init__(self,arm):self.expected=unit_spec(arm);self.calls=[]
    def invoke(self,name,dimension,callback,*args,**kwargs):
        assert callable(callback) and len(self.calls)<len(self.expected)
        assert type(dimension) is int and (name,dimension)==self.expected[len(self.calls)]
        self.calls.append({'name':name,'dimension':dimension,'started':True,'returned':False})
        value=callback(*args,**kwargs)
        self.calls[-1]['returned']=True
        return value
    def complete(self):
        assert [(v['name'],v['dimension']) for v in self.calls]==self.expected
        assert all(value['returned'] is True for value in self.calls)
        return list(self.calls)


def check_model(model,task,config,pool):
    assert isinstance(model,dict) and model['arm']==task['arm'] and model['config']==config
    required={'arm','config','feature_width','canonical_mean','canonical_scorer','optimizer_method',
              'optimizer_options','training_rows','training_pairs','optimizer_units','scaling',
              'objective','optimizer_summaries'}
    required|={'heads'} if task['arm']=='independent' else {'beta','delta'} if task['arm']=='joint_shrink10' else {'beta'}
    assert set(model)==required,'No alternate or additional model heads/fields'
    assert model['feature_width']==FEATURE_WIDTH and model['canonical_mean']==CANONICAL_MEAN
    assert model['canonical_scorer']==SCORER and model['optimizer_method']==METHOD and model['optimizer_options']==OPTIONS
    assert model['training_rows']==pool['training_rows'] and model['training_pairs']==pool['training_pairs']
    assert model['optimizer_units']==task['optimizer_units']
    scaling=model['scaling'];assert set(scaling)=={'pair_rms','scale','active','mean'}
    assert hash_value(scaling)==pool['common_scaling_sha256'],'Model does not match the pre-birth source scaling'
    assert scaling['mean']==[0.]*FEATURE_WIDTH
    active=scaling['active'];assert len(active)==FEATURE_WIDTH and all(type(v) is bool for v in active)
    for rms,scale,use in zip(scaling['pair_rms'],scaling['scale'],active):
        assert type(rms) in (int,float) and math.isfinite(rms) and rms>=0
        assert type(scale) in (int,float) and math.isfinite(scale) and scale>0
        assert use==(rms>=1e-8) and scale==(rms if use else 1.)
    assert len(scaling['pair_rms'])==len(scaling['scale'])==FEATURE_WIDTH
    coefficients=[model['heads'][cell] for cell in CELLS] if task['arm']=='independent' else [model['beta']]+([model['delta']] if task['arm']=='joint_shrink10' else [])
    if task['arm']=='independent':assert set(model['heads'])==set(CELLS)
    for vector in coefficients:
        assert len(vector)==FEATURE_WIDTH
        assert all(type(v) in (int,float) and math.isfinite(v) and (use or v==0.) for v,use in zip(vector,active))
    assert type(model['objective']) in (int,float) and math.isfinite(model['objective'])
    assert set(model['optimizer_summaries'])=={name for name,_ in unit_spec(task['arm'])}
    for value in model['optimizer_summaries'].values():
        assert set(value)=={'objective','success','message','iterations','maximum_gradient_abs'}
        assert value['success'] is True and isinstance(value['message'],str)
        assert type(value['iterations']) is int and value['iterations']>=0
        assert type(value['objective']) in (int,float) and math.isfinite(value['objective'])
        assert type(value['maximum_gradient_abs']) in (int,float) and math.isfinite(value['maximum_gradient_abs']) and value['maximum_gradient_abs']>=0
    objectives=[value['objective'] for value in model['optimizer_summaries'].values()]
    expected_objective=.5*math.fsum(objectives) if task['arm']=='independent' else objectives[0]
    assert model['objective']==expected_objective
    canonical_bytes(model) # No pickle, nonfinite token or unserializable object.


def check_predictions(predictions,pool):
    assert set(predictions)=={'row_ids','scores','canonical_shape','canonical_dtype','canonical_order','canonical_scorer'}
    assert predictions['row_ids']==pool['validation_ids'],'Not the complete original target ID order'
    assert id_hash(predictions['row_ids'])==pool['validation_ids_sha256']
    assert predictions['canonical_shape']==[pool['validation_rows'],FEATURE_WIDTH]
    assert predictions['canonical_dtype']=='float64' and predictions['canonical_order']=='C'
    assert predictions['canonical_scorer']==SCORER
    scores=predictions['scores']
    assert isinstance(scores,list) and len(scores)==pool['validation_rows']
    assert all(type(value) in (int,float) and math.isfinite(value) for value in scores)


class Campaign:
    """Only a newly created directory can start; a failed run cannot resume."""
    def __init__(self,directory,plan):
        assert isinstance(plan,BoundPlan)
        assert digest(plan.prefit_raw)==plan.prefit_sha256
        assert validate_prefit(plan.document())['runtime_binding_sha256']==plan.runtime_binding_sha256
        valid_hash(plan.prefit_commit,40)
        self.directory=Path(directory);self.plan=plan
        self.directory.mkdir(parents=False,exist_ok=False)
        self.identity=plan.identity()
        self.run_birth_sha=write_new(self.directory/'campaign_birth.json',{'status':'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS',**self.identity})
        self.tasks={task_key(task):task for task in task_roster()}
        self.failed=False

    def paths(self,key):
        assert key in self.tasks
        return [self.directory/(key+suffix) for suffix in ('.birth.json','.model.json','.complete.json')]

    def selection(self,task,value):
        """Bind the supplied source-only receipt to all six completed inner fits.

        No selection arithmetic is claimed here. The future independent replay
        must recompute the frozen paired OOF criterion and its lambda choice.
        """
        assert isinstance(value,dict) and value['arm']==task['arm'] and value['outer_fold']==task['outer_fold']
        assert value['selected_config'] in CONFIGS
        assert value['source_only'] is True and value['primary_paired_only'] is True
        assert value['selection_rule']=='concatenated_paired_OOF_equal_cell_component_context_direction_regret'
        assert value['prefit_sha256']==self.plan.prefit_sha256 and value['runtime_binding_sha256']==self.plan.runtime_binding_sha256
        assert value['source_training_ids_sha256']==self.plan.pool(task)['training_ids_sha256']
        valid_hash(value['configuration_metrics_sha256'])
        expected={}
        for key,inner in self.tasks.items():
            if inner['arm']==task['arm'] and inner['outer_fold']==task['outer_fold'] and inner['phase']=='inner':
                complete=self.check_saved(key)
                expected[key]=complete['model_sha256']
        assert len(expected)==6 and value['inner_checkpoint_sha256']==expected
        return dict(value['selected_config']),hash_value(value)

    def write_checkpoint(self,key,optimizer_callback,selection=None):
        assert not self.failed and callable(optimizer_callback) and key in self.tasks
        assert not (self.directory/'campaign_complete.json').exists()
        paths=self.paths(key);assert not any(path.exists() for path in paths),'Partial resume/overwrite is forbidden'
        task=self.tasks[key];pool=self.plan.pool(task)
        if task['phase']=='inner':
            assert selection is None
            config=next(dict(v) for v in CONFIGS if v['id']==task['configuration_id']);selection_sha=None
        else:config,selection_sha=self.selection(task,selection)
        hashes={field:pool[field] for field in ('training_ids_sha256','training_metadata_sha256','training_features_sha256',
                'training_effects_sha256','original_pair_roster_sha256','pair_weights_sha256','common_scaling_sha256')}
        identity=birth_identity(arm=task['arm'],phase=task['phase'],outer_fold=task['outer_fold'],inner_fold=task['inner_fold'],
                                configuration=config,runtime_binding_sha256=self.plan.runtime_binding_sha256,prefit_sha256=self.plan.prefit_sha256,**hashes)
        birth={'task_key':key,'identity':identity,'campaign_birth_sha256':self.run_birth_sha,
               'source_pool_sha256':hash_value(pool),'validation_ids_sha256':pool['validation_ids_sha256'],
               'validation_metadata_sha256':pool['validation_metadata_sha256'],
               'validation_features_sha256':pool['validation_features_sha256'],'validation_effects_sha256':pool['validation_effects_sha256'],
               'validation_rows':pool['validation_rows'],'full_validation_shape':[pool['validation_rows'],FEATURE_WIDTH],
               'prefit_commit':self.plan.prefit_commit,'source_only_selection_sha256':selection_sha,
               'source_only_selection':selection}
        birth_sha=write_new(paths[0],birth) # Durable exclusive write BEFORE callback.
        units=UnitCalls(task['arm'])
        try:
            # Deep JSON copies prevent callback mutation of live birth/plan state.
            answer=optimizer_callback(strict_json(canonical_bytes(task)),strict_json(canonical_bytes(birth)),units)
            calls=units.complete()
            assert isinstance(answer,dict) and set(answer)=={'model','predictions'}
            check_model(answer['model'],task,config,pool);check_predictions(answer['predictions'],pool)
            assert digest(paths[0].read_bytes())==birth_sha,'Birth bytes changed during callback'
            model_sha=write_new(paths[1],{'task_key':key,'birth_sha256':birth_sha,
                                        'model':answer['model'],'predictions':answer['predictions']})
            receipt={'status':'CHECKPOINT_LIFECYCLE_COMPLETE_NOT_NUMERICAL_REPLAY','task_key':key,
                     'birth_sha256':birth_sha,'model_sha256':model_sha,'optimizer_invocations':calls,
                     'optimizer_units':len(calls),'configuration':config,
                     'source_only_selection_sha256':selection_sha,'campaign_birth_sha256':self.run_birth_sha}
            write_new(paths[2],receipt)
            return receipt
        except BaseException as error:
            self.failed=True
            write_new(self.directory/(key+'.failure.json'),{'status':'FAILED_NO_RESUME','task_key':key,'birth_sha256':birth_sha,
                      'error_type':type(error).__name__,'error':str(error),'optimizer_invocations':units.calls})
            raise

    def check_saved(self,key):
        birth_path,model_path,complete_path=self.paths(key)
        birth,model,complete=[read_object(path) for path in (birth_path,model_path,complete_path)]
        task=self.tasks[key];pool=self.plan.pool(task)
        assert complete['status']=='CHECKPOINT_LIFECYCLE_COMPLETE_NOT_NUMERICAL_REPLAY'
        assert birth['task_key']==model['task_key']==complete['task_key']==key
        assert complete['birth_sha256']==model['birth_sha256']==digest(birth_path.read_bytes())
        assert complete['model_sha256']==digest(model_path.read_bytes())
        assert birth['campaign_birth_sha256']==complete['campaign_birth_sha256']==self.run_birth_sha
        assert digest((self.directory/'campaign_birth.json').read_bytes())==self.run_birth_sha
        assert birth['source_pool_sha256']==hash_value(pool)
        identity=birth['identity']
        assert identity['prefit_sha256']==self.plan.prefit_sha256 and identity['runtime_binding_sha256']==self.plan.runtime_binding_sha256
        assert identity['arm']==task['arm'] and identity['phase']==task['phase'] and identity['outer_fold']==task['outer_fold'] and identity['inner_fold']==task['inner_fold']
        assert identity['configuration']==complete['configuration']
        for field in ('training_ids_sha256','training_metadata_sha256','training_features_sha256','training_effects_sha256',
                      'original_pair_roster_sha256','pair_weights_sha256','common_scaling_sha256'):
            assert identity[field]==pool[field]
        expected_identity=birth_identity(arm=task['arm'],phase=task['phase'],outer_fold=task['outer_fold'],inner_fold=task['inner_fold'],
                   configuration=complete['configuration'],runtime_binding_sha256=self.plan.runtime_binding_sha256,prefit_sha256=self.plan.prefit_sha256,
                   **{field:pool[field] for field in ('training_ids_sha256','training_metadata_sha256','training_features_sha256','training_effects_sha256',
                                                     'original_pair_roster_sha256','pair_weights_sha256','common_scaling_sha256')})
        assert identity==expected_identity
        for field in ('validation_ids_sha256','validation_metadata_sha256','validation_features_sha256','validation_effects_sha256','validation_rows'):
            assert birth[field]==pool[field]
        assert birth['prefit_commit']==self.plan.prefit_commit
        assert birth['full_validation_shape']==[pool['validation_rows'],FEATURE_WIDTH]
        if task['phase']=='inner':
            assert complete['configuration']==next(v for v in CONFIGS if v['id']==task['configuration_id'])
            assert birth['source_only_selection_sha256'] is None
            assert birth['source_only_selection'] is None
        else:
            selected,selection_sha=self.selection(task,birth['source_only_selection'])
            assert selected==complete['configuration'] and selection_sha==birth['source_only_selection_sha256']
        assert birth['source_only_selection_sha256']==complete['source_only_selection_sha256']
        calls=complete['optimizer_invocations']
        assert [(v['name'],v['dimension']) for v in calls]==unit_spec(task['arm'])
        assert all(v['started'] is True and v['returned'] is True for v in calls)
        assert complete['optimizer_units']==task['optimizer_units']==len(calls)
        check_model(model['model'],task,complete['configuration'],pool);check_predictions(model['predictions'],pool)
        return complete

    def finish(self):
        assert not self.failed and not (self.directory/'campaign_complete.json').exists()
        assert digest((self.directory/'campaign_birth.json').read_bytes())==self.run_birth_sha
        expected={'campaign_birth.json'}|{path.name for key in self.tasks for path in self.paths(key)}
        assert {path.name for path in self.directory.iterdir()}==expected,'Incomplete/extra/failed roster'
        receipts=[self.check_saved(key) for key in self.tasks]
        assert len(receipts)==63 and sum(v['optimizer_units'] for v in receipts)==84
        result={'status':'COMPLETE63_CHECKPOINT84_UNIT_LIFECYCLE_NOT_SCIENTIFIC_REPLAY_OR_GATE',
                **self.identity,'campaign_birth_sha256':self.run_birth_sha,
                'inner_checkpoints':54,'outer_checkpoints':9,
                'checkpoint_receipt_sha256':{key:digest(self.paths(key)[2].read_bytes()) for key in self.tasks},
                'independent_numeric_and_selection_replay_complete':False,'biological_or_gate_claim':False}
        write_new(self.directory/'campaign_complete.json',result)
        return result
