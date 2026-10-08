"""Invented-site interval integrity only; no external values or project labels."""
from pathlib import Path
import hashlib,json,unittest
from .site_inventory import adjacent_intervals,OUT,SRC,jsave
class SiteIntervalTests(unittest.TestCase):
 def test_adjacent_merge_and_gaps(self):
  self.assertEqual(adjacent_intervals([('chr2',8),('chr2',9),('chr2',11)]),[('chr2',8,10),('chr2',11,12)])
 def test_repeated_sites_deduplicate_without_gap_bridge(self):
  self.assertEqual(adjacent_intervals([('chr1',10),('chr1',10),('chr1',13)]),[('chr1',10,11),('chr1',13,14)])
 def test_chromosomes_never_merge(self):
  self.assertEqual(adjacent_intervals([('chr2',5),('chr1',4),('chr2',6)]),[('chr1',4,5),('chr2',5,7)])
 def test_invalid_position_rejected_and_empty_supported(self):
  self.assertEqual(adjacent_intervals([]),[])
  for value in [-1,True,1.5]:
   with self.assertRaises(AssertionError):adjacent_intervals([('chr1',value)])
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SiteIntervalTests))
 assert result.wasSuccessful()
 jsave(OUT/'synthetic_tests_receipt.json',{'status':'PASS_INVENTED_SITE_INTERVAL_TESTS_ONLY','tests':result.testsRun,'annotation_values_read':False,'outcomes_read':False,'models_fit':0,'files':{str(p.relative_to(SRC)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SRC/'site_inventory.py',SRC/'tests.py']}})