from .faraway_dna_audit import US, DS, barcode_record, reverse_complement, references, aligner, call_construct
import unittest


class DNAAuditTests(unittest.TestCase):
    def test_barcode_orientation_quality_and_concatemer_guard(self):
        barcode = 'ACGTCGATACGTTGACCTAG'
        s = 'GATTACA'+US+barcode+DS+'TTT'; q = 'I'*len(s)
        self.assertEqual(barcode_record(s,q)['barcode'],barcode)
        self.assertEqual(barcode_record(reverse_complement(s),q)['barcode'],barcode)
        self.assertIsNone(barcode_record(s,'!'*len(s)))
        self.assertIsNone(barcode_record(s+s,q+q))

    def test_existing_design_reference_recovered(self):
        refs,index = references()
        for ga,intron in [(1,0),(1,1),(0,0),(0,1)]:
            seq = ''.join(refs[(i,ga,intron)] for i in range(1,9))
            call,error = call_construct(seq,refs,index,aligner())
            self.assertIsNone(error)
            self.assertEqual(call['genotype'],str(ga)*8+str(intron)*8)

    def test_incomplete_reporter_is_rejected(self):
        refs,index = references();seq=''.join(refs[(i,1,0)] for i in range(2,9))
        call,error = call_construct(seq,refs,index,aligner())
        self.assertIsNone(call)
        self.assertIsNotNone(error)


if __name__ == '__main__': unittest.main()
