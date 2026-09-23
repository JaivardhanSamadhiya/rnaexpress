import gzip
import unittest
from .seers_dna_qc import decode_prefix, records, insert, LEFT, RIGHT


class PrefixTests(unittest.TestCase):
    def test_concatenated_members(self):
        data = gzip.compress(b'first') + gzip.compress(b'second')
        self.assertEqual(decode_prefix(data), (b'firstsecond', 2, True))

    def test_truncated_last_member(self):
        data = gzip.compress(b'first') + gzip.compress(b'second')[:-4]
        self.assertEqual(decode_prefix(data), (b'firstsecond', 2, False))

    def test_partial_record_excluded(self):
        value = b'@a\nAC\n+\nII\n@b\nAC\n+\nI'
        self.assertEqual(len(records(gzip.compress(value))[0]), 1)

    def test_reverse_and_quality(self):
        value = LEFT + 'A'*45 + RIGHT
        reverse = value.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
        self.assertEqual(insert(reverse, 'I'*len(value), True), 'A'*45)
        self.assertIsNone(insert(value, '!'*len(value)))

    def test_corruption_rejected(self):
        data = bytearray(gzip.compress(b'first'))
        data[-8] ^= 1
        with self.assertRaises(Exception):
            decode_prefix(bytes(data))
