"""Root-authorized schema-only stage; never requests annotation values."""
import argparse
from . import common as c,parser,transport
def run(root_start=False):
 assert root_start,'Root must explicitly start frozen schema-only queries'
 c.certify(c.SCHEMA_DESIGN)
 roster=c.read(c.OUT/'schema_query_roster.json');spec=c.read(c.OUT/'extraction_spec.json')
 client=transport.Client(q['url'] for q in roster);records=[];logical={};physical={}
 for q in roster:
  p=c.ART/'schema'/('mm10_'+q['key']+'.json');body,response=client.get(q['url'],p)
  record={**q,'response_receipt':p.with_name(p.name+'.receipt.json').relative_to(c.ROOT).as_posix(),'response_receipt_sha256':c.sha(p.with_name(p.name+'.receipt.json')),'response_receipt_birth_sha256':c.sha(p.with_name(p.name+'.receipt.json.sha256.json')),'body_path':p.relative_to(c.ROOT).as_posix() if response['sha256'] else None,'body_sha256':response['sha256'],'available':False}
  if body is not None:
   try:
    record['metadata']=parser.schema(body,q['track'],q['physical'],spec['expected_track_types'].get(q['track']))
    record['available']=True
   except parser.SchemaError as error:record['missing_reason']='schema_unavailable:'+str(error)
  else:record['missing_reason']=response.get('failure','missing_public_body')
  if q['physical']:physical[q['chrom']+'|'+q['logical_track']]=record
  else:logical[q['track']]=record
  records.append(record)
  print('Schema-only',q['key'],'available' if record['available'] else 'unavailable',flush=True)
 c.certify(c.SCHEMA_DESIGN)
 receipt={'status':'COMPLETED_SCHEMA_METADATA_ONLY','design_sha256':c.sha(c.SCHEMA_DESIGN),'records':records,'logical':logical,'physical':physical,'logical_tracks_available':all(logical[t]['available'] for t in c.TRACKS),'available_physical_groups':sum(v['available'] for v in physical.values()),'new_metadata_requests':client.new_requests,'acquired_bytes_across_own_cache':client.total_used,'annotation_values_read':False,'aligned_bases_read':False,'outcomes_read':False,'models_fit':0,'source_live_binary_version_certified':False,'source_timezone_not_invented':True}
 c.jsave(c.OUT/'metadata_admission_receipt.json',receipt)
 print('Schema-only completion; no values:',receipt['logical_tracks_available'],receipt['available_physical_groups'],flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root-start',action='store_true');run(a.parse_args().root_start)
