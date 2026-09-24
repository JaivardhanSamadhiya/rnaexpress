"""Synthetic cohort-integrity and weighting tests; no biological inputs."""
from .srle_aggregate_replay import MODELS, MEMBERS, calculate, read_groups, sha256, verify_integrity
from pathlib import Path
import csv
import json
import tempfile
import unittest


class AggregateReplayTests(unittest.TestCase):
    def test_equal_class_weight_with_unequal_neighborhood_counts(self):
        groups = {(c, rep, model, direction): (9 if c < 8 else 10, c / 100, .1)
                  for c in range(60) for rep in (1, 2) for model in MODELS
                  for direction in (-1, 1)}
        result = calculate(groups, [list(range(60))] * 2000)
        # Equal weighting of the 60 classes gives (0+.59)/2; counting parents
        # equally would give a different, larger value because small classes
        # deliberately contain lower scores.
        value = result['replicates']['1']['models']['kmer123']
        self.assertAlmostEqual(value['regret_gain_over_uniform'], .295)
        self.assertAlmostEqual(value['gain_ci'][0], .295)
        self.assertAlmostEqual(value['oriented_nrs_change'], .1)

    def test_changed_comparison_cohort_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'groups.csv'
            with path.open('w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['class_id', 'replicate', 'model', 'direction',
                                 'record_count', 'mean_regret_gain', 'mean_oriented_nrs_change'])
                for c in range(60):
                    for rep in (1, 2):
                        for model in MODELS:
                            for direction in (-1, 1):
                                count = 9 if c < 8 else 10
                                if (c, rep, model, direction) == (0, 1, 'kmer123', 1):
                                    count += 1
                                writer.writerow([c, rep, model, direction, count, .1, .1])
            with self.assertRaisesRegex(ValueError, 'different cohorts'):
                read_groups(path)

    def test_changed_package_data_fails_before_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in MEMBERS:
                (root / name).write_text('original')
            (root / 'integrity.json').write_text(json.dumps({
                'files': {name: sha256(root / name) for name in MEMBERS}}))
            verify_integrity(root)
            (root / 'group_metrics.csv').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                verify_integrity(root)


if __name__ == '__main__':
    unittest.main()
