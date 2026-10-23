"""Invented-only fail-closed tests, retaining every original test/source byte."""
import ast
from datetime import datetime,timezone
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
from . import tests as invented
from . import writer as original
from .writer_v2 import Campaign
from .contracts import canonical_bytes,digest
from .spec import NS

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results'/NS


class FailClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=invented.plan_for()
    def new_run(self,temporary):return Campaign(Path(temporary)/'run',self.plan)
    def inner_keys(self,campaign):return [key for key,task in campaign.tasks.items() if task['phase']=='inner']
    def assert_no_later_callback(self,campaign,key,callback):
        self.assertTrue(campaign.failed)
        with self.assertRaises(AssertionError):campaign.write_checkpoint(key,callback)
        with self.assertRaises(AssertionError):campaign.finish()
        self.assertFalse(any(path.exists() for path in campaign.paths(key)))

    def test_partial_birth_write_poisons_before_another_key_can_start(self):
        with invented.LifecycleTests.run_directory(self) as temporary:
            campaign=self.new_run(temporary);first,second=self.inner_keys(campaign)[:2];events=[]
            real=original.write_new
            def partial(path,value):
                if str(path).endswith('.birth.json'):
                    with Path(path).open('xb') as stream:stream.write(b'{"partial":')
                    raise OSError('invented partial birth write')
                return real(path,value)
            with patch.object(original,'write_new',partial):
                with self.assertRaises(OSError):campaign.write_checkpoint(first,lambda *args:events.append('callback'))
            self.assertEqual(campaign.paths(first)[0].read_bytes(),b'{"partial":')
            self.assertEqual(events,[])
            self.assertEqual(original.read_object(campaign.directory/'campaign_failure_v2.json')['status'],'FAILED_V2_NO_RESUME')
            self.assert_no_later_callback(campaign,second,lambda *args:events.append('later'))
            self.assertEqual(events,[])

    def test_checkpoint_birth_fsync_failure_poisons_with_full_birth_preserved(self):
        with invented.LifecycleTests.run_directory(self) as temporary:
            campaign=self.new_run(temporary);first,second=self.inner_keys(campaign)[:2];events=[]
            real=original.os.fsync;calls=[]
            def fsync(fd):
                calls.append(fd)
                if len(calls)==1:raise OSError('invented birth fsync failure')
                return real(fd)
            with patch.object(original.os,'fsync',fsync):
                with self.assertRaises(OSError):campaign.write_checkpoint(first,lambda *args:events.append('callback'))
            self.assertEqual(original.read_object(campaign.paths(first)[0])['task_key'],first)
            self.assertFalse(campaign.paths(first)[1].exists());self.assertEqual(events,[])
            self.assert_no_later_callback(campaign,second,lambda *args:events.append('later'))
            self.assertEqual(events,[])

    def test_campaign_birth_mutation_stops_before_any_checkpoint_birth_or_callback(self):
        with invented.LifecycleTests.run_directory(self) as temporary:
            campaign=self.new_run(temporary);first,second=self.inner_keys(campaign)[:2];events=[]
            (campaign.directory/'campaign_birth.json').write_bytes(b'invented mutation')
            with self.assertRaises(AssertionError):campaign.write_checkpoint(first,lambda *args:events.append('callback'))
            self.assertFalse(any(path.exists() for path in campaign.paths(first)));self.assertEqual(events,[])
            self.assert_no_later_callback(campaign,second,lambda *args:events.append('later'))
            self.assertEqual(events,[])

    def test_failure_logging_error_preserves_original_exception_and_poison(self):
        with invented.LifecycleTests.run_directory(self) as temporary:
            campaign=self.new_run(temporary);first,second=self.inner_keys(campaign)[:2]
            real=original.write_new
            def failures(path,value):
                if str(path).endswith('.birth.json'):raise OSError('invented original write failure')
                if Path(path).name=='campaign_failure_v2.json':raise PermissionError('invented evidence failure')
                return real(path,value)
            with patch.object(original,'write_new',failures):
                with self.assertRaises(OSError) as caught:campaign.write_checkpoint(first,lambda *_:None)
            self.assertIn('invented original write failure',str(caught.exception))
            self.assertTrue(any('PermissionError' in note for note in caught.exception.__notes__))
            self.assert_no_later_callback(campaign,second,lambda *_:None)

    def test_invalid_outer_selection_and_unknown_key_poison_entire_run(self):
        for unknown in (False,True):
            with invented.LifecycleTests.run_directory(self) as temporary:
                campaign=self.new_run(temporary)
                key='unknown' if unknown else next(k for k,t in campaign.tasks.items() if t['phase']=='outer')
                with self.assertRaises((AssertionError,KeyError)):campaign.write_checkpoint(key,lambda *_:None,{} if not unknown else None)
                self.assertTrue(campaign.failed)
                self.assert_no_later_callback(campaign,self.inner_keys(campaign)[0],lambda *_:None)

    def test_original_callback_failure_retains_both_old_and_v2_evidence(self):
        with invented.LifecycleTests.run_directory(self) as temporary:
            campaign=self.new_run(temporary);first,second=self.inner_keys(campaign)[:2]
            def callback(*_):raise RuntimeError('invented optimizer callback failure')
            with self.assertRaises(RuntimeError):campaign.write_checkpoint(first,callback)
            self.assertTrue((campaign.directory/(first+'.failure.json')).exists())
            self.assertTrue((campaign.directory/'campaign_failure_v2.json').exists())
            self.assert_no_later_callback(campaign,second,lambda *_:None)

    def test_valid_full63_roster84_units_and_stored_outer_selection_still_complete(self):
        with invented.LifecycleTests.run_directory(self) as temporary:
            campaign=self.new_run(temporary);callback=invented.callback_for(campaign)
            for key,task in campaign.tasks.items():
                if task['phase']=='inner':campaign.write_checkpoint(key,callback)
            for key,task in campaign.tasks.items():
                if task['phase']=='outer':campaign.write_checkpoint(key,callback,invented.selection_for(campaign,task))
            complete=campaign.finish()
            self.assertEqual(complete['checkpoint_count'],63);self.assertEqual(complete['optimizer_units'],84)
            self.assertFalse(complete['independent_numeric_and_selection_replay_complete'])
            self.assertFalse((campaign.directory/'campaign_failure_v2.json').exists())


