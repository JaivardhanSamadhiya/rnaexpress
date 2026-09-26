"""Replay coefficients and candidate choices; no fits or new data."""
from .core import *
from .fit import design
import importlib
import io
import unittest
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.stats import pearsonr


def run():
    frozen=readj(OUT/'evaluation_freeze.json')
    for p,h in frozen['files'].items():assert sha256(ROOT/p)==h,p
    prior=readj(ROOT/'artifacts/small_edit_20260925/delivery_receipt.json')
    for p,v in prior['manifest'].items():assert sha256(ROOT/p)==v['sha256'],p
    from src.research_20260921.srle_clean_verification_20260925 import preservation
    protected=preservation()
    source=pd.read_csv(OUT/'sequence_inventory.csv',dtype={'group':str},float_precision='round_trip')
    pred=pd.read_csv(ART/'srle_heldout_predictions.csv',dtype={'group':str},float_precision='round_trip')
    splits=pd.read_csv(OUT/'split_inventory.csv',dtype={'held_group':str})
    xs=design(source.kmer);features_comp=counts(source.kmer);errors=[];n=0
    def reconstruct(x,c):return ((x-np.array(c['mean']))/np.array(c['scale']))@np.array(c['coefficient'])+c['intercept']
    for fit in readj(OUT/'fitted_parameters.json'):
        scheme=fit['scheme'];key=fit['held_group'];c=fit['coefficients']
        train=training_mask(source,scheme,None if key=='original_hash' else key)
        test=source.scored.to_numpy() & (True if key=='original_hash' else source.group.eq(key).to_numpy())
        record=splits[(splits.scheme==scheme)&(splits.held_group==key)].iloc[0]
        assert record.mask_sha256==hashlib.sha256(train.tobytes()+test.tobytes()).hexdigest()
        assert not np.any(train & test)
        if scheme=='purged_composition_holdout':
            assert np.min(np.abs(features_comp[train]-np.array(list(map(int,key)))).sum(1))>=6
        fallback=reconstruct(features_comp,c['composition']['unseen_composition_ridge'])
        means=c['composition']['training_class_means']
        for group,mean in means.items():assert abs(mean-source.loc[train&source.group.eq(group).to_numpy(),'nrs'].mean())<1e-12
        base=np.array([means.get(group,fallback[i]) for i,group in enumerate(source.group)])
        for model in MODELS:
            prediction=base if model in ('composition','1mer') else base+reconstruct(xs[model],c[model])
            target=pred[(pred.scheme==scheme)&(pred.held_group.astype(str)==key)&(pred.model==model)].set_index('kmer')
            observed=target.loc[source.loc[test,'kmer'],'predicted_score'].to_numpy()
            errors.append(float(np.max(np.abs(prediction[test]-observed))));n+=len(observed)
    assert max(errors)<1e-12 and n==len(pred)
    candidates=pd.read_csv(ART/'srle_candidate_selection.csv',dtype={'group':str},float_precision='round_trip')
    assert (ART/'heldout_candidate_predictions.csv').read_bytes()==(ART/'srle_candidate_selection.csv').read_bytes()
    choices=pd.read_csv(OUT/'decision_rows.csv',dtype={'group':str},float_precision='round_trip').set_index(['scheme','model','parent','direction'])
    maxregret=0.;seen=0
    for key,g in candidates.groupby(['evaluation_split','model_name','parent','direction']):
        scheme,model,parent,direction=key
        selected=g[g.selected];assert len(selected)==1
        selected=selected.iloc[0];old=choices.loc[key]
        assert selected.candidate==old.selected
        ranked=g.sort_values('predicted_rank')
        assert (np.diff(direction*ranked.predicted_delta)<=1e-12).all()
        for target,column in [('published','measured_delta'),('rep1','rep1_delta'),('rep2','rep2_delta')]:
            truth=direction*g[column].to_numpy();score=direction*selected[column]
            regret=(truth.max()-score)/np.ptp(truth)
            maxregret=max(maxregret,abs(regret-old[target+'_regret']))
        assert bool(selected.wrong_both)==bool(old.wrong_both);seen+=1
    assert maxregret<1e-12
    effects=pd.read_csv(OUT/'edit_effect_predictions.csv',dtype={'group':str},float_precision='round_trip')
    metrics=pd.read_csv(OUT/'prediction_metrics.csv',float_precision='round_trip')
    metric_errors=[]
    for (scheme,model),g in effects.groupby(['scheme','model']):
        for target in ('published','rep1','rep2'):
            y=g[target+'_delta'];p=g.predicted_delta
            expected=metrics[(metrics.kind=='edit_delta')&(metrics.scheme==scheme)&(metrics.model==model)&(metrics.target==target)].iloc[0]
            for name,value in {'mae':mean_absolute_error(y,p),'rmse':np.sqrt(mean_squared_error(y,p)),'r2':r2_score(y,p)}.items():metric_errors.append(abs(value-expected[name]))
            if np.ptp(p)>TOL:metric_errors.append(abs(pearsonr(y,p).statistic-expected.pearson))
    assert max(metric_errors)<1e-12
    suite=unittest.TestSuite()
    for package in ('research_20260921','small_edit_20260925','srle_prediction_20260926'):
        for path in sorted((ROOT/'src'/package).glob('test_*.py')):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module('src.'+package+'.'+path.stem)))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
    save(OUT/'scoped_tests.txt',stream.getvalue().encode());assert result.wasSuccessful(),stream.getvalue()
    jsave(OUT/'verification_receipt.json',{'status':'PASS','prediction_rows':n,'coefficient_replay_max_error':max(errors),
        'candidate_decisions_verified':seen,'candidate_regret_max_error':maxregret,'independent_metric_max_error':max(metric_errors),
        'purged_global_levenshtein_lower_bound':3,'whole_biological_context_overlap':1,'tests':result.testsRun,
        'protected_manifests':protected,'prior_bundle_files_unchanged':len(prior['manifest']),
        'new_models_fit':0,'scope':'Computation checks and synthetic/scoped tests, not independent biological validation'})
    print({'status':'PASS','tests':result.testsRun,'rows':n,'decisions':seen,'max_prediction_error':max(errors),'max_metric_error':max(metric_errors)})


if __name__=='__main__':run()
