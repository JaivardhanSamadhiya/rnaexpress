from .common import *

def run():
    contributions=pd.read_csv(ART/'dinucleotide_contributions.csv',dtype={'group':str},float_precision='round_trip')
    rows=[];identity_error=[]
    for (parent,candidate),g in contributions.groupby(['parent','candidate']):
        g=g.sort_values('feature');b=g.raw_count_coefficient.to_numpy().reshape(4,4);delta=g.delta_count.to_numpy()
        grand=b.mean();r=b.mean(1)-grand;c=b.mean(0)-grand;interaction=b-grand-r[:,None]-c[None,:]
        additive=grand+r[:,None]+c[None,:]
        endpoint=-(r['ACGT'.index(candidate[-1])]-r['ACGT'.index(parent[-1])])-(c['ACGT'.index(candidate[0])]-c['ACGT'.index(parent[0])])
        adjacency=float(delta@interaction.ravel());full=float(g.predicted_effect.iloc[0])
        identity_error.extend([abs(endpoint+adjacency-full),abs(endpoint-delta@additive.ravel()),abs(delta[::-1]@b.ravel()[::-1]-full)])
        rows.append({'parent':parent,'candidate':candidate,'group':g.group.iloc[0],'endpoint_encoded_contribution':endpoint,'interaction_contribution':adjacency,'full_prediction':full,'measured_effect':g.measured_effect.iloc[0],'first_or_last_base_changed':parent[0]!=candidate[0] or parent[-1]!=candidate[-1]})
    a=pd.DataFrame(rows);assert max(identity_error)<1e-12;csvsave(ART/'boundary_contributions.csv',a)
    metrics=[]
    for name in ('endpoint_encoded_contribution','interaction_contribution','full_prediction'):
        pred=a[name].to_numpy();truth=a.measured_effect.to_numpy()
        metrics.append({'component':name,'variance':np.var(pred),'mean_absolute_contribution':np.abs(pred).mean(),'pearson_with_measured':np.corrcoef(pred,truth)[0,1],'descriptive_mse_reduction_vs_zero':1-np.mean((pred-truth)**2)/np.mean(truth**2),'status':'algebraic diagnostic only; not a refitted or independently validated predictor'})
    csvsave(OUT/'boundary_component_diagnostics.csv',pd.DataFrame(metrics))
    jsave(OUT/'boundary_receipt.json',{'status':'PASS','max_identity_error':max(identity_error),'endpoint_interaction_covariance':np.cov(a.endpoint_encoded_contribution,a.interaction_contribution,ddof=0)[0,1],'endpoint_absolute_share':np.abs(a.endpoint_encoded_contribution).sum()/(np.abs(a.endpoint_encoded_contribution).sum()+np.abs(a.interaction_contribution).sum()),'endpoint_changed_edges':int(a.first_or_last_base_changed.sum()),'interpretation':'Local order includes boundary position; not exclusively internal adjacency and not causal mechanism','addendum_sha256':sha256(REPORT/'srle_boundary_decomposition_addendum.md')})
    print(pd.DataFrame(metrics).to_string(index=False))

if __name__=='__main__':run()
