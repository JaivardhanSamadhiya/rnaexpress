"""Preserves16-test v1 receipt; adds invented final-resource-bound arithmetic."""
import unittest
from .common import ROOT,OUT,sha,save
from .tests import Tests
from .supervise_v2 import completion_failure,PEAK_BYTES
class CompletionTests(unittest.TestCase):
 def test_just_after_deadline(self):
  self.assertIn("including final completion",completion_failure(30.000001,100*2**20,0,None,True))
 def test_exact_deadline(self):self.assertIsNone(completion_failure(30.,100*2**20,0,None,True))
 def test_unsampled_peak(self):self.assertIn("lifetime",completion_failure(.01,PEAK_BYTES+1,0,None,True))
 def test_final_query_failure(self):self.assertIn("unavailable",completion_failure(.01,100*2**20,0,None,False))
 def test_prior_failure_and_bad_exit(self):
  self.assertEqual(completion_failure(.01,100*2**20,0,"preserved",True),"preserved")
  self.assertIn("failed",completion_failure(.01,100*2**20,1,None,True))
 def test_zero_peak(self):self.assertIn("positive",completion_failure(.01,0,0,None,True))
def run():
 suite=unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromTestCase(Tests),unittest.defaultTestLoader.loadTestsFromTestCase(CompletionTests)))
 result=unittest.TextTestRunner(verbosity=2).run(suite);assert result.wasSuccessful()
 names=("supervise_v2.py","tests_v2.py","freeze_v2.py")
 save(OUT/"synthetic_tests_receipt_v2.json",{"status":"PASS_SYNTHETIC_ONLY_V2_FINAL_CAPS","tests":result.testsRun,
  "sequence_values_read":False,"published_parameter_values_loaded":False,"native_process_calls_in_tests":False,"models_fit":0,
  "original_synthetic_receipt_sha256":sha(OUT/"synthetic_tests_receipt.json"),
  "original_design_manifest_sha256":sha(OUT/"design_manifest.json"),
  "source_files":{("src/"+OUT.name+"/"+name):sha(ROOT/"src"/OUT.name/name) for name in names}})
if __name__=="__main__":run()
