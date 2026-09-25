from .common import *
import itertools

VOCAB={k:[''.join(p) for p in itertools.product('ACGT',repeat=k)] for k in (1,2,3)}
MOTIFS=('CCC','CCTCCC','ATAT','TATA','TGCA','TGTA')
BASELINES=('no_change','train_mean','edit_size','edit_position','composition','delta_AU','delta_1mer','delta_2mer','delta_3mer','delta123','local_window','motifs','random_projection','paired')


def frequencies(sequences,k):
    lookup={s:i for i,s in enumerate(VOCAB[k])}
    x=np.zeros((len(sequences),len(lookup)))
    for i,s in enumerate(sequences):
        for j in range(len(s)-k+1): x[i,lookup[s[j:j+k]]]+=1
        x[i]/=max(1,len(s)-k+1)
    return x


def features(frame):
    parent=frame.parent_sequence.tolist(); mutant=frame.mutant_sequence.tolist()
    p={k:frequencies(parent,k) for k in (1,2,3)}
    d={k:frequencies(mutant,k)-p[k] for k in (1,2,3)}
    geometry=[]; windows=[]
    for a,b in zip(parent,mutant):
        pos=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
        if not pos or len(a)!=len(b): raise ValueError('Expected aligned edited sequence')
        geometry.append([len(pos),min(pos)/len(a),max(pos)/len(a),np.mean(pos)/len(a),(max(pos)-min(pos)+1)/len(a)])
        w=np.zeros((2,11,4))
        for center in pos:
            for offset in range(-5,6):
                j=center+offset
                if 0<=j<len(a):
                    w[0,offset+5,'ACGT'.index(a[j])]+=1
                    w[1,offset+5,'ACGT'.index(b[j])]+=1
                    w[1,offset+5,'ACGT'.index(a[j])]-=1
        windows.append(w.ravel()/len(pos))
    g=np.array(geometry); local=np.array(windows); delta=np.column_stack([d[k] for k in (1,2,3)])
    motifs=np.array([[sum(b[j:j+len(m)]==m for j in range(len(b)-len(m)+1))-sum(a[j:j+len(m)]==m for j in range(len(a)-len(m)+1)) for m in MOTIFS] for a,b in zip(parent,mutant)])
    interaction=(p[1][:,:,None]*d[1][:,None,:]).reshape(len(frame),-1)
    projection=np.random.default_rng(20260925).normal(size=(84,16))/np.sqrt(84)
    return {'train_mean':np.ones((len(frame),1)),'edit_size':g[:,:1],'edit_position':g[:,1:],'composition':np.column_stack([p[1],p[1]+d[1]]),
        'delta_AU':(d[1][:,0]+d[1][:,3])[:,None],**{'delta_'+str(k)+'mer':d[k] for k in (1,2,3)},
        'delta123':delta,'local_window':local,'motifs':motifs,'random_projection':delta@projection,
        'paired':np.column_stack([delta,g,local,interaction])}
