"""Outcome-free fixed point-cohort scores; no binding labels or localization import."""
from .model import ROOT,MODES,score,load_parameters
from pathlib import Path
import ctypes,hashlib,json,math,subprocess,time
OUT=ROOT/'results/generalization_pum2_fixed_math_20261008'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def fresh_guard():
 class Memory(ctypes.Structure):
  _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
 memory=Memory();memory.length=ctypes.sizeof(memory)
 assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
 assert memory.available>=3*2**30,'Unchanged fresh3GiB scientific feature guard'
 return memory.available

def run():
 fresh_guard();mpath=OUT/'feature_manifest.json';m=read(mpath)
 assert subprocess.check_output(['git','show','HEAD:'+mpath.relative_to(ROOT).as_posix()],cwd=ROOT)==mpath.read_bytes()
 for rel,digest in m['files'].items():assert sha(ROOT/rel)==digest,rel
 rows={x['source_excel_row']:x for x in read(ROOT/m['source_design'])['rows']}
 parents=read(ROOT/m['parents']);points=read(ROOT/m['points']);assert len(parents)==16 and len(points)==4054
 params=load_parameters();production_files=[];start=time.monotonic();scored=0
 for index,parent in enumerate(parents):
  fresh_guard();path=OUT/('background_'+str(index).zfill(2)+'_fixed_sequence_features.json')
  group=[x for x in points if x['parent_excel_row']==parent['source_excel_row']]
  expected={parent['source_excel_row']}|{x['source_variant_excel_row'] for x in group}
  assert len(expected)==len(group)+1
  if path.exists():
   prior=read(path);assert prior['feature_manifest_sha256']==sha(mpath) and prior['prefix']==parent['prefix']
   assert {x['source_excel_row'] for x in prior['sequence_scores']}==expected
   assert len(prior['point_delta_logZ'])==len(group)
   for item in prior['sequence_scores']:
    assert item['sequence_sha256']==hashlib.sha256(rows[item['source_excel_row']]['Sequence'].encode()).hexdigest()
   scored+=len(expected);production_files.append(path);print(parent['prefix'],'existing feature checkpoint preserved',flush=True);continue
  records=[];byindex={}
  for i in sorted(expected):
   row=rows[i];assert len(row['Sequence'])==140 and set(row['Sequence'])<=set('ACGT')
   result={mode:score(row['Sequence'],params,mode) for mode in MODES}
   for mode,x in result.items():
    assert x['available'] and x['state_count']==(132 if mode in ('no_flip_no_c1c2','coupled_consecutive') else 1696)
    assert all(math.isfinite(x[key]) for key in ('logZ','relative_ensemble_energy_kcal','best_state_energy_kcal'))
   record={'source_excel_row':i,'source_ID':row['ID'],'sequence_sha256':hashlib.sha256(row['Sequence'].encode()).hexdigest(),'fixed_mode_scores':result}
   records.append(record);byindex[i]=result
  deltas=[]
  for point in group:
   i=point['source_variant_excel_row'];j=point['parent_excel_row']
   deltas.append({'source_variant_ID':point['source_variant_ID'],'source_variant_excel_row':i,'source_parent_ID':point['source_parent_ID'],'parent_excel_row':j,
    'lineage_nominal':point['lineage'],'mPRE_background':point['mPRE_background'],
    'delta_logZ':{mode:byindex[i][mode]['logZ']-byindex[j][mode]['logZ'] for mode in MODES},'is_localization_prediction':False,'training_pair_admitted':False})
  save(path,{'feature_manifest_sha256':sha(mpath),'prefix':parent['prefix'],'sequence_scores':records,'point_delta_logZ':deltas,
   'only_four_delta_logZ_features_for_possible_future_training':True,'energy_and_logZ_are_redundant_not_extra_training_columns':True,
   'no_outcome_or_expression_values_read':True,'source_context_is_available140nt_fragment_only':True,'models_fit':0})
  production_files.append(path);scored+=len(expected);print(parent['prefix'],len(expected),'fixed sequence features complete',flush=True)
 assert scored==4070
 save(OUT/'feature_production_receipt.json',{'status':'COMPLETE_FIXED_PUM2_POINT_FRAGMENT_FEATURES_ONLY_NOT_LOCALIZATION_OR_TRAINING_ADMISSION',
  'feature_manifest_sha256':sha(mpath),'sequence_rows':scored,'point_rows':4054,'backgrounds':16,'nominal_lineages':7,'fixed_mode_features':list(MODES),
  'temperature_C':25,'fitted_biological_parameters':0,'binding_or_localization_labels_read':False,'independent_production_numeric_replay_pending':True,
  'all_existing_model_feature_floors_unchanged':True,'models_fit':0,'training_pairs_admitted':0,'elapsed_seconds':time.monotonic()-start,
  'files':{p.relative_to(ROOT).as_posix():sha(p) for p in production_files}})
 print('FEATURES_ONLY_COMPLETE',scored,flush=True)
if __name__=='__main__':run()
