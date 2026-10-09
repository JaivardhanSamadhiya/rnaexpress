"""Bounded exact cached-reference gene/transcript-name screen, not orthology."""
from .audit import ROOT,OUT,sha,read,save,fresh
import csv,re,subprocess
def normalized(text):
 text=text.strip().upper()
 return re.sub(r'^((?:NM|NR)_\d+)\.\d+$',r'\1',text)
def run():
 fresh();path=OUT/'alias_reference_audit_manifest_v2.json';m=read(path)
 assert subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
 for rel,h in m['files'].items():assert sha(ROOT/rel)==h,rel
 aliases={g:{normalized(x) for x in values} for g,values in m['reference_symbol_transcript_aliases'].items()}
 matched=[];rows=0
 with (ROOT/m['canonical_csv']).open(newline='',encoding='utf-8-sig') as f:
  for row in csv.DictReader(f):
   rows+=1
   for gene,names in aliases.items():
    if normalized(row['gene_transcript']) in names:
     matched.append({'intervention_id':row['intervention_id'],'dataset':row['dataset'],'biological_component':row['biological_component'],'parent_context_id':row['parent_context_id'],
      'canonical_gene_transcript_literal':row['gene_transcript'],'PRELib_nominal_lineage':gene,'exact_cached_symbol_or_accession_alias':True,'orthology_not_certified':True})
 assert rows==26258
 save(OUT/'alias_reference_audit_receipt_v2.json',{'status':'PASS_DECLARED_CACHED_REFERENCE_NAME_SCREEN','manifest_sha256':sha(path),'canonical_rows':rows,
  'reference_symbol_transcript_aliases':m['reference_symbol_transcript_aliases'],'matched_records':matched,'matched_record_count':len(matched),
  'outcome_strings_not_converted_or_selected':True,'no_reserved_source':True,'no_complete_cross_species_orthology_or_all_gene_exclusion_certificate':True,'models_fit':0})
 print('CACHED_REFERENCE_ALIAS_SCREEN',len(matched),'matches',flush=True)
if __name__=='__main__':run()
