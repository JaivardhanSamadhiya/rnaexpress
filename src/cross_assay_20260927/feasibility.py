from .common import *
from .models import row_weights,scaler,optimize
from scipy.special import expit

def group_features(frame,x):
    rows=[];features=[]
    for context,g in frame.groupby('parent_context_id'):
        v=x[g.index];mean=v.mean(0);sd=v.std(0);lo=v.min(0);hi=v.max(0)
        for direction in (-1,1):
            rows.append({'dataset':g.dataset.iloc[0],'biological_component':g.biological_component.iloc[0],'parent_context_id':context,'direction':direction,'label':int((direction*g.measured_delta>1e-12).any())})
            features.append(np.r_[direction,mean,sd,lo,hi,direction*mean])
    return pd.DataFrame(rows),np.array(features)
def fit_feasibility(frame,x):
    g,z=group_features(frame.reset_index(drop=True),x);w=row_weights(g);mean,scale=scaler(z,w);z=(z-mean)/scale
    beta,_,_=optimize(np.column_stack([np.ones(len(z)),z]),2*g.label.to_numpy()-1,w)
    return {'mean':mean.tolist(),'scale':scale.tolist(),'beta':beta.tolist(),'training_sets':len(g),'prevalence':float(w@g.label)}
def predict_feasibility(model,frame,x):
    g,z=group_features(frame.reset_index(drop=True),x);p=expit(np.column_stack([np.ones(len(z)),(z-model['mean'])/model['scale']])@np.array(model['beta']))
    return {(r.parent_context_id,r.direction):float(p[i]) for i,r in enumerate(g.itertuples())}
