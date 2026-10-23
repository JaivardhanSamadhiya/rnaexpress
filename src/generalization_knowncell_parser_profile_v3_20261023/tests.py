"""Prior invented stdlib tests, new cache checker and exact two-file closure."""
import ast
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import sys
from src.generalization_knowncell_parser_profile_20261022.tests import Checks as OriginalChecks
from src.generalization_knowncell_parser_profile_20261022.tests_v2 import CacheChecks as PriorCacheChecks
from .common import *
from .cache_integrity import possible_cache_proof


class CacheChecks(PriorCacheChecks):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='invented_cache_v3_',dir=OUT)
        self.home=Path(self.temporary.name).resolve()
        assert self.home.is_relative_to(OUT.resolve()) and self.home!=OUT.resolve()
        self.addCleanup(self.temporary.cleanup)
        self.prefix=self.home/'prefix';self.prefix.mkdir()
        self.source=self.prefix/'invented_module.py';self.source.write_bytes(b'# invented source only\n')
        self.cached=self.prefix/'invented_cache.pyc';self.cached.write_bytes(b'invented bytecode payload, never executed')
        self.expected={self.source.name:sha(self.source),self.cached.name:sha(self.cached)}
        self.module=SimpleNamespace(__file__=str(self.source),__cached__=str(self.cached))

    def proof(self):return possible_cache_proof({'invented':self.module},self.prefix,self.expected)

    def test_unpinned_error_identifies_module_and_exact_path(self):
        del self.expected[self.cached.name]
        with self.assertRaises(AssertionError) as caught:self.proof()
        self.assertIn('invented',str(caught.exception))
        self.assertIn(str(self.source),str(caught.exception))
        self.assertIn(str(self.cached),str(caught.exception))

    def test_expansion_is_exactly_the_two_declared_old_caches(self):
        base={'six.py':'a'*64,'threadpoolctl.py':'b'*64}
        old=dict(base,**ADDITIONAL_CACHES)
        old['__pycache__/py.cpython-312.pyc']='c'*64
        result=expanded_files(base,old)
        self.assertEqual(set(result)-set(base),set(ADDITIONAL_CACHES))
        self.assertNotIn('__pycache__/py.cpython-312.pyc',result)

    def test_unverified_extra_cache_cannot_be_admitted(self):
        old=dict(ADDITIONAL_CACHES);old.pop(next(iter(old)))
        with self.assertRaises(AssertionError):expanded_files({},old)

    def test_new_worker_and_final_deadline_order(self):
        tree=ast.parse((SRC/'supervise.py').read_text(encoding='utf-8'))
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='spawn']
        self.assertEqual(len(calls),1);command=calls[0].args[0]
        self.assertEqual([node.value for node in command.elts[1:5]],['-S','-B','-u','-m'])
        self.assertEqual(command.elts[5].value,'src.generalization_knowncell_parser_profile_v3_20261023.worker')
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='run')
        lines={}
        for node in function.body:
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Name):lines[target.id]=node.lineno
        for key in ('unchanged','preparation_sha','completion_sha','complete'):
            self.assertGreater(lines['after'],lines[key])


def run():
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(OriginalChecks),
                             unittest.defaultTestLoader.loadTestsFromTestCase(CacheChecks)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    for path in SRC.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
    jsave(OUT/'stdlib_test_receipt.json',{'status':'PASS_STDLIB_MOCK_V3_CACHE_CLOSURE_PREPARATION_ONLY',
        'tests_run':result.testsRun,'source_sha256':{path.relative_to(ROOT).as_posix():sha(path) for path in SRC.glob('*.py')},
        'scientific_modules_imported':False,'real_scientific_cache_bytes_read':False,
        'native_retry_executed':False,'project_biological_inputs_read':False})


if __name__=='__main__':run()