def run():
    forbidden=('numpy','pandas','scipy','torch','openvino','sklearn')
    assert not any(name in sys.modules for name in forbidden)
    started=time.monotonic();suite=unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(invented.PlanTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(invented.SourceTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(FailClosedTests))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful() and not any(name in sys.modules for name in forbidden)
    paths=sorted((ROOT/'src'/NS).glob('*.py'))
    for path in paths:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    receipt={'status':'PASS_INVENTED_FAIL_CLOSED_LIFECYCLE_V2_NOT_SCIENTIFIC_CAMPAIGN',
             'tests':result.testsRun,'elapsed_seconds':time.monotonic()-started,
             'generated_utc':datetime.now(timezone.utc).isoformat(),'scientific_imports':False,
             'project_metadata_reads':0,'project_feature_reads':0,'project_outcome_reads':0,'native_optimizer_calls':0,'models_fitted':0,
             'partial_birth_and_fsync_failures_stop_later_callbacks':True,
             'campaign_birth_checked_before_new_callbacks':True,
             'source_files':{path.relative_to(ROOT).as_posix():digest(path.read_bytes()) for path in paths}}
    path=OUT/'synthetic_tests_receipt_v2.json'
    with path.open('xb') as stream:stream.write(canonical_bytes(receipt))
    print('FAIL_CLOSED_LIFECYCLE_V2_PASS',result.testsRun,digest(path.read_bytes()),flush=True)


if __name__=='__main__':run()
