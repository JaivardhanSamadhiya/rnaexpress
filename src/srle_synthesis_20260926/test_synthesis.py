import unittest
from .common import *
import predict_edit_candidates as api

class PrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=api.load_bundle();cls.parent=sorted(cls.bundle['parents'])[0];cls.candidates=cls.bundle['parents'][cls.parent]['candidates']
    def test_normalization(self):self.assertEqual(api.normalize(' acuuga '),'ACTTGA')
    def test_invalid_sequence(self):
        for s in ('ACGNTA','ACG','AAAAAAA',''):
            with self.assertRaises(ValueError):api.normalize(s)
    def test_valid_swap(self):self.assertEqual(api.validate_edit('AAACTG','AAAGTC'),[4,6])
    def test_invalid_edits(self):
        for a,b in [('AAAAAA','AAAACA'),('AAAAAA','AAAAAA'),('ACGTAC','CATGCA')]:
            with self.assertRaises(ValueError):api.validate_edit(a,b)
    def test_count_overlapping(self):
        c=api.counts('AAAAAA','2mer');self.assertEqual(c[0],5);self.assertEqual(sum(c),5)
        self.assertEqual(sum(api.counts('AAAAAA','kmer123')),15)
    def test_complete_roster_required(self):
        with self.assertRaises(ValueError):api.predict(self.parent,self.candidates[:-1],bundle=self.bundle)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):api.predict(self.parent,self.candidates+[self.candidates[0]],bundle=self.bundle)
    def test_unknown_parent(self):
        with self.assertRaises(ValueError):api.predict('AAAAAA',['CAAAAA'],bundle=self.bundle)
    def test_bad_mode(self):
        for kwargs in ({'direction':'up'},{'model':'new_model'}):
            with self.assertRaises(ValueError):api.predict(self.parent,self.candidates,bundle=self.bundle,**kwargs)
    def test_rna_and_dna_same(self):
        a=api.predict(self.parent,self.candidates,bundle=self.bundle)
        b=api.predict(self.parent.replace('T','U'),[s.replace('T','U') for s in self.candidates],bundle=self.bundle)
        self.assertEqual(a,b)
    def test_candidate_input_order_invariant(self):
        self.assertEqual(api.predict(self.parent,self.candidates,bundle=self.bundle),api.predict(self.parent,list(reversed(self.candidates)),bundle=self.bundle))
    def test_direction_inverts_ranking(self):
        a=api.predict(self.parent,self.candidates,'increase',bundle=self.bundle)['candidates']
        b=api.predict(self.parent,self.candidates,'decrease',bundle=self.bundle)['candidates']
        self.assertEqual(a[0]['predicted_effect'],max(x['predicted_effect'] for x in a))
        self.assertEqual(b[0]['predicted_effect'],min(x['predicted_effect'] for x in b))
    def test_no_individual_outcome_fields(self):
        self.assertEqual(set(self.bundle),{'schema','scope','parents','scores','folds','cohort_risk'})
        for value in self.bundle['parents'].values():self.assertEqual(set(value),{'candidates','group'})
        self.assertEqual(set(self.bundle['scores']),{'2mer','kmer123'})
    def test_constant_count_coefficient_offset_cancels(self):
        a=np.array(api.counts('AAACTG','2mer'));b=np.array(api.counts('AAAGTC','2mer'));w=np.arange(16)/17
        self.assertAlmostEqual((a-b)@w,(a-b)@(w+42),places=12)
    def test_endpoint_interaction_identity(self):
        w=np.arange(16).reshape(4,4)**2/17;g=w.mean();r=w.mean(1)-g;c=w.mean(0)-g;inter=w-g-r[:,None]-c[None,:]
        parent='AAACTG';mutant='AAAGTC';delta=np.array(api.counts(mutant,'2mer'))-api.counts(parent,'2mer')
        endpoint=-(r['ACGT'.index(mutant[-1])]-r['ACGT'.index(parent[-1])])-(c['ACGT'.index(mutant[0])]-c['ACGT'.index(parent[0])])
        self.assertAlmostEqual(delta@w.ravel(),endpoint+delta@inter.ravel())

if __name__=='__main__':unittest.main()
