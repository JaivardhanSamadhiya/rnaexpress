"""Descriptive, prespecified coefficient and two-gene diagnostics."""
from .common import *
from .evaluation import correlations

def centered(x):return x-x.mean()
def interaction(x):
    a=x.reshape(4,4);return (a-a.mean(0,keepdims=True)-a.mean(1,keepdims=True)+a.mean()).ravel()
def agreement(a,b):
    return {'pearson':float(np.corrcoef(a,b)[0,1]),'cosine':float(a@b/(np.linalg.norm(a)*np.linalg.norm(b))),'sign_concordance':float(np.mean(sign(a)==sign(b)))}

def run():
    assert_frozen();fits=readj(OUT/'test_b_fits.json');source=np.array(readj(OUT/'source_predictor.json')['order_beta']['2mer'])
    arrays=np.array([f['feature_raw_coefficients'] for f in fits if f['model']=='delta2']);parents=[f['held_parent'] for f in fits if f['model']=='delta2']
    csvsave(OUT/'cross_assay_coefficients.csv',pd.DataFrame({'dinucleotide':VOCAB[2],'srle_raw':source,'astrocyte_mean_raw':arrays.mean(0),**{p:a for p,a in zip(parents,arrays)}}))
    rng=np.random.default_rng(SEED);perms=np.array([rng.permutation(16) for _ in range(4096)]);rows=[]
    for label,b in list(zip(parents,arrays))+[('mean_outer_coefficients',arrays.mean(0))]:
        for gauge,transform in [('grand_mean',centered),('row_column_interaction',interaction)]:
            a=transform(source);v=transform(b);stats=agreement(a,v)
            null=np.array([agreement(a,transform(b[ix]))['pearson'] for ix in perms])
            rows.append({'held_parent':label,'gauge':gauge,**stats,'permutation_p_positive':(1+(null>=stats['pearson']-TOL).sum())/4097,'permutations':4096,'interpretation':'descriptive feature-label permutation, not independent biological or causal inference'})
    csvsave(OUT/'cross_assay_coefficient_agreement.csv',pd.DataFrame(rows))
    f=pd.read_csv(ART/'GSE330741_leave_gene_out_predictions.csv');rows=[]
    for (gene,model,parent),g in f.groupby(['held_gene','model','parent_id']):
        rho,r,constant=correlations(g.observed_delta.to_numpy(),g.predicted_delta.to_numpy())
        rows.append({'held_gene':gene,'model':model,'parent_id':parent,'snps':len(g),'spearman':rho,'pearson':r,'mse':np.mean((g.predicted_delta-g.observed_delta)**2)})
    csvsave(OUT/'leave_gene_out_parent_metrics.csv',pd.DataFrame(rows))

if __name__=='__main__':run()
