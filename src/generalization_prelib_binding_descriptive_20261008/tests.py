import io,math,unittest,zipfile
from unittest.mock import patch
import xml.etree.ElementTree as ET
from .extract import count_cell,effect,mean_log,decode,FIELDS,N

def cell(body,attrs=""):
 return ET.fromstring('<c xmlns="'+N['m']+'" '+attrs+'>'+body+'</c>')
def row(values):return {"raw_counts":{k:{"value":v} for k,v in zip(('Input_1.raw','Input_2.raw','PUM1_IP_1.raw','PUM1_IP_2.raw','PUM2_IP_1.raw','PUM2_IP_2.raw'),values)}}
def workbook(identity='v',seq='A'*140,bad_header=False):
 cells=[]
 for c,h in FIELDS.items():cells.append('<c r="'+c+'1" t="inlineStr"><is><t>'+('wrong' if bad_header and c=='L' else h)+'</t></is></c>')
 header='<row r="1">'+''.join(cells)+'</row>'
 data='<row r="2"><c r="A2" t="inlineStr"><is><t>'+identity+'</t></is></c><c r="C2" t="inlineStr"><is><t>'+seq+'</t></is></c>'
 data+=''.join('<c r="'+c+'2"><v>0</v></c>' for c in ('L','M','N','O','P','Q'))+'</row>'
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="'+N['m']+'"><sheetData>'+header+data+'</sheetData></worksheet>')
 return zipfile.ZipFile(io.BytesIO(b.getvalue()))
class Contracts(unittest.TestCase):
 def test_zero_not_missing(self):self.assertEqual(count_cell(cell('<v>0</v>'))['value'],0)
 def test_missing_distinct(self):self.assertEqual(count_cell(None)['missing_kind'],'absent_cell');self.assertEqual(count_cell(cell(''))['missing_kind'],'blank_numeric_cell')
 def test_integral_decimal(self):self.assertEqual(count_cell(cell('<v>2.000E2</v>'))['value'],200)
 def test_invalid_counts(self):
  for s in ('-1','1.2','NaN','Infinity','1000000000001'):
   with self.assertRaises(AssertionError):count_cell(cell('<v>'+s+'</v>'))
 def test_formula_cached_never_used(self):
  with self.assertRaises(AssertionError):count_cell(cell('<f>SUM(A1)</f><v>3</v>'))
 def test_string_number_refused(self):
  with self.assertRaises(AssertionError):count_cell(cell('<v>3</v>','t="s"'))
 def test_pairing_invariant(self):
  a=row([20,40,10,80,3,5]);b=row([5,9,2,6,1,4]);x=effect(a,b,'PUM1',.5)
  swapped=row([40,20,10,80,3,5]);self.assertAlmostEqual(x['delta_mean_log_enrichment'],effect(swapped,b,'PUM1',.5)['delta_mean_log_enrichment'])
 def test_self_delta(self):
  a=row([0,4,3,0,1,9])
  for p in ('PUM1','PUM2'):
   for pseudo in (.5,1.):self.assertEqual(effect(a,a,p,pseudo)['delta_mean_log_enrichment'],0)
 def test_component_identity(self):
  x=effect(row([0,4,3,0,1,9]),row([5,6,7,8,9,10]),'PUM1',.5)
  self.assertAlmostEqual(x['delta_mean_log_enrichment'],x['delta_logIP']-x['delta_logInput'])
 def test_incomplete_retained(self):self.assertFalse(effect(row([None,4,3,0,1,9]),row([5,6,7,8,9,10]),'PUM1',.5)['complete'])
 def test_sensitivity_fixed(self):
  a=row([0,4,3,0,1,9]);b=row([5,6,7,8,9,10]);self.assertNotEqual(effect(a,b,'PUM1',.5)['delta_mean_log_enrichment'],effect(a,b,'PUM1',1.)['delta_mean_log_enrichment'])
 def test_literal_source_replay(self):
  with workbook() as z:self.assertEqual(len(decode(z,'xl/worksheets/sheet1.xml',{2:{'ID':'v','Sequence':'A'*140}})),1)
 def test_wrong_identity_opens_no_counts(self):
  with workbook(identity='bad') as z,patch('src.generalization_prelib_binding_descriptive_20261008.extract.count_cell') as spy:
   with self.assertRaises(AssertionError):decode(z,'xl/worksheets/sheet1.xml',{2:{'ID':'v','Sequence':'A'*140}})
   spy.assert_not_called()
 def test_header_change_refused(self):
  with workbook(bad_header=True) as z:
   with self.assertRaises(AssertionError):decode(z,'xl/worksheets/sheet1.xml',{2:{'ID':'v','Sequence':'A'*140}})
if __name__=='__main__':unittest.main()
