from .common import *
from src.cross_assay_20260927.models import row_weights,scaler,optimize
from scipy.optimize import minimize

def noise_targets(pairs,stats,w):
    pools={};q=np.array(stats['q2'],float);sigma=np.ones(len(pairs));identified=np.zeros(len(pairs),bool)
    for study in sorted(pairs.dataset.unique()):
        ix=pairs.dataset.eq(study).to_numpy();good=ix&(stats['n']>=2)&np.isfinite(stats['variance'])
        if not good.any():pools[study]=None;continue
        pool=max(1e-12,float(np.average(stats['variance'][good],weights=w[good])));pools[study]=pool;eligible=ix&(stats['n']>0);n=stats['n'][eligible];var=np.nan_to_num(stats['variance'][eligible],nan=0.);v=((n-1)*var+2*pool)/(n+1);se=np.sqrt(v/n)
        q[eligible]=ndtr(stats['mean'][eligible]/se);sigma[eligible]=np.clip(se/np.sqrt(pool),.25,4);identified[eligible]=True
    return q,sigma,identified,pools

def fit_soft(z,q,w,probit=False,sigma=None):
    def objective(beta):
        score=z@beta
        if probit:
            t=score/sigma;lp=log_ndtr(t);ln=log_ndtr(-t);logpdf=-.5*t*t-.5*np.log(2*np.pi);loss=-float(w@(q*lp+(1-q)*ln));res=((1-q)*np.exp(logpdf-ln)-q*np.exp(logpdf-lp))/sigma
        else:
            loss=float(w@(q*np.logaddexp(0,-score)+(1-q)*np.logaddexp(0,score)));res=expit(score)-q
        return loss+.025*(beta@beta),z.T@(w*res)+.05*beta
    result=minimize(objective,np.zeros(z.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-11,'gtol':1e-7});assert result.success,result.message
    return result.x,float(result.fun),int(result.nit)

def wedges(a,b):return a[:,:17]*b[:,1:18]-a[:,1:18]*b[:,:17]

def fit_all_inputs(frame,x,r,pairs,train,rep_slots=None,crossrep=False):
    tr=frame.loc[train].reset_index(drop=True);wrow=row_weights(tr);mean,scale=scaler(x[train],wrow);z=(x-mean)/scale
    keep=train[pairs.left.to_numpy()]&train[pairs.right.to_numpy()];p=pairs[keep].copy().reset_index(drop=True)
    rr=r if rep_slots is None else r[:,rep_slots];stats=pair_stats(rr[p.left.to_numpy()]-rr[p.right.to_numpy()])
    hard=np.where(stats['mean']>0,1,np.where(stats['mean']<0,0,.5)) if crossrep else p.q_H0.to_numpy()
    eligible=(stats['n']>0)&(stats['mean']!=0) if crossrep else p.historical_train_eligible.to_numpy()
    p=p[eligible].reset_index(drop=True);stats={k:v[eligible] for k,v in stats.items()};hard=hard[eligible];w=pair_weights(tr,p)
    q1=np.where(stats['n']>0,stats['q1'],hard);q2=np.where(stats['n']>0,stats['q2'],hard);q3,sigma,identified,pools=noise_targets(p,stats,w);q3=np.where(stats['n']>0,q3,hard)
    qraw=np.where(stats['n']>0,np.where(stats['mean']>TOL,1,np.where(stats['mean']<-TOL,0,.5)),hard)
    a,b=z[p.left.to_numpy()],z[p.right.to_numpy()];diff=a-b
    rawmean=np.divide(np.nansum(rr[train],axis=1),np.isfinite(rr[train]).sum(1),out=np.zeros(train.sum()),where=np.isfinite(rr[train]).sum(1)>0)
    y=rawmean if crossrep else tr.measured_delta.to_numpy();nz=y!=0;dw=wrow[nz]/wrow[nz].sum();head,_,_=optimize(np.column_stack([np.ones(nz.sum()),z[train][nz]]),np.sign(y[nz]),dw)
    base={'mean':mean.tolist(),'scale':scale.tolist(),'direction_beta':head.tolist(),'training_studies':sorted(tr.dataset.unique()),'training_components':sorted(tr.biological_component.unique()),'training_rows':len(tr),'training_pairs':len(p),'training_ids_sha256':hashlib.sha256('|'.join(tr.intervention_id).encode()).hexdigest(),'noise_pools':pools,'P3_fallback_P2_pairs':int(((stats['n']>0)&~identified).sum()),'aggregate_fallback_pairs':int((stats['n']==0).sum())}
    return dict(base=base,pairs=p,stats=stats,w=w,hard=hard,q1=q1,q2=q2,q3=q3,qraw=qraw,sigma=sigma,identified=identified,diff=diff,a=a,b=b,train_frame=tr)

