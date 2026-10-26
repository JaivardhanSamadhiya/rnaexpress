"""Invented reserve contradictions; no actual OS/job or project-data call."""
import hashlib
import json
from pathlib import Path
import unittest
from .probe import failure,DURATION,DEADLINE


class Cases(unittest.TestCase):
    def test_lifetime_and_reserves_fail_closed(self):
        valid={'physical_available':512*2**20,'commit_headroom':1920*2**20,'disk_available':2**30}
        self.assertIsNone(failure(valid,0,startup=True))
        self.assertIsNone(failure(valid,DEADLINE))
        self.assertGreater(DEADLINE,DURATION)
        self.assertEqual(failure(valid,DEADLINE+.1),'1140-second total background diagnostic deadline')
        for key,bad in (('physical_available',256*2**20-1),('commit_headroom',2**30-1),('disk_available',2**30-1)):
            with self.subTest(key=key):self.assertIsNotNone(failure(dict(valid,**{key:bad}),1))
        self.assertIsNotNone(failure(dict(valid,physical_available=512*2**20-1),0,startup=True))


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    root=Path(__file__).resolve().parents[2];ns=Path(__file__).parent.name
    with (root/'results'/ns/'synthetic_tests_receipt.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump({'status':'PASS_INVENTED_LIFETIME_AND_RESERVE_CONTRADICTIONS','tests':result.testsRun,
            'sources':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in Path(__file__).parent.glob('*.py')},'actual_jobs_native_probes_payload_reads_or_fits':0},stream,indent=2,sort_keys=True)
        stream.write('\n')
