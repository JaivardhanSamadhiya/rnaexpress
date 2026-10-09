import unittest
from .acquire import decode
class MetadataIdentity(unittest.TestCase):
 def test_experiment(self):
  b=b'<EXPERIMENT_SET><EXPERIMENT accession="SRX1"><TITLE>rep1</TITLE><DESIGN><DESIGN_DESCRIPTION>one culture</DESIGN_DESCRIPTION><SAMPLE_DESCRIPTOR accession="SRS1"/><LIBRARY_DESCRIPTOR><LIBRARY_NAME>Input1</LIBRARY_NAME><LIBRARY_LAYOUT><PAIRED/></LIBRARY_LAYOUT></LIBRARY_DESCRIPTOR></DESIGN></EXPERIMENT></EXPERIMENT_SET>'
  x=decode(b,'experiment','SRX1');self.assertEqual(x['DESIGN_DESCRIPTION'],'one culture');self.assertEqual(x['LIBRARY_LAYOUT'][0]['tag'],'PAIRED')
 def test_sample_external_id(self):
  x=decode(b'<SAMPLE_SET><SAMPLE accession="SRS1"><IDENTIFIERS><EXTERNAL_ID namespace="BioSample">SAMN1</EXTERNAL_ID></IDENTIFIERS></SAMPLE></SAMPLE_SET>','sample','SAMN1')
  self.assertEqual(x['returned_attributes']['accession'],'SRS1')
 def test_wrong_identity(self):
  with self.assertRaises(AssertionError):decode(b'<SAMPLE accession="SRS1"/>','sample','SAMN1')
 def test_multiple_objects(self):
  with self.assertRaises(AssertionError):decode(b'<SAMPLE_SET><SAMPLE accession="A"/><SAMPLE accession="B"/></SAMPLE_SET>','sample','A')
 def test_reject_entity(self):
  with self.assertRaises(AssertionError):decode(b'<!DOCTYPE SAMPLE><SAMPLE accession="A"/>','sample','A')
if __name__=='__main__':unittest.main()
