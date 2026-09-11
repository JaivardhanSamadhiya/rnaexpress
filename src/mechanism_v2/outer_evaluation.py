"""Frozen outer evaluation: train on each outer training partition, score it once.

The contract this module enforces is narrow and mechanical:

* an outer fold's rows are never seen by the model that scores them, and the
  whole fold is scored exactly once;
* the recipe used for a fold is the one the committed inner-only selection
  already chose from that fold's development rows, read from
  `results/mechanism_v2/training/outer_*/selection.json`, never re-chosen here;
* every dependency of the evaluation is verified to be committed at HEAD before
  a single outer score can be produced, and recorded in an outer freeze;
* no Astrocyte path exists. `io.open_holdout` still refuses.

Recipes, features, splits, folds, tie rules and gate thresholds are inputs to
this module. It has no code path that can change any of them.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .development_training import FREEZE, committed_hash, metric_summary, verify_freeze
from .evaluation import decision_metrics
from .feature_store import BLOCK_MANIFESTS, FeatureStore
from .fitting import (assert_outer_boundary, development_partitions, fit_identity, inner_partition,
                      outer_partition, partition_audit, provider_digest, run_fit)
from .gates import gate_config_sha256, GATE_CONFIG
from .io import ROOT, git, sha256, write_json
from .primitives import choose_recipe
from .providers import primary_family_providers

OUTER_FREEZE = 'results/mechanism_v2/manifests/outer_evaluation_freeze.json'
NUISANCE_DIMENSIONS = {'none': 0, 'source': 3, 'size': 7, 'source_size': 10}

EVALUATION_CODE = ['src/mechanism_v2/' + name + '.py' for name in [
    'io', 'groups', 'splits', 'ranking', 'primitives', 'feature_store', 'development_training',
    'evaluation', 'forensics', 'features', 'fitting', 'providers', 'gates', 'control_kernels',
    'control_features', 'outer_evaluation', 'development_analysis', 'controls',
    'transfer_evaluation', 'uncertainty', 'shortcut_probes', 'reporting', 'transfer_inventory',
    'training_status', 'motif_processing', 'allele_summaries']]
EVALUATION_DESIGN = [
    'configs/mechanism_v2/localization_design.json', GATE_CONFIG,
    'configs/mechanism_v2/environment.lock.txt',
    'reports/mechanism_v2/protocol_design.md', 'reports/mechanism_v2/model_selection.md',
    'reports/mechanism_v2/prospective_gate_design.md', 'reports/mechanism_v2/frozen_protocol.md',
]
EVALUATION_EVIDENCE = [
    FREEZE, 'results/mechanism_v2/manifests/splits_all_alleles95.json',
    'results/mechanism_v2/manifests/transfer_inventory.json',
    'results/mechanism_v2/manifests/splits_all_alleles90.json',
    'results/mechanism_v2/manifests/splits_gene_group_sensitivity.json',
    'results/mechanism_v2/training/inner_complete.json',
    'results/mechanism_v2/training/status/verified_0720_fits.json',
] + [f'results/mechanism_v2/training/outer_{outer}/selection.json' for outer in range(5)]


def prepare_outer_evaluation():
    """Authorize outer evaluation only when every dependency is committed at HEAD."""
    frozen = verify_freeze()
    store = FeatureStore()
    paths = EVALUATION_CODE + EVALUATION_DESIGN + EVALUATION_EVIDENCE + [store.split['outer']]
    paths += ['results/mechanism_v2/features/' + p for p in BLOCK_MANIFESTS.values()]
    paths += ['results/mechanism_v2/features/random_kmer_delta_manifest.json',
              'results/mechanism_v2/features/rbp_absolute_allele_manifest.json',
              'results/mechanism_v2/features/bert_pooled_absolute_manifest.json',
              'results/mechanism_v2/features/broken_reference_manifest.json']
    hashes = {path: committed_hash(path) for path in sorted(set(paths))}
    selections = selected_recipes(store, frozen)
    record = {
        'format': 'mechanism_v2_outer_evaluation_freeze_v1',
        'git_commit': git('rev-parse', 'HEAD'),
        'inner_training_freeze_sha256': sha256(ROOT / FREEZE),
        'gate_config_sha256': gate_config_sha256(),
        'dependencies': hashes,
        'candidate_rows': int(len(store.rows)),
        'components': int(store.rows.component.nunique()),
        'outer_folds': int(store.design['outer_folds']),
        'family_selections': {str(outer): selections['family'][outer] for outer in selections['family']},
        'primary_selections': {str(outer): selections['primary'][outer] for outer in selections['primary']},
        'primary_family': selections['primary_family'],
        'primary_family_agreement': selections['primary_family_agreement'],
        'outer_evaluation_authorized': True,
        'holdout_authorized': False,
        'contract': ('for each outer fold, fit the inner-selected recipe on that fold\'s whole '
                     'development partition and score the untouched fold exactly once'),
    }
    write_json(OUTER_FREEZE, record)
    print(f'Outer evaluation freeze verified at {record["git_commit"][:12]}; '
          f'primary family {record["primary_family"]}', flush=True)
    return record


def verify_outer_freeze():
    record = json.loads((ROOT / OUTER_FREEZE).read_text())
    if record['format'] != 'mechanism_v2_outer_evaluation_freeze_v1':
        raise ValueError('Unknown outer evaluation freeze')
    if not record['outer_evaluation_authorized']:
        raise PermissionError('Outer evaluation is not authorized by the committed freeze')
    for path, digest in record['dependencies'].items():
        if sha256(ROOT / path) != digest:
            raise PermissionError(f'Frozen outer evaluation dependency changed: {path}')
    if sha256(ROOT / FREEZE) != record['inner_training_freeze_sha256']:
        raise PermissionError('Inner training freeze changed')
    if gate_config_sha256() != record['gate_config_sha256']:
        raise PermissionError('Gate thresholds changed after the outer freeze')
    return record


def selected_recipes(store, frozen):
    """Read the committed inner-only selections; never reselect against outcomes."""
    digest = sha256(ROOT / FREEZE)
    lookup = {r['recipe_id']: r for r in frozen['recipes']}
    family, primary, families = {}, {}, []
    for outer in range(store.design['outer_folds']):
        path = ROOT / f'results/mechanism_v2/training/outer_{outer}/selection.json'
        record = json.loads(path.read_text())
        if record['freeze_sha256'] != digest or record['outer_outcomes_used']:
            raise PermissionError('Inner selection record is not the committed outcome-blind selection')
        if len(record['inner_summaries']) != len(frozen['recipes']):
            raise ValueError('Incomplete inner selection')
        family[outer] = {f: lookup[r] for f, r in record['family_selections'].items()}
        primary[outer] = lookup[record['primary_selection']]
        families.append(primary[outer]['family'])
    counts = {f: families.count(f) for f in sorted(set(families))}
    dominant = min(counts, key=lambda f: (-counts[f], f))
    return {'family': family, 'primary': primary,
            'primary_family': dominant,
            'primary_family_agreement': {'per_fold': families, 'counts': counts,
                                         'unanimous': len(counts) == 1}}


def _finite_slice(x, indices, label):
    values = x[np.asarray(indices, int)]
    if not np.isfinite(values).all():
        raise ValueError(f'Non-finite feature reached {label}')
    return values


def recipe_variants(store, columns):
    """The same six frozen recipes, with complexity recomputed for this width."""
    records = []
    for variant in store.design['recipes_per_family']:
        config = {k: v for k, v in variant.items() if k != 'id'}
        config.update(store.design['ranker_constants'])
        config['seed'] = store.design['seed']
        records.append({'variant': variant['id'], 'config': config,
                        'complexity': int(columns + NUISANCE_DIMENSIONS[config['nuisance']]
                                          + 3 * int(config['ranking_heads']))})
    return records


def inner_selection(store, provider, namespace, *, freeze_sha256, seed=None):
    """Inner-only selection of one of the six recipes for an arbitrary provider.

    This is the same nested procedure, tie order and tolerance as the committed
    primary inner runner. It reads no outer-fold row and no outer-fold outcome.
    """
    if not provider.eligible:
        return {'provider': provider.name, 'eligible': False,
                'ineligible_reason': provider.ineligible_reason}
    tolerance = store.design['selection']['regret_tolerance']
    static_audit = provider.audit(store)
    chosen, summaries = {}, {}
    for outer in range(store.design['outer_folds']):
        predictions, variants = {}, None
        for inner in range(store.design['inner_folds']):
            label = f'inner_{outer}_{inner}'
            train_all, valid_all = inner_partition(store, outer, inner)
            boundary = partition_audit(store.rows, train_all, valid_all)
            x, columns, provenance = provider.build(store, train_all, valid_all, label)
            keep = provider.eligibility(store, train_all, valid_all, label)
            train = train_all[keep[train_all]]
            valid = valid_all[keep[valid_all]]
            if not train.size or not valid.size:
                raise ValueError(f'{provider.name}: empty eligible inner partition {label}')
            partition = partition_audit(store.rows, train, valid)
            _finite_slice(x, train, f'{provider.name} inner training')
            _finite_slice(x, valid, f'{provider.name} inner validation')
            variants = variants or recipe_variants(store, len(columns))
            frame = store.train_frame(train)
            for variant in variants:
                config = dict(variant['config'])
                if seed is not None:
                    config['seed'] = int(seed)
                predictions.setdefault(variant['variant'], np.full(len(store.rows), np.nan))
                identity = fit_identity(
                    freeze_sha256=freeze_sha256,
                    recipe={'provider': provider.name, 'variant': variant['variant'], 'config': config},
                    provider={'name': provider.name,
                              'static_digest': provider_digest(static_audit),
                              'partition_digest': provider_digest(provenance),
                              'columns': len(columns)},
                    partition=partition,
                    extra={'boundary': boundary, 'stage': 'inner_selection'})
                _, prediction = run_fit(f'{namespace}/{provider.name}/{label}_{variant["variant"]}',
                                        identity, x, columns, config, frame, train, valid)
                predictions[variant['variant']][valid] = prediction
            del x
        records = []
        for variant in variants:
            value = predictions[variant['variant']]
            mask = np.isfinite(value)
            metrics, _ = decision_metrics(store.rows.loc[mask], value[mask])
            records.append({'recipe_id': f'{provider.name}_{variant["variant"]}',
                            'variant': variant['variant'], 'config': variant['config'],
                            'complexity': variant['complexity'],
                            'scored_rows': int(mask.sum()), **metric_summary(metrics)})
        selected = choose_recipe(records, tolerance)
        chosen[outer] = next(r for r in records if r['recipe_id'] == selected)
        summaries[str(outer)] = records
    return {'provider': provider.name, 'eligible': True, 'static_audit': static_audit,
            'selection_tolerance': tolerance, 'inner_summaries': summaries,
            'selected_per_outer_fold': {str(k): v['recipe_id'] for k, v in chosen.items()},
            'selected': chosen, 'outer_outcomes_used': False}


def outer_scores(store, provider, recipe_by_fold, namespace, *, freeze_sha256, seed=None,
                 suffix=''):
    """Fit each outer training partition once and score its untouched fold once."""
    score = np.full(len(store.rows), np.nan)
    eligible = np.zeros(len(store.rows), bool)
    mixed = isinstance(provider, dict)
    name = 'primary_selector' if mixed else provider.name
    static_audit = ({str(k): v.audit(store) for k, v in sorted(provider.items())} if mixed
                    else provider.audit(store))
    audits = []
    for outer in range(store.design['outer_folds']):
        label = f'outer_{outer}'
        train_all, held_all = outer_partition(store, outer)
        boundary = assert_outer_boundary(store.rows, outer, train_all, held_all)
        active = _resolve(provider, outer)
        x, columns, provenance = active.build(store, train_all, held_all, label)
        keep = active.eligibility(store, train_all, held_all, label)
        train = train_all[keep[train_all]]
        held = held_all[keep[held_all]]
        if not train.size or not held.size:
            raise ValueError(f'{name}: empty eligible outer partition {label}')
        partition = partition_audit(store.rows, train, held)
        _finite_slice(x, train, f'{name} outer training')
        _finite_slice(x, held, f'{name} outer evaluation')
        recipe = recipe_by_fold[outer]
        config = dict(recipe['config'])
        if seed is not None:
            config['seed'] = int(seed)
        identity = fit_identity(
            freeze_sha256=freeze_sha256,
            recipe={'provider': active.name, 'recipe_id': recipe.get('recipe_id'),
                    'variant': recipe.get('variant'), 'family': recipe.get('family'), 'config': config},
            provider={'name': active.name, 'static_digest': provider_digest(static_audit),
                      'partition_digest': provider_digest(provenance), 'columns': len(columns)},
            partition=partition,
            extra={'boundary': boundary, 'stage': 'outer_evaluation', 'outer_fold': int(outer)})
        record, prediction = run_fit(f'{namespace}/{name}/outer_{outer}{suffix}', identity,
                                    x, columns, config, store.train_frame(train), train, held)
        score[held] = prediction
        eligible[held] = True
        audits.append({'outer_fold': int(outer), 'provider': active.name,
                       'recipe_id': recipe.get('recipe_id'),
                       'variant': recipe.get('variant'), 'columns': len(columns),
                       'boundary': boundary, 'eligible_partition': partition,
                       'provider_partition_audit': provenance,
                       'model': record['model'], 'predictions': record['predictions'],
                       'fit_audit': record['fit_audit']})
        del x
    if not np.isfinite(score[eligible]).all():
        raise ValueError('Non-finite outer score')
    if eligible.all() and np.isfinite(score).sum() != len(store.rows):
        raise ValueError('Full-coverage provider did not score every candidate exactly once')
    return score, eligible, {'provider': name, 'static_audit': static_audit,
                             'seed': seed, 'folds': audits,
                             'scored_rows': int(eligible.sum()),
                             'coverage': float(eligible.mean())}


def score_record(relative, score, eligible, audit):
    from .features import array_file
    array = array_file(relative, np.column_stack([score, eligible.astype(np.float64)]))
    return {'array': array, 'audit': audit}


SCORE_MANIFEST = 'results/mechanism_v2/outer/score_manifest.json'
EVIDENCE = 'results/mechanism_v2/outer/development_evidence.json'


def _resolve(provider, outer):
    return provider[outer] if isinstance(provider, dict) else provider


def load_scores(names=None):
    """Rehydrate frozen outer score vectors by hash; never recompute silently."""
    manifest = json.loads((ROOT / SCORE_MANIFEST).read_text())
    scores = {}
    for name, record in manifest['scores'].items():
        if names is not None and name not in names:
            continue
        entry = record['array']
        path = ROOT / entry['path']
        if sha256(path) != entry['sha256']:
            raise ValueError(f'Outer score array hash mismatch: {entry["path"]}')
        value = np.load(path, allow_pickle=False)
        scores[name] = (value[:, 0], value[:, 1].astype(bool))
    return scores, manifest


def evaluate_families():
    """Produce the one frozen outer score vector per family and for the selector."""
    freeze = verify_outer_freeze()
    frozen = verify_freeze()
    store = FeatureStore()
    digest = freeze['inner_training_freeze_sha256']
    selections = selected_recipes(store, frozen)
    providers = primary_family_providers(store)
    records = {}
    for family in sorted(providers):
        recipe_by_fold = {outer: selections['family'][outer][family]
                          for outer in range(store.design['outer_folds'])}
        score, eligible, audit = outer_scores(store, providers[family], recipe_by_fold, 'outer',
                                              freeze_sha256=digest)
        records[family] = score_record(f'data/interim/mechanism_v2/outer_scores/{family}.npy',
                                       score, eligible, audit)
        print(f'Outer evaluation complete for {family}: '
              f'{records[family]["audit"]["scored_rows"]} candidate rows scored once', flush=True)
    primary_provider = {outer: providers[selections['primary'][outer]['family']]
                        for outer in range(store.design['outer_folds'])}
    primary_recipe = {outer: selections['primary'][outer] for outer in range(store.design['outer_folds'])}
    score, eligible, audit = outer_scores(store, primary_provider, primary_recipe, 'outer',
                                          freeze_sha256=digest)
    records['primary'] = score_record('data/interim/mechanism_v2/outer_scores/primary.npy',
                                      score, eligible, audit)
    write_json(SCORE_MANIFEST, {
        'format': 'mechanism_v2_outer_score_manifest_v1',
        'outer_freeze_git_commit': freeze['git_commit'],
        'inner_training_freeze_sha256': digest,
        'gate_config_sha256': freeze['gate_config_sha256'],
        'primary_family': selections['primary_family'],
        'primary_family_agreement': selections['primary_family_agreement'],
        'family_selections': {str(o): {f: r['recipe_id'] for f, r in selections['family'][o].items()}
                               for o in selections['family']},
        'primary_selections': {str(o): selections['primary'][o]['recipe_id'] for o in selections['primary']},
        'scores': records,
        'evaluated_once': True, 'holdout_opened': False})
    print(f'Frozen outer scores recorded for {len(records)} score vectors', flush=True)
    return records
