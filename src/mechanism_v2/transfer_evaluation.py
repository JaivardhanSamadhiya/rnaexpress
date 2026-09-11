"""Purged transfer evaluation: leave-source, cross-cell, cross-reporter, large-to-small.

Every transfer task comes from the committed, outcome-blind inventory in
`results/mechanism_v2/manifests/transfer_inventory.json`, in which the connected
component of any held-out row is purged from the training side. A measured
mutant therefore never serves as its own transfer, and a paired-context training
parent can never masquerade as zero-shot evidence.

Recipes are re-selected inside each task's own training domain using that task's
committed inner component folds, because borrowing the primary-fold choice for a
different training domain would not be a valid nested selection. Selection uses
training-side rows only; the held context's outcomes are read once, by the
metric code, after the model is frozen.
"""
from __future__ import annotations

import json

import numpy as np

from .development_training import verify_freeze
from .feature_store import FeatureStore
from .fitting import fit_identity, partition_audit, provider_digest, run_fit
from .gates import frozen_gates, gate_cross_context, gate_leave_source, paired_evidence, with_strata
from .io import ROOT, sha256, write_json
from .outer_evaluation import recipe_variants, verify_outer_freeze
from .primitives import choose_recipe
from .providers import FamilyProvider
from .evaluation import decision_metrics
from .development_training import metric_summary

TRANSFER_INVENTORY = 'results/mechanism_v2/manifests/transfer_inventory.json'
TRANSFER_EVIDENCE = 'results/mechanism_v2/transfer/transfer_evidence.json'
FOLDED_KINDS = ('within_source', 'cross_cell', 'cross_reporter', 'large_to_small')


def load_inventory():
    record = json.loads((ROOT / TRANSFER_INVENTORY).read_text())
    if record['outcomes_used'] or record['models_fit']:
        raise ValueError('Transfer inventory is not the committed outcome-blind inventory')
    if sha256(ROOT / 'results/mechanism_v2/manifests/splits_all_alleles95.json') != \
            record['primary_split_manifest_sha256']:
        raise ValueError('Transfer inventory was built against a different primary split')
    return record


def group_key(task):
    return task['name'] if task['kind'] not in FOLDED_KINDS else task['name'].rsplit('_', 1)[0]


def task_groups(inventory):
    groups = {}
    for task in inventory['tasks']:
        groups.setdefault(group_key(task), {'kind': task['kind'], 'tasks': []})['tasks'].append(task)
    return groups


def _task_inner_folds(store, task):
    """The committed component-to-inner-fold map for this task's training domain."""
    train = np.asarray(task['train_row_ids'], int)
    mapping = task['inner_component_folds']
    components = store.rows.component.astype(str).to_numpy()[train]
    unknown = sorted(set(components) - set(map(str, mapping)))
    if unknown:
        raise ValueError(f'Task {task["name"]} has training components without an inner fold')
    return train, np.array([int(mapping[str(c)]) for c in components], int)


def select_for_task(store, provider, task, *, freeze_sha256, namespace='transfer'):
    """Inner-only selection of one of the six recipes inside a task's training domain."""
    train, assignment = _task_inner_folds(store, task)
    tolerance = store.design['selection']['regret_tolerance']
    static_audit = provider.audit(store)
    predictions, variants = {}, None
    for inner in sorted(set(assignment.tolist())):
        inner_train = train[assignment != inner]
        inner_valid = train[assignment == inner]
        if not inner_train.size or not inner_valid.size:
            continue
        label = f'{task["name"]}_inner_{inner}'
        boundary = partition_audit(store.rows, inner_train, inner_valid)
        x, columns, provenance = provider.build(store, inner_train, inner_valid, label)
        variants = variants or recipe_variants(store, len(columns))
        frame = store.train_frame(inner_train)
        for variant in variants:
            predictions.setdefault(variant['variant'], np.full(len(store.rows), np.nan))
            identity = fit_identity(
                freeze_sha256=freeze_sha256,
                recipe={'provider': provider.name, 'variant': variant['variant'],
                        'config': variant['config']},
                provider={'name': provider.name, 'static_digest': provider_digest(static_audit),
                          'partition_digest': provider_digest(provenance), 'columns': len(columns)},
                partition=boundary,
                extra={'stage': 'transfer_inner_selection', 'task': task['name'], 'inner_fold': int(inner)})
            _, prediction = run_fit(f'{namespace}/{provider.name}/{label}_{variant["variant"]}',
                                    identity, x, columns, variant['config'], frame,
                                    inner_train, inner_valid)
            predictions[variant['variant']][inner_valid] = prediction
    if variants is None:
        return None
    records = []
    for variant in variants:
        value = predictions[variant['variant']]
        mask = np.isfinite(value)
        if not mask.any():
            return None
        metrics, _ = decision_metrics(store.rows.loc[mask], value[mask])
        if metrics.empty:
            return None
        records.append({'recipe_id': f'{provider.name}_{variant["variant"]}',
                        'variant': variant['variant'], 'config': variant['config'],
                        'complexity': variant['complexity'], **metric_summary(metrics)})
    selected = choose_recipe(records, tolerance)
    return {'selected': next(r for r in records if r['recipe_id'] == selected),
            'inner_summaries': records, 'outer_outcomes_used': False}


