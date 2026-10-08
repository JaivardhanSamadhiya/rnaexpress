"""Invented direct-genome replay controls; preserve original pilot tests."""
from . import replay as r
from . import audit as a
from unittest.mock import patch
import unittest

class IndependentReplayTests(unittest.TestCase):
    def test_both_strand_orders_and_direct_reference(self):
        plus={'exonStarts':'100,108,','exonEnds':'106,112,','exonCount':2,'strand':'+','cdsStart':100,'cdsEnd':103}
        negative=plus|{'strand':'-','cdsStart':110,'cdsEnd':112}
        with patch.object(a,'transcript_utr',side_effect=AssertionError('Original reconstructor forbidden')):
            p=r.exon_coordinate_order(plus); m=r.exon_coordinate_order(negative)
            self.assertEqual(p,[103,104,105,108,109,110,111]); self.assertEqual(m,[109,108,105,104,103,102,101,100])
            self.assertEqual(r.direct_reference('AACCGGTTACGT',100,p,'+'),'CGGACGT')
            self.assertEqual(r.direct_reference('AACCGGTTACGT',100,m,'-'),'GTCCGGTT')

    def test_reference_bound_and_overlapping_exon_rejection(self):
        with self.assertRaises(AssertionError): r.direct_reference('ACGT',100,[99],'+')
        bad={'exonStarts':'100,102,','exonEnds':'104,106,','exonCount':2,'strand':'+','cdsStart':100,'cdsEnd':101}
        with self.assertRaises(AssertionError): r.exon_coordinate_order(bad)

    def test_noncoding_or_wrong_strand_not_assigned(self):
        noncoding={'exonStarts':'100,','exonEnds':'104,','exonCount':1,'strand':'+','cdsStart':100,'cdsEnd':100}
        with self.assertRaises(AssertionError): r.exon_coordinate_order(noncoding)
        with self.assertRaises(AssertionError): r.direct_reference('ACGT',100,[100],'unknown')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentReplayTests))
    if not result.wasSuccessful(): raise SystemExit(1)
    a.jsave(a.OUT/'independent_replay_synthetic_receipt.json',{'status':'PASS','tests':result.testsRun,
        'source_hashes':{p.name:a.sha(p) for p in (a.SRC/'replay.py',a.SRC/'test_replay.py')},
        'original_reconstructor_disabled_in_synthetic_test':True,'project_data_read':False,'remote_requests':0,'models_fit':0})
