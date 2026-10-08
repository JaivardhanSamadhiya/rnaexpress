import unittest
from .audit import parent_for,check
class Tests(unittest.TestCase):
 def test_parent_from_literal_hierarchy_not_nearest(self):
  parent={"ID":"gene:baseline:gene","Sequence":"A"*140}
  self.assertEqual(parent_for([parent,{"ID":"gene:Mut:1:A->C","Sequence":"C"+"A"*139}],"gene"),parent)
  with self.assertRaises(AssertionError):parent_for([parent,parent],"gene")
 def test_exact_physical_ref_alt(self):
  parent={"Sequence":"A"*140};variant={"ID":"gene:Mut:3:A->C","Sequence":"AA"+"C"+"A"*137}
  self.assertEqual(check(parent,variant,"gene"),(3,"A","C"))
  variant["Sequence"]="CA"+"C"+"A"*137
  with self.assertRaises(AssertionError):check(parent,variant,"gene")
 def test_wrong_reference_index_or_family_rejected(self):
  for identifier in ("gene:Mut:0:A->C","gene:Mut:1:G->C","other:Mut:1:A->C"):
   with self.assertRaises(AssertionError):check({"Sequence":"A"*140},{"ID":identifier,"Sequence":"C"+"A"*139},"gene")
if __name__=="__main__":unittest.main(verbosity=2)
