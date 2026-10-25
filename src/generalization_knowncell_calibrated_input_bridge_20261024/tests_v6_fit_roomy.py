"""Private source/path regressions only; no data, native import or stage."""
import ast
from pathlib import Path
import sys
import unittest
from . import spec_v3 as old,spec_v6_fit_roomy as new
from src.generalization_knowncell_metadata_verification_execution_20261024 import common as saved


class Cases(unittest.TestCase):
    def test_complete_bridge_function_AST_is_identical_to_V3(self):
        base=Path(__file__).parent
        def function(name):return next(n for n in ast.parse((base/name).read_text()).body if isinstance(n,ast.FunctionDef))
        self.assertEqual(ast.dump(function('bridge_v3.py'),include_attributes=False),ast.dump(function('bridge_v6_fit_roomy.py'),include_attributes=False))

    def test_new_only_fit_path_cannot_replace_original_static_binding(self):
        self.assertNotEqual(new.binding_path('fit'),old.binding_path('fit'))
        self.assertEqual(new.binding_path('fit'),'results/'+new.NS+'/root_bindings_v6_fit_roomy_20261025.json')
        for stage in ('prefit','replay','evaluation'):
            with self.subTest(stage=stage),self.assertRaises(AssertionError):new.binding_path(stage)

    def test_schema_and_stable_source_or_runtime_contracts_unchanged(self):
        for key in ('HASH_FIELDS','OWNER_FIELDS','BINDING_STATUS','POLICY_SHA','AUTH_SHA','SCOPE_SHA','ARRAY_SHA','V4_ORIGIN_SHA'):
            self.assertEqual(getattr(new,key),getattr(old,key))


def run():
    assert not any(n.split('.')[0] in ('numpy','pandas','scipy','torch','sklearn','openvino') for n in sys.modules)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases));assert result.wasSuccessful()
    names=('spec_v6_fit_roomy.py','bridge_v6_fit_roomy.py','tests_v6_fit_roomy.py')
    saved.save_new(saved.ROOT/'results'/new.NS/'synthetic_tests_receipt_v6_fit_roomy_20261025.json',
        {'status':'PASS_INVENTED_V6_ROOMY_FRESH_FIT_BINDING_PATH_NOT_RETRY_AUTHORITY','tests':result.testsRun,
         'sources':{(Path(__file__).parent/name).relative_to(saved.ROOT).as_posix():saved.sha((Path(__file__).parent/name).read_bytes()) for name in names},
         'scientific_function_AST_identical_to_frozen_V3':True,'actual_jobs_native_probes_payload_reads_or_fits':0})


if __name__=='__main__':run()
