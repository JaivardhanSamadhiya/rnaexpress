from .shukla_transfer import read_target,tied_regret,require_confirmation,family,HEADER
from .shukla_reference_admission import reference_candidate
import unittest,tempfile,gzip
from pathlib import Path
import numpy as np


class TransferTests(unittest.TestCase):
    def test_closed_counts_and_excluded_rows_are_not_parsed(self):
        row=['keep','2','4','8','SEALED','SEALED','SEALED','1','2','4','SEALED','SEALED','SEALED']
        excluded=['exclude']+['UNOPENED']*12
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'counts.gz'
            with gzip.open(path,'wt') as f:f.write('\t'.join(HEADER)+'\n'+'\t'.join(row)+'\n'+'\t'.join(excluded)+'\n')
            result,accessed=read_target(path,['keep'],(1,2,3))
        self.assertEqual(result,{'keep':[1.,1.,1.]});self.assertEqual(len(accessed),6)

    def test_ties_equal_random_and_perfect_order_has_zero_regret(self):
        y=np.arange(10,dtype=float)
        self.assertAlmostEqual(tied_regret(y,np.zeros(10)),.5)
        self.assertAlmostEqual(tied_regret(y,y),0.)
        self.assertAlmostEqual(tied_regret(y,-y),1.)

    def test_confirmation_gate_blocks_failure(self):
        with self.assertRaises(PermissionError):require_confirmation({'discovery_pass':False})
        require_confirmation({'discovery_pass':True})

    def test_reference_admission_does_not_truncate_other_bases(self):
        self.assertEqual(reference_candidate('CGTAAA',4),('CGTA','terminal_polyA_only_trim_to_metadata_length'))
        self.assertIsNone(reference_candidate('CGTACC',4)[0])
        self.assertIsNone(reference_candidate('CGT',4)[0])
        self.assertEqual(family('FIRRE(HG)'),family('FIRRE(MM)'))


if __name__=='__main__':unittest.main()
