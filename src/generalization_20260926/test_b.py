"""Locked nested parent/overlap holdouts; never select on outer outcomes."""
from .common import *
from .features import matrices,disjoint_train
from .evaluation import evaluate
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

def fit_predict(x, y, parents, target, alpha):
    labels, counts=np.unique(parents,return_counts=True)
    indicators=(parents[:,None]==labels[None,:]).astype(float)
    nuisance=indicators-counts[None,:]/len(parents)
    train=np.column_stack([x,nuisance]);test=np.column_stack([target,np.zeros((len(target),len(labels)))])
    scaler=StandardScaler().fit(train)
    weights=np.array([len(parents)/(len(labels)*counts[np.where(labels==p)[0][0]]) for p in parents])
    model=Ridge(alpha=alpha,fit_intercept=True).fit(scaler.transform(train),y,sample_weight=weights)
    prediction=model.predict(scaler.transform(test))
    raw=model.coef_/scaler.scale_
    return prediction, {'alpha':alpha,'training_parents':labels.tolist(),'training_n':len(y),'feature_raw_coefficients':raw[:x.shape[1]].tolist(),'nuisance_raw_coefficients':raw[x.shape[1]:].tolist(),'scaler_mean':scaler.mean_.tolist(),'scaler_scale':scaler.scale_.tolist(),'intercept':float(model.intercept_),'training_weight_by_parent':{p:float(weights[parents==p].sum()) for p in labels}}

def select_alpha(frame,x,outer_mask):
    """Only outer training outcomes are read, including in all inner folds."""
    train=frame.loc[outer_mask];scores=[]
    for held in sorted(train.parent_id.unique()):
        inner_train=outer_mask & disjoint_train(frame,held)
        inner_test=outer_mask & frame.parent_id.eq(held).to_numpy()
        assert not set(frame.loc[inner_train,'overlap_component']) & set(frame.loc[inner_test,'overlap_component'])
        for alpha in config()['test_b_ridge_alphas']:
            pred,_=fit_predict(x[inner_train],frame.loc[inner_train,'observed_delta'].to_numpy(),frame.loc[inner_train,'parent_id'].to_numpy(),x[inner_test],alpha)
            scores.append({'inner_parent':held,'alpha':alpha,'mse':float(np.mean((pred-frame.loc[inner_test,'observed_delta'].to_numpy())**2))})
    means=pd.DataFrame(scores).groupby('alpha').mse.mean();best=means.min()
    alpha=float(max(a for a in means.index if means[a]<=best+TOL))
    return alpha,scores

def run():
    assert_frozen();assert readj(OUT/'test_a_verdict.json')['test_b_run_allowed']
    assert not (OUT/'test_b_verdict.json').exists(),'B already evaluated'
    frame=pd.read_csv(ART/'GSE330741_mapped_outcomes.csv',float_precision='round_trip')
    frame=frame[frame.qc_status.eq('VERIFIED')].reset_index(drop=True)
    xs=matrices(frame);cfg=config();models=cfg['test_b_models'];predictions=pd.DataFrame(np.nan,index=frame.index,columns=models)
    folds=[];selection=[];assignments=[]
    for held in sorted(frame.parent_id.unique()):
        train=disjoint_train(frame,held);test=frame.parent_id.eq(held).to_numpy()
        train_parents=sorted(frame.loc[train,'parent_id'].unique())
        assert held not in train_parents and not set(frame.loc[train,'overlap_component']) & set(frame.loc[test,'overlap_component'])
        predictions.loc[test,'no_change']=0
        predictions.loc[test,'training_mean']=frame.loc[train].groupby('parent_id').observed_delta.mean().mean()
        assignments.append({'held_parent':held,'training_parents':train_parents,'purged_parents':sorted(set(frame.parent_id)-set(train_parents)-{held}),'held_n':int(test.sum()),'training_n':int(train.sum())})
        for model,x in xs.items():
            alpha,scores=select_alpha(frame,x,train)
            selection.extend(dict(held_parent=held,model=model,**s) for s in scores)
            pred,fit=fit_predict(x[train],frame.loc[train,'observed_delta'].to_numpy(),frame.loc[train,'parent_id'].to_numpy(),x[test],alpha)
            predictions.loc[test,model]=pred;folds.append(dict(held_parent=held,model=model,**fit))
        print('Completed held parent',held,flush=True)
    assert np.isfinite(predictions.to_numpy()).all()
    jsave(OUT/'test_b_fits.json',folds);jsave(OUT/'test_b_fold_assignments.json',assignments)
    csvsave(OUT/'test_b_inner_selection.csv',pd.DataFrame(selection))
    export=pd.concat([frame,predictions],axis=1);export['model_prediction']=predictions[cfg['test_b_primary_model']]
    export['predicted_direction']=sign(export.model_prediction);export['observed_direction']=sign(export.observed_delta)
    for held,g in export.groupby('parent_id'):
        for direction,label in [(1,'increase'),(-1,'decrease')]:
            ordered=g.assign(score=direction*g.model_prediction).sort_values(['score','element'],ascending=[False,True]);export.loc[ordered.index,'candidate_rank_'+label]=np.arange(1,len(g)+1)
    csvsave(ART/'GSE330741_leave_parent_out_predictions.csv',export)
    evaluate(frame,predictions,'test_b',cfg['test_b_primary_model'],[cfg['test_b_primary_comparator']])
    # Fixed secondary diagnostic, never used to select or change the primary models.
    gene_rows=[]
    for gene in sorted(frame.gene.unique()):
        train=frame.gene.ne(gene).to_numpy();test=~train
        for model in ('simple_full','simple_full_delta2'):
            x=xs[model];pred,fit=fit_predict(x[train],frame.loc[train,'observed_delta'].to_numpy(),frame.loc[train,'parent_id'].to_numpy(),x[test],10.)
            for ix,p in zip(frame.index[test],pred):gene_rows.append({'element':frame.loc[ix,'element'],'parent_id':frame.loc[ix,'parent_id'],'held_gene':gene,'model':model,'predicted_delta':p,'observed_delta':frame.loc[ix,'observed_delta']})
    csvsave(ART/'GSE330741_leave_gene_out_predictions.csv',pd.DataFrame(gene_rows))

if __name__=='__main__':run()
