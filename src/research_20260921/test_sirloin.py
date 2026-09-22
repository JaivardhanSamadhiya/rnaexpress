"""Synthetic scoring and target-column access checks."""
import unittest
from unittest.mock import patch
from .sirloin_transfer import window_mean,motif_count,load_discovery


class SirloinTests(unittest.TestCase):
    def test_overlapping_window_score(self):
        self.assertEqual(window_mean('ACGTACG',{'ACGTAC':2.,'CGTACG':6.}),4.)
        with self.assertRaises(ValueError): window_mean('ACGTAN',{})
        with self.assertRaises(ValueError): window_mean('ACGTA',{})
        self.assertEqual(motif_count('CCCCCC','CCC'),4)
        self.assertEqual(motif_count('ACCTCCCT','CCTCCC'),1)

    def test_discovery_never_requests_confirmation_or_other_sheet(self):
        class Sheet:
            def iter_rows(inner,**kwargs):
                self.assertEqual(kwargs,dict(min_row=3,max_col=8,values_only=True))
                return iter([('WT',None,None,None,None,None,1.,'NA')])
        class Workbook:
            def __getitem__(inner,key):
                self.assertEqual(key,'NucLibC')
                return Sheet()
            def close(inner): pass
        with patch('src.research_20260921.sirloin_transfer.openpyxl.load_workbook',return_value=Workbook()):
            result=load_discovery()
            self.assertEqual(result['WT'][0],1.)
            self.assertNotEqual(result['WT'][1],result['WT'][1])


if __name__=='__main__': unittest.main()
