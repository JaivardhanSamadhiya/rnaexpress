"""Invented regression suite; no actual owner, scientific runtime or IO calls."""
import ast
import copy
import os
import struct
import sys
import unittest
from contextlib import ExitStack
from unittest.mock import patch
from . import tests as previous,bridge_v3 as b,contracts_v3 as c
from .spec_v3 import *

base_fixture=previous.fixture


def refresh_context(f,*,birth=None,utc=None):
    """Invented live evidence with this real test-process PID, never Job proof."""
    proof=f['current']
    if birth is not None:proof['caller_birth_sha256']=birth
    if utc is not None:proof['UTC']=utc
    static_sha=c.digest(c.canonical(f['binding']))
    proof['static_root_binding_sha256']=static_sha
    f['owner']={'status':OWNER_STATUS,'stage':f['binding']['stage'],
        'current_pid':os.getpid(),'parent_pid':os.getppid(),
        'caller_birth_sha256':proof['caller_birth_sha256'],
        'current_stage_origin_proof_sha256':c.digest(c.canonical(proof)),
        'static_root_binding_sha256':static_sha,
        'reviewed_controller_admission_sha256':f['binding']['reviewed_controller_admission_sha256'],
        'actual_parent_Job_and_native_origins_checked_by_fixed_caller':True,
        'runtime_and_FIT_authority_granted_here':False}


def fixture():
    f=base_fixture()
    f['binding'].pop('caller_birth_sha256')
    f['binding'].pop('current_stage_origin_proof_sha256')
    f['binding']['status']=BINDING_STATUS
    refresh_context(f)
    return f


def invoke(f):
    return b.bridge_inputs(previous.NP,f['bundle_raw'],f['matrix'],f['array_raw'],f['label_raw'],
        c.canonical(f['binding']),f['current'],f['owner'],root_start=True)


