"""Strict identity planning on supplied metadata, never project-file readers."""
from dataclasses import dataclass
import hashlib
import json
from .spec import ARMS,CELLS,CONFIGS,COUNTS,FOLDS,POOL_HASH_FIELDS,PREFIT_STATUS
from src.generalization_knowncell_joint_implementation_20261022.contracts import checkpoint_roster


def canonical_bytes(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()


def digest(raw):return hashlib.sha256(raw).hexdigest()


def hash_value(value):return digest(canonical_bytes(value))


def valid_hash(value,length=64):
    assert isinstance(value,str) and len(value)==length and all(c in '0123456789abcdef' for c in value)
    return value


def strict_json(raw):
    assert isinstance(raw,bytes) and len(raw)<=16*2**20
    def unique(pairs):
        result={}
        for key,value in pairs:
            assert key not in result,'Duplicate JSON key'
            result[key]=value
        return result
    def nonfinite(value):raise AssertionError('Nonfinite JSON token '+value)
    return json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=nonfinite)


def id_hash(ids):
    assert isinstance(ids,list) and ids and all(isinstance(v,str) and v for v in ids)
    assert len(set(ids))==len(ids)
    return hashlib.sha256('|'.join(ids).encode()).hexdigest()


def pool_key(outer,inner):
    assert type(outer) is int and outer in FOLDS
    assert inner is None or (type(inner) is int and inner in set(FOLDS)-{outer})
    return f'outer{outer}_'+('final' if inner is None else f'inner{inner}')


def task_key(task):
    assert task['arm'] in ARMS
    pool_key(task['outer_fold'],task['inner_fold'])
    assert task['phase']==('outer' if task['inner_fold'] is None else 'inner')
    return task['arm']+'__'+pool_key(task['outer_fold'],task['inner_fold'])+'__'+task['configuration_id']


def task_roster():
    tasks=checkpoint_roster()
    assert len({task_key(task) for task in tasks})==63
    assert sum(task['phase']=='inner' for task in tasks)==54
    assert sum(task['optimizer_units'] for task in tasks)==84
    assert len({pool_key(task['outer_fold'],task['inner_fold']) for task in tasks})==9
    return tasks


def validate_prefit(document):
    """Validate declarations/ID masks; source numerical values are not opened."""
    assert isinstance(document,dict) and document['status']==PREFIT_STATUS
    assert document['counts']==COUNTS and document['arms']==list(ARMS) and document['configs']==list(CONFIGS)
    assert document['numerical_threads']==1 and document['resource_exception_applies'] is False
    valid_hash(document['runtime_binding_sha256'])
    for key in ('metadata_admission_sha256','feature_admission_sha256','label_admission_sha256','fit_source_manifest_sha256'):
        valid_hash(document[key])
    ids,folds=document['all_row_ids'],document['all_row_folds']
    id_hash(ids)
    assert len(ids)==len(folds)==COUNTS['all_rows']
    assert all(type(fold) is int and fold in FOLDS for fold in folds) and set(folds)==set(FOLDS)
    expected_pools={pool_key(outer,inner) for outer in FOLDS for inner in (None,*[f for f in FOLDS if f!=outer])}
    pools=document['source_pools'];assert set(pools)==expected_pools
    for outer in FOLDS:
        for inner in (None,*[f for f in FOLDS if f!=outer]):
            value=pools[pool_key(outer,inner)]
            held=outer if inner is None else inner
            excluded={outer} if inner is None else {outer,inner}
            training=[row_id for row_id,fold in zip(ids,folds) if fold not in excluded]
            target=[row_id for row_id,fold in zip(ids,folds) if fold==held]
            assert training and target
            assert value['training_ids']==training and value['validation_ids']==target,'Full both-cell inherited-fold ID order'
            assert value['training_ids_sha256']==id_hash(training)
            assert value['validation_ids_sha256']==id_hash(target)
            assert value['training_rows']==len(training) and value['validation_rows']==len(target)
            assert type(value['training_pairs']) is int and value['training_pairs']>0
            assert value['both_cells_confirmed'] is True and value['full_original_menus_confirmed'] is True
            assert value['gene_component_allele_contradictions']==0
            for field in POOL_HASH_FIELDS:valid_hash(value[field])
    # Full inherited-fold masks are allowed only after independent metadata
    # admission proves the reference component purge has no contradictions.
    return document


@dataclass(frozen=True)
class BoundPlan:
    prefit_relative_path:str
    prefit_commit:str
    prefit_raw:bytes
    prefit_sha256:str
    runtime_binding_sha256:str

    def document(self):return strict_json(self.prefit_raw)
    def pool(self,task):return self.document()['source_pools'][pool_key(task['outer_fold'],task['inner_fold'])]
    def identity(self):
        return {'prefit_relative_path':self.prefit_relative_path,'prefit_commit':self.prefit_commit,
                'prefit_sha256':self.prefit_sha256,'runtime_binding_sha256':self.runtime_binding_sha256,
                'source_pool_sha256':{name:hash_value(value) for name,value in self.document()['source_pools'].items()},
                'checkpoint_roster':task_roster(),'checkpoint_count':63,'optimizer_units':84,
                'metadata_and_scientific_values_independently_certified_here':False}


def bind_plan(prefit_relative_path,prefit_raw,prefit_commit,committed_reader,current_runtime_binding_sha256):
    """Compare supplied bytes to an injected exact-commit reader BEFORE parsing.

    Future admission must certify the reader's Git implementation. This module
    does not run Git, read scientific files, admit runtime packages or authorize
    an actual campaign. A caller declaration alone is not a native-origin proof.
    """
    assert isinstance(prefit_relative_path,str)
    name=prefit_relative_path.replace('\\','/')
    assert name==prefit_relative_path and not name.startswith('/') and ':' not in name
    assert all(part not in ('','..','.') for part in name.split('/')) and name.startswith('results/')
    valid_hash(prefit_commit,40);valid_hash(current_runtime_binding_sha256)
    assert callable(committed_reader) and isinstance(prefit_raw,bytes)
    assert committed_reader(name,prefit_commit)==prefit_raw,'Uncommitted/changed prefit bytes'
    document=validate_prefit(strict_json(prefit_raw))
    assert current_runtime_binding_sha256==document['runtime_binding_sha256'],'Runtime/prefit mismatch'
    return BoundPlan(name,prefit_commit,prefit_raw,digest(prefit_raw),current_runtime_binding_sha256)
