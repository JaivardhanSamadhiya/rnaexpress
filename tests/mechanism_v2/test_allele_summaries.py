import numpy as np
import pytest
from src.mechanism_v2.allele_summaries import pooled_features,decoded_sequence_hashes


def test_sequence_hash_encoding_is_explicit_and_strict():
    hashes=['0'*64,'a'*64]
    np.testing.assert_array_equal(decoded_sequence_hashes(np.asarray(hashes,dtype='S64')),np.asarray(hashes))
    np.testing.assert_array_equal(decoded_sequence_hashes(np.asarray(hashes,dtype='U64')),np.asarray(hashes))
    with pytest.raises(ValueError):decoded_sequence_hashes(np.asarray(['bad'],dtype='S64'))
    with pytest.raises(ValueError):decoded_sequence_hashes(np.asarray(['a'*65],dtype='S65'))


def test_absolute_pooling_reproduces_signed_delta():
    p=np.array([[.1,.2,.3,.4],[.2,.1,.25,.45]],dtype=np.float32)
    mix=np.array([.3,.4],dtype=np.float32);lengths=np.array([4,4])
    a=pooled_features(p,mix,np.array([0]),np.array([0]),np.array([2]),lengths)
    b=pooled_features(p,mix,np.array([1]),np.array([0]),np.array([2]),lengths)
    np.testing.assert_allclose(b-a,[[0,0,0,.1]],atol=1e-7)


def test_absolute_windows_are_clipped_to_native_length():
    p=np.zeros((2,150),np.float32);p[0,20]=.6;p[0,140]=.4;p[1,20]=.8;p[1,140]=.2
    out=pooled_features(p,np.array([.5,.5]),np.array([0,1]),np.array([20,20]),np.array([21,21]),np.array([150,150]))
    np.testing.assert_allclose(out[:,:3],[[.6,.6,.6],[.8,.8,.8]])
