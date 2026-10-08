"""Declared post-exposure normalization sensitivities, with every cohort record retained."""
from pathlib import Path
import collections,hashlib,json,math,statistics,subprocess
ROOT=Path(__file__).resolve().parents[2];NS='generalization_prelib_binding_descriptive_20261008';OUT=ROOT/'results'/NS

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def adjusted(grid):
 assert len(grid)==2 and all(len(line)==2 for line in grid)
 perIP=[math.fsum(line)/2 for line in grid]
 perInput=[math.fsum(grid[i][j] for i in range(2))/2 for j in range(2)]
 return perIP,perInput

def run():
 path=OUT/'input_sensitivity_manifest.json';m=json.loads(path.read_text())
 assert subprocess.check_output(['git','show','HEAD:'+path.relative_to(ROOT).as_posix()],cwd=ROOT)==path.read_bytes()
 for rel,digest in m['files'].items():assert sha(ROOT/rel)==digest,rel
 effects=json.loads((OUT/'descriptive_point_association_effects.json').read_text());assert len(effects)==4054
 records=[];groups=collections.defaultdict(list)
 for e in effects:
  data={}
  for protein in ('PUM1','PUM2'):
   data[protein]={}
   for pseudo in ('0.5','1.0'):
    x=e['association_effects'][protein][pseudo]
    if x['complete']:
     perIP,perInput=adjusted(x['crossed_input_deltas']);assert abs(math.fsum(perIP)/2-x['delta_mean_log_enrichment'])<1e-12
     data[protein][pseudo]={'perIP_common_meanInput_delta':perIP,'perInput_common_meanIP_delta':perInput,
      'perIP_strict_sign_disagreement':perIP[0]*perIP[1]<0,'perInput_strict_sign_disagreement':perInput[0]*perInput[1]<0,
      'effect_range_across_Input_choices':abs(perInput[0]-perInput[1]),'effect_range_across_IP_choices':abs(perIP[0]-perIP[1])}
    else:data[protein][pseudo]=None
  record={'source_variant_ID':e['source_variant_ID'],'source_variant_excel_row':e['source_variant_excel_row'],
   'parent_excel_row':e['parent_excel_row'],'lineage_nominal':e['lineage_nominal'],'prefix':e['prefix'],'normalization_sensitivities':data}
  records.append(record);groups[e['lineage_nominal']].append(record)
 def summarize(group):
  result={}
  for protein in ('PUM1','PUM2'):
   result[protein]={}
   for pseudo in ('0.5','1.0'):
    valid=[x['normalization_sensitivities'][protein][pseudo] for x in group if x['normalization_sensitivities'][protein][pseudo] is not None]
    result[protein][pseudo]={'complete_rows':len(valid),'perIP_commonInput_strict_sign_disagreement':sum(x['perIP_strict_sign_disagreement'] for x in valid),
     'perInput_commonIP_strict_sign_disagreement':sum(x['perInput_strict_sign_disagreement'] for x in valid),
     'Input_choice_effect_range_median':statistics.median(x['effect_range_across_Input_choices'] for x in valid),
     'Input_choice_effect_range_max':max(x['effect_range_across_Input_choices'] for x in valid)}
  return result
 save(OUT/'all_point_input_IP_choice_sensitivities.json',records)
 result={'status':'COMPLETE_ALL_RETAINED_POINT_INPUT_IP_NORMALIZATION_SENSITIVITY_DESCRIPTIONS',
  'manifest_sha256':sha(path),'rows_retained':len(records),'overall':summarize(records),'by_nominal_lineage':{k:summarize(v) for k,v in sorted(groups.items())},
  'diagnostics_declared_after_count_exposure':True,'no_favorable_normalization_selected':True,'not_biological_replicate_agreement_or_independence':True,
  'sample_pairing_not_assumed':True,'no_cohort_filter_or_weighting':True,'models_fit':0,'training_pairs_admitted':0,
  'sensitivity_output_sha256':sha(OUT/'all_point_input_IP_choice_sensitivities.json')}
 save(OUT/'input_sensitivity_receipt.json',result);print(json.dumps({'status':result['status'],'overall':result['overall']},sort_keys=True),flush=True)
if __name__=='__main__':run()
