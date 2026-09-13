"""Mechanism-v4 entry point.

Stages:
  audit     report the committed design hash and data inventory, produce no score
  test      run tests/mechanism_v4 only; broad repository pytest is never used
  evaluate  the single scored pass over the pre-registered estimands
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
        from .evaluate import build_units
        design = io.load_design()
        units = build_units(design)
        print(json.dumps({
            'protocol': design['protocol'],
            'design_sha256': io.design_sha256(),
            'committed_before_scoring': design['committed_before_scoring'],
            'primary_source': design['primary_source'],
            'unique_sequences': int(len(units)),
            'components': int(units.component.nunique()),
            'genes': int(units.gene.nunique()),
            'positive_rate': round(float(units.label.mean()), 4),
            'frozen_folds': sorted(int(f) for f in units.fold.unique()),
            'holdout': 'sealed',
        }, indent=2))
    elif args.stage == 'test':
        import pytest
        raise SystemExit(pytest.main(
            ['-q', 'tests/mechanism_v4', '--junitxml=results/mechanism_v4/tests.xml']))
    elif args.stage == 'evaluate':
        from .evaluate import main as evaluate_main
        result = evaluate_main()
        print(json.dumps({'outcome': result['outcome'], 'gates': result['gates']}, indent=2))
    elif args.stage == 'holdout':
        from .io import open_holdout
        open_holdout()


if __name__ == '__main__':
    main()
