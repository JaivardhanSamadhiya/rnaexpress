"""Fixed outcome-free query and physical-schema rosters; no network."""
import hashlib,json
from . import common as c
def find_type(catalog,track):
 found=[]
 def visit(o):
  if isinstance(o,dict):
   if track in o and isinstance(o[track],dict) and 'type' in o[track]:found.append(o[track]['type'])
   for value in o.values():visit(value)
  elif isinstance(o,list):
   for value in o:visit(value)
 visit(catalog);assert len(set(found))==1,'Unambiguous catalog type required';return found[0]
def run():
 c.bind_mapping();sites,rows=c.reference_inventory()
 old=c.read(c.FEAS/'proposed_native_request_roster.json');assert len(old)==6006
 queries=[]
 for index in range(0,len(old),2):
  a,b=old[index:index+2];assert a['track']==c.TRACKS[0] and b['track']==c.TRACKS[1]
  assert all(a[k]==b[k] for k in ('genome','chrom','start0','end0','admitted_sites'))
  assert a['genome']=='mm10' and 0<a['end0']-a['start0']<=320
  item={k:a[k] for k in ('genome','chrom','start0','end0','admitted_sites')}
  item['key']=f"mm10_{a['chrom']}_{a['start0']}_{a['end0']}"
  item['url']=f"{c.API}/getData/track?genome=mm10;track={','.join(c.TRACKS)};chrom={a['chrom']};start={a['start0']};end={a['end0']};maxItemsOutput=10000"
  queries.append(item)
 assert len(queries)==3003
 assert {(q['chrom'],p) for q in queries for p in range(q['start0'],q['end0'])}=={(s['chrom'],s['position0']) for s in sites}
 catalog=c.read(c.ROOT/'artifacts/generalization_conservation_feasibility_20261007/public_metadata/mm10_tracks.json')
 types={t:find_type(catalog,t) for t in c.TRACKS}
 chroms=sorted({s['chrom'] for s in sites});metadata=[]
 for t in c.TRACKS:
  metadata.append({'key':t+'_logical_schema','track':t,'physical':False,'chrom':None,'url':f'{c.API}/list/schema?genome=mm10;track={t}'})
 for chrom in chroms:
  for t in c.TRACKS:
   name=chrom+'_'+t
   metadata.append({'key':name+'_physical_schema','track':name,'logical_track':t,'physical':True,'chrom':chrom,'url':f'{c.API}/list/schema?genome=mm10;track={name}'})
 c.jsave(c.OUT/'value_query_roster.json',queries);c.jsave(c.OUT/'schema_query_roster.json',metadata)
 c.jsave(c.OUT/'extraction_spec.json',{'tracks':list(c.TRACKS),'expected_track_types':types,'genome':'mm10','ordered_root_pairs_required':True,'row_schema':['chrom','start','end','value'],'max_response_bytes':c.MAX_RESPONSE,'max_total_bytes_across_both_stages':c.MAX_TOTAL,'request_spacing_seconds':c.RATE,'timeout_seconds':45,'retry_count':0,'metadata_requests':len(metadata),'maximum_value_requests':len(queries),'certified_chromosomes':chroms,'cohort_rows':26258,'original_menus':5436,'sites':15132,'parent_availability_policy':'dataset+exactparent complete across every candidate and both cells; any missing coordinate/track/site disables native covariates for entire parent','values_are_browser_API_representation_not_original_full_precision':True,'live_server_binary_version_unobserved':True,'features_or_supervised_models_produced':False})
 c.jsave(c.OUT/'preparation_receipt.json',{'status':'PREPARED_ROSTERS_ONLY_NO_NETWORK','metadata_requests':len(metadata),'value_requests':len(queries),'mapped_rows':15769,'original_rows':len(rows),'annotation_values_read':False,'outcomes_read':False,'models_fit':0,'source_sha256':c.sha(__file__),'mapping_receipt_sha256':c.MAP_SHA,'mapping_replay_sha256':c.REPLAY_SHA})
 print('Native extraction preparation only:',len(metadata),'metadata requests;',len(queries),'future dual-track requests',flush=True)
if __name__=='__main__':run()