def fit_method(inp,name):
    p=inp['pairs'];w=inp['w'].copy();z=inp['diff'];model=dict(inp['base']);model.update(name=name,kind='bt',wedge_scale=None,noise_head=None)
    q={'H0':inp['hard'],'P1':inp['q1'],'P2':inp['q2'],'P3':inp['q3'],'Hraw':inp['qraw'],'P2_weighted':inp['q2'],'Partial':np.where(inp['q1']>.5,1,0),'H0_pairfree':inp['hard'],'P2_pairfree':inp['q2'],'P3_hetero':inp['q3']}[name]
    use=np.ones(len(p),bool)
    if name=='P2_weighted':
        factor=np.where(inp['stats']['n']>0,.25+.75*abs(2*inp['q1']-1),1.)
        for _,g in p.groupby('parent_context_id'):
            ix=g.index.to_numpy();w[ix]=w[ix].sum()*(w[ix]*factor[ix])/(w[ix]*factor[ix]).sum()
    if name=='Partial':
        s=inp['stats'];use=(s['n']==0)|((s['n']>=2)&((s['posterior_tail']>=.9)|(s['posterior_tail']<=.1)));q=np.where(s['n']==0,inp['hard'],q)
        kept=p[use];remaining=inp['train_frame'][inp['train_frame'].parent_context_id.isin(kept.parent_context_id)];w=pair_weights(remaining,kept);model.update(retained_pairs=int(use.sum()),discarded_pairs=int((~use).sum()),retained_contexts=int(kept.parent_context_id.nunique()),retained_studies=sorted(kept.dataset.unique()))
    if name.endswith('pairfree'):
        wg=wedges(inp['a'],inp['b']);scale=np.sqrt(np.sum(w[:,None]*wg*wg,axis=0));scale[scale<1e-8]=1;z=np.column_stack([z,wg/scale]);model.update(kind='pairfree',wedge_scale=scale.tolist())
    sigma=None
    if name=='P3_hetero':
        v=np.column_stack([np.ones(len(z)),abs(z[:,:18])]);good=inp['identified'];assert good.any();ww=w[good]/w[good].sum();noise=np.linalg.solve((v[good].T*ww)@v[good]+.05*np.eye(19),v[good].T@(ww*np.log(inp['sigma'][good])));sigma=np.clip(np.exp(v@noise),.25,4);model.update(kind='hetero',noise_head=noise.tolist())
    if name=='H0':beta,_,loss=optimize(z,2*q-1,w);nit=None
    else:beta,loss,nit=fit_soft(z[use],q[use],w if name=='Partial' else w[use]/w[use].sum(),probit=name=='P3_hetero',sigma=sigma)
    model.update(beta=beta.tolist(),objective=loss,iterations=nit)
    targets=p[['pair_id','dataset','parent_context_id']].copy();targets['target']=q;targets['included']=use;targets['weight']=0.;targets.loc[use,'weight']=w if name=='Partial' else w[use]/w[use].sum();targets['measurement_scale']=inp['sigma'];targets['measurement_scale_identified']=inp['identified']
    return model,targets

def transformed(model,x):return (x-np.array(model['mean']))/np.array(model['scale'])
def probabilities(model,a,b):
    d=a-b;beta=np.array(model['beta']);score=d@beta[:d.shape[1]]
    if model['kind']=='pairfree':score+=(wedges(a,b)/model['wedge_scale'])@beta[d.shape[1]:]
    if model['kind']=='hetero':
        sigma=np.clip(np.exp(np.column_stack([np.ones(len(d)),abs(d[:,:18])])@model['noise_head']),.25,4);return ndtr(score/sigma)
    return expit(score)

def candidate_scores(model,x):
    z=transformed(model,x);latent=z@np.array(model['beta'])[:z.shape[1]];n=len(x)
    if model['kind']=='bt':matrix=expit(latent[:,None]-latent[None,:])
    else:
        matrix=np.empty((n,n));width=max(1,32768//n)
        for start in range(0,n,width):
            stop=min(n,start+width);a=np.repeat(z[start:stop],n,axis=0);b=np.tile(z,(stop-start,1));matrix[start:stop]=probabilities(model,a,b).reshape(stop-start,n)
    np.fill_diagonal(matrix,.5);expected=(matrix.sum(1)-.5)/(n-1);score=latent if model['kind']=='bt' else expected
    return score,latent,matrix,expected
