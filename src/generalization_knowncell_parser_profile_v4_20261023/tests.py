"""Invented manifest bytes/callback spies only; no scientific execution."""
import ast
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import tempfile
import unittest
import sys
from .common import *
from .binding import *


class Checks(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='invented_binding_v4_',dir=OUT)
        self.home=Path(self.temporary.name).resolve()
        assert self.home.is_relative_to(OUT.resolve()) and self.home!=OUT.resolve()
        self.addCleanup(self.temporary.cleanup)
        self.path=self.home/'invented_manifest.json'
        self.raw=b'{"status":"INVENTED_ONLY","files":{}}\n'
        self.path.write_bytes(self.raw)
        self.bound=bind_initial(self.raw,self.raw)

    def test_exact_verified_raw_identity_is_retained(self):
        self.assertEqual(self.bound.initial_sha256,digest(self.raw))
        self.assertEqual(self.bound.manifest['status'],'INVENTED_ONLY')
        self.assertEqual(require_unchanged(self.path,self.bound),digest(self.raw))

    def test_initial_identity_field_cannot_be_reassigned(self):
        with self.assertRaises(FrozenInstanceError):self.bound.initial_sha256='0'*64

    def test_different_git_bytes_rejected(self):
        with self.assertRaises(AssertionError):bind_initial(self.raw,self.raw+b' ')

    def test_child_rejects_changed_bytes_even_with_consistent_new_git(self):
        changed=b'{"status":"DIFFERENT_INVENTED_ONLY","files":{}}\n'
        with self.assertRaises(AssertionError):bind_initial(changed,changed,self.bound.initial_sha256)

    def test_whitespace_only_raw_change_is_rejected(self):
        self.path.write_bytes(self.raw+b' ')
        with self.assertRaises(AssertionError):require_unchanged(self.path,self.bound)

    def test_changed_manifest_prevents_bootstrap_callback(self):
        self.path.write_bytes(b'{"changed":true}')
        called=[]
        with self.assertRaises(AssertionError):guarded_call(self.path,self.bound,lambda:called.append('bootstrap'))
        self.assertEqual(called,[])

    def test_changed_manifest_prevents_output_callback(self):
        self.path.write_bytes(b'{"changed":true}')
        called=[]
        with self.assertRaises(AssertionError):guarded_call(self.path,self.bound,lambda:called.append('output'))
        self.assertEqual(called,[])

    def test_unchanged_callback_runs_once(self):
        called=[]
        result=guarded_call(self.path,self.bound,lambda value:(called.append(value),value+1)[1],7)
        self.assertEqual(called,[7]);self.assertEqual(result,8)

    def test_child_sha_argument_mandatory_and_strict(self):
        expected=self.bound.initial_sha256
        self.assertEqual(child_expected(['--expected-manifest-sha',expected]),expected)
        for args in ([],[expected],['--other',expected],['--expected-manifest-sha','A'*64],
                     ['--expected-manifest-sha',expected,'extra']):
            with self.subTest(args=args),self.assertRaises(AssertionError):child_expected(args)

    def test_duplicate_json_keys_rejected(self):
        raw=b'{"files":{},"files":{}}'
        with self.assertRaises(AssertionError):bind_initial(raw,raw)

    def test_all_outputs_use_initial_field_and_no_live_expected_hash(self):
        for name in ('worker.py','supervise.py'):
            tree=ast.parse((SRC/name).read_text(encoding='utf-8'))
            live=[node for node in ast.walk(tree) if isinstance(node,ast.Call)
                  and isinstance(node.func,ast.Name) and node.func.id=='sha'
                  and any(isinstance(arg,ast.Name) and arg.id=='MANIFEST' for arg in node.args)]
            self.assertEqual(live,[])
        worker=ast.parse((SRC/'worker.py').read_text(encoding='utf-8'))
        identity_values=[]
        for node in ast.walk(worker):
            if isinstance(node,ast.Dict):
                identity_values += [value for key,value in zip(node.keys,node.values)
                    if isinstance(key,ast.Constant) and key.value=='preparation_manifest_sha256']
        self.assertEqual(len(identity_values),3)
        self.assertTrue(all(isinstance(value,ast.Attribute) and value.attr=='initial_sha256' for value in identity_values))

    def test_child_launch_binds_initial_identity(self):
        tree=ast.parse((SRC/'supervise.py').read_text(encoding='utf-8'))
        spawn=[node for node in ast.walk(tree) if isinstance(node,ast.Call)
               and isinstance(node.func,ast.Attribute) and node.func.attr=='spawn']
        self.assertEqual(len(spawn),1);command=spawn[0].args[0].elts
        self.assertEqual([node.value for node in command[1:5]],['-S','-B','-u','-m'])
        self.assertEqual(command[6].value,'--expected-manifest-sha')
        self.assertIsInstance(command[7],ast.Attribute)
        self.assertEqual(command[7].attr,'initial_sha256')


def run():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    assert result.wasSuccessful()
    assert not any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules)
    for path in SRC.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
    jsave(OUT/'stdlib_test_receipt.json',{
        'status':'PASS_INVENTED_INITIAL_MANIFEST_BINDING_ONLY','tests_run':result.testsRun,
        'source_sha256':{path.relative_to(ROOT).as_posix():sha(path) for path in SRC.glob('*.py')},
        'scientific_modules_imported':False,'native_execution':False,'scientific_case_expansion':False,
        'project_data_arrays_labels_or_checkpoints_read':False})


if __name__=='__main__':run()
