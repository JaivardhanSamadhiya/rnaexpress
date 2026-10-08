
"""Invented conservation-block corruption and control tests."""
import copy,math,unittest
from . import spec as s
from .matrix_contracts import addon,validate_blocks
from .contracts import information_checks,comparison_checks

def fake():
    rows=[{'intervention_id':'a','dataset':'fake','cell_type':'CAD'},{'intervention_id':'b','dataset':'fake','cell_type':'Neuro-2a'}]
    blocks=[{'intervention_id':r['intervention_id'],'parent_id':'same','annotation_complete_parent':True,
        'raw_position8':[1.,-1.,0.,0.,2.,0.,-2.,0.],'reference_conservation8':[-3.,3.,0.,0.,0.,1.,0.,-1.]} for r in rows]
    return rows,blocks

class Tests(unittest.TestCase):
    def test_negative_native_scores_and_real_zero_allowed(self):
        rows,blocks=fake();self.assertTrue(all(validate_blocks(rows,blocks).values()))
        blocks[0]['reference_conservation8']=[0.]*8;validate_blocks(rows,blocks)
    def test_reordered_same_ids_rejected(self):
        rows,blocks=fake()
        with self.assertRaises(AssertionError):validate_blocks(rows,list(reversed(blocks)))
    def test_duplicate_and_missing_ids_rejected(self):
        rows,blocks=fake();blocks[1]['intervention_id']='a'
        with self.assertRaises(AssertionError):validate_blocks(rows,blocks)
        with self.assertRaises(AssertionError):validate_blocks(rows,blocks[:1])
    def test_missing_parent_policy_must_match_both_cells(self):
        rows,blocks=fake();blocks[1]['annotation_complete_parent']=False
        blocks[1]['raw_position8']=blocks[1]['reference_conservation8']=[0.]*8
        with self.assertRaises(AssertionError):validate_blocks(rows,blocks)
    def test_unavailable_both_blocks_zero_without_filter(self):
        rows,blocks=fake()
        for block in blocks:
            block['annotation_complete_parent']=False
            block['raw_position8']=block['reference_conservation8']=[0.]*8
        self.assertFalse(any(validate_blocks(rows,blocks).values()))
        blocks[1]['raw_position8']=[1.,-1.,0.,0.,0.,0.,0.,0.]
        with self.assertRaises(AssertionError):validate_blocks(rows,blocks)
    def test_nonfinite_or_boolean_features_rejected(self):
        for value in (math.nan,math.inf,True,'0'):
            rows,blocks=fake();blocks[0]['reference_conservation8'][0]=value
            with self.assertRaises(AssertionError):validate_blocks(rows,blocks)
    def test_wrong_width_and_base_group_sum_rejected(self):
        rows,blocks=fake();blocks[0]['raw_position8']=blocks[0]['raw_position8'][:7]
        with self.assertRaises(AssertionError):validate_blocks(rows,blocks)
        rows,blocks=fake();blocks[0]['raw_position8'][0]=2.
        with self.assertRaises(AssertionError):validate_blocks(rows,blocks)
    def test_controls_fix_native_raw_column_order_and_duplicate_span(self):
        raw=[1.,-1.,0.,0.,2.,-2.,0.,0.];native=[-3.,3.,0.,0.,4.,-4.,0.,0.]
        self.assertEqual(addon('native',raw,native),native)
        self.assertEqual(addon('combined',raw,native),raw+native)
        duplicate=addon('duplicate_raw',raw,native)
        self.assertEqual(duplicate[:8],duplicate[8:])
        beta=[.1*i for i in range(16)]
        full=sum(x*y for x,y in zip(duplicate,beta))
        collapsed=sum(x*(a+b) for x,a,b in zip(raw,beta[:8],beta[8:]))
        self.assertAlmostEqual(full,collapsed)
    def test_only_native_combined_eligible_and_all_controls_required(self):
        self.assertEqual(s.INFORMED,['native','combined'])
        self.assertEqual(s.INFORMATION_CONTROLS['native'],['raw'])
        self.assertEqual(s.INFORMATION_CONTROLS['combined'],['raw','duplicate_raw','native'])
        self.assertEqual(s.WIDTHS,dict(simple=102,base=246,raw=254,native=254,duplicate_raw=262,combined=262))
        self.assertEqual(s.NEW_CHECKPOINTS,168)
    def test_information_gate_boundary_remains_strict_leave_best(self):
        self.assertTrue(all(information_checks({'mean_gain':.01,'remaining_gene_gain':1e-12,'remaining_gain':1e-12}).values()))
        self.assertFalse(all(information_checks({'mean_gain':.009999,'remaining_gene_gain':.01,'remaining_gain':.01}).values()))
        self.assertFalse(all(information_checks({'mean_gain':.01,'remaining_gene_gain':.01,'remaining_gain':0.}).values()))

    def comparison(self):
        return {'mean_gain':.01,'per_cell_gain':{'a':.005,'b':.015},'gain_ci':[.001,.1],
          'remaining_gain':.001,'remaining_gene_gain':.001,'wrong_direction_harm':{'a':0.,'b':0.},
          'macro_wrong_direction_harm':0.,'avoidable_wrong_harm':{'a':0.,'b':0.},'macro_avoidable_wrong_harm':0.}
    def test_avoidable_harm_cannot_hide_behind_total_wrong_gain(self):
        value=self.comparison();self.assertTrue(all(comparison_checks(value).values()))
        value['macro_avoidable_wrong_harm']=.020001
        self.assertFalse(all(comparison_checks(value).values()))
        value=self.comparison();value['avoidable_wrong_harm']['a']=.050001
        self.assertFalse(all(comparison_checks(value).values()))
    def test_individual_gene_and_fold_removal_both_required(self):
        value=self.comparison();value['remaining_gene_gain']=0.
        self.assertFalse(all(comparison_checks(value).values()))
        self.assertFalse(all(information_checks(value).values()))
        value=self.comparison();value['remaining_gain']=0.
        self.assertFalse(all(comparison_checks(value).values()))
    def test_zero_lower_interval_and_each_cell_boundary_not_relaxed(self):
        value=self.comparison();value['gain_ci'][0]=0.
        self.assertFalse(all(comparison_checks(value).values()))
        value=self.comparison();value['per_cell_gain']['a']=.0049999
        self.assertFalse(all(comparison_checks(value).values()))

if __name__=='__main__':unittest.main(verbosity=2)
