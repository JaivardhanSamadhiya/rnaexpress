"""Actual current scientific modules/native DLLs against frozen local inventory."""
from .common import *

SCIENTIFIC=ROOT/'artifacts/generalization_splicebert_runtime_compatibility_20261007/scientific_runtime_receipt.json'
PREFIX=ROOT/'data/interim/mechanism_v2/runtime'


def python_contract(reference):
    import sys
    executable=Path(sys.executable).resolve()
    assert executable==Path(reference['python_executable']).resolve(),'Python executable differs from pinned runtime'
    assert sys.version_info[:2]==(3,12)
    assert sys.implementation.cache_tag==reference['python_cache_tag']=='cpython-312'
    native=reference['python_native_files'];pins={}
    for name,expected in native.items():
        path=Path(name).resolve();key=str(path).casefold()
        assert key not in pins,'Python native path alias';pins[key]=(path,expected)
    expected={str(executable).casefold(),str(executable.parent/'python3.dll').casefold(),
              str(executable.parent/'python312.dll').casefold()}
    assert set(pins)==expected,'Python native inventory must contain exact pinned executable/CP312 DLLs'
    for path,digest in pins.values():assert sha256(path)==digest,'Changed Python native file: '+str(path)
    return {'python_executable':str(executable),'python_cache_tag':sys.implementation.cache_tag,
            'python_native_files':native}


def native_paths():
    from ctypes import wintypes
    psapi=ctypes.WinDLL('psapi',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE;process=kernel.GetCurrentProcess()
    modules=(wintypes.HMODULE*8192)();needed=wintypes.DWORD()
    psapi.EnumProcessModules.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.HMODULE),wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
    psapi.GetModuleFileNameExW.argtypes=[wintypes.HANDLE,wintypes.HMODULE,wintypes.LPWSTR,wintypes.DWORD]
    assert psapi.EnumProcessModules(process,modules,ctypes.sizeof(modules),ctypes.byref(needed))
    assert needed.value<=ctypes.sizeof(modules)
    paths=[]
    for module in modules[:needed.value//ctypes.sizeof(wintypes.HMODULE)]:
        buffer=ctypes.create_unicode_buffer(32768)
        size=psapi.GetModuleFileNameExW(process,module,buffer,len(buffer));assert size and size<len(buffer)-1
        paths.append(Path(buffer.value).resolve())
    return paths


def origins(reference):
    python=python_contract(reference)
    np,pd,*_=runtime();import scipy
    files=reference['files'];modules={}
    pins={key.replace('\\','/'):value for key,value in files.items()}
    assert len(pins)==len(files),'Runtime inventory path alias'
    for package in (np,pd,scipy):
        path=Path(package.__file__).resolve();assert path.is_relative_to(PREFIX.resolve())
        name=path.relative_to(PREFIX.resolve()).as_posix();assert sha256(path)==pins[name]
        modules[package.__name__]={'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(path),'version':package.__version__}
    selected={}
    for path in native_paths():
        name=path.name.casefold()
        relevant=path.is_relative_to(PREFIX.resolve()) or any(key in name for key in ('openblas','mkl','libiomp','blas'))
        if not relevant:continue
        assert path.is_relative_to(PREFIX.resolve()),'Scientific native DLL outside admitted runtime: '+str(path)
        name=path.relative_to(PREFIX.resolve()).as_posix();assert sha256(path)==pins[name],name
        selected[path.relative_to(ROOT).as_posix()]=sha256(path)
    assert selected,'No observed scientific native modules'
    return {'modules':modules,'loaded_scientific_native_files':selected,**python}


def make():
    thread_check();committed(SCIENTIFIC);reference=readj(SCIENTIFIC);assert reference['status']=='PASS'
    for name,expected in reference['files'].items():assert sha256(PREFIX/name)==expected,name
    result=origins(reference)
    jsave(OUT/'runtime_binding.json',{'status':'PASS','scientific_receipt_sha256':sha256(SCIENTIFIC),
        'scientific_files':reference['files'],'python_executable':reference['python_executable'],
        'python_cache_tag':reference['python_cache_tag'],'python_native_files':reference['python_native_files'],
        'initial_origins':result,'numerical_threads':1,
        'current_origin_proof_not_retroactive_old_fit_runtime_certificate':True})
    return result


def check():
    thread_check();value=readj(OUT/'runtime_binding.json');assert value['status']=='PASS'
    assert value['scientific_receipt_sha256']==sha256(SCIENTIFIC)
    reference=readj(SCIENTIFIC)
    for name in ('python_executable','python_cache_tag','python_native_files'):assert value[name]==reference[name]
    result=origins({'files':value['scientific_files'],**{name:reference[name] for name in
                   ('python_executable','python_cache_tag','python_native_files')}})
    assert result['modules']==value['initial_origins']['modules']
    assert result['python_executable']==value['initial_origins']['python_executable']
    return result
