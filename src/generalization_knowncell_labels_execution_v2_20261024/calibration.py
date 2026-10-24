"""Additive fixed production adapter. No context is entered at import.

Human approval, pinned parent-owned Job, immutable birth and source checks are
mandatory through the fixed sibling common module. Public callers cannot
replace probes/modules/guards. Private helpers exist for invented tests only.
"""
from contextlib import contextmanager
import importlib
import hashlib
import math
import os
from pathlib import Path
import types

STAGES = ('metadata','array','labels','prefit','fit','replay','evaluation')
STARTUP_PHYSICAL = 512*2**20
LIVE_PHYSICAL = 256*2**20
DISK_FLOOR = COMMIT_RESERVE = 2**30
THREAD_KEYS = ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')
ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_knowncell_labels_execution_v2_20261024'
PURE_MODULE = 'src.generalization_knowncell_joint_implementation_20261022.admission'
PURE_SHA = 'dbb318fcc310102e1a3dddd9397bbdf9e6f624532d0fb7ea70d9548005f8e773'
TARGETS = (
    ('src.generalization_knowncell_joint_loader_20261022.guard','5a91012ce95b822e2cdd04bc2e4c90a0c1b2e01f7f203bb0c3b26ec69fcd353f'),
    ('src.generalization_knowncell_array_contract_20261022.validate','3d573e92f0f0e012f8979ef6dbfd7ea09b393f78c9cc1ba24c262b500960d438'),
    ('src.generalization_knowncell_joint_engine_20261023.adapter','86284cb259eec329585d078997decca776c3786044733591e811c16be3304d57'),
    ('src.generalization_knowncell_joint_replay_20261023.arithmetic','62ed6d6ec72738d8302542b058d7152d5d9e6e05f10c965aeb7c3b1388a11760'),
    ('src.generalization_knowncell_joint_evaluation_20261023.evaluation','7bcbda853d0d4e7e6b550153b089514a13ed7b44650b6d1afd017020c539c181'),
)
_ACTIVE = None
RESOURCE_BOOLEANS = {
    'every_payload_open_fresh_original_resource_gated':False,
    'fresh_original_resource_gate_before_open':False,
    'original_resource_guards_unchanged':False,
    'original_three_GiB_project_guards_unchanged':False,
    'original_3GiB_resource_guard_unchanged':False,
    'original_resource_guards_changed':True,
    'original_runtime_or_resource_guards_changed':True,
}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _hash(value):
    assert isinstance(value,str) and len(value)==64 and all(character in '0123456789abcdef' for character in value)
    return value


def _environment(environment):
    assert all(environment.get(name)=='1' for name in THREAD_KEYS),'Exactly one numerical thread'


def _snapshot(snapshot,environment,*,startup=False,real=False):
    assert isinstance(snapshot,dict)
    for key in ('physical_available','disk_available'):
        assert type(snapshot[key]) is int and snapshot[key]>=0
    assert snapshot['physical_available'] >= (STARTUP_PHYSICAL if startup else LIVE_PHYSICAL),'Knowncell calibrated physical reserve'
    assert snapshot['disk_available'] >= DISK_FLOOR,'Original one-GiB workspace disk floor'
    if real or 'commit_headroom' in snapshot:
        assert type(snapshot['commit_headroom']) is int and snapshot['commit_headroom']>=COMMIT_RESERVE,'One-GiB actual global system commit reserve'
    assert snapshot.get('PUM_resource_exception_applied',False) is False
    assert snapshot.get('PRELib_resource_exception_applied',False) is False
    _environment(environment)
    return snapshot


def _authorization(value,stage,manifest_sha):
    assert value['generation_manifest_sha256']==_hash(manifest_sha)
    assert value['approved_policy_manifest_sha256']=='a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9'
    assert value['approval_scope_sha256']=='c40b929187a35199e88523ab5c6b351789c45fddb3aebe6dcf68172684ce6495'
    assert value['approved_invocation']=='original_pandas_label_admission'
    _hash(value['approval_sha256'])
    assert value['explicit_human_approval'] is True and value['owned_job_required'] is True
    assert value['allowed_stages']==list(STAGES) and stage in STAGES
    return value


def _owner(value,manifest_sha,evidence):
    assert value['manifest_sha256']==manifest_sha
    assert value['current_pid']==os.getpid() and value['parent_pid']==os.getppid()
    assert type(value['current_pid']) is int and type(value['parent_pid']) is int
    assert value['parent_pid']==evidence['parent_pid']
    assert value['birth_sha256']==_hash(evidence['birth_sha256'])
    assert value['in_owned_job'] is True and value['continuous_monitoring_owned_by_controller'] is True
    if value.get('stage_controller_admission_sha256') is not None:
        assert value['stage_controller_admission_sha256']==_hash(evidence['stage_controller_admission_sha256'])
    return value


def _resource_key(name):
    low = name.lower()
    return 'original' in low and any(token in low for token in ('resource','guard','floor'))


