"""Conditional SRLE class-cluster intervals on the fixed measured edge cohort."""
from .common import *


def calculate(stats):
    n,sy,sp,sy2,sp2,syp,abs_err,sq_err,correct=stats.T
    cov=syp-sy*sp/n
    denom=np.sqrt(np.maximum(0,sy2-sy*sy/n)*np.maximum(0,sp2-sp*sp/n))
    rho=np.divide(cov,denom,out=np.full_like(cov,np.nan),where=denom>0)
    return {'pearson':rho,'mae':abs_err/n,'rmse':np.sqrt(sq_err/n),'sign_accuracy':correct/n}


def run():
    frame=pd.read_csv(OUT/'small_edit_secondary_predictions.csv')
    frame=frame[frame.dataset.eq('srle')]
    rows=[]
    for (rep,model),g in frame.groupby(['replicate','model']):
        stats=[]
        for _,c in g.groupby('group'):
            y=c.measured_effect.to_numpy(); p=c.predicted_score_difference.to_numpy()
            if (y==0).any(): raise ValueError('Unexpected ties in original SRLE cohort')
            stats.append([len(c),y.sum(),p.sum(),(y*y).sum(),(p*p).sum(),(y*p).sum(),np.abs(y-p).sum(),((y-p)**2).sum(),(np.sign(y)==np.sign(p)).sum()])
        stats=np.array(stats,float)
        draws=np.random.default_rng(20260925).integers(0,len(stats),(2000,len(stats)))
        boot=calculate(stats[draws].sum(1)); point=calculate(stats.sum(0)[None,:])
        for metric in point:
            values=boot[metric]; finite=values[np.isfinite(values)]
            lo,hi=np.quantile(finite,[.025,.975]) if len(finite) else (np.nan,np.nan)
            rows.append({'dataset':'srle','replicate':rep,'model':model,'metric':metric,'estimate':float(point[metric][0]),
                'ci_low':float(lo),'ci_high':float(hi),'clusters':len(stats),'edges':len(g),'draws':2000,
                'scope':'conditional class-cluster bootstrap of row-weighted edge metrics; one shared experiment; not independent biology'})
    csvsave('srle_direct_effect_intervals.csv',pd.DataFrame(rows))
    print(pd.DataFrame(rows).query('model == "kmer123"').to_string(index=False))


if __name__=='__main__': run()
