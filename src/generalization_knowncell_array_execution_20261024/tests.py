"""Invented receipt and source-integrity tests; no payload or native execution."""
import ast
import copy
import os
import sys
import unittest
from unittest.mock import patch
from . import common as c,calibration,worker,supervise


def admission():
    return {'status':'FROZEN_ACTUAL_ARRAY_EXECUTION_INPUT_ADMISSION','invocation':c.INVOCATION,'stage':c.STAGE,
        'generation_manifest_sha256':'a'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
        'authorization_sha256':c.AUTH_SHA,'approval_scope_sha256':c.SCOPE_SHA,'resource_policy':c.resource_policy(),
        'input_pins':{c.REQUEST:'b'*64,c.INDEPENDENT_REPORT:c.INDEPENDENT_REPORT_SHA,
            c.INDEPENDENT_SUPERVISOR:c.INDEPENDENT_SUPERVISOR_SHA,c.array.METADATA_BUNDLE:c.METADATA_BUNDLE_SHA},
        'runtime_import_authorized':True,'label_access_authorized':False,'model_fitting_authorized':False}


def nodes(path):
    result={}
    for node in ast.parse(path.read_bytes()).body:
        if isinstance(node,ast.FunctionDef):result[node.name]=node
        elif isinstance(node,ast.ClassDef):
            for method in node.body:
                if isinstance(method,ast.FunctionDef):result[node.name+'.'+method.name]=method
    return result


