"""Separate original-unit normal equations and direct crossed-ratio replay."""
from . import pipeline as gate
from . import contracts as c
import gzip,json,math,random
ROOT=c.ROOT;OUT=c.OUT
def independent_targets(rows,raw,protein,view):
 pc,ip,inp=view
 ips=('1','2') if ip=='mean' else (ip,);inputs=('1','2') if inp=='mean' else (inp,)
 result=[]
 for row in rows:
  effects=[]
  for i in ips:
   for j in inputs:
    mut=raw[row['source_variant_excel_row']]['raw_counts'];parent=raw[row['parent_excel_row']]['raw_counts']
    effects.append(math.log2((mut[protein+'_IP_'+i+'.raw']['value']+pc)/(mut['Input_'+j+'.raw']['value']+pc))
     -math.log2((parent[protein+'_IP_'+i+'.raw']['value']+pc)/(parent['Input_'+j+'.raw']['value']+pc)))
  result.append(math.fsum(effects)/len(effects))
 return result
def macro(rows,truth,pred):
 backgrounds={}
 for r,y,p in zip(rows,truth,pred):backgrounds.setdefault((r['lineage'],r['parent_excel_row']),[]).append(abs(y-p))
 genes={}
 for (g,b),values in backgrounds.items():genes.setdefault(g,[]).append(math.fsum(values)/len(values))
 gene={g:math.fsum(values)/len(values) for g,values in genes.items()}
 return math.fsum(gene.values())/len(gene),gene
def replay_fit(np,x,y,w,fit,penalty):
 scales=np.asarray(fit['scale']);b=np.asarray(fit['scaled_coefficients']);active=np.asarray(fit['active_columns'])
 rms=np.sqrt(np.einsum('i,ij,ij->j',w,x,x));expected=np.where(rms>0,rms,1.)
 assert np.array_equal(active,rms>0) and np.all(b[~active]==0)
 assert np.max(np.abs(scales-expected))<=1e-10
 # Work in original feature units: beta=b/scale, penalty=lambda*scale^2*beta.
 beta=b/scales;pred=np.einsum('ij,j->i',x,beta)
 residual=np.einsum('i,ij,i->j',w,x,y-pred)-penalty*scales*b
 maximum=float(np.max(np.abs(residual)));assert maximum<=1e-9,maximum
 scaled_residual=residual/scales
 reference=np.einsum('i,ij,i->j',w,x,y)/scales
 relative=float(np.max(np.abs(scaled_residual)))/(1.+float(np.max(np.abs(reference)))+float(np.max(np.abs(penalty*b))))
 assert relative<=1e-10,'Independent scaled-coordinate stationarity failed'
 return beta,maximum
