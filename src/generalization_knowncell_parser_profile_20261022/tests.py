"""Standard-library/mock tests only; deliberately no scientific imports."""
import ast
import csv
import io
import json
import math
from pathlib import Path
import sys
import unittest
from . import cases
from .common import *
from .parser_profile import GOLDEN_HEX


class Effects:
    def __init__(self,values): self.values=values; self.conversion=None
    def to_numpy(self,kind): self.conversion=kind; return self.values


class FakePandas:
    def __init__(self): self.call=None; self.effects=None
    def read_csv(self,stream,**kwargs):
        self.call=kwargs
        rows=list(csv.reader(stream)); header=rows[0]
        kept=[row for i,row in enumerate(rows[1:],1) if not kwargs['skiprows'](i)]
        result=type('Values',(),{})()
        result.intervention_id=[row[header.index('intervention_id')] for row in kept]
        # These simple invented numeric values verify mock plumbing only.
        self.effects=Effects([float(row[header.index('measured_delta')]) for row in kept])
        result.measured_delta=self.effects
        return result


class Checks(unittest.TestCase):
    def test_exact_options_and_mask(self):
        text=cases.csv_text([('a','1.25','x'),('skip','bad','x'),('z','-2.5','x')])
        selected=cases.metadata(text,[0,2]); fake=FakePandas()
        ids,values=cases.original_pandas(text,fake,selected)
        self.assertEqual(ids,['a','z']); self.assertEqual(values,[1.25,-2.5])
        self.assertEqual(set(fake.call),{'usecols','low_memory','skiprows'})
        self.assertEqual(fake.call['usecols'],['intervention_id','measured_delta'])
        self.assertIs(fake.call['low_memory'],False); self.assertIs(fake.effects.conversion,float)
        self.assertEqual([fake.call['skiprows'](i) for i in range(5)],[False,False,True,False,True])

    def test_golden_binary_values(self):
        self.assertEqual(cases.float_bytes([1.25,-2.5,0.,-0.,9007199254740992.]).hex(),GOLDEN_HEX)

    def test_tricky_corpus_stays_tokens(self):
        self.assertIn('9007199254740993',cases.TRICKY)
        self.assertIn('5e-324',cases.TRICKY)
        self.assertTrue(all(isinstance(value,str) for value in cases.TRICKY))

    def test_all_successful_metadata_cases(self):
        for _,text,positions in cases.successful_cases():
            selected=cases.metadata(text,positions)
            self.assertEqual(selected['original_core_rows'],positions)

    def test_all_invalid_csv_envelopes(self):
        for name,text,positions in cases.rejected_csv_cases():
            with self.subTest(name=name), self.assertRaises((AssertionError,ValueError,csv.Error)):
                cases.metadata(text,positions)

    def test_metadata_never_converts_invalid_unselected_value(self):
        selected=cases.metadata(cases.csv_text([('a','1','x'),('b','arbitrary-not-float','x')]),[0])
        self.assertEqual(selected['rows'],[{'intervention_id':'a'}])

    def test_bad_row_masks(self):
        text=cases.csv_text([('a','1','x'),('b','2','x')])
        for mask in ([],[1,0],[0,0],[2],[-1],[True]):
            with self.subTest(mask=mask),self.assertRaises(AssertionError): cases.metadata(text,mask)

    def test_id_order_corruption_rejected(self):
        text=cases.csv_text([('a','1','x'),('b','2','x')]); selected=cases.metadata(text,[0,1])
        selected['rows'].reverse()
        with self.assertRaises(AssertionError): cases.original_pandas(text,FakePandas(),selected)

    def test_nonfinite_rejected_by_original_wrapper(self):
        for word in ('NaN','inf','-inf','1e309'):
            text=cases.csv_text([('a',word,'x')]); selected=cases.metadata(text,[0])
            with self.assertRaises(AssertionError): cases.original_pandas(text,FakePandas(),selected)

    def test_payload_component_selection(self):
        fake={component+'/file': 'x' for component in COMPONENTS}
        fake['unused_package/file']='y'
        self.assertEqual(len(payload_members(fake)),len(COMPONENTS))

    def test_missing_pandas_payload_is_blocker(self):
        fake={component+'/file':'x' for component in COMPONENTS if component!='pandas'}
        with self.assertRaises(AssertionError): payload_members(fake)

    def test_native_suffix_roster(self):
        self.assertEqual(native_members({'p/a.pyd':'a','p/b.DLL':'b','p/c.py':'c'}),{'p/a.pyd':'a','p/b.DLL':'b'})

    def test_one_thread_environment(self):
        check_thread_environment(dict(THREAD_ENV))
        for key in THREAD_ENV:
            bad=dict(THREAD_ENV);bad[key]='2'
            with self.subTest(key=key),self.assertRaises(AssertionError):check_thread_environment(bad)

    def test_exact_loader_python_certificate_roster(self):
        home=Path('C:/invented_python').resolve()
        files={str(home/name):'a'*64 for name in ('python.exe','python3.dll','python312.dll')}
        record={'python_executable':str(home/'python.exe'),'python_native_files':files}
        self.assertEqual(certificate_python_files(record),files)

    def test_extra_python_native_certificate_is_rejected(self):
        home=Path('C:/invented_python').resolve()
        files={str(home/name):'a'*64 for name in ('python.exe','python3.dll','python312.dll','_csv.pyd')}
        with self.assertRaises(AssertionError):
            certificate_python_files({'python_executable':str(home/'python.exe'),'python_native_files':files})

    def test_resource_start_exact_boundary(self):
        state={'physical_available':512*2**20,'commit_headroom':896*2**20+2**30,'disk_available':2**30}
        self.assertIsNone(resource_failure(state,0.,startup=True))
        state['physical_available']-=1
        self.assertIsNotNone(resource_failure(state,0.,startup=True))

    def test_resource_stop_exact_boundary(self):
        state={'physical_available':256*2**20,'commit_headroom':2**30,'disk_available':256*2**20}
        self.assertIsNone(resource_failure(state,120.,2))
        for key in state:
            bad=dict(state);bad[key]-=1
            self.assertIsNotNone(resource_failure(bad,120.,2))

    def test_final_completion_just_after_deadline_fails(self):
        state={'physical_available':2**30,'commit_headroom':3*2**30,'disk_available':2**30}
        self.assertIsNotNone(resource_failure(state,120.00001,0))
        self.assertIsNotNone(resource_failure(state,0.,3))

    def test_solver_source_not_imported_by_stdtests(self):
        self.assertFalse(any(name.split('.')[0] in ('numpy','pandas','scipy') for name in sys.modules))

    def test_scientific_child_no_site_flag_is_fixed(self):
        tree=ast.parse((SRC/'supervise.py').read_text(encoding='utf-8'))
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call)
               and isinstance(node.func,ast.Attribute) and node.func.attr=='spawn']
        self.assertEqual(len(calls),1)
        command=calls[0].args[0]
        self.assertIsInstance(command,ast.List)
        self.assertEqual([node.value for node in command.elts[1:5]],['-S','-B','-u','-m'])

    def test_all_owned_sources_parse(self):
        for path in SRC.glob('*.py'): ast.parse(path.read_text(encoding='utf-8'))


def run():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    assert result.wasSuccessful()
    jsave(OUT/'stdlib_test_receipt_final.json',{'status':'PASS_STDLIB_MOCK_PREPARATION_ONLY',
        'tests_run':result.testsRun,'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in SRC.glob('*.py')},
        'scientific_modules_imported':False,'native_profile_executed':False,
        'project_biological_inputs_read':False})


if __name__=='__main__':run()
