"""Synthetic source-free tests; no runtime/biological sequence/parameter loading."""
import json,unittest
from .common import ROOT,OUT,sha,save
from .geometry import sites,pairs,select_pair,audit_sequence
from .selective_metadata import selected_rows
from .replay import independent_windows,independent_pairs
def fake_energy(x):return float(x.count("C"))
def design(rows):return json.dumps({"selected_columns_only":["ID","Sequence"],"rows":rows,"nonselected_values_analyzed":False})
def row(i,seq="ACGT"):return {"source_excel_row":i,"ID":"invented:"+str(i),"Sequence":seq}
class Tests(unittest.TestCase):
 def test_no_site(self):self.assertEqual(audit_sequence("A"*140,fake_energy)["site_count"],0)
 def test_coreN_allbases(self):
  for n in "ACGT":
   a,b=sites("TGTA"+n+"ATAT",fake_energy);self.assertEqual(len(a),1);self.assertEqual(a[0]["start_0based"],0)
 def test_terminal_without9(self):
  a,b=sites("TGTACATA",fake_energy);self.assertEqual(len(a),0);self.assertEqual(b[0]["core_start_0based"],0)
 def test_exact_endpoint(self):
  a,b=sites("A"*131+"TGTACATAT",fake_energy);self.assertEqual(a[0]["contact_end_0based_exclusive"],140)
 def test_touching9windows(self):
  x=audit_sequence("TGTACATAT"*2,fake_energy);self.assertEqual(x["nonoverlapping_pair_count"],1);self.assertEqual(x["selected_pair"]["intervening_bases"],0)
 def test_8core_nonoverlap_9window_overlap(self):
  x=audit_sequence("TGTACATA"*2+"T",fake_energy);self.assertEqual(x["site_count"],2);self.assertEqual(x["nonoverlapping_pair_count"],0)
 def test_all_pairs_and_tie(self):
  x=audit_sequence("TGTACATAT"*3,fake_energy);self.assertEqual(len(x["all_nonoverlapping_pairs"]),3)
  self.assertEqual((x["selected_pair"]["left_start_0based"],x["selected_pair"]["right_start_0based"]),(0,9))
 def test_min_energy_before_gap(self):
  x=audit_sequence("TGTACATAT"+"TGTA AATAT".replace(" ","")+"TGTA AATAT".replace(" ",""),fake_energy)
  self.assertEqual((x["selected_pair"]["left_start_0based"],x["selected_pair"]["right_start_0based"]),(9,18))
 def test_no_reverse_scan(self):
  reverse="TGTACATAT".translate(str.maketrans("ACGT","TGCA"))[::-1]
  self.assertEqual(sites(reverse,fake_energy)[0],[])
 def test_independent_geometry(self):
  for s in ("A"*140,"TGTACATAT"*3,"TGTACATA"*2+"T"):
   x=audit_sequence(s,fake_energy);a,b=independent_windows(s)
   self.assertEqual([r["start_0based"] for r in x["sites"]],a)
   self.assertEqual([(r["left_start_0based"],r["right_start_0based"],r["intervening_bases"]) for r in x["all_nonoverlapping_pairs"]],independent_pairs(a))
 def test_skip_nonselected_semantics(self):
  bad=row(3,{"not_a_sequence":"escaped quote\\\" and braces}{"})
  x,n=selected_rows(design([row(2),bad]),{2});self.assertEqual(n,2);self.assertEqual(set(x),{2})
 def test_missing_duplicate_rows(self):
  for rows in ([row(3)],[row(2),row(2)]):
   with self.assertRaises(AssertionError):selected_rows(design(rows),{2})
 def test_unknown_or_outcome_field(self):
  r=row(2);r["IP_input"]=1
  with self.assertRaises(AssertionError):selected_rows(design([r]),{2})
 def test_duplicate_json_field(self):
  text=design([row(2)]).replace('"source_excel_row": 2','"source_excel_row":2,"source_excel_row":2')
  with self.assertRaises(AssertionError):selected_rows(text,{2})
 def test_missing_or_changed_header(self):
  for columns in (["ID","Sequence","l2fc"],["Sequence","ID"]):
   d=json.loads(design([row(2)]));d["selected_columns_only"]=columns
   with self.assertRaises(AssertionError):selected_rows(json.dumps(d),{2})
 def test_invalid_DNA(self):
  for s in ("N"*140,"acgt","A"*141):
   with self.assertRaises(AssertionError):sites(s,fake_energy)
def run():
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 assert result.wasSuccessful()
 source=ROOT/"src"/OUT.name
 save(OUT/"synthetic_tests_receipt.json",{"status":"PASS_SYNTHETIC_ONLY","tests":result.testsRun,
  "sequence_values_read":False,"published_parameter_values_loaded":False,"scientific_runtime_imported":False,
  "models_fit":0,"source_files":{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(source.glob("*.py"))}})
if __name__=="__main__":run()
