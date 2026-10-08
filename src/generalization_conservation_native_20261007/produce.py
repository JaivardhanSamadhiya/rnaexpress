"""Frozen exact-site retrieval and whole-parent availability, no model features."""
import argparse
from collections import defaultdict,Counter
from . import common as c,parser,transport
def expected_for(metadata,query):
 answer={}
 for track in c.TRACKS:
  logical=metadata['logical'][track];physical=metadata['physical'][query['chrom']+'|'+track]
  if not logical['available'] or not physical['available']:return None
  answer[track]={'trackType':logical['metadata']['trackType'],'dataTime':physical['metadata']['dataTime'],'dataTimeStamp':physical['metadata']['dataTimeStamp']}
 return answer
def parent_availability(rows,site_values):
 groups=defaultdict(list)
 for r in rows:groups[(r['dataset'],r['parent_id'])].append(r)
 output=[]
 for (dataset,parent),rr in sorted(groups.items()):
  positions={(s['chrom'],s['genomic_position0']) for r in rr for s in r['edited_site_coordinates']}
  coordinates_complete=all(r['mapping_status']==c.MAPPED and len(r['edited_site_coordinates'])==len(r['edit_positions0']) for r in rr)
  missing={key for key in positions if key not in site_values or any(site_values[key]['scores'][t] is None for t in c.TRACKS)}
  eligible=coordinates_complete and bool(positions) and not missing
  output.append({'dataset':dataset,'parent_id':parent,'original_rows':len(rr),'original_menus':sorted({r['parent_context_id'] for r in rr}),'original_intervention_ids':sorted(r['intervention_id'] for r in rr),'native_annotation_complete_parent':eligible,'coordinates_complete_parent':coordinates_complete,'required_unique_sites':len(positions),'missing_unique_sites':len(missing),'all_native_covariates_unavailable_for_entire_parent':not eligible})
 return output
def run(root_start=False):
 assert root_start,'Root must explicitly start separately frozen value requests'
 c.certify(c.VALUE_DESIGN)
 metadata=c.read(c.OUT/'metadata_admission_receipt.json');assert metadata['logical_tracks_available'],'Missing logical schemas; no value start'
 roster=c.read(c.OUT/'value_query_roster.json');sites,rows=c.reference_inventory()
 allowed=[q['url'] for q in roster if expected_for(metadata,q) is not None]
 client=transport.Client(allowed) if allowed else None
 values={};response_records=[]
 for q in roster:
  expected=expected_for(metadata,q);p=c.ART/'values'/(q['key']+'.json');reason='missing_pinned_physical_schema';arrays=None;groups=None
  rec={'key':q['key'],'url':q['url'],'queried':False,'expected_metadata':expected,'status':'UNAVAILABLE_SCHEMA_NO_QUERY'}
  if expected is not None:
   body,response=client.get(q['url'],p);rec.update(queried=True,response_receipt=p.with_name(p.name+'.receipt.json').relative_to(c.ROOT).as_posix(),response_receipt_sha256=c.sha(p.with_name(p.name+'.receipt.json')),response_receipt_birth_sha256=c.sha(p.with_name(p.name+'.receipt.json.sha256.json')),body_path=p.relative_to(c.ROOT).as_posix() if response['sha256'] else None,body_sha256=response['sha256'])
   if body is not None:
    try:arrays,groups=parser.values(body,q,expected);rec.update(status='ADMITTED_EXACT_ORDERED_DUAL_TRACK_RESPONSE',source_metadata_groups=groups)
    except parser.SchemaError as error:reason='unavailable_value_schema:'+str(error);rec.update(status='UNAVAILABLE_VALUE_RESPONSE',missing_reason=reason)
   else:reason=response.get('failure','missing_public_body');rec.update(status='UNAVAILABLE_VALUE_RESPONSE',missing_reason=reason)
  for pos in range(q['start0'],q['end0']):
   key=(q['chrom'],pos);assert key not in values
   score={t:(arrays[t].get(pos) if arrays is not None else None) for t in c.TRACKS}
   values[key]={'scores':score,'missing_reason':None if all(v is not None for v in score.values()) else ('source_score_absent' if arrays is not None else reason),'query_key':q['key']}
  response_records.append(rec)
  print('Native site interval',q['key'],rec['status'],flush=True)
 assert set(values)=={(s['chrom'],s['position0']) for s in sites}
 result=[{**s,**values[s['chrom'],s['position0']]} for s in sites]
 parents=parent_availability(rows,values)
 assert sum(p['original_rows'] for p in parents)==26258 and len(parents)==3022
 c.jsave(c.OUT/'site_annotation_values.json',result);c.jsave(c.OUT/'parent_annotation_availability.json',parents)
 c.certify(c.VALUE_DESIGN)
 receipt={'status':'COMPLETED_NATIVE_SITE_VALUE_EXTRACTION_NO_FEATURES_OR_MODELS','value_design_sha256':c.sha(c.VALUE_DESIGN),'metadata_admission_sha256':c.sha(c.OUT/'metadata_admission_receipt.json'),'mapping_receipt_sha256':c.MAP_SHA,'mapping_replay_sha256':c.REPLAY_SHA,'response_records':response_records,'original_rows':len(rows),'original_menus':len({r['parent_context_id'] for r in rows}),'parents':len(parents),'original_cohort_preserved':True,'complete_annotation_parents':sum(p['native_annotation_complete_parent'] for p in parents),'parent_status_by_dataset':{d:dict(Counter('complete' if p['native_annotation_complete_parent'] else 'unavailable' for p in parents if p['dataset']==d)) for d in sorted({p['dataset'] for p in parents})},'new_value_requests':client.new_requests if client else 0,'acquired_bytes_across_own_cache':client.total_used if client else metadata['acquired_bytes_across_own_cache'],'files':{p.relative_to(c.ROOT).as_posix():c.sha(p) for p in (c.OUT/'site_annotation_values.json',c.OUT/'parent_annotation_availability.json')},'native_score_representation':'UCSC browser/API wig representation; original full precision not certified','features_produced':False,'outcomes_read':False,'models_fit':0}
 c.jsave(c.OUT/'value_extraction_receipt.json',receipt)
 print('Native extraction completed, pending independent replay; no feature/fit production',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root-start',action='store_true');run(a.parse_args().root_start)
