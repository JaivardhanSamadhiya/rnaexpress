from .common import *
from src.srle_prediction_20260926.core import training_mask
from src.srle_prediction_20260926.fit import linear_fit
from src.research_20260921.robustness import count_features
import hashlib
import subprocess
from datetime import datetime,timezone


def freeze():
    paths=sorted(Path(__file__).parent.glob('*.py'))+[REPORT/'srle_synthesis_analysis_protocol.md',OUT/'clean_replay_receipt.json']
    old=readj(OLDART/'srle_prediction_delivery_receipt.json')
    paths += [ROOT/p for p in old['manifest']]
    jsave(OUT/'analysis_freeze.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
        'status':'Exploratory fixed interpretation/controls; preserves original primary results',
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
        'label_permutation_seeds':list(range(2026092600,2026092632)),
        'position_permutation':[0,2,4,1,3,5],'original_result_commit':'e5b9288'})


def verify_freeze():
    frozen=readj(OUT/'analysis_freeze.json')
    for name,h in frozen['files'].items():assert sha256(ROOT/name)==h,name
    rel=(OUT/'analysis_freeze.json').relative_to(ROOT).as_posix()
    assert subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)==(OUT/'analysis_freeze.json').read_bytes()
    return frozen


def run():
    frozen=verify_freeze();source,effects,choices,fits,roster=load()
    seq=source.kmer.to_numpy();groups=source.group.to_numpy();train0=~source.test.to_numpy()
    y=source.nrs.to_numpy();residual=np.full(len(y),np.nan)
    for group in sorted(set(groups[train0])):
        mask=train0 & (groups==group);residual[mask]=y[mask]-y[mask].mean()
    x=count_features(seq)[:,4:20]
    shuffled=[''.join(s[i] for i in frozen['position_permutation']) for s in seq]
    shuffle_features=count_features(np.array(shuffled))[:,4:20]
    random_features=np.array([np.random.default_rng(int(hashlib.sha256(('srle-synthesis-random16-20260926|'+s).encode()).hexdigest(),16)).normal(size=16) for s in seq])
    null_labels=[]
    for seed in frozen['label_permutation_seeds']:
        rng=np.random.default_rng(seed);r=residual.copy()
        for group in sorted(set(groups[train0])):
            ix=np.flatnonzero(train0&(groups==group));r[ix]=rng.permutation(r[ix])
        null_labels.append(r)
    lookup={s:i for i,s in enumerate(seq)};pi=np.array([lookup[s] for s in roster.parent]);ci=np.array([lookup[s] for s in roster.candidate])
    control_names=['position_shuffled_2mer','random16']+[f'within_composition_label_null_{i:02d}' for i in range(32)]
    values={name:np.full(len(roster),np.nan) for name in control_names}
    for number,group in enumerate(sorted(roster.group.unique())):
        train=training_mask(source,'purged_composition_holdout',group);edge=roster.group.eq(group).to_numpy()
        assert not np.any(train[pi[edge]]) and not np.any(train[ci[edge]])
        for name,features,response in [('position_shuffled_2mer',shuffle_features,residual),('random16',random_features,residual)]+[(control_names[i+2],x,r) for i,r in enumerate(null_labels)]:
            prediction,_=linear_fit(features,response,train)
            values[name][edge]=prediction[ci[edge]]-prediction[pi[edge]]
        if number%10==0:print('Fixed controls group',number+1,'/60',flush=True)
    result=roster[['parent','candidate','group','published_delta','rep1_delta','rep2_delta']].copy()
    for name,v in values.items():assert np.isfinite(v).all();result[name]=v
    csvsave(ART/'control_predictions.csv',result)
    metrics=[]
    for target in ('published','rep1','rep2'):
        truth=result[target+'_delta'].to_numpy()
        for name in control_names:
            prediction=result[name].to_numpy();frame=pd.DataFrame({'group':result.group,'sse':(prediction-truth)**2,'base':truth**2})
            totals=frame.groupby('group')[['sse','base']].sum();ix=draws(len(totals))
            gain=1-totals.sse.sum()/totals.base.sum();dist=1-totals.sse.to_numpy()[ix].sum(1)/totals.base.to_numpy()[ix].sum(1)
            lo,hi=np.quantile(dist,[.025,.975]);valid=sign(truth)!=0
            metrics.append({'target':target,'control':name,'mse_improvement':gain,'ci_low':lo,'ci_high':hi,
                'rmse':np.sqrt(np.mean((prediction-truth)**2)),'sign_accuracy':np.mean(sign(prediction[valid])==sign(truth[valid])),
                'groups':60,'edges':1744,'biological_contexts':1,'interpretation':'fixed descriptive control, not independent confirmation'})
    csvsave(OUT/'control_metrics.csv',pd.DataFrame(metrics))
    jsave(OUT/'control_receipt.json',{'status':'PASS','controls':len(control_names),'training_partitions':60,
        'ridge_fits':60*len(control_names),'seed_retries':0,'test_labels_in_training_permutation':False,
        'position_shuffle_note':'retains nonadjacent sequence-order information; not an information-free null',
        'label_column_permutation_note':'renaming features and their coefficients leaves predictions identical; not a null'})
    print(pd.DataFrame(metrics).query("target=='published' and not control.str.contains('label_null')").to_string(index=False))


if __name__=='__main__':
    import sys
    freeze() if sys.argv[1:]==['freeze'] else run()
