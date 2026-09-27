"""SRLE-only frozen coefficients; target design only, no target outcome access."""
from .common import *
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

def run():
    target=pd.read_csv(ART/'GSE330741_design_without_outcomes.csv')
    dx=delta_features(target)
    old=ROOT/'results/srle_prediction_20260926'
    fits=readj(old/'fitted_parameters.json')
    f=[v for v in fits if v['scheme']=='sequence_holdout' and v['held_group']=='original_hash'];assert len(f)==1
    c=f[0]['coefficients'];mono=c['composition']['unseen_composition_ridge']
    mono_beta=np.array(mono['coefficient'])/np.array(mono['scale'])
    source=pd.read_csv(old/'sequence_inventory.csv');train=~source.test.to_numpy();seq=source.kmer.to_numpy();y=source.nrs.to_numpy()
    train_y={s:float(v) for s,v,t in zip(seq,y,train) if t};sub={a+'>'+b:[] for a in 'ACGT' for b in 'ACGT' if a!=b}
    for p,v in train_y.items():
        for i,ref in enumerate(p):
            for alt in 'ACGT':
                if alt==ref:continue
                m=p[:i]+alt+p[i+1:]
                if m in train_y:sub[ref+'>'+alt].append(train_y[m]-v)
    sub_beta={k:float(np.mean(v)) for k,v in sub.items()};assert all(len(v)>0 for v in sub.values())
    au=np.array([[s.count('A')+s.count('T')] for s in seq],float);sc=StandardScaler().fit(au[train]);ridge=Ridge(alpha=10).fit(sc.transform(au[train]),y[train]);au_beta=float(ridge.coef_[0]/sc.scale_[0])
    weights={'source_partition':{'scheme':f[0]['scheme'],'held_group':f[0]['held_group']},'composition_beta':mono_beta.tolist(),'source_delta_AU_beta':au_beta,'source_substitution_means':sub_beta,'source_substitution_pair_counts':{k:len(v) for k,v in sub.items()},'order_beta':{},'source_parameter_sha256':sha256(old/'fitted_parameters.json'),'source_inventory_sha256':sha256(old/'sequence_inventory.csv'),'target_outcomes_used':False}
    result=target.copy();result['no_change']=0.;result['srle_composition']=dx[:,:4]@mono_beta
    result['srle_delta_AU']=(dx[:,0]+dx[:,3])*au_beta
    result['srle_substitution']=[sub_beta[a+'>'+b] for a,b in zip(target.reference_nt,target.alternate_nt)]
    for name,sl in [('2mer',slice(4,20)),('3mer',slice(20,84)),('kmer123',slice(0,84))]:
        beta=np.array(c[name]['coefficient'])/np.array(c[name]['scale']);weights['order_beta'][name]=beta.tolist()
        result['srle_'+name+'_full']=result.srle_composition+dx[:,sl]@beta
        if name=='2mer':result['srle_2mer_order_only']=dx[:,sl]@beta
    # Exact feature definition equals the original count generator on both lengths.
    from src.research_20260921.robustness import count_features
    subset=target.iloc[:7]
    assert np.array_equal(delta_features(subset),count_features(subset.mutant_sequence.to_numpy())-count_features(subset.parent_sequence.to_numpy()))
    result=pd.concat([result,pd.DataFrame(dx,columns=['delta_'+w for w in WORDS])],axis=1)
    result['target_outcome_accessed']=False
    csvsave(ART/'GSE330741_prefit_predictions_without_outcomes.csv',result)
    jsave(OUT/'source_predictor.json',weights)
    jsave(OUT/'source_prediction_receipt.json',{'status':'PASS','rows':len(result),'models':config()['test_a_models'],'source_training_sequences':int(train.sum()),'target_outcome_accessed':False,'prediction_sha256':sha256(ART/'GSE330741_prefit_predictions_without_outcomes.csv'),'features':'unchanged raw overlapping full-insert 1/2/3-mer counts; unchanged regions cancel in differences','support_warning':'190nt composition-changing SNPs are outside demonstrated 6nt composition-preserving support; mathematically defined extrapolation','sign':1,'no_parameter_refitting_of_primary':True})
    print('Frozen source predictions generated for',len(result),'target designs; no outcomes')

if __name__=='__main__':run()
