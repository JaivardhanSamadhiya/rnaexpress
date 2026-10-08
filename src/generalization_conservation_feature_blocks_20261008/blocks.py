"""Reference-conservation-weighted substitution deltas; pure stdlib contracts."""
import math
ALPHABET='ACGT'
TRACKS=('phyloP60wayAll','phastCons60way')
COMPLEMENT=dict(zip('ACGT','TGCA'))


def substitutions(parent,mutant):
    assert isinstance(parent,str) and isinstance(mutant,str)
    assert len(parent)==len(mutant)>0 and set(parent+mutant)<=set(ALPHABET)
    changed=[i for i,(a,b) in enumerate(zip(parent,mutant)) if a!=b]
    assert 1<=len(changed)<=6
    return changed


def compute(parent,mutant,sites,annotations,available):
    changed=substitutions(parent,mutant)
    assert type(available) is bool
    if not available:return [0.]*8,[0.]*8
    assert len(sites)==len(changed)
    assert [s['insert_position0'] for s in sites]==changed
    length=len(parent);terms_raw=[[] for _ in range(8)];terms_native=[[] for _ in range(8)]
    for site in sites:
        i=site['insert_position0'];a,b=parent[i],mutant[i]
        assert site['expressed_reference']==a and site['expressed_alternate']==b
        assert site['strand'] in ('+','-')
        ga,gb=(a,b) if site['strand']=='+' else (COMPLEMENT[a],COMPLEMENT[b])
        assert site['genomic_reference']==ga and site['genomic_alternate']==gb
        assert type(site['genomic_position0']) is int and site['genomic_position0']>=0
        annotation=annotations[site['chrom'],site['genomic_position0']]
        assert annotation['reference']==ga and gb in annotation['alternates']
        score=annotation['scores']
        for t in TRACKS:
            assert type(score[t]) in (int,float) and math.isfinite(score[t])
        assert 0<=score['phastCons60way']<=1
        # 0-basedi/L, SUM/L. No division by number of edits, no clipping.
        for j,nt in enumerate(ALPHABET):
            delta=int(b==nt)-int(a==nt)
            for k in (1,2):terms_raw[(k-1)*4+j].append((i/length)**k*delta/length)
            for t,track in enumerate(TRACKS):terms_native[t*4+j].append(score[track]*delta/length)
    raw=[math.fsum(t) for t in terms_raw];native=[math.fsum(t) for t in terms_native]
    assert all(math.isfinite(x) for x in raw+native)
    return raw,native
