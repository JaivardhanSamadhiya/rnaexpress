"""Fresh original-floor checks and byte-hashed streams; no eager native calls."""
import hashlib
import io
import os
from pathlib import Path
import shutil
from src.generalization_knowncell_joint_implementation_20261022.admission import require_resources
from .spec import ROOT


def live_resources():
    """Called only during a separately authorized future project admission."""
    assert os.name == 'nt', 'This project controller requires Windows'
    import ctypes
    from ctypes import wintypes
    class MemoryStatus(ctypes.Structure):
        _fields_ = [('dwLength', wintypes.DWORD), ('dwMemoryLoad', wintypes.DWORD),
                    ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MemoryStatus)]
    kernel.GlobalMemoryStatusEx.restype = wintypes.BOOL
    status = MemoryStatus(); status.dwLength = ctypes.sizeof(status)
    if not kernel.GlobalMemoryStatusEx(ctypes.byref(status)): raise ctypes.WinError(ctypes.get_last_error())
    return {'physical_available': status.ullAvailPhys, 'physical_total': status.ullTotalPhys,
            'disk_available': shutil.disk_usage(ROOT).free, 'PUM_resource_exception_applied': False}


def fresh_gate(resource_probe=None, environment=None):
    probe = live_resources if resource_probe is None else resource_probe
    environment = os.environ if environment is None else environment
    snapshot = probe()
    require_resources(snapshot, environment)
    return snapshot


class HashingRaw(io.RawIOBase):
    def __init__(self, raw):
        super().__init__(); self.raw = raw; self.digest = hashlib.sha256(); self.byte_count = 0
    def readable(self): return True
    def readinto(self, buffer):
        count = self.raw.readinto(buffer)
        if count:
            self.digest.update(memoryview(buffer)[:count]); self.byte_count += count
        return count


def guarded_payload(path, expected_sha256, parser, *, text=False, resource_probe=None, environment=None):
    """Immediate probe before EACH open; hash the exact bytes seen by the parser.

    A caller must additionally validate the fixed alias/admission. Tests use
    only invented temporary files. This helper grants no path authorization.
    """
    assert isinstance(expected_sha256, str) and len(expected_sha256) == 64
    path = Path(path)
    fresh_gate(resource_probe, environment)
    with path.open('rb') as raw:
        tee = HashingRaw(raw)
        with io.BufferedReader(tee) as buffered:
            if text:
                with io.TextIOWrapper(buffered, encoding='utf-8-sig', newline='') as stream:
                    result = parser(stream)
            else:
                result = parser(buffered)
            assert tee.byte_count == path.stat().st_size, 'Parser did not traverse entire pinned payload'
            actual = tee.digest.hexdigest()
    assert actual == expected_sha256, 'Actual payload bytes differ from immutable admission'
    return result, {'actual_sha256': actual, 'raw_bytes_traversed': tee.byte_count,
                    'fresh_original_resource_gate_before_open': True}


def guarded_bytes(path, *, resource_probe=None, environment=None, maximum=64 * 2**20):
    """For fixed small admission/source/metadata objects, never NPZ or CORE."""
    fresh_gate(resource_probe, environment)
    path = Path(path); assert path.stat().st_size <= maximum
    with path.open('rb') as handle: raw = handle.read(maximum + 1)
    assert len(raw) <= maximum
    return raw
