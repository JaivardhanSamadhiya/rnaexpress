
"""Invented reference/factor/unsafe-class metadata contract tests."""
import unittest
from types import SimpleNamespace as S
from . import decode as d
def node(kind,value=None,attrs=None,tag=None,gp=64):
 return S(info=S(type=S(name=kind),gp=gp),value=value,attributes=attrs,tag=tag,referenced_object=None)
def char(value,gp=64):return node("CHAR",value.encode("ascii") if value is not None else None,gp=gp)
def strings(values):return node("STR",[char(v) for v in values])
def pair(values):
 result=node("NILVALUE")
 for name,value in reversed(list(values.items())):result=node("LIST",(value,result),tag=node("SYM",char(name)))
 return result
class Arr(list):
 def tolist(self):return list(self)
class Tests(unittest.TestCase):
 def test_string_encoding_and_missing_preserved(self):
  self.assertEqual(d.strings(strings(["a",None])),["a",None])
  self.assertEqual(d.string(node("CHAR","µ".encode("utf8"),gp=8)),"µ")
  with self.assertRaises(UnicodeDecodeError):d.string(node("CHAR",b"\xff",gp=64))
 def test_reference_cycle_rejected(self):
  a=node("REF");a.referenced_object=a
  with self.assertRaises(AssertionError):d.deref(a)
 def test_duplicate_named_global_rejected(self):
  end=pair({"x":char("b")});top=node("LIST",(char("a"),end),tag=node("SYM",char("x")))
  with self.assertRaises(AssertionError):d.pairs(top)
 def test_factor_missing_and_levels_preserved(self):
  obj=node("INT",Arr([1,2,-2147483648,None]),attrs=pair({"class":strings(["factor"]),"levels":strings(["WT","mut"])}))
  value,meta=d.column(obj);self.assertEqual(value,["WT","mut",None,None]);self.assertEqual(meta["levels"],["WT","mut"])
 def test_out_of_bounds_factor_rejected(self):
  obj=node("INT",Arr([3]),attrs=pair({"class":strings(["factor"]),"levels":strings(["WT","mut"])}))
  with self.assertRaises(AssertionError):d.column(obj)
 def test_unknown_class_closure_altrep_numeric_rejected(self):
  with self.assertRaises(AssertionError):d.column(node("STR",[char("a")],attrs=pair({"class":strings(["unsafe"])})))
  for kind in ("ALTREP","CLO","PROM","ENV","EXTPTR","REAL"):
   with self.assertRaises(AssertionError):d.column(node(kind,Arr([1])))
  with self.assertRaises(AssertionError):d.column(node("INT",Arr([1])))
 def test_integer_design_metadata_explicit_allow(self):
  values,_=d.column(node("INT",Arr([2,-2147483648])),True);self.assertEqual(values,[2,None])
 def test_wrong_annotation_class_and_alias_columns_rejected(self):
  with self.assertRaises(AssertionError):d.columns(node("VEC",[],attrs=pair({"class":strings(["list"]),"names":strings([])})))
  obj=node("VEC",[char("a"),char("b")],attrs=pair({"class":strings(["data.frame"]),"names":strings(["tileID","tileID"])}))
  with self.assertRaises(AssertionError):d.columns(obj)
if __name__=="__main__":unittest.main(verbosity=2)
