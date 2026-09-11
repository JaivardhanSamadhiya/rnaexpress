"""Shortcut-resistance evidence for the frozen primary score (gate 8).

Three separate things are checked, and they are not interchangeable:

1. a structural check that no fitted primary model contains a source, reporter,
   parent, gene, outcome or requested-direction channel;
2. nuisance decodability probes, computed from the frozen score with legal
   grouping. Strong decodability alone neither proves nor disproves a shortcut:
   edit size is genuinely correlated with mechanism, so a decodable score is not
   automatically a cheating score;
3. a pointer to the matched-stratum and partition-local permutation nulls, which
   are the actual falsification tests and live in the control evidence.

Probes use grouped out-of-fold nearest-class-mean decoding of a single score.
That is deliberately the weakest reasonable decoder: it exists to describe the
score, not to maximize an accuracy number.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .feature_store import FeatureStore
from .gates import with_strata
from .io import ROOT, sha256, write_json
from .outer_evaluation import load_scores, verify_outer_freeze
from .ranking import PairedRanker

PROBES = 'results/mechanism_v2/outer/shortcut_probes.json'
FORBIDDEN = ('source_id', 'dataset_id', 'parent_id', 'gene_id', 'reporter_id',
             'localization_effect', 'requested_direction')
UNSEEN_LABEL_PROBES = ('biological_unit', 'gene_label')


def structural_check(manifest):
    """Read back every fitted primary model and inspect its actual column names."""
    findings = []
    for name, record in sorted(manifest['scores'].items()):
        for fold in record['audit']['folds']:
            path = ROOT / fold['model']['path']
            if sha256(path) != fold['model']['sha256']:
                raise ValueError(f'Model record hash mismatch: {fold["model"]["path"]}')
            model = PairedRanker.from_record(json.loads(path.read_text()))
            offending = sorted({column for column in model.feature_names_
                                if any(part in column.lower() for part in FORBIDDEN)})
            findings.append({'score': name, 'outer_fold': fold['outer_fold'],
                             'columns': len(model.feature_names_),
                             'blocks': sorted({c.split(':')[0] for c in model.feature_names_}),
                             'identity_columns': offending,
                             'ranking_temperatures': model.ranking_temperatures_})
    violations = [f for f in findings if f['identity_columns']]
    return {'models_inspected': len(findings), 'violations': violations,
            'clean': not violations, 'per_model': findings}


def grouped_nearest_mean_probe(score, labels, groups, folds=5, seed=20260909):
    """Grouped out-of-fold decoding of a nuisance label from the single score."""
    score = np.asarray(score, float)
    labels = np.asarray(labels).astype(str)
    groups = np.asarray(groups).astype(str)
    unique_groups = np.array(sorted(set(groups)))
    if len(unique_groups) < folds:
        return {'eligible': False, 'reason': 'fewer independent groups than folds'}
    rng = np.random.default_rng(seed)
    assignment = dict(zip(unique_groups, rng.permutation(len(unique_groups)) % folds))
    fold_of = np.array([assignment[g] for g in groups])
    predicted = np.empty(len(labels), dtype=object)
    unseen = 0
    for fold in range(folds):
        train = fold_of != fold
        test = ~train
        if not train.any() or not test.any():
            continue
        classes = sorted(set(labels[train]))
        centres = np.array([score[train & (labels == c)].mean() for c in classes])
        unseen += int(np.isin(labels[test], classes, invert=True).sum())
        predicted[test] = [classes[int(np.argmin(np.abs(centres - v)))] for v in score[test]]
    accuracy = float((predicted == labels).mean())
    frequencies = pd.Series(labels).value_counts(normalize=True)
    balanced = float(np.mean([
        (predicted[labels == c] == c).mean() for c in sorted(set(labels))]))
    return {'eligible': True, 'accuracy': accuracy,
            'majority_class_accuracy': float(frequencies.max()),
            'balanced_accuracy': balanced, 'classes': int(len(frequencies)),
            'labels_absent_from_some_training_fold': unseen,
            'groups': int(len(unique_groups)), 'folds': folds,
            'decoder': 'grouped out-of-fold nearest-class-mean on the single frozen score'}


def run_shortcut_probes():
    freeze = verify_outer_freeze()
    store = FeatureStore()
    scores, manifest = load_scores(['primary', 'M0'])
    rows = with_strata(store.rows)
    score = scores['primary'][0]
    groups = rows.component.astype(str).to_numpy()
    targets = {
        'dataset': rows.dataset.astype(str).to_numpy(),
        'reporter': rows.reporter.astype(str).to_numpy(),
        'cell_type': rows.cell_type.astype(str).to_numpy(),
        'edit_band': rows.edit_band.astype(str).to_numpy(),
        'intervention_class': rows.intervention_class.astype(str).to_numpy(),
        'direction': rows.direction.astype(str).to_numpy(),
    }
    probes = {name: grouped_nearest_mean_probe(score, values, groups)
              for name, values in targets.items()}
    for name in UNSEEN_LABEL_PROBES:
        probes[name] = {
            'eligible': False,
            'reason': ('every evaluation label is unseen because whole connected components are held '
                       'out, so this classification task is ineligible rather than a zero-accuracy '
                       'success')}
    probes['direction_identifiability'] = {
        'note': ('the two directional decisions on a set share identical covariates and differ only '
                 'by the sign applied to the shared latent score, so direction decodability is not '
                 'separately identifiable from the representation')}
    structural = structural_check(manifest)
    record = {
        'format': 'mechanism_v2_shortcut_probes_v1',
        'outer_freeze_git_commit': freeze['git_commit'],
        'structural_identity_check': structural,
        'probes': probes,
        'falsification_tests': {
            'matched_stratum_permutations': 'results/mechanism_v2/controls/control_evidence.json '
                                            '(n5_bijection_source, n5_bijection_edit_band, '
                                            'n5_bijection_parent, n8_bijection_source_edit_band)',
            'partition_local': 'every bijection is constructed separately inside the training rows '
                               'and inside the evaluation rows of each partition',
            'permutation_seeds': [20260909, 20260910, 20260911]},
        'gate': {
            'gate': 'g8_shortcut_resistance',
            'status': 'pass' if structural['clean'] else 'fail',
            'checks': {'no_identity_channel_in_any_primary_model': structural['clean']},
            'note': ('the numeric permutation falsification requirement is evaluated by gate 7; this '
                     'record supplies the structural guarantee and the descriptive probe table')},
        'interpretation': ('decodability is descriptive. Edit size and mutation class are genuinely '
                           'correlated with mechanism, so a decodable score is not by itself a '
                           'shortcut, and an undecodable score is not by itself a mechanism.'),
    }
    write_json(PROBES, record)
    print(f'g8_shortcut_resistance: {record["gate"]["status"]} '
          f'({structural["models_inspected"]} fitted models inspected)', flush=True)
    return record
