"""Mocked software objects only; never call real guard, bootstrap or proof."""
from contextlib import ExitStack, contextmanager
import copy
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from . import contracts as c, provider as p
from . import bootstrap as explicit_bootstrap
from .spec import *
from src.generalization_knowncell_joint_implementation_20261022.admission import require_resources

ENV = {name:'1' for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS',
                            'PYTHONUTF8','PYTHONDONTWRITEBYTECODE')}


def binding():
    return {'request_relative_path':REQUEST,'request_sha256':'a'*64,
            'provider_preparation_manifest_sha256':'b'*64,
            'software_status_sha256':SOFTWARE_STATUS_SHA,'pandas_admission_sha256':PANDAS_ADMISSION_SHA}


def proof_fixture():
    inventory = {'files':{name+'/__init__.py':str(i)*64 for i,name in enumerate(('numpy','pandas','scipy'),1)},
                 'native_files':{'numpy.libs/openblas.dll':'4'*64,'scipy.libs/openblas.dll':'5'*64},
                 'current_python_native_files':{'invented_python3.dll':'6'*64}}
    pools = [{'num_threads':1,'user_api':'blas','filepath':str(SCIENTIFIC_PREFIX/name)} for name in inventory['native_files']]
    proof = {'current_python_inventory_sha256':'7'*64,'v3_payload_inventory_sha256':'8'*64,
             'python_version':'invented-current-CP312','actually_loaded_Python_DLLs':{'invented_python3.dll':'6'*64},
             'actually_loaded_current_python_native_files':{'invented_python3.dll':'6'*64},
             'actually_loaded_scientific_modules':dict(inventory['files']),
             'actually_loaded_scientific_native_files':{str((SCIENTIFIC_PREFIX/name).resolve()):sha for name,sha in inventory['native_files'].items()},
             'actually_loaded_threadpools':pools,'old_interpreter_bitwise_parity_established':False,
             'old_exact_runtime_identity_passes':False,'fresh_full_NumPy_payload_check':True,
             'unused_pandas_SciPy_files_freshly_rehashed_in_worker':False,
             'possible_bytecode_payload_proof':{'status':'PASS_EXISTING_POSSIBLE_BYTECODE_PAYLOADS_BOUND','possible_existing_bytecode_payloads':{}},
             'two_explicit_root_cache_admissions':{'invented-root-cache':'9'*64}}
    return inventory,proof


@contextmanager
def invented_runtime(snapshots=None):
    inventory,proof = proof_fixture()
    np = SimpleNamespace(__name__='numpy',__version__='1.26.4',__file__=str(SCIENTIFIC_PREFIX/'numpy/__init__.py'))
    pd = SimpleNamespace(__name__='pandas',__version__='2.2.3',__file__=str(SCIENTIFIC_PREFIX/'pandas/__init__.py'))
    scipy = SimpleNamespace(__name__='scipy',__version__='1.14.1',__file__=str(SCIENTIFIC_PREFIX/'scipy/__init__.py'))
    minimize,expit = Mock(name='invented_minimize_never_called'),Mock(name='invented_expit_never_called')
    threadpoolctl = SimpleNamespace(__name__='threadpoolctl')
    current = SimpleNamespace(flags=SimpleNamespace(no_site=1,dont_write_bytecode=1),dont_write_bytecode=True,
                              implementation=SimpleNamespace(cache_tag='cpython-312'),version_info=(3,12),
                              pycache_prefix=str(CACHE_PREFIX),modules={})
    values = (np,pd,scipy,minimize,expit,threadpoolctl,{'invented_runtime':True},inventory,{'invented_python_payload':True})
    def bootstrap():
        current.modules.update(numpy=np,pandas=pd,scipy=scipy,threadpoolctl=threadpoolctl)
        current.modules['scipy.optimize'] = SimpleNamespace(minimize=minimize)
        current.modules['scipy.special'] = SimpleNamespace(expit=expit)
        return values
    functions = SimpleNamespace(bootstrap=Mock(side_effect=bootstrap),actual_proof=Mock(side_effect=lambda *args:copy.deepcopy(proof)))
    admission = {'manifest':{'files':{SOURCE:'c'*64}},'origin':{'final':copy.deepcopy(proof)},'certificate':{'invented':True}}
    samples = iter(snapshots) if snapshots is not None else None
    def fake_real_gate_no_arguments():
        snapshot = next(samples) if samples is not None else {'physical_available':3*2**30,'disk_available':2**30}
        require_resources(snapshot,ENV)
        return snapshot
    with ExitStack() as stack:
        stack.enter_context(patch.object(p,'_OWNED',None))
        stack.enter_context(patch.object(p,'_FAILED',False))
        stack.enter_context(patch.object(p,'sys',current))
        stack.enter_context(patch.dict(p.os.environ,ENV))
        stack.enter_context(patch.object(p.os.path,'lexists',return_value=False))
        gate = stack.enter_context(patch.object(p.guard,'fresh_gate',side_effect=fake_real_gate_no_arguments))
        admit = stack.enter_context(patch.object(p,'admit',return_value=admission))
        module = stack.enter_context(patch.object(p,'runtime_module',return_value=functions))
        stack.enter_context(patch.object(p,'bootstrap_runtime',side_effect=functions.bootstrap))
        yield SimpleNamespace(np=np,pd=pd,functions=functions,proof=proof,inventory=inventory,
                              current=current,admission=admission,admit=admit,module=module,gate=gate)
    minimize.assert_not_called();expit.assert_not_called()


