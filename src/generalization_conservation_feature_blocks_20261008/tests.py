"""Invented sequences only: physical edits, strand, missingness and algebra."""
import unittest
from .blocks import compute,substitutions,TRACKS


def site(i,a,b,minus=False):
    from .blocks import COMPLEMENT
    return {'insert_position0':i,'chrom':'chrInvented','genomic_position0':100+i,
        'expressed_reference':a,'expressed_alternate':b,'strand':'-' if minus else '+',
        'genomic_reference':COMPLEMENT[a] if minus else a,'genomic_alternate':COMPLEMENT[b] if minus else b}


def scores(pos,phylo=-2.,phast=.5,minus=False):return {('chrInvented',100+pos):{'reference':'T' if minus else 'A','alternates':['G' if minus else 'C'],'scores':dict(zip(TRACKS,(phylo,phast)))}}


class Contracts(unittest.TestCase):
    def test_zero_vs_missing(self):
        raw,nat=compute('AAAA','ACAA',[site(1,'A','C')],scores(1,0.,0.),True)
        self.assertNotEqual(raw,[0.]*8);self.assertEqual(nat,[0.]*8)
        self.assertEqual(compute('AAAA','ACAA',[],{},False),([0.]*8,[0.]*8))
    def test_negative_phylo_retained(self):
        _,n=compute('AAAA','ACAA',[site(1,'A','C')],scores(1),True)
        self.assertEqual(n[:4],[.5,-.5,0.,0.])
    def test_position_is_zero_based(self):
        r,_=compute('AAAA','CAAA',[site(0,'A','C')],scores(0),True)
        self.assertEqual(r,[0.]*8)
    def test_sum_not_mean_over_edits(self):
        s=[site(1,'A','C'),site(2,'A','C')];a={**scores(1,4.,1.),**scores(2,4.,1.)}
        _,n=compute('AAAA','ACCA',s,a,True);self.assertEqual(n[1],2.)
    def test_parent_length_normalization(self):
        _,n=compute('AAAA','ACAA',[site(1,'A','C')],scores(1,4.,1.),True);self.assertEqual(n[1],1.)
    def test_strand_uses_expressed_allele(self):
        x=compute('AAAA','ACAA',[site(1,'A','C',True)],scores(1,minus=True),True)
        self.assertEqual(x,compute('AAAA','ACAA',[site(1,'A','C')],scores(1),True))
    def test_wrong_reference_rejected(self):
        s=site(1,'A','C');s['genomic_reference']='G'
        with self.assertRaises(AssertionError):compute('AAAA','ACAA',[s],scores(1),True)
    def test_wrong_edit_site_rejected(self):
        with self.assertRaises(AssertionError):compute('AAAA','ACAA',[site(2,'A','C')],scores(2),True)
    def test_missing_track_rejected_if_available(self):
        a=scores(1);a['chrInvented',101]['scores'][TRACKS[0]]=None
        with self.assertRaises(AssertionError):compute('AAAA','ACAA',[site(1,'A','C')],a,True)
    def test_invalid_phast_rejected(self):
        with self.assertRaises(AssertionError):compute('AAAA','ACAA',[site(1,'A','C')],scores(1,1.,1.01),True)
    def test_nonfinite_rejected(self):
        with self.assertRaises(AssertionError):compute('AAAA','ACAA',[site(1,'A','C')],scores(1,float('nan')),True)
    def test_duplicate_sites_rejected(self):
        with self.assertRaises(AssertionError):compute('AAAA','ACAA',[site(1,'A','C')]*2,scores(1),True)
    def test_allele_groups_sum_zero(self):
        r,n=compute('AAAA','ACAA',[site(1,'A','C')],scores(1),True)
        for value in (r,n):
            self.assertEqual(sum(value[:4]),0.);self.assertEqual(sum(value[4:]),0.)
    def test_six_physical_edits_admitted(self):self.assertEqual(substitutions('AAAAAA','CCCCCC'),list(range(6)))
    def test_noop_rejected(self):
        with self.assertRaises(AssertionError):substitutions('AAAA','AAAA')
    def test_seven_changes_rejected(self):
        with self.assertRaises(AssertionError):substitutions('AAAAAAA','CCCCCCC')
    def test_indel_rejected(self):
        with self.assertRaises(AssertionError):substitutions('AAAA','AAA')
    def test_unknown_bases_rejected(self):
        with self.assertRaises(AssertionError):substitutions('AAAA','ANAA')
    def test_availability_must_be_boolean(self):
        with self.assertRaises(AssertionError):compute('AAAA','ACAA',[],{},0)
    def test_annotation_reference_disagreement_rejected(self):
        a=scores(1);a['chrInvented',101]['reference']='G'
        with self.assertRaises(AssertionError):compute('AAAA','ACAA',[site(1,'A','C')],a,True)
    def test_uncertified_alternate_rejected(self):
        a=scores(1);a['chrInvented',101]['alternates']=['G']
        with self.assertRaises(AssertionError):compute('AAAA','ACAA',[site(1,'A','C')],a,True)


if __name__=='__main__':unittest.main()
