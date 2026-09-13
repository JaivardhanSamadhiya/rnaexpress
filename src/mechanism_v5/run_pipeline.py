"""Mechanism-v5 entry point.

Stages:
  audit     committed design hash and arm inventory; produces no score
  test      runs tests/mechanism_v5 only; broad repository pytest is never used
  evaluate  the single scored pass over both pre-registered arms
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The archived Mechanism-v2 runtime is read-only and shared; never modify it.
runtime = Path(__file__).resolve().parents[2] / 'data/interim/mechanism_v2/runtime'
if runtime.exists():
    sys.path.insert(0, str(runtime))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('stage', choices=['audit', 'test', 'evaluate', 'holdout'])
    args = parser.parse_args()

    if args.stage == 'audit':
        from . import io
        from .evaluate import _sequence_table, confident
        design = io.load_design()
        rows = io.load_development(design['data']['table'])
        mikl = _sequence_table(rows, 'mikl_gse173098')
        moffatt = _sequence_table(rows, 'moffatt_gse334718')
        conf = confident(mikl)
        print(json.dumps({
            'protocol': design['protocol'],
            'design_sha256': io.design_sha256(),
            'committed_before_scoring': design['committed_before_scoring'],
            'arm_a_rows': int(len(conf)),
            'arm_a_genes': int(conf.gene.nunique()),
            'arm_a_positive_rate': round(float(conf.label.mean()), 4),
            'arm_a_genes_per_fold': {str(k): int(v) for k, v in
                                     conf.groupby('fold').gene.nunique().items()},
            'arm_b_train_rows': int(len(moffatt)),
            'holdout': 'sealed',
        }, indent=2))
    elif args.stage == 'test':
        import pytest
        raise SystemExit(pytest.main(
            ['-q', 'tests/mechanism_v5', '--junitxml=results/mechanism_v5/tests.xml']))
    elif args.stage == 'evaluate':
        from .evaluate import main as evaluate_main
        result = evaluate_main()
        print(json.dumps({'outcome': result['outcome'], 'gates': result['gates']}, indent=2))
    elif args.stage == 'holdout':
        from .io import open_holdout
        open_holdout()


if __name__ == '__main__':
    main()
