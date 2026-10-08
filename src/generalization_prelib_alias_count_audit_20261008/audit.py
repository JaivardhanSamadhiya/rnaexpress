"""Fixed exact-sequence alias count assignment audit, not extra training pairs."""
from pathlib import Path
import collections,hashlib,io,json,subprocess,zipfile
from src.generalization_prelib_binding_descriptive_20261008.extract import decode,COUNTS
ROOT=Path(__file__).resolve().parents[2];NS='generalization_prelib_alias_count_audit_20261008';OUT=ROOT/'results'/NS

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2)+'\n').encode())
def run():
 p=OUT/'alias_manifest.json';m=read(p)
 assert subprocess.check_output(['git','show','HEAD:'+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for name,digest in m['files'].items():assert sha(ROOT/name)==digest,name
 design=read(ROOT/m['design'])['rows'];groups=collections.defaultdict(list)
 for row in design:groups[row['Sequence']].append(row)
 aliases=[rows for rows in groups.values() if len(rows)>1]
 assert len(design)==6293 and len(groups)==6275 and len(aliases)==18
 expected={row['source_excel_row']:row for rows in aliases for row in rows};assert len(expected)==36
 points=read(ROOT/m['points']);parents=read(ROOT/m['parents']);cohort={x['source_variant_excel_row'] for x in points}|{x['source_excel_row'] for x in parents}
 save(OUT/'alias_count_exposure_started.json',{'exposed_development_metadata_selected_raw_counts_only':True,'new_outside_point_raw_rows':len(set(expected)-cohort),'new_raw_cells_to_open':6*len(set(expected)-cohort),'other_numerical_endpoints_closed':True,'manifest_sha256':sha(p)})
 headers=read(ROOT/m['headers']);book=next(b for b in headers['workbooks'] if b['bundle_member']=='TableS4_PRELibB.xlsx')
 with zipfile.ZipFile(ROOT/m['archive']) as bundle:
  body=bundle.read('TableS4_PRELibB.xlsx');assert hashlib.sha256(body).hexdigest()==book['workbook_sha256']
  with zipfile.ZipFile(io.BytesIO(body)) as z:rows=decode(z,book['sheets'][0]['worksheet_member'],expected)
 comparisons=[]
 for group in aliases:
  records=[rows[row['source_excel_row']] for row in group]
  count_equal={c:len({row['raw_counts'][c]['value'] for row in records})==1 for c in COUNTS}
  comparisons.append({'sequence_sha256':hashlib.sha256(group[0]['Sequence'].encode()).hexdigest(),'source_rows':[{'source_excel_row':row['source_excel_row'],'ID':row['ID'],'in_fixed_point_parent_cohort':row['source_excel_row'] in cohort,'raw_counts':row['raw_counts']} for row in records],
    'counts_identical_by_field':count_equal,'all_six_counts_identical':all(count_equal.values()),'author_count_assignment_algorithm_independently_certified':False,'rows_are_not_independent_sequence_interventions':True})
 save(OUT/'full_library_exact_sequence_aliases_and_counts.json',comparisons)
 alias_cohort=set(expected)&cohort
 parent_aliases=alias_cohort&{x['source_excel_row'] for x in parents}
 save(OUT/'alias_audit_receipt.json',{'status':'COMPLETE_FULL_SOURCE_EXACT_SEQUENCE_ALIAS_AND_SELECTED_RAW_COUNT_AUDIT',
  'manifest_sha256':sha(p),'source_design_rows':len(design),'source_unique_exact_DNA_sequences':len(groups),'exact_sequence_alias_groups':len(aliases),
  'rows_in_alias_groups':len(expected),'cohort_rows_with_external_exact_aliases':len(alias_cohort),'point_parent_baselines_with_external_aliases':len(parent_aliases),
  'alias_groups_with_identical_six_counts':sum(x['all_six_counts_identical'] for x in comparisons),
  'alias_groups_with_differing_selected_raw_counts':sum(not x['all_six_counts_identical'] for x in comparisons),
  'raw_count_rows_outside_fixed_point_cohort_opened':len(set(expected)-cohort),'no_extra_training_pairs_or_independent_genes':True,
  'source_assignment_or_construct_barcodes_not_certified_by_equal_counts':True,'no_cohort_rows_filtered':True,'models_fit':0,'training_pairs_admitted':0,
  'alias_output_sha256':sha(OUT/'full_library_exact_sequence_aliases_and_counts.json')})
 print('ALIASES',len(aliases),'point aliases',len(alias_cohort),'parent aliases',len(parent_aliases),'equal six counts',sum(x['all_six_counts_identical'] for x in comparisons),flush=True)
if __name__=='__main__':run()