def score_task(store, provider, task, selection, *, freeze_sha256, namespace='transfer'):
    train = np.asarray(task['train_row_ids'], int)
    test = np.asarray(task['test_row_ids'], int)
    boundary = partition_audit(store.rows, train, test)
    x, columns, provenance = provider.build(store, train, test, task['name'])
    recipe = selection['selected']
    identity = fit_identity(
        freeze_sha256=freeze_sha256,
        recipe={'provider': provider.name, 'recipe_id': recipe['recipe_id'],
                'variant': recipe['variant'], 'config': recipe['config']},
        provider={'name': provider.name, 'static_digest': provider_digest(provider.audit(store)),
                  'partition_digest': provider_digest(provenance), 'columns': len(columns)},
        partition=boundary,
        extra={'stage': 'transfer_evaluation', 'task': task['name']})
    record, prediction = run_fit(f'{namespace}/{provider.name}/{task["name"]}', identity, x, columns,
                                 recipe['config'], store.train_frame(train), train, test)
    return prediction, test, {'task': task['name'], 'recipe_id': recipe['recipe_id'],
                              'boundary': boundary, 'purged_train_rows': task['purged_train_rows'],
                              'model': record['model'], 'fit_audit': record['fit_audit']}


def evaluate_transfer():
    freeze = verify_outer_freeze()
    frozen = verify_freeze()
    gates = frozen_gates()
    store = FeatureStore()
    digest = freeze['inner_training_freeze_sha256']
    inventory = load_inventory()
    rows = with_strata(store.rows)
    primary = FamilyProvider(freeze['primary_family'])
    baseline = FamilyProvider('M0')
    groups = task_groups(inventory)
    minimum_components = gates['eligibility']['transfer_minimum_components']
    minimum_decisions = gates['eligibility']['transfer_minimum_decisions']
    results, audits = {}, {}
    for key in sorted(groups):
        group = groups[key]
        scores = {'primary': np.full(len(store.rows), np.nan),
                  'M0': np.full(len(store.rows), np.nan)}
        covered = np.zeros(len(store.rows), bool)
        fold_audit, ineligible = [], []
        for task in group['tasks']:
            if not task['eligible_for_fitting']:
                ineligible.append({'task': task['name'], 'reason': task['ineligible_reason'],
                                   'train_components': task['train_components'],
                                   'test_decisions': task['test_decisions']})
                continue
            selections = {}
            for name, provider in (('primary', primary), ('M0', baseline)):
                selection = select_for_task(store, provider, task, freeze_sha256=digest)
                if selection is None:
                    ineligible.append({'task': task['name'],
                                       'reason': f'{name}: no eligible inner decision set in the task domain'})
                    selections = None
                    break
                selections[name] = selection
            if not selections:
                continue
            for name, provider in (('primary', primary), ('M0', baseline)):
                prediction, test, audit = score_task(store, provider, task, selections[name],
                                                     freeze_sha256=digest)
                scores[name][test] = prediction
                covered[test] = True
                fold_audit.append({'model': name, **audit})
            print(f'Transfer task fitted and scored once: {task["name"]}', flush=True)
        if not covered.any():
            results[key] = {'kind': group['kind'], 'eligible': False,
                            'reason': 'no eligible fold in this directed transfer',
                            'ineligible_folds': ineligible}
            continue
        mask = covered & np.isfinite(scores['primary']) & np.isfinite(scores['M0'])
        entry = {'kind': group['kind'], 'coverage_rows': int(mask.sum()),
                 'folds_scored': len(fold_audit) // 2, 'ineligible_folds': ineligible,
                 'directions': {}}
        for direction in ('increase', 'decrease'):
            evidence = paired_evidence(rows, scores['primary'], scores['M0'], mask=mask,
                                       direction=direction, bootstrap=0,
                                       minimum_decisions=minimum_decisions,
                                       label=f'{key}|{direction}')
            if evidence.get('eligible') and evidence['components'] < minimum_components:
                evidence = {'label': f'{key}|{direction}', 'eligible': False, 'direction': direction,
                            'reason': f'{evidence["components"]} independent components below the '
                                      f'required {minimum_components}',
                            'descriptive_point': evidence['point'],
                            'components': evidence['components']}
            entry['directions'][direction] = evidence
        entry['eligible'] = any(v.get('eligible') for v in entry['directions'].values())
        results[key] = entry
        audits[key] = fold_audit
    leave_source = {f'{k}|{d}': v['directions'][d] for k, v in results.items()
                    if v['kind'] == 'leave_source' for d in ('increase', 'decrease')
                    if 'directions' in v}
    cell = {f'{k}|{d}': v['directions'][d] for k, v in results.items()
            if v['kind'] == 'cross_cell' for d in ('increase', 'decrease') if 'directions' in v}
    reporter = {f'{k}|{d}': v['directions'][d] for k, v in results.items()
                if v['kind'] == 'cross_reporter' for d in ('increase', 'decrease') if 'directions' in v}
    record = {
        'format': 'mechanism_v2_transfer_evidence_v1',
        'outer_freeze_git_commit': freeze['git_commit'],
        'gate_config_sha256': freeze['gate_config_sha256'],
        'primary_family': freeze['primary_family'],
        'inventory_sha256': sha256(ROOT / TRANSFER_INVENTORY),
        'inventory_scope': inventory['scope'],
        'tasks': results,
        'fold_audits': audits,
        'gates': {'g4_leave_source': gate_leave_source(leave_source, gates),
                  'g5_cross_context': gate_cross_context(cell, reporter, gates)},
        'notes': [
            'Held connected groups are purged from the training side of every task, so a measured '
            'mutant never serves as its own transfer.',
            'Recipes are re-selected inside each task training domain; the primary-fold choice is '
            'never borrowed for a different training domain.',
            'A directed transfer with no eligible fold is reported as ineligible, never passed.'],
    }
    write_json(TRANSFER_EVIDENCE, record)
    for name, gate in record['gates'].items():
        print(f'{name}: {gate["status"]}', flush=True)
    return record