def run():
 np,proof=gate.numpy_runtime();m,data,rows,raw,rosters=gate.admitted()
 receipt=gate.read(OUT/'fit_receipt.json');assert receipt['prefit_sha256']==gate.sha(OUT/'prefit_manifest.json')
 x=np.asarray(data['kmer_delta_features']);pm=np.asarray(data['fixed_mode_delta_logZ'])
 xs={c.ARMS[0]:x,c.ARMS[1]:np.column_stack((x,pm[:,2])),c.ARMS[2]:np.column_stack((x,x[:,list(c.KMERS).index('TGT')]))}
 y=np.asarray(independent_targets(rows,raw,'PUM2',c.VIEWS[0]));models=0;values=0;max_prediction=0.;max_gradient=0.
 outer={arm:[None]*len(rows) for arm in c.ARMS};seen=set()
 for rel,h in receipt['files'].items():
  gate.fresh();path=ROOT/rel;assert gate.sha(path)==h
  record=json.loads(gzip.decompress(path.read_bytes()));held=record['held_lineage'];arm=record['arm'];roster=rosters[held];matrix=xs[arm]
  assert (held,arm) not in seen;seen.add((held,arm));scores={lam:[] for lam in c.LAMBDAS};inner_seen=set()
  for validation in record['inner_validations']:
   inner=validation['held_inner_lineage'];penalty=validation['penalty'];split=roster['inner'][inner]
   assert (inner,penalty) not in inner_seen;inner_seen.add((inner,penalty))
   ti=split['train_indices'];vi=split['validation_indices'];assert vi==validation['validation_indices']
   beta,res=replay_fit(np,matrix[ti],y[ti],np.asarray(split['train_weights']),validation['fit'],penalty)
   pred=np.einsum('ij,j->i',matrix[vi],beta);difference=float(np.max(np.abs(pred-np.asarray(validation['predictions']))))
   assert difference<=1e-9;max_prediction=max(max_prediction,difference);max_gradient=max(max_gradient,res);values+=len(vi);models+=1
   mae,per=macro([rows[i] for i in vi],y[vi].tolist(),pred.tolist());assert set(per)=={inner} and abs(mae-validation['MAE'])<=1e-10;scores[penalty].append(mae)
  assert inner_seen=={(inner,lam) for inner in roster['inner'] for lam in c.LAMBDAS}
  averaged={lam:math.fsum(values)/6 for lam,values in scores.items()}
  # Bound independent arithmetic drift, then preserve the frozen canonical
  # validation scores for exact tie selection rather than redefining it.
  canonical={lam:record['inner_macro_MAE_by_penalty'][str(lam)] for lam in c.LAMBDAS}
  assert all(abs(averaged[lam]-canonical[lam])<=1e-10 for lam in c.LAMBDAS)
  best=min(canonical.values());chosen=max(lam for lam,value in canonical.items() if value<=best+1e-12)
  assert chosen==record['chosen_penalty'] and all(abs(averaged[lam]-record['inner_macro_MAE_by_penalty'][str(lam)])<=1e-10 for lam in c.LAMBDAS)
  ti=roster['train_indices'];vi=roster['test_indices'];assert vi==record['outer_indices']
  beta,res=replay_fit(np,matrix[ti],y[ti],np.asarray(roster['train_weights']),record['outer_fit'],chosen)
  pred=np.einsum('ij,j->i',matrix[vi],beta);difference=float(np.max(np.abs(pred-np.asarray(record['outer_predictions']))))
  assert difference<=1e-9;max_prediction=max(max_prediction,difference);max_gradient=max(max_gradient,res);models+=1;values+=len(vi)
  for i,p in zip(vi,pred.tolist()):assert outer[arm][i] is None;outer[arm][i]=p
 assert seen=={(held,arm) for held in rosters for arm in c.ARMS} and models==399
 evaluation=gate.read(OUT/'evaluation_results.json');per_primary={}
 for protein in ('PUM2','PUM1'):
  for view in c.VIEWS:
   name=c.view_name(view);target=independent_targets(rows,raw,protein,view)
   for arm,pred in {**outer,'zero_effect':[0.]*len(rows)}.items():
    mae,per=macro(rows,target,pred);expected=evaluation['MAE_all18_views_both_proteins'][protein][name][arm]
    assert abs(mae-expected['macro_MAE'])<=1e-10 and set(per)==set(expected['per_lineage_MAE'])
    assert all(abs(value-expected['per_lineage_MAE'][g])<=1e-10 for g,value in per.items())
    if protein=='PUM2' and name==c.PRIMARY:per_primary[arm]=per
 comparisons=evaluation['primary_comparisons'];genes=sorted(per_primary[c.ARMS[1]]);rng=random.Random(20261009)
 draws=[[rng.randrange(7) for _ in range(7)] for _ in range(10000)];passes=[]
 for arm in (c.ARMS[0],c.ARMS[2]):
  actual=comparisons[arm];delta=[per_primary[arm][g]-per_primary[c.ARMS[1]][g] for g in genes]
  gain=math.fsum(delta)/7;baseline=math.fsum(per_primary[arm].values())/7;relative=None if baseline<=1e-12 else gain/baseline
  best=min(range(7),key=lambda i:(-delta[i],genes[i]));leave=math.fsum(delta[i] for i in range(7) if i!=best)/6
  samples=sorted(math.fsum(delta[i] for i in draw)/7 for draw in draws)
  bounds=[]
  for q in (.025,.975):
   position=(len(samples)-1)*q;i=int(position);bounds.append(samples[i]+(samples[min(i+1,len(samples)-1)]-samples[i])*(position-i))
  assert abs(gain-actual['macro_MAE_gain'])<=1e-10 and abs(leave-actual['leave_best_lineage_out_gain'])<=1e-10
  assert all(abs(a-b)<=1e-10 for a,b in zip(bounds,actual['paired_lineage_bootstrap95']))
  sensitivity=[]
  for view in c.VIEWS[1:]:
   target=independent_targets(rows,raw,'PUM2',view);_,a=macro(rows,target,outer[arm]);_,b=macro(rows,target,outer[c.ARMS[1]])
   g=math.fsum(a[lineage]-b[lineage] for lineage in genes)/7;sensitivity.append(g)
   assert abs(g-actual['all17_sensitivity_MAE_gains'][c.view_name(view)])<=1e-10
  passed=relative is not None and relative>=.05 and sum(v>1e-12 for v in delta)>=5 and leave>0 and bounds[0]>0 and all(v>0 for v in sensitivity)
  assert passed==actual['criterion_pass'];passes.append(passed)
 verdict=gate.read(OUT/'provisional_verdict.json')
 assert verdict['status']==('PROVISIONAL_BINDING_SUPPORT' if all(passes) else 'NO_GO_FOR_DECLARED_POOLED_BINDING_ROBUSTNESS_CRITERION')
 gate.save(OUT/'independent_model_score_and_gate_replay_receipt.json',{'status':'PASS_ALL399_NORMAL_EQUATIONS_SCORES_TARGET_VIEWS_AND_PRIMARY_GATE_REPLAY',
  'fit_receipt_sha256':gate.sha(OUT/'fit_receipt.json'),'evaluation_sha256':gate.sha(OUT/'evaluation_results.json'),'verdict_sha256':gate.sha(OUT/'provisional_verdict.json'),
  'models_verified_without_refitting':models,'stored_predictions_compared':values,'maximum_prediction_difference':max_prediction,'maximum_original_unit_gradient_residual':max_gradient,
  'all18_target_views_both_proteins_replayed':True,'training_RMS_and_zero_support_replayed':True,'source_only_selection_replayed':True,'bootstrap_draws_shared_across_controls':True,
  'production_fit_target_macro_and_gate_helpers_used':False,'admission_and_runtime_functions_shared':True,'same_root_runtime_not_independent_agent_execution':True,
  'localization_generalization_pass':False,'numpy_runtime_proof':proof})
 print('ALL399_MODEL_SCORE_AND_GATE_REPLAY_PASS',flush=True)
if __name__=='__main__':run()
