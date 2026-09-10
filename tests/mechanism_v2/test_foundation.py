import itertools
import numpy as np
import pandas as pd
import pytest
from src.mechanism_v2.io import cache_key, load_development, open_holdout, output_path, write_once
from src.mechanism_v2.primitives import align, bijective_map, choose_recipe, delta, edit_band


@pytest.mark.parametrize('path', ['results/finalshot/x.json', '../elsewhere.json',
    'results/mechanism_v2/../../finalshot/x.json', 'data/frozen/outcomes/anything.csv'])
def test_output_protection(path):
    with pytest.raises(PermissionError):
        output_path(path)


def test_sealed_before_reader(monkeypatch):
    def fail(*a, **kw):
        pytest.fail('A data reader was called before authorization')
    monkeypatch.setattr(pd, 'read_csv', fail)
    for path in ('astrocyte.csv', 'data/frozen/outcomes/astrocyte.csv', 'nzip.csv', 'unknown.csv'):
        with pytest.raises(PermissionError):
            load_development(path)
    with pytest.raises(PermissionError):
        open_holdout(authorized=True, frozen=True)


def test_cache_invalidates_all_dependencies():
    base = cache_key('ACGU', 'a'*64, {'temperature': 37})
    assert base == cache_key('ACGT', 'a'*64, {'temperature': 37})
    assert len({base, cache_key('ACGA','a'*64,{'temperature':37}),
        cache_key('ACGT','b'*64,{'temperature':37}),
        cache_key('ACGT','a'*64,{'temperature':25})}) == 4


def test_delta_antisymmetry():
    a, b = np.arange(10.), np.arange(10.)**2
    assert np.array_equal(delta(a,b), -delta(b,a))
    assert np.count_nonzero(delta(a,a)) == 0
    with pytest.raises(ValueError):
        delta(a,b[:5])


@pytest.mark.parametrize('r,m', [('ACGT','ATGT'), ('ACGT','ACAGT'), ('ACAGT','ACGT'),
    ('ACGT','TACGT'), ('TACGT','ACGT'), ('ACGT','ACGTT'), ('ACGTT','ACGT')])
def test_alignment_reconstructs_and_windows(r,m):
    a = align(r,m)
    assert ''.join(r[i] for i in a.reference_indices if i >= 0) == r
    assert ''.join(m[i] for i in a.mutant_indices if i >= 0) == m
    assert a.windows(100) == ((0,len(r)),(0,len(m)))
    for (start,end), seq in zip(a.windows(1), (r,m)):
        assert 0 <= start <= end <= len(seq)


def test_insertion_boundary():
    assert align('ACGT','ACAGT').windows(0) == ((2,2),(2,3))
    assert align('ACAGT','ACGT').windows(0) == ((2,3),(2,2))


def test_bands():
    assert list(edit_band([0,1,2,5,6,10,11,25,26,50,51])) == [
        '0','1','2-5','2-5','6-10','6-10','11-25','11-25','26-50','26-50','>50']
    with pytest.raises(ValueError):
        edit_band([np.nan])


def test_total_tie_order():
    records = [{'recipe_id':n,'regret':r,'rank':k,'complexity':c} for n,r,k,c in
               [('a',.10,.6,2),('b',.101,.7,3),('c',.102,.7,1),('d',.11,.9,1)]]
    for order in itertools.permutations(records):
        assert choose_recipe(order) == 'c'


def test_bijections_and_partition_locality():
    frame = pd.DataFrame({'intervention_id':range(18), 'fold':[0]*9+[1]*9,
        'source':['s']*18, 'parent':['a']*4+['b']*3+['c']*2+['d']*8+['e']})
    donors, eligible, audit = bijective_map(frame,partition='fold',strata=['source'],unit='parent')
    assert np.array_equal(np.sort(donors),np.arange(18))
    assert eligible[:9].all() and not eligible[9:].any()
    assert audit[1]['reason'] == 'cross_unit_derangement_impossible'
    assert np.array_equal(donors, bijective_map(frame,partition='fold',strata=['source'],unit='parent')[0])
    assert np.all(frame.parent.to_numpy()[eligible] != frame.iloc[donors].parent.to_numpy()[eligible])


def test_bijection_unequal_units_exhaustive():
    for counts in itertools.product(range(1,5), repeat=3):
        units = np.repeat(['a','b','c'], counts)
        f = pd.DataFrame({'intervention_id':range(len(units)),'fold':0,'unit':units})
        d,e,_ = bijective_map(f,partition='fold',unit='unit')
        assert e.all() == (max(counts)*2 <= sum(counts))
        assert np.array_equal(np.sort(d),np.arange(len(units)))