def _check_scientific_subtree(value):
    """Never rewrite hashes/IDs/metadata/contracts to hide resource provenance."""
    if isinstance(value,dict):
        for key,item in value.items():
            assert not _resource_key(key),'Resource claim inside protected scientific metadata/contract; needs separate integration'
            _check_scientific_subtree(item)
    elif isinstance(value,list):
        for item in value:_check_scientific_subtree(item)


def _annotated_copy(value,path,changes):
    if isinstance(value,dict):
        result = {}
        for key,item in value.items():
            assert isinstance(key,str)
            current = path+[key]
            if key in ('metadata','contract'):
                _check_scientific_subtree(item)
                result[key] = _plain_copy(item)
            elif key in RESOURCE_BOOLEANS:
                assert type(item) is bool,'Reviewed resource annotation must remain boolean'
                replacement = RESOURCE_BOOLEANS[key]
                result[key] = replacement
                changes.append({'path':current,'previous_value':item,'calibrated_value':replacement})
            elif key=='fresh_original_resource_gates_checked' and type(item) is int:
                assert 'calibrated_resource_gates_checked' not in value,'Conflicting calibration count alias'
                result['calibrated_resource_gates_checked'] = item
                changes.append({'path':current,'renamed_to':'calibrated_resource_gates_checked','previous_value':item})
            elif key=='original_scientific_guards_changed':
                assert item is False,'Resource calibration never authorizes scientific guard changes'
                result[key] = False
            elif _resource_key(key):
                raise AssertionError('Unreviewed original-resource/guard annotation; requires separate explicit integration: '+key)
            elif key=='status' and isinstance(item,str) and 'ORIGINAL_FLOOR' in item:
                result[key] = item.replace('ORIGINAL_FLOOR','BOUNDED_RESOURCE_CALIBRATION')
                changes.append({'path':current,'previous_value':item,'calibrated_value':result[key]})
            else:
                result[key] = _annotated_copy(item,current,changes)
        return result
    if isinstance(value,list):
        return [_annotated_copy(item,path+[index],changes) for index,item in enumerate(value)]
    return _plain_copy(value)


def _plain_copy(value):
    if isinstance(value,dict):return {key:_plain_copy(item) for key,item in value.items()}
    if isinstance(value,list):return [_plain_copy(item) for item in value]
    assert value is None or type(value) in (str,int,float,bool),'Annotate JSON receipts only, never software/data arrays'
    if type(value) is float:assert math.isfinite(value)
    return value


class _Session:
    """Private dependency injection is confined to invented helper tests."""
    def __init__(self,stage,manifest_sha,authorization,owner,evidence,memory,common):
        self.stage,self.manifest_sha = stage,manifest_sha
        self.authorization,self.owner,self.evidence = authorization,owner,dict(evidence)
        self._memory,self._common = memory,common
        self.calls = 0
        self.restored = False
        self.failed = False
        self._targets = []
        self._wrapper = None
        self.minimum_physical = self.minimum_commit = None

    def _real_check(self,*,startup=False):
        _environment(os.environ)
        _owner(self._common.verify_owner(self.stage,self.manifest_sha,self.evidence),self.manifest_sha,self.evidence)
        actual = self._memory()  # Public path always supplies unchanged headless.memory.
        _snapshot(actual,os.environ,startup=startup,real=True)
        for attribute,key in (('minimum_physical','physical_available'),('minimum_commit','commit_headroom')):
            old = getattr(self,attribute)
            setattr(self,attribute,actual[key] if old is None else min(old,actual[key]))
        return actual

    def _aliases(self):
        assert _ACTIVE is self and self._targets and self._wrapper is not None,'No active owned calibration context'
        assert all(module.require_resources is self._wrapper for module,_ in self._targets),'Calibration alias replaced while active'

    def _invoke(self,snapshot,environment):
        self.calls += 1
        try:
            assert not self.failed,'Failed resource session cannot continue'
            self._aliases()
            _snapshot(snapshot,environment)
            actual = self._real_check()
            return {'fresh_resource_probe_required':True,'RAM_floor':LIVE_PHYSICAL,'disk_floor':DISK_FLOOR,
                    'numerical_threads':1,'PUM_resource_exception_applies':False,
                    'original_resource_guards_unchanged':False,'bounded_knowncell_calibration_applied':True,
                    'stage':self.stage,'execution_manifest_sha256':self.manifest_sha,
                    'actual_global_commit_headroom':actual['commit_headroom']}
        except BaseException:
            self.failed = True
            raise

    def annotate(self,payload):
        assert isinstance(payload,dict) and 'resource_calibration' not in payload,'No duplicate resource annotation'
        assert not self.failed,'Cannot certify a receipt after a failed resource check'
        changes = []
        result = _annotated_copy(payload,[],changes)
        result['original_resource_guards_unchanged'] = False
        result['resource_calibration'] = {'status':'EXPLICITLY_AUTHORIZED_BOUNDED_KNOWNCELL_RESOURCE_CALIBRATION',
            'stage':self.stage,'execution_manifest_sha256':self.manifest_sha,
            'authorization_sha256':self.authorization['approval_sha256'],'birth_sha256':self.owner['birth_sha256'],
            'current_pid':self.owner['current_pid'],'parent_pid':self.owner['parent_pid'],
            'startup_physical_floor':STARTUP_PHYSICAL,'live_physical_floor':LIVE_PHYSICAL,
            'disk_floor':DISK_FLOOR,'live_global_commit_reserve':COMMIT_RESERVE,
            'fresh_calibrated_guard_calls':self.calls,'callbacks_restored_at_annotation':self.restored,
            'minimum_observed_physical_available':self.minimum_physical,
            'minimum_observed_global_commit_headroom':self.minimum_commit,
            'hard_job_caps_and_continuous_monitoring_owned_by_controller':True,
            'exact_parent_job_handle_not_queried_by_adapter':True,
            'scientific_metadata_and_contracts_unchanged':True,
            'scientific_protocol_settings_changed':False,'resource_annotation_changes':changes}
        if self.owner.get('stage_controller_admission_sha256') is not None:
            result['resource_calibration']['stage_controller_admission_sha256'] = _hash(self.owner['stage_controller_admission_sha256'])
        result['resource_calibration']['approved_policy_manifest_sha256']=self.authorization['approved_policy_manifest_sha256']
        result['resource_calibration']['approval_scope_sha256']=self.authorization['approval_scope_sha256']
        result['resource_calibration']['invocation']='original_pandas_label_admission'
        return result


