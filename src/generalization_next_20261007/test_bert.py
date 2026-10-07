"""Scoped synthetic-only projection and exact-token pooling QA."""
import unittest
from .common import np
from .route_bert import affected_starts, lookup_pair, projected_pair, projections, vocabulary


class BertFeatureTests(unittest.TestCase):
    def setUp(self):
        self.pg,self.pl=projections()
        self.parent='ACGTAACCGGTTAACCTTGG'
        self.mutant=self.parent[:5]+'T'+self.parent[6:12]+'C'+self.parent[13:]
        rng=np.random.default_rng(92)
        self.hp=rng.normal(size=(len(self.parent),768)).astype(np.float32)
        self.hm=rng.normal(size=(len(self.parent),768)).astype(np.float32)

    def test_projection_commutes_pooling(self):
        starts=affected_starts(self.parent,self.mutant)
        raw=np.r_[self.hm[1:-1].mean(0)-self.hp[1:-1].mean(0),
                  (self.hm[starts+1]-self.hp[starts+1]).mean(0)]
        expected=np.r_[raw[:768]@self.pg,raw[768:]@self.pl]
        actual=projected_pair(self.parent,self.mutant,self.hp,self.hm,self.pg,self.pl)
        projected_first=np.r_[(self.hm[1:-1]@self.pg).mean(0)-(self.hp[1:-1]@self.pg).mean(0),
                              ((self.hm[starts+1]@self.pl)-(self.hp[starts+1]@self.pl)).mean(0)]
        np.testing.assert_allclose(actual,expected,rtol=1e-5,atol=5e-6)
        np.testing.assert_allclose(actual,projected_first,rtol=1e-5,atol=5e-6)

    def test_no_edit_and_reverse(self):
        np.testing.assert_array_equal(projected_pair(self.parent,self.parent,self.hp,self.hm,self.pg,self.pl),np.zeros(256))
        np.testing.assert_array_equal(lookup_pair(self.parent,self.parent,self.pg,self.pl),np.zeros(256))
        a=projected_pair(self.parent,self.mutant,self.hp,self.hm,self.pg,self.pl)
        b=projected_pair(self.mutant,self.parent,self.hm,self.hp,self.pg,self.pl)
        np.testing.assert_array_equal(a,-b)
        np.testing.assert_array_equal(lookup_pair(self.parent,self.mutant,self.pg,self.pl),-lookup_pair(self.mutant,self.parent,self.pg,self.pl))

    def test_exact_onehot_control(self):
        ids=vocabulary()
        hp=np.zeros((len(self.parent),768),dtype=np.float32)
        hm=np.zeros_like(hp)
        for i in range(len(self.parent)-2):
            hp[i+1,ids[self.parent[i:i+3]]]=1
            hm[i+1,ids[self.mutant[i:i+3]]]=1
        expected=projected_pair(self.parent,self.mutant,hp,hm,self.pg,self.pl)
        np.testing.assert_allclose(lookup_pair(self.parent,self.mutant,self.pg,self.pl),expected,rtol=1e-5,atol=2e-7)
        self.assertEqual(len(ids),64)
        self.assertLessEqual(np.linalg.matrix_rank(self.pg[:64]),64)

    def test_boundaries_and_special_tokens(self):
        parent='ACGTAC';mutant='TCGTAA'
        np.testing.assert_array_equal(affected_starts(parent,mutant),[0,3])
        hp=np.ones((6,768),dtype=np.float32);hm=hp.copy()
        hm[0]=100;hm[-1]=100
        np.testing.assert_array_equal(projected_pair(parent,mutant,hp,hm,self.pg,self.pl),np.zeros(256))


if __name__=='__main__':unittest.main()
