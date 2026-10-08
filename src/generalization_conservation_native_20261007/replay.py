"""Independent site joins and full-parent missingness; shared strict envelope parser."""
from collections import defaultdict
from . import common as c,parser
from .produce import expected_for

def birth_bind(records,roster):
 assert [r['key'] for r in records]==[q['key'] for q in roster] and len(records)==len(roster)
 for q,r in zip(roster,records):
  assert r['url']==q['url']
  p=c.ART/'values'/(q['key']+'.json');receipt=p.with_name(p.name+'.receipt.json')
  if not r['queried']:
   assert r['status']=='UNAVAILABLE_SCHEMA_NO_QUERY' and not p.exists() and not receipt.exists() and not receipt.with_name(receipt.name+'.sha256.json').exists();continue
  assert r['response_receipt']==receipt.relative_to(c.ROOT).as_posix() and c.sha(receipt)==r['response_receipt_sha256']
  birth=receipt.with_name(receipt.name+'.sha256.json');assert c.sha(birth)==r['response_receipt_birth_sha256'] and c.read(birth)['receipt_sha256']==c.sha(receipt)
  d=c.read(receipt);assert d['url']==q['url']
  if d['sha256'] is None:
   assert r['body_path'] is None and r['body_sha256'] is None and not p.exists()
  else:
   assert r['body_path']==p.relative_to(c.ROOT).as_posix() and c.sha(p)==r['body_sha256']==d['sha256'] and p.stat().st_size==d['bytes']
  if d.get('oversize_prefix_path'):
   prefix=p.with_name(p.name+'.oversize_prefix.bin')
   assert d['oversize_prefix_path']==prefix.name and c.sha(prefix)==d['oversize_prefix_sha256']

def direct_scores(payload,q):
 o=parser.pairs(payload);out={}
 for track in c.TRACKS:
  raw=parser.one(o,track)
  entries=[parser.regular(row) for row in raw]
  for pos in range(q['start0'],q['end0']):
   matches=[row['value'] for row in entries if row['chrom']==q['chrom'] and row['start']<=pos<row['end']]
   assert len(matches)<=1
   out[q['chrom'],pos,track]=float(matches[0]) if matches else None
 return out

def run():
 c.certify(c.VALUE_DESIGN);done=c.read(c.OUT/'value_extraction_receipt.json')
 assert done['status']=='COMPLETED_NATIVE_SITE_VALUE_EXTRACTION_NO_FEATURES_OR_MODELS' and done['value_design_sha256']==c.sha(c.VALUE_DESIGN)
 for path,digest in done['files'].items():assert c.sha(c.ROOT/path)==digest
 roster=c.read(c.OUT/'value_query_roster.json');metadata=c.read(c.OUT/'metadata_admission_receipt.json')
 assert done['metadata_admission_sha256']==c.sha(c.OUT/'metadata_admission_receipt.json')
 birth_bind(done['response_records'],roster)
 scores={}
 for q,r in zip(roster,done['response_records']):
  expected=expected_for(metadata,q);assert r['expected_metadata']==expected and r['queried']==(expected is not None)
  got={}
  if r['queried']:
   p=c.ROOT/r['response_receipt'];d=c.read(p)
   if d['http_status']==200 and not d.get('failure'):
    body=(c.ROOT/r['body_path']).read_bytes()
    try:
     _,groups=parser.values(body,q,expected)
     assert r['status']=='ADMITTED_EXACT_ORDERED_DUAL_TRACK_RESPONSE' and r['source_metadata_groups']==groups
     got=direct_scores(body,q)
    except parser.SchemaError:
     assert r['status']=='UNAVAILABLE_VALUE_RESPONSE'
   else: assert r['status']=='UNAVAILABLE_VALUE_RESPONSE'
  for pos in range(q['start0'],q['end0']):
   for track in c.TRACKS:scores[q['chrom'],pos,track]=got.get((q['chrom'],pos,track))
 sites,rows=c.reference_inventory();saved=c.read(c.OUT/'site_annotation_values.json')
 assert [(s['chrom'],s['position0'],s['reference'],s['alternates']) for s in saved]==[(s['chrom'],s['position0'],s['reference'],s['alternates']) for s in sites]
 for s in saved:
  assert s['scores']=={track:scores[s['chrom'],s['position0'],track] for track in c.TRACKS}
 original=defaultdict(list)
 for row in rows:original[row['dataset'],row['parent_id']].append(row)
 parent=c.read(c.OUT/'parent_annotation_availability.json')
 assert [(p['dataset'],p['parent_id']) for p in parent]==sorted(original)
 for p in parent:
  rr=original[p['dataset'],p['parent_id']];coordinates_complete=True;required=set()
  for row in rr:
   if row['mapping_status']!=c.MAPPED or len(row['edited_site_coordinates'])!=len(row['edit_positions0']):coordinates_complete=False
   for site in row['edited_site_coordinates']:required.add((site['chrom'],site['genomic_position0']))
  missing={key for key in required if any(scores.get((*key,track)) is None for track in c.TRACKS)}
  complete=coordinates_complete and bool(required) and not missing
  assert p['native_annotation_complete_parent']==complete and p['all_native_covariates_unavailable_for_entire_parent']==(not complete)
  assert p['coordinates_complete_parent']==coordinates_complete and p['required_unique_sites']==len(required) and p['missing_unique_sites']==len(missing)
  assert p['original_rows']==len(rr) and p['original_intervention_ids']==sorted(row['intervention_id'] for row in rr) and p['original_menus']==sorted({row['parent_context_id'] for row in rr})
 assert len(rows)==done['original_rows']==26258 and len(parent)==done['parents']==3022 and len({r['parent_context_id'] for r in rows})==done['original_menus']==5436
 assert done['complete_annotation_parents']==sum(p['native_annotation_complete_parent'] for p in parent)
 c.certify(c.VALUE_DESIGN)
 receipt={'status':'PASS_INDEPENDENT_SITE_JOIN_AND_WHOLE_PARENT_POLICY_REPLAY','extraction_receipt_sha256':c.sha(c.OUT/'value_extraction_receipt.json'),'value_manifest_sha256':c.sha(c.VALUE_DESIGN),'original_rows':len(rows),'original_menus':5436,'parents':len(parent),'exact_sites':len(sites),'source_envelope_validation_shared_with_reviewed_parser':True,'site_join_and_parent_policy_independently_reconstructed':True,'features_produced':False,'outcomes_read':False,'models_fit':0}
 c.jsave(c.OUT/'independent_extraction_replay_receipt.json',receipt);print(receipt['status'],flush=True)
if __name__=='__main__':run()
