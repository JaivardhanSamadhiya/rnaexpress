"""Invented resource/owned-process and immutable-write fault cases only."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from .common import *
from .supervise import monitor


def good():
    return {'physical_available': 3*2**30, 'disk_available': 2**30, 'commit_headroom': 2**30}


class Job:
    def __init__(self):
        self.stopped = False
    def accounting(self):
        return {'active_processes': 1}
    def terminate(self):
        self.stopped = True


class Child:
    def __init__(self, codes):
        self.codes = iter(codes)
    def exit_code(self):
        return next(self.codes)
    def memory(self):
        return {'peak_working_set': 123, 'peak_private_commit': 100}


class Cases(unittest.TestCase):
    def test_original_floor_rejects_one_byte_short(self):
        state = good(); state['physical_available'] -= 1
        self.assertIn('three-GiB', resource_failure(state, 0))
        self.assertIsNone(resource_failure(good(), 0))

    def test_disk_commit_and_deadline(self):
        for field in ('disk_available', 'commit_headroom'):
            state = good(); state[field] -= 1
            self.assertIsNotNone(resource_failure(state, 0))
        self.assertIsNone(resource_failure(good(), 300))
        self.assertIsNotNone(resource_failure(good(), 300.001))
        self.assertIsNotNone(resource_failure(good(), 0, 3))

    def test_monitor_kills_running_owned_child_when_floor_drops(self):
        job = Job(); times = iter([0., 0., .1])
        states = iter([good(), {**good(), 'physical_available': 3*2**30-1}])
        result = monitor(job, Child([None, None]), lambda: next(states), lambda: next(times), lambda _: None)
        self.assertTrue(job.stopped)
        self.assertIsNone(result['exit_code'])
        self.assertEqual(result['minimum_physical'], 3*2**30-1)

    def test_finished_child_does_not_hide_a_simultaneous_floor_failure(self):
        job = Job(); state = {**good(), 'commit_headroom': 2**30-1}
        result = monitor(job, Child([0]), lambda: state, lambda: 0., lambda _: self.fail('Unexpected wait'))
        self.assertTrue(job.stopped)
        self.assertIsNotNone(result['failure'])

    def test_success_preserves_exit_and_memory(self):
        job = Job(); times = iter([0., 0., .1])
        result = monitor(job, Child([None, 0]), good, lambda: next(times), lambda _: None)
        self.assertFalse(job.stopped)
        self.assertIsNone(result['failure'])
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['peak_working_set'], 123)

    def test_exclusive_save_cannot_replace_prior_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'receipt.json'
            original = save_new(path, {'invented': 1})
            with self.assertRaises(FileExistsError):
                save_new(path, {'invented': 2})
            self.assertEqual(sha(path.read_bytes()), original)

    def test_fsync_failure_preserves_partial_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'receipt.json'
            with patch('os.fsync', side_effect=OSError('Invented fsync error')):
                with self.assertRaises(OSError):
                    save_new(path, {'invented': 1})
            self.assertTrue(path.exists())
            with self.assertRaises(FileExistsError):
                save_new(path, {'invented': 2})


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Cases)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    sources = sorted((ROOT/'src'/NS).glob('*.py'))
    save_new(OUT/'synthetic_tests_receipt_reviewed.json', {
        'status': 'PASS_INVENTED_METADATA_EXECUTION_CONTROL_CHECKS',
        'tests_run': result.testsRun, 'sources': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sources},
        'project_payloads_read': 0, 'native_optimizer_calls': 0, 'model_fits': 0,
        'scientific_imports': False, 'actual_owned_job_started': False})


if __name__ == '__main__':
    run()