@contextmanager
def _installed(session,modules,original):
    """Private testable alias transaction; public API fixes every dependency."""
    global _ACTIVE
    assert _ACTIVE is None,'Duplicate or nested calibration context'
    assert len(modules)==len(TARGETS)==5 and len({id(module) for module in modules})==5
    assert [module.__name__ for module in modules]==[name for name,_ in TARGETS]
    assert all(module.require_resources is original for module in modules),'Original resource alias already replaced'
    saved = [(module,module.require_resources) for module in modules]
    session._targets = saved
    session._wrapper = session._invoke
    installed = []
    body_error = None
    _ACTIVE = session
    try:
        for module,_ in saved:
            module.require_resources = session._wrapper
            installed.append(module)
        yield session
        assert not session.failed,'A caught resource failure cannot leave a successful context'
    except BaseException as error:
        body_error = error
        session.failed = True
        raise
    finally:
        missing = object()
        replaced = [module.__name__ for module in installed if getattr(module,'require_resources',missing) is not session._wrapper]
        restoration_errors = []
        for module,previous in reversed(saved):
            try:module.require_resources = previous
            except BaseException as error:restoration_errors.append(type(error).__name__+': '+str(error))
        session.restored = not restoration_errors and all(getattr(module,'require_resources',missing) is previous for module,previous in saved)
        _ACTIVE = None
        if replaced or restoration_errors or not session.restored:
            session.failed = True
            raise RuntimeError('Resource alias transaction integrity failure: replaced='+repr(replaced)+' restore_errors='+repr(restoration_errors)) from body_error


def _source_module(name,expected):
    module = importlib.import_module(name)
    path = ROOT/(name.replace('.','/')+'.py')
    assert Path(module.__file__).resolve()==path.resolve()
    assert _sha(path.read_bytes())==expected,'Frozen resource-binding source changed'
    return module


@contextmanager
def calibrated(stage,manifest_sha,owner_evidence):
    """PROPOSED; actual entry requires committed human approval and owned Job.

    Never callable standalone: fixed common admission/owner verification must
    succeed. No production callback is changed before those checks and startup.
    """
    assert stage=='labels' and type(stage) is str
    _hash(manifest_sha)
    assert _ACTIVE is None,'Duplicate or nested calibration context'
    common = importlib.import_module('src.'+NS+'.common')
    authorization = _authorization(common.admit_authorization(manifest_sha),stage,manifest_sha)
    owner = _owner(common.verify_owner(stage,manifest_sha,owner_evidence),manifest_sha,owner_evidence)
    from src.generalization_pum_process_probe_20261021 import headless
    session = _Session(stage,manifest_sha,authorization,owner,owner_evidence,headless.memory,common)
    session._real_check(startup=True)
    pure = _source_module(PURE_MODULE,PURE_SHA)
    original = pure.require_resources
    assert isinstance(original,types.FunctionType) and original.__module__==PURE_MODULE
    assert Path(original.__code__.co_filename).resolve()==Path(pure.__file__).resolve()
    modules = [_source_module(name,expected) for name,expected in TARGETS]
    with _installed(session,modules,original):
        yield session
        # Even if the body catches a guard exception it cannot receive a clean
        # exit. Final auth/owner/resource checks precede unconditional restore.
        assert not session.failed
        assert common.admit_authorization(manifest_sha)==authorization,'Authorization/source identity changed during stage'
        session._real_check()
        assert pure.require_resources is original,'Pure original admission function was changed'
