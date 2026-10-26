"""Invented metadata and temporary software-like files only; no live inventory."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from .contracts import accepted_v4, compare_inventory, decode, digest, native_contract, payload_contract, relative_key
from .inventory import enumerate_native, enumerate_payload, safe_file, save, stable_file_hash

A, B, C, D = ('a'*64,'b'*64,'c'*64,'d'*64)


def payload_fixture():
    files = {'numpy/item'+str(i)+'.txt':A for i in range(7996)}
    caches = {'__pycache__/six.cpython-312.pyc':B,'__pycache__/threadpoolctl.cpython-312.pyc':C}
    versions = {'numpy':'1.26.4','pandas':'2.2.3','scipy':'1.14.1'}
    base = {'files':files,'file_count':7996,'versions':versions,'current_python_native_files':{'C:/py/python.exe':A}}
    expanded = dict(base,files=dict(files,**caches),file_count=7998)
    return base,expanded,{'files':dict(expanded['files'])},caches


def native_fixture():
    home = 'C:\\bundled'
    old = {home+'\\'+name:A for name in ('python.exe','python3.dll','python312.dll','DLLs\\_ssl.pyd')}
    replacements = {'python.exe':B,'python3.dll':C,'python312.dll':D}
    observed = dict(old)
    observed.update({home+'\\'+name:want for name,want in replacements.items()})
    return old,observed,replacements,home


def v4_fixture():
    names = ('preparation_manifest.json','supervisor_receipt.json','invented_profile_receipt.json',
        'actual_origin_receipt.json','pandas_admission_candidate.json')
    hashes = {name:A for name in names}
    status = {'status':'VERIFIED_CURRENT_RUNTIME_INVENTED_COMPATIBILITY_NOT_BIOLOGICAL_ADMISSION',
        'initial_manifest_sha256':A,'metadata_array_label_and_fit_admissions_granted_here':False,
        'verified_files':dict(hashes)}
    supervisor = {'status':'PASS_BOUNDED_ONE_THREAD_INVENTED_PANDAS_SCIPY_PROFILE_V4',
        'exit_code':0,'failure':None,'manifest_observed_final_sha256':A,'invented_completion_sha256':A}
    completion = {'status':'PASS_INVENTED_PANDAS_SCIPY_PROFILE_CURRENT_PYTHON_V4',
        'actual_origin_receipt_sha256':A,'pandas_admission_candidate_sha256':A}
    candidate = {'status':'PASS_PINNED_PANDAS223_CURRENT_PYTHON_AND_INVENTED_ORIGINAL_PARSER',
        'actual_origin_receipt_sha256':A,'old_interpreter_bitwise_parity_established':False}
    return status,supervisor,completion,candidate,hashes,A


class SourceTests(unittest.TestCase):
    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'[]',b'{broken}'):
            with self.assertRaises((AssertionError,json.JSONDecodeError)):
                decode(raw)
        self.assertEqual(decode(b'{"x":{"q":1}}'),{'x':{'q':1}})

    def test_relative_paths_reject_escape_noncanonical_and_drive(self):
        for name in ('../native','/native','a/../b','C:/native','a\\b','a//b','a/./b',''):
            with self.assertRaises(AssertionError):relative_key(name)
        self.assertEqual(relative_key('numpy/core/file.pyd'),'numpy/core/file.pyd')

    def test_exact_7996_plus_two_cache_ancestry(self):
        base,expanded,full,caches = payload_fixture()
        self.assertEqual(len(payload_contract(base,expanded,full,caches,['numpy'])),7998)

    def test_ancestry_extra_cache_or_missing_original_rejected(self):
        for mode in ('extra','missing','changed','fullpin','version'):
            base,expanded,full,caches = payload_fixture()
            if mode == 'extra':expanded['files']['__pycache__/other.pyc']=D
            if mode == 'missing':expanded['files'].pop('numpy/item0.txt')
            if mode == 'changed':expanded['files']['numpy/item0.txt']=D
            if mode == 'fullpin':full['files']['numpy/item0.txt']=D
            if mode == 'version':expanded['versions']=dict(expanded['versions'],numpy='2.4.6')
            with self.assertRaises(AssertionError):payload_contract(base,expanded,full,caches,['numpy'])

    def test_exact_payload_membership_and_hashes(self):
        self.assertEqual(compare_inventory({'numpy/a':A},{'numpy/a':A},'invented'),1)
        for observed in ({'numpy/a':B},{'numpy/a':A,'numpy/b':A},{'numpy/b':A}):
            with self.assertRaises(AssertionError):compare_inventory({'numpy/a':A},observed,'invented')

    def test_native_exact_three_changes_and_untouched_other(self):
        self.assertEqual(len(native_contract(*native_fixture())),3)

    def test_native_extra_missing_or_fourth_drift_rejected(self):
        for mode in ('extra','missing','fourth','wrongnew'):
            old,observed,replacements,home = native_fixture()
            if mode == 'extra':observed[home+'\\DLLs\\extra.pyd']=D
            if mode == 'missing':observed.pop(home+'\\DLLs\\_ssl.pyd')
            if mode == 'fourth':observed[home+'\\DLLs\\_ssl.pyd']=B
            if mode == 'wrongnew':observed[home+'\\python.exe']=A
            with self.assertRaises(AssertionError):native_contract(old,observed,replacements,home)

    def test_native_case_duplicate_or_declared_unchanged_rejected(self):
        old,observed,replacements,home = native_fixture()
        old[home+'\\PYTHON.EXE']=A;observed[home+'\\PYTHON.EXE']=B
        with self.assertRaises(AssertionError):native_contract(old,observed,replacements,home)
        old,observed,replacements,home = native_fixture()
        old[home+'\\python.exe']=B
        with self.assertRaises(AssertionError):native_contract(old,observed,replacements,home)

    def test_v4_historical_chain(self):
        self.assertTrue(accepted_v4(*v4_fixture()))

    def test_v4_changed_receipt_failure_or_false_authority_rejected(self):
        for mode in ('hash','failure','authority','oldparity'):
            args = list(v4_fixture())
            if mode == 'hash':args[4]['actual_origin_receipt.json']=B
            if mode == 'failure':args[1]['failure']='invented error'
            if mode == 'authority':args[0]['metadata_array_label_and_fit_admissions_granted_here']=True
            if mode == 'oldparity':args[3]['old_interpreter_bitwise_parity_established']=True
            with self.assertRaises(AssertionError):accepted_v4(*args)

    def test_enumerate_only_selected_components_and_two_named_caches(self):
        with tempfile.TemporaryDirectory() as temporary:
            prefix = Path(temporary)
            for name in ('numpy/a.py','numpy/sub/b.pyd','__pycache__/six.pyc','__pycache__/threadpoolctl.pyc','__pycache__/not_admitted.pyc','other/c.py'):
                target=prefix/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'invented')
            paths=enumerate_payload(prefix,['numpy'],{'__pycache__/six.pyc':A,'__pycache__/threadpoolctl.pyc':A})
            self.assertEqual(set(paths),{'numpy/a.py','numpy/sub/b.pyd','__pycache__/six.pyc','__pycache__/threadpoolctl.pyc'})

    def test_missing_named_cache_and_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            prefix=Path(temporary);(prefix/'numpy').mkdir();(prefix/'numpy/a').write_bytes(b'x')
            with self.assertRaises(AssertionError):enumerate_payload(prefix,['numpy'],{'__pycache__/six.pyc':A})
            with self.assertRaises(AssertionError):safe_file(prefix/'numpy/a',prefix/'unrelated')

    def test_native_roster_rules_on_invented_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'DLLs').mkdir()
            for name in ('python.exe','python3.dll','python312.dll','DLLs/_ssl.pyd','DLLs/other.dll','not_selected.pyd','DLLs/source.py'):
                (root/name).write_bytes(b'invented')
            self.assertEqual({Path(name).relative_to(root).as_posix() for name in enumerate_native(root)},
                {'python.exe','python3.dll','python312.dll','DLLs/_ssl.pyd','DLLs/other.dll'})

    def test_opaque_hash_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'possible.pyc';source.write_bytes(b'opaque invented bytecode-like payload')
            value,metadata=stable_file_hash(source)
            self.assertEqual(value,digest(source.read_bytes()));self.assertEqual(metadata['size_bytes'],source.stat().st_size)
            output=root/'receipt.json';save(output,{'status':'invented'})
            with self.assertRaises(FileExistsError):save(output,{'status':'overwrite'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
