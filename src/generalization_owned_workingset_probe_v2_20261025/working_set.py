"""An additional physical working-set cap on our suspended child only."""
import ctypes as C
from functools import lru_cache
from src.generalization_pum_process_probe_20261021 import headless

MAXIMUM=190*2**20
MAX_ENABLE=4
MAX_DISABLE=8
MIN_FLAGS=3


class Native:
    def __init__(self):
        w=headless.original
        self.dll=C.WinDLL('kernel32',use_last_error=True)
        self.get=self.dll.GetProcessWorkingSetSizeEx
        self.get.argtypes=[w.HANDLE,C.POINTER(w.SIZE_T),C.POINTER(w.SIZE_T),C.POINTER(w.DWORD)]
        self.get.restype=w.BOOL
        self.set=self.dll.SetProcessWorkingSetSizeEx
        self.set.argtypes=[w.HANDLE,w.SIZE_T,w.SIZE_T,w.DWORD]
        self.set.restype=w.BOOL

    def query(self,handle):
        w=headless.original
        low,high,flags=w.SIZE_T(),w.SIZE_T(),w.DWORD()
        if not self.get(handle,C.byref(low),C.byref(high),C.byref(flags)):
            raise C.WinError(C.get_last_error())
        return {'minimum':low.value,'maximum':high.value,'flags':flags.value}

    def install(self,handle,minimum,maximum,flags):
        if not self.set(handle,minimum,maximum,flags):raise C.WinError(C.get_last_error())


@lru_cache(maxsize=1)
def native():return Native()


def owned(job,child,*,suspended=False):
    assert child._owner is job and child.process_handle
    if suspended:assert child._resumed is False,'Apply before first resume only'
    job._verify_limits()
    job._membership(child.process_handle)


def apply(job,child):
    owned(job,child,suspended=True)
    before=native().query(child.process_handle)
    assert 0<before['minimum']<=MAXIMUM
    assert before['flags']&~15==0 and (before['flags']&MIN_FLAGS) in (0,1,2)
    flags=(before['flags']&MIN_FLAGS)|MAX_ENABLE
    native().install(child.process_handle,before['minimum'],MAXIMUM,flags)
    after=native().query(child.process_handle)
    assert after=={'minimum':before['minimum'],'maximum':MAXIMUM,'flags':flags}
    owned(job,child,suspended=True)
    return {'before':before,'after':after,'only_suspended_owned_child_changed':True,
        'private_and_job_caps_or_live_guards_changed':False}


def verify(job,child,receipt):
    owned(job,child)
    assert native().query(child.process_handle)==receipt['after']
    return True
