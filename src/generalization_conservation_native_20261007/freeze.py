"""Two independent committed guards: code/schema then observed-source values."""
import argparse,hashlib
from . import common as c
def source_files():
 paths=[]
 for top in ('src','reports','results','artifacts'):
  paths.append(c.ROOT/top/c.NS/'.gitattributes')
 paths+=list(c.SRC.glob('*.py'))+[c.REP/'protocol.md',c.REP/'readiness.md']
 paths+=[c.OUT/name for name in ('value_query_roster.json','schema_query_roster.json','extraction_spec.json','preparation_receipt.json','synthetic_tests_receipt.json','synthetic_tests_receipt_v2.json','synthetic_tests_receipt_v3.json')]
 external=[c.MAP/name for name in ('design_manifest.json','mapping_receipt.json','independent_mapping_replay_receipt.json','parent_mappings.json','edited_site_metadata.json')]
 old=c.read(c.MAP/'design_manifest.json');external += [c.ROOT/p for p in old['files']]
 external += [c.FEAS/name for name in ('preparation_receipt.json','site_inventory_feasibility_receipt.json','certified_site_inventory.json','proposed_native_request_roster.json','all_original_row_site_metadata.json.gz')]
 v1=c.bind_feasibility()
 external += [c.ROOT/p for p in v1['files']]
 external += [c.ROOT/p for p in v1['external_coordinate_and_metadata_bindings']]
 external += [c.ROOT/'src/generalization_conservation_features_feasibility_20261007/kent_source_probe.py']
 external += [c.ROOT/'reports/generalization_conservation_features_feasibility_20261007/multitrack_efficiency_v2.md']
 ext=c.ROOT/'artifacts/generalization_conservation_features_feasibility_20261007/kent_source'
 external += list(ext.glob('*.body'))+list(ext.glob('*.receipt.json'))
 return sorted(set(paths+external))
def schema():
 c.bind_mapping();c.bind_feasibility();tests=c.read(c.OUT/'synthetic_tests_receipt_v3.json');assert tests['status']=='PASS_SCOPED_INVENTED_AND_MOCK_TESTS_ONLY'
 for relative,digest in tests['source_files'].items():assert c.sha(c.ROOT/relative)==digest
 paths=source_files()
 m={'status':'FROZEN_CODE_SCHEMA_ONLY_DESIGN_NO_VALUE_AUTHORIZATION','files':{p.relative_to(c.ROOT).as_posix():c.sha(p) for p in paths},'file_count':len(paths),'mapping_receipt_sha256':c.MAP_SHA,'mapping_replay_sha256':c.REPLAY_SHA,'maximum_metadata_requests':c.read(c.OUT/'extraction_spec.json')['metadata_requests'],'maximum_value_requests':3003,'annotation_value_requests_authorized':False,'supervised_fits_authorized':False}
 c.jsave(c.SCHEMA_DESIGN,m);print('Schema design manifest',len(paths),c.sha(c.SCHEMA_DESIGN),flush=True)
def values():
 c.certify(c.SCHEMA_DESIGN)
 d=c.read(c.OUT/'metadata_admission_receipt.json');assert d['status']=='COMPLETED_SCHEMA_METADATA_ONLY' and d['logical_tracks_available']
 roster=c.read(c.OUT/'schema_query_roster.json');assert [r['key'] for r in d['records']]==[q['key'] for q in roster]
 paths=source_files()+[c.SCHEMA_DESIGN,c.OUT/'metadata_admission_receipt.json']
 for q,r in zip(roster,d['records']):
  assert all(r[k]==v for k,v in q.items()),'Observed schema roster differs'
  planned=c.ART/'schema'/('mm10_'+q['key']+'.json')
  p=planned.with_name(planned.name+'.receipt.json')
  assert r['response_receipt']==p.relative_to(c.ROOT).as_posix() and c.sha(p)==r['response_receipt_sha256'];paths.append(p)
  birth=p.with_name(p.name+'.sha256.json');assert c.sha(birth)==r['response_receipt_birth_sha256'] and c.read(birth)['receipt_sha256']==c.sha(p);paths.append(birth)
  response=c.read(p);assert response['url']==q['url']
  if r['body_path']:
   assert r['body_path']==planned.relative_to(c.ROOT).as_posix()
   b=c.ROOT/r['body_path'];assert c.sha(b)==r['body_sha256']==response['sha256'];paths.append(b)
  else: assert not planned.exists() and response['sha256'] is None
  if response.get('oversize_prefix_path'):
   b=planned.with_name(planned.name+'.oversize_prefix.bin');assert response['oversize_prefix_path']==b.name and c.sha(b)==response['oversize_prefix_sha256'];paths.append(b)
 paths=sorted(set(paths));m={'status':'FROZEN_NATIVE_VALUE_EXTRACTION_ONLY_NO_FEATURES_OR_FITS','files':{p.relative_to(c.ROOT).as_posix():c.sha(p) for p in paths},'file_count':len(paths),'code_schema_design_sha256':c.sha(c.SCHEMA_DESIGN),'metadata_admission_sha256':c.sha(c.OUT/'metadata_admission_receipt.json'),'live_server_binary_version_certified':False,'request_roster_upper_bound':3003,'missing_physical_schema_skips_fixed_interval_and_preserves_all_rows':True,'supervised_fits_authorized':False}
 c.jsave(c.VALUE_DESIGN,m);print('Value design manifest',len(paths),c.sha(c.VALUE_DESIGN),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['schema','values']);a=p.parse_args();schema() if a.stage=='schema' else values()
