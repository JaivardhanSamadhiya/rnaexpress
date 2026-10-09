import unittest
from .acquire import gb,hits,rc
class References(unittest.TestCase):
 def test_versioned_record(self):self.assertEqual(gb(b'LOCUS X\nVERSION NR_X.1\nORIGIN\n 1 acgtac\n//\n','NR_X.1'),'ACGTAC')
 def test_reject_substituted_version(self):
  with self.assertRaises(AssertionError):gb(b'VERSION NR_X.2\nORIGIN\n 1 acgt\n//','NR_X.1')
 def test_all_repeated_hits(self):self.assertEqual(hits('AAAA','AA'),[0,1,2])
 def test_minus_strand(self):self.assertEqual(rc('ACCGT'),'ACGGT')
if __name__=='__main__':unittest.main()
