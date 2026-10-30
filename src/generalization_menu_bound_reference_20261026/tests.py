"""Invented source problems demonstrating the integration fix's boundaries."""
from copy import deepcopy
import unittest
from .reference import evaluate
from src.generalization_menu_comparison_core_20261026 import layout, scalar
from src.generalization_menu_comparison_core_20261026.tests import problem


def inputs():
    rows,catalog,y,x,sampled,pairs,scale=problem()
    return dict(beta=(.2,-.4,0.,0.),features=x,effects=y,source_metadata=rows,
                sampled_pairs=sampled,arm='pairwise',penalty=.05),catalog,pairs,scale


class SourceBoundTests(unittest.TestCase):
    def test_equals_legitimate_full_roster_arithmetic_all_arms(self):
        kwargs,catalog,pairs,scale=inputs()
        for arm in layout.ARMS:
            kwargs['arm']=arm
            result=evaluate(**kwargs,recorded_scaling=scale)
            want=scalar.objective(kwargs['beta'],kwargs['features'],kwargs['effects'],
                                  catalog,pairs,scale,arm=arm,penalty=.05)
            self.assertEqual((result['objective'],result['gradient']),want)
            self.assertEqual(result['source_contexts'],12)
            self.assertFalse(result['input_admission_certified'])
            self.assertFalse(result['recorded_scaling_used_for_computation'])

    def test_frozen_lower_level_witness_cannot_enter_new_api(self):
        kwargs,catalog,pairs,_=inputs()
        first=tuple((a,b,y,w/catalog[0]['weight']) for a,b,y,w in pairs
                    if a in catalog[0]['indices'])
        # The original public low-level functions accept this normalized but
        # incomplete roster. They are preserved, not relabeled as bound inputs.
        wrong_scale=scalar.scaling(kwargs['features'],first,catalog)
        scalar.objective(kwargs['beta'],kwargs['features'],kwargs['effects'],catalog,
                         first,wrong_scale,arm='pairwise',penalty=.05)
        with self.assertRaises(TypeError):evaluate(**kwargs,pair_rows=first)
        with self.assertRaises(TypeError):evaluate(**kwargs,menu_catalog=catalog)

    def test_omitted_context_in_supplied_sampler_rejects(self):
        kwargs,_,_,_=inputs();kwargs['sampled_pairs']=dict(kwargs['sampled_pairs'])
        kwargs['sampled_pairs'].pop(next(iter(kwargs['sampled_pairs'])))
        with self.assertRaisesRegex(ValueError,'pair/context roster'):evaluate(**kwargs)

    def test_forged_recorded_scale_and_support_reject(self):
        kwargs,_,_,scale=inputs()
        bad=deepcopy(scale);bad['scale']=list(bad['scale']);bad['scale'][0]*=2
        with self.assertRaisesRegex(ValueError,'scaling differs'):evaluate(**kwargs,recorded_scaling=bad)
        bad=deepcopy(scale);bad['active']=(False,True,False,False)
        with self.assertRaisesRegex(ValueError,'support differs'):evaluate(**kwargs,recorded_scaling=bad)

    def test_extra_held_rows_and_outcome_metadata_reject(self):
        kwargs,_,_,_=inputs();kwargs['features']=kwargs['features']+((0.,0.,0.,0.),)
        with self.assertRaisesRegex(ValueError,'row counts differ'):evaluate(**kwargs)
        kwargs,_,_,_=inputs();kwargs['source_metadata']=deepcopy(kwargs['source_metadata'])
        kwargs['source_metadata'][0]['measured_delta']=1.
        with self.assertRaisesRegex(ValueError,'outcome-free fields'):evaluate(**kwargs)

    def test_recorded_scale_tolerance_does_not_change_computed_arithmetic(self):
        kwargs,_,_,scale=inputs();bad=deepcopy(scale)
        bad['mean']=tuple(v+1e-11 for v in bad['mean'])
        first=evaluate(**kwargs);second=evaluate(**kwargs,recorded_scaling=bad)
        self.assertEqual(first['objective'],second['objective'])
        self.assertEqual(first['gradient'],second['gradient'])


if __name__=='__main__':unittest.main()
