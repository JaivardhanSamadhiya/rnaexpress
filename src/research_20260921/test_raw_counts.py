"""Synthetic paired-end, strand, quality and malformed-file checks."""
import gzip
from pathlib import Path
import tempfile
import unittest
from .raw_counts import count_pair, extract, reverse_complement


def insert(kmer):
    return b'ATCACTAAGC' + kmer + b'ATCATAATCA'


class RawTests(unittest.TestCase):
    def test_strand_normalization(self):
        seq = insert(b'CGAAGG')
        self.assertEqual(extract(seq, b'I'*len(seq)), b'CGAAGG')
        rev = reverse_complement(seq)
        self.assertEqual(extract(rev, b'I'*len(seq)), b'CGAAGG')

    def test_quality_flanks_length_and_ambiguity(self):
        seq = insert(b'CGAAGG')
        self.assertIsNone(extract(seq, b'I'*10+b'!'+b'I'*15))
        self.assertIsNone(extract(insert(b'CGANGG'), b'I'*26))
        self.assertIsNone(extract(insert(b'CGAGG'), b'I'*25))
        self.assertIsNone(extract(seq+seq, b'I'*52))
        self.assertIsNone(extract(b'T'+seq[1:], b'I'*26))

    def test_fragment_once_discordance_and_pair_id_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory)/'1.gz', Path(directory)/'2.gz']
            def write(path, seqs, names):
                with gzip.open(path, 'wb') as f:
                    for name, seq in zip(names, seqs):
                        f.write(b'@'+name+b'\n'+seq+b'\n+\n'+b'I'*len(seq)+b'\n')
            first = [insert(b'CGAAGG'), b'AAAA', insert(b'CGAAGG')]
            second = [reverse_complement(insert(b'CGAAGG')), insert(b'AAAAAA'), insert(b'CCCCCC')]
            write(paths[0], first, [b'a',b'b',b'c'])
            write(paths[1], second, [b'a',b'b',b'c'])
            counts, qc = count_pair(*paths)
            self.assertEqual(dict(counts), {'CGAAGG':1,'AAAAAA':1})
            self.assertEqual(qc['both_agree'], 1)
            self.assertEqual(qc['discordant'], 1)
            self.assertEqual(qc['accepted'], 2)
            write(paths[1], second, [b'a',b'b',b'wrong'])
            with self.assertRaises(ValueError):
                count_pair(*paths)


if __name__ == '__main__':
    unittest.main()
