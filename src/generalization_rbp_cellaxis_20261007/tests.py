"""Invented metadata/mock contracts only; zero project/model/numeric reads."""
import ast
import copy
import sys
import unittest
from pathlib import Path
from . import spec as s, contracts as c, common as common


def invented():
    rows = []
    for cell in ('CAD', 'Neuro-2a'):
        for fold, parent, mutants in ((0, 'AAAA', ('AAAC', 'AAAG')),
                                      (1, 'CCCC', ('CCCA', 'CCCT')),
                                      (2, 'GGGG', ('GGGA', 'GGGT'))):
            for index, mutant in enumerate(mutants):
                rows.append({'intervention_id': cell + str(fold) + str(index),
                    'cell_type': cell, 'held_parent_fold': fold, 'parent_sequence': parent,
                    'mutant_sequence': mutant, 'biological_component': 'component' + str(fold),
                    'gene_transcript': 'gene' + str(fold),
                    'parent_context_id': cell + str(fold)})
    return rows


class Tests(unittest.TestCase):
    def test_exact_tracks_widths_and_fit_counts(self):
        self.assertEqual(s.WIDTHS, {'simple':102,'base':246,'raw':502,'access':758,'duplicate_marginal':1014,'joint':1014})
        self.assertEqual(s.NEW_CHECKPOINTS, len(s.NEW_FIT_TRACKS)*6*7)
        self.assertEqual(s.NEW_INNER_CHECKPOINTS, len(s.NEW_FIT_TRACKS)*6*6)
        self.assertEqual(s.NEW_OUTER_CHECKPOINTS, len(s.NEW_FIT_TRACKS)*6)
        self.assertEqual(s.REUSED_CHECKPOINTS, len(s.REUSED_CONTROLS)*42)

    def test_no_endpoint_polarity_or_config_grid_change(self):
        self.assertEqual(s.CONFIGS, [{'id':'pair_005','penalty':.005,'scaling':'pair'},
                                    {'id':'pair_05','penalty':.05,'scaling':'pair'},
                                    {'id':'pair_5','penalty':.5,'scaling':'pair'}])
        self.assertEqual(s.NUMERICAL_THREADS, 1)

    def test_fixed_information_controls_and_eligibility(self):
        self.assertEqual(s.INFORMED, ['raw','access','joint'])
        self.assertEqual(s.INFORMATION_CONTROLS['joint'], ['access','duplicate_marginal'])
        self.assertEqual(s.INFORMATION_CONTROLS['access'], ['raw'])
        self.assertNotIn('duplicate_marginal',s.INFORMED)

    def test_outer_no_target_cell_or_gene_fold(self):
        rows=invented()
        for task,(source,target) in s.TASKS.items():
            for fold in s.FOLDS:
                train,test=c.outer(rows,task,fold)
                self.assertEqual(sum(train),4);self.assertEqual(sum(test),2)
                self.assertEqual({r['cell_type'] for r,k in zip(rows,train) if k},{source})
                self.assertEqual({r['cell_type'] for r,k in zip(rows,test) if k},{target})
                self.assertNotIn(fold,{r['held_parent_fold'] for r,k in zip(rows,train) if k})

    def test_source_only_inner_fold_validation_complete(self):
        rows=invented();train,_=c.outer(rows,'CAD_to_N2A',0)
        source=[r for r,k in zip(rows,train) if k];covered=[]
        for fold in (1,2):
            a,b=c.inner(source,fold);self.assertEqual(sum(a),2);self.assertEqual(sum(b),2)
            covered+=c.ids(source,b)
        self.assertEqual(sorted(covered),sorted(r['intervention_id'] for r in source))

    def test_known_uses_identical_original_source_mask(self):
        rows=invented()
        for task,(_,source_task) in s.KNOWN_TASKS.items():
            for fold in s.FOLDS:
                train,known,opposite=c.known(rows,task,fold)
                self.assertEqual((train,opposite),c.outer(rows,source_task,fold))
                self.assertEqual(sum(known),2)

    def test_allele_contradiction_stops_without_extra_purge(self):
        rows=invented();rows[2]['mutant_sequence']=rows[6]['parent_sequence']
        with self.assertRaises(AssertionError):c.outer(rows,'CAD_to_N2A',0)

    def test_gene_contradiction_stops_without_extra_purge(self):
        rows=invented();rows[2]['gene_transcript']=' GENE0 '
        with self.assertRaises(AssertionError):c.outer(rows,'CAD_to_N2A',0)

    def test_same_cell_allele_contradiction_stops_no_refit(self):
        rows=invented()
        # Only CAD held0 gets this allele; opposite-cell outer mask is safe,
        # but the represented-cell target must independently reject overlap.
        rows[0]['mutant_sequence']=rows[2]['mutant_sequence']
        c.outer(rows,'CAD_to_N2A',0)
        with self.assertRaises(AssertionError):c.known(rows,'CAD_known',0)

    def test_source_choice_fixed_exact_tolerance_order(self):
        self.assertEqual(c.source_choice([.3+5e-13,.3,.4]),s.CONFIGS[0])
        self.assertEqual(c.source_choice([.3+5e-11,.3,.4]),s.CONFIGS[1])
        with self.assertRaises(AssertionError):c.source_choice([float('nan'),.3,.4])

    def test_exact_feature_bytes_no_close_fallback(self):
        c.byte_equality(b'abc',b'abc','mock')
        with self.assertRaises(AssertionError):c.byte_equality(b'abc',b'abd','mock')

    def test_original_gate_boundaries(self):
        value={'mean_gain':.01,'per_cell_gain':{'a':.005,'b':.015},'gain_ci':[1e-9,.02],
               'macro_wrong_direction_harm':.02,'wrong_direction_harm':{'a':.05,'b':-.01},'remaining_gain':1e-9}
        self.assertTrue(all(c.comparison_checks(value).values()))
        for name in ('gain_ci','remaining_gain'):
            bad=copy.deepcopy(value);bad[name]=[0,.02] if name=='gain_ci' else 0
            self.assertFalse(all(c.comparison_checks(bad).values()))
        self.assertFalse(all(c.information_checks({'mean_gain':.009999,'remaining_gain':.1}).values()))

    def test_root_start_required_before_any_source_read(self):
        with self.assertRaises(AssertionError):common.preparation_check(False)

    def test_source_ast_and_no_top_level_numeric_imports(self):
        for path in Path(__file__).parent.glob('*.py'):
            tree=ast.parse(path.read_text())
            for node in tree.body:
                if isinstance(node,ast.Import):
                    self.assertFalse(any(alias.name.split('.')[0] in {'numpy','pandas','RNA','torch','openvino'} for alias in node.names))
                if isinstance(node,ast.ImportFrom):
                    self.assertFalse((node.module or '').startswith(('src.generalization_crosscell','src.generalization_rbp','src.generalization_joint')))
        self.assertFalse(any(name in sys.modules for name in ('numpy','pandas','RNA','torch','openvino')))


if __name__=='__main__':unittest.main(verbosity=2)
