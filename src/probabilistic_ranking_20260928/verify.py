from .common import *
from .models import fit_all_inputs,fit_method
from src.cross_assay_20260927.models import purge
from src.cross_assay_20260927.run import safe_id
import sys

def run():
    freeze=frozen();assert readj(OUT/'run_complete.json')['status']=='PASS';frame,x,r,pairs=load();ix={v:i for i,v in enumerate(frame.intervention_id)};pred=pd.read_csv(OUT/'predictions.csv',float_precision='round_trip');prob=pd.read_csv(ART/'pairwise_probabilities.csv',float_precision='round_trip');errors=[];fresh=[]
    for study in STUDIES:
        test=frame.dataset.eq(study).to_numpy();train=purge(frame,~test,test);fold=safe_id('held_assay|'+study);inp=fit_all_inputs(frame,x,r,pairs,train)
        for name in PRIMARY+SECONDARY:
            m=readj(OUT/'fits'/(fold+'_'+name+'.json'));assert study not in m['training_studies'];assert not set(m['training_components'])&set(frame.loc[test,'biological_component']);z=(x-np.array(m['mean']))/np.array(m['scale']);beta=np.array(m['beta']);p=prob[prob.dataset.eq(study)&prob.model.eq(name)];a=np.array([ix[v] for v in p.left_id]);b=np.array([ix[v] for v in p.right_id]);delta=z[a]-z[b];s=delta@beta[:x.shape[1]]
            if m['kind']=='pairfree':
                cross=z[a,:17]*z[b,1:18]-z[a,1:18]*z[b,:17];s+=(cross/np.array(m['wedge_scale']))@beta[x.shape[1]:]
            if m['kind']=='hetero':
                noise=np.column_stack([np.ones(len(delta)),abs(delta[:,:18])]);sigma=np.clip(np.exp(noise@np.array(m['noise_head'])),.25,4);pp=ndtr(s/sigma)
            else:pp=expit(s)
            err=float(np.max(abs(pp-p.probability_left_beats_right.to_numpy())));assert err<1e-12;errors.append(err);assert np.max(abs(p.probability_left_beats_right+p.reverse_probability-1))<1e-12
            if m['kind']=='bt':
                saved=pred[pred.model.eq(name)&pred.dataset.eq(study)].set_index('intervention_id').loc[frame.loc[test,'intervention_id']];score=z[test]@beta;assert np.max(abs(score-saved.score.to_numpy()))<1e-10
            targets=pd.read_csv(OUT/'training_targets'/(fold+'_'+name+'.csv.gz'),float_precision='round_trip');assert set(targets.pair_id)==set(inp['pairs'].pair_id);assert abs(targets.weight.sum()-1)<1e-12
            if name in PRIMARY:
                expected={'H0':inp['hard'],'P1':inp['q1'],'P2':inp['q2'],'P3':inp['q3']}[name];np.testing.assert_allclose(targets.target,expected,rtol=0,atol=1e-14)
            if name=='P1':
                mf,_=fit_method(inp,name);error=float(np.max(abs(np.array(mf['beta'])-beta)));assert error<1e-10;fresh.append(error)
        print('Verified held study',study,flush=True)
    # Independent vectorized reconstruction of every selected primary-stage decision.
    d=pd.read_csv(OUT/'decision_metrics.csv',float_precision='round_trip');d=d[d.stage.eq('held_assay')].copy();p=pred.merge(frame[['intervention_id','measured_delta','biological_component']],on='intervention_id',validate='many_to_one');checks=[]
    for direction in (-1,1):
        selected=p.assign(utility=direction*p.score).sort_values(['model','parent_context_id','utility','intervention_id'],ascending=[True,True,False,True]).drop_duplicates(['model','parent_context_id']).set_index(['model','parent_context_id']);dd=d[d.direction.eq(direction)].set_index(['model','parent_context_id']).loc[selected.index];assert np.array_equal(selected.intervention_id.to_numpy(),dd.selected_id.to_numpy());rng=p.groupby(['model','parent_context_id']).measured_delta.agg(['min','max']).loc[selected.index];best=rng['max'].to_numpy() if direction==1 else -rng['min'].to_numpy();effect=direction*selected.measured_delta.to_numpy();reg=(best-effect)/(rng['max']-rng['min']).to_numpy();assert np.max(abs(reg-dd.regret.to_numpy()))<1e-12;wrong=effect<-TOL;feasible=best>TOL;assert np.array_equal(wrong.astype(float),dd.wrong_direction.to_numpy());assert np.array_equal((wrong&feasible).astype(float),dd.avoidable_wrong.to_numpy());checks.append(len(dd))
    comp=pd.read_csv(ART/'model_comparison.csv');core=comp[comp.stage.eq('held_assay')].set_index(['model','dataset']);independent=d.groupby(['model','dataset','biological_component']).regret.mean().groupby(['model','dataset']).mean();assert np.max(abs(independent-core.loc[independent.index,'regret']))<1e-12
    assert np.max(abs(d.wrong_direction-d.avoidable_wrong-d.unavoidable_wrong-d.neutral_only_alternative_wrong))<1e-12
    initial=readj(OUT/'initial_state.json')
    for p,h in initial['unchanged_user_files'].items():assert sha256(ROOT/p)==h
    previous=[]
    for old in initial['previous_receipts']:
        path=ROOT/old['path'];assert sha256(path)==old['sha256'];receipt=readj(path)
        for p,e in receipt['manifest'].items():assert sha256(ROOT/p)==e['sha256'],p
        assert sha256(ROOT/receipt['archive'])==receipt['sha256'];previous.append(old['members'])
    checks_run=subprocess.run([sys.executable,'-u','-m','src.probabilistic_ranking_20260928.test_scoped'],cwd=ROOT,capture_output=True,text=True);assert checks_run.returncode==0,checks_run.stderr;save(OUT/'postfit_tests.txt',(checks_run.stdout+checks_run.stderr).encode())
    jsave(OUT/'verification_receipt.json',{'status':'PASS','probability_rows_replayed':len(prob),'max_probability_error':max(errors),'selected_decisions_independently_checked':sum(checks),'macro_regret_checks':len(independent),'fresh_P1_fits':len(fresh),'fresh_fit_max_coefficient_error':max(fresh),'scoped_tests':9,'prefit_files_unchanged':len(freeze['files']),'prior_bundle_members_unchanged':previous,'unrelated_modified_files_unchanged':len(initial['unchanged_user_files']),'H0_replays':readj(OUT/'historical_H0_replay.json'),'code_sha256':sha256(Path(__file__))})
    print('Postfit verification PASS',flush=True)
if __name__=='__main__':run()
