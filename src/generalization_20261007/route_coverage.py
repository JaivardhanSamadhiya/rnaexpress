"""A connected label-blind pair roster and smooth worst-source training risk."""
from .common import *
from src.cross_assay_20260927.models import pair_indices as historical_pairs
from scipy.optimize import minimize
from scipy.special import expit, logsumexp
import itertools

CONFIGS = [{'id':'historical_pairs_l2_05','coverage':'historical','robust':False,'penalty':.05}]+[
    {'id':f'{kind}_l2_{p:g}', 'coverage':'connected', 'robust':kind=='connected_robust', 'penalty':p}
    for kind in ('connected_erm','connected_robust') for p in (.005,.05,.5)]
_PAIR_CACHE = {}

def build_features(frame, base):
    return base

def pairs_for(frame, coverage):
    if coverage == 'historical':
        return historical_pairs(frame)
    # Cache is outcome-sensitive so independent training partitions cannot alias.
    key = hashlib.sha256('|'.join(frame.intervention_id).encode()+frame.measured_delta.to_numpy(float).tobytes()).hexdigest()
    if key in _PAIR_CACHE:
        return _PAIR_CACHE[key]
    units=frame[['dataset','biological_component','parent_context_id']].drop_duplicates()
    nu=units.groupby('dataset').biological_component.nunique()
    nc=units.groupby(['dataset','biological_component']).size()
    left,right,labels,weights,studies=[],[],[],[],[]
    for context,g in frame.groupby('parent_context_id',sort=True):
        idx=g.index.to_numpy(); n=len(idx); total=n*(n-1)//2
        if total <= 256:
            chosen=list(itertools.combinations(range(n),2))
        else:
            rng=np.random.default_rng(int(hashlib.sha256((str(SEED)+'|'+context).encode()).hexdigest()[:8],16))
            chain=rng.permutation(n)
            edges={tuple(sorted((int(a),int(b)))) for a,b in zip(chain[:-1],chain[1:])}
            cap=min(total,max(2048,n-1))
            while len(edges)<cap:
                a,b=sorted(rng.choice(n,2,replace=False).tolist()); edges.add((a,b))
            chosen=sorted(edges)
        # Only training labels remove exact ties; pair sampling itself is label-blind.
        valid=[(idx[a],idx[b]) for a,b in chosen if frame.loc[idx[a],'measured_delta']!=frame.loc[idx[b],'measured_delta']]
        if not valid:
            continue
        study,unit=g.dataset.iloc[0],g.biological_component.iloc[0]
        w=1/(len(nu)*nu[study]*nc[study,unit]*len(valid))
        for a,b in valid:
            left.append(a);right.append(b);labels.append(1 if frame.loc[a,'measured_delta']>frame.loc[b,'measured_delta'] else -1)
            weights.append(w);studies.append(study)
    w=np.array(weights);w/=w.sum()
    value=np.array(left),np.array(right),np.array(labels),w,np.array(studies)
    _PAIR_CACHE[key]=value
    return value

def objective(beta,diff,y,w,studies,penalty,robust):
    score=diff@beta
    losses=np.logaddexp(0,-y*score)
    if robust:
        keys=sorted(set(studies))
        group_risks=np.array([np.average(losses[studies==k],weights=w[studies==k]) for k in keys])
        # Fixed temperature, smooth maximum of normalized source risks.
        t=5.; q=expit(-y*score); soft=np.exp(t*group_risks-logsumexp(t*group_risks))
        effective=np.zeros(len(w))
        for k,alpha in zip(keys,soft):
            ix=studies==k;effective[ix]=alpha*w[ix]/w[ix].sum()
        loss=(logsumexp(t*group_risks)-np.log(len(keys)))/t
        gradient=diff.T@(-effective*y*q)+penalty*beta
    else:
        loss=w@losses
        gradient=diff.T@(-w*y*expit(-y*score))+penalty*beta
    return float(loss+penalty*.5*(beta@beta)),gradient

def fit_model(frame,x,config):
    frame=frame.reset_index(drop=True)
    a,b,y,w,studies=pairs_for(frame,config['coverage'])
    assert len(y)>0
    delta=x[a]-x[b]
    scale=np.sqrt(np.sum(w[:,None]*delta*delta,axis=0)); supported=scale>=1e-8; scale[~supported]=1
    diff=delta/scale
    result=minimize(objective,np.zeros(x.shape[1]),args=(diff,y,w,studies,config['penalty'],config['robust']),
        jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-11,'gtol':1e-7})
    assert result.success,result.message
    beta=result.x;beta[~supported]=0
    return {'beta':beta.tolist(),'scale':scale.tolist(),'config':config,'training_pairs':len(y),
            'training_candidate_coverage':int(len(np.unique(np.r_[a,b]))),
            'training_candidates':len(frame),'objective':float(result.fun),'iterations':int(result.nit)}

def predict_model(model,x):
    return (x/np.asarray(model['scale']))@np.asarray(model['beta'])
