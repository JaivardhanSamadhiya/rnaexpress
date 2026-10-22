"""Invented API failures plus optional tiny native children; no PUM data/worker."""
import ctypes as C
import hashlib
import os
from pathlib import Path
import shutil
import sys
import time
import unittest
from unittest.mock import patch
from . import winjob as w


class FakeAPI:
    def __init__(self):
        self.events = []
        self.extended = w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        self.job_handle = 0x100000010
        self.process_handle, self.thread_handle = 0x200000010, 0x300000010
        self.active = 0; self.total = 0; self.running = True
        self.assign_ok = self.member = self.query_ok = self.memory_ok = True
        self.resume_result = 1; self.code = 0; self.query_length_offset = 0

    def CreateJobObjectW(self, *_):
        self.events.append(('create_job', self.job_handle)); return self.job_handle

    def SetInformationJobObject(self, handle, kind, pointer, size):
        self.extended = w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION.from_buffer_copy(C.string_at(pointer, size))
        self.events.append(('set_limits', handle)); return 1

    def QueryInformationJobObject(self, handle, kind, pointer, size, returned):
        if not self.query_ok:return 0
        if kind == 9:
            C.memmove(pointer, C.byref(self.extended), size)
        else:
            pointer._obj.ActiveProcesses = self.active
            pointer._obj.TotalProcesses = self.total
        returned._obj.value = size + self.query_length_offset
        self.events.append(('query', kind)); return 1

    def CreateProcessW(self, executable, command, pa, ta, inherit, flags, env, cwd, startup, info):
        self.events.append(('create_process', executable, command.value, inherit, flags, env, cwd))
        info._obj.hProcess = self.process_handle; info._obj.hThread = self.thread_handle
        info._obj.dwProcessId = 12345; info._obj.dwThreadId = 12346
        return 1

    def AssignProcessToJobObject(self, handle, process):
        self.events.append(('assign', handle, process))
        if self.assign_ok:self.active = 1; self.total += 1
        return self.assign_ok

    def IsProcessInJob(self, process, job, result):
        self.events.append(('membership', process, job)); result._obj.value = self.member
        return 1

    def ResumeThread(self, handle):
        self.events.append(('resume', handle)); return self.resume_result

    def WaitForSingleObject(self, handle, timeout):
        return w.WAIT_TIMEOUT if self.running else w.WAIT_OBJECT_0

    def GetExitCodeProcess(self, handle, result):
        result._obj.value = self.code; return 1

    def TerminateProcess(self, handle, code):
        self.events.append(('terminate_process', handle)); self.running = False; return 1

    def TerminateJobObject(self, handle, code):
        self.events.append(('terminate_job', handle)); self.running = False; self.active = 0; return 1

    def CloseHandle(self, handle):
        self.events.append(('close', handle))
        if handle == self.job_handle:self.running = False; self.active = 0
        return 1

    def GlobalMemoryStatusEx(self, pointer):
        pointer._obj.ullTotalPhys = 16000
        pointer._obj.ullAvailPhys = 4000
        pointer._obj.ullAvailPageFile = 7  # Deliberately wrong for system headroom.
        return self.memory_ok

    def GetPerformanceInfo(self, pointer, size):
        pointer._obj.CommitLimit = 2000; pointer._obj.CommitTotal = 500; pointer._obj.PageSize = 4096
        return self.memory_ok

    def GetProcessMemoryInfo(self, handle, pointer, size):
        pointer._obj.PeakWorkingSetSize = 100; pointer._obj.WorkingSetSize = 80
        pointer._obj.PeakPagefileUsage = 90; pointer._obj.PrivateUsage = 70
        return self.memory_ok


class MockTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI(); self.patch = patch.object(w, '_api', return_value=self.api)
        self.patch.start(); self.addCleanup(self.patch.stop)

    def spawn(self, job):return job.spawn([sys.executable, '-B', '-c', 'pass'], str(w.ROOT))

    def test_win64_structures_and_pointer_offsets(self):
        if C.sizeof(w.HANDLE) != 8:self.skipTest('Win64 layouts only')
        for structure, size in ((w.MEMORYSTATUSEX,64), (w.PERFORMANCE_INFORMATION,104),
            (w.PROCESS_MEMORY_COUNTERS_EX,80), (w.JOBOBJECT_BASIC_LIMIT_INFORMATION,64),
            (w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION,144),
            (w.JOBOBJECT_BASIC_ACCOUNTING_INFORMATION,48), (w.STARTUPINFOW,104),
            (w.PROCESS_INFORMATION,24)):
            self.assertEqual(C.sizeof(structure),size)
        self.assertEqual(w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION.ProcessMemoryLimit.offset,112)
        self.assertEqual(w.PROCESS_MEMORY_COUNTERS_EX.PrivateUsage.offset,72)

    def test_system_commit_is_performance_counter_not_job_pagefile(self):
        with patch.object(w.shutil,'disk_usage',return_value=shutil._ntuple_diskusage(100,20,80)):
            value=w.memory()
        self.assertEqual(value['commit_headroom'],1500*4096)
        self.assertEqual(value['physical_available'],4000)
        self.assertEqual(value['disk_available'],80)

    def test_process_memory_counter_mapping(self):
        self.assertEqual(w.process_memory(self.api.process_handle),{
            'peak_working_set':100,'working_set':80,'peak_private_commit':90,'private_commit':70})

    def test_suspended_hidden_assignment_verification_then_single_resume(self):
        with w.Job() as job:
            child=self.spawn(job)
            events=[e[0] for e in self.api.events]
            self.assertNotIn('resume',events)
            self.assertLess(events.index('create_process'),events.index('assign'))
            self.assertLess(events.index('assign'),events.index('membership'))
            creation=next(e for e in self.api.events if e[0]=='create_process')
            self.assertFalse(creation[3]);self.assertEqual(creation[4],w.CREATE_SUSPENDED|w.CREATE_NO_WINDOW)
            self.assertIsNone(creation[5])
            child.resume();self.assertEqual(self.api.events[-1],('resume',self.api.thread_handle))
            with self.assertRaises(w.WinJobError):child.resume()
            self.assertEqual(child.pid,12345);child.close()

    def test_exact_limits_and_accounting(self):
        with w.Job() as job:
            self.assertEqual(job.limits(),{'process_memory_limit':768*2**20,
                'job_memory_limit':896*2**20,'active_process_limit':2,'limit_flags':w.LIMIT_FLAGS})
            self.api.extended.PeakJobMemoryUsed=456
            self.api.extended.PeakProcessMemoryUsed=123
            self.assertEqual(job.accounting()['peak_job_memory_used'],456)
            self.assertEqual(job.accounting()['peak_process_memory_used'],123)

    def test_assignment_failure_terminates_only_created_suspended_process(self):
        job=w.Job();self.api.assign_ok=False
        with self.assertRaises(OSError):self.spawn(job)
        self.assertIn(('terminate_process',self.api.process_handle),self.api.events)
        self.assertNotIn('resume',[e[0] for e in self.api.events])
        self.assertIsNone(job.handle)

    def test_false_membership_never_resumes(self):
        job=w.Job();self.api.member=False
        with self.assertRaises(w.WinJobError):self.spawn(job)
        self.assertNotIn('resume',[e[0] for e in self.api.events])
        self.assertIsNone(job.handle)

    def test_unassigned_cleanup_failure_preserves_owned_pid_in_error_text(self):
        job=w.Job();self.api.assign_ok=False
        self.api.TerminateProcess=lambda *_:0
        with self.assertRaisesRegex(w.WinJobError,'Owned child PID 12345 failed cleanup'):
            self.spawn(job)
        self.assertNotIn('resume',[e[0] for e in self.api.events])
        self.assertIsNone(job.handle)

    def test_changed_limits_before_resume_terminate_owned_job(self):
        job=w.Job();child=self.spawn(job)
        self.api.extended.BasicLimitInformation.LimitFlags |= 0x1000
        with self.assertRaises(w.WinJobError):child.resume()
        self.assertIn(('terminate_job',self.api.job_handle),self.api.events)
        self.assertNotIn('resume',[e[0] for e in self.api.events])
        child.close();job.close()

    def test_unexpected_suspend_count_is_fatal(self):
        job=w.Job();child=self.spawn(job);self.api.resume_result=0
        with self.assertRaises(w.WinJobError):child.resume()
        self.assertIn(('terminate_job',self.api.job_handle),self.api.events)
        child.close();job.close()

    def test_exit_poll_and_literal_259_exit_code(self):
        with w.Job() as job:
            child=self.spawn(job);self.assertIsNone(child.exit_code())
            self.api.running=False;self.api.code=259
            self.assertEqual(child.exit_code(),259)
            child.close()
            with self.assertRaises(w.WinJobError):child.exit_code()

    def test_failed_resource_measurement_fails_closed(self):
        self.api.memory_ok=False
        with self.assertRaises(OSError):w.memory()
        with self.assertRaises(OSError):w.process_memory(self.api.process_handle)

    def test_bad_query_length_closes_job_without_child(self):
        self.api.query_length_offset=-1
        with self.assertRaises(w.WinJobError):w.Job()
        self.assertIn(('close',self.api.job_handle),self.api.events)
        self.assertNotIn('create_process',[e[0] for e in self.api.events])

    def test_close_idempotent_and_only_owned_handles(self):
        job=w.Job();child=self.spawn(job);child.close();child.close();job.close();job.close()
        closed=[e[1] for e in self.api.events if e[0]=='close']
        self.assertEqual(closed,[self.api.thread_handle,self.api.process_handle,self.api.job_handle])

    def test_command_validation_and_no_second_live_worker(self):
        with w.Job() as job:
            for command in ('python -c pass', [], ['relative.exe'], [sys.executable,'bad\x00argument']):
                with self.assertRaises(ValueError):job.spawn(command,str(w.ROOT))
            child=self.spawn(job)
            with self.assertRaises(w.WinJobError):self.spawn(job)
            child.close()


