"""Outcome-free feature caches used only by prospectively specified controls.

Nothing here reads a localization outcome, a split outcome column or any sealed
resource. Two artifacts are produced:

* matched absolute pooled-BERT allele blocks, so the N6 absolute comparator has
  exactly the same 540 columns as M1 rather than an arbitrary subset;
* the N7 broken-reference cache, in which a donor intervention's REFERENCE
  profile is pooled at the RECIPIENT's edit window. Pooling a donor reference at
  the donor's own unrelated window would make the null trivially different for
  reasons that have nothing to do with reference pairing, so it is not done.

Donor assignment is a true bijection over unique interventions, computed
separately inside every train/evaluation partition of the development protocol,
stratified by source x native sequence length x edit band with a cross-component
derangement requested. Equal native length is what makes recipient-window
pooling well defined; it is asserted, not assumed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .features import array_file
from .io import ROOT, canonical_json, load_development, output_path, sha256, write_json

BERT_SOURCE = 'data/interim/v4_phaseB_3utrbert_full_features.npy'
BERT_SOURCE_SHA256 = '51912767e74dc19a06dadf6bab9f3022f11939f1cc537f024af148cc18f948d9'
BROKEN_STRATA = ('dataset', 'native_length', 'edit_band')
BROKEN_SEED = 20260909
BERT_ABSOLUTE_MANIFEST = 'results/mechanism_v2/features/bert_pooled_absolute_manifest.json'
BROKEN_MANIFEST = 'results/mechanism_v2/features/broken_reference_manifest.json'


def build_bert_absolute_blocks():
    """Split the archived pooled allele embedding into its two absolute halves."""
    path = ROOT / BERT_SOURCE
    if sha256(path) != BERT_SOURCE_SHA256:
        raise ValueError('BERT source array hash mismatch')
    values = np.load(path, mmap_mode='r')
    if values.shape[1] != 384:
        raise ValueError('Unexpected pooled BERT schema')
    reference = np.asarray(values[:, :128])
    mutant = np.asarray(values[:, 128:256])
    delta_record = json.loads((ROOT / 'results/mechanism_v2/features/bert_pooled_allele_delta_manifest.json').read_text())
    delta = np.load(ROOT / delta_record['path'], mmap_mode='r')
    if sha256(ROOT / delta_record['path']) != delta_record['sha256']:
        raise ValueError('Pooled BERT delta array changed')
    if not np.array_equal(mutant - reference, np.asarray(delta)):
        raise ValueError('Absolute halves do not reproduce the frozen pooled delta')
    record = {
        'reference': array_file('data/interim/mechanism_v2/bert_pooled_reference_absolute.npy', reference),
        'mutant': array_file('data/interim/mechanism_v2/bert_pooled_mutant_absolute.npy', mutant),
        'source_sha256': BERT_SOURCE_SHA256, 'source_columns': {'reference': [0, 128], 'mutant': [128, 256]},
        'code_sha256': sha256(Path(__file__)),
        'reproduces_frozen_delta': True,
        'interpretation': 'absolute pooled allele embeddings; N6/N7 comparators only, never a primary block',
    }
    write_json(BERT_ABSOLUTE_MANIFEST, record)
    print(f'Absolute pooled BERT allele blocks verified: {reference.shape}', flush=True)
    return record


def intervention_windows():
    """Edit window and parent sequence identity per intervention, outcome-free."""
    rows = load_development('results/v4_phaseB/model_interventions.csv.gz')
    if not np.array_equal(rows.feature_row, np.arange(len(rows))):
        raise ValueError('Intervention indices not contiguous')
    sequences = sorted(set(rows.parent_sequence) | set(rows.mutant_sequence),
                       key=lambda s: hashlib.sha256(s.encode()).hexdigest())
    lookup = {s: i for i, s in enumerate(sequences)}
    lengths = np.array([len(s) for s in sequences], int)
    parent = np.array([lookup[s] for s in rows.parent_sequence], int)
    starts, ends = [], []
    for a, b in zip(rows.parent_sequence, rows.mutant_sequence):
        if len(a) != len(b):
            raise ValueError('Archived RBP profiles require the equal-length pair convention')
        changed = np.flatnonzero(np.frombuffer(a.encode(), np.uint8) != np.frombuffer(b.encode(), np.uint8))
        if not len(changed):
            raise ValueError('No mutation in intervention')
        starts.append(changed.min())
        ends.append(changed.max() + 1)
    return {'sequences': sequences, 'lengths': lengths, 'parent_index': parent,
            'starts': np.array(starts, int), 'ends': np.array(ends, int),
            'native_length': np.array([len(s) for s in rows.parent_sequence], int)}


def broken_reference_plan(store, seed=BROKEN_SEED):
    """Donor feature rows for N7, one bijection per protocol partition."""
    from .control_kernels import intervention_permutation
    from .fitting import development_partitions
    plan = {}
    audits = {}
    for label, (train, held) in sorted(development_partitions(store).items()):
        idx = np.concatenate([train, held])
        subset = store.rows.iloc[idx]
        role = np.where(np.arange(len(idx)) < len(train), 'train', 'evaluation')
        donor, eligible, audit = intervention_permutation(
            subset, role, strata=BROKEN_STRATA, seed=seed, cross_component=True)
        plan[label] = {'rows': idx, 'donor_feature_row': donor, 'eligible': eligible}
        audits[label] = {k: v for k, v in audit.items() if k != 'stratum_audit'}
        audits[label]['ineligible_strata'] = sorted(
            {a['reason'] for a in audit['stratum_audit'] if a['reason']})
        audits[label]['strata_total'] = len(audit['stratum_audit'])
        audits[label]['strata_eligible'] = int(sum(a['eligible'] for a in audit['stratum_audit']))
    return plan, audits


def build_broken_reference_cache(store=None, seed=BROKEN_SEED):
    """Pool each donor reference profile at the recipient edit window, once."""
    from .feature_store import FeatureStore
    from .preservation import preserve
    from .allele_summaries import decoded_sequence_hashes, pooled_features
    preserve()
    store = store or FeatureStore()
    windows = intervention_windows()
    plan, audits = broken_reference_plan(store, seed)
    feature_rows = store.feature_rows
    requests = []
    for label in sorted(plan):
        entry = plan[label]
        donor = np.asarray(entry['donor_feature_row'], int)
        recipient = feature_rows[entry['rows']]
        keep = np.asarray(entry['eligible'], bool)
        if donor.shape != recipient.shape or keep.shape != recipient.shape:
            raise ValueError('Donor plan is not aligned to its partition rows')
        requests.append(np.column_stack([donor[keep], recipient[keep]]))
    stacked = np.vstack(requests)
    pairs = np.unique(stacked, axis=0)
    donor_parent = windows['parent_index'][pairs[:, 0]]
    starts = windows['starts'][pairs[:, 1]]
    ends = windows['ends'][pairs[:, 1]]
    if not np.array_equal(windows['native_length'][pairs[:, 0]], windows['native_length'][pairs[:, 1]]):
        raise ValueError('Donor and recipient native lengths differ; recipient-window pooling undefined')
    signature_path = ROOT / 'results/finalshot/rbp_signature_manifest.json'
    manifest = json.loads(signature_path.read_text())
    entries = {e['task']: e for e in manifest['checkpoint_caches']}
    absolute = json.loads((ROOT / 'results/mechanism_v2/features/rbp_absolute_allele_manifest.json').read_text())
    tasks = absolute['task_order']
    if len(entries) != 103 or set(tasks) != set(entries):
        raise ValueError('RBP channel inventory mismatch')
    hashes = np.array([hashlib.sha256(s.encode()).hexdigest() for s in windows['sequences']])
    array_path = output_path('data/interim/mechanism_v2/broken_reference_rbp_pooled.npy')
    array_path.parent.mkdir(parents=True, exist_ok=True)
    if array_path.exists():
        array_path.unlink()
    pooled = np.lib.format.open_memmap(array_path, mode='w+', dtype=np.float32,
                                       shape=(len(pairs), 4 * len(tasks)))
    for ordinal, task in enumerate(tasks):
        entry = entries[task]
        path = (ROOT / entry['profile_file']).resolve()
        if path.parent != (ROOT / 'data/interim/finalshot_rbpnet_cache/profiles').resolve():
            raise PermissionError('Unexpected archived profile path')
        if sha256(path) != entry['profile_sha256']:
            raise ValueError(f'Archived profile hash mismatch: {task}')
        with np.load(path, allow_pickle=False) as data:
            if not np.array_equal(decoded_sequence_hashes(data['sequence_sha256']), hashes) \
                    or not np.array_equal(data['lengths'], windows['lengths']):
                raise ValueError('Profile sequence order/length changed')
            pooled[:, ordinal * 4:ordinal * 4 + 4] = pooled_features(
                data['target_profile'], data['mixing'], donor_parent, starts, ends, windows['lengths'])
        print(f'Broken-reference pooling {ordinal + 1}/103 complete: {task}', flush=True)
    pooled.flush()
    del pooled
    index = pd.DataFrame({'donor_feature_row': pairs[:, 0], 'recipient_feature_row': pairs[:, 1]})
    index_path = 'data/interim/mechanism_v2/broken_reference_index.csv'
    output_path(index_path).parent.mkdir(parents=True, exist_ok=True)
    index.to_csv(ROOT / index_path, index=False, lineterminator='\n')
    record = {
        'pooled': {'path': 'data/interim/mechanism_v2/broken_reference_rbp_pooled.npy',
                   'shape': [int(len(pairs)), 4 * len(tasks)], 'dtype': 'float32',
                   'sha256': sha256(array_path)},
        'index': {'path': index_path, 'rows': int(len(pairs)), 'sha256': sha256(ROOT / index_path)},
        'task_order': tasks, 'strata': list(BROKEN_STRATA), 'seed': int(seed),
        'cross_component_derangement_requested': True,
        'partition_audits': audits,
        'code_sha256': sha256(Path(__file__)),
        'source_signature_manifest_sha256': sha256(signature_path),
        'definition': "donor intervention REFERENCE profile pooled at the RECIPIENT's edit window; "
                      'radii 10/25/50 mass plus the mixing coefficient, identical pooling code as the primary block',
        'interpretation': 'pairing perturbation for necessity testing, not a biologically plausible alternative model',
        'outcomes_used': False,
    }
    write_json(BROKEN_MANIFEST, record)
    print(f'Broken-reference cache complete: {len(pairs)} unique donor/recipient pooling pairs', flush=True)
    return record


def broken_reference_lookup():
    record = json.loads((ROOT / BROKEN_MANIFEST).read_text())
    path = ROOT / record['pooled']['path']
    if sha256(path) != record['pooled']['sha256']:
        raise ValueError('Broken-reference pooled cache hash mismatch')
    index = pd.read_csv(ROOT / record['index']['path'])
    if sha256(ROOT / record['index']['path']) != record['index']['sha256']:
        raise ValueError('Broken-reference index hash mismatch')
    values = np.load(path, mmap_mode='r', allow_pickle=False)
    if list(values.shape) != record['pooled']['shape']:
        raise ValueError('Broken-reference cache shape mismatch')
    key = {(int(a), int(b)): i for i, (a, b) in
           enumerate(zip(index.donor_feature_row, index.recipient_feature_row))}
    return values, key, record


def build_control_features():
    build_bert_absolute_blocks()
    return build_broken_reference_cache()


if __name__ == '__main__':  # pragma: no cover
    from . import run_pipeline  # noqa: F401  initialize the isolated runtime first
    build_control_features()
