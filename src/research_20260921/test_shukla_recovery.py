from .shukla_sequence_recovery import prefix_records,consensus,assemble,rc
import unittest,zlib
import numpy as np


class RecoveryTests(unittest.TestCase):
    def test_partial_final_quality_is_not_a_record(self):
        payload=b'@one\nACGT\n+\nIIII\n@two\nACGT\n+\nII'
        c=zlib.compressobj(wbits=31);compressed=c.compress(payload)+c.flush()
        self.assertEqual(list(prefix_records(compressed)),[('ACGT','IIII')])

    def test_quality_support_and_disagreement(self):
        counts=np.array([[4,0,0,0],[5,0,0,0],[18,2,0,0],[19,1,0,0]])
        self.assertEqual(consensus(counts).tolist(),[-1,0,-1,0])

    def test_overlap_does_not_fill_unknowns_or_hide_conflicts(self):
        calls=np.zeros((2,90),dtype=np.int8);calls[1,0]=1
        seq,conflicts=assemble(calls,[(0,0),(1,10)],120)
        self.assertTrue((seq[:20]==-1).all())
        self.assertEqual(seq[30],-1)
        self.assertEqual(conflicts,1)
        self.assertEqual(seq[29],0)

    def test_raw_barcode_and_insert_orientation(self):
        barcode='ACGTACGGTT';insert='A'*20+'C'*90
        read=rc(barcode)+rc(insert[20:])
        self.assertEqual(rc(read[:10]),barcode)
        self.assertEqual(rc(read[10:]),insert[20:])


if __name__=='__main__':unittest.main()
