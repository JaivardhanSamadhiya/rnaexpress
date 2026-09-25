"""One fixed nested grouped fit; no outcome-dependent continuation."""
from .common import *
from .features import features,BASELINES
from pathlib import Path
import sys
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge,LogisticRegression


def weights(genes):
    _,index,counts=np.unique(genes,return_inverse=True,return_counts=True)
    return len(genes)/len(counts)/counts[index]


def fit_ridge(x,y,genes,alpha):
    scaler=StandardScaler().fit(x)
    model=Ridge(alpha=alpha).fit(scaler.transform(x),y,sample_weight=weights(genes))
    return scaler,model


def predict(model,x): return model[1].predict(model[0].transform(x))


def freeze():
    import datetime
    paths=[OUT/'inventory_receipt.json',OUT/'mikl_existing_fold_eligible.csv.gz',REPORT/'small_edit_prediction_protocol.md']
    paths+=sorted(Path(__file__).parent.glob('*.py'))
    jsave('prediction_freeze.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'Exploratory exposed-data size-stratified study; fixed before new fitting',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},'seed':20260925,
        'alpha_grid':[10,100],'primary_families':['delta123','paired'],'bootstrap_draws':2000,
        'models':list(BASELINES),'new_external_confirmation':False})


def run():
    config=readj(OUT/'prediction_freeze.json')
    for p,h in config['files'].items():
        if sha256(ROOT/p)!=h: raise ValueError('Prediction freeze changed '+p)
    frame=pd.read_csv(OUT/'mikl_existing_fold_eligible.csv.gz')
    all_results=[]; selection=[]; coefficients=[]
    for context,part in frame.groupby('cell_type',sort=True):
        part=part.sort_values('pair_id').reset_index(drop=True)
        xs=features(part)
        y=part.localization_change.to_numpy(); genes=part.gene_name.to_numpy(); folds=part.biological_fold.to_numpy(int)
        output=part.copy()
        for name in BASELINES+('primary',):
            output['pred_'+name]=0.0 if name=='no_change' else np.nan
            output['prob_'+name]=.5 if name=='no_change' else np.nan
        output['selected_family']=''; output['selected_alpha']=np.nan
        for fold in sorted(set(folds)):
            test=folds==fold; train=~test
            if set(genes[test])&set(genes[train]): raise ValueError('Gene leakage')
            best={}; fitted={}
            for name,x in xs.items():
                scores=[]
                for alpha in config['alpha_grid']:
                    errors=[]
                    for inner in sorted(set(folds[train])):
                        val=folds==inner; fit=train&~val
                        model=fit_ridge(x[fit],y[fit],genes[fit],alpha)
                        error=(predict(model,x[val])-y[val])**2
                        errors.extend(pd.DataFrame({'gene':genes[val],'error':error}).groupby('gene').error.mean().tolist())
                    loss=float(np.mean(errors)); scores.append((loss,alpha))
                    selection.append({'context':context,'outer_fold':int(fold),'model':name,'alpha':alpha,'inner_gene_mse':loss})
                loss,alpha=min(scores)
                best[name]=(loss,alpha)
                model=fit_ridge(x[train],y[train],genes[train],alpha)
                output.loc[test,'pred_'+name]=predict(model,x[test])
                sign_train=train&(y!=0)
                scaler=StandardScaler().fit(x[sign_train])
                classifier=LogisticRegression(C=1,max_iter=2000,random_state=20260925).fit(scaler.transform(x[sign_train]),y[sign_train]>0,sample_weight=weights(genes[sign_train]))
                output.loc[test,'prob_'+name]=classifier.predict_proba(scaler.transform(x[test]))[:,1]
                coefficients.append({'context':context,'fold':int(fold),'model':name,'alpha':alpha,
                    'ridge_coef':model[1].coef_.tolist(),'ridge_intercept':float(model[1].intercept_),
                    'ridge_scale':model[0].scale_.tolist(),'ridge_mean':model[0].mean_.tolist(),
                    'logistic_coef':classifier.coef_.tolist(),'logistic_intercept':classifier.intercept_.tolist(),
                    'logistic_scale':scaler.scale_.tolist(),'logistic_mean':scaler.mean_.tolist()})
            chosen=min(config['primary_families'],key=lambda n:(best[n][0],config['primary_families'].index(n)))
            output.loc[test,'pred_primary']=output.loc[test,'pred_'+chosen]
            output.loc[test,'prob_primary']=output.loc[test,'prob_'+chosen]
            output.loc[test,'selected_family']=chosen
            output.loc[test,'selected_alpha']=best[chosen][1]
            print(context,'fold',fold,'selected',chosen,'alpha',best[chosen][1],flush=True)
        predcols=[c for c in output if c.startswith(('pred_','prob_'))]
        if not np.isfinite(output[predcols].to_numpy()).all(): raise ValueError('Missing held-out predictions')
        output['predicted_effect']=output.pred_primary
        output['predicted_direction']=np.sign(output.pred_primary)
        output['predicted_direction_probability']=output.prob_primary
        output['fold_status']='gene-held-out; reused development source; seen assay context'
        all_results.append(output)
    csvsave('small_edit_predictions.csv',pd.concat(all_results,ignore_index=True))
    csvsave('inner_model_selection.csv',pd.DataFrame(selection))
    jsave('fitted_parameters.json',coefficients)
    jsave('prediction_receipt.json',{'status':'PASS','rows':sum(len(x) for x in all_results),
        'freeze_sha256':sha256(OUT/'prediction_freeze.json'),
        'prediction_sha256':sha256(OUT/'small_edit_predictions.csv'),'models_fit_scope':'Mikl development only; fixed once; no other outcomes',
        'outputs':{n:sha256(OUT/n) for n in ('small_edit_predictions.csv','inner_model_selection.csv','fitted_parameters.json')}})


if __name__=='__main__': freeze() if sys.argv[1:]==['freeze'] else run()
