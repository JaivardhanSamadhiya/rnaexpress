import unittest
from . import checks as c
class Tests(unittest.TestCase):
 def test_unique_author_wt_required(self):
  self.assertEqual(c.single([{"type":"WT","id":"x"}],"type","WT")["id"],"x")
  for rows in ([],[{"type":"WT"},{"type":"WT"}]):
   with self.assertRaises(AssertionError):c.single(rows,"type","WT")
 def test_ranges_not_nearest_sequence(self):
  self.assertEqual(c.index_set("1:2,7:8"),{1,2,7,8})
  for value in ("0","8:7","1:3,3:4","1-4",""):
   with self.assertRaises(AssertionError):c.index_set(value)
 def test_wrong_ref_alt_or_coordinates_rejected(self):
  self.assertEqual(c.expected_check("ACGT","TCGT",{1},("A","T")),{1:("A","T")})
  for pos,pair in (({2},("A","T")),({1},("G","T"))):
   with self.assertRaises(AssertionError):c.expected_check("ACGT","TCGT",pos,pair)
 def test_full_physical_edits_and_indels(self):
  self.assertEqual(len(c.diff("AAAA","CCCC")),4)
  self.assertIsNone(c.diff("AAAA","AAA"))
  with self.assertRaises(AssertionError):c.expected_check("AAAA","AAA",{1})
 def test_compensatory_union_no_folding_claim(self):
  self.assertTrue(c.quartet_union("ACGT","TCGT","ACGA","TCGA"))
  with self.assertRaises(AssertionError):c.quartet_union("ACGT","TCGT","ACGA","TCGT")
 def test_explicit_namespace_alias_only(self):
  self.assertEqual(c.alias("hTR","hTR_512"),"hTR:512")
  self.assertEqual(c.alias("ms2_4x","ms2-4x:10"),"design:10")
  with self.assertRaises(AssertionError):c.alias("hTR","unrelated_512")
if __name__=="__main__":unittest.main(verbosity=2)
