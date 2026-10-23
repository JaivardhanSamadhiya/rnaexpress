"""Additive console-free owned jobs and narrowly scoped source-Git launches.

All memory counters/limits and lifecycle verification come from the unchanged
original utility. No import or global subprocess module is patched.
"""
from contextlib import contextmanager
import ctypes as C
import hashlib
from pathlib import Path
from src.generalization_pum_resource_calibration_20261009 import winjob as original

DETACHED_PROCESS=0x00000008
DIRECT_GIT=Path('C:/Program Files/Git/mingw64/bin/git.exe')
DIRECT_GIT_SHA='51c6331aab2426ae2df187975590587b5a10042e3423f4bc0fdcb54aeb3efab7'
WINJOB_SHA='3a2b470f116e87ff6233cdc8710b2703cf33b908dae68ece7fb4592227b5f741'
memory=original.memory
process_memory=original.process_memory


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):value.update(block)
    return value.hexdigest()


class _DetachedCreation:
    def __init__(self,api):self.api=api
    def __getattr__(self,name):return getattr(self.api,name)
    def CreateProcessW(self,*args):
        if args[5] != original.CREATE_SUSPENDED|original.CREATE_NO_WINDOW:
            raise RuntimeError('Unexpected original creation flags; no fallback')
        amended=list(args);amended[5]=original.CREATE_SUSPENDED|DETACHED_PROCESS
        return self.api.CreateProcessW(*amended)


class Job(original.Job):
    def __init__(self):
        if sha(original.__file__)!=WINJOB_SHA:
            raise RuntimeError('Frozen original WinJob source changed')
        super().__init__()
        self._api=_DetachedCreation(self._api)


class GitFacade:
    """One module binding only: Git show bytes with pinned exe and DETACHED flag."""
    def __init__(self,module):
        if isinstance(module,GitFacade):raise RuntimeError('Nested Git facades are forbidden')
        if sha(DIRECT_GIT)!=DIRECT_GIT_SHA:raise RuntimeError('Pinned direct Git changed')
        self._module=module
    def __getattr__(self,name):return getattr(self._module,name)
    def check_output(self,args,**kwargs):
        if not isinstance(args,(list,tuple)) or len(args)!=3 or args[1]!='show':
            raise ValueError('Only the frozen three-argument Git show calls are allowed')
        if not all(isinstance(x,str) and '\x00' not in x for x in args):
            raise ValueError('Literal Git arguments required')
        if args[0] not in ('git','git.exe') and Path(args[0]).resolve()!=DIRECT_GIT.resolve():
            raise ValueError('Only pinned direct Git is allowed')
        if not args[2].startswith('HEAD:') or not args[2][5:]:raise ValueError('Only HEAD file bytes allowed')
        if kwargs.get('shell') or kwargs.get('text') or kwargs.get('encoding') or kwargs.get('universal_newlines'):
            raise ValueError('No shell or text conversion is admitted')
        if kwargs.get('creationflags',0) not in (0,DETACHED_PROCESS):
            raise ValueError('Unexpected helper creation flags')
        amended=dict(kwargs);amended['creationflags']=DETACHED_PROCESS
        return self._module.check_output([str(DIRECT_GIT),*args[1:]],**amended)


@contextmanager
def scoped_git(module):
    """Rebind only module.subprocess, then restore the exact original object."""
    old=module.subprocess
    module.subprocess=GitFacade(old)
    try:yield module.subprocess
    finally:module.subprocess=old


def native_origins():
    """Actual system DLL paths/hashes used by the original native bindings."""
    api=original._api();kernel=C.WinDLL('kernel32',use_last_error=True)
    kernel.GetModuleFileNameW.argtypes=[original.HANDLE,C.POINTER(C.c_wchar),original.DWORD]
    kernel.GetModuleFileNameW.restype=original.DWORD
    kernel.GetSystemDirectoryW.argtypes=[C.POINTER(C.c_wchar),original.DWORD]
    kernel.GetSystemDirectoryW.restype=original.DWORD
    directory=C.create_unicode_buffer(32768)
    count=kernel.GetSystemDirectoryW(directory,len(directory))
    if not 0<count<len(directory):raise C.WinError(C.get_last_error())
    result={}
    for name,dll in (('kernel32.dll',api.kernel32),('psapi.dll',api.psapi)):
        text=C.create_unicode_buffer(32768)
        count=kernel.GetModuleFileNameW(dll._handle,text,len(text))
        if not 0<count<len(text):raise C.WinError(C.get_last_error())
        path=Path(text.value).resolve()
        if path!=Path(directory.value,name).resolve():raise RuntimeError('Unexpected native DLL origin')
        result[name]={'path':str(path),'sha256':sha(path)}
    return result