class Cases(unittest.TestCase):
    def test_public_API_has_no_resource_bootstrap_or_proof_callback(self):
        self.assertEqual(set(inspect.signature(p.provide).parameters),{'request_binding','phase','root_start'})

    def test_two_phases_bootstrap_once_retain_objects_and_distinct_origin_hashes(self):
        with invented_runtime() as runtime:
            first = p.provide(binding(),phase='before_array',root_start=True)
            second = p.provide(binding(),phase='after_array',root_start=True)
            self.assertIs(first['np'],second['np']);self.assertIs(first['pd'],second['pd'])
            self.assertEqual(runtime.functions.bootstrap.call_count,1)
            self.assertEqual(runtime.functions.actual_proof.call_count,4)
            for result,phase in ((first,'before_array'),(second,'after_array')):
                self.assertEqual(set(result),{'np','pd','minimize','expit','actual_origin_receipt_sha256','fresh_origin_proof','fresh_origin_proof_sha256'})
                self.assertEqual(result['actual_origin_receipt_sha256'],PROFILE_ORIGIN_SHA)
                proof = result['fresh_origin_proof']
                self.assertEqual(proof['request_binding'],binding());self.assertEqual(proof['phase'],phase)
                self.assertEqual(result['fresh_origin_proof_sha256'],c.digest(c.canonical(proof)))
                self.assertNotEqual(result['fresh_origin_proof_sha256'],PROFILE_ORIGIN_SHA)
                self.assertFalse(proof['input_or_FIT_admission_granted_here'])

    def test_low_RAM_stops_before_static_admission_and_bootstrap(self):
        with invented_runtime([{'physical_available':3*2**30-1,'disk_available':2**30}]) as runtime:
            with self.assertRaisesRegex(AssertionError,'three-GiB'):
                p.provide(binding(),phase='before_array',root_start=True)
            runtime.admit.assert_not_called();runtime.module.assert_not_called()

    def test_wrong_software_SHA_and_wrong_request_path_stop_before_bootstrap(self):
        for field,value in (('software_status_sha256','0'*64),('pandas_admission_sha256','0'*64),('request_relative_path','results/another/request.json')):
            with invented_runtime() as runtime:
                damaged = binding();damaged[field] = value
                with self.subTest(field=field),self.assertRaises(AssertionError):
                    p.provide(damaged,phase='before_array',root_start=True)
                runtime.admit.assert_not_called();runtime.module.assert_not_called()

    def test_changed_request_binding_rejected_before_second_native_call(self):
        with invented_runtime() as runtime:
            p.provide(binding(),phase='before_array',root_start=True)
            count = runtime.functions.actual_proof.call_count
            changed = binding();changed['request_sha256'] = 'd'*64
            with self.assertRaisesRegex(AssertionError,'binding changed'):
                p.provide(changed,phase='after_array',root_start=True)
            self.assertEqual(runtime.functions.actual_proof.call_count,count)
            self.assertEqual(runtime.functions.bootstrap.call_count,1)

    def test_initial_post_phase_and_duplicate_phase_rejected(self):
        with invented_runtime() as runtime:
            with self.assertRaisesRegex(AssertionError,'Initial phase'):
                p.provide(binding(),phase='after_array',root_start=True)
            runtime.module.assert_not_called()
        with invented_runtime() as runtime:
            p.provide(binding(),phase='before_array',root_start=True)
            with self.assertRaisesRegex(AssertionError,'duplicate'):
                p.provide(binding(),phase='before_array',root_start=True)
            self.assertEqual(runtime.functions.bootstrap.call_count,1)

    def test_exact_S_B_and_absent_cache_mode_required(self):
        for defect in ('site','bytecode','cache'):
            with invented_runtime() as runtime:
                if defect == 'site':runtime.current.flags.no_site = 0
                elif defect == 'bytecode':runtime.current.flags.dont_write_bytecode = 0
                else:runtime.current.pycache_prefix = str(ROOT/'wrong_cache')
                with self.subTest(defect=defect),self.assertRaises(AssertionError):
                    p.provide(binding(),phase='before_array',root_start=True)
                runtime.module.assert_not_called()

    def test_existing_cache_prefix_is_rejected_without_bootstrap(self):
        with invented_runtime() as runtime,patch.object(p.os.path,'lexists',return_value=True):
            with self.assertRaisesRegex(AssertionError,'absent cache'):
                p.provide(binding(),phase='before_array',root_start=True)
            runtime.module.assert_not_called()

    def test_changed_Git_source_admission_stops_before_bootstrap(self):
        with invented_runtime() as runtime:
            runtime.admit.side_effect = AssertionError('Git source bytes differ')
            with self.assertRaisesRegex(AssertionError,'Git source'):
                p.provide(binding(),phase='before_array',root_start=True)
            runtime.module.assert_not_called()

    def test_read_bound_rejects_wrong_SHA_and_Git_bytes(self):
        raw = b'invented source bytes'
        with patch.object(p.guard,'guarded_bytes',return_value=raw),patch.object(p.loader,'_committed') as committed:
            with self.assertRaises(AssertionError):
                p.read_bound('src/invented.py','0'*64)
            committed.assert_not_called()
            committed.side_effect = AssertionError('not exact committed bytes')
            with self.assertRaisesRegex(AssertionError,'exact committed'):
                p.read_bound('src/invented.py',c.digest(raw))

    def test_fresh_proof_wrong_native_identity_or_threads_cannot_pass(self):
        for defect in ('python','module','threads','cache'):
            with invented_runtime() as runtime:
                proof = copy.deepcopy(runtime.proof)
                if defect == 'python':proof['current_python_inventory_sha256'] = '0'*64
                elif defect == 'module':proof['actually_loaded_scientific_modules']['numpy/__init__.py'] = '0'*64
                elif defect == 'threads':proof['actually_loaded_threadpools'][0]['num_threads'] = 2
                else:proof['possible_bytecode_payload_proof']['possible_existing_bytecode_payloads']['cache'] = 'bad'
                runtime.functions.actual_proof.side_effect = lambda *args:copy.deepcopy(proof)
                with self.subTest(defect=defect),self.assertRaises(AssertionError):
                    p.provide(binding(),phase='before_array',root_start=True)
                self.assertTrue(p._FAILED)
                with self.assertRaisesRegex(AssertionError,'cannot resume'):
                    p.provide(binding(),phase='before_array',root_start=True)

    def test_resource_drop_after_initial_proof_cannot_return_acceptance(self):
        good = {'physical_available':3*2**30,'disk_available':2**30}
        bad = {'physical_available':3*2**30-1,'disk_available':2**30}
        with invented_runtime([good,good,good,good,bad]) as runtime:
            with self.assertRaisesRegex(AssertionError,'three-GiB'):
                p.provide(binding(),phase='before_array',root_start=True)
            self.assertEqual(runtime.functions.bootstrap.call_count,1)
            self.assertEqual(runtime.functions.actual_proof.call_count,1)
            self.assertTrue(p._FAILED)

    def test_changed_software_objects_before_refresh_are_rejected(self):
        with invented_runtime() as runtime:
            p.provide(binding(),phase='before_array',root_start=True)
            runtime.current.modules['numpy'] = SimpleNamespace()
            with self.assertRaises(AssertionError):
                p.provide(binding(),phase='after_array',root_start=True)
            self.assertEqual(runtime.functions.bootstrap.call_count,1)

    def test_changed_source_evidence_during_bootstrap_is_rejected(self):
        with invented_runtime() as runtime:
            changed = copy.deepcopy(runtime.admission);changed['certificate']['invented'] = False
            runtime.admit.side_effect = [runtime.admission,changed]
            with self.assertRaisesRegex(AssertionError,'evidence changed'):
                p.provide(binding(),phase='before_array',root_start=True)
            self.assertTrue(p._FAILED)

    def test_request_requires_explicit_runtime_authorization_and_fixed_source(self):
        request = {'namespace':'generalization_knowncell_array_admission_20261023','status':REQUEST_STATUS,
                   'runtime_import_authorized':True,'label_access_authorized':False,'model_fitting_authorized':False,
                   'PUM_resource_exception_applies':False,'PRELib_resource_exception_applies':False,'numerical_threads':1,
                   'software_status_sha256':SOFTWARE_STATUS_SHA,'software_certificate_sha256':PANDAS_ADMISSION_SHA,
                   'provider_preparation_manifest_sha256':'b'*64,
                   'provider_binding':{'source_path':SOURCE,'source_sha256':'c'*64,'module':MODULE,
                                       'qualname':'provide','reviewed_deferred_only':True}}
        self.assertTrue(c.request_contract(request,binding(),'c'*64))
        request['runtime_import_authorized'] = False
        with self.assertRaises(AssertionError):c.request_contract(request,binding(),'c'*64)
        request['runtime_import_authorized'] = True;request['provider_binding']['module'] = 'another.module'
        with self.assertRaises(AssertionError):c.request_contract(request,binding(),'c'*64)

    def test_duplicate_nonfinite_JSON_and_nonsoftware_paths_are_rejected(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}'):
            with self.assertRaises(AssertionError):c.decode(raw)
        self.assertFalse(static_allowed('artifacts/generalization_crosscell_20261007/simple_model_features.npz'))
        self.assertFalse(static_allowed('results/probabilistic_ranking_20260928/candidate_index.csv'))

    def test_real_gate_surrounds_each_top_level_scientific_import(self):
        events = []
        def import_invented(name):
            events.append(('import',name))
            return SimpleNamespace(minimize='invented-minimize',expit='invented-expit')
        with patch.object(explicit_bootstrap.guard,'fresh_gate',side_effect=lambda:events.append(('gate',))),patch.object(explicit_bootstrap.importlib,'import_module',side_effect=import_invented):
            values = explicit_bootstrap.load_scientific()
        expected = []
        for name in ('numpy','pandas','scipy','scipy.optimize','scipy.special','threadpoolctl'):
            expected.extend([('gate',),('import',name),('gate',)])
        self.assertEqual(events,expected)
        self.assertEqual(values[3:5],('invented-minimize','invented-expit'))


def run():
    def clean():
        return not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in BLOCKED)
    assert clean()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful() and clean()
    sources = sorted((ROOT/'src'/NS).glob('*.py'))
    receipt = {'status':'PASS_MOCKED_REAL_RUNTIME_PROVIDER_SOURCE_NOT_NATIVE_OR_PROJECT_ADMISSION',
               'tests':result.testsRun,'UTC':datetime.now(timezone.utc).isoformat(),
               'sources':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
               'actual_resource_guard_or_native_bootstrap_invoked':False,'scientific_imports':False,
               'project_payload_reads':0,'actual_optimizer_calls':0,
               'fresh_actual_provider_invocation_and_origin_acceptance_pending':True}
    with (ROOT/'results'/NS/'synthetic_tests_receipt.json').open('xb') as stream:
        stream.write((json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())


if __name__ == '__main__':run()
