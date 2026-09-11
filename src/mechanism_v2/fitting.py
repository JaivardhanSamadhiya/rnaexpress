"""Shared, resumable, boundary-checked fitting for outer, control and transfer work.

Nothing in this module selects a recipe, chooses a threshold or interprets a
score. Every fit records the exact partition identity, the feature-provenance
digest and artifact hashes, so a replay either reproduces the identical record
or fails loudly. Row identities are stored as counts plus a canonical SHA-256
of the ordered row list: the same immutable identity check as the inner runner,
without writing hundreds of megabytes of repeated index lists.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

from .features import array_file
from .io import ROOT, canonical_json, sha256, write_json
from .ranking import PairedRanker, RankConfig

FIT_ROOT = 'data/interim/mechanism_v2/fits'
MODEL_ROOT = 'models/mechanism_v2/fits'
PREDICTION_ROOT = 'data/interim/mechanism_v2/fit_predictions'


def row_identity(indices):
    idx = np.asarray(indices, int)
    if idx.ndim != 1 or not idx.size:
        raise ValueError('Row identity requires a nonempty one-dimensional index')
    return {'count': int(idx.size),
            'sha256': hashlib.sha256(canonical_json([int(v) for v in idx])).hexdigest()}


def partition_audit(rows, train_idx, eval_idx, *, purge_groups=True):
    """Verify a train/evaluation boundary before any model sees the evaluation rows."""
    train = np.asarray(train_idx, int)
    held = np.asarray(eval_idx, int)
    if not train.size or not held.size:
        raise ValueError('Empty partition')
    for name, idx in (('train', train), ('evaluation', held)):
        if idx.ndim != 1 or idx.min() < 0 or idx.max() >= len(rows):
            raise ValueError(f'{name} row index outside the certified inventory')
        if len(set(idx.tolist())) != idx.size:
            raise ValueError(f'Duplicate {name} row index')
    if np.intersect1d(train, held).size:
        raise ValueError('Train/evaluation row overlap')
    left = rows.iloc[train]
    right = rows.iloc[held]
    shared_components = sorted(set(left.component.astype(str)) & set(right.component.astype(str)))
    shared_interventions = sorted(int(v) for v in set(left.feature_row) & set(right.feature_row))
    if purge_groups and (shared_components or shared_interventions):
        raise PermissionError('Connected component or intervention leakage across the evaluation boundary')
    return {'train': row_identity(train), 'evaluation': row_identity(held),
            'train_components': int(left.component.nunique()),
            'evaluation_components': int(right.component.nunique()),
            'evaluation_decisions': int(right.decision_set_id.nunique()),
            'shared_components': shared_components,
            'shared_interventions': shared_interventions,
            'group_purged': bool(purge_groups)}


def assert_outer_boundary(rows, outer, train_idx, eval_idx):
    """The outer test partition is exactly one fold and never reaches training."""
    train = np.asarray(train_idx, int)
    held = np.asarray(eval_idx, int)
    fold = rows.outer_fold.to_numpy()
    if np.any(fold[train] == outer):
        raise PermissionError('Outer test fold rows reached outer training')
    if not np.all(fold[held] == outer):
        raise PermissionError('Outer evaluation partition contains rows from another fold')
    expected = np.flatnonzero(fold == outer)
    if not np.array_equal(np.sort(held), expected):
        raise PermissionError('Outer evaluation must score the whole untouched fold exactly once')
    if not np.array_equal(np.sort(train), np.flatnonzero(fold != outer)):
        raise PermissionError('Outer training must use the whole remaining development partition')
    return partition_audit(rows, train, held)


def checked_fit_record(path, identity):
    record = json.loads(path.read_text())
    if record['identity'] != identity:
        raise ValueError(f'Fit identity mismatch; refusing to overwrite evidence: {path}')
    for field in ('model', 'predictions'):
        if sha256(ROOT / record[field]['path']) != record[field]['sha256']:
            raise ValueError(f'Fit artifact hash mismatch: {record[field]["path"]}')
    value = np.load(ROOT / record['predictions']['path'], allow_pickle=False)
    if value.ndim != 2 or value.shape[1] != 2 or not np.isfinite(value).all():
        raise ValueError('Invalid cached predictions')
    if row_identity(value[:, 0].astype(int)) != identity['partition']['evaluation']:
        raise ValueError('Prediction row identity mismatch')
    PairedRanker.from_record(json.loads((ROOT / record['model']['path']).read_text()))
    return record, value[:, 1]


def run_fit(label, identity, x, columns, config, frame, train_idx, eval_idx, *,
            fit_root=FIT_ROOT, model_root=MODEL_ROOT, prediction_root=PREDICTION_ROOT):
    """Fit on train rows only, score the held rows once, and record everything."""
    train = np.asarray(train_idx, int)
    held = np.asarray(eval_idx, int)
    path = ROOT / f'{fit_root}/{label}.json'
    if path.exists():
        return checked_fit_record(path, identity)
    if len(frame) != train.size:
        raise ValueError('Training frame must correspond to the training rows')
    model = PairedRanker(RankConfig(**config)).fit(x[train], frame, columns)
    prediction = model.predict(x[held])
    restored = PairedRanker.from_record(model.to_record()).predict(x[held])
    if not np.allclose(restored, prediction, rtol=0, atol=1e-12):
        raise ValueError('Model serialization changes prediction')
    model_path = f'{model_root}/{label}.json'
    write_json(model_path, model.to_record())
    predictions = array_file(f'{prediction_root}/{label}.npy',
                             np.column_stack([held.astype(np.float64), prediction]))
    record = {'identity': identity, 'model': {'path': model_path, 'sha256': sha256(ROOT / model_path)},
              'predictions': predictions, 'fit_audit': model.fit_audit_}
    write_json(f'{fit_root}/{label}.json', record)
    return record, prediction


def fit_identity(*, freeze_sha256, recipe, provider, partition, extra=None):
    identity = {'freeze_sha256': freeze_sha256, 'recipe': recipe, 'provider': provider,
                'partition': partition}
    if extra:
        identity.update(extra)
    return identity


def provider_digest(audit):
    return hashlib.sha256(canonical_json(audit)).hexdigest()


def outer_partition(store, outer):
    """Whole development partition for training; the untouched fold for scoring."""
    fold = store.rows.outer_fold.to_numpy()
    return np.flatnonzero(fold != outer), np.flatnonzero(fold == outer)


def inner_partition(store, outer, inner):
    """Exactly the partition the committed inner runner used, regenerated, not guessed."""
    fold = store.rows.outer_fold.to_numpy()
    pool = np.flatnonzero(fold != outer)
    assignment = store.rows.component.map(store.split['inner_component_folds'][str(outer)])
    if assignment.iloc[pool].isna().any():
        raise ValueError('Missing inner fold assignment')
    values = assignment.iloc[pool].to_numpy()
    return pool[values != inner], pool[values == inner]


def development_partitions(store):
    """Every train/evaluation boundary the development protocol ever fits inside."""
    partitions = {}
    for outer in range(store.design['outer_folds']):
        partitions[f'outer_{outer}'] = outer_partition(store, outer)
        for inner in range(store.design['inner_folds']):
            partitions[f'inner_{outer}_{inner}'] = inner_partition(store, outer, inner)
    return partitions
