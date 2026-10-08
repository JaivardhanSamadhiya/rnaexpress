"""Only invented JSON, toy metadata and mocked transports; zero network."""
from pathlib import Path
import ast,io,json,tempfile,unittest,urllib.error
from unittest.mock import patch
from . import common as c,parser,produce,replay,transport
Q={'chrom':'chr1','start0':10,'end0':12,'url':c.API+'/getData/track?genome=mm10;track=phyloP60wayAll,phastCons60way;chrom=chr1;start=10;end=12;maxItemsOutput=10000','key':'toy'}
E={t:{'trackType':'wig 0 1','dataTime':'2019-09-19T15:18:52','dataTimeStamp':1568931532} for t in c.TRACKS}
def payload(second_missing=False):
 o=[('downloadTime','2026:10:07T00:00:00Z'),('downloadTimeStamp',123),('genome','mm10')]
 count=0
 for t in c.TRACKS:
  o += [('dataTime',E[t]['dataTime']),('dataTimeStamp',E[t]['dataTimeStamp']),('trackType',E[t]['trackType']),('track',t),('chrom','chr1'),('start',10),('end',12)]
  values=[] if second_missing and t==c.TRACKS[1] else [{'chrom':'chr1','start':10,'end':12,'value':-.3 if t==c.TRACKS[0] else .3}]
  count+=len(values);o.append((t,values))
 o.append(('itemsReturned',count))
 return ('{'+','.join(json.dumps(k)+':'+json.dumps(v) for k,v in o)+'}').encode()
def schema_payload(physical=False,duplicate_type=False):
 cols=['chrom','chromStart','chromEnd','span','file','offset'] if physical else ['chrom','start','end','value']
 o={'genome':'mm10','track':'chr1_phyloP60wayAll' if physical else c.TRACKS[0],'dataTime':'2019-09-19T15:18:52','dataTimeStamp':1568931532,'columnTypes':[{'name':n,'jsonType':'string' if n=='chrom' else 'number'} for n in cols]}
 if not physical:o.update(type='wig 0 1',splitTable=True)
 b=json.dumps(o)
 if duplicate_type:b=b[:-1]+',"type":"wig 0 1"}'
 return b.encode()
class FakeResponse:
 def __init__(self,body,status=200,url=Q['url'],length=None):self.body=body;self.status=status;self.url=url;self.headers={} if length is None else {'Content-Length':str(length)}
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def read(self,n):return self.body[:n]
 def geturl(self):return self.url
class FakeOpener:
 def __init__(self,response=None,error=None):self.response=response;self.error=error;self.calls=0
 def open(self,*a,**kw):
  self.calls+=1
  if self.error:raise self.error
  return self.response
