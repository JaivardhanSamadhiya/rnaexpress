"""Small, fixed convex pairwise rankers. All preprocessing uses training rows."""
from .common import *
from scipy.optimize import minimize
from scipy.special import expit
PAIR_CACHE={}

def row_weights(frame):
    # Equal study, component, decision context, then candidate. No large library dominates.
    sizes=frame.groupby('parent_context_id').size();units=frame[['dataset','biological_component','parent_context_id']].drop_duplicates()
    nu=units.groupby('dataset').biological_component.nunique();nc=units.groupby(['dataset','biological_component']).size();nd=frame.dataset.nunique()
    return np.array([1/(nd*nu[r.dataset]*nc[r.dataset,r.biological_component]*sizes[r.parent_context_id]) for r in frame.itertuples()])

def pair_indices(frame):
    key=hashlib.sha256(('|'.join(frame.intervention_id)).encode()+frame.measured_delta.to_numpy(float).tobytes()).hexdigest()
    if key in PAIR_CACHE:return PAIR_CACHE[key]
    left=[];right=[];labels=[];weights=[];studies=[]
    units=frame[['dataset','biological_component','parent_context_id']].drop_duplicates();nu=units.groupby('dataset').biological_component.nunique();nc=units.groupby(['dataset','biological_component']).size();nd=frame.dataset.nunique()
    for context,g in frame.groupby('parent_context_id',sort=True):
        idx=g.index.to_numpy();n=len(idx);total=n*(n-1)//2
        seed=int(hashlib.sha256((str(SEED)+context).encode()).hexdigest()[:8],16);rng=np.random.default_rng(seed)
        if total<=256:pairs=list(itertools.combinations(range(n),2))
        else:
            chosen=set()
            while len(chosen)<256:
                a,b=sorted(rng.choice(n,2,replace=False).tolist());chosen.add((a,b))
            pairs=sorted(chosen)
        # Selection is independent of labels. Exact truth ties contribute no preference loss.
        valid=[(idx[a],idx[b]) for a,b in pairs if frame.loc[idx[a],'measured_delta']!=frame.loc[idx[b],'measured_delta']]
        if not valid:continue
        study=g.dataset.iloc[0];unit=g.biological_component.iloc[0];weight=1/(nd*nu[study]*nc[study,unit]*len(valid))
        for a,b in valid:left.append(a);right.append(b);labels.append(1 if frame.loc[a,'measured_delta']>frame.loc[b,'measured_delta'] else -1);weights.append(weight);studies.append(study)
    weights=np.array(weights);weights/=weights.sum()
    result=np.array(left),np.array(right),np.array(labels),weights,np.array(studies)
    PAIR_CACHE[key]=result
    return result

def scaler(x,w):
    mean=np.sum(x*w[:,None],axis=0)/w.sum();scale=np.sqrt(np.sum((x-mean)**2*w[:,None],axis=0)/w.sum());scale[scale<1e-8]=1.
    return mean,scale

def optimize(z,y,w,penalty=.05,groups=None):
    p=z.shape[1];keys=sorted(set(groups)) if groups is not None else [];m=len(keys);gidx=np.array([keys.index(k) for k in groups]) if m else None
    def fun(theta):
        beta=theta[:p];res=theta[p:].reshape(m,p) if m else None
        score=z@beta
        if m:score+=np.einsum('ij,ij->i',z,res[gidx])
        t=y*score;loss=float(w@np.logaddexp(0,-t)+penalty/2*(beta@beta))
        q=-w*y*expit(-t);grad=z.T@q+penalty*beta
        if m:
            grad_r=np.array([z[gidx==k].T@q[gidx==k] for k in range(m)])+penalty*10*res
            loss+=penalty*10/2*float(np.sum(res*res));grad=np.r_[grad,grad_r.ravel()]
        return loss,grad
    result=minimize(fun,np.zeros(p*(1+m)),jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-11,'gtol':1e-7})
    assert result.success, result.message
    return result.x[:p],{k:result.x[p:].reshape(m,p)[i].tolist() for i,k in enumerate(keys)},float(result.fun)

def fit(frame,x,kind='pooled'):
    frame=frame.reset_index(drop=True);w=row_weights(frame);mean,scale=scaler(x,w);z=(x-mean)/scale
    left,right,y,pw,studies=pair_indices(frame);diff=z[left]-z[right]
    assert len(y)>0
    if kind=='meta':
        betas=[];variances=[]
        for study in sorted(set(studies)):
            ix=studies==study;weights=pw[ix]/pw[ix].sum();beta,_,_=optimize(diff[ix],y[ix],weights)
            prob=expit(diff[ix]@beta);h=(diff[ix].T*(weights*prob*(1-prob)))@diff[ix]+.05*np.eye(diff.shape[1])
            # Working curvature uncertainty, not independent biological standard errors.
            eff=frame[frame.dataset.eq(study)].biological_component.nunique();variances.append(np.diag(np.linalg.inv(h))/max(1,eff));betas.append(beta)
        betas=np.array(betas);var=np.array(variances);tau=np.maximum(betas.var(0,ddof=1)-var.mean(0),0) if len(betas)>1 else np.zeros(diff.shape[1]);precision=1/(var+tau+1e-12);beta=(precision*betas).sum(0)/precision.sum(0);res={};loss=np.nan
    else:beta,res,loss=optimize(diff,y,pw,groups=studies if kind=='hierarchical' else None)
    # Separate sign head. A rank score is not an absolute-effect prediction.
    nz=frame.measured_delta.ne(0).to_numpy();dz=np.column_stack([np.ones(nz.sum()),z[nz]]);dw=w[nz]/w[nz].sum();direction,_,_=optimize(dz,np.sign(frame.loc[nz,'measured_delta'].to_numpy()),dw)
    return {'mean':mean.tolist(),'scale':scale.tolist(),'universal_beta':beta.tolist(),'residual_beta':res,'direction_beta':direction.tolist(),'training_studies':sorted(frame.dataset.unique()),'training_components':sorted(frame.biological_component.unique()),'training_rows':len(frame),'training_pairs':len(y),'kind':kind,'objective':loss}

def predict(model,x,studies):
    z=(x-np.array(model['mean']))/np.array(model['scale']);universal=z@np.array(model['universal_beta']);residual=np.zeros(len(x))
    for study,beta in model['residual_beta'].items():
        ix=studies==study;residual[ix]=z[ix]@np.array(beta)
    prob=expit(np.column_stack([np.ones(len(z)),z])@np.array(model['direction_beta']))
    return universal,residual,prob

def purge(frame,train,test):
    held=frame.loc[test];components=set(held.biological_component)
    mask=train & ~frame.biological_component.isin(components).to_numpy()
    alleles=set(held.parent_sequence)|set(held.mutant_sequence)
    # Component construction includes all sequences; this explicit check is a second guard.
    assert not (set(frame.loc[mask,'parent_sequence'])|set(frame.loc[mask,'mutant_sequence'])) & alleles
    return mask
