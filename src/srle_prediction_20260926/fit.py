from .core import *
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from src.research_20260921.pilots import position_features
from src.research_20260921.robustness import count_features
import subprocess


def design(sequences):
    k=count_features(np.asarray(sequences)); p=position_features(np.asarray(sequences))
    return {'2mer':k[:,4:20],'3mer':k[:,20:84],'kmer123':k,'position_additive':p[:,:24],'position_pair':p}


def linear_fit(x,y,train):
    scaler=StandardScaler().fit(x[train])
    ridge=Ridge(alpha=10).fit(scaler.transform(x[train]),y[train])
    return ridge.predict(scaler.transform(x)),{'mean':scaler.mean_.tolist(),'scale':scaler.scale_.tolist(),
        'coefficient':ridge.coef_.tolist(),'intercept':float(ridge.intercept_)}


def fit_fold(frame,xs,train):
    y=frame.nrs.to_numpy(); group=frame.group.to_numpy()
    fallback,params=linear_fit(counts(frame.kmer),y,train)
    means={g:float(np.mean(y[train & (group==g)])) for g in sorted(set(group[train]))}
    base=np.array([means.get(g,fallback[i]) for i,g in enumerate(group)])
    predictions={'composition':base,'1mer':base.copy()}
    coefficients={'composition':{'training_class_means':means,'unseen_composition_ridge':params},
                  '1mer':{'analytic_identity':'composition residuals sum to zero within every training class; no additional order information'}}
    for name,x in xs.items():
        delta,params=linear_fit(x,y-base,train)
        predictions[name]=base+delta;coefficients[name]=params
    return predictions,coefficients


def freeze():
    import datetime
    files=sorted(Path(__file__).parent.glob('*.py'))+[REPORT/'srle_small_edit_prediction_protocol.md',OUT/'inventory_receipt.json']
    inventory=readj(OUT/'inventory_receipt.json')
    files += [ROOT/p for p in inventory['inputs']]+[ROOT/p for p in inventory['outputs']]
    jsave(OUT/'evaluation_freeze.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'User-requested exploratory generalization audit of already-exposed SRLE; not independent confirmation',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in files},'alpha':10,'seed':SEED,
        'bootstrap_draws':2000,'primary_scheme':'purged_composition_holdout','primary_model':'position_pair',
        'models':MODELS,'schemes':SCHEMES,'outcomes_newly_admitted':False})


def run():
    frozen=readj(OUT/'evaluation_freeze.json')
    rel=(OUT/'evaluation_freeze.json').relative_to(ROOT).as_posix()
    assert subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)==(OUT/'evaluation_freeze.json').read_bytes()
    for p,h in frozen['files'].items():assert sha256(ROOT/p)==h,p
    frame=pd.read_csv(OUT/'sequence_inventory.csv',dtype={'group':str},float_precision='round_trip')
    xs=design(frame.kmer); output=[];coefficients=[];replay={}
    for scheme in SCHEMES:
        groups=[None] if scheme=='sequence_holdout' else sorted(frame.loc[frame.scored,'group'].unique())
        for number,key in enumerate(groups):
            train=training_mask(frame,scheme,key)
            test=frame.scored.to_numpy() & (True if key is None else frame.group.eq(key).to_numpy())
            predictions,coefs=fit_fold(frame,xs,train)
            if scheme=='sequence_holdout':
                for name in ('composition','position_pair','position_additive','kmer123'):
                    error=float(np.max(np.abs(predictions[name][test]-frame.loc[test,name].to_numpy())))
                    assert error<1e-12,(name,error)
                    replay[name+'_max_error']=error
                y=frame.loc[test,'nrs'].to_numpy()
                reduction=1-np.sum((y-predictions['position_pair'][test])**2)/np.sum((y-predictions['composition'][test])**2)
                expected=readj(OLD/'robustness_result.json')['models']['position_pair']['error_reduction_vs_composition']
                assert abs(reduction-expected)<1e-12
                replay.update(error_reduction=reduction,expected_error_reduction=expected)
                print('Historical 27.04% replay PASS',reduction,flush=True)
            for name in MODELS:
                part=frame.loc[test,['kmer','group','nrs','NRS1','NRS2','biological_context']].copy()
                part['scheme']=scheme;part['held_group']=key or 'original_hash';part['model']=name
                part['predicted_score']=predictions[name][test];part['train_sequences']=int(train.sum())
                part['measurement']='published NRS log2FC; constituent log2 NRS retained separately'
                output.append(part)
            coefficients.append({'scheme':scheme,'held_group':key or 'original_hash','coefficients':coefs})
            if number%10==0 or number==len(groups)-1:print(scheme,number+1,'/',len(groups),flush=True)
    result=pd.concat(output,ignore_index=True)
    assert len(result)==855*len(MODELS)*len(SCHEMES)
    csvsave(ART/'srle_heldout_predictions.csv',result)
    jsave(OUT/'fitted_parameters.json',coefficients)
    jsave(OUT/'fit_receipt.json',{'status':'PASS','historical_replay':replay,'fits_with_shared_split':len(coefficients),
        'heldout_prediction_rows':len(result),'freeze_sha256':sha256(OUT/'evaluation_freeze.json'),
        'outputs':{p.relative_to(ROOT).as_posix():sha256(p) for p in (ART/'srle_heldout_predictions.csv',OUT/'fitted_parameters.json')}})


if __name__=='__main__':
    import sys
    freeze() if sys.argv[1:]==['freeze'] else run()
