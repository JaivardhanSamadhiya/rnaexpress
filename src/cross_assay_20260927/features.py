from .common import *
from collections import Counter
from functools import lru_cache
import io
WORDS=[''.join(t) for k in (1,2,3) for t in itertools.product('ACGT',repeat=k)]
SUBS=[a+'>'+b for a in 'ACGT' for b in 'ACGT' if a!=b]
@lru_cache(200000)
def counts(seq):
    c=Counter(seq[i:i+k] for k in (1,2,3) for i in range(len(seq)-k+1));return np.array([c[w] for w in WORDS],float)
def build(frame):
    metadata=[];delta=[];contexts={str(w):[] for w in (3,10,25,50,'full')}
    for r in frame.itertuples():
        p,m=r.parent_sequence,r.mutant_sequence;ix=[i for i,(a,b) in enumerate(zip(p,m)) if a!=b];n=len(p);s=Counter(p[i]+'>'+m[i] for i in ix)
        pos=(np.mean(ix)/(n-1)) if n>1 else 0
        metadata.append([len(ix),np.log1p(n),pos,pos*pos,(max(ix)-min(ix)+1)/n,float(0 in ix or n-1 in ix)]+[s[v] for v in SUBS])
        delta.append(counts(m)-counts(p))
        for w in contexts:
            local=p if w=='full' else p[max(0,min(ix)-int(w)):max(ix)+int(w)+1]
            c=counts(local)[:20];den=np.array([len(local)]*4+[max(1,len(local)-1)]*16);contexts[w].append(c/den)
    meta=np.array(metadata);dx=np.array(delta);xs={'metadata':meta,'composition':np.column_stack([meta,dx[:,:4]]),'delta2':np.column_stack([meta,dx[:,:20]]),'kmer123':np.column_stack([meta,dx])}
    names={'metadata':['edit_size','log_parent_length','relative_edit_midpoint','relative_midpoint_squared','edit_span_fraction','boundary_edit']+SUBS}
    names['composition']=names['metadata']+['delta_'+w for w in WORDS[:4]]
    names['delta2']=names['metadata']+['delta_'+w for w in WORDS[:20]]
    names['kmer123']=names['metadata']+['delta_'+w for w in WORDS]
    for w in contexts:
        c=np.array(contexts[w]);inter1=np.einsum('ij,ik->ijk',dx[:,:4],c).reshape(len(frame),-1);inter2=np.einsum('ij,ik->ijk',dx[:,4:20],c[:,:4]).reshape(len(frame),-1)
        xs['interaction_'+w]=np.column_stack([meta,dx,inter1,inter2]);names['interaction_'+w]=names['kmer123']+[f'delta_{a}*parentfreq_{b}' for a in WORDS[:4] for b in WORDS[:20]]+[f'delta_{a}*parentfreq_{b}' for a in WORDS[4:20] for b in WORDS[:4]]
    xs['feasibility']=np.column_stack([meta,dx[:,:4],np.array(contexts['10'])[:,:4]])
    return xs,names
def run():
    f=pd.read_csv(ART/'canonical_interventions.csv',low_memory=False)
    # Features for core and permitted SIRLOIN discovery diagnostics; no reserved replicates.
    f=f[f.primary_eligible | (f.dataset.eq('sirloin')&f.candidate_set_eligible)].reset_index(drop=True)
    xs,names=build(f);csvsave(OUT/'model_row_index.csv',f[['intervention_id','dataset','parent_context_id','biological_component','held_parent_fold']])
    buf=io.BytesIO();np.savez_compressed(buf,**{k:v.astype(np.float32) for k,v in xs.items()});save(ART/'features.npz',buf.getvalue())
    jsave(OUT/'feature_schema.json',{'columns':names,'windows':[3,10,25,50,'full'],'context_interactions':'delta mono x parent mono/dinucleotide frequencies and delta dinucleotide x parent mono frequencies','local_delta_equivalence':'With >=2 unchanged flanking bases all 1-3mer deltas equal full-insert deltas; window experiment changes parent-context interactions, not duplicate delta vectors.','encoder':'explicit sequences; frozen pretrained comparator admitted separately only where cache coverage exists','arrays_sha256':sha256(ART/'features.npz'),'rows':len(f)})
    print('Features',len(f),{k:v.shape[1] for k,v in xs.items()})
if __name__=='__main__':run()
