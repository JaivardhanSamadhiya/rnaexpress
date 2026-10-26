"""Source and invented boundary tests; no biological inputs or native imports."""
import ast
from pathlib import Path
import unittest
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from . import replay,evaluation
from src.generalization_knowncell_joint_evaluation_20261023 import evaluation as original


class Normalize(ast.NodeTransformer):
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='fresh':node.args=[];node.keywords=[]
        return node


class Cases(unittest.TestCase):
    def test_evaluation_mathematics_exact_original_AST(self):
        def body(module):
            node=next(n for n in ast.parse(Path(module.__file__).read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='evaluate')
            return ast.dump(Normalize().visit(ast.Module(body=node.body,type_ignores=[])),include_attributes=False)
        self.assertEqual(body(evaluation),body(original))
    def test_expired_owner_precedes_replay_or_evaluation_data(self):
        def stopped():raise RuntimeError('invented owner expired')
        with self.assertRaises(RuntimeError):replay.replay(None,None,None,b'',[],b'',fresh=stopped,before_checkpoint=lambda *a:True)
        with self.assertRaises(RuntimeError):evaluation.evaluate(None,None,None,None,fresh=stopped)
    def test_no_optimizers_or_file_readers_in_new_libraries(self):
        for module in (replay,evaluation):
            tree=ast.parse(Path(module.__file__).read_bytes())
            calls={n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id for n in ast.walk(tree)
                if isinstance(n,ast.Call) and isinstance(n.func,(ast.Attribute,ast.Name))}
            self.assertFalse(calls & {'open','read_bytes','load','minimize','fit_prepared','fit','run_fixed_campaign'})
    def test_existing_outer_roster_helper_is_retained(self):
        self.assertIs(evaluation.collect_outer,original.collect_outer)
        self.assertIs(evaluation.secondary_summary,original.secondary_summary)
        self.assertIs(evaluation.gate,original.gate)
    def test_complete_new_campaign_replays_all63_and_rejects_missing_closure(self):
        from src.generalization_current_fixed_fit_core_20261026 import tests as fixtures
        harness=fixtures.Cases();harness.setUp()
        try:
            old,prepared=fixtures.fixture();plan=fixtures.current(old)
            prepared=fixtures.p.rebind_prepared(plan,prepared)
            with tempfile.TemporaryDirectory() as folder:
                directory=Path(folder)/'invented'
                fixtures.d.run_fixed_campaign(fixtures.FakeNP,fixtures.OptimizerSpy(),fixtures.expit,prepared,plan,
                    fresh=lambda:None,before_checkpoint_integrity=lambda **kw:True,directory=directory)
                checkpoints=directory/'checkpoints';records=[]
                for task in fixtures.lc.task_roster():
                    key=fixtures.lc.task_key(task)
                    records.append({'task_key':key,'birth_raw':(checkpoints/(key+'.birth.json')).read_bytes(),
                        'checkpoint_raw':(checkpoints/(key+'.model.json')).read_bytes(),
                        'completion_raw':(checkpoints/(key+'.complete.json')).read_bytes()})
                birth=(checkpoints/'campaign_birth.json').read_bytes();complete=(checkpoints/'campaign_complete.json').read_bytes()
                seen=[]
                def hook(key,task):seen.append(key);return True
                with patch.object(replay.metadata,'COUNTS',fixtures.lc.COUNTS):
                    result=replay.replay(fixtures.FakeNP,prepared,plan,birth,records,complete,fresh=lambda:None,before_checkpoint=hook)
                self.assertEqual(len(seen),63);self.assertEqual(result['recorded_optimizer_units_not_refitted'],84)
                self.assertEqual(len(result['canonical_outer_records']),9)
                with patch.object(replay.metadata,'COUNTS',fixtures.lc.COUNTS),self.assertRaises((AssertionError,ValueError)):
                    replay.replay(fixtures.FakeNP,prepared,plan,birth,records,b'{}',fresh=lambda:None,before_checkpoint=hook)
        finally:harness.doCleanups()


if __name__=='__main__':unittest.main(verbosity=2)
