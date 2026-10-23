"""Invented source identity, startup rejection and live-handle peak checks."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from . import common as c
from . import supervise as s


class Cases(unittest.TestCase):
    def test_child_command_carries_fixed_expected_manifest_and_cache_prefix(self):
        command = s.worker_command('a'*64)
        self.assertIn('pycache_prefix='+str(c.CACHE_PREFIX), command)
        self.assertEqual(command[-2:], ['--manifest-sha','a'*64])
        self.assertIn('-S', command); self.assertIn('-B', command)
        with self.assertRaises(AssertionError):
            s.worker_command('not-a-hash')

    def test_source_mode_rejects_cache_creation_and_wrong_prefix(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'must_stay_absent'
            with patch.object(c,'CACHE_PREFIX',target), patch.object(c.sys,'flags',SimpleNamespace(no_site=1)), \
                 patch.object(c.sys,'dont_write_bytecode',True), patch.object(c.sys,'pycache_prefix',str(target)):
                self.assertTrue(c.source_mode()['cache_prefix_absent'])
                target.mkdir()
                with self.assertRaisesRegex(AssertionError,'must remain absent'):
                    c.source_mode()
            with patch.object(c,'CACHE_PREFIX',target), patch.object(c.sys,'flags',SimpleNamespace(no_site=1)), \
                 patch.object(c.sys,'dont_write_bytecode',True), patch.object(c.sys,'pycache_prefix','wrong'):
                with self.assertRaisesRegex(AssertionError,'exact -X'):
                    c.source_mode()

    def test_changed_manifest_cannot_redefine_expected_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'manifest.json'
            original = b'{"invented": 1}\n'
            target.write_bytes(original)
            expected = c.sha(original)
            target.write_bytes(b'{"invented": 2}\n')
            with patch.object(c,'MANIFEST',target), patch.object(c,'source_mode',return_value={}):
                with self.assertRaisesRegex(AssertionError,'initially committed bytes'):
                    c.verify_sources(expected)

    def test_startup_floor_blocks_before_job_or_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            state = {'physical_available':3*2**30-1,'disk_available':2**30,'commit_headroom':2**30}
            job = Mock(side_effect=AssertionError('No job before original floor'))
            with patch.object(s,'admitted',return_value=({},'b'*64)), patch.object(s,'OUT',out), \
                 patch.object(s,'verify_sources',return_value={}), patch.object(s,'source_mode',return_value={'invented':True}), \
                 patch.object(s.headless,'memory',return_value=state), patch.object(s.headless,'Job',job):
                s.run(root_start=True)
            record = c.read_json((out/'supervisor_receipt.json').read_bytes())
            self.assertFalse(record['worker_started'])
            self.assertEqual(record['project_payloads_opened'],0)
            self.assertEqual(record['initial_committed_execution_manifest_sha256'],'b'*64)
            job.assert_not_called()

    def test_explicit_root_start_required_before_admission(self):
        admission = Mock(side_effect=AssertionError('No admission'))
        with patch.object(s,'admitted',admission):
            with self.assertRaisesRegex(AssertionError,'root-start'):
                s.run()
        admission.assert_not_called()

    def test_final_lifetime_peak_is_sampled_and_cannot_reduce_prior_peak(self):
        record = {'peak_working_set':100,'peak_private_commit':50}
        s.final_peak(record,lambda:{'peak_working_set':90,'peak_private_commit':60})
        self.assertEqual(record['peak_working_set'],100)
        self.assertEqual(record['peak_private_commit'],60)
        with self.assertRaisesRegex(AssertionError,'Unavailable'):
            s.final_peak({},lambda:{'peak_working_set':0,'peak_private_commit':0})


def run():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    assert result.wasSuccessful()
    sources = sorted((c.ROOT/'src'/c.NS).glob('*.py'))
    c.save_new(c.OUT/'synthetic_tests_receipt.json', {
        'status':'PASS_INVENTED_SOURCE_BOUND_METADATA_V2_CONTROL_CHECKS',
        'UTC':datetime.now(timezone.utc).isoformat(),'tests':result.testsRun,
        'sources':{p.relative_to(c.ROOT).as_posix():c.sha(p.read_bytes()) for p in sources},
        'actual_worker_or_job_started':False,'scientific_imports':False,
        'project_payloads_read':0,'model_fits':0})


if __name__=='__main__':run()
