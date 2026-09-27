from .common import *

SUBSTITUTIONS=[a+'>'+b for a in 'ACGT' for b in 'ACGT' if a!=b]

def matrices(frame):
    delta=delta_features(frame);sid=np.array([a+'>'+b for a,b in zip(frame.reference_nt,frame.alternate_nt)])
    sub=(sid[:,None]==np.array(SUBSTITUTIONS)[None,:]).astype(float)
    p=(frame.edit_position_1based.to_numpy(float)-1)/189
    position=np.column_stack([p,p*p,((p==0)|(p==1)).astype(float)])
    simple=np.column_stack([sub,delta[:,:4],position])
    values={'delta_AU':(delta[:,0]+delta[:,3])[:,None],'delta1':delta[:,:4],'substitution':sub,'position':position,
       'substitution_composition':np.column_stack([sub,delta[:,:4]]),'substitution_position':np.column_stack([sub,position]),'simple_full':simple,
       'delta2':delta[:,4:20],'delta3':delta[:,20:84],'kmer123':delta,'simple_full_delta2':np.column_stack([simple,delta[:,4:20]]),'simple_full_delta2_delta3':np.column_stack([simple,delta[:,4:20],delta[:,20:84]])}
    assert all(np.isfinite(x).all() for x in values.values())
    return values

def disjoint_train(frame,held):
    group=frame.loc[frame.parent_id.eq(held),'overlap_component'].unique();assert len(group)==1
    return ~frame.overlap_component.eq(group[0]).to_numpy()
