"""Invented pretty/minified syntax tests; no project sequence or parameter reads."""
import json,unittest
from unittest import mock
from .common import ROOT,OUT,sha,save
from . import tests as original_tests
from .tests_v2 import CompletionTests
from . import worker_v3
from .selective_metadata_v3 import selected_rows,fields,value_end,whitespace
def specimen():
 return {"selected_columns_only":["ID","Sequence"],"rows":[{"source_excel_row":2,"ID":"inventedWT","Sequence":"ACGT"},
  {"source_excel_row":3,"ID":"SKIPPED_ID_SENTINEL","Sequence":{"nested":["SKIPPED_VALUE_SENTINEL",True,None,-1.25e3,{"escaped":"quote\\\"{}[]"}]}}],
  "nonselected_values_analyzed":False}
class ParserTests(unittest.TestCase):
 def test_minified_pretty_parity(self):
  for options in ({},{"indent":2},{"indent":4,"sort_keys":True},{"separators":(",",":")}):
   x,n=selected_rows(json.dumps(specimen(),**options)+" \r\n\t",{2})
   self.assertEqual(n,2);self.assertEqual(x[2]["Sequence"],"ACGT")
 def test_explicit_row_end_followed_by_pretty_space(self):
  text='  {"x": {"a": [1, 2, {"z":true}]} } \r\n, NEXT'
  start=text.index("{");end=value_end(text,start)
  self.assertEqual([k for k,a,b in fields(text,start,end)],["x"])
  self.assertEqual(whitespace(text,end,end),end)
 def test_bound_must_not_hide_internal_garbage(self):
  with self.assertRaises((AssertionError,ValueError)):list(fields('{"a":1} x'))
 def test_skipped_values_not_semantically_decoded(self):
  seen=[];selected_rows(json.dumps(specimen(),indent=2),{2},lambda purpose,raw:seen.append((purpose,raw)))
  self.assertFalse(any("SKIPPED" in raw for purpose,raw in seen))
  self.assertEqual(sum(p=="selected_WT_row" for p,r in seen),1)
 def test_invalid_skipped_scalars(self):
  text=json.dumps(specimen(),separators=(",",":"))
  for bad in ("NaN","Infinity","truX","+1","01","1.","1e","--1"):
   broken=text.replace('"SKIPPED_VALUE_SENTINEL"',bad)
   with self.assertRaises((AssertionError,ValueError)):selected_rows(broken,{2})
 def test_invalid_escape_in_skipped_string(self):
  text=json.dumps(specimen())
  for bad in ('"bad\\q"','"bad\\u12xz"','"bad'+chr(1)+'"'):
   with self.assertRaises((AssertionError,ValueError)):selected_rows(text.replace('"SKIPPED_VALUE_SENTINEL"',bad),{2})
 def test_duplicate_nested_skipped_keys(self):
  text=json.dumps(specimen()).replace('"SKIPPED_VALUE_SENTINEL"','{"a":1,"a":2}')
  with self.assertRaises((AssertionError,ValueError)):selected_rows(text,{2})
 def test_escaped_duplicate_keys(self):
  text=json.dumps(specimen()).replace('"SKIPPED_VALUE_SENTINEL"','{"a":1,"\\u0061":2}')
  with self.assertRaises((AssertionError,ValueError)):selected_rows(text,{2})
 def test_invalid_array_object_delimiters(self):
  text=json.dumps(specimen()).replace('"SKIPPED_VALUE_SENTINEL"','REPLACE')
  for bad in ('[1,]','{"a":1,}','[1 2]','{"a" 1}','[}','true false'):
   with self.assertRaises((AssertionError,ValueError)):selected_rows(text.replace('REPLACE',bad),{2})
 def test_truncation_and_suffix_rejected(self):
  text=json.dumps(specimen(),indent=2)
  for bad in (text[:-1],text+'false',text+'{}'):
   with self.assertRaises((AssertionError,ValueError)):selected_rows(bad,{2})
 def test_scoped_binding_restored_on_success(self):
  original=worker_v3.audit.selected_rows;calls=[]
  with mock.patch.object(worker_v3.audit,"run",lambda:calls.append(worker_v3.audit.selected_rows is selected_rows)):
   worker_v3.execute_stage("audit")
  self.assertEqual(calls,[True]);self.assertIs(worker_v3.audit.selected_rows,original)
 def test_scoped_binding_restored_on_failure(self):
  original=worker_v3.audit.selected_rows
  def fail():
   self.assertIs(worker_v3.audit.selected_rows,selected_rows);raise RuntimeError("invented")
  with mock.patch.object(worker_v3.replay,"run",fail):
   with self.assertRaisesRegex(RuntimeError,"invented"):worker_v3.execute_stage("replay")
  self.assertIs(worker_v3.audit.selected_rows,original)
def run():
 suite=unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromTestCase(original_tests.Tests),
  unittest.defaultTestLoader.loadTestsFromTestCase(CompletionTests),unittest.defaultTestLoader.loadTestsFromTestCase(ParserTests)))
 with mock.patch.object(original_tests,"selected_rows",selected_rows):
  result=unittest.TextTestRunner(verbosity=2).run(suite)
 assert result.wasSuccessful()
 names=("selective_metadata_v3.py","worker_v3.py","supervise_v3.py","freeze_v3.py","tests_v3.py")
 save(OUT/"synthetic_tests_receipt_v3.json",{"status":"PASS_INVENTED_BOUNDED_JSON_V3","tests":result.testsRun,
  "biological_values_read":False,"parameter_values_read":False,"actual_worker_or_native_guard_called":False,"models_fit":0,
  "original_design_manifest_sha256":sha(OUT/"design_manifest.json"),"v2_design_manifest_sha256":sha(OUT/"design_manifest_v2.json"),
  "original_v2_tests_receipt_sha256":sha(OUT/"synthetic_tests_receipt_v2.json"),
  "source_files":{("src/"+OUT.name+"/"+name):sha(ROOT/"src"/OUT.name/name) for name in names}})
if __name__=="__main__":run()
