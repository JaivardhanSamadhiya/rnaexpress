"""Separate source/effect replay. No producer helper or fitted model is imported."""
from pathlib import Path
from decimal import Decimal
import collections,hashlib,io,json,math,re,statistics,subprocess,zipfile
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];NS='generalization_prelib_binding_descriptive_20261008';OUT=ROOT/'results'/NS
URI='http://schemas.openxmlformats.org/spreadsheetml/2006/main';Q='{'+URI+'}'
SELECTED={'A':'ID','C':'Sequence','L':'Input_1.raw','M':'Input_2.raw','N':'PUM1_IP_1.raw','O':'PUM1_IP_2.raw','P':'PUM2_IP_1.raw','Q':'PUM2_IP_2.raw'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def bounded_read(z,name):
 assert z.getinfo(name).file_size<=32*2**20
 data=z.read(name);assert len(data)<=32*2**20;return data

def parse_selected(z,member,expected):
 strings=[]
 if 'xl/sharedStrings.xml' in z.namelist():
  root=ET.fromstring(bounded_read(z,'xl/sharedStrings.xml'))
  strings=[''.join(t.text or '' for t in item.iter(Q+'t')) for item in root]
  assert len(strings)<=100000 and max(map(len,strings),default=0)<=10000
 root=ET.fromstring(bounded_read(z,member));result={};seen=set()
 def literal(cell):
  assert cell is not None and cell.find(Q+'f') is None
  kind=cell.attrib.get('t','n');value=cell.find(Q+'v')
  if kind=='s':return strings[int(value.text)]
  if kind=='inlineStr':return ''.join(t.text or '' for t in cell.iter(Q+'t'))
  assert kind=='str' and value is not None;return value.text
 for row in root.find(Q+'sheetData'):
  index=int(row.attrib['r']);assert index not in seen;seen.add(index)
  cells={re.fullmatch(r'([A-Z]+)\d+',cell.attrib['r'])[1]:cell for cell in row}
  if index==1:assert {c:literal(cells.get(c)) for c in SELECTED}==SELECTED
  if index not in expected:continue
  e=expected[index];assert literal(cells.get('A'))==e['ID'] and literal(cells.get('C'))==e['Sequence']
  counts={}
  for column,field in SELECTED.items():
   if column in ('A','C'):continue
   cell=cells.get(column)
   if cell is None:value=None;token=None;missing='absent_cell'
   else:
    assert cell.find(Q+'f') is None and cell.attrib.get('t','n')=='n'
    node=cell.find(Q+'v');token=None if node is None else node.text
    if token is None:value=None;missing='blank_numeric_cell'
    else:
     d=Decimal(token);assert d.is_finite() and d==d.to_integral() and 0<=d<=10**12
     value=int(d);missing=None
   counts[field]={'value':value,'source_token':token,'missing_kind':missing}
  result[index]={'ID':e['ID'],'Sequence':e['Sequence'],'raw_counts':counts}
 assert set(result)==set(expected)
 return result

def independent_contrast(a,b,protein,pseudo):
 get=lambda row,name:row['raw_counts'][name]['value']
 ips=[[get(row,protein+'_IP_'+str(i)+'.raw') for i in (1,2)] for row in (a,b)]
 inputs=[[get(row,'Input_'+str(i)+'.raw') for i in (1,2)] for row in (a,b)]
 if any(v is None for family in (ips,inputs) for group in family for v in group):return None
 grid=[[math.log2((ips[0][i]+pseudo)/(inputs[0][j]+pseudo))-math.log2((ips[1][i]+pseudo)/(inputs[1][j]+pseudo)) for j in range(2)] for i in range(2)]
 ip=[math.log2((x+pseudo)/(y+pseudo)) for x,y in zip(*ips)]
 inp=[math.log2((x+pseudo)/(y+pseudo)) for x,y in zip(*inputs)]
 return {'delta':math.fsum(v for line in grid for v in line)/4,'grid':grid,'deltaIP':math.fsum(ip)/2,'deltaInput':math.fsum(inp)/2,'IP':ip,'Input':inp}

def quality(countrows,points,parents,effects):
 mapping={p['source_excel_row']:(p['lineage'],p['prefix']) for p in parents}
 mapping.update({p['source_variant_excel_row']:(p['lineage'],p['prefix']) for p in points})
 fixed_groups={}
 for dimension,slot in (('nominal_lineage',0),('literal_background_prefix',1)):
  grouped=collections.defaultdict(list)
  for index,row in countrows.items():grouped[mapping[index][slot]].append(row)
  fixed_groups[dimension]={key:{'source_rows':len(rows),'zero_counts':{field:sum(row['raw_counts'][field]['value']==0 for row in rows) for field in SELECTED.values() if field not in ('ID','Sequence')}} for key,rows in sorted(grouped.items())}
 diagnostics={}
 for protein in ('PUM1','PUM2'):
  available=[e['association_effects'][protein] for e in effects if e['association_effects'][protein]['0.5']['complete']]
  primary=[e['0.5']['delta_mean_log_enrichment'] for e in available]
  differences=[abs(e['0.5']['delta_mean_log_enrichment']-e['1.0']['delta_mean_log_enrichment']) for e in available]
  diagnostics[protein]={'complete_effects':len(primary),'effect_min':min(primary),'effect_median':statistics.median(primary),'effect_max':max(primary),
   'pseudocount_absolute_change_median':statistics.median(differences),'pseudocount_absolute_change_max':max(differences),
   'strict_sign_reversals_between_fixed_pseudocounts':sum(e['0.5']['delta_mean_log_enrichment']*e['1.0']['delta_mean_log_enrichment']<0 for e in available),
   'positive_enrichment_with_nonpositive_IP_and_negative_Input_delta':sum(e['0.5']['delta_mean_log_enrichment']>0 and e['0.5']['delta_logIP']<=0 and e['0.5']['delta_logInput']<0 for e in available),
   'IP_column_delta_strict_sign_disagreement':sum(e['0.5']['IP_column_deltas'][0]*e['0.5']['IP_column_deltas'][1]<0 for e in available),
   'these_are_source_quality_descriptions_not_biological_replication_or_significance':True}
 return {'fixed_metadata_group_diagnostics':fixed_groups,'effect_quality_by_protein':diagnostics,
  'selected_cohort_totals_are_not_library_depth':True,'no_rows_filtered_or_reweighted':True,
  'diagnostics_declared_after_initial_count_exposure_not_prefit_model_evidence':True,'training_pairs_admitted':0,'models_fit':0}

def run():
 p=OUT/'replay_manifest.json';m=read(p)
 assert subprocess.check_output(['git','show','HEAD:'+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for name,digest in m['files'].items():assert sha(ROOT/name)==digest,name
 saved=read(OUT/'selected_raw_count_rows.json');expected={r['source_excel_row']:r for r in saved['rows']};assert len(expected)==4070
 with zipfile.ZipFile(ROOT/m['archive_path']) as bundle:
  body=bundle.read('TableS4_PRELibB.xlsx');assert hashlib.sha256(body).hexdigest()==saved['source_workbook_SHA256']
  with zipfile.ZipFile(io.BytesIO(body)) as z:rows=parse_selected(z,'xl/worksheets/sheet1.xml',expected)
 for index,row in rows.items():
  assert row['raw_counts']==expected[index]['raw_counts'],index
  assert hashlib.sha256(row['Sequence'].encode()).hexdigest()==expected[index]['sequence_sha256']
 points=read(ROOT/m['points']);parents=read(ROOT/m['parents']);effects=read(OUT/'descriptive_point_association_effects.json')
 byID={e['source_variant_ID']:e for e in effects};assert len(byID)==len(effects)==len(points)==4054
 maxerr=0.;checks=0
 def equal(x,y):
  nonlocal maxerr,checks
  error=abs(x-y);assert error<=1e-11,(x,y,error)
  maxerr=max(maxerr,error);checks+=1
 for point in points:
  a=rows[point['source_variant_excel_row']];b=rows[point['parent_excel_row']];e=byID[point['source_variant_ID']]
  assert a['ID']==point['source_variant_ID'] and b['ID']==point['source_parent_ID']
  assert e['source_variant_excel_row']==point['source_variant_excel_row'] and e['parent_excel_row']==point['parent_excel_row']
  assert e['lineage_nominal']==point['lineage'] and e['mPRE_background']==point['mPRE_background'] and e['prefix']==point['prefix']
  i=point['source_coordinate_0based'];assert b['Sequence'][i]==point['ref']
  assert b['Sequence'][:i]+point['alt']+b['Sequence'][i+1:]==a['Sequence']
  for protein in ('PUM1','PUM2'):
   for pseudo in (.5,1.):
    independent=independent_contrast(a,b,protein,pseudo);original=e['association_effects'][protein][str(pseudo)]
    assert original['complete']==(independent is not None)
    if independent is None:assert original['delta_mean_log_enrichment'] is None;continue
    equal(independent['delta'],original['delta_mean_log_enrichment']);equal(independent['deltaIP'],original['delta_logIP']);equal(independent['deltaInput'],original['delta_logInput'])
    for j in range(2):
     equal(independent['IP'][j],original['IP_column_deltas'][j]);equal(independent['Input'][j],original['Input_column_deltas'][j])
     for k in range(2):equal(independent['grid'][j][k],original['crossed_input_deltas'][j][k])
 parent_controls=read(OUT/'parent_self_delta_controls.json');assert len(parent_controls)==16
 parent_byID={p['source_parent_ID']:p for p in parent_controls};assert len(parent_byID)==16
 for parent in parents:
  row=rows[parent['source_excel_row']]
  for protein in ('PUM1','PUM2'):
   for pseudo in (.5,1.):
    x=independent_contrast(row,row,protein,pseudo);original=parent_byID[parent['source_parent_ID']]['effects'][protein][str(pseudo)]
    assert x is not None and x['delta']==0. and original['delta_mean_log_enrichment']==0.
 save(OUT/'source_quality_descriptions.json',quality(rows,points,parents,effects))
 save(OUT/'independent_source_effect_replay_receipt.json',{'status':'PASS_SEPARATE_WORKBOOK_TOKEN_AND_CROSSED_RATIO_EFFECT_REPLAY',
  'replay_manifest_sha256':sha(p),'source_rows_replayed':4070,'raw_cells_exact_token_and_missing_kind_replayed':24420,
  'point_effects_replayed':4054,'parent_self_controls_replayed':16,'numeric_comparisons':checks,'max_absolute_numeric_difference':maxerr,
  'producer_helper_imported':False,'root_separate_implementation_not_independent_agent_or_runtime':True,
  'source_processing_raw_reads_not_replayed':True,'source_sample_pairing_not_certified':True,'no_models_or_training_pair_admission':True,
  'quality_output_sha256':sha(OUT/'source_quality_descriptions.json')})
 print('PASS source tokens and independent crossed-ratio replay',checks,'comparisons; max difference',maxerr,flush=True)
if __name__=='__main__':run()