class Contracts(unittest.TestCase):
    def test_actual_input_pins_and_no_label_or_fit(self):
        c.run_contract(admission(),'a'*64)
        for field,value in [('label_access_authorized',True),('model_fitting_authorized',True),
            ('runtime_import_authorized',False),('generation_manifest_sha256','0'*64),('invocation','fit')]:
            item=admission();item[field]=value
            with self.assertRaises(AssertionError):c.run_contract(item,'a'*64)

    def test_metadata_pins_and_input_set_are_exact(self):
        for key in (c.INDEPENDENT_REPORT,c.INDEPENDENT_SUPERVISOR,c.array.METADATA_BUNDLE):
            item=admission();item['input_pins'][key]='0'*64
            with self.assertRaises(AssertionError):c.run_contract(item,'a'*64)
        item=admission();item['input_pins']['other']='b'*64
        with self.assertRaises(AssertionError):c.run_contract(item,'a'*64)

    def test_resource_policy_is_identical(self):
        self.assertEqual(c.resource_policy(),c.prior.resource_policy())
        item=admission();item['resource_policy']['process_cap']+=1
        with self.assertRaises(AssertionError):c.run_contract(item,'a'*64)

    def test_guard_transaction_bodies_unchanged(self):
        old=nodes(c.ROOT/'src/generalization_knowncell_metadata_verification_execution_20261024/calibration.py')
        new=nodes(c.ROOT/'src'/c.NS/'calibration.py')
        self.assertEqual(set(old),set(new))
        for name in old:
            a,b=copy.deepcopy(old[name]),copy.deepcopy(new[name])
            if name=='calibrated':
                for node in ast.walk(a):
                    if isinstance(node,ast.Constant) and node.value=='metadata':node.value='array'
            for node in ast.walk(a):
                if isinstance(node,ast.Constant) and node.value=='independent_metadata_verification':node.value='array_admission'
            self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False),name)

    def test_monitor_is_same_function(self):
        from src.generalization_knowncell_metadata_verification_execution_20261024.monitor import observe
        self.assertIs(supervise.observe,observe)

    def test_no_start_performs_no_probe(self):
        with patch.object(c,'admit_authorization',side_effect=RuntimeError('must not execute')):
            with self.assertRaises(AssertionError):supervise.run('a'*64,'b'*64)

    def test_startup_precedes_birth_and_job_assignment_precedes_resume(self):
        source=(c.ROOT/'src'/c.NS/'supervise.py').read_text(encoding='utf8')
        self.assertLess(source.index('before=headless.memory()'),source.index('birth_sha=c.save_new'))
        self.assertLess(source.index('job.limits()'),source.index('job.spawn('))
        self.assertLess(source.index('job.spawn('),source.index('child.resume()'))
        self.assertLess(source.index('validate_certificate(c.decode(raw)'),source.index('after=headless.memory()'))

    def test_command_pins_source_no_bytecode_and_identities(self):
        command=supervise.command('a'*64,'b'*64,'c'*64)
        self.assertEqual(command[1:4],['-S','-B','-X'])
        self.assertEqual(command[-3:],['a'*64,'b'*64,'c'*64])
        self.assertIn('src.'+c.NS+'.worker',command)

    def test_protected_runtime_proofs_and_truthful_resource_annotation(self):
        fake_common=type('Common',(),{})()
        owner={'birth_sha256':'c'*64,'current_pid':os.getpid(),'parent_pid':os.getppid()}
        session=calibration._Session('array','a'*64,{'approval_sha256':c.AUTH_SHA,
            'approved_policy_manifest_sha256':c.POLICY_SHA,'approval_scope_sha256':c.SCOPE_SHA},owner,{},lambda:None,fake_common)
        value={'resource_exception_applies':False,'original_resource_guards_unchanged':True,
            'runtime_acceptance':{'initial':{'tuple':(1,2)},'hash':'d'*64},
            'runtime_acceptance_after_array':{'initial':{'tuple':(3,4)},'hash':'e'*64},
            'underlying_report':{'fresh_original_resource_gates_checked':2,'scalar':.5},
            'array_acquisition':{'fresh_original_resource_gate_before_open':True}}
        result=worker.assemble(session,value,'a'*64,'b'*64,'c'*64)
        self.assertTrue(result['resource_exception_applies'])
        self.assertFalse(result['original_resource_guards_unchanged'])
        self.assertFalse(result['array_acquisition']['fresh_original_resource_gate_before_open'])
        self.assertEqual(result['underlying_report'],{'calibrated_resource_gates_checked':2,'scalar':.5})
        for key in ('runtime_acceptance','runtime_acceptance_after_array'):
            self.assertEqual(c.canonical(value[key]),c.canonical(result[key]))
        self.assertIs(value['resource_exception_applies'],False)

    def test_unknown_resource_claim_and_nonfinite_values_rejected(self):
        with self.assertRaises(AssertionError):calibration._annotated_copy({'unknown_original_resource_guard':True},[],[])
        with self.assertRaises(ValueError):c.canonical({'x':float('nan')})

    def test_calibration_authorization_requires_array_invocation(self):
        value={'generation_manifest_sha256':'a'*64,'approved_policy_manifest_sha256':c.POLICY_SHA,
            'approval_scope_sha256':c.SCOPE_SHA,'approved_invocation':c.INVOCATION,'approval_sha256':c.AUTH_SHA,
            'explicit_human_approval':True,'owned_job_required':True,'allowed_stages':list(c.policy.STAGES)}
        calibration._authorization(value,'array','a'*64)
        for key,item in [('approved_invocation','independent_metadata_verification'),('approval_scope_sha256','0'*64),
            ('generation_manifest_sha256','0'*64)]:
            changed=dict(value);changed[key]=item
            with self.assertRaises(AssertionError):calibration._authorization(changed,'array','a'*64)

    def test_full_actual_shape_certificate_contract_and_corruption(self):
        from src.generalization_knowncell_array_admission_20261023.tests import report
        a=worker.a
        proof={'status':a.PROVIDER_STATUS,'phase':'before_array',
            'request_binding':{'request_sha256':'b'*64,'provider_preparation_manifest_sha256':c.PROVIDER_PREPARATION_SHA},
            'fresh_current_python_and_loaded_native_origins_checked':True,'invented_only':False,'model_fits':0,
            'numpy_version':'1.26.4','source_cache_remained_absent':True}
        underlying=report(a.sha(a.canonical(proof)),'b20281b69b3360a1e60197f5c7ed01d105642a5e79c9fb0ee4cd76001d8f2795')
        underlying['fresh_original_resource_gates_checked']=2
        after=copy.deepcopy(proof);after['phase']='after_array'
        result={'status':a.STATUS,'actual_npz_sha256':a.NPZ_SHA,'metadata_bundle_sha256':c.METADATA_BUNDLE_SHA,
            'rows':13781,'columns':102,'same_allele_feature_bytes_equal':True,'original_row_ids_sha256':a.ROW_IDS_SHA,
            'resource_exception_applies':False,'original_resource_guards_unchanged':True,
            'numeric_labels_admitted':False,'FIT_admission_granted':False,'models_fitted':0,
            'array_request_sha256':'b'*64,'source_readiness_sha256':c.ARRAY_READY_SHA,
            'array_acquisition':{'actual_sha256':a.NPZ_SHA,'fresh_original_resource_gate_before_open':True},
            'underlying_report':underlying,'runtime_acceptance':proof,'runtime_acceptance_after_array':after}
        owner={'birth_sha256':'c'*64,'current_pid':os.getpid(),'parent_pid':os.getppid()}
        auth={'approval_sha256':c.AUTH_SHA,'approved_policy_manifest_sha256':c.POLICY_SHA,'approval_scope_sha256':c.SCOPE_SHA}
        session=calibration._Session('array','a'*64,auth,owner,{},lambda:None,None)
        value=worker.assemble(session,result,'a'*64,'b'*64,'c'*64)
        with patch.object(c,'read_run',return_value=admission()):
            worker.validate_certificate(value,'a'*64,'b'*64,'c'*64)
            for key,item in [('actual_npz_sha256','0'*64),('metadata_bundle_sha256','0'*64),
                ('resource_exception_applies',False),('FIT_admission_granted',True),('models_fitted',1),('rows',1)]:
                changed=copy.deepcopy(value);changed[key]=item
                with self.assertRaises(AssertionError):worker.validate_certificate(changed,'a'*64,'b'*64,'c'*64)
            changed=copy.deepcopy(value);changed['runtime_acceptance']['numpy_version']='0'
            with self.assertRaises(AssertionError):worker.validate_certificate(changed,'a'*64,'b'*64,'c'*64)

    def test_new_output_paths_do_not_reuse_metadata_birth(self):
        self.assertNotEqual(c.BIRTH,c.prior.BIRTH)
        for path in (c.OUTPUT,c.BIRTH,c.COMPLETION,c.SUPERVISOR,c.WORKER_LOG):
            self.assertEqual(path.parent,c.OUT)


def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contracts)
    with (c.OUT/'synthetic_tests_attempt_02.log').open('x',encoding='utf8') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    assert result.wasSuccessful()
    sources=sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn') for name in sys.modules)
    c.save_new(c.OUT/'synthetic_tests_receipt.json',{'status':'PASS_INVENTED_ARRAY_EXECUTION_CONTRACT_TESTS',
        'tests':result.testsRun,'source_files':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources},
        'actual_jobs':0,'actual_resource_probes':0,'project_payload_reads':0,'models_fitted':0,
        'scientific_runtimes_imported':False})
    print('PASS_INVENTED_ARRAY_EXECUTION_TESTS',result.testsRun,flush=True)


if __name__=='__main__':main()
