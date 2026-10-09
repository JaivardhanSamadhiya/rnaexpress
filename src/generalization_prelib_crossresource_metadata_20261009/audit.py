"""Only declared metadata columns used from exposed canonical development CSV."""
from pathlib import Path
import csv,ctypes,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2];NS='generalization_prelib_crossresource_metadata_20261009';OUT=ROOT/'results'/NS
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def rc(seq):return seq.translate(str.maketrans('ACGT','TGCA'))[::-1]
def fresh():
 class M(ctypes.Structure):
  _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
 m=M();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
 assert m.available>=1.3*2**30,'Fresh metadata-only1.3GiB floor; original feature/model3GiB unchanged'
 return m.available
def run():
 fresh();mpath=OUT/'audit_manifest.json';m=read(mpath)
 assert subprocess.check_output(['git','show','HEAD:'+mpath.relative_to(ROOT).as_posix()],cwd=ROOT)==mpath.read_bytes()
 for rel,h in m['files'].items():assert sha(ROOT/rel)==h,rel
 design=read(ROOT/m['design'])['rows'];rows={x['source_excel_row']:x for x in design}
 parents=read(ROOT/m['parents']);points=read(ROOT/m['points']);assert len(parents)==16 and len(points)==4054
 parentmap={x['source_excel_row']:x for x in parents};members={}
 for p in parents:members[p['source_excel_row']]={'lineage':p['lineage'],'prefix':p['prefix'],'role':'parent'}
 for p in points:
  assert p['parent_excel_row'] in parentmap and p['lineage']==parentmap[p['parent_excel_row']]['lineage']
  seq=rows[p['source_variant_excel_row']]['Sequence'];wt=rows[p['parent_excel_row']]['Sequence']
  assert len(seq)==len(wt)==140 and sum(a!=b for a,b in zip(seq,wt))==1
  members[p['source_variant_excel_row']]={'lineage':p['lineage'],'prefix':p['prefix'],'role':'point','parent_excel_row':p['parent_excel_row']}
 exact={};seeds={}
 for i,x in members.items():
  seq=rows[i]['Sequence'];assert set(seq)<=set('ACGT')
  for orientation,text in (('forward',seq),('reverse_complement',rc(seq))):
   exact.setdefault(text,[]).append((i,orientation))
 for i,p in parentmap.items():
  seq=rows[i]['Sequence']
  for orientation,text in (('forward',seq),('reverse_complement',rc(seq))):
   for start in range(len(text)-60):seeds.setdefault(text[start:start+61],set()).add((p['lineage'],p['prefix'],orientation))
 lineages=sorted({p['lineage'] for p in parents});assert len(lineages)==7
 counts={g:{'backgrounds':sum(p['lineage']==g for p in parents),'points':sum(p['lineage']==g for p in points)} for g in lineages}
 exact_matches=[];fragment_matches={};gene_matches=[];canonical=0;datasets={}
 columns=m['metadata_columns']
 with (ROOT/m['canonical_csv']).open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f);assert set(columns)<=set(reader.fieldnames)
  # File contains previously exposed outcomes; these strings are never converted,
  # selected, used for eligibility or written. Only the fixed metadata subset is used.
  for full in reader:
   row={name:full[name] for name in columns};canonical+=1;dataset=row['dataset'];datasets[dataset]=datasets.get(dataset,0)+1
   genes=row['gene_transcript'].casefold()
   if genes in {g.casefold() for g in lineages}:gene_matches.append({**{k:row[k] for k in columns if 'sequence' not in k},'PRELib_lineage':next(g for g in lineages if g.casefold()==genes),'identity_is_literal_name_match_only':True})
   for role in ('parent_sequence','mutant_sequence'):
    seq=row[role];assert seq and set(seq)<=set('ACGT')
    for i,orientation in exact.get(seq,[]):
     exact_matches.append({'canonical_intervention_id':row['intervention_id'],'dataset':dataset,'biological_component':row['biological_component'],'canonical_sequence_role':role,'PRELib_source_excel_row':i,'PRELib_lineage':members[i]['lineage'],'orientation':orientation})
    found=set()
    for start in range(max(0,len(seq)-60)):found.update(seeds.get(seq[start:start+61],()))
    for lineage,prefix,orientation in found:
     key=(dataset,row['biological_component'],row['parent_context_id'],lineage,prefix,orientation)
     entry=fragment_matches.setdefault(key,{'dataset':dataset,'biological_component':row['biological_component'],'parent_context_id':row['parent_context_id'],'gene_transcript_literal':row['gene_transcript'],'PRELib_lineage':lineage,'PRELib_prefix':prefix,'orientation':orientation,'sequence_roles':set(),'canonical_intervention_ids':set(),'minimum_exact_shared_fragment_length':61,'same_gene_or_homology_not_certified':True})
     entry['sequence_roles'].add(role);entry['canonical_intervention_ids'].add(row['intervention_id'])
 assert canonical==26258 and set(datasets)==set(m['canonical_datasets'])
 fragments=[]
 for key,entry in sorted(fragment_matches.items()):
  entry['sequence_roles']=sorted(entry['sequence_roles']);entry['canonical_intervention_ids']=sorted(entry['canonical_intervention_ids']);fragments.append(entry)
 sequence_lineages={}
 for i,x in members.items():sequence_lineages.setdefault(rows[i]['Sequence'],set()).add(x['lineage'])
 crosslineage=[{'sequence_sha256':hashlib.sha256(seq.encode()).hexdigest(),'lineages':sorted(gs)} for seq,gs in sequence_lineages.items() if len(gs)>1]
 save(OUT/'declared_metadata_overlap_records.json',{'exact_sequence_matches_including_RC':exact_matches,'parent_fragment61_matches':fragments,'literal_gene_name_matches':gene_matches,'cross_lineage_sequence_groups':crosslineage,'lineage_counts':counts,
  'cohort_membership':[{'source_excel_row':i,'source_ID':rows[i]['ID'],'sequence_sha256':hashlib.sha256(rows[i]['Sequence'].encode()).hexdigest(),**x} for i,x in sorted(members.items())]})
 save(OUT/'audit_receipt.json',{'status':'PASS_DECLARED_METADATA_AUDIT' if not crosslineage else 'REQUIRES_CROSS_LINEAGE_GROUPING_BEFORE_FITS','manifest_sha256':sha(mpath),
  'canonical_rows':canonical,'canonical_datasets':datasets,'PRELib_sequence_rows':len(members),'points':len(points),'backgrounds':len(parents),'nominal_lineages':lineages,
  'exact_sequence_match_records_including_RC':len(exact_matches),'parent_fragment61_match_groups':len(fragments),'literal_gene_match_records':len(gene_matches),
  'cross_lineage_sequence_groups':len(crosslineage),'only_selected_metadata_columns_used':True,'whole_CSV_bytes_contain_previously_exposed_development_labels':True,
  'numeric_outcomes_converted_or_analyzed':False,'reserved_outcomes_read':False,'models_fit':0,'training_pairs_admitted':0,
  'genomic_identity_of_all_lineages_or_partial_overlap_homology_certified':False,'records_sha256':sha(OUT/'declared_metadata_overlap_records.json')})
 print('METADATA_AUDIT',canonical,'canonical rows;',len(exact_matches),'exact;',len(fragments),'fragment groups;',len(gene_matches),'literal gene records',flush=True)
if __name__=='__main__':run()
