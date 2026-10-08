"""Invented source-header/parser/transport checks; no network or project values."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from . import pilot, transport
from src.generalization_conservation_native_20261007 import parser

TYPES = {'phyloP60wayAll': 'wig -20 7.532', 'phastCons60way': 'wig 0 1'}
QUERY = {'chrom': 'chr1', 'start0': 10, 'end0': 11}


def body(empty=False):
    pairs = [('genome', 'mm10')]
    for index, track in enumerate(pilot.TRACKS):
        pairs += [('dataTime', '2014-04-18T13:59:54'), ('dataTimeStamp', 1397854794 + index),
            ('trackType', TYPES[track]), ('track', track), ('chrom', 'chr1'), ('start', 10), ('end', 11),
            (track, [] if empty else [{'chrom': 'chr1', 'start': 10, 'end': 11, 'value': .25}])]
    if not empty: pairs.append(('itemsReturned', 2))
    return ('{' + ','.join(json.dumps(k) + ':' + json.dumps(v) for k, v in pairs) + '}').encode()


def schema():
    return json.dumps({'genome': 'mm10', 'track': 'phyloP60wayAll', 'type': TYPES['phyloP60wayAll'],
        'dataTime': '2014-04-18T13:59:54', 'dataTimeStamp': 1397854794,
        'columnTypes': [{'name': n, 'jsonType': t} for n, t in zip(['chrom', 'start', 'end', 'value'], ['string', 'number', 'number', 'number'])]}).encode()


class ParseTests(unittest.TestCase):
    def test_ordered_headers_and_arrays(self):
        headers, arrays, groups = pilot.observed(body(), QUERY, TYPES)
        self.assertEqual(list(headers), list(pilot.TRACKS))
        self.assertEqual(arrays['phastCons60way'], {10: .25})
        self.assertEqual(len(groups), 2)

    def test_empty_arrays_do_not_choose_another_pilot(self):
        headers, arrays, groups = pilot.observed(body(True), QUERY, TYPES)
        self.assertTrue(headers)
        self.assertEqual(arrays, {t: {} for t in pilot.TRACKS})

    def test_missing_split_table_is_explicitly_not_claimed(self):
        value = pilot.logical_schema(schema(), 'phyloP60wayAll', TYPES['phyloP60wayAll'])
        self.assertFalse(value['physical_SQL_storage_certified'])

    def test_wrong_logical_type_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.logical_schema(schema(), 'phyloP60wayAll', 'bigWig')

    def test_wrong_logical_column_rejected(self):
        value = schema().replace(b'"value"', b'"score"')
        with self.assertRaises(parser.SchemaError): pilot.logical_schema(value, 'phyloP60wayAll', TYPES['phyloP60wayAll'])

    def test_wrong_interval_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body(), {**QUERY, 'end0': 12}, TYPES)

    def test_wrong_assembly_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body().replace(b'mm10', b'mm39'), QUERY, TYPES)

    def test_changed_type_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body().replace(b'wig 0 1', b'wig 0 2'), QUERY, TYPES)

    def test_misordered_source_group_rejected(self):
        value = body().replace(b'"trackType":"wig -20 7.532","track":"phyloP60wayAll"', b'"track":"phyloP60wayAll","trackType":"wig -20 7.532"')
        self.assertNotEqual(value, body())
        with self.assertRaises(parser.SchemaError): pilot.observed(value, QUERY, TYPES)

    def test_invalid_calendar_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body().replace(b'2014-04-18', b'2014-02-30'), QUERY, TYPES)

    def test_invalid_timestamp_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body().replace(b'1397854794', b'-1'), QUERY, TYPES)

    def test_exact_item_count_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body().replace(b'"itemsReturned":2', b'"itemsReturned":3'), QUERY, TYPES)

    def test_truncation_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body()[:-1] + b',"maxItemsLimit":true}', QUERY, TYPES)

    def test_out_of_range_phastcons_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body().replace(b'0.25', b'1.25'), QUERY, TYPES)

    def test_nonfinite_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body().replace(b'0.25', b'NaN'), QUERY, TYPES)

    def test_duplicate_singleton_rejected(self):
        with self.assertRaises(parser.SchemaError): pilot.observed(body()[:-1] + b',"genome":"mm10"}', QUERY, TYPES)

    def test_later_header_drift_rejected_by_unchanged_parser(self):
        headers, _, _ = pilot.observed(body(), QUERY, TYPES)
        with self.assertRaises(parser.SchemaError): parser.values(body().replace(b'1397854794', b'1397854795'), QUERY, headers)


class Response(io.BytesIO):
    def __init__(self, data, url, status=200, headers=None):
        super().__init__(data); self.url=url; self.status=status; self.headers={} if headers is None else headers
    def geturl(self): return self.url


class Opener:
    def __init__(self, url, data, status=200, headers=None):
        self.url,self.data,self.status,self.headers=url,data,status,headers;self.calls=0
    def open(self, request, timeout):
        self.calls+=1
        assert timeout==45
        return Response(self.data,self.url,self.status,self.headers)


class TransportTests(unittest.TestCase):
    def execute(self, action):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            urls=['https://api.genome.ucsc.edu/getData/track?genome=mm10;start='+str(i) for i in range(20)]
            with patch.object(pilot,'ART',root),patch.object(transport,'ART',root):
                action(root,urls)

    def test_complete_body_and_birth_receipt_reused_without_network(self):
        def run(root,urls):
            opener=Opener(urls[0],b'complete')
            client=transport.Client(urls,123,opener=opener,sleep=lambda _:None)
            a,r=client.get(urls[0],root/'body.json');b,r2=client.get(urls[0],root/'body.json')
            self.assertEqual(a,b);self.assertEqual(opener.calls,1);self.assertEqual(client.total,131)
            self.assertTrue((root/'body.json.receipt.json.sha256.json').exists())
        self.execute(run)

    def test_non200_is_preserved_but_unavailable(self):
        def run(root,urls):
            client=transport.Client(urls,0,opener=Opener(urls[0],b'partial',206),sleep=lambda _:None)
            data,receipt=client.get(urls[0],root/'body.json')
            self.assertIsNone(data);self.assertEqual(receipt['http_status'],206);self.assertTrue((root/'body.json').exists())
        self.execute(run)

    def test_changed_final_url_is_unavailable(self):
        def run(root,urls):
            client=transport.Client(urls,0,opener=Opener('https://untrusted.example/',b'unread'),sleep=lambda _:None)
            data,receipt=client.get(urls[0],root/'body.json')
            self.assertIsNone(data);self.assertIsNone(receipt['sha256']);self.assertFalse((root/'body.json').exists())
        self.execute(run)

    def test_declared_oversize_not_read(self):
        def run(root,urls):
            client=transport.Client(urls,0,opener=Opener(urls[0],b'unread',headers={'Content-Length':'4000001'}),sleep=lambda _:None)
            _,receipt=client.get(urls[0],root/'body.json')
            self.assertEqual(receipt['acquired_bytes'],0);self.assertIsNone(receipt['sha256'])
        self.execute(run)

    def test_changed_cache_receipt_rejected(self):
        def run(root,urls):
            client=transport.Client(urls,0,opener=Opener(urls[0],b'complete'),sleep=lambda _:None)
            client.get(urls[0],root/'body.json')
            (root/'body.json.receipt.json').write_bytes(b'{}')
            with self.assertRaises(AssertionError):client.get(urls[0],root/'body.json')
        self.execute(run)

    def test_unfrozen_url_rejected(self):
        def run(root,urls):
            client=transport.Client(urls,0,opener=Opener(urls[0],b'complete'),sleep=lambda _:None)
            with self.assertRaises(AssertionError):client.get(urls[0]+'x',root/'body.json')
        self.execute(run)


if __name__ == '__main__':
    unittest.main()
