"""Independent coefficient sums and direct original-truth decision metrics."""
from .common import runtime

ERRORS=['regret','wrong_direction','avoidable_wrong','no_feasible_candidate',
        'unavoidable_wrong','neutral_only_alternative_wrong']
RANKING=['pairwise_accuracy','best_recovery','top5_best_recovery']


def canonical(model,x):
    np,_,_,_,predict=runtime()
    x=np.asarray(x,dtype=float)
    beta,mean,scale=[np.asarray(model[k],dtype=float) for k in ('beta','mean','scale')]
    assert beta.shape==mean.shape==scale.shape==(x.shape[1],) and (scale>0).all()
    assert all(np.isfinite(v).all() for v in (x,beta,mean,scale))
    score=np.asarray(predict(model,x),dtype=float)
    assert score.shape==(len(x),) and np.isfinite(score).all()
    manual=np.empty(len(x));coeff=beta/scale
    for first in range(0,len(x),1024):
        last=min(first+1024,len(x));manual[first:last]=np.sum((x[first:last]-mean)*coeff,axis=1)
    error=float(np.max(abs(score-manual)))
    assert error<1e-9
    return score,error


def pair_credit(truth,score):
    np,*_=runtime();numerator=0.;denominator=0
    for i in range(len(truth)-1):
        dy=truth[i+1:]-truth[i];ds=score[i+1:]-score[i];allowed=dy!=0
        numerator+=float(np.sum((np.sign(dy[allowed])*np.sign(ds[allowed])+1)*.5));denominator+=int(allowed.sum())
    assert denominator>0;return numerator/denominator


def decisions(frame,score,ranking=True):
    np,pd,*_=runtime();score=np.asarray(score,dtype=float)
    assert score.shape==(len(frame),) and np.isfinite(score).all()
    rows=[]
    for context,group in frame.assign(_score=score).groupby('parent_context_id',sort=True):
        assert group.intervention_id.is_unique and len(group)>=2
        assert group.dataset.nunique()==group.biological_component.nunique()==1
        low,high=float(group.measured_delta.min()),float(group.measured_delta.max());assert high>low
        accuracy=pair_credit(group.measured_delta.to_numpy(float),group._score.to_numpy(float)) if ranking else None
        for direction in (-1,1):
            ordered=group.assign(_utility=direction*group._score).sort_values(['_utility','intervention_id'],ascending=[False,True],kind='stable')
            chosen=ordered.iloc[0];effect=direction*float(chosen.measured_delta)
            oriented=direction*group.measured_delta.to_numpy(float);best=float(oriented.max())
            wrong=effect<-1e-12;feasible=bool((oriented>1e-12).any());unavoidable=bool((oriented<-1e-12).all())
            row={'dataset':chosen.dataset,'biological_component':chosen.biological_component,
                'parent_context_id':context,'direction':direction,'selected_id':chosen.intervention_id,
                'candidates':len(group),'regret':(best-effect)/(high-low),'selected_score':float(chosen._score),
                'selected_effect':float(chosen.measured_delta),'wrong_direction':float(wrong),
                'avoidable_wrong':float(wrong and feasible),'no_feasible_candidate':float(not feasible),
                'unavoidable_wrong':float(wrong and unavoidable),
                'neutral_only_alternative_wrong':float(wrong and not feasible and not unavoidable)}
            if ranking:row.update({'pairwise_accuracy':accuracy,'best_recovery':float(effect==best),
                                  'top5_best_recovery':float((direction*ordered.head(5).measured_delta).max()==best)})
            rows.append(row)
    return pd.DataFrame(rows)


def regret(frame,score):
    d=decisions(frame,score,False)
    return float(d.groupby('biological_component').regret.mean().mean())


def equal_decisions(actual,saved,ranking=True):
    np,*_=runtime();keys=['parent_context_id','direction']
    assert not actual.duplicated(keys).any() and not saved.duplicated(keys).any()
    actual,saved=[v.set_index(keys) for v in (actual,saved)]
    assert set(actual.index)==set(saved.index);saved=saved.loc[actual.index]
    for name in ('dataset','biological_component','selected_id','candidates'):np.testing.assert_array_equal(actual[name],saved[name])
    for name in ERRORS+(RANKING if ranking else []):np.testing.assert_allclose(actual[name],saved[name],atol=1e-12,rtol=0)
    for name in ('selected_effect','selected_score'):
        if name in saved:np.testing.assert_allclose(actual[name],saved[name],atol=1e-9 if name=='selected_score' else 1e-12,rtol=0)


def task_summary(d):
    fields=['regret','wrong_direction','avoidable_wrong','pairwise_accuracy']
    return d.groupby(['model','task','biological_component'])[fields].mean().groupby(['model','task']).mean().reset_index()
