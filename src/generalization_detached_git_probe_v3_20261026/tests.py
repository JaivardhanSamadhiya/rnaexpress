"""Invented variable-length buffer tests; no native calls or project data."""
import ctypes as C
from types import SimpleNamespace as Obj
import unittest
from .probe import roster,headless


class Cases(unittest.TestCase):
    def job(self,assigned=1,listed=1,length=None):
        def query(handle,kind,output,size,returned):
            assert handle==7 and kind==3
            value=output._obj;value.assigned=assigned;value.listed=listed
            for index in range(min(listed,16)):value.pids[index]=101+index
            returned._obj.value=8+listed*C.sizeof(headless.original.SIZE_T) if length is None else length
            return True
        return Obj(handle=7,_open=lambda:None,_api=Obj(QueryInformationJobObject=query))
    def test_short_valid_return_length_is_not_buffer_capacity(self):self.assertEqual(roster(self.job()),[101])
    def test_two_identifiers(self):self.assertEqual(roster(self.job(2,2)),[101,102])
    def test_truncated_roster_refused(self):
        with self.assertRaises(AssertionError):roster(self.job(2,1))
    def test_short_bytes_refused(self):
        with self.assertRaises(AssertionError):roster(self.job(length=8))
    def test_oversized_roster_refused(self):
        with self.assertRaises(AssertionError):roster(self.job(17,17))


if __name__=='__main__':unittest.main(verbosity=2)
