"""Tiny invented native NPZ contract and fixed-prediction bootstrap checks."""
import ast
import hashlib
import io
from .common import ROOT
from .cases import float_bytes

ORIGINAL_BOOTSTRAP=ROOT/'src/generalization_crosscell_20261007/bootstrap.py'


def array_check(np):
    from src.generalization_knowncell_array_contract_20261022.envelope import inspect_supplied_npz
    from src.generalization_knowncell_array_contract_20261022.inspect_bytes import source_row_bytes
    original=np.array([[1.25,-2.5,-0.0],[5e-324,9007199254740992.,0.0]],dtype=np.float64,order='C')
    stream=io.BytesIO();np.savez_compressed(stream,features=original)
    raw=stream.getvalue();digest=hashlib.sha256(raw).hexdigest()
    inspected=inspect_supplied_npz(raw,digest,expected_shape=(2,3))
    stored=b''.join(source_row_bytes(inspected['npy_bytes'],inspected['npy']))
    with np.load(io.BytesIO(raw),allow_pickle=False) as archive:
        converted=archive['features'].astype(float)
    assert converted.shape==(2,3) and converted.dtype==np.float64
    assert stored==converted.tobytes(order='C')==original.tobytes(order='C')
    assert float_bytes(converted.ravel(order='C'))==stored
    return {'status':'PASS_INVENTED_SUPPLIED_NUMPY_NPZ_AND_ASTYPE_FLOAT_BITS',
            'shape':[2,3],'npz_bytes':len(raw),'npz_sha256':digest,
            'scalar_float64_bits_hex':stored.hex(),'project_wrapper_called':False,
            'project_array_reads':0,'allow_pickle':False}


class _ObservedGenerator:
    def __init__(self,generator,observed):self.generator=generator;self.observed=observed
    def exponential(self,*args,**kwargs):
        value=self.generator.exponential(*args,**kwargs)
        self.observed.append({'sha256':hashlib.sha256(value.tobytes(order='C')).hexdigest(),
                              'shape':list(value.shape)})
        return value


class _ObservedRandom:
    def __init__(self,np,observed):self.np=np;self.observed=observed
    def default_rng(self,seed):
        assert seed==20261007
        return _ObservedGenerator(self.np.random.default_rng(seed),self.observed)


class _ObservedNP:
    def __init__(self,np,observed):self.np=np;self.random=_ObservedRandom(np,observed)
    def __getattr__(self,name):return getattr(self.np,name)


def original_bootstrap_function(np,observed):
    """Compile only the exact pinned old function; do not import its loader."""
    tree=ast.parse(ORIGINAL_BOOTSTRAP.read_text(encoding='utf-8'))
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='shared_bootstrap']
    assert len(functions)==1 and not functions[0].decorator_list
    module=ast.Module(body=functions,type_ignores=[])
    scope={'np':_ObservedNP(np,observed),'SEED':20261007}
    exec(compile(module,str(ORIGINAL_BOOTSTRAP),'exec'),scope)
    return scope['shared_bootstrap']


def bootstrap_check(np,pd):
    from src.generalization_knowncell_joint_gate_20261023.gate import native_shared_bootstrap
    genes=[f'invented_gene_{index:03}' for index in range(187)]
    comparisons={}
    for name in ('pooled','independent'):
        gains={}
        for cell,sign in (('CAD',1.),('Neuro-2a',-1.)):
            gains[cell]={gene:(((i%17)-8)/1000.+sign*.003 if name=='pooled'
                               else ((i%13)-6)/2000.+sign*.002)
                         for i,gene in enumerate(genes)}
        comparisons[name]={'component_gains':gains}
    actual=native_shared_bootstrap(np,comparisons)
    observed=[];original=original_bootstrap_function(np,observed);expected={}
    for name,comparison in comparisons.items():
        series={cell:pd.Series([values[gene] for gene in genes],index=genes,dtype=np.float64)
                for cell,values in comparison['component_gains'].items()}
        samples=original(series,5000,20261007)
        interval=[float(np.quantile(samples,.025)),float(np.quantile(samples,.975))]
        assert interval==actual['intervals'][name]
        expected[name]=interval
    assert len(observed)==2
    assert all(value['shape']==[5000,187] for value in observed)
    assert all(value['sha256']==actual['shared_original_exponential_draws_sha256'] for value in observed)
    assert actual['components']==genes and actual['draws']==5000 and actual['seed']==20261007
    return {'status':'PASS_INVENTED_NATIVE_SHARED_BOOTSTRAP_EXACT_CURRENT_RUNTIME_REPLAY',
            'components':187,'draws':5000,'seed':20261007,'controls':['pooled','independent'],
            'target_uses_one_shared_draw_matrix':True,'original_reference_function_calls':2,
            'identical_draw_matrix_sha256':actual['shared_original_exponential_draws_sha256'],
            'intervals':expected,'default_numpy_quantiles_preserved':True,
            'original_function_only_compiled_not_broad_module_imported':True,
            'fixed_invented_predictions_only':True,'biological_gate_run':False}


def run(np,pd):
    return {'array_contract':array_check(np),'shared_bootstrap':bootstrap_check(np,pd)}
