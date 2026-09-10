"""Staged runner. Unimplemented/unauthorized stages fail instead of reporting success."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

# The package directory is isolated; never modify the archived runtime.
runtime=Path(__file__).resolve().parents[2]/'data/interim/mechanism_v2/runtime'
if runtime.exists():
    sys.path.insert(0,str(runtime))


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('stage', choices=['audit','resources','features','external_stability',
        'train','evaluate','controls','freeze','holdout','test','audit-probes','stability-reads','stability-recover','splits'])
    parser.add_argument('--limit',type=int)
    parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args()
    if args.stage=='audit':
        from .preservation import preserve
        preserve()
        from .forensics import run_forensics
        run_forensics()
    elif args.stage=='resources':
        from .resources import audit_resources
        audit_resources()
    elif args.stage=='audit-probes':
        from .preservation import preserve
        preserve()
        from .probes import run_probes
        run_probes()
    elif args.stage=='features':
        from .features import build_delta_caches,build_structure
        build_delta_caches()
        build_structure(args.limit,args.workers)
    elif args.stage=='external_stability':
        from .stability_resources import audit_stability
        audit_stability()
    elif args.stage=='stability-reads':
        from .stability_resources import fetch_recovery_reads
        fetch_recovery_reads()
    elif args.stage=='stability-recover':
        from .stability_recovery import discover_library
        discover_library(args.limit)
    elif args.stage=='splits':
        from .splits import build_splits
        build_splits()
    elif args.stage=='test':
        import pytest
        raise SystemExit(pytest.main(['-q','tests/mechanism_v2','--junitxml=results/mechanism_v2/tests.xml']))
    elif args.stage=='holdout':
        from .io import open_holdout
        open_holdout()
    else:
        raise SystemExit(f'{args.stage}: unavailable until preceding audits, tests and protocol are complete')


if __name__=='__main__':
    main()
