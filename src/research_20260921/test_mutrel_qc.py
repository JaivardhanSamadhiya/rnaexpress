"""Synthetic orientation and quality checks for the bounded read inspection."""
import random,unittest
from .mutrel_read_qc import align

class ReadQCTests(unittest.TestCase):
    def test_reverse_mate_retains_reference_coordinate_variants(self):
        rng=random.Random(55);ref=''.join(rng.choice('ACGT') for _ in range(162))
        mutant=list(ref)
        for i in [30,70]:mutant[i]=next(b for b in 'ACGT' if b!=ref[i])
        mutant=''.join(mutant)
        a=align(mutant[:150],'I'*150,ref)
        b=align(mutant[12:].translate(str.maketrans('ACGT','TGCA'))[::-1],'I'*150,ref)
        shared=set(a)&set(b)
        self.assertEqual([i for i in sorted(shared) if a[i]!=ref[i] and b[i]!=ref[i]],[30,70])

    def test_low_quality_calls_are_excluded(self):
        rng=random.Random(55);ref=''.join(rng.choice('ACGT') for _ in range(162))
        quality='I'*30+'!'+'I'*119
        calls=align(ref[:150],quality,ref)
        self.assertNotIn(30,calls)
        self.assertIsNone(align('N'*150,'I'*150,ref))

if __name__=='__main__':unittest.main()
