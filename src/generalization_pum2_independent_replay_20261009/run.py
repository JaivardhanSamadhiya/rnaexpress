"""Replay every production allele; no association or localization outcomes."""
from . import numeric as n
import ctypes,hashlib,json,math,subprocess,time
OUT=n.ROOT/'results/generalization_pum2_independent_replay_20261009'
OLD=n.ROOT/'results/generalization_pum2_fixed_math_20261008'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
def guard():
 class Memory(ctypes.Structure):
  _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
 memory=Memory();memory.length=ctypes.sizeof(memory)
 assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
 assert memory.available>=3*2**30,'Unchanged fresh3GiB feature-replay admission floor'
 return memory.available
def run():
 guard();manifest=OUT/'replay_manifest.json';m=read(manifest)
 assert subprocess.check_output(['git','show','HEAD:'+manifest.relative_to(n.ROOT).as_posix()],cwd=n.ROOT)==manifest.read_bytes()
 for rel,h in m['files'].items():assert sha(n.ROOT/rel)==h,rel
 assert read(OUT/'synthetic_tests_receipt.json')['status']=='PASS_INVENTED_CASES_WITH_FROZEN_TOLERANCE'
 receipt=read(OLD/'feature_production_receipt.json')
 assert receipt['status']=='COMPLETE_FIXED_PUM2_POINT_FRAGMENT_FEATURES_ONLY_NOT_LOCALIZATION_OR_TRAINING_ADMISSION'
 assert receipt['feature_manifest_sha256']==sha(OLD/'feature_manifest.json') and receipt['sequence_rows']==4070
 source=read(n.ROOT/m['source_design'])['rows'];rows={x['source_excel_row']:x for x in source}
 params=n.parameters();count=0;values=0;max_difference=0.;start=time.monotonic();all_points=set();files={}
 for rel,h in sorted(receipt['files'].items()):
  guard();path=n.ROOT/rel;assert sha(path)==h
  data=read(path);assert data['feature_manifest_sha256']==sha(OLD/'feature_manifest.json')
  byrow={}
  for item in data['sequence_scores']:
   row=rows[item['source_excel_row']];seq=row['Sequence']
   assert item['source_ID']==row['ID'] and item['sequence_sha256']==hashlib.sha256(seq.encode()).hexdigest() and len(seq)==140
   assert set(item['fixed_mode_scores'])==set(n.MODES)
   scored={mode:n.score(seq,params,mode) for mode in n.MODES}
   for mode,result in scored.items():
    old=item['fixed_mode_scores'][mode]
    assert old['available']==result['available'] and old['state_count']==result['state_count']==(132 if mode in n.MODES[:2] else 1696)
    for name in ('logZ','relative_ensemble_energy_kcal','best_state_energy_kcal'):
     difference=abs(old[name]-result[name]);assert difference<=m['absolute_tolerance'],(item['source_excel_row'],mode,name,difference)
     max_difference=max(max_difference,difference);values+=1
   byrow[item['source_excel_row']]=scored;count+=1
  for point in data['point_delta_logZ']:
   i=point['source_variant_excel_row'];j=point['parent_excel_row'];assert i not in all_points;all_points.add(i)
   assert point['source_variant_ID']==rows[i]['ID'] and point['source_parent_ID']==rows[j]['ID']
   for mode in n.MODES:
    independent=byrow[i][mode]['logZ']-byrow[j][mode]['logZ'];difference=abs(independent-point['delta_logZ'][mode])
    assert difference<=m['absolute_tolerance'];max_difference=max(max_difference,difference);values+=1
  files[rel]=h;print(data['prefix'],'all independent contacts and values replayed',flush=True)
 assert count==4070 and len(all_points)==4054 and len(files)==16
 save(OUT/'independent_feature_replay_receipt.json',{'status':'PASS_ALL_PRODUCTION_ALLELES_DIRECT_CONTACT_AND_ORDINARY_PARTITION_REPLAY','manifest_sha256':sha(manifest),
 'feature_production_receipt_sha256':sha(OLD/'feature_production_receipt.json'),'sequence_rows':count,'point_rows':len(all_points),'modes':list(n.MODES),
 'numerical_comparisons':values,'maximum_absolute_difference':max_difference,'absolute_tolerance':m['absolute_tolerance'],'files':files,
 'elapsed_seconds':time.monotonic()-start,'same_root_runtime_not_independent_agent_execution':True,'production_helpers_imported':False,
 'association_or_localization_labels_read':False,'models_fit':0,'training_pairs_admitted':0})
 print('ALL_FIXED_FEATURES_INDEPENDENTLY_REPLAYED',count,values,max_difference,flush=True)
if __name__=='__main__':run()
