"""Stdlib duck arrays, invented contracts and mocked guards; zero project reads."""
import ast
import math
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from . import common as c,numeric as n,prepare_inputs,checkpoints,controls,freeze,runtime_guard
from src.generalization_rbp_cellaxis_20261007 import spec as s


class Arr:
    def __init__(self,value):
        self.data=value.data if isinstance(value,Arr) else list(value)
        self.dim=2 if self.data and isinstance(self.data[0],list) else 1
        self.shape=(len(self.data),len(self.data[0])) if self.dim==2 else (len(self.data),)
    def __len__(self):return len(self.data)
    def __getitem__(self,key):
        if isinstance(key,Arr):return Arr([v for v,k in zip(self.data,key.data) if k])
        value=self.data[key];return Arr(value) if isinstance(key,slice) else value
    def __setitem__(self,key,value):self.data[key]=value.data if isinstance(value,Arr) else value
    def flat(self):return [v for row in self.data for v in row] if self.dim==2 else self.data
    def op(self,other,fn):
        other=other.data if isinstance(other,Arr) else other
        if self.dim==2:return Arr([[fn(v,other[j] if isinstance(other,list) else other) for j,v in enumerate(row)] for row in self.data])
        return Arr([fn(v,other[i] if isinstance(other,list) else other) for i,v in enumerate(self.data)])
    def __sub__(self,other):return self.op(other,lambda a,b:a-b)
    def __mul__(self,other):return self.op(other,lambda a,b:a*b)
    def __rmul__(self,other):return self.__mul__(other)
    def __truediv__(self,other):return self.op(other,lambda a,b:a/b)
    def __add__(self,other):return self.op(other,lambda a,b:a+b)
    def __gt__(self,other):return self.op(other,lambda a,b:a>b)
    def __lt__(self,other):return self.op(other,lambda a,b:a<b)
    def __ne__(self,other):return self.op(other,lambda a,b:a!=b)
    def __abs__(self):return self.op(0,lambda a,b:abs(a))
    def all(self):return all(self.flat())
    def any(self):return any(self.flat())
    def max(self):return max(self.flat())
    def sum(self):return sum(self.flat())


class NP:
    @staticmethod
    def asarray(value,dtype=None):return Arr(value)
    @staticmethod
    def empty(count):return Arr([0.]*count)
    @staticmethod
    def isfinite(value):return Arr([math.isfinite(v) for v in value.flat()])
    @staticmethod
    def max(value):return max(value.flat())
    @staticmethod
    def sum(value,axis=None):return Arr([sum(row) for row in value.data]) if axis==1 else sum(value.flat())
    @staticmethod
    def sign(value):return Arr([0 if v==0 else (1 if v>0 else -1) for v in value.flat()])


def fake_predict(model,x):
    return Arr([sum((v-m)/scale*b for v,m,scale,b in zip(row,model['mean'],model['scale'],model['beta'])) for row in x.data])


class Series:
    def __init__(self,data):self.data=list(data)
    def min(self):return min(self.data)
    def max(self):return max(self.data)
    def nunique(self):return len(set(self.data))
    @property
    def is_unique(self):return len(self.data)==len(set(self.data))
    def to_numpy(self,dtype=None):return Arr(self.data)
    def __rmul__(self,value):return Series([value*x for x in self.data])


class Frame:
    def __init__(self,rows):self.rows=[dict(row) for row in rows]
    def __len__(self):return len(self.rows)
    def __getattr__(self,key):
        if key=='iloc':return Index(self.rows)
        return Series([row[key] for row in self.rows])
    def assign(self,**values):
        rows=[dict(row) for row in self.rows]
        for key,value in values.items():
            data=value.data if isinstance(value,(Arr,Series)) else [value]*len(rows)
            for row,x in zip(rows,data):row[key]=x
        return Frame(rows)
    def groupby(self,key,sort=True):
        return [(value,Frame([row for row in self.rows if row[key]==value])) for value in sorted({row[key] for row in self.rows})]
    def sort_values(self,keys,ascending,kind=None):
        return Frame(sorted(self.rows,key=lambda row:(-row['_utility'],row['intervention_id'])))
    def head(self,count):return Frame(self.rows[:count])


class Index:
    def __init__(self,rows):self.rows=rows
    def __getitem__(self,index):return SimpleNamespace(**self.rows[index])