class Tests(previous.Tests):
    # The fourteen prior cases are retained. These operational cases need the
    # new separate owner argument; none changes a scientific acceptance rule.
    def test_no_root_stops_before_real_gate_or_input_parse(self):
        with patch.object(c,'fresh',side_effect=RuntimeError('must not probe')):
            with self.assertRaises(AssertionError):b.bridge_inputs(None,None,None,None,None,None,None,None)

    def test_failed_real_guard_precedes_commit_or_supplied_matrix_access(self):
        with patch.object(c,'fresh',side_effect=AssertionError('invented resource stop')),patch.object(c,'committed_bytes') as git:
            with self.assertRaisesRegex(AssertionError,'resource stop'):
                b.bridge_inputs(None,None,None,None,None,None,None,None,root_start=True)
        git.assert_not_called()

    def test_signed_zero_and_subnormal_float_bits_are_preserved(self):
        f=fixture();doc=c.decode(f['label_raw']);values=doc['labels_result']['measured_delta']
        values[0]=-0.0;values[1]=5e-324;raw=b''.join(struct.pack('<d',v) for v in values)
        doc['labels_result']['parsed_effects_float64_sha256']=c.digest(raw)
        f['label_raw']=c.canonical(doc);f['binding']['label_certificate_sha256']=c.digest(f['label_raw'])
        refresh_context(f)
        with previous.supplied(f):result=invoke(f)
        self.assertEqual(b''.join(struct.pack('<d',v) for v in result['effects'].values()),raw)

    def test_dynamic_current_proof_is_distinct_from_stable_anchor(self):
        f=fixture()
        self.assertNotEqual(f['binding']['runtime_binding_sha256'],f['owner']['current_stage_origin_proof_sha256'])
        with previous.supplied(f):result=invoke(f)
        self.assertEqual(result['admissions']['runtime_binding_sha256'],f['binding']['runtime_binding_sha256'])
        self.assertEqual(result['bridge_report']['current_stage_origin_proof_sha256'],f['owner']['current_stage_origin_proof_sha256'])

    def test_wrong_current_owner_stage_or_native_declaration_fails(self):
        for key,value in (('current_pid',-1),('parent_pid',-1),('stage','labels'),('numpy_version','2.4.6'),('numerical_threads',2)):
            f=fixture();f['current'][key]=value
            f['owner']['current_stage_origin_proof_sha256']=c.digest(c.canonical(f['current']))
            with previous.supplied(f),self.assertRaises(AssertionError):invoke(f)

    def test_two_current_contexts_use_identical_precommittable_static_binding(self):
        first=fixture();second=copy.deepcopy(first)
        refresh_context(second,birth='8'*64,utc='invented-second-live-UTC')
        raw=c.canonical(first['binding'])
        self.assertEqual(raw,c.canonical(second['binding']))
        self.assertNotEqual(first['owner']['caller_birth_sha256'],second['owner']['caller_birth_sha256'])
        self.assertNotEqual(first['owner']['current_stage_origin_proof_sha256'],second['owner']['current_stage_origin_proof_sha256'])
        # Both use the real current test PID/parent PID but invented, explicitly
        # nonauthoritative resource/Job declarations. No actual Job is queried.
        for f in (first,second):
            self.assertEqual(f['owner']['current_pid'],os.getpid())
            self.assertEqual(f['owner']['parent_pid'],os.getppid())
        with previous.supplied(first) as first_commits:one=invoke(first)
        with previous.supplied(second) as second_commits:two=invoke(second)
        self.assertEqual(first_commits.call_args_list[0].args[1],second_commits.call_args_list[0].args[1])
        self.assertEqual(one['admissions'],two['admissions'])
        self.assertEqual(one['bridge_report']['root_binding_sha256'],two['bridge_report']['root_binding_sha256'])
        self.assertNotEqual(one['bridge_report']['current_owner_context_sha256'],two['bridge_report']['current_owner_context_sha256'])
        self.assertFalse(one['bridge_report']['actual_parent_Job_or_reviewed_caller_execution_certified_here'])

    def test_static_binding_forbids_either_live_field(self):
        for key in ('caller_birth_sha256','current_stage_origin_proof_sha256'):
            f=fixture();f['binding'][key]='9'*64
            with previous.supplied(f),self.assertRaisesRegex(AssertionError,'Static binding'):invoke(f)

    def test_owner_and_proof_bind_exact_static_bytes_birth_and_current_process(self):
        mutations=(('static_root_binding_sha256','0'*64),('caller_birth_sha256','0'*64),
            ('reviewed_controller_admission_sha256','0'*64),('current_stage_origin_proof_sha256','0'*64),
            ('current_pid',-1),('parent_pid',-1),('actual_parent_Job_and_native_origins_checked_by_fixed_caller',False))
        for key,value in mutations:
            f=fixture();f['owner'][key]=value
            with previous.supplied(f),self.assertRaises(AssertionError):invoke(f)

    def test_proof_static_bytes_binding_cannot_be_changed_even_with_rehashed_owner(self):
        f=fixture();f['current']['static_root_binding_sha256']='0'*64
        f['owner']['current_stage_origin_proof_sha256']=c.digest(c.canonical(f['current']))
        with previous.supplied(f),self.assertRaises(AssertionError):invoke(f)

    def test_scientific_validation_statements_are_identical_to_frozen_v2(self):
        def scientific_nodes(path):
            function=next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='bridge_inputs')
            start=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Assign)
                and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='bundle')
            end=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Return))
            return [ast.dump(n,include_attributes=False) for n in function.body[start:end]]
        self.assertEqual(scientific_nodes(SRC/'bridge_v2.py'),scientific_nodes(SRC/'bridge_v3.py'))


def run():
    # Private invented test-module binding only; no production global is patched.
    with ExitStack() as stack:
        for name,value in (('b',b),('c',c),('fixture',fixture),('invoke',invoke),('LABEL_PATH',LABEL_PATH),('binding_path',binding_path)):
            stack.enter_context(patch.object(previous,name,value))
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    assert result.wasSuccessful()
    assert result.testsRun==19
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for name in sys.modules)
    sources=sorted(SRC.glob('*.py'))
    for path in sources:ast.parse(path.read_bytes())
    payload={'status':'PASS_INVENTED_STATIC_DYNAMIC_INPUT_BRIDGE_V3_NOT_ACTUAL_EXECUTION',
        'tests':result.testsRun,'retained_previous_cases':14,'new_static_dynamic_cases':5,
        'source_files':{p.relative_to(ROOT).as_posix():c.digest(p.read_bytes()) for p in sources},
        'actual_test_process_PIDs_used':True,'actual_Job_or_native_origins_proved':False,
        'same_static_binding_two_distinct_current_contexts_PASS':True,
        'scientific_validation_AST_unchanged_from_v2':True,
        'actual_project_payloads_Git_resource_probe_scientific_native_sampler_pool_fit_calls':0,
        'actual_root_bindings_created':False,'scientific_imports':False}
    path=OUT/'synthetic_tests_receipt_v3_reviewed.json'
    with path.open('xb') as stream:stream.write(c.canonical(payload))
    print('INVENTED_STATIC_DYNAMIC_BRIDGE_V3_PASS',result.testsRun,c.digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
