"""Stdlib invented/mock preflight only; native kernels remain unexecuted."""
import ast
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from . import common as c, kernels as k, spec as s, guard

class Tests(unittest.TestCase):
    def test_fixed_sizes_dimensions_and_threads(self):
        self.assertEqual((s.SIZES,s.WIDTHS,s.CAP,s.BLOCK),([24,256,1024,2048],[246,251],256,128))
        self.assertEqual((s.REPEATS,s.THREADS,s.SMALL_OPTIMIZER_SHAPE),(3,'1',[64,6]))
    def test_block_upper_triangle_exact_coverage(self):
        for n in (2,23,24,129,257):
            edges=[(a,b) for start,stop in k.blocks(n) for a in range(start,stop) for b in range(n) if b>a]
            self.assertEqual(len(edges),n*(n-1)//2);self.assertEqual(len(set(edges)),len(edges))
            self.assertLessEqual(max(stop-start for start,stop in k.blocks(n)),s.BLOCK)
    def test_sampler_small_complete_large_mock_unique(self):
        self.assertEqual(len(k.cap_edges(23,'a')),253)
        pairs=k.cap_edges(24,'a');self.assertEqual(len(pairs),256);self.assertEqual(pairs,k.cap_edges(24,'a'))
        self.assertTrue(all(0<=a<b<24 for a,b in pairs))
    def test_native_rng_contract_seed_and_choice_without_import(self):
        seen=[]
        class Array(list):
            def tolist(self):return list(self)
        class RNG:
            def __init__(self):self.i=0
            def choice(self,n,size,replace):
                self.assertions=(n,size,replace);a,b=list(__import__('itertools').combinations(range(n),2))[self.i];self.i+=1;return Array([a,b])
        class Random:
            def default_rng(self,seed):seen.append(seed);return RNG()
        class Fake:random=Random()
        pairs=k.cap_edges(24,'native',np=Fake())
        self.assertEqual(seen,[int(hashlib.sha256((str(s.CAP_SEED)+'native').encode()).hexdigest()[:8],16)])
        self.assertEqual(len(pairs),256)
    def test_tied_cap_context_never_revived(self):
        prepared=k.prepare_contexts([0.,-0.,1.,2.],[{'name':'drop','indices':[0,1],'mass':.8},{'name':'retain','indices':[2,3],'mass':.2}])
        self.assertEqual([row['name'] for row in prepared],['retain']);self.assertEqual(prepared[0]['mass'],1.)
    def test_unequal_mass_stays_context_not_pair_count(self):
        rows=k.prepare_contexts([0.,1.,2.,0.,1.],[{'name':'a','indices':[0,1,2],'mass':.25},{'name':'b','indices':[3,4],'mass':.75}])
        self.assertEqual([row['mass'] for row in rows],[.25,.75]);self.assertEqual([row['all_count'] for row in rows],[3,1])
    def test_exact_ties_count_and_all_equal(self):
        self.assertEqual(k.non_tied_count([0.,-0.,1.,1.]),4);self.assertEqual(k.non_tied_count([4.,4.,4.]),0)
    def test_original_context_partition_rejects_overlap(self):
        with self.assertRaises(AssertionError):k.prepare_contexts([0.,1.,2.],[{'name':'a','indices':[0,1],'mass':.5},{'name':'b','indices':[1,2],'mass':.5}])
    def test_invented_replay_and_constant_support_column(self):
        x,y,b=k.invented(24,6,1);self.assertEqual((x,y,b),k.invented(24,6,1))
        self.assertEqual(len(x),24);self.assertEqual(len(x[0]),6);self.assertEqual({r[-1] for r in x},{7.});self.assertEqual(b[-1],0.)
    def test_resources_floor_before_import(self):
        value={'available_RAM_bytes':s.MIN_RAM,'workspace_disk_free_bytes':s.MIN_DISK};self.assertEqual(guard.resource_contract(value),value)
        for key in value:
            bad=dict(value);bad[key]-=1
            with self.assertRaises(AssertionError):guard.resource_contract(bad)
    def test_time_cap_inclusive_finite_and_final_check(self):
        self.assertEqual(guard.time_contract(120.),120.)
        for elapsed in (120.00001,-1.,float('nan'),float('inf')):
            with self.assertRaises(AssertionError):guard.time_contract(elapsed)
        tree=ast.parse((c.SRC/'probe.py').read_text(encoding='utf-8'))
        funcs={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
        self.assertTrue(any(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='time_contract' for node in ast.walk(funcs['completed_call'])))
        self.assertGreaterEqual(sum(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='time_contract' for node in ast.walk(funcs['run'])),2)
    def test_explicit_native_start_is_mandatory(self):
        with self.assertRaises(AssertionError):guard.admit(False)
    def test_manifest_cannot_grant_biological_authority(self):
        v={'status':'FROZEN_INVENTED_ALLPAIRS_NATIVE_PREPARATION','project_data_or_fitting_authorized':False,'native_executed':False,'files':{}}
        c.manifest_checks(v)
        v['project_data_or_fitting_authorized']=True
        with self.assertRaises(AssertionError):c.manifest_checks(v)
    def test_immutable_write_preserves_existing_bytes(self):
        original=(c.SRC,c.ART,c.OUT,c.REP)
        try:
            with tempfile.TemporaryDirectory() as directory:
                c.SRC=c.ART=c.OUT=c.REP=Path(directory)
                path=Path(directory)/'invented.json';c.save(path,b'original')
                with self.assertRaises(FileExistsError):c.save(path,b'changed')
                self.assertEqual(path.read_bytes(),b'original')
        finally:c.SRC,c.ART,c.OUT,c.REP=original
    def test_no_top_level_numeric_or_biological_readers(self):
        for path in c.SRC.glob('*.py'):
            tree=ast.parse(path.read_text(encoding='utf-8'))
            for node in tree.body:
                if isinstance(node,ast.Import):self.assertFalse(any(a.name.split('.')[0] in {'numpy','pandas','scipy','torch','openvino'} for a in node.names))
                if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').startswith(('src.generalization_crosscell','src.cross_assay')))
        c.clean_imports()

def run():
    c.clean_imports();assert not c.TESTS.exists()
    output=io.StringIO();result=unittest.TextTestRunner(stream=output,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    print(output.getvalue());assert result.wasSuccessful();c.clean_imports()
    files={p.relative_to(c.ROOT).as_posix():c.sha(p) for p in c.SRC.glob('*.py')}
    files[(c.REP/'plan.md').relative_to(c.ROOT).as_posix()]=c.sha(c.REP/'plan.md')
    for home in (c.SRC,c.ART,c.OUT,c.REP):files[(home/'.gitattributes').relative_to(c.ROOT).as_posix()]=c.sha(home/'.gitattributes')
    c.jsave(c.TESTS,{'status':'PASS_STDLIB_PREPARATION_ONLY','tests':result.testsRun,'files':files,'test_output':output.getvalue(),
        'numerical_packages_imported':False,'native_kernels_executed':False,'project_data_read':False,'optimizer_calls':0})
    print('Native pair benchmark stdlib preparation PASS',c.sha(c.TESTS),flush=True)

if __name__=='__main__':run()
