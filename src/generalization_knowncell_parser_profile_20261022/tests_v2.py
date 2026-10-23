"""All prior stdlib tests plus invented cache/provenance checks; no native run."""
import ast
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import sys
from .common import ROOT,SRC,OUT,sha,jsave
from .tests import Checks as OriginalChecks
from .cache_integrity_v2 import possible_cache_proof
from .extras_v2 import original_bootstrap_function


class CacheChecks(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='invented_cache_v2_',dir=OUT)
        self.home=Path(self.temporary.name).resolve()
        assert self.home.is_relative_to(OUT.resolve()) and self.home!=OUT.resolve()
        self.addCleanup(self.temporary.cleanup)
        self.prefix=self.home/'prefix';self.prefix.mkdir()
        self.source=self.prefix/'invented_module.py';self.source.write_bytes(b'# invented source only\n')
        self.cached=self.prefix/'invented_cache.pyc';self.cached.write_bytes(b'invented bytecode payload, never executed')
        self.expected={self.source.name:sha(self.source),self.cached.name:sha(self.cached)}
        self.module=SimpleNamespace(__file__=str(self.source),__cached__=str(self.cached))

    def proof(self):return possible_cache_proof({'invented':self.module},self.prefix,self.expected)

    def test_existing_pinned_cache_bound_without_execution_claim(self):
        value=self.proof()
        self.assertEqual(value['possible_existing_bytecode_payloads']['invented']['sha256'],sha(self.cached))
        self.assertIs(value['execution_from_cache_established'],False)

    def test_missing_cache_is_allowed(self):
        self.module.__cached__=str(self.prefix/'absent.pyc')
        self.assertEqual(self.proof()['modules_without_existing_cache'],['invented'])

    def test_existing_unpinned_cache_rejected(self):
        del self.expected[self.cached.name]
        with self.assertRaises(AssertionError):self.proof()

    def test_existing_changed_cache_rejected(self):
        self.cached.write_bytes(b'different invented bytes')
        with self.assertRaises(AssertionError):self.proof()

    def test_existing_outside_prefix_cache_rejected(self):
        outside=self.home/'outside.pyc';outside.write_bytes(b'outside invented bytes')
        self.module.__cached__=str(outside)
        with self.assertRaises(AssertionError):self.proof()

    def test_invalid_cache_attribute_rejected(self):
        self.module.__cached__=42
        with self.assertRaises(AssertionError):self.proof()

    def test_no_cache_attribute_allowed(self):
        del self.module.__cached__
        self.assertEqual(self.proof()['modules_without_existing_cache'],['invented'])

    def test_existing_directory_not_bytecode_file(self):
        path=self.prefix/'directory.pyc';path.mkdir();self.module.__cached__=str(path)
        with self.assertRaises(AssertionError):self.proof()

    def test_module_outside_scientific_prefix_is_helper_out_of_scope(self):
        self.module.__file__=str(self.home/'other.py')
        self.assertEqual(self.proof()['possible_existing_bytecode_payloads'],{})

    def test_sourceless_module_cache_also_bound(self):
        self.module.__file__=str(self.cached)
        self.assertEqual(self.proof()['possible_existing_bytecode_payloads']['invented']['relative_path'],self.cached.name)

    def test_original_bootstrap_function_only_compile_no_numpy(self):
        def forbidden(*args,**kwargs):raise AssertionError('No RNG operation during preparation')
        fake=SimpleNamespace(random=SimpleNamespace(default_rng=forbidden))
        function=original_bootstrap_function(fake,[])
        self.assertEqual(function.__name__,'shared_bootstrap')
        self.assertFalse(any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules))

    def test_v2_child_and_two_proof_calls_are_fixed(self):
        supervisor=ast.parse((SRC/'supervise_v2.py').read_text(encoding='utf-8'))
        spawn=[node for node in ast.walk(supervisor) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='spawn']
        self.assertEqual(len(spawn),1)
        command=spawn[0].args[0]
        self.assertEqual([node.value for node in command.elts[1:5]],['-S','-B','-u','-m'])
        self.assertEqual(command.elts[5].value,'src.generalization_knowncell_parser_profile_20261022.worker_v2')
        worker=ast.parse((SRC/'worker_v2.py').read_text(encoding='utf-8'))
        calls=[node for node in ast.walk(worker) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='actual_proof']
        self.assertEqual(len(calls),2)

    def test_final_resource_check_follows_provenance_hashing(self):
        tree=ast.parse((SRC/'supervise_v2.py').read_text(encoding='utf-8'))
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='run')
        lines={}
        for node in function.body:
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Name):lines[target.id]=node.lineno
        self.assertGreater(lines['after'],lines['unchanged'])
        self.assertGreater(lines['after'],lines['completion_sha'])
        self.assertGreater(lines['after'],lines['preparation_sha'])
        self.assertGreater(lines['after'],lines['complete'])


def run():
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(OriginalChecks),
                             unittest.defaultTestLoader.loadTestsFromTestCase(CacheChecks)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    jsave(OUT/'stdlib_test_receipt_cache_v2.json',{
        'status':'PASS_STDLIB_MOCK_CACHE_V2_PREPARATION_ONLY','tests_run':result.testsRun,
        'source_sha256':{path.relative_to(ROOT).as_posix():sha(path) for path in SRC.glob('*.py')},
        'scientific_modules_imported':False,'native_profile_executed':False,
        'real_scientific_cache_bytes_read':False,'project_biological_inputs_read':False})


if __name__=='__main__':run()
