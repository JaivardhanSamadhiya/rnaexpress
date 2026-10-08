"""Invented reference metadata only; no biological data or remote requests."""
from . import audit as a
from pathlib import Path
import unittest

class CoordinateTests(unittest.TestCase):
    def test_overlapping_exact_occurrences(self):
        self.assertEqual(a.occurrences('AAAAA','AAA'),[0,1,2])
        self.assertEqual(a.occurrences('ACGT','TT'),[])

    def test_plus_strand_multiexon_utr_positions(self):
        row={'exonStarts':'100,108,','exonEnds':'106,112,','exonCount':2,'strand':'+','cdsStart':100,'cdsEnd':103}
        sequence,positions=a.transcript_utr(row,'AACCGGTTACGT',100)
        self.assertEqual(sequence,'CGGACGT'); self.assertEqual(positions,[103,104,105,108,109,110,111])
        self.assertEqual(a.occurrences(sequence,'GAC'),[2])
        self.assertEqual(positions[2:5],[105,108,109])

    def test_minus_strand_complement_and_exon_order(self):
        row={'exonStarts':'100,108,','exonEnds':'106,112,','exonCount':2,'strand':'-','cdsStart':110,'cdsEnd':112}
        sequence,positions=a.transcript_utr(row,'AACCGGTTACGT',100)
        self.assertEqual(sequence,'GTCCGGTT'); self.assertEqual(positions,[109,108,105,104,103,102,101,100])
        for base,position in zip(sequence,positions):
            self.assertEqual(a.reverse_complement(base),'AACCGGTTACGT'[position-100])

    def test_same_coordinate_multiple_isoform_collapse(self):
        x={'chrom':'chr1','strand':'+','positions0':[4,5,9]}
        self.assertEqual(a.unique_vector([x,x|{'transcript':'other'}]),'reference_site_vector_unique')
        self.assertEqual(a.unique_vector([x,x|{'positions0':[4,5,10]}]),'ambiguous_reference_site_vectors')
        self.assertEqual(a.unique_vector([]),'no_exact_reference_vector')

    def test_orientation_is_part_of_certificate(self):
        x={'chrom':'chr1','strand':'+','positions0':[4,5,6]}
        self.assertEqual(a.unique_vector([x,x|{'strand':'-'}]),'ambiguous_reference_site_vectors')

    def test_noncoding_has_no_certified_coding_utr(self):
        row={'exonStarts':'100,','exonEnds':'104,','exonCount':1,'strand':'+','cdsStart':100,'cdsEnd':100}
        self.assertEqual(a.transcript_utr(row,'ACGT',100),(None,None))

    def test_fixed_region_does_not_silently_extend(self):
        row={'exonStarts':'99,','exonEnds':'105,','exonCount':1,'strand':'+','cdsStart':99,'cdsEnd':100}
        with self.assertRaises(AssertionError): a.transcript_utr(row,'ACGT',100)

    def test_gene_offsets_are_not_genomic_vector(self):
        x={'chrom':'chr1','strand':'+','positions0':[1,2,9]}
        self.assertNotEqual(x['positions0'],list(range(1,4)))
        self.assertEqual(a.unique_vector([x]),'reference_site_vector_unique')

def run():
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(CoordinateTests))
    if not result.wasSuccessful(): raise SystemExit(1)
    a.jsave(a.OUT/'synthetic_tests_receipt.json',{'status':'PASS','tests':result.testsRun,
        'source_hashes':{p.name:a.sha(p) for p in sorted(a.SRC.glob('*.py'))},
        'outcomes_read':False,'project_metadata_read':False,'remote_requests':0,'models_fit':0,
        'scope':'Exact overlapping occurrences, plus/minus spliced coordinate vectors, isoform-coordinate ambiguity, no-code UTR and fixed boundary rejection'})

if __name__=='__main__': run()