def fake_frame(truth,ids=None):
    return Frame([{'dataset':'fake','biological_component':'component','parent_context_id':'parent',
                   'intervention_id':identifier,'measured_delta':value}
                  for identifier,value in zip(ids or ['i'+str(i) for i in range(len(truth))],truth)])


class Tests(unittest.TestCase):
    def test_canonical_formula_actual_values_one_full_shape(self):
        calls=[]
        def predictor(model,x):calls.append(x.shape);return fake_predict(model,x)
        model={'mean':[1.,2.],'scale':[2.,4.],'beta':[3.,-2.]}
        with patch.object(n,'runtime',return_value=(NP,None,None,None,predictor)):
            score,error=n.canonical(model,[[3.,6.],[5.,2.],[9.,10.]])
        self.assertEqual(score.data,[1.,6.,8.]);self.assertEqual(error,0.)
        self.assertEqual(calls,[(3,2)])

    def test_inconsistent_canonical_scorer_rejected(self):
        model={'mean':[0.],'scale':[1.],'beta':[1.]}
        with patch.object(n,'runtime',return_value=(NP,None,None,None,lambda m,x:Arr([100.]*len(x)))):
            with self.assertRaises(AssertionError):n.canonical(model,[[1.],[2.]])

    def test_permitted_rounding_does_not_redefine_canonical_tie(self):
        model={'mean':[0.],'scale':[1.],'beta':[0.]}
        with patch.object(n,'runtime',return_value=(NP,None,None,None,lambda m,x:Arr([5e-13,0.]))):
            score,error=n.canonical(model,[[0.],[0.]])
        self.assertEqual(error,5e-13);self.assertEqual(score.data,[5e-13,0.])
        # Independent formula is tied, canonical original shape is NOT tied.
        self.assertGreater(score.data[0],score.data[1])

    def test_zero_or_nonfinite_scale_rejected(self):
        for scale in (0.,float('nan')):
            with patch.object(n,'runtime',return_value=(NP,None,None,None,fake_predict)):
                with self.assertRaises(AssertionError):n.canonical({'mean':[0.],'scale':[scale],'beta':[1.]},[[1.]])

    def test_direct_pair_credit_truth_ties_and_score_ties(self):
        with patch.object(n,'runtime',return_value=(NP,None,None,None,None)):
            self.assertEqual(n.pair_credit(Arr([0.,0.,1.]),Arr([0.,0.,1.])),1.)
            self.assertEqual(n.pair_credit(Arr([0.,0.,1.]),Arr([0.,0.,0.])),.5)
            self.assertEqual(n.pair_credit(Arr([0.,0.,1.]),Arr([1.,1.,0.])),0.)

    def test_information_error_metrics_complete(self):
        self.assertEqual(n.ERRORS,['regret','wrong_direction','avoidable_wrong','no_feasible_candidate','unavoidable_wrong','neutral_only_alternative_wrong'])
        self.assertEqual(n.RANKING,['pairwise_accuracy','best_recovery','top5_best_recovery'])

    def test_independent_all_negative_neutral_positive_categories(self):
        for truth,field in (([-2.,-1.],'unavoidable_wrong'),([-1.,0.],'neutral_only_alternative_wrong'),([-1.,1.],'avoidable_wrong')):
            with patch.object(n,'runtime',return_value=(NP,SimpleNamespace(DataFrame=Frame),None,None,None)):
                out=n.decisions(fake_frame(truth),[0.,0.]).rows
            row=next(r for r in out if r['direction']==1)
            self.assertEqual(row['wrong_direction'],1.)
            self.assertEqual(row[field],1.)
            self.assertEqual(sum(row[k] for k in ('avoidable_wrong','unavoidable_wrong','neutral_only_alternative_wrong')),1.)

    def test_independent_exact_ID_tie_and_pair_recovery(self):
        with patch.object(n,'runtime',return_value=(NP,SimpleNamespace(DataFrame=Frame),None,None,None)):
            rows=n.decisions(fake_frame([-1.,1.],['b','a']),[0.,0.]).rows
        self.assertEqual({r['selected_id'] for r in rows},{'a'})
        self.assertTrue(all(r['pairwise_accuracy']==.5 for r in rows))
        self.assertEqual(next(r for r in rows if r['direction']==1)['best_recovery'],1.)

    def test_independent_top5_excludes_sixth_best(self):
        with patch.object(n,'runtime',return_value=(NP,SimpleNamespace(DataFrame=Frame),None,None,None)):
            rows=n.decisions(fake_frame([0.,1.,2.,3.,4.,5.]),[6.,5.,4.,3.,2.,1.]).rows
        row=next(r for r in rows if r['direction']==1)
        self.assertEqual(row['best_recovery'],0.);self.assertEqual(row['top5_best_recovery'],0.)

    def test_saved_candidate_count_corruption_rejected(self):
        class Table:
            def __init__(self,columns):self.columns=columns;self.index=[('parent',-1),('parent',1)];self.loc=self
            def duplicated(self,keys):return SimpleNamespace(any=lambda:False)
            def set_index(self,keys):return self
            def __getitem__(self,key):return self.columns[key] if isinstance(key,str) else self
            def __contains__(self,key):return key in self.columns
        columns={name:[0.,0.] for name in n.ERRORS+n.RANKING}
        columns.update(dataset=['fake']*2,biological_component=['gene']*2,selected_id=['a','b'],candidates=[2,2])
        altered={**columns,'candidates':[2,3]}
        testing=SimpleNamespace(assert_array_equal=lambda a,b:self.assertEqual(a,b),
            assert_allclose=lambda a,b,atol,rtol:self.assertTrue(all(abs(x-y)<=atol for x,y in zip(a,b))))
        with patch.object(n,'runtime',return_value=(SimpleNamespace(testing=testing),None,None,None,None)):
            n.equal_decisions(Table(columns),Table(columns))
            with self.assertRaises(AssertionError):n.equal_decisions(Table(columns),Table(altered))

    def test_resource_wrapper_before_original_import_or_call(self):
        with patch.object(prepare_inputs,'design_check'),patch.object(prepare_inputs,'resource_check',side_effect=AssertionError('floor')):
            with self.assertRaises(AssertionError):prepare_inputs.run('matrices',True)
        self.assertNotIn('src.generalization_rbp_cellaxis_20261007.prepare',sys.modules)

    def test_python_guard_before_common_scientific_runtime_import(self):
        c.runtime.cache_clear()
        with patch.object(c,'committed'),patch.object(c,'readj',return_value={'invented':True}),patch.object(runtime_guard,'python_contract',side_effect=AssertionError('Python guard')):
            with self.assertRaises(AssertionError):c.runtime()
        self.assertFalse(any(name in sys.modules for name in ('numpy','pandas','scipy')))

    def test_python_guard_before_initial_preparation_import(self):
        with patch.object(prepare_inputs,'design_check'),patch.object(prepare_inputs,'resource_check'),patch.object(prepare_inputs,'committed'),patch.object(prepare_inputs,'readj',return_value={'invented':True}),patch.object(runtime_guard,'python_contract',side_effect=AssertionError('Python guard')):
            with self.assertRaises(AssertionError):prepare_inputs.run('matrices',True)
        self.assertNotIn('src.generalization_rbp_cellaxis_20261007.prepare',sys.modules)

    def test_explicit_root_start_before_manifest_read(self):
        with patch.object(c,'manifest_check',side_effect=RuntimeError('must not read')):
            with self.assertRaises(AssertionError):c.design_check(False)

    def test_birth_checkpoint_missing_sidecar_stops(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'checkpoint.json';path.write_text('{}')
            with self.assertRaises(AssertionError):checkpoints.checked(path,{},s.CONFIGS[0])

    def test_birth_checkpoint_changed_digest_stops(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'checkpoint.json';path.write_text('{}');path.with_suffix('.sha256').write_text('wrong')
            with self.assertRaises(AssertionError):checkpoints.checked(path,{},s.CONFIGS[0])

    def test_manifest_alias_and_outside_rejected(self):
        with patch.object(c,'sha256',return_value='ok'):
            with self.assertRaises(AssertionError):c.hash_files({'src/a.py':'ok','src\\a.py':'ok'})
            with self.assertRaises(AssertionError):c.hash_files({'../outside':'ok'})

    def test_fixed_source_tracks_grid_controls_reused(self):
        self.assertEqual(s.NEW_FIT_TRACKS,['raw','access','duplicate_marginal','joint'])
        self.assertEqual(s.REUSED_CONTROLS,['simple','base'])
        self.assertEqual(s.INFORMED,['raw','access','joint'])
        self.assertEqual(s.INFORMATION_CONTROLS['joint'],['access','duplicate_marginal'])

    def test_fitting_only_four_new_tracks(self):
        with self.assertRaises(AssertionError):checkpoints.fit('base','invented',None,None,s.CONFIGS[0])
        with self.assertRaises(AssertionError):checkpoints.fit('simple','invented',None,None,s.CONFIGS[0])

    def test_no_retroactive_creation_claim_or_control_fit_call(self):
        tree=ast.parse(Path(controls.__file__).read_text())
        self.assertFalse(any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ('fit','fit_model','fitter') for node in ast.walk(tree)))
        self.assertIn('observed_checkpoint_bytes_not_creation_time_proof',Path(controls.__file__).read_text())

    def test_actual_native_origin_outside_runtime_rejected_mock(self):
        prefix=runtime_guard.PREFIX
        packages=[SimpleNamespace(__name__=name,__version__='invented',__file__=str(prefix/name/'__init__.py')) for name in ('numpy','pandas','scipy')]
        files={name+'/__init__.py':'mock' for name in ('numpy','pandas','scipy')}
        with patch.dict(sys.modules,{'scipy':packages[2]}),patch.object(runtime_guard,'python_contract',return_value={}),patch.object(runtime_guard,'runtime',return_value=(packages[0],packages[1],None,None,None)),patch.object(runtime_guard,'sha256',return_value='mock'),patch.object(runtime_guard,'native_paths',return_value=[c.ROOT/'outside/openblas.dll']):
            with self.assertRaises(AssertionError):runtime_guard.origins({'files':files})

    def python_reference(self):
        executable=Path(sys.executable).resolve()
        paths=[executable,executable.parent/'python3.dll',executable.parent/'python312.dll']
        return {'python_executable':str(executable),'python_cache_tag':'cpython-312',
                'python_native_files':{str(path):'mock' for path in paths}}

    def test_wrong_python_executable_stops_before_scientific_import(self):
        reference=self.python_reference();reference['python_executable']=str(c.ROOT/'invented_python/python.exe')
        with patch.object(runtime_guard,'runtime',side_effect=RuntimeError('must not import')):
            with self.assertRaises(AssertionError):runtime_guard.origins(reference)

    def test_wrong_python_cache_tag_rejected_without_native_reads(self):
        reference=self.python_reference();reference['python_cache_tag']='cpython-311'
        with patch.object(runtime_guard,'sha256',side_effect=RuntimeError('must not read')):
            with self.assertRaises(AssertionError):runtime_guard.python_contract(reference)

    def test_changed_python_native_digest_rejected_mock(self):
        with patch.object(runtime_guard,'sha256',return_value='different'):
            with self.assertRaises(AssertionError):runtime_guard.python_contract(self.python_reference())

    def test_exact_python_native_roster_and_hashes_mock(self):
        reference=self.python_reference();calls=[]
        def digest(path):calls.append(Path(path));return 'mock'
        with patch.object(runtime_guard,'sha256',side_effect=digest):
            result=runtime_guard.python_contract(reference)
            self.assertEqual(len(calls),3);self.assertEqual(result['python_cache_tag'],'cpython-312')
            reference['python_native_files'].pop(next(iter(reference['python_native_files'])))
            with self.assertRaises(AssertionError):runtime_guard.python_contract(reference)

    def test_all_modules_parse_no_numeric_top_import(self):
        for path in Path(__file__).parent.glob('*.py'):
            tree=ast.parse(path.read_text())
            for node in tree.body:
                if isinstance(node,ast.Import):self.assertFalse(any(a.name.split('.')[0] in ('numpy','pandas','scipy','torch','RNA','openvino') for a in node.names))
                if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').startswith(('src.generalization_crosscell','src.generalization_knowncell','src.research')))

    def test_no_actual_numeric_import_or_project_load(self):
        self.assertFalse(any(name in sys.modules for name in ('numpy','pandas','scipy','torch','RNA','openvino')))


if __name__=='__main__':unittest.main(verbosity=2)
