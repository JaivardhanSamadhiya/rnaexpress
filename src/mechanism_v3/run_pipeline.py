"""Staged runner for Mechanism-v3. Holdout remains sealed."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

runtime = Path(__file__).resolve().parents[2] / 'data/interim/mechanism_v2/runtime'
if runtime.exists():
    sys.path.insert(0, str(runtime))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('stage', choices=['audit', 'evaluate', 'test', 'holdout', 'report'])
    args = parser.parse_args()
    if args.stage == 'audit':
        import json
        from .grammar import load_grammar
        design = load_grammar()
        print(json.dumps({
            'elements': len(design['elements']),
            'config_sha256': design['config_sha256'],
            'split_manifest': design['split_manifest'],
            'learned_from_localization_effect': False,
            'mechanism_v2_verdict': 'NO-GO preserved',
        }, indent=2), flush=True)
    elif args.stage == 'evaluate':
        from .evaluate import evaluate
        evaluate()
    elif args.stage == 'test':
        import pytest
        raise SystemExit(pytest.main(['-q', 'tests/mechanism_v3',
                                      '--junitxml=results/mechanism_v3/tests.xml']))
    elif args.stage == 'report':
        from .report import write_status_report
        write_status_report()
    elif args.stage == 'holdout':
        from .io import open_holdout
        open_holdout()
    else:
        raise SystemExit(f'Unknown stage: {args.stage}')


if __name__ == '__main__':
    main()
