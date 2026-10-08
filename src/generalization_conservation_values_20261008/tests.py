"""Invented missingness, source-drift and immutable transport tests."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from src.generalization_conservation_header_pilot_20261008.tests import body, QUERY, TYPES, Opener
from src.generalization_conservation_header_pilot_20261008.pilot import observed
from src.generalization_conservation_native_20261007 import parser
from src.generalization_conservation_native_20261007.produce import parent_availability
from . import common as c, transport
from .produce import add_interval
from .replay import direct_scores, parent_status


class PolicyTests(unittest.TestCase):
    def row(self, identifier, cell, pos, mapped=True):
        return {'dataset':'invented','parent_id':'parent','intervention_id':identifier,'parent_context_id':cell,
            'mapping_status':c.old.MAPPED if mapped else 'unmapped','edit_positions0':[pos],
            'edited_site_coordinates':[{'chrom':'chr1','genomic_position0':pos}] if mapped else []}

    def test_independent_scalar_joins_match_expansion(self):
        _,arrays,_=observed(body(),QUERY,TYPES);values={}
        add_interval(values,{**QUERY,'key':'invented'},arrays,'none')
        direct=direct_scores(body(),QUERY)
        for track in c.old.TRACKS:self.assertEqual(values['chr1',10]['scores'][track],direct['chr1',10,track])

    def test_missing_is_none_not_zero(self):
        values={};add_interval(values,{**QUERY,'key':'invented'},None,'failed')
        self.assertEqual(values['chr1',10]['scores'],{t:None for t in c.old.TRACKS})

    def test_zero_score_is_available(self):
        values={};add_interval(values,{**QUERY,'key':'invented'},{t:{10:0.0} for t in c.old.TRACKS},'none')
        self.assertIsNone(values['chr1',10]['missing_reason'])

    def test_duplicate_coordinate_rejected(self):
        values={};q={**QUERY,'key':'invented'};add_interval(values,q,None,'failed')
        with self.assertRaises(AssertionError):add_interval(values,q,None,'failed')

    def test_candidate_in_other_cell_vetoes_entire_parent(self):
        rows=[self.row('one','CAD',10),self.row('two','N2A',11)]
        values={('chr1',10):{'scores':{t:.5 for t in c.old.TRACKS}},('chr1',11):{'scores':{'phyloP60wayAll':.5,'phastCons60way':None}}}
        produced=parent_availability(rows,values)[0]
        flat={(chrom,pos,track):value['scores'][track] for (chrom,pos),value in values.items() for track in c.old.TRACKS}
        check=parent_status(rows,flat)
        self.assertFalse(produced['native_annotation_complete_parent']);self.assertEqual(produced['original_rows'],2)
        self.assertEqual(produced['original_menus'],['CAD','N2A'])
        for key,value in check.items():self.assertEqual(produced[key],value)

    def test_missing_coordinate_vetoes_parent(self):
        rows=[self.row('one','CAD',10,False)]
        self.assertFalse(parent_status(rows,{})['native_annotation_complete_parent'])

    def test_source_header_drift_never_updates_reference(self):
        headers,_,_=observed(body(),QUERY,TYPES);before={t:dict(h) for t,h in headers.items()}
        with self.assertRaises(parser.SchemaError):parser.values(body().replace(b'1397854794',b'1397854795'),QUERY,headers)
        self.assertEqual(headers,before)

    def test_empty_pilot_means_missing_site(self):
        headers,arrays,_=observed(body(True),QUERY,TYPES);values={}
        add_interval(values,{**QUERY,'key':'invented'},arrays,'none')
        self.assertTrue(headers);self.assertEqual(values['chr1',10]['missing_reason'],'source_score_absent')


class TransportTests(unittest.TestCase):
    def execute(self,action):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);urls=['https://api.genome.ucsc.edu/getData/track?genome=mm10;start='+str(i) for i in range(2983)]
            with patch.object(c,'ART',root):action(root,urls)

    def test_birth_bound_complete_cache_has_no_retry(self):
        def run(root,urls):
            opener=Opener(urls[0],b'complete');client=transport.Client(urls,34217,opener=opener,sleep=lambda _:None)
            a,_=client.get(urls[0],root/'body.json');b,_=client.get(urls[0],root/'body.json')
            self.assertEqual(a,b);self.assertEqual(opener.calls,1);self.assertEqual(client.total,34225)
        self.execute(run)

    def test_non200_preserved_unavailable(self):
        def run(root,urls):
            client=transport.Client(urls,34217,opener=Opener(urls[0],b'partial',206),sleep=lambda _:None)
            body,record=client.get(urls[0],root/'body.json');self.assertIsNone(body);self.assertEqual(record['http_status'],206)
        self.execute(run)

    def test_changed_receipt_rejected(self):
        def run(root,urls):
            client=transport.Client(urls,34217,opener=Opener(urls[0],b'complete'),sleep=lambda _:None)
            client.get(urls[0],root/'body.json');(root/'body.json.receipt.json').write_bytes(b'{}')
            with self.assertRaises(AssertionError):client.get(urls[0],root/'body.json')
        self.execute(run)

    def test_unfrozen_request_rejected(self):
        def run(root,urls):
            client=transport.Client(urls,34217,opener=Opener(urls[0],b'complete'),sleep=lambda _:None)
            with self.assertRaises(AssertionError):client.get(urls[0]+'different',root/'body.json')
        self.execute(run)

    def test_exhausted_budget_refuses_network(self):
        def run(root,urls):
            opener=Opener(urls[0],b'complete');client=transport.Client(urls,c.old.MAX_TOTAL,opener=opener,sleep=lambda _:None)
            with self.assertRaises(AssertionError):client.get(urls[0],root/'body.json')
            self.assertEqual(opener.calls,0)
        self.execute(run)


if __name__ == '__main__':
    unittest.main()
