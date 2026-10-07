"""Small synthetic context and permutation invariants, no project outcomes."""
from .common import np, pd, encoded_frame
from .permutation import permute_training
from src.cross_assay_20260927.features import build, counts, WORDS

def test_local_context_features_are_recomputed_at_shifted_edit():
    original = pd.DataFrame([{'dataset':'srle','parent_sequence':'AAAAAA','mutant_sequence':'AACAAA'}])
    encoded = encoded_frame(original)
    parent, mutant = encoded.parent_sequence.iloc[0], encoded.mutant_sequence.iloc[0]
    assert len(parent) == len(mutant) == 46
    assert [i for i, (p, m) in enumerate(zip(parent, mutant)) if p != m] == [22]
    assert original.parent_sequence.iloc[0] == 'AAAAAA'
    features, _ = build(encoded)
    meta = features['metadata'][0]
    assert meta[0] == 1 and meta[1] == np.log1p(46)
    assert meta[2] == 22/45 and meta[4] == 1/46 and meta[5] == 0
    expected = np.array([sum(mutant[i:i+len(w)] == w for i in range(47-len(w)))
                         -sum(parent[i:i+len(w)] == w for i in range(47-len(w))) for w in WORDS])
    np.testing.assert_array_equal(features['kmer123'][0, 18:], expected)

def test_training_permutation_preserves_each_context_and_input():
    original = pd.DataFrame({'dataset':['a']*8,'biological_component':['g']*8,
        'parent_context_id':['p']*4+['q']*4,'intervention_id':list('abcdefgh'),
        'measured_delta':[-3.,-1.,1.,3.,10.,20.,30.,40.]})
    shuffled = permute_training(original)
    replay = permute_training(original)
    pd.testing.assert_frame_equal(shuffled, replay)
    np.testing.assert_array_equal(original.measured_delta, [-3.,-1.,1.,3.,10.,20.,30.,40.])
    for context in ['p','q']:
        assert sorted(shuffled[shuffled.parent_context_id.eq(context)].measured_delta) == sorted(original[original.parent_context_id.eq(context)].measured_delta)
    assert not np.array_equal(shuffled.measured_delta, original.measured_delta)
