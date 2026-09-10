import numpy as np
from rapidfuzz.distance import Levenshtein
from src.mechanism_v2.sequence_leakage import exact_near_components


def test_seed_audit_matches_exhaustive_components_and_indels():
    rng=np.random.default_rng(13)
    sequences=[''.join(rng.choice(list('ACGT'),99)) for _ in range(6)]
    for original in sequences.copy():
        mutated=original[:20]+('A' if original[20]!='A' else 'C')+original[21:]
        sequences.extend([mutated,mutated[:30]+'T'+mutated[30:]])
    groups=[f'g{i}' for i in range(len(sequences))]
    found,_=exact_near_components(sequences,groups,0.95)
    for i,a in enumerate(sequences):
        for j,b in enumerate(sequences):
            if Levenshtein.distance(a,b)<=0.05*max(len(a),len(b))+1e-9:assert found[i]==found[j]
    assert len(set(found))==6


def test_near_duplicate_mutant_joins_other_parent():
    sequences=['A'*100,'C'*100,'A'*95+'C'*5]
    groups=['parent_a','parent_b','parent_b']
    found,audit=exact_near_components(sequences,groups,0.95)
    assert len(set(found))==1 and audit['final_components']==1
