"""Outcome-free exact site/request feasibility after full coordinate replay."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,gzip,hashlib,io,json
ROOT=Path('D:/rnaexpress')
NS='generalization_conservation_features_feasibility_20261007'
OUT=ROOT/'results'/NS
SRC=ROOT/'src'/NS
MAP=ROOT/'results/generalization_conservation_mapping_20261007'
MAPPED='reference_site_vector_unique_complete_candidates'
MAP_SHA='ae393a91e19b1394763a27d49275df078aabac5688bb33f26214b040e2d43c62'
REPLAY_SHA='cc41a93dca06f1f528720d8ddfd24f4f4b563fc81ff244f3bf142465e4e23218'
TRACKS=('phyloP60wayAll','phastCons60way')
def sha(p):
 return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  assert p.read_bytes()==b,'Preserve existing output: '+str(p)
 else:
  with p.open('xb') as s:s.write(b)
def jsave(p,o):
 save(p,(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
def adjacent_intervals(sites):
 by=defaultdict(set)
 for chrom,pos in sites:
  assert isinstance(chrom,str) and type(pos) is int and pos>=0
  by[chrom].add(pos)
 ans=[]
 for chrom in sorted(by):
  values=sorted(by[chrom]);begin=previous=values[0]
  for pos in values[1:]:
   if pos!=previous+1:
    ans.append((chrom,begin,previous+1));begin=pos
   previous=pos
  ans.append((chrom,begin,previous+1))
 return ans

def run():
 assert sha(MAP/'mapping_receipt.json')==MAP_SHA
 assert sha(MAP/'independent_mapping_replay_receipt.json')==REPLAY_SHA
 mapping=read(MAP/'mapping_receipt.json');replay=read(MAP/'independent_mapping_replay_receipt.json')
 assert mapping['status']=='COMPLETED_FULL_COORDINATE_METADATA_ONLY'
 assert replay['status']=='PASS_FULL_DIRECT_COORDINATE_REPLAY_ONLY' and replay['mapping_receipt_sha256']==MAP_SHA
 assert not mapping['conservation_values_read'] and not mapping['outcomes_read'] and not mapping['features_loaded'] and mapping['models_fit']==0
 for relative,digest in mapping['files'].items(): assert sha(ROOT/relative)==digest
 parents=read(MAP/'parent_mappings.json');rows=read(MAP/'edited_site_metadata.json')
 assert len(rows)==26258 and len(parents)==3022
 assert len({r['intervention_id'] for r in rows})==26258
 by_dataset={};sites={};alt_pairs=set();strand_rows=Counter();metadata_rows=[]
 for dataset in sorted({r['dataset'] for r in rows}):
  rr=[r for r in rows if r['dataset']==dataset];good=[r for r in rr if r['mapping_status']==MAPPED]
  pp=[p for p in parents if p['dataset']==dataset]
  by_dataset[dataset]={
   'original_rows':len(rr),'certified_rows':len(good),
   'original_parents':len(pp),'certified_parents':sum(p['mapping_status']==MAPPED for p in pp),
   'original_menus':len({r['parent_context_id'] for r in rr}),'certified_menus':len({r['parent_context_id'] for r in good}),
   'original_genes':len({r['gene_transcript'] for r in rr}),'genes_with_any_certified_row':len({r['gene_transcript'] for r in good}),
   'original_components':len({r['biological_component'] for r in rr}),'components_with_any_certified_row':len({r['biological_component'] for r in good}),
   'row_statuses':dict(Counter(r['mapping_status'] for r in rr)),
   'parent_statuses':dict(Counter(p['mapping_status'] for p in pp)),
   'unresolved_anchor_reasons':dict(Counter(u['reason'] for p in pp for u in p['unresolved_candidates']))}
 for r in rows:
  coords=r['edited_site_coordinates'];ok=r['mapping_status']==MAPPED
  assert bool(coords)==ok
  assert (not ok) or len(coords)==len(r['edit_positions0'])
  for c in coords:
   key=(c['chrom'],c['genomic_position0']);ref=c['genomic_reference'];alt=c['genomic_alternate']
   assert ref in 'ACGT' and alt in 'ACGT' and ref!=alt
   assert c['strand'] in ('+','-') and c['insert_position0'] in r['edit_positions0']
   assert key not in sites or sites[key]['reference']==ref,'Conflicting certified reference at shared genomic site'
   if key not in sites: sites[key]={'reference':ref,'alternates':set(),'datasets':set(),'genes':set()}
   sites[key]['alternates'].add(alt);sites[key]['datasets'].add(r['dataset']);sites[key]['genes'].add(r['gene_transcript'])
   alt_pairs.add((*key,ref,alt))
  if ok: strand_rows[coords[0]['strand']]+=1
  metadata_rows.append({k:r[k] for k in ['intervention_id','dataset','biological_component','parent_context_id','parent_id','gene_transcript','mapping_status','edit_positions0','edited_site_coordinates']})
 intervals=adjacent_intervals(sites)
 assert sum(end-begin for chrom,begin,end in intervals)==len(sites)
 assert { (chrom,p) for chrom,begin,end in intervals for p in range(begin,end)}==set(sites)
 serial_sites=[{'chrom':chrom,'position0':pos,'reference':s['reference'],'alternates':sorted(s['alternates']),'datasets':sorted(s['datasets']),'genes':sorted(s['genes'])} for (chrom,pos),s in sorted(sites.items())]
 serial_queries=[{'genome':'mm10','track':track,'chrom':chrom,'start0':begin,'end0':end,'admitted_sites':end-begin} for chrom,begin,end in intervals for track in TRACKS]
 jsave(OUT/'certified_site_inventory.json',serial_sites)
 jsave(OUT/'proposed_native_request_roster.json',serial_queries)
 save(OUT/'all_original_row_site_metadata.json.gz',gzip.compress((json.dumps(metadata_rows,sort_keys=True,separators=(',',':'))+'\n').encode(),mtime=0))
 bodies=0;response_status=Counter();failed=[]
 for rec in mapping['public_response_receipts']:
  receipt=ROOT/rec['receipt'];assert sha(receipt)==rec['receipt_sha256']
  d=read(receipt);response_status[str(d['http_status'])]+=1
  if rec.get('response'):
   response=ROOT/rec['response'];assert sha(response)==rec['response_sha256'];bodies+=response.stat().st_size
  if d['http_status']!=200:failed.append(rec['receipt'])
 counts={
  'status':'PASS_EXACT_COORDINATE_SITE_REQUEST_FEASIBILITY_ONLY',
  'mapping_receipt_sha256':MAP_SHA,'replay_receipt_sha256':REPLAY_SHA,
  'source_sha256':sha(Path(__file__)),
  'original_rows':len(rows),'original_parents':len(parents),'original_menus':len({r['parent_context_id'] for r in rows}),
  'certified_rows':sum(r['mapping_status']==MAPPED for r in rows),
  'certified_parents':sum(p['mapping_status']==MAPPED for p in parents),
  'certified_menus':len({r['parent_context_id'] for r in rows if r['mapping_status']==MAPPED}),
  'certified_genomic_sites':len(sites),'distinct_reference_alternate_site_pairs':len(alt_pairs),
  'certified_edit_records_with_repeats':sum(len(r['edited_site_coordinates']) for r in rows),
  'all_original_edit_records':sum(len(r['edit_positions0']) for r in rows),
  'certified_rows_by_transcript_strand':dict(strand_rows),
  'datasets':by_dataset,
  'full_mapping_new_requests':mapping['new_region_requests'],'full_mapping_response_count':len(mapping['public_response_receipts']),
  'full_mapping_response_statuses':dict(response_status),'full_mapping_body_bytes_including_pilot_reuse':bodies,
  'failed_response_receipts':failed,
  'adjacent_only_intervals':len(intervals),'largest_interval_bases':max(end-begin for chrom,begin,end in intervals),
  'proposed_native_track_requests':len(serial_queries),'minimum_request_spacing_seconds':1.05,
  'minimum_network_seconds_excluding_latency':len(serial_queries)*1.05,
  'annotation_value_queries':0,'aligned_base_queries':0,'outcomes_read':False,'models_fit':0,
  'query_roster_not_authorized_or_frozen':True,
  'files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [OUT/'certified_site_inventory.json',OUT/'proposed_native_request_roster.json',OUT/'all_original_row_site_metadata.json.gz']}}
 jsave(OUT/'site_inventory_feasibility_receipt.json',counts)
 print(json.dumps(counts,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':run()