class NativeTests(unittest.TestCase):
 def test_duplicate_root_metadata_is_preserved(self):
  b=payload();o=parser.pairs(b);self.assertEqual(len(parser.occurrences(o,'track')),2)
  arrays,groups=parser.values(b,Q,E);self.assertEqual([g['track'] for g in groups],list(c.TRACKS));self.assertEqual(arrays[c.TRACKS[0]][10],-.3)
 def test_missing_or_reordered_group_rejected(self):
  b=payload()
  for altered in [b.replace(b'"dataTime":',b'"lostTime":',1),b.replace(json.dumps(c.TRACKS[0]).encode(),b'"wrong_track"',1)]:
   with self.assertRaises(parser.SchemaError):parser.values(altered,Q,E)
 def test_singleton_duplicate_rejected(self):
  b=payload().replace(b'"genome":"mm10"',b'"genome":"mm10","genome":"mm10"')
  with self.assertRaises(parser.SchemaError):parser.values(b,Q,E)
 def test_timestamp_and_type_bindings_exact(self):
  for b in [payload().replace(b'1568931532',b'1568931533',1),payload().replace(b'wig 0 1',b'wig 0 2',1)]:
   with self.assertRaises(parser.SchemaError):parser.values(b,Q,E)
 def test_source_timezone_is_not_invented(self):
  # Cached official metadata has an unqualified text time and stamp differing by7h from naive UTC.
  self.assertEqual(parser.schema(schema_payload(),c.TRACKS[0],expected_type='wig 0 1')['dataTimeStamp'],1568931532)
 def test_exact_schemas_and_equal_type_duplicates(self):
  self.assertEqual(parser.schema(schema_payload(duplicate_type=True),c.TRACKS[0],expected_type='wig 0 1')['trackType'],'wig 0 1')
  self.assertIsNone(parser.schema(schema_payload(physical=True),'chr1_phyloP60wayAll',physical=True)['trackType'])
  with self.assertRaises(parser.SchemaError):parser.schema(schema_payload(duplicate_type=True).replace(b',"type":"wig 0 1"}',b',"type":"wig 0 2"}'),c.TRACKS[0],expected_type='wig 0 1')
 def test_wrong_schema_scope_nonobject_and_physical_split_rejected(self):
  for b in [b'[]',schema_payload(physical=True).replace(b'"mm10"',b'"mm39"'),schema_payload(physical=True)[:-1]+b',"splitTable":true}']:
   with self.assertRaises(parser.SchemaError):parser.schema(b,'chr1_phyloP60wayAll',physical=True)
 def test_malformed_column_and_nonstr_type_are_unavailable(self):
  original=json.loads(schema_payload())
  for changed in ('missing_name','missing_jsonType','nonstr_type'):
   toy=json.loads(json.dumps(original))
   if changed=='nonstr_type':toy['type']=None
   else:toy['columnTypes'][0].pop('name' if changed=='missing_name' else 'jsonType')
   with self.assertRaises(parser.SchemaError):parser.schema(json.dumps(toy).encode(),c.TRACKS[0],expected_type='wig 0 1')
  physical=json.loads(schema_payload(physical=True));physical['columnTypes'][0]['name']=['chrom']
  with self.assertRaises(parser.SchemaError):parser.schema(json.dumps(physical).encode(),'chr1_phyloP60wayAll',physical=True)
 def test_physical_metadata_optional_table_binding(self):
  toy=json.loads(schema_payload(physical=True));toy['table']='chr1_phyloP60wayAll'
  self.assertEqual(parser.schema(json.dumps(toy).encode(),'chr1_phyloP60wayAll',physical=True)['source_table'],'chr1_phyloP60wayAll')
  for replacement in ('chr2_phyloP60wayAll',None,{},123):
   toy['table']=replacement
   with self.assertRaises(parser.SchemaError):parser.schema(json.dumps(toy).encode(),'chr1_phyloP60wayAll',physical=True)
 def test_nonfinite_boolean_and_outside_phastcons_rejected(self):
  for val in [b'NaN',b'true',b'2']:
   b=payload().replace(b'"value": 0.3',b'"value": '+val)
   with self.assertRaises(parser.SchemaError):parser.values(b,Q,E)
 def test_overhang_overlap_and_nested_duplicate_rejected(self):
  b=payload();needle=json.dumps({'chrom':'chr1','start':10,'end':12,'value':-.3}).encode()
  for altered in [b.replace(b'"start": 10',b'"start": 9',1),b.replace(needle,needle+b','+needle),b.replace(b'"value": -0.3',b'"value": -0.3,"value": -0.3',1)]:
   with self.assertRaises(parser.SchemaError):parser.values(altered,Q,E)
 def test_empty_track_is_missing_not_zero(self):
  arrays,_=parser.values(payload(True),Q,E);self.assertEqual(arrays[c.TRACKS[1]],{})
 def test_direct_independent_join_equals_validated_values(self):
  arrays,_=parser.values(payload(),Q,E);direct=replay.direct_scores(payload(),Q)
  for t in c.TRACKS:
   for pos in (10,11):self.assertEqual(direct['chr1',pos,t],arrays[t][pos])
 def test_parent_complete_across_cells_and_menus(self):
  rows=[]
  for i,(cell,pos) in enumerate([('CAD',10),('N2A',11)]):
   rows.append({'dataset':'toy','parent_id':'parent','parent_context_id':cell+'|parent','intervention_id':str(i),'mapping_status':c.MAPPED,'edit_positions0':[0],'edited_site_coordinates':[{'chrom':'chr1','genomic_position0':pos}]})
  values={('chr1',10):{'scores':dict.fromkeys(c.TRACKS,.2)},('chr1',11):{'scores':{c.TRACKS[0]:.2,c.TRACKS[1]:None}}}
  got=produce.parent_availability(rows,values)[0];self.assertFalse(got['native_annotation_complete_parent']);self.assertTrue(got['all_native_covariates_unavailable_for_entire_parent']);self.assertEqual(got['original_rows'],2)
  values['chr1',11]['scores'][c.TRACKS[1]]=.2;self.assertTrue(produce.parent_availability(rows,values)[0]['native_annotation_complete_parent'])
  rows[1]['mapping_status']='unresolved';rows[1]['edited_site_coordinates']=[];self.assertFalse(produce.parent_availability(rows,values)[0]['native_annotation_complete_parent'])
 def test_http0_missing_cache_never_retries(self):
  with tempfile.TemporaryDirectory(prefix='native_mock_',dir=c.OUT) as tmp:
   d=Path(tmp).resolve();assert d.is_relative_to(c.OUT.resolve())
   with patch.object(c,'ART',d):
    op=FakeOpener(error=urllib.error.URLError('invented lost transport'));client=transport.Client([Q['url']],opener=op,sleep=lambda x:None,total_used=0);p=d/'lost.json'
    self.assertIsNone(client.get(Q['url'],p)[0]);self.assertIsNone(client.get(Q['url'],p)[0]);self.assertEqual(op.calls,1);self.assertFalse(p.exists())
 def test_receipt_and_body_corruption_or_orphan_stop(self):
  with tempfile.TemporaryDirectory(prefix='native_mock_',dir=c.OUT) as tmp:
   d=Path(tmp).resolve();assert d.is_relative_to(c.OUT.resolve())
   with patch.object(c,'ART',d):
    p=d/'body.json';client=transport.Client([Q['url']],opener=FakeOpener(FakeResponse(b'{}')),sleep=lambda x:None,total_used=0);client.get(Q['url'],p)
    p.write_bytes(b'{ }')
    with self.assertRaises(AssertionError):transport.cached(p,Q['url'])
    p.write_bytes(b'{}');r=p.with_name(p.name+'.receipt.json');original=r.read_bytes();r.write_bytes(original+b' ')
    with self.assertRaises(AssertionError):transport.cached(p,Q['url'])
    orphan=d/'orphan.json';orphan.write_bytes(b'{}')
    with self.assertRaises(AssertionError):transport.cached(orphan,Q['url'])
 def test_http206_preserved_and_rejected(self):
  with tempfile.TemporaryDirectory(prefix='native_mock_',dir=c.OUT) as tmp:
   d=Path(tmp).resolve();assert d.is_relative_to(c.OUT.resolve())
   with patch.object(c,'ART',d):
    p=d/'partial.json';client=transport.Client([Q['url']],opener=FakeOpener(FakeResponse(b'{}',status=206)),sleep=lambda x:None,total_used=0);body,r=client.get(Q['url'],p)
    self.assertIsNone(body);self.assertEqual(r['http_status'],206);self.assertEqual(p.read_bytes(),b'{}');self.assertIsNone(client.get(Q['url'],p)[0])
 def test_cap_overflow_and_total_budget_stop(self):
  with tempfile.TemporaryDirectory(prefix='native_mock_',dir=c.OUT) as tmp:
   d=Path(tmp).resolve();assert d.is_relative_to(c.OUT.resolve())
   with patch.object(c,'ART',d),patch.object(c,'MAX_RESPONSE',4):
    p=d/'large.json';op=FakeOpener(FakeResponse(b'123456'));client=transport.Client([Q['url']],opener=op,sleep=lambda x:None,total_used=0);body,r=client.get(Q['url'],p)
    self.assertIsNone(body);self.assertFalse(p.exists());self.assertEqual((d/'large.json.oversize_prefix.bin').read_bytes(),b'1234');self.assertEqual(r['acquired_bytes'],5)
    capclient=transport.Client([Q['url']],opener=op,sleep=lambda x:None,total_used=c.MAX_TOTAL)
    with self.assertRaises(transport.BudgetExceeded):capclient.get(Q['url'],d/'unattempted.json')
 def test_wrong_redirect_url_rejected_before_body(self):
  with self.assertRaises(urllib.error.URLError):transport.ExactRedirect().redirect_request(urllib.request.Request(Q['url']),None,302,'',{},'https://evil.example/query')
  with tempfile.TemporaryDirectory(prefix='native_mock_',dir=c.OUT) as tmp:
   d=Path(tmp).resolve();assert d.is_relative_to(c.OUT.resolve())
   with patch.object(c,'ART',d):
    op=FakeOpener(FakeResponse(b'{}',url=c.API+'/getData/track?genome=mm39'));client=transport.Client([Q['url']],opener=op,sleep=lambda x:None,total_used=0)
    body,r=client.get(Q['url'],d/'changed.json');self.assertIsNone(body);self.assertEqual(r['failure'],'untrusted_or_changed_final_url')
 def test_birth_binder_rejects_missing_extra_and_mutated_receipts(self):
  with self.assertRaises(AssertionError):replay.birth_bind([], [Q])
  with self.assertRaises(AssertionError):replay.birth_bind([{'key':'extra'}], [])
  with tempfile.TemporaryDirectory(prefix='native_mock_',dir=c.OUT) as tmp:
   d=Path(tmp).resolve();assert d.is_relative_to(c.OUT.resolve())
   with patch.object(c,'ART',d):
    p=d/'values'/'toy.json';op=FakeOpener(FakeResponse(b'{}'));client=transport.Client([Q['url']],opener=op,sleep=lambda x:None,total_used=0);_,rr=client.get(Q['url'],p)
    receipt=p.with_name(p.name+'.receipt.json');birth=receipt.with_name(receipt.name+'.sha256.json')
    record={'key':'toy','url':Q['url'],'queried':True,'response_receipt':receipt.relative_to(c.ROOT).as_posix(),'response_receipt_sha256':c.sha(receipt),'response_receipt_birth_sha256':c.sha(birth),'body_path':p.relative_to(c.ROOT).as_posix(),'body_sha256':c.sha(p)}
    replay.birth_bind([record],[Q]);receipt.write_bytes(receipt.read_bytes()+b' ')
    with self.assertRaises(AssertionError):replay.birth_bind([record],[Q])
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeTests));assert result.wasSuccessful()
 sources=sorted(c.SRC.glob('*.py'))
 for p in sources:ast.parse(p.read_text())
 c.jsave(c.OUT/'synthetic_tests_receipt_v3.json',{'status':'PASS_SCOPED_INVENTED_AND_MOCK_TESTS_ONLY','tests':result.testsRun,'network_calls':0,'project_values_read':False,'outcomes_read':False,'models_fit':0,'prior_test_receipts':{name:c.sha(c.OUT/name) for name in ('synthetic_tests_receipt.json','synthetic_tests_receipt_v2.json')},'source_files':{p.relative_to(c.ROOT).as_posix():c.sha(p) for p in sources}})
