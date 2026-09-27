"""Read-only numerical replay and preservation audit; no new scientific test."""
from .common import *
from collections import Counter
from .features import matrices,disjoint_train
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import subprocess,sys

def run():
    freeze=assert_frozen();checks={};old=[]
    for name in ['artifacts/srle_synthesis_20260926/delivery_receipt.json','artifacts/small_edit_20260925/delivery_receipt.json','artifacts/small_edit_20260925/srle_prediction_delivery_receipt.json']:
        receipt=readj(ROOT/name)
        for path,entry in receipt['manifest'].items():assert sha256(ROOT/path)==entry['sha256'],path
        assert sha256(ROOT/receipt['archive'])==receipt['sha256']
        old.append({'receipt':name,'preserved_files':len(receipt['manifest']),'archive_sha256':receipt['sha256']})
    checks['historical_bundles']=old
    pre=pd.read_csv(ART/'GSE330741_prefit_predictions_without_outcomes.csv',float_precision='round_trip');w=readj(OUT/'source_predictor.json')
    def counts(s):
        c=Counter(s[i:i+k] for k in (1,2,3) for i in range(len(s)-k+1));return np.array([c[t] for t in WORDS])
    parents={s:counts(s) for s in pre.parent_sequence.unique()};dx=np.array([counts(m)-parents[p] for p,m in zip(pre.parent_sequence,pre.mutant_sequence)])
    assert np.array_equal(dx,pre[['delta_'+t for t in WORDS]].to_numpy())
    source_pred=dx[:,:4]@np.array(w['composition_beta'])+dx[:,4:20]@np.array(w['order_beta']['2mer'])
    assert np.allclose(source_pred,pre.srle_2mer_full,atol=1e-14,rtol=0)
    checks['prefit_source_predictions_replayed']=len(pre)
    frame=pd.read_csv(ART/'GSE330741_leave_parent_out_predictions.csv',float_precision='round_trip');xs=matrices(frame)
    fits=readj(OUT/'test_b_fits.json');sel=pd.read_csv(OUT/'test_b_inner_selection.csv');maxerror=0.
    for fit in fits:
        held=fit['held_parent'];model=fit['model'];tr=disjoint_train(frame,held);te=frame.parent_id.eq(held).to_numpy();x=xs[model]
        labels=sorted(frame.loc[tr,'parent_id'].unique());assert labels==fit['training_parents']
        counts_p=frame.loc[tr,'parent_id'].value_counts();n=tr.sum();p=frame.loc[tr,'parent_id'].to_numpy()
        nuisance=np.column_stack([(p==label).astype(float)-counts_p[label]/n for label in labels])
        tx=np.column_stack([x[tr],nuisance]);vx=np.column_stack([x[te],np.zeros((te.sum(),len(labels)))])
        scaler=StandardScaler().fit(tx);weights=np.array([n/(len(labels)*counts_p[label]) for label in p])
        reg=Ridge(alpha=fit['alpha']).fit(scaler.transform(tx),frame.loc[tr,'observed_delta'],sample_weight=weights)
        fresh=reg.predict(scaler.transform(vx));error=float(np.max(abs(fresh-frame.loc[te,model])));maxerror=max(maxerror,error);assert error<1e-12
        choices=sel[sel.held_parent.eq(held)&sel.model.eq(model)]
        assert set(choices.inner_parent)==set(labels)
        avg=choices.groupby('alpha').mse.mean();assert fit['alpha']==max(a for a in avg.index if avg[a]<=avg.min()+TOL)
    checks.update(fresh_outer_model_fits=len(fits),max_prediction_replay_error=maxerror)
    comparisons=0;candidate_checks=0
    for stage,file in [('test_a','GSE330741_zero_shot_predictions.csv'),('test_b','GSE330741_leave_parent_out_predictions.csv')]:
        f=pd.read_csv(ART/file,float_precision='round_trip');f=f[f.qc_status.eq('VERIFIED')]
        metrics=pd.read_csv(OUT/(stage+'_parent_metrics.csv'));decisions=pd.read_csv(OUT/(stage+'_decisions.csv'))
        for row in metrics.itertuples():
            g=f[f.parent_id.eq(row.parent_id)].sort_values('element');y=g.observed_delta;p=g[row.model]
            rho=0. if np.ptp(p)<=TOL else np.corrcoef(y.rank(),p.rank())[0,1]
            assert abs(rho-row.spearman)<1e-12 and abs(np.mean((y-p)**2)-row.mse)<1e-12;comparisons+=1
            for d in (-1,1):
                choice=g.assign(score=d*p).sort_values(['score','element'],ascending=[False,True]).iloc[0]
                r=decisions[decisions.parent_id.eq(row.parent_id)&decisions.model.eq(row.model)&decisions.direction.eq(d)].iloc[0]
                regret=((d*y).max()-d*choice.observed_delta)/np.ptp(y)
                assert choice.element==r.selected and abs(regret-r.regret)<1e-12
                assert int(d*choice.observed_delta < -TOL)==r.wrong_direction;candidate_checks+=1
        summary=pd.read_csv(OUT/(stage+'_metrics.csv'))
        for r in summary.itertuples():assert abs(metrics[metrics.model.eq(r.model)].spearman.mean()-r.spearman)<1e-12
        # Independently reconstruct the primary contrast's component resampling and sign-flip.
        primary=config()['test_a_primary_model' if stage=='test_a' else 'test_b_primary_model']
        base='srle_composition' if stage=='test_a' else 'simple_full'
        m=metrics.pivot(index=['parent_id','overlap_component'],columns='model',values='spearman').reset_index();m['gain']=m[primary]-m[base]
        clusters=sorted(m.overlap_component.unique());arrays=[m.loc[m.overlap_component.eq(c),'gain'].to_numpy() for c in clusters]
        draws=np.random.default_rng(SEED).integers(0,len(clusters),(10000,len(clusters)))
        boot=np.array([sum(arrays[j].sum() for j in ix)/sum(len(arrays[j]) for j in ix) for ix in draws]);interval=np.quantile(boot,[.025,.975])
        values=[sum(s*a.sum() for s,a in zip(ss,arrays))/len(m) for ss in itertools.product([-1,1],repeat=len(arrays))]
        pval=np.mean(np.array(values)>=m.gain.mean()-TOL)
        saved=pd.read_csv(OUT/(stage+'_contrasts.csv'));r=saved[saved.baseline.eq(base)&saved.metric.eq('spearman_gain')].iloc[0]
        assert np.allclose(interval,[r.ci_low,r.ci_high],atol=1e-12,rtol=0) and pval==r.one_sided_block_signflip_p
    checks.update(parent_model_metric_replays=comparisons,chosen_candidate_replays=candidate_checks,primary_uncertainty_replays=2)
    test=subprocess.run([sys.executable,'-u','-m','src.generalization_20260926.test_prefit'],cwd=ROOT,capture_output=True,text=True);assert test.returncode==0
    save(OUT/'verification_scoped_tests.txt',(test.stdout+test.stderr).encode())
    checks.update(status='PASS',prefit_hashes_unchanged=len(freeze['files']),tests=12,scientific_model_selection_repeated=False,protected_data_opened=False,raw_or_source_outcomes_reopened=False)
    jsave(OUT/'verification_receipt.json',checks);print(clean(checks))

if __name__=='__main__':run()
