import unittest,zipfile,io
from .extract_v2 import decode
N="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
def workbook(row):
 data=io.BytesIO()
 xml='<worksheet xmlns="'+N+'"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Name</t></is></c><c r="B1" t="inlineStr"><is><t>Number of oligos</t></is></c></row>'+row+'</sheetData></worksheet>'
 with zipfile.ZipFile(data,"w") as z:z.writestr("xl/worksheets/sheet1.xml",xml)
 return zipfile.ZipFile(io.BytesIO(data.getvalue()))
class Tests(unittest.TestCase):
 def test_author_total_formula_unresolved_no_cache_or_evaluation(self):
  with workbook('<row r="2"><c r="A2" t="inlineStr"><is><t>Total</t></is></c><c r="B2"><f>SUM(B3:B9)</f><v>999</v></c></row>') as z:
   rows,forms=decode(z,"xl/worksheets/sheet1.xml",{"A":"Name","B":"Number of oligos"})
  self.assertIsNone(rows[0]["Number of oligos"]);self.assertFalse(forms[0]["cached_value_used"])
 def test_formula_in_identity_rejected(self):
  with workbook('<row r="2"><c r="A2" t="str"><f>anything()</f><v>name</v></c></row>') as z:
   with self.assertRaises(AssertionError):decode(z,"xl/worksheets/sheet1.xml",{"A":"Name","B":"Number of oligos"})
 def test_nonselected_measurement_numeric_text_ignored(self):
  with workbook('<row r="2"><c r="A2" t="inlineStr"><is><t>fragment</t></is></c><c r="B2"><v>3</v></c><c r="C2" t="unknown"><v>NOT_A_NUMBER</v></c></row>') as z:
   rows,_=decode(z,"xl/worksheets/sheet1.xml",{"A":"Name","B":"Number of oligos"})
  self.assertEqual(rows[0]["Number of oligos"],3);self.assertNotIn("C",rows[0])
 def test_missing_design_cells_preserved(self):
  with workbook('<row r="2"><c r="A2"/><c r="B2"/></row>') as z:
   rows,_=decode(z,"xl/worksheets/sheet1.xml",{"A":"Name","B":"Number of oligos"})
  self.assertIsNone(rows[0]["Name"]);self.assertIsNone(rows[0]["Number of oligos"])
 def test_fractional_design_count_rejected(self):
  with workbook('<row r="2"><c r="B2"><v>1.5</v></c></row>') as z:
   with self.assertRaises(AssertionError):decode(z,"xl/worksheets/sheet1.xml",{"A":"Name","B":"Number of oligos"})
if __name__=="__main__":unittest.main(verbosity=2)
