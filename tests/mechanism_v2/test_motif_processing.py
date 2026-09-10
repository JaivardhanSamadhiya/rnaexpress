import numpy as np
import pytest
from src.mechanism_v2.motif_processing import motif_spans,motif_values,processing_values


def test_overlapping_motifs_are_counted():
    assert motif_spans('TGTGTGTG','TGTGTG')==[(0,6),(2,8)]


def test_processing_pas_and_donor_change():
    assert processing_values('CCCAATAAACCC')[2]>0
    assert processing_values('CCCACTAAACCC')[2]==0
    assert processing_values('CAGGTAAGT')[0]>0
    assert processing_values('CAGGCAAGT')[0]==0


def test_no_motif_is_real_zero_not_missing_data():
    assert motif_values('A'*40)==[0.]*8
    with pytest.raises(ValueError):motif_values('ACNG')


def test_site_accessibility_bounds_and_repeatability():
    seq='A'*12+'TGTATATA'+'A'*12+'ACTAAC'+'A'*12
    a=np.array(motif_values(seq));b=np.array(motif_values(seq))
    np.testing.assert_array_equal(a,b)
    assert (a[4:]>=0).all() and (a[4:]<=a[:4]+1e-8).all()
    assert a[0]>0 and a[1]>0
