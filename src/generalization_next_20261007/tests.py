"""Explicit synthetic test roster; no repository discovery or pytest dependency."""
from .common import *
import importlib, inspect, unittest

MODULES = ['test_common', 'test_structure', 'test_structure_cache', 'test_bert']

def run():
    suite = unittest.TestSuite()
    for name in MODULES:
        module = importlib.import_module('src.'+NS+'.'+name)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
        for label, function in inspect.getmembers(module, inspect.isfunction):
            if label.startswith('test_') and function.__module__ == module.__name__:
                suite.addTest(unittest.FunctionTestCase(function))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    print(stream.getvalue(), flush=True)
    assert result.wasSuccessful(), 'Scoped synthetic test failure'
    jsave(OUT/'tests_receipt.json', {'status':'PASS', 'tests':result.testsRun, 'modules':MODULES,
        'code_hashes':{name:sha256(SRC/(name+'.py')) for name in MODULES},
        'unfiltered_pytest':False, 'runner':'stdlib unittest; bundled Python lacks pytest',
        'research_outcomes_used':False})

if __name__ == '__main__': run()
