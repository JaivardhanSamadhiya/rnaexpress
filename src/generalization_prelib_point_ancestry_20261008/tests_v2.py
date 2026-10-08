import unittest
from .audit_v2 import parent_for,check,baseline_category
def allele(id_="Hafner_HIAT1:Mut:0:A->C",sequence="C"+"A"*139):return {"ID":id_,"Sequence":sequence}
class Tests(unittest.TestCase):
 def test_known_baseline_category_required(self):
  rows=[{"ID":"Hafner_HIAT1:Hafner_Pum2:native"},{"ID":"Hafner_HIAT1:unexpected:construct"}]
  self.assertEqual(parent_for(rows,"Hafner_HIAT1"),rows[0])
  with self.assertRaises(AssertionError):parent_for([rows[1]],"Hafner_HIAT1")
 def test_conflicting_duplicate_baseline_rejected(self):
  row={"ID":"Hafner_HIAT1:Hafner_Pum2:native","Sequence":"A"*140}
  with self.assertRaises(AssertionError):parent_for([row,{**row,"Sequence":"C"+"A"*139}],"Hafner_HIAT1")
 def test_zero_based_both_endpoints_complete_reconstruction(self):
  parent={"Sequence":"A"*140}
  self.assertEqual(check(parent,allele(),"Hafner_HIAT1"),(1,"A","C"))
  self.assertEqual(check(parent,allele("Hafner_HIAT1:Mut:139:A->C","A"*139+"C"),"Hafner_HIAT1"),(140,"A","C"))
 def test_one_based_shift_is_not_accepted(self):
  with self.assertRaises(AssertionError):check({"Sequence":"A"*140},allele("Hafner_HIAT1:Mut:1:A->C"),"Hafner_HIAT1")
 def test_wrong_reference_alternate_family_or_outside_index(self):
  for id_ in ("Hafner_HIAT1:Mut:0:G->C","Hafner_HIAT1:Mut:0:A->G","other:Mut:0:A->C","Hafner_HIAT1:Mut:140:A->C"):
   with self.assertRaises(AssertionError):check({"Sequence":"A"*140},allele(id_),"Hafner_HIAT1")
 def test_zero_or_two_physical_edits_rejected(self):
  for seq in ("A"*140,"CC"+"A"*138):
   with self.assertRaises(AssertionError):check({"Sequence":"A"*140},allele(sequence=seq),"Hafner_HIAT1")
 def test_invalid_dna_and_length_rejected(self):
  for seq in ("C"+"A"*138+"N","C"+"A"*138):
   with self.assertRaises(AssertionError):check({"Sequence":"A"*140},allele(sequence=seq),"Hafner_HIAT1")
 def test_wt_mpre_prefixes_not_interchangeable(self):
  row={"ID":"Hafner_HIAT1:Hafner_Pum2:WT","Sequence":"A"*140}
  with self.assertRaises(AssertionError):parent_for([row],"mHafner_HIAT1")
  self.assertEqual(baseline_category("mHafner_HIAT1"),"mHafner_Pum2")
 def test_unknown_template_category_not_admitted(self):
  with self.assertRaises(AssertionError):baseline_category("unknown")
if __name__=="__main__":unittest.main(verbosity=2)
