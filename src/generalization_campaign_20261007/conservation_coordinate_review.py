"""Independent stdlib completed-coordinate metadata review; no reference replay."""
from __future__ import annotations
from collections import Counter,defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'results/generalization_conservation_mapping_20261007'
OUT=ROOT/'results/generalization_campaign_20261007/conservation_coordinate_review_01.json'
REPORT=ROOT/'reports/generalization_campaign_20261007/conservation_coordinate_review_01.md'
MAPPED='reference_site_vector_unique_complete_candidates'
SIX=['intervention_id','dataset','biological_component','parent_context_id','parent_sequence','mutant_sequence']
TEN=SIX+['gene_transcript','parent_id','mutant_id']
COMPLEMENT=dict(zip('ACGT','TGCA'))

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
 return h.hexdigest()

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def array_items(path,chunk=131072):
 """Incremental JSON-array reader; retain one object instead of a large table."""
 decoder=json.JSONDecoder()
 with Path(path).open('r',encoding='utf-8') as stream:
  buffer=stream.read(chunk).lstrip();assert buffer.startswith('[');buffer=buffer[1:];expect_object=True
  while True:
   buffer=buffer.lstrip()
   if not buffer:
    extra=stream.read(chunk);assert extra,'Incomplete JSON array';buffer+=extra;continue
   if buffer.startswith(']'):
    assert not (buffer[1:]+stream.read()).strip();return
   if not expect_object:
    assert buffer.startswith(',');buffer=buffer[1:];expect_object=True;continue
   try:value,end=decoder.raw_decode(buffer)
   except json.JSONDecodeError:
    extra=stream.read(chunk);assert extra,'Malformed/incomplete JSON object';buffer+=extra;assert len(buffer)<8*2**20;continue
   assert isinstance(value,dict);yield value;buffer=buffer[end:];expect_object=False

def csv_items(path,fields):
 with gzip.open(path,'rt',encoding='utf-8',newline='') as stream:
  reader=csv.DictReader(stream);assert set(reader.fieldnames)==set(fields) and len(reader.fieldnames)==len(fields)
  for row in reader:assert None not in row;yield row

def region(ref):return ('chrM' if ref['chromosome']=='MT' else 'chr'+str(ref['chromosome']),int(ref['gene_start1'])-1,int(ref['gene_end1']))

def vector_state(parent):
 vectors={(m['chrom'],m['strand'],tuple(m['positions0'])) for m in parent['matches']}
 for chrom,strand,positions in vectors:
  assert strand in ('+','-') and len(positions)==len(parent['parent_sequence']) and len(set(positions))==len(positions)
  assert all(isinstance(p,int) and p>=0 for p in positions)
  assert all((b>a if strand=='+' else b<a) for a,b in zip(positions,positions[1:]))
 complete=bool(parent['candidate_anchor_count']) and not parent['unresolved_candidates']
 assert parent['candidate_resolution_complete']==complete
 assert (parent['mapping_status']==MAPPED)==(complete and len(vectors)==1)
 return next(iter(vectors)) if parent['mapping_status']==MAPPED else None,len(vectors)

def check_edit(row,edited,parent,vector):
 assert set(edited)==set(TEN+['mapping_status','edit_positions0','edited_site_coordinates'])
 assert all(edited[key]==row[key] for key in TEN)
 assert parent['parent_sequence']==row['parent_sequence'] and parent['gene']==row['gene_transcript']
 assert edited['mapping_status']==parent['mapping_status']
 assert len(row['parent_sequence'])==len(row['mutant_sequence']) and set(row['parent_sequence']+row['mutant_sequence'])<=set('ACGT')
 changes=[i for i,(a,b) in enumerate(zip(row['parent_sequence'],row['mutant_sequence'])) if a!=b]
 assert changes and changes==edited['edit_positions0']
 if vector is None:assert not edited['edited_site_coordinates'];return changes,[]
 chrom,strand,positions=vector;expected=[]
 for i in changes:
  a,b=row['parent_sequence'][i],row['mutant_sequence'][i]
  expected.append({'insert_position0':i,'chrom':chrom,'genomic_position0':positions[i],'strand':strand,
   'expressed_reference':a,'expressed_alternate':b,'genomic_reference':a if strand=='+' else COMPLEMENT[a],'genomic_alternate':b if strand=='+' else COMPLEMENT[b]})
 assert edited['edited_site_coordinates']==expected
 return changes,expected

