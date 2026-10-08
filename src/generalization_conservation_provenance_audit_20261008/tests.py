"""Invented dual-track JSON responses only; no project data or requests."""
import json
import unittest
from .audit import reconstruct
from src.generalization_conservation_native_20261007.common import TRACKS

Q={'chrom':'chrInvented','start0':4,'end0':6,'key':'fixed_query'}
H={t:{'dataTime':'2014-01-01T01:01:01','dataTimeStamp':1234,'trackType':'wig fixed'} for t in TRACKS}


def payload(empty=False,drift=False,zero=False):
    pairs=[('genome','mm10')];count=0
    for index,t in enumerate(TRACKS):
        m=H[t].copy()
        if drift and index==0:m['dataTimeStamp']=9999
        pairs.extend([(k,m[k]) for k in ('dataTime','dataTimeStamp','trackType')])
        pairs.extend([('track',t),('chrom',Q['chrom']),('start',Q['start0']),('end',Q['end0'])])
        rows=[] if empty else [{'chrom':Q['chrom'],'start':4,'end':5,'value':0. if zero else .5}]
        count+=len(rows);pairs.append((t,rows))
    pairs.append(('itemsReturned',count))
    return ('{'+','.join(json.dumps(k)+':'+json.dumps(v) for k,v in pairs)+'}').encode()


class MissingReasonContracts(unittest.TestCase):
    def test_query_bindings_and_interval_missing(self):
        s,g,r,v=reconstruct(payload(),{'http_status':200},Q,H)
        self.assertEqual(s,'ADMITTED_EXACT_ORDERED_DUAL_TRACK_RESPONSE')
        self.assertEqual(v['chrInvented',4]['query_key'],'fixed_query')
        self.assertIsNone(v['chrInvented',4]['missing_reason'])
        self.assertEqual(v['chrInvented',5]['missing_reason'],'source_score_absent')
    def test_real_zero_available(self):
        _,_,_,v=reconstruct(payload(zero=True),{'http_status':200},Q,H)
        self.assertEqual(v['chrInvented',4]['scores'],dict.fromkeys(TRACKS,0.))
        self.assertIsNone(v['chrInvented',4]['missing_reason'])
    def test_empty_arrays_are_missing_values_not_bad_headers(self):
        s,g,_,v=reconstruct(payload(empty=True),{'http_status':200},Q,H)
        self.assertEqual(s,'ADMITTED_EXACT_ORDERED_DUAL_TRACK_RESPONSE');self.assertEqual(len(g),2)
        self.assertTrue(all(x['missing_reason']=='source_score_absent' for x in v.values()))
    def test_header_drift_preserves_failure(self):
        s,g,r,v=reconstruct(payload(drift=True),{'http_status':200},Q,H)
        self.assertEqual(s,'UNAVAILABLE_VALUE_RESPONSE');self.assertIsNone(g)
        self.assertIn('Pinned chromosome source metadata changed',r)
        self.assertTrue(all(x['missing_reason']==r and set(x['scores'].values())=={None} for x in v.values()))
    def test_non200_cannot_admit_body(self):
        s,g,r,v=reconstruct(payload(),{'http_status':403,'failure':'HTTP status is not complete 200'},Q,H)
        self.assertEqual(s,'UNAVAILABLE_VALUE_RESPONSE');self.assertIsNone(g)
        self.assertEqual(r,'HTTP status is not complete 200')
    def test_transport_failure_cannot_admit_body(self):
        s,g,r,v=reconstruct(payload(),{'http_status':200,'failure':'Changed or untrusted URL'},Q,H)
        self.assertEqual(s,'UNAVAILABLE_VALUE_RESPONSE');self.assertIsNone(g)
        self.assertEqual(r,'Changed or untrusted URL')
    def test_invalid_json_bound_as_unavailable(self):
        s,g,r,v=reconstruct(b'{broken',{'http_status':200},Q,H)
        self.assertEqual(s,'UNAVAILABLE_VALUE_RESPONSE');self.assertIn('Invalid JSON',r)
    def test_absent_body_default_reason(self):
        s,g,r,v=reconstruct(None,{'http_status':0},Q,H)
        self.assertEqual(r,'Missing complete public body')
        self.assertTrue(all(x['missing_reason']==r for x in v.values()))


if __name__=='__main__':unittest.main()
