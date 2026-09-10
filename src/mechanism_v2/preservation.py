"""Read-only re-verification of FinalShot and immutable new preservation manifest."""
from __future__ import annotations

import json
from pathlib import Path
from .io import ROOT, DEVELOPMENT_INPUTS, git, sha256, write_json

MANIFEST = 'results/mechanism_v2/manifests/finalshot_preservation.json'
OLD_COMMIT = '98ffc02'


def verify_record(record):
    path = (ROOT / record['path']).resolve()
    if not path.is_relative_to(ROOT) or path.stat().st_size != record['bytes']:
        raise ValueError(f'Invalid artifact/size: {record["path"]}')
    if sha256(path) != record['sha256']:
        raise ValueError(f'Preserved artifact hash mismatch: {record["path"]}')


def preserve():
    existing = ROOT / MANIFEST
    if existing.exists():
        result = json.loads(existing.read_text(encoding='utf-8'))
        for record in result['artifacts']:
            verify_record(record)
        print(f'Preservation reverified: {len(result["artifacts"])} artifacts', flush=True)
        return result
    release_path = ROOT / 'results/finalshot/release_verification_manifest.json'
    release = json.loads(release_path.read_text(encoding='utf-8'))
    if len(release['artifacts']) != 238:
        raise ValueError('Unexpected old release inventory; investigate before proceeding')
    for record in release['artifacts']:
        verify_record(record)
    extras = [release_path, *(ROOT / p for p in DEVELOPMENT_INPUTS),
              ROOT / 'data/interim/finalshot_rbpnet_features.npy',
              ROOT / 'data/interim/finalshot_rbpnet_cache/progress_manifest.json',
              ROOT / 'data/interim/v4_phaseB_3utrbert_full_features.npy']
    artifacts = {r['path']: r for r in release['artifacts']}
    for path in extras:
        artifacts[path.relative_to(ROOT).as_posix()] = {
            'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': sha256(path),
        }
    for p, digest in DEVELOPMENT_INPUTS.items():
        if artifacts[p]['sha256'] != digest:
            raise ValueError(f'Development input changed: {p}')
    result = {
        'schema': 1, 'old_experiment_commit': git('rev-parse', OLD_COMMIT),
        'old_scientific_verdict': release['scientific_verdict'],
        'old_release_inventory_count': 238,
        'artifacts': sorted(artifacts.values(), key=lambda r: r['path']),
        'policy': 'Write-once hash inventory, anchored by Git. Not a filesystem write lock.',
        'scope': 'FinalShot release plus exact development inputs and reused representation matrices. '
                 'Large per-checkpoint caches remain covered by the archived reconstruction audit, '
                 'and must be rehashed individually before reuse.',
        'astrocyte_data_accessed': False, 'nzip_outcomes_accessed': False,
    }
    write_json(MANIFEST, result)
    print(f'FinalShot preserved: {len(artifacts)} artifacts; 238 original hashes passed', flush=True)
    return result
