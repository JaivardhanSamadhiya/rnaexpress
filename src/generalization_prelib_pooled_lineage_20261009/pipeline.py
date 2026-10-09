"""Staged, committed-prefit-only pooled binding development. No localization."""
from . import contracts as c
import ctypes,gzip,hashlib,importlib,json,math,os,random,subprocess,sys,time
ROOT=c.ROOT;OUT=c.OUT
PUM=ROOT/'results/generalization_pum2_fixed_math_20261008'
REPLAY=ROOT/'results/generalization_pum2_independent_replay_20261009'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x,compressed=False):
 data=(json.dumps(x,sort_keys=True,indent=None if compressed else 2,allow_nan=False)+'\n').encode()
 if compressed:data=gzip.compress(data,mtime=0)
 with p.open('xb') as f:f.write(data)
def committed(p):assert subprocess.check_output(['git','show','HEAD:'+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes(),str(p)
def fresh():
 class M(ctypes.Structure):
  _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
 m=M();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
 assert m.available>=3*2**30,'Fresh feature/model3GiB floor unchanged'
 return m.available
def implementation():
 mpath=OUT/'implementation_manifest.json';committed(mpath);m=read(mpath)
 for rel,h in m['files'].items():assert sha(ROOT/rel)==h,rel
 assert read(OUT/'synthetic_tests_receipt.json')['status']=='PASS_STANDARD_LIBRARY_CONTRACTS_ONLY'
 return m
def numpy_runtime():
 fresh()
 from src.generalization_splicebert_runtime_compatibility_20261007 import launcher
 launcher.clean_import_state();runtime=read(launcher.RUNTIME_RECEIPT);committed(launcher.RUNTIME_RECEIPT)
 assert sys.version_info[:2]==(3,12) and sys.implementation.cache_tag=='cpython-312'
 assert os.environ.get('OMP_NUM_THREADS')==os.environ.get('OPENBLAS_NUM_THREADS')=='2'
 assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1' and os.environ.get('PYTHONUTF8')=='1'
 assert sys.executable.casefold()==runtime['python_executable'].casefold()
 for rel,h in runtime['python_native_files'].items():assert sha(__import__('pathlib').Path(rel))==h
 launcher.select_prefix();np=importlib.import_module('numpy');proof=launcher.numpy_proof(np,runtime)
 fresh()
 return np,proof
def ridge(np,x,y,w,penalty):
 assert len(x)==len(y)==len(w) and abs(float(w.sum())-1)<1e-12
 scale=np.sqrt(np.sum(w[:,None]*x*x,axis=0));active=scale>0;scale=np.where(active,scale,1.)
 z=x[:,active]/scale[active];coef=np.zeros(x.shape[1],dtype=np.float64)
 if active.any():coef[active]=np.linalg.solve(z.T@(w[:,None]*z)+penalty*np.eye(int(active.sum())),z.T@(w*y))
 prediction=(x/scale)@coef
 residual=(x/scale).T@(w*(y-prediction))-penalty*coef
 assert np.max(np.abs(residual))<=1e-9 and np.all(coef[~active]==0)
 return {'scale':scale.tolist(),'scaled_coefficients':coef.tolist(),'active_columns':active.tolist(),'normal_equation_max_abs_residual':float(np.max(np.abs(residual)))}
def predict(np,x,fit):return (x/np.asarray(fit['scale']))@np.asarray(fit['scaled_coefficients'])
def numerical_contract(np):
 # Invented analytic and independently derived rank-deficient cases; no labels.
 x=np.array([[1.],[2.]]);y=np.array([3.,5.]);w=np.array([.5,.5]);fit=ridge(np,x,y,w,.5)
 scale=math.sqrt(2.5);expected=(.5*(1/scale)*3+.5*(2/scale)*5)/1.5
 assert abs(fit['scaled_coefficients'][0]-expected)<1e-12
 assert np.max(np.abs(predict(np,np.zeros((2,1)),fit)))==0
 x=np.array([[1.,1.,0.],[2.,2.,0.]]);fit=ridge(np,x,y,w,.5)
 expected_each=(.5*(1/scale)*3+.5*(2/scale)*5)/2.5
 assert max(abs(fit['scaled_coefficients'][i]-expected_each) for i in (0,1))<1e-12 and fit['scaled_coefficients'][2]==0
 assert fit['active_columns']==[True,True,False]
 return {'status':'PASS_INVENTED_WEIGHTED_RIDGE_NORMALIZATION_ZERO_SUPPORT_AND_SELF_ZERO','biological_data_read':False,'independent_analytic_expected_coefficients':True}
def metadata(m):
 parents=read(ROOT/m['parents']);points=read(ROOT/m['points']);assert len(parents)==16 and len(points)==4054
 rows=sorted(points,key=lambda r:r['source_variant_excel_row'])
 assert len({r['source_variant_excel_row'] for r in rows})==4054 and len({r['lineage'] for r in rows})==7
 return rows
def features():
 fresh();m=implementation();np,proof=numpy_runtime()
 analytic=numerical_contract(np)
 for p in (PUM/'feature_production_receipt.json',REPLAY/'independent_feature_replay_receipt.json'):committed(p)
 production=read(PUM/'feature_production_receipt.json');replay=read(REPLAY/'independent_feature_replay_receipt.json')
 assert replay['status']=='PASS_ALL_PRODUCTION_ALLELES_DIRECT_CONTACT_AND_ORDINARY_PARTITION_REPLAY'
 assert replay['feature_production_receipt_sha256']==sha(PUM/'feature_production_receipt.json')
 assert production['sequence_rows']==4070 and production['point_rows']==4054 and production['files']==replay['files']
 scored={}
 for rel,h in production['files'].items():
  path=ROOT/rel;assert sha(path)==h
  for record in read(path)['point_delta_logZ']:
   i=record['source_variant_excel_row'];assert i not in scored;scored[i]=record
 rows=metadata(m);source={x['source_excel_row']:x for x in read(ROOT/m['design'])['rows']}
 x=[];pum_modes=[]
 for row in rows:
  i=row['source_variant_excel_row'];j=row['parent_excel_row'];mut=source[i];parent=source[j]
  assert mut['ID']==row['source_variant_ID'] and parent['ID']==row['source_parent_ID'] and scored[i]['parent_excel_row']==j
  assert hashlib.sha256(mut['Sequence'].encode()).hexdigest()==row['variant_sequence_sha256']
  assert sum(a!=b for a,b in zip(mut['Sequence'],parent['Sequence']))==1 and len(mut['Sequence'])==len(parent['Sequence'])==140
  x.append(c.delta_vector(parent['Sequence'],mut['Sequence']));pum_modes.append([scored[i]['delta_logZ'][mode] for mode in c.MODES])
 matrix=np.array(x,dtype=np.float64);pm=np.array(pum_modes,dtype=np.float64);assert matrix.shape==(4054,84) and pm.shape==(4054,4)
 assert np.isfinite(matrix).all() and np.isfinite(pm).all()
 span={}
 for held in sorted({r['lineage'] for r in rows}):
  fresh();indices=[i for i,r in enumerate(rows) if r['lineage']!=held];w=np.asarray(c.weights([rows[i] for i in indices]))
  a=matrix[indices];b=pm[indices,2];rootw=np.sqrt(w)
  coeff,_,rank,_=np.linalg.lstsq(a*rootw[:,None],b*rootw,rcond=1e-12)
  residual=b-a@coeff
  span[held]={'training_only_kmer_rank':int(rank),'PUM2_weighted_RMS':float(np.sqrt(np.sum(w*b*b))),
   'PUM2_outside_kmer_span_weighted_RMS':float(np.sqrt(np.sum(w*residual*residual))),'uses_labels':False,'no_extra_span_threshold':1e-10}
 path=OUT/'fixed_feature_roster.json.gz'
 save(path,{'rows':rows,'kmer_columns':list(c.KMERS),'kmer_delta_features':x,'fixed_mode_columns':list(c.MODES),'fixed_mode_delta_logZ':pum_modes},True)
 save(OUT/'feature_receipt.json',{'status':'PASS_MATCHED_FEATURES_AND_NUMERICAL_CONTRACTS_NO_LABELS','rows':4054,'backgrounds':16,'nominal_lineages':7,
  'files':{path.relative_to(ROOT).as_posix():sha(path)},'numpy_runtime_proof':proof,'numerical_contract':analytic,'train_only_span_checks':span,
  'fixed_feature_production_sha256':sha(PUM/'feature_production_receipt.json'),'independent_replay_sha256':sha(REPLAY/'independent_feature_replay_receipt.json'),'labels_read':False,'models_fit':0})
 print('MATCHED_FEATURES_READY_NO_LABELS',flush=True)
def prefit():
 fresh();m=implementation();receipt=OUT/'feature_receipt.json';committed(receipt);f=read(receipt)
 assert f['status']=='PASS_MATCHED_FEATURES_AND_NUMERICAL_CONTRACTS_NO_LABELS'
 for rel,h in f['files'].items():assert sha(ROOT/rel)==h
 rows=metadata(m);genes=sorted({r['lineage'] for r in rows});rosters={}
 for held in genes:
  training=[i for i,r in enumerate(rows) if r['lineage']!=held];testing=[i for i,r in enumerate(rows) if r['lineage']==held]
  rosters[held]={'train_indices':training,'test_indices':testing,'train_weights':c.weights([rows[i] for i in training]),'inner':{}}
  for inner in genes:
   if inner==held:continue
   ti=[i for i in training if rows[i]['lineage']!=inner];vi=[i for i in training if rows[i]['lineage']==inner]
   rosters[held]['inner'][inner]={'train_indices':ti,'validation_indices':vi,'train_weights':c.weights([rows[i] for i in ti])}
 path=OUT/'fold_and_weight_roster.json';save(path,rosters)
 files=dict(m['files']);files.update(f['files'])
 for p in (OUT/'implementation_manifest.json',receipt,path):files[p.relative_to(ROOT).as_posix()]=sha(p)
 save(OUT/'prefit_manifest.json',{'status':'FROZEN_PREFIT_POST_EXPOSURE_BINDING_DEVELOPMENT','files':files,'features_sha256':sha(OUT/'fixed_feature_roster.json.gz'),
  'rosters_sha256':sha(path),'primary_target':c.PRIMARY,'primary_protein':'PUM2','arms':list(c.ARMS),'penalties':list(c.LAMBDAS),'inner_fits':378,'outer_fits':21,
  'target_views':[c.view_name(v) for v in c.VIEWS],'uncertainty_is_seven_lineages_fixed_predictions_only':True,'unknown_lysate_pairing_remains':True,'localization_prediction':False,'models_fit':0})
 print('PREFIT_WRITTEN_ROOT_COMMIT_REQUIRED_BEFORE_FITS',flush=True)
def admitted():
 fresh();implementation();p=OUT/'prefit_manifest.json';committed(p);m=read(p)
 assert m['status']=='FROZEN_PREFIT_POST_EXPOSURE_BINDING_DEVELOPMENT'
 for rel,h in m['files'].items():assert sha(ROOT/rel)==h,rel
 data=json.loads(gzip.decompress((OUT/'fixed_feature_roster.json.gz').read_bytes()))
 rows=data['rows'];raw={x['source_excel_row']:x for x in read(ROOT/'results/generalization_prelib_binding_descriptive_20261008/selected_raw_count_rows.json')['rows']}
 for row in rows:
  for i,ident in ((row['source_variant_excel_row'],row['source_variant_ID']),(row['parent_excel_row'],row['source_parent_ID'])):assert raw[i]['ID']==ident and raw[i]['sequence_sha256']==hashlib.sha256(raw[i]['Sequence'].encode()).hexdigest()
 return m,data,rows,raw,read(OUT/'fold_and_weight_roster.json')
def matrices(np,data):
 x=np.asarray(data['kmer_delta_features']);p=np.asarray(data['fixed_mode_delta_logZ'])[:,2,None]
 result={c.ARMS[0]:x,c.ARMS[1]:np.concatenate([x,p],axis=1),c.ARMS[2]:np.concatenate([x,x[:,c.KMERS.index('TGT'),None]],axis=1)}
 assert all(np.isfinite(a).all() for a in result.values()) and [a.shape[1] for a in result.values()]==[84,85,85]
 return result
def fit():
 fresh();np,proof=numpy_runtime();m,data,rows,raw,rosters=admitted()
 numerical_contract(np);targets=c.targets(rows,raw,'PUM2');y=np.asarray(targets[c.PRIMARY]);xs=matrices(np,data);completed=[]
 for held,roster in rosters.items():
  for arm,x in xs.items():
   fresh();path=OUT/('fit_'+held+'_'+arm+'.json.gz')
   if path.exists():raise RuntimeError('Preserve partial fit checkpoint; review explicitly before any resumed fit')
   validations=[];pooled={lam:[] for lam in c.LAMBDAS}
   for inner,split in roster['inner'].items():
    ti=split['train_indices'];vi=split['validation_indices'];w=np.asarray(split['train_weights'])
    for lam in c.LAMBDAS:
     fresh();trained=ridge(np,x[ti],y[ti],w,lam);pred=predict(np,x[vi],trained)
     mae,per=c.macro_errors([rows[i] for i in vi],y[vi].tolist(),pred.tolist());assert set(per)=={inner}
     pooled[lam].append(mae);validations.append({'held_inner_lineage':inner,'penalty':lam,'fit':trained,'validation_indices':vi,'predictions':pred.tolist(),'MAE':mae})
   scores={lam:math.fsum(values)/6 for lam,values in pooled.items()};chosen=c.choose_lambda(scores)
   ti=roster['train_indices'];vi=roster['test_indices'];trained=ridge(np,x[ti],y[ti],np.asarray(roster['train_weights']),chosen)
   pred=predict(np,x[vi],trained)
   save(path,{'prefit_sha256':sha(OUT/'prefit_manifest.json'),'held_lineage':held,'arm':arm,'inner_validations':validations,
    'inner_macro_MAE_by_penalty':{str(lam):v for lam,v in scores.items()},'chosen_penalty':chosen,'outer_fit':trained,'outer_indices':vi,'outer_predictions':pred.tolist(),
    'same_fitted_predictions_for_every_target_view':True,'no_localization_prediction':True},True)
   completed.append(path);print('FIT_COMPLETE',held,arm,flush=True)
 assert len(completed)==21
 save(OUT/'fit_receipt.json',{'status':'COMPLETE_399_NESTED_FITS_POST_EXPOSURE_POOLED_BINDING_ONLY','inner_fits':378,'outer_fits':21,'numpy_runtime_proof':proof,
  'files':{p.relative_to(ROOT).as_posix():sha(p) for p in completed},'prefit_sha256':sha(OUT/'prefit_manifest.json'),'PUM1_used_for_fitting':False,'models_admitted_for_localization':0})
def evaluate():
 m,data,rows,raw,rosters=admitted();f=read(OUT/'fit_receipt.json');assert f['status']=='COMPLETE_399_NESTED_FITS_POST_EXPOSURE_POOLED_BINDING_ONLY'
 predictions={arm:[None]*4054 for arm in c.ARMS}
 for rel,h in f['files'].items():
  path=ROOT/rel;assert sha(path)==h;result=json.loads(gzip.decompress(path.read_bytes()))
  assert result['prefit_sha256']==sha(OUT/'prefit_manifest.json')
  for i,v in zip(result['outer_indices'],result['outer_predictions']):assert predictions[result['arm']][i] is None;predictions[result['arm']][i]=v
 assert all(all(v is not None and math.isfinite(v) for v in p) for p in predictions.values())
 primary={};all_results={};menus=[]
 for protein in ('PUM2','PUM1'):
  target=c.targets(rows,raw,protein);values={}
  for view,truth in target.items():
   values[view]={}
   for arm,pred in predictions.items():
    mae,per=c.macro_errors(rows,truth,pred);values[view][arm]={'macro_MAE':mae,'per_lineage_MAE':per}
   mae,per=c.macro_errors(rows,truth,[0.]*4054);values[view]['zero_effect']={'macro_MAE':mae,'per_lineage_MAE':per}
  all_results[protein]=values
  truth=target[c.PRIMARY]
  for arm,pred in predictions.items():
   for background in sorted({r['parent_excel_row'] for r in rows}):
    indices=[i for i,r in enumerate(rows) if r['parent_excel_row']==background]
    menus.append({'protein':protein,'arm':arm,'lineage':rows[indices[0]]['lineage'],'parent_excel_row':background,**c.menu_metrics([rows[i]['source_variant_ID'] for i in indices],[truth[i] for i in indices],[pred[i] for i in indices])})
 primary=all_results['PUM2'][c.PRIMARY];candidate=primary[c.ARMS[1]]['per_lineage_MAE']
 comparisons={arm:c.comparison(candidate,primary[arm]['per_lineage_MAE']) for arm in (c.ARMS[0],c.ARMS[2])}
 genes=sorted(candidate);rng=random.Random(20261009);draws=[[rng.randrange(7) for _ in range(7)] for _ in range(10000)]
 for arm,record in comparisons.items():
  deltas=[record['lineage_gains'][g] for g in genes];sampled=[math.fsum(deltas[i] for i in draw)/7 for draw in draws]
  record['paired_lineage_bootstrap95']= [c.quantile(sampled,.025),c.quantile(sampled,.975)]
  sensitivities={}
  for view,values in all_results['PUM2'].items():
   if view==c.PRIMARY:continue
   sensitivities[view]=c.comparison(values[c.ARMS[1]]['per_lineage_MAE'],values[arm]['per_lineage_MAE'])['macro_MAE_gain']
  record['all17_sensitivity_MAE_gains']=sensitivities
  record['criterion_pass']=record['relative_MAE_gain'] is not None and record['relative_MAE_gain']>=.05 and record['improved_lineages']>=5 and record['leave_best_lineage_out_gain']>0 and record['paired_lineage_bootstrap95'][0]>0 and all(x>0 for x in sensitivities.values())
 fixed=[]
 for k,mode in enumerate(c.MODES):
  pred=[x[k]/math.log(2) for x in data['fixed_mode_delta_logZ']]
  truth=c.targets(rows,raw,'PUM2')[c.PRIMARY]
  for background in sorted({r['parent_excel_row'] for r in rows}):
   indices=[i for i,r in enumerate(rows) if r['parent_excel_row']==background]
   fixed.append({'mode':mode,'protein':'PUM2','lineage':rows[indices[0]]['lineage'],'parent_excel_row':background,**c.menu_metrics([rows[i]['source_variant_ID'] for i in indices],[truth[i] for i in indices],[pred[i] for i in indices])})
 save(OUT/'evaluation_results.json',{'post_exposure_development':True,'MAE_all18_views_both_proteins':all_results,'primary_comparisons':comparisons,'primary_menu_metrics':menus,'fixed_operator_rank_only_metrics':fixed,
  'bootstrap_scope':'Seven observed lineages, fixed nested predictions; no biological replicate or selection uncertainty','PUM1_descriptive_not_selection_or_rescue':True,'matched_lysate_pairing_unknown':True})
 save(OUT/'provisional_verdict.json',{'status':'PROVISIONAL_BINDING_SUPPORT' if all(x['criterion_pass'] for x in comparisons.values()) else 'NO_GO_FOR_DECLARED_POOLED_BINDING_ROBUSTNESS_CRITERION',
  'independent_verification_pending':True,'evaluation_sha256':sha(OUT/'evaluation_results.json'),'localization_generalization_pass':False,'independent_confirmation':False,'novelty_certified':False})
 print('PROVISIONAL_BINDING_EVALUATION_ONLY',flush=True)
def main():
 assert sys.argv[1:] and sys.argv[1] in ('features','prefit','fit','evaluate')
 {'features':features,'prefit':prefit,'fit':fit,'evaluate':evaluate}[sys.argv[1]]()
if __name__=='__main__':main()