def run():
 assert not OUT.exists() and not REPORT.exists(),'Immutable new audit outputs only'
 assert not any(n.split('.')[0] in ('numpy','pandas','torch','openvino','scipy','sklearn') for n in sys.modules)
 paths=[SOURCE/name for name in ('mapping_receipt.json','independent_mapping_replay_receipt.json','design_manifest.json','metadata_preparation_receipt.json','region_plan.json','parent_reference_candidates.json','parent_mappings.json','edited_site_metadata.json','candidate_metadata.csv.gz')]
 inventory=ROOT/'artifacts/generalization_next_20261007/sequence_inventory.csv.gz';paths.append(inventory)
 before={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
 done=read(SOURCE/'mapping_receipt.json');replay=read(SOURCE/'independent_mapping_replay_receipt.json');design=read(SOURCE/'design_manifest.json');prep=read(SOURCE/'metadata_preparation_receipt.json')
 assert done['status']=='COMPLETED_FULL_COORDINATE_METADATA_ONLY' and replay['status']=='PASS_FULL_DIRECT_COORDINATE_REPLAY_ONLY'
 assert replay['mapping_receipt_sha256']==sha(SOURCE/'mapping_receipt.json') and replay['source_manifest_sha256']==done['design_manifest_sha256']==sha(SOURCE/'design_manifest.json')
 for name,expected in done['files'].items():assert sha(ROOT/name)==expected
 assert sha(inventory)==prep['files'][inventory.relative_to(ROOT).as_posix()]==design['files'][inventory.relative_to(ROOT).as_posix()]
 assert all(done[k] is False for k in ('outcomes_read','features_loaded','conservation_values_read','genome_wide_uniqueness_or_actual_isoform_certified')) and done['models_fit']==0
 plan=read(SOURCE/'region_plan.json');eligible={tuple(p['key']):p for p in plan if p['planned_status']=='eligible'}
 assert len(plan)==192 and len(eligible)==179
 expected={(key,kind) for key in eligible for kind in ('knownGene','sequence')};responses=done['public_response_receipts']
 assert len(responses)==len(expected)==358 and {(tuple(v['region']),v['kind']) for v in responses}==expected
 assert len({(tuple(v['region']),v['kind']) for v in responses})==len(responses)
 http=Counter();reuse=0;response_bytes=0;response_pins={}
 for item in responses:
  p=eligible[tuple(item['region'])];kind=item['kind'];path=(ROOT/item['response']).resolve();receipt=(ROOT/item['receipt']).resolve()
  assert path.is_relative_to(ROOT/'artifacts') and receipt==path.with_name(path.name+'.receipt.json')
  assert sha(receipt)==item['receipt_sha256'];internal=read(receipt)
  assert internal['url']==p['urls'][kind] and internal['http_status']==item['http_status'] and internal['sha256']==item['response_sha256']
  if item['response_sha256'] is None:assert not path.exists()
  else:
   assert sha(path)==item['response_sha256'] and path.stat().st_size==internal['bytes'];response_bytes+=internal['bytes']
  if kind in p['reuse']:assert item['response']==p['reuse'][kind]['response'] and item['reused_immutable_pilot'] is True;reuse+=1
  else:assert item['reused_immutable_pilot'] is False and path.is_relative_to(ROOT/'artifacts/generalization_conservation_mapping_20261007')
  http[str(item['http_status'])]+=1;response_pins[item['receipt']]=item['receipt_sha256']
  if item['response_sha256'] is not None:response_pins[item['response']]=item['response_sha256']
 assert reuse==8 and len(responses)-reuse==done['new_region_requests']==350
 references={(p['dataset'],p['parent_id']):p for p in array_items(SOURCE/'parent_reference_candidates.json')}
 parents={};parent_status=defaultdict(Counter);unresolved=Counter();vectors=0
 for p in array_items(SOURCE/'parent_mappings.json'):
  key=p['dataset'],p['parent_id'];assert key not in parents and key in references
  ref=references[key];assert p['gene']==ref['gene'] and p['parent_sequence']==ref['parent_sequence'] and p['parent_sequence_sha256']==ref['parent_sequence_sha256']==hashlib.sha256(p['parent_sequence'].encode()).hexdigest()
  anchors={(r['transcript_id'].split('.')[0],region(r)) for r in ref['reference_candidates']}
  assert len(anchors)==p['candidate_anchor_count']
  for match in p['matches']:
   assert match['assembly']=='mm10' and match['annotation_data_time']=='2019-09-19T15:18:52'
   assert (match['transcript'].split('.')[0],tuple(match['region'])) in anchors
   assert match['region'][0]==match['chrom'] and all(match['region'][1]<=v<match['region'][2] for v in match['positions0'])
  vector,count=vector_state(p);vectors+=len(p['matches']);parent_status[p['dataset']][p['mapping_status']]+=1
  unresolved.update(v['reason'] for v in p['unresolved_candidates'])
  parents[key]=(p,vector,count)
 assert set(parents)==set(references) and len(parents)==done['parents']==replay['parents']==3022
 assert {k:dict(v) for k,v in parent_status.items()}==done['parent_status_by_dataset']
 row_status=defaultdict(Counter);gene_all=defaultdict(set);gene_mapped=defaultdict(set);component_all=defaultdict(set);component_mapped=defaultdict(set);menus={};ids=set();sites=set();triples=set();strands=Counter();edit_total=0;edited_records=0;rowcount=0
 rows=csv_items(SOURCE/'candidate_metadata.csv.gz',TEN);original=csv_items(inventory,SIX);edits=array_items(SOURCE/'edited_site_metadata.json')
 for row in rows:
  orig=next(original);edited=next(edits);assert all(row[k]==orig[k] for k in SIX)
  assert row['intervention_id'] not in ids;ids.add(row['intervention_id']);rowcount+=1
  parent,vector,nvectors=parents[(row['dataset'],row['parent_id'])];changes,coords=check_edit(row,edited,parent,vector)
  dataset,status=row['dataset'],edited['mapping_status'];row_status[dataset][status]+=1
  gene_all[dataset].add(row['gene_transcript']);component_all[dataset].add(row['biological_component'])
  menu=menus.setdefault((dataset,row['parent_context_id']),{'rows':0,'mapped':0});menu['rows']+=1
  if vector is not None:
   menu['mapped']+=1;gene_mapped[dataset].add(row['gene_transcript']);component_mapped[dataset].add(row['biological_component']);strands[vector[1]]+=1
  edit_total+=len(changes);edited_records+=len(coords)
  for coordinate in coords:
   sites.add((coordinate['chrom'],coordinate['genomic_position0']));triples.add((coordinate['chrom'],coordinate['genomic_position0'],coordinate['genomic_reference'],coordinate['genomic_alternate']))
 assert next(original,None) is None and next(edits,None) is None
 assert rowcount==done['original_candidate_rows']==replay['original_candidate_rows']==26258 and len(menus)==prep['full_parent_context_menus']==5436
 assert {k:dict(v) for k,v in row_status.items()}==done['row_status_by_dataset']
 assert vectors==replay['transcript_vectors']==4525 and edited_records==replay['edited_site_records']==66669
 assert all(sha(ROOT/name)==value for name,value in before.items())
 assert all(sha(ROOT/name)==value for name,value in response_pins.items())
 counts={}
 for dataset,stats in sorted(row_status.items()):
  n=sum(stats.values());mapped=stats[MAPPED];ms=[v for (d,k),v in menus.items() if d==dataset]
  counts[dataset]={'rows':n,'mapped_rows':mapped,'row_coverage':mapped/n,'status_rows':dict(stats),
   'parents':sum(parent_status[dataset].values()),'mapped_parents':parent_status[dataset][MAPPED],
   'genes_total':len(gene_all[dataset]),'genes_with_mapped_rows':len(gene_mapped[dataset]),'components_total':len(component_all[dataset]),'components_with_mapped_rows':len(component_mapped[dataset]),
   'menus_total':len(ms),'fully_mapped_menus':sum(v['mapped']==v['rows'] for v in ms),'partially_mapped_menus':sum(0<v['mapped']<v['rows'] for v in ms),'unmapped_menus':sum(v['mapped']==0 for v in ms)}
 result={'status':'PASS_INDEPENDENT_COORDINATE_METADATA_COUNTS_ROSTERS_PROVENANCE','source_sha256':sha(__file__),'observed_input_sha256':before,'observed_response_receipt_and_body_sha256':response_pins,
  'observed_hash_timing':'Independent post-completion audit; mapping-time public response binding preserved, not newly invented birth assurance',
  'all_original_ids_and_full_menus_preserved':True,'rows':rowcount,'parents':len(parents),'menus':len(menus),'mapped_rows':sum(v[MAPPED] for v in row_status.values()),'mapped_parents':sum(v[MAPPED] for v in parent_status.values()),
  'coverage_by_dataset':counts,'region_status_counts':dict(Counter(p['planned_status'] for p in plan)),
  'public_response_count':len(responses),'new_response_count':len(responses)-reuse,'reused_response_count':reuse,'HTTP_status_counts':dict(http),'total_response_bytes':response_bytes,
  'candidate_edit_position_count':edit_total,'mapped_edited_site_records':edited_records,'unique_forward_genome_positions':len(sites),'unique_forward_site_reference_alternate_tuples':len(triples),'transcript_match_vectors':vectors,'mapped_rows_by_strand':dict(strands),'unresolved_anchor_reason_counts':dict(unresolved),
  'existing_full_reference_replay_PASS_bound':True,'full_reference_replay_rerun':False,'source_or_output_modified':False,
  'genomewide_uniqueness_or_actual_reporter_isoform_certified':False,'conservation_values_or_aligned_columns_queried':False,'outcomes_read':False,'features_or_models_read':False,'model_fits':0,
  'limits':['Unique only among all fixed author candidate transcripts/regions that resolved, not all genome loci or the actual expressed mature reporter.','Moffatt/SRLE and unresolved/ambiguous parents retain empty coordinates; missingness is not zero conservation or negative biology.','HTTP200 and coordinate replay do not certify a conservation value source, an aligned allele consensus or localization usefulness.','Gene/parent mapping metadata and original sequence identities were reviewed; original author outcome-estimation pipelines were not re-proven.']}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')
 lines=['# Independent full-coordinate metadata review','',f"All {rowcount:,} original IDs, {len(parents):,} exact parents and {len(menus):,} complete menus remain. {result['mapped_rows']:,} rows ({100*result['mapped_rows']/rowcount:.2f}%) / {result['mapped_parents']:,} parents have a unique reference vector with every fixed anchored candidate resolved. No conservation values, alignment columns, localization outcomes, feature matrices or models were accessed.",'','| Exposed source | Mapped / all rows | Coverage | Genes with mapped rows / all | Mapped / all menus |','|---|---:|---:|---:|---:|']
 for ds,v in counts.items():lines.append(f"| {ds} | {v['mapped_rows']:,} / {v['rows']:,} | {100*v['row_coverage']:.2f}% | {v['genes_with_mapped_rows']} / {v['genes_total']} | {v['fully_mapped_menus']:,} / {v['menus_total']:,} |")
 lines.extend(['',f"The audit independently matched original six-field sequence inventories to metadata IDs/order, parent identities/anchor counts, all reported statuses, full-vector uniqueness, every changed-site coordinate and forward-strand allele complement, with no partial menu introduced. It checked {edited_records:,} mapped edit records, {len(sites):,} unique forward sites and {len(triples):,} site/reference/alternate tuples. The existing full-reference exon/strand replay is hash-bound PASS and was not repeated.",'',f"All {len(responses)} eligible public responses ({len(responses)-reuse} new + {reuse} preserved pilot) match the fixed regional roster and mapping-time receipt/body SHA bindings. HTTP status counts are {dict(http)}; {response_bytes:,} bytes are bound. Missing/capped/unmatched rows remain. Input and response hashes matched before/after this audit.",'','The useful result is coordinate feasibility on two exposed studies. It does not certify genome-wide uniqueness, actual mature reporter processing, any mutant conservation difference, alternate-consensus access, phylogenetic independence or localization direction. Zero native mapping for Moffatt and synthetic SRLE is a substantial future-feature missingness confound; coverage-only matched controls remain necessary. No generalization or biological positive result follows from these metadata counts.','',f"Numerical/provenance receipt SHA: `{sha(OUT)}`. Source: `{Path(__file__).relative_to(ROOT).as_posix()}`."])
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 with REPORT.open('x',encoding='utf-8') as stream:stream.write('\n'.join(lines)+'\n')
 print('Coordinate metadata review PASS',result['mapped_rows'],len(sites),len(triples),sha(OUT),flush=True)

class Tests(unittest.TestCase):
 def test_streaming_tiny_chunks(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory)/'x.json';values=[{'a':'quote \\" unicode α','x':[1,2]},{'b':3}];p.write_text(json.dumps(values),encoding='utf-8');self.assertEqual(list(array_items(p,3)),values)
 def test_unique_vector_requires_all_candidates(self):
  p={'candidate_anchor_count':2,'candidate_resolution_complete':True,'unresolved_candidates':[],'parent_sequence':'AC','mapping_status':MAPPED,'matches':[{'chrom':'chr1','strand':'+','positions0':[1,2]}]}
  self.assertEqual(vector_state(p)[1],1);p['unresolved_candidates']=[{'reason':'missing'}]
  with self.assertRaises(AssertionError):vector_state(p)
 def test_minus_forward_allele_and_no_map_empty(self):
  row=dict(zip(TEN,['i','d','g','c','AC','AT','gene','parent','mutant']))
  parent={'parent_sequence':'AC','gene':'gene','mapping_status':MAPPED};e={**row,'mapping_status':MAPPED,'edit_positions0':[1],'edited_site_coordinates':[{'insert_position0':1,'chrom':'chr1','genomic_position0':8,'strand':'-','expressed_reference':'C','expressed_alternate':'T','genomic_reference':'G','genomic_alternate':'A'}]}
  self.assertEqual(len(check_edit(row,e,parent,('chr1','-',(9,8)))[1]),1)
  with self.assertRaises(AssertionError):check_edit(row,e,parent,None)
 def test_edit_identity_or_coordinate_corruption(self):
  row=dict(zip(TEN,['i','d','g','c','AC','AT','gene','parent','mutant']));parent={'parent_sequence':'AC','gene':'gene','mapping_status':'no_exact_source_utr'}
  e={**row,'mapping_status':'no_exact_source_utr','edit_positions0':[1],'edited_site_coordinates':[]};check_edit(row,e,parent,None);e['intervention_id']='other'
  with self.assertRaises(AssertionError):check_edit(row,e,parent,None)

if __name__=='__main__':
 assert sys.argv[1:] in (['test'],['run'])
 unittest.main(argv=[sys.argv[0]]) if sys.argv[1:] == ['test'] else run()
