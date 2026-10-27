"""Only invented metadata/arrays; no numerical libraries or project inputs."""
import itertools
import math
import unittest
from . import layout, scalar


def dna(number, width=8):
    return ''.join('ACGT'[(number//4**j)%4] for j in range(width))


def fixture():
    rows = []
    for study_index, study in enumerate(layout.STUDIES):
        for context in range(3):
            number = 1+study_index*3+context
            parent = dna(number)+'AA'
            for candidate, suffix in enumerate(('CC','GG','TT')):
                rows.append(dict(zip(('intervention_id','dataset','biological_component',
                                      'parent_context_id','parent_sequence','mutant_sequence'),
                                     (f'id{number:02d}_{candidate}',study,f'gene{number:02d}',
                                      f'context{number:02d}',parent,dna(number)+suffix))))
    return rows


def problem():
    rows = layout.metadata(fixture())
    catalog = layout.menus(rows,range(len(rows)))
    effects = tuple(float(i%3-1) for i in range(len(rows)))
    x = tuple((float(i%3-1),(-1.)**i,2.,1e-10*(i%3)) for i in range(len(rows)))
    supplied = {m['context']:tuple(itertools.combinations(m['indices'],2)) for m in catalog}
    pairs = scalar.pair_contract(effects,catalog,supplied)
    scale = scalar.scaling(x,pairs,catalog)
    return rows,catalog,effects,x,supplied,pairs,scale


class ComparisonCoreTests(unittest.TestCase):
    def test_entire_120_task_plan_is_metadata_only(self):
        rows = fixture(); plan = layout.comparison_plan(rows)
        self.assertEqual(len(plan['tasks']),120)
        self.assertEqual(sum(t['phase']=='inner' for t in plan['tasks']),108)
        self.assertEqual(sum(t['phase']=='outer' for t in plan['tasks']),12)
        self.assertEqual(plan['actual_fit_calls'],0)
        for held,pool in plan['pools'].items():
            self.assertEqual({rows[i]['dataset'] for i in pool['outer']['target']},{held})
            self.assertEqual(len(pool['outer']['train']),27)
            for inner,split in pool['inner'].items():
                self.assertEqual(len(split['train']),18)
                self.assertNotIn(held,{rows[i]['dataset'] for i in split['train']+split['target']})
                self.assertNotIn(inner,{rows[i]['dataset'] for i in split['train']})

    def test_global_component_purge_retains_complete_menus(self):
        rows = fixture()
        for row in rows[9:12]:row['biological_component']=rows[0]['biological_component']
        plan = layout.comparison_plan(rows)
        split = plan['pools'][layout.STUDIES[0]]['outer']
        self.assertEqual(len(split['train']),24)
        self.assertFalse(set(range(9,12)) & set(split['train']))

    def test_exact_allele_mismatch_rejects_instead_of_trimming(self):
        rows = fixture()
        for row in rows[9:12]:
            row['parent_sequence']=rows[0]['parent_sequence']
            row['mutant_sequence']=rows[0]['mutant_sequence']
        with self.assertRaisesRegex(ValueError,'exact allele overlap'):layout.comparison_plan(rows)

    def test_no_outcome_or_incomplete_roster_in_metadata(self):
        rows = fixture();rows[0]['measured_delta']=1.
        with self.assertRaises(ValueError):layout.comparison_plan(rows)
        with self.assertRaises(ValueError):layout.comparison_plan(fixture()[:27])
        with self.assertRaises(ValueError):layout.comparison_plan(fixture()+[fixture()[0]])

    def test_equal_hierarchy_weights_with_unequal_context_counts(self):
        rows=fixture()
        # Two contexts share a component, so each gets half its component mass.
        for row in rows[3:6]:row['biological_component']=rows[0]['biological_component']
        rows=layout.metadata(rows);catalog=layout.menus(rows,range(len(rows)))
        self.assertAlmostEqual(math.fsum(m['weight'] for m in catalog),1.)
        for study in layout.STUDIES:
            self.assertAlmostEqual(math.fsum(m['weight'] for m in catalog if m['dataset']==study),.25)
        self.assertAlmostEqual(catalog[0]['weight'],.0625)
        self.assertAlmostEqual(catalog[1]['weight'],.0625)
        self.assertAlmostEqual(catalog[2]['weight'],.125)

    def test_partial_context_and_extra_feature_rows_rejected(self):
        rows,catalog,y,x,supplied,pairs,scale=problem()
        with self.assertRaisesRegex(ValueError,'partial candidate menu'):layout.menus(rows,range(1,len(rows)))
        with self.assertRaisesRegex(ValueError,'partition every supplied source row'):
            scalar.scaling(x+((0.,0.,0.,0.),),pairs,catalog)
        with self.assertRaisesRegex(ValueError,'partition every supplied source row'):
            scalar.pair_contract(y+(0.,),catalog,supplied)

    def test_sample_roster_and_truth_tie_rules(self):
        _,catalog,y,_,supplied,pairs,_=problem()
        tied=list(y);tied[0]=tied[1]
        result=scalar.pair_contract(tied,catalog,supplied)
        self.assertEqual(len(result),len(pairs)-1)
        self.assertAlmostEqual(math.fsum(row[3] for row in result),1.)
        bad=dict(supplied);bad[catalog[0]['context']]=((0,1),(0,1),(0,2))
        with self.assertRaises(ValueError):scalar.pair_contract(y,catalog,bad)
        tied[2]=tied[1]
        with self.assertRaisesRegex(ValueError,'uninformative menu'):scalar.pair_contract(tied,catalog,supplied)

    def test_scaling_and_unsupported_coordinates(self):
        _,catalog,y,x,_,pairs,scale=problem()
        self.assertEqual(scale['active'],(True,True,False,False))
        self.assertEqual(scale['scale'][2:],(1.,1.))
        for j in range(4):
            want=math.sqrt(math.fsum(w*(x[a][j]-x[b][j])**2 for a,b,_,w in pairs))
            self.assertAlmostEqual(scale['pair_rms'][j],want,delta=1e-14)
        with self.assertRaisesRegex(ValueError,'unsupported coefficient'):
            scalar.objective((0.,0.,1.,0.),x,y,catalog,pairs,scale,arm='menu_cost',penalty=.05)

    def test_full_vector_gradients_for_both_losses(self):
        _,catalog,y,x,_,pairs,scale=problem()
        beta=(.2,-.4,0.,0.)
        for arm in layout.ARMS:
            value,gradient=scalar.objective(beta,x,y,catalog,pairs,scale,arm=arm,penalty=.05)
            self.assertTrue(math.isfinite(value));self.assertEqual(gradient[2:],(0.,0.))
            for j in (0,1):
                plus,minus=list(beta),list(beta);plus[j]+=1e-6;minus[j]-=1e-6
                a=scalar.objective(plus,x,y,catalog,pairs,scale,arm=arm,penalty=.05)[0]
                b=scalar.objective(minus,x,y,catalog,pairs,scale,arm=arm,penalty=.05)[0]
                self.assertAlmostEqual((a-b)/2e-6,gradient[j],delta=2e-9)

    def test_pairwise_scalar_loss_matches_direct_logistic_expression(self):
        _,catalog,y,x,_,pairs,scale=problem();beta=(.2,-.4,0.,0.)
        value,_=scalar.objective(beta,x,y,catalog,pairs,scale,arm='pairwise',penalty=.05)
        direct=math.fsum(w*math.log1p(math.exp(-sign*math.fsum(
            beta[j]*(x[a][j]-x[b][j])/scale['scale'][j] for j in (0,1))))
            for a,b,sign,w in pairs)+.025*math.fsum(v*v for v in beta)
        self.assertAlmostEqual(value,direct,delta=1e-14)

    def test_source_only_centering_cancels_and_losses_are_convex(self):
        _,catalog,y,x,_,pairs,scale=problem();a=(.2,-.4,0.,0.);b=(-.8,.1,0.,0.)
        changed={**scale,'mean':tuple(v+16 for v in scale['mean'])}
        for arm in layout.ARMS:
            first=scalar.objective(a,x,y,catalog,pairs,scale,arm=arm,penalty=.05)
            shifted=scalar.objective(a,x,y,catalog,pairs,changed,arm=arm,penalty=.05)
            self.assertAlmostEqual(first[0],shifted[0],delta=1e-12)
            for g,h in zip(first[1],shifted[1]):self.assertAlmostEqual(g,h,delta=1e-12)
            mid=tuple((v+w)/2 for v,w in zip(a,b))
            second=scalar.objective(b,x,y,catalog,pairs,scale,arm=arm,penalty=.05)[0]
            self.assertLessEqual(scalar.objective(mid,x,y,catalog,pairs,scale,arm=arm,penalty=.05)[0],
                                 (first[0]+second)/2+1e-12)

    def test_wrong_pair_labels_and_missing_weights_rejected(self):
        _,catalog,y,x,_,pairs,scale=problem()
        bad=list(pairs);a,b,sign,w=bad[0];bad[0]=(a,b,-sign,w)
        with self.assertRaises(ValueError):scalar.objective((0.,)*4,x,y,catalog,bad,scale,arm='pairwise',penalty=.05)
        with self.assertRaises(ValueError):scalar.objective((0.,)*4,x,y,catalog,pairs,scale,arm='menu_cost',penalty=0.)

    def test_binary_menu_cost_exactly_matches_margin_pair_control(self):
        rows=layout.metadata([row for i,row in enumerate(fixture()) if i%3 != 2])
        catalog=layout.menus(rows,range(len(rows)))
        y=tuple((-1.)**i for i in range(len(rows)))
        x=tuple((float(i%2),float(i%5)) for i in range(len(rows)))
        supplied={m['context']:tuple(itertools.combinations(m['indices'],2)) for m in catalog}
        pairs=scalar.pair_contract(y,catalog,supplied);scale=scalar.scaling(x,pairs,catalog)
        for beta in ((0.,0.),(.2,-.3),(-3.,1.)):
            a=scalar.objective(beta,x,y,catalog,pairs,scale,arm='margin_pair',penalty=.05)
            b=scalar.objective(beta,x,y,catalog,pairs,scale,arm='menu_cost',penalty=.05)
            self.assertAlmostEqual(a[0],b[0],delta=1e-13)
            for first,second in zip(a[1],b[1]):self.assertAlmostEqual(first,second,delta=1e-13)

    def test_margin_control_and_menu_loss_differ_for_larger_menus(self):
        _,catalog,y,x,_,pairs,scale=problem();beta=(.2,-.4,0.,0.)
        a=scalar.objective(beta,x,y,catalog,pairs,scale,arm='margin_pair',penalty=.05)[0]
        b=scalar.objective(beta,x,y,catalog,pairs,scale,arm='menu_cost',penalty=.05)[0]
        self.assertNotAlmostEqual(a,b,places=8)


if __name__=='__main__':unittest.main()
