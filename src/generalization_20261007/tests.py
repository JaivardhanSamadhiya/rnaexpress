"""Explicit safe test roster; never discover the repository test tree."""
from .common import *
import unittest, io

def run():
    names=['test_scaling','test_representation','test_mechanism','test_coverage','test_endpoint']
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName('src.'+NS+'.'+n) for n in names)
    output=io.StringIO();result=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
    assert result.wasSuccessful(),output.getvalue()
    print(output.getvalue(),flush=True)
    # Runtime-bearing log is not an immutable input; receipt records the exact source roster.
    jsave(OUT/'tests_receipt_final.json',{'status':'PASS','tests':result.testsRun,'modules':names,
        'code_hashes':{n:sha256(SRC/(n+'.py')) for n in names},'unfiltered_pytest':False})

if __name__=='__main__':run()
