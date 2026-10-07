"""Synthetic analytic tests only; cached encoder is never imported."""
import unittest
from .features import np,pooled_delta,lookup_delta,projection_arrays,changed_positions


class SingleBaseTests(unittest.TestCase):
    def setUp(self):
        self.pg,self.pl=projection_arrays()
        self.parent='ACGTACGT';self.mutant='TCGTACGA'
        rng=np.random.default_rng(41)
        self.hp=rng.normal(size=(10,512)).astype(np.float32)
        self.hm=rng.normal(size=(10,512)).astype(np.float32)

    def test_projection_pooling_commute(self):
        changed=changed_positions(self.parent,self.mutant)
        after=pooled_delta(self.parent,self.mutant,self.hp,self.hm,self.pg,self.pl)
        before=np.r_[(self.hm[1:-1]@self.pg).mean(0)-(self.hp[1:-1]@self.pg).mean(0),
                     ((self.hm[changed+1]@self.pl)-(self.hp[changed+1]@self.pl)).mean(0)]
        np.testing.assert_allclose(after,before,rtol=1e-5,atol=5e-6)

    def test_no_edit_and_reversal(self):
        np.testing.assert_array_equal(pooled_delta(self.parent,self.parent,self.hp,self.hm,self.pg,self.pl),np.zeros(256))
        a=pooled_delta(self.parent,self.mutant,self.hp,self.hm,self.pg,self.pl)
        b=pooled_delta(self.mutant,self.parent,self.hm,self.hp,self.pg,self.pl)
        np.testing.assert_array_equal(a,-b)
        np.testing.assert_array_equal(lookup_delta(self.parent,self.mutant,self.pg,self.pl),-lookup_delta(self.mutant,self.parent,self.pg,self.pl))

    def test_single_base_exact_lookup_and_special_exclusion(self):
        hp=np.zeros((10,512),dtype=np.float32);hm=hp.copy();ids={b:i for i,b in enumerate('ACGT')}
        for i,(p,m) in enumerate(zip(self.parent,self.mutant)):
            hp[i+1,ids[p]]=1;hm[i+1,ids[m]]=1
        hp[0]=300;hm[-1]=-400
        np.testing.assert_allclose(pooled_delta(self.parent,self.mutant,hp,hm,self.pg,self.pl),
                                   lookup_delta(self.parent,self.mutant,self.pg,self.pl),rtol=1e-5,atol=2e-7)
        np.testing.assert_array_equal(changed_positions(self.parent,self.mutant),[0,7])


if __name__=='__main__':unittest.main()
