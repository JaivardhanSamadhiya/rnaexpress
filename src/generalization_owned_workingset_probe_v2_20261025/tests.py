"""Invented ownership/ordering/fail-closed tests; no OS handles or payloads."""
from pathlib import Path
import hashlib
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from . import working_set as w


class Cases(unittest.TestCase):
    def setup_objects(self):
        events=[]
        job=SimpleNamespace(_verify_limits=lambda:events.append('limits'),
            _membership=lambda h:events.append('membership'))
        child=SimpleNamespace(_owner=job,_resumed=False,process_handle=object())
        backend=SimpleNamespace(current={'minimum':204800,'maximum':1413120,'flags':0})
        def query(_):events.append('query');return dict(backend.current)
        def install(handle,minimum,maximum,flags):
            events.append('set');backend.current={'minimum':minimum,'maximum':maximum,'flags':flags}
        backend.query=query;backend.install=install
        return job,child,backend,events

    def test_only_suspended_owned_child_and_unchanged_job_are_required_before_API(self):
        for kind in ('foreign','resumed','closed','limits'):
            job,child,backend,events=self.setup_objects()
            if kind=='foreign':child._owner=object()
            if kind=='resumed':child._resumed=True
            if kind=='closed':child.process_handle=None
            if kind=='limits':job._verify_limits=lambda:(_ for _ in ()).throw(AssertionError('changed original limits'))
            with self.subTest(kind=kind),patch.object(w,'native',return_value=backend),self.assertRaises(AssertionError):
                w.apply(job,child)
            self.assertNotIn('query',events)
            self.assertNotIn('set',events)

    def test_exact_additional_cap_preserves_minimum_and_flags_and_verifies_after_set(self):
        for flags in (0,1,2,8,9,10):
            job,child,backend,events=self.setup_objects();backend.current['flags']=flags
            with self.subTest(flags=flags),patch.object(w,'native',return_value=backend):
                receipt=w.apply(job,child)
                self.assertEqual(receipt['after'],{'minimum':204800,'maximum':190*2**20,'flags':(flags&3)|4})
                self.assertEqual(events,['limits','membership','query','set','query','limits','membership'])
                self.assertTrue(w.verify(job,child,receipt))

    def test_set_failure_has_no_fallback_or_success(self):
        job,child,backend,events=self.setup_objects()
        def fail(*_):raise OSError('invented denied set')
        backend.install=fail
        with patch.object(w,'native',return_value=backend),self.assertRaisesRegex(OSError,'denied set'):
            w.apply(job,child)
        self.assertEqual(events,['limits','membership','query'])

    def test_changed_readback_or_later_limit_is_rejected(self):
        job,child,backend,events=self.setup_objects()
        backend.install=lambda *_:None
        with patch.object(w,'native',return_value=backend),self.assertRaises(AssertionError):w.apply(job,child)
        job,child,backend,events=self.setup_objects()
        with patch.object(w,'native',return_value=backend):
            receipt=w.apply(job,child);backend.current['maximum']+=4096
            with self.assertRaises(AssertionError):w.verify(job,child,receipt)

    def test_unknown_flags_or_minimum_above_cap_fail_before_set(self):
        for key,value in (('flags',16),('flags',3),('minimum',w.MAXIMUM+1)):
            job,child,backend,events=self.setup_objects();backend.current[key]=value
            with self.subTest(key=key,value=value),patch.object(w,'native',return_value=backend),self.assertRaises(AssertionError):
                w.apply(job,child)
            self.assertNotIn('set',events)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    root=Path(__file__).resolve().parents[2];ns=Path(__file__).parent.name
    out=root/'results'/ns/'synthetic_tests_receipt.json'
    with out.open('x',encoding='utf8',newline='\n') as stream:
        json.dump({'status':'PASS_INVENTED_OWNED_WORKINGSET_CAP_HELPER','tests':result.testsRun,
            'sources':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},
            'native_calls_jobs_project_payload_reads_or_fits':0},stream,sort_keys=True,indent=2)
        stream.write('\n')