@unittest.skipUnless(sys.platform=='win32' and os.environ.get('PUM_WINJOB_NATIVE_TESTS')=='1',
    'Native invented-child checks require explicit PUM_WINJOB_NATIVE_TESTS=1')
class NativeInventedChildTests(unittest.TestCase):
    def setUp(self):
        end=time.monotonic()+5
        while True:
            state=w.memory()
            if state['physical_available']>=512*2**20 and state['commit_headroom']>=896*2**20+2**30:
                break
            if time.monotonic()>=end:
                self.skipTest('Approved physical/commit headroom unavailable for tiny invented child')
            time.sleep(.1)

    def wait_exit(self, child, seconds=5):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            code=child.exit_code()
            if code is not None:return code
            time.sleep(.01)
        self.fail('Invented child did not terminate within bounded check')

    def wait_inactive(self, job, seconds=2):
        # The process object can be signaled just before the job's separate
        # active-process bookkeeping drains. Neither event permits cap widening.
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            active=job.accounting()['active_processes']
            self.assertLessEqual(active,2)
            if active==0:return
            time.sleep(.01)
        self.fail('Owned job accounting did not drain after invented child exit')

    def test_tiny_child_real_limits_membership_and_postexit_counters(self):
        with w.Job() as job:
            child=job.spawn([sys.executable,'-B','-c','import time; time.sleep(0.05)'],str(w.ROOT))
            try:
                self.assertNotEqual(child.pid,os.getpid())
                self.assertIsNone(child.exit_code())
                self.assertEqual(job.limits()['job_memory_limit'],896*2**20)
                child.resume()
                sample=w.process_memory(child.process_handle)
                self.assertGreater(sample['working_set'],0)
                self.assertEqual(self.wait_exit(child),0)
                final=w.process_memory(child.process_handle)
                self.assertGreaterEqual(final['peak_working_set'],sample['working_set'])
                self.wait_inactive(job)
                self.assertGreater(job.accounting()['peak_process_memory_used'],0)
            finally:child.close()

    def test_job_close_kills_only_owned_tiny_child(self):
        job=w.Job();child=None
        try:
            child=job.spawn([sys.executable,'-B','-c','import time; time.sleep(30)'],str(w.ROOT))
            child.resume();self.assertIsNone(child.exit_code())
            job.close()
            self.assertIsNotNone(self.wait_exit(child))
        finally:
            if child:child.close()
            job.close()

    def test_original_git_show_source_helper_fits_active_two(self):
        source='src/generalization_pum2_fixed_math_20261008/model.py'
        digest=hashlib.sha256((w.ROOT/source).read_bytes()).hexdigest()
        direct=Path('C:/Program Files/Git/mingw64/bin/git.exe')
        direct_sha='51c6331aab2426ae2df187975590587b5a10042e3423f4bc0fdcb54aeb3efab7'
        self.assertEqual(hashlib.sha256(direct.read_bytes()).hexdigest(),direct_sha)
        self.assertEqual(Path(shutil.which('git')).resolve(),direct.resolve(),
            'Tests require the explicit direct-Git resource route, never a larger process cap')
        script=('import hashlib,subprocess; '
            "r=subprocess.run(['git','show','HEAD:"+source+"'],capture_output=True); "
            'assert r.returncode==0,(r.returncode,r.stderr); '
            'assert hashlib.sha256(r.stdout).hexdigest()=='+repr(digest))
        with w.Job() as job:
            child=job.spawn([sys.executable,'-B','-c',script],str(w.ROOT))
            try:
                child.resume()
                self.assertEqual(self.wait_exit(child,10),0,'Original Git helper could not run inside active-process cap2')
                self.wait_inactive(job)
                self.assertLessEqual(job.accounting()['total_processes'],3)
            finally:child.close()


if __name__=='__main__':unittest.main()
