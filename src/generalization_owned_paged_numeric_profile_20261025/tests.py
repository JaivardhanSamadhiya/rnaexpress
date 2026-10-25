"""Invented contradiction checks; no actual job or scientific import."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from .probe import compare_optimizer


class Cases(unittest.TestCase):
    def test_exact_original_invented_result_is_required(self):
        value={'status':'PASS_INVENTED_SCIPY_SOLVER_REFERENCE_AND_SCORER',
            'scipy_optimizer_units':12,'biological_model_fits':0,'checks':[{'gradient':1e-14}]}
        self.assertEqual(compare_optimizer(value,copy.deepcopy(value)),compare_optimizer(value,value))
        changed=copy.deepcopy(value);changed['checks'][0]['gradient']=2e-14
        with self.assertRaisesRegex(AssertionError,'differ'):compare_optimizer(changed,value)
        for key,bad in (('status','FAIL'),('scipy_optimizer_units',11),('biological_model_fits',1)):
            changed=copy.deepcopy(value);changed[key]=bad
            with self.subTest(key=key),self.assertRaises(AssertionError):compare_optimizer(changed,changed)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    root=Path(__file__).resolve().parents[2];ns=Path(__file__).parent.name
    with (root/'results'/ns/'synthetic_tests_receipt_final.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump({'status':'PASS_INVENTED_EXACT_NUMERICAL_RESULT_CONTRADICTIONS','tests':result.testsRun,
            'source_sha256':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in Path(__file__).parent.glob('*.py')},'native_jobs_or_biological_payload_reads':0},stream,indent=2,sort_keys=True)
        stream.write('\n')
