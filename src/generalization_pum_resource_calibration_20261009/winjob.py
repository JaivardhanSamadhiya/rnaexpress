"""Owned Win64 jobs and byte-valued memory counters; no scientific imports.

The caller owns resource admission, monitoring, provenance, and receipt policy.
This module never changes a producer callback or a host/parent job policy.
"""
from __future__ import annotations

import ctypes as C
from functools import lru_cache
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DWORD = C.c_uint32
BOOL = C.c_int32
SIZE_T = C.c_size_t
HANDLE = C.c_void_p
ULONG64 = C.c_uint64
LARGE_INTEGER = C.c_int64
PROCESS_LIMIT = 768 * 2**20
JOB_LIMIT = 896 * 2**20
ACTIVE_LIMIT = 2
JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
LIMIT_FLAGS = (JOB_OBJECT_LIMIT_ACTIVE_PROCESS | JOB_OBJECT_LIMIT_PROCESS_MEMORY
               | JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
WAIT_FAILED = 0xFFFFFFFF
RESOURCE_EXIT_CODE = 0xE0000001


class MEMORYSTATUSEX(C.Structure):
    _fields_ = [('dwLength', DWORD), ('dwMemoryLoad', DWORD)] + [
        (name, ULONG64) for name in ('ullTotalPhys', 'ullAvailPhys', 'ullTotalPageFile',
            'ullAvailPageFile', 'ullTotalVirtual', 'ullAvailVirtual', 'ullAvailExtendedVirtual')]


class PERFORMANCE_INFORMATION(C.Structure):
    _fields_ = [('cb', DWORD)] + [(name, SIZE_T) for name in (
        'CommitTotal', 'CommitLimit', 'CommitPeak', 'PhysicalTotal', 'PhysicalAvailable',
        'SystemCache', 'KernelTotal', 'KernelPaged', 'KernelNonpaged', 'PageSize')] + [
        ('HandleCount', DWORD), ('ProcessCount', DWORD), ('ThreadCount', DWORD)]


class PROCESS_MEMORY_COUNTERS_EX(C.Structure):
    _fields_ = [('cb', DWORD), ('PageFaultCount', DWORD)] + [(name, SIZE_T) for name in (
        'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
        'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage',
        'PeakPagefileUsage', 'PrivateUsage')]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(C.Structure):
    _fields_ = [('PerProcessUserTimeLimit', LARGE_INTEGER), ('PerJobUserTimeLimit', LARGE_INTEGER),
        ('LimitFlags', DWORD), ('MinimumWorkingSetSize', SIZE_T), ('MaximumWorkingSetSize', SIZE_T),
        ('ActiveProcessLimit', DWORD), ('Affinity', SIZE_T), ('PriorityClass', DWORD),
        ('SchedulingClass', DWORD)]


class IO_COUNTERS(C.Structure):
    _fields_ = [(name, ULONG64) for name in ('ReadOperationCount', 'WriteOperationCount',
        'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(C.Structure):
    _fields_ = [('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION), ('IoInfo', IO_COUNTERS),
        ('ProcessMemoryLimit', SIZE_T), ('JobMemoryLimit', SIZE_T),
        ('PeakProcessMemoryUsed', SIZE_T), ('PeakJobMemoryUsed', SIZE_T)]


class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(C.Structure):
    _fields_ = [(name, LARGE_INTEGER) for name in ('TotalUserTime', 'TotalKernelTime',
        'ThisPeriodTotalUserTime', 'ThisPeriodTotalKernelTime')] + [(name, DWORD) for name in (
        'TotalPageFaultCount', 'TotalProcesses', 'ActiveProcesses', 'TotalTerminatedProcesses')]


class STARTUPINFOW(C.Structure):
    _fields_ = [('cb', DWORD), ('lpReserved', C.c_wchar_p), ('lpDesktop', C.c_wchar_p),
        ('lpTitle', C.c_wchar_p)] + [(name, DWORD) for name in ('dwX', 'dwY', 'dwXSize',
        'dwYSize', 'dwXCountChars', 'dwYCountChars', 'dwFillAttribute', 'dwFlags')] + [
        ('wShowWindow', C.c_uint16), ('cbReserved2', C.c_uint16), ('lpReserved2', C.c_void_p),
        ('hStdInput', HANDLE), ('hStdOutput', HANDLE), ('hStdError', HANDLE)]


class PROCESS_INFORMATION(C.Structure):
    _fields_ = [('hProcess', HANDLE), ('hThread', HANDLE), ('dwProcessId', DWORD), ('dwThreadId', DWORD)]


class WinJobError(RuntimeError):
    pass


def _error(operation):
    number = C.get_last_error() if hasattr(C, 'get_last_error') else 0
    description = C.FormatError(number).strip() if hasattr(C, 'FormatError') else 'native failure'
    return OSError(number, operation + ': ' + description)


class _NativeAPI:
    def __init__(self):
        if sys.platform != 'win32' or C.sizeof(HANDLE) != 8:
            raise WinJobError('This utility requires 64-bit Windows Python')
        self.kernel32 = C.WinDLL('kernel32', use_last_error=True)
        self.psapi = C.WinDLL('psapi', use_last_error=True)
        definitions = {
            'CreateJobObjectW': ([C.c_void_p, C.c_wchar_p], HANDLE),
            'SetInformationJobObject': ([HANDLE, C.c_int32, C.c_void_p, DWORD], BOOL),
            'QueryInformationJobObject': ([HANDLE, C.c_int32, C.c_void_p, DWORD, C.POINTER(DWORD)], BOOL),
            'AssignProcessToJobObject': ([HANDLE, HANDLE], BOOL),
            'IsProcessInJob': ([HANDLE, HANDLE, C.POINTER(BOOL)], BOOL),
            'CreateProcessW': ([C.c_wchar_p, C.POINTER(C.c_wchar), C.c_void_p, C.c_void_p,
                BOOL, DWORD, C.c_void_p, C.c_wchar_p, C.POINTER(STARTUPINFOW),
                C.POINTER(PROCESS_INFORMATION)], BOOL),
            'ResumeThread': ([HANDLE], DWORD),
            'GetExitCodeProcess': ([HANDLE, C.POINTER(DWORD)], BOOL),
            'WaitForSingleObject': ([HANDLE, DWORD], DWORD),
            'TerminateProcess': ([HANDLE, DWORD], BOOL),
            'TerminateJobObject': ([HANDLE, DWORD], BOOL),
            'CloseHandle': ([HANDLE], BOOL),
            'GlobalMemoryStatusEx': ([C.POINTER(MEMORYSTATUSEX)], BOOL),
        }
        for name, (arguments, result) in definitions.items():
            function = getattr(self.kernel32, name)
            function.argtypes, function.restype = arguments, result
            setattr(self, name, function)
        for name, arguments in (
            ('GetPerformanceInfo', [C.POINTER(PERFORMANCE_INFORMATION), DWORD]),
            ('GetProcessMemoryInfo', [HANDLE, C.POINTER(PROCESS_MEMORY_COUNTERS_EX), DWORD])):
            function = getattr(self.psapi, name)
            function.argtypes, function.restype = arguments, BOOL
            setattr(self, name, function)


@lru_cache(maxsize=1)
def _api():
    return _NativeAPI()


def memory():
    """Fresh system physical/commit and workspace disk bytes, not job pagefile capacity."""
    api = _api()
    physical = MEMORYSTATUSEX(); physical.dwLength = C.sizeof(physical)
    performance = PERFORMANCE_INFORMATION(); performance.cb = C.sizeof(performance)
    if not api.GlobalMemoryStatusEx(C.byref(physical)):
        raise _error('GlobalMemoryStatusEx')
    if not api.GetPerformanceInfo(C.byref(performance), C.sizeof(performance)):
        raise _error('GetPerformanceInfo')
    if performance.PageSize <= 0 or performance.CommitLimit < performance.CommitTotal:
        raise WinJobError('Invalid system commit counter snapshot')
    return {'physical_available': int(physical.ullAvailPhys),
        'physical_total': int(physical.ullTotalPhys),
        'commit_headroom': int((performance.CommitLimit-performance.CommitTotal)*performance.PageSize),
        'disk_available': int(shutil.disk_usage(ROOT).free)}


def process_memory(handle):
    """Process counters in bytes; peak_private_commit is Windows PeakPagefileUsage."""
    if not handle:
        raise WinJobError('A live owned process handle is required')
    counters = PROCESS_MEMORY_COUNTERS_EX(); counters.cb = C.sizeof(counters)
    if not _api().GetProcessMemoryInfo(handle, C.byref(counters), C.sizeof(counters)):
        raise _error('GetProcessMemoryInfo')
    return {'peak_working_set': int(counters.PeakWorkingSetSize),
        'working_set': int(counters.WorkingSetSize),
        'peak_private_commit': int(counters.PeakPagefileUsage),
        'private_commit': int(counters.PrivateUsage)}


class Job:
    def __init__(self):
        self._api = _api()
        self.handle = self._api.CreateJobObjectW(None, None)
        if not self.handle:
            raise _error('CreateJobObjectW')
        try:
            value = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            value.BasicLimitInformation.LimitFlags = LIMIT_FLAGS
            value.BasicLimitInformation.ActiveProcessLimit = ACTIVE_LIMIT
            value.ProcessMemoryLimit, value.JobMemoryLimit = PROCESS_LIMIT, JOB_LIMIT
            if not self._api.SetInformationJobObject(self.handle, 9, C.byref(value), C.sizeof(value)):
                raise _error('SetInformationJobObject')
            self._verify_limits()
        except BaseException:
            self.close()
            raise

    def _open(self):
        if not self.handle:
            raise WinJobError('Owned job is already closed')

    def _query(self, information_class, structure):
        self._open(); value = structure(); returned = DWORD()
        if not self._api.QueryInformationJobObject(self.handle, information_class,
                C.byref(value), C.sizeof(value), C.byref(returned)):
            raise _error('QueryInformationJobObject')
        if returned.value != C.sizeof(value):
            raise WinJobError('Unexpected job query structure length')
        return value

    def limits(self):
        value = self._query(9, JOBOBJECT_EXTENDED_LIMIT_INFORMATION)
        return {'process_memory_limit': int(value.ProcessMemoryLimit),
            'job_memory_limit': int(value.JobMemoryLimit),
            'active_process_limit': int(value.BasicLimitInformation.ActiveProcessLimit),
            'limit_flags': int(value.BasicLimitInformation.LimitFlags)}

    def _verify_limits(self):
        expected = {'process_memory_limit': PROCESS_LIMIT, 'job_memory_limit': JOB_LIMIT,
            'active_process_limit': ACTIVE_LIMIT, 'limit_flags': LIMIT_FLAGS}
        if self.limits() != expected:
            raise WinJobError('Exact owned-job limits were not applied; no fallback')

    def accounting(self):
        extended = self._query(9, JOBOBJECT_EXTENDED_LIMIT_INFORMATION)
        basic = self._query(1, JOBOBJECT_BASIC_ACCOUNTING_INFORMATION)
        return {'peak_job_memory_used': int(extended.PeakJobMemoryUsed),
            'peak_process_memory_used': int(extended.PeakProcessMemoryUsed),
            'active_processes': int(basic.ActiveProcesses), 'total_processes': int(basic.TotalProcesses),
            'terminated_processes': int(basic.TotalTerminatedProcesses),
            'user_time_100ns': int(basic.TotalUserTime), 'kernel_time_100ns': int(basic.TotalKernelTime)}

    def _membership(self, process_handle):
        answer = BOOL()
        if not self._api.IsProcessInJob(process_handle, self.handle, C.byref(answer)):
            raise _error('IsProcessInJob')
        if not answer.value:
            raise WinJobError('Child is not in the exact owned job; no fallback')

    def spawn(self, command: list[str], cwd: str):
        self._open(); self._verify_limits()
        if not isinstance(command, list) or not command or not all(
                isinstance(x, str) and '\x00' not in x for x in command):
            raise ValueError('A nonempty argument list without NUL is required')
        executable = Path(command[0]); directory = Path(cwd)
        if not executable.is_absolute() or not executable.is_file():
            raise ValueError('An explicit existing absolute executable path is required')
        if not directory.is_absolute() or not directory.is_dir():
            raise ValueError('An existing absolute working directory is required')
        if self.accounting()['active_processes'] != 0:
            raise WinJobError('Only one scientific child at a time is permitted')
        text = subprocess.list2cmdline(command)
        if len(text) >= 32767:
            raise ValueError('Windows command line is too long')
        mutable = C.create_unicode_buffer(text)
        startup = STARTUPINFOW(); startup.cb = C.sizeof(startup)
        info = PROCESS_INFORMATION()
        if not self._api.CreateProcessW(str(executable), mutable, None, None, False,
                CREATE_SUSPENDED | CREATE_NO_WINDOW, None, str(directory),
                C.byref(startup), C.byref(info)):
            raise _error('CreateProcessW')
        try:
            if not info.hProcess or not info.hThread or not info.dwProcessId:
                raise WinJobError('Incomplete owned child identity')
            if not self._api.AssignProcessToJobObject(self.handle, info.hProcess):
                raise _error('AssignProcessToJobObject; host hierarchy fallback forbidden')
            self._verify_limits(); self._membership(info.hProcess)
            return Child(self, int(info.dwProcessId), info.hProcess, info.hThread)
        except BaseException as error:
            # This process was just created by us and is still suspended. It may
            # not yet belong to the job if assignment failed: terminate its own
            # creation handle explicitly, then close only our resources.
            cleanup_failures = []
            if info.hProcess:
                if not self._api.TerminateProcess(info.hProcess, RESOURCE_EXIT_CODE):
                    cleanup_failures.append('TerminateProcess failed')
                if self._api.WaitForSingleObject(info.hProcess, 5000) != WAIT_OBJECT_0:
                    cleanup_failures.append('owned process termination was not observed within5s')
            for handle in (info.hThread, info.hProcess):
                if handle and not self._api.CloseHandle(handle):
                    cleanup_failures.append('creation-handle close failed')
            try:
                self.close()
            except BaseException as close_error:
                cleanup_failures.append('owned job close failed: '+str(close_error))
            if cleanup_failures:
                raise WinJobError('Owned child PID '+str(int(info.dwProcessId))+
                    ' failed cleanup: '+'; '.join(cleanup_failures)+
                    '; original '+type(error).__name__+': '+str(error)) from error
            raise

    def terminate(self):
        if self.handle and not self._api.TerminateJobObject(self.handle, RESOURCE_EXIT_CODE):
            raise _error('TerminateJobObject')

    def close(self):
        if self.handle:
            if not self._api.CloseHandle(self.handle):
                raise _error('CloseHandle(owned job)')
            self.handle = None

    def __enter__(self):
        self._open(); return self

    def __exit__(self, *_):
        self.close()


class Child:
    def __init__(self, owner, pid, process_handle, thread_handle):
        self._owner, self._api = owner, owner._api
        self.pid, self.process_handle, self.thread_handle = pid, process_handle, thread_handle
        self._resumed = False

    def resume(self):
        if self._resumed or not self.thread_handle or not self.process_handle:
            raise WinJobError('Child can only be resumed once with open creation handles')
        try:
            self._owner._verify_limits(); self._owner._membership(self.process_handle)
            previous = self._api.ResumeThread(self.thread_handle)
            if previous == WAIT_FAILED:
                raise _error('ResumeThread')
            if previous != 1:
                raise WinJobError('Unexpected original suspend count; terminate owned job')
            self._resumed = True
        except BaseException:
            self._owner.terminate()
            raise

    def exit_code(self):
        if not self.process_handle:
            raise WinJobError('Owned process handle is closed')
        wait = self._api.WaitForSingleObject(self.process_handle, 0)
        if wait == WAIT_TIMEOUT:
            return None
        if wait == WAIT_FAILED:
            raise _error('WaitForSingleObject')
        if wait != WAIT_OBJECT_0:
            raise WinJobError('Unexpected process wait result')
        code = DWORD()
        if not self._api.GetExitCodeProcess(self.process_handle, C.byref(code)):
            raise _error('GetExitCodeProcess')
        return int(code.value)

    def terminate(self):
        self._owner.terminate()

    def close(self):
        failures = []
        for name in ('thread_handle', 'process_handle'):
            handle = getattr(self, name)
            if handle:
                if self._api.CloseHandle(handle):
                    setattr(self, name, None)
                else:
                    failures.append(name)
        if failures:
            raise _error('CloseHandle(owned child: '+','.join(failures)+')')
