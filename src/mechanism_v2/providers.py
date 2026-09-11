"""Feature-matrix providers: the frozen families and every specified control null.

A provider turns a partition boundary into a feature matrix plus an auditable
provenance record. Providers never see an outcome column. Providers whose
construction depends on the partition build the permutation separately inside
the training rows and inside the evaluation rows, which is what makes a
permutation null a real null rather than a leak.

Column names are explicit and are rejected by the ranker if they smuggle source,
parent, gene or reporter identity into a primary latent score. The two providers
that deliberately use identity information are marked `diagnostic_only` and are
never eligible to be a primary selector.
"""
from __future__ import annotations

import json

import numpy as np

from .feature_store import DIMENSIONS
from .io import ROOT, SOURCES, sha256

ROW_INDEXED = ('geometry', 'trans_aligned')
EDIT_BANDS = ('0', '1', '2-5', '6-10', '11-25', '26-50', '>50')
INTERVENTION_CLASSES = (
    'motif_random_replacement', 'necessity_deletion_with_inactive_padding',
    'random_substitution', 'regional_shuffle', 'shape_structure_perturbation',
    'sufficiency_background_replacement', 'tdp43_motif_complement_replacement',
)
SOURCE_ORDER = tuple(sorted(SOURCES))


def _checked(manifest_relative, field=None):
    record = json.loads((ROOT / manifest_relative).read_text())
    entry = record[field] if field else record
    path = ROOT / entry['path']
    if sha256(path) != entry['sha256']:
        raise ValueError(f'Control feature array hash mismatch: {entry["path"]}')
    value = np.load(path, mmap_mode='r', allow_pickle=False)
    if list(value.shape) != entry['shape']:
        raise ValueError(f'Control feature shape mismatch: {entry["path"]}')
    return value, {'path': entry['path'], 'sha256': entry['sha256'], 'shape': entry['shape']}


def _stack(store, names, feature_rows, prefix=''):
    blocks, columns = [], []
    for name in names:
        value = np.asarray(store.blocks[name])
        if name not in ROW_INDEXED:
            value = value[feature_rows]
        if value.shape[0] != len(store.rows):
            raise ValueError(f'Block {name} does not span the candidate inventory')
        blocks.append(value)
        columns += [f'{prefix}{name}:{j:03d}' for j in range(value.shape[1])]
    return np.column_stack(blocks).astype(np.float32, copy=False), columns


class Provider:
    """Base provider: static, partition-independent, fully auditable."""

    diagnostic_only = False
    eligible = True
    ineligible_reason = None
    partition_dependent = False

    def __init__(self, name, *, family=None):
        self.name = name
        self.family = family
        self._memo = None

    def audit(self, store):
        return {'provider': self.name, 'family': self.family, 'kind': type(self).__name__,
                'partition_dependent': self.partition_dependent,
                'diagnostic_only': self.diagnostic_only}

    def build(self, store, train_idx, eval_idx, label):
        """Partition-independent providers are built once and reused byte-identically."""
        if self.partition_dependent:
            return self._build(store, train_idx, eval_idx, label)
        if self._memo is None:
            self._memo = self._build(store, train_idx, eval_idx, label)
        return self._memo

    def release(self):
        """Drop the cached matrix; large feature blocks are not kept alive by accident."""
        self._memo = None

    def _build(self, store, train_idx, eval_idx, label):
        raise NotImplementedError

    def eligibility(self, store, train_idx, eval_idx, label):
        """Rows a matched null comparison may legitimately use (default: all)."""
        return np.ones(len(store.rows), bool)


class FamilyProvider(Provider):
    """A frozen M0-M7 family, built by exactly the committed inner-training code."""

    def __init__(self, family):
        super().__init__(family, family=family)

    def audit(self, store):
        record = super().audit(store)
        record.update({'blocks': list(store.design['families'][self.family]),
                       'block_manifests': {b: store.records[b]['sha256']
                                           for b in store.design['families'][self.family]
                                           if b in store.records}})
        return record

    def _build(self, store, train_idx, eval_idx, label):
        x, columns = store.matrix(self.family)
        return x, columns, {'columns': len(columns)}


class BlockRemovalProvider(Provider):
    """The selected family with exactly one named block removed and refit."""

    def __init__(self, family, removed):
        super().__init__(f'{family}_minus_{removed}', family=family)
        self.removed = removed

    def audit(self, store):
        record = super().audit(store)
        record.update({'removed_block': self.removed,
                       'retained_blocks': self._retained(store)})
        return record

    def _retained(self, store):
        blocks = list(store.design['families'][self.family])
        if self.removed not in blocks:
            raise ValueError(f'{self.removed} is not part of {self.family}')
        return [b for b in blocks if b != self.removed]

    def _build(self, store, train_idx, eval_idx, label):
        retained = self._retained(store)
        if not retained:
            raise ValueError('Block removal would leave no features')
        x, columns = _stack(store, retained, store.feature_rows)
        return x, columns, {'columns': len(columns), 'removed_block': self.removed}


class EditDescriptorProvider(Provider):
    """N1: fixed edit-size and mutation-class descriptors, declared in code."""

    def __init__(self):
        super().__init__('n1_edit_descriptors')

    def _build(self, store, train_idx, eval_idx, label):
        from .primitives import edit_band
        rows = store.rows
        band = edit_band(rows.edit_cost.to_numpy())
        classes = rows.intervention_class.astype(str).to_numpy()
        unknown = sorted(set(classes) - set(INTERVENTION_CLASSES))
        if unknown:
            raise ValueError(f'Undeclared mutation class: {unknown}')
        blocks = [np.equal.outer(band, np.array(EDIT_BANDS)).astype(np.float32),
                  np.equal.outer(classes, np.array(INTERVENTION_CLASSES)).astype(np.float32),
                  np.column_stack([rows.edit_cost.to_numpy(float),
                                   np.log1p(rows.edit_cost.to_numpy(float)),
                                   rows.edit_fraction.to_numpy(float)]).astype(np.float32)]
        columns = [f'edit_band:{b}' for b in EDIT_BANDS]
        columns += [f'mutation_class:{c}' for c in INTERVENTION_CLASSES]
        columns += ['edit_cost', 'log1p_edit_cost', 'edit_fraction']
        return np.column_stack(blocks), columns, {'columns': len(columns)}


class SourceSlopeProvider(Provider):
    """N2: geometry with source-specific slopes. Diagnostic only, never primary.

    An unseen source contributes zero to every source-specific block and is
    therefore scored by the pooled training-only geometry slope. That fallback
    is stated rather than hidden, and its coverage is recorded per partition.
    """

    diagnostic_only = True
    partition_dependent = True

    def __init__(self):
        super().__init__('n2_geometry_source_slopes')

    def _build(self, store, train_idx, eval_idx, label):
        geometry = np.asarray(store.blocks['geometry'], np.float32)
        sources = store.rows.dataset.astype(str).to_numpy()
        blocks = [geometry]
        columns = [f'geometry:{j:03d}' for j in range(geometry.shape[1])]
        for source in SOURCE_ORDER:
            indicator = (sources == source).astype(np.float32)[:, None]
            blocks.append(geometry * indicator)
            columns += [f'n2_slope_{source}:{j:03d}' for j in range(geometry.shape[1])]
        train_sources = sorted(set(sources[np.asarray(train_idx, int)]))
        held = sources[np.asarray(eval_idx, int)]
        covered = float(np.isin(held, train_sources).mean())
        return np.column_stack(blocks), columns, {
            'columns': len(columns), 'training_sources': train_sources,
            'evaluation_rows_with_a_trained_source': covered,
            'fallback': 'pooled training-only geometry slope for any unseen source'}


class ParentIdentityProvider(Provider):
    """N3: structurally ineligible here, and recorded as such rather than faked.

    Every evaluation partition in this protocol holds out whole connected
    components, so no evaluation parent is ever present in training. A shared
    constant parent intercept also cannot reorder candidates inside a decision
    set, because a decision set is a single parent landscape. Training and
    testing the same parents in order to obtain a number would not be zero-shot
    evidence, so the control is reported ineligible.
    """

    diagnostic_only = True
    eligible = False
    ineligible_reason = ('held-out components leave every evaluation parent unseen, and constant '
                         'parent intercepts are rank-invariant inside a single-parent decision set')

    def __init__(self):
        super().__init__('n3_parent_identity')

    def _build(self, store, train_idx, eval_idx, label):  # pragma: no cover - never fit
        raise PermissionError('N3 is ineligible; see ineligible_reason')


class RandomKmerProvider(Provider):
    """N4: frozen 540-dimensional random projection of 1-4mer allele count deltas."""

    def __init__(self):
        super().__init__('n4_random_kmer_delta')

    def audit(self, store):
        _, provenance = _checked('results/mechanism_v2/features/random_kmer_delta_manifest.json')
        record = super().audit(store)
        record.update({'array': provenance, 'learned_from_localization': False,
                       'maximum_information_rank': 340})
        return record

    def _build(self, store, train_idx, eval_idx, label):
        value, provenance = _checked('results/mechanism_v2/features/random_kmer_delta_manifest.json')
        x = np.asarray(value)[store.feature_rows].astype(np.float32, copy=False)
        columns = [f'n4_random_kmer:{j:03d}' for j in range(x.shape[1])]
        return x, columns, {'columns': len(columns), 'array': provenance}


class AbsoluteAlleleProvider(Provider):
    """N6: absolute allele blocks matched to M1's 540 columns."""

    def __init__(self, allele='mutant'):
        if allele not in {'reference', 'mutant'}:
            raise ValueError('Allele must be reference or mutant')
        super().__init__(f'n6_absolute_{allele}')
        self.allele = allele

    def _arrays(self):
        rbp, rbp_provenance = _checked(
            'results/mechanism_v2/features/rbp_absolute_allele_manifest.json', self.allele)
        bert, bert_provenance = _checked(
            'results/mechanism_v2/features/bert_pooled_absolute_manifest.json', self.allele)
        return rbp, bert, {'rbp': rbp_provenance, 'bert': bert_provenance}

    def audit(self, store):
        record = super().audit(store)
        record.update({'arrays': self._arrays()[2], 'allele': self.allele,
                       'interpretation': 'absolute allele state, not a mutation-induced difference'})
        return record

    def _build(self, store, train_idx, eval_idx, label):
        rbp, bert, provenance = self._arrays()
        x = np.column_stack([np.asarray(rbp)[store.feature_rows],
                             np.asarray(bert)[store.feature_rows]]).astype(np.float32, copy=False)
        columns = [f'n6_{self.allele}_rbp:{j:03d}' for j in range(rbp.shape[1])]
        columns += [f'n6_{self.allele}_bert:{j:03d}' for j in range(bert.shape[1])]
        if x.shape[1] != DIMENSIONS['rbp_delta'] + DIMENSIONS['bert_pooled_delta']:
            raise ValueError('Absolute comparator is not column-matched to M1')
        return x, columns, {'columns': len(columns), 'arrays': provenance}


class ParentAwareProvider(Provider):
    """Named M1-plus-absolute-reference comparator; never part of a primary score."""

    diagnostic_only = True

    def __init__(self):
        super().__init__('m1_parent_aware_comparator', family='M1')

    def _build(self, store, train_idx, eval_idx, label):
        base, columns = store.matrix('M1')
        rbp, _ = _checked('results/mechanism_v2/features/rbp_absolute_allele_manifest.json', 'reference')
        bert, _ = _checked('results/mechanism_v2/features/bert_pooled_absolute_manifest.json', 'reference')
        extra = np.column_stack([np.asarray(rbp)[store.feature_rows],
                                 np.asarray(bert)[store.feature_rows]]).astype(np.float32, copy=False)
        columns = list(columns) + [f'absolute_reference_rbp:{j:03d}' for j in range(rbp.shape[1])]
        columns += [f'absolute_reference_bert:{j:03d}' for j in range(bert.shape[1])]
        return np.column_stack([base, extra]), columns, {'columns': len(columns)}


class BijectionProvider(Provider):
    """N5/N8/N9: whole-block donor bijections, separately inside each partition.

    `blocks=None` permutes every mutation-induced block of the family, which is
    the whole-intervention bijection. A named subset permutes only that block
    and preserves the others. Candidate-row-indexed blocks (trans context) are
    never silently permuted; they are listed as preserved.
    """

    partition_dependent = True

    def __init__(self, family, *, strata=(), blocks=None, seed=20260909,
                 cross_component=False, name=None):
        super().__init__(name or f'bijection_{family}_{"_".join(strata) or "global"}', family=family)
        self.strata = tuple(strata)
        self.blocks = tuple(blocks) if blocks else None
        self.seed = int(seed)
        self.cross_component = bool(cross_component)

    def _targets(self, store):
        names = list(store.design['families'][self.family])
        permutable = [n for n in names if n not in ROW_INDEXED]
        targets = list(self.blocks) if self.blocks else permutable
        unknown = sorted(set(targets) - set(permutable))
        if unknown:
            raise ValueError(f'Cannot permute blocks absent from {self.family}: {unknown}')
        return names, targets, [n for n in names if n not in targets]

    def audit(self, store):
        names, targets, preserved = self._targets(store)
        record = super().audit(store)
        record.update({'partition_dependent': True, 'strata': list(self.strata), 'seed': self.seed,
                       'cross_component_derangement_requested': self.cross_component,
                       'permuted_blocks': targets, 'preserved_blocks': preserved,
                       'donor_unit': 'unique intervention feature_row, replicated to candidate rows afterwards'})
        return record

    def _plan(self, store, train_idx, eval_idx):
        from .control_kernels import intervention_permutation
        idx = np.concatenate([np.asarray(train_idx, int), np.asarray(eval_idx, int)])
        subset = store.rows.iloc[idx]
        role = np.where(np.arange(len(idx)) < len(train_idx), 'train', 'evaluation')
        donor, eligible, audit = intervention_permutation(
            subset, role, strata=self.strata, seed=self.seed, cross_component=self.cross_component)
        return idx, np.asarray(donor, int), np.asarray(eligible, bool), audit

    def _build(self, store, train_idx, eval_idx, label):
        names, targets, preserved = self._targets(store)
        idx, donor, eligible, audit = self._plan(store, train_idx, eval_idx)
        permuted_rows = store.feature_rows.copy()
        permuted_rows[idx] = donor
        blocks, columns = [], []
        for name in names:
            if name in ROW_INDEXED:
                value = np.asarray(store.blocks[name])
            else:
                value = np.asarray(store.blocks[name])[permuted_rows if name in targets else store.feature_rows]
            blocks.append(value)
            columns += [f'{name}:{j:03d}' for j in range(value.shape[1])]
        x = np.column_stack(blocks).astype(np.float32, copy=False)
        summary = {k: v for k, v in audit.items() if k != 'stratum_audit'}
        summary.update({'columns': len(columns), 'permuted_blocks': targets, 'preserved_blocks': preserved,
                        'strata_total': len(audit['stratum_audit']),
                        'strata_eligible': int(sum(a['eligible'] for a in audit['stratum_audit'])),
                        'ineligible_reasons': sorted({a['reason'] for a in audit['stratum_audit'] if a['reason']}),
                        'eligible_rows': int(eligible.sum()), 'partition_rows': int(len(idx))})
        return x, columns, summary

    def eligibility(self, store, train_idx, eval_idx, label):
        idx, _, eligible, _ = self._plan(store, train_idx, eval_idx)
        mask = np.zeros(len(store.rows), bool)
        mask[idx] = eligible
        return mask


class BrokenReferenceProvider(Provider):
    """N7: mutant allele minus an independently assigned reference allele.

    The donor reference RBP profile is pooled at the recipient's edit window, so
    the only perturbed thing is which reference the mutant is compared against.
    Strata are source x native sequence length x edit band with a requested
    cross-component derangement; ineligible strata are named, never repaired.
    """

    partition_dependent = True

    def __init__(self, seed=None):
        from .control_features import BROKEN_SEED
        super().__init__('n7_broken_reference')
        self.seed = int(BROKEN_SEED if seed is None else seed)
        self._cache = None

    def _lookup(self):
        from .control_features import broken_reference_lookup
        if self._cache is None:
            self._cache = broken_reference_lookup()
        return self._cache

    def _plan(self, store):
        from .control_features import broken_reference_plan
        if not hasattr(self, '_plan_cache'):
            self._plan_cache = broken_reference_plan(store, self.seed)
        return self._plan_cache

    def audit(self, store):
        _, _, record = self._lookup()
        summary = super().audit(store)
        summary.update({'partition_dependent': True, 'seed': self.seed,
                        'strata': record['strata'], 'pooled_cache': record['pooled']['sha256'],
                        'cross_component_derangement_requested': True,
                        'definition': record['definition'], 'interpretation': record['interpretation']})
        return summary

    def _build(self, store, train_idx, eval_idx, label):
        pooled, key, record = self._lookup()
        plan, audits = self._plan(store)
        if label not in plan:
            raise KeyError(f'No committed broken-reference donor plan for partition {label}')
        entry = plan[label]
        rows = np.asarray(entry['rows'], int)
        donor = np.asarray(entry['donor_feature_row'], int)
        eligible = np.asarray(entry['eligible'], bool)
        expected = np.concatenate([np.asarray(train_idx, int), np.asarray(eval_idx, int)])
        if not np.array_equal(rows, expected):
            raise ValueError('Broken-reference plan does not match the requested partition')
        rbp_mutant, _ = _checked('results/mechanism_v2/features/rbp_absolute_allele_manifest.json', 'mutant')
        bert_mutant, _ = _checked('results/mechanism_v2/features/bert_pooled_absolute_manifest.json', 'mutant')
        bert_reference, _ = _checked('results/mechanism_v2/features/bert_pooled_absolute_manifest.json', 'reference')
        recipient = store.feature_rows
        width = rbp_mutant.shape[1] + bert_mutant.shape[1]
        x = np.full((len(store.rows), width), np.nan, np.float32)
        lookup_rows = np.array([key.get((int(d), int(r)), -1) for d, r in
                                zip(donor, recipient[rows])], int)
        usable = eligible & (lookup_rows >= 0)
        if usable.sum() != eligible.sum():
            raise ValueError('Eligible donor/recipient pair missing from the pooled cache')
        target = rows[usable]
        donor_rbp = np.asarray(pooled[lookup_rows[usable]], np.float32)
        x[target] = np.column_stack([
            np.asarray(rbp_mutant)[recipient[target]] - donor_rbp,
            np.asarray(bert_mutant)[recipient[target]] - np.asarray(bert_reference)[donor[usable]],
        ])
        columns = [f'n7_broken_rbp:{j:03d}' for j in range(rbp_mutant.shape[1])]
        columns += [f'n7_broken_bert:{j:03d}' for j in range(bert_mutant.shape[1])]
        summary = dict(audits[label])
        summary.update({'columns': len(columns), 'eligible_rows': int(usable.sum()),
                        'partition_rows': int(len(rows))})
        return x, columns, summary

    def eligibility(self, store, train_idx, eval_idx, label):
        plan, _ = self._plan(store)
        entry = plan[label]
        mask = np.zeros(len(store.rows), bool)
        mask[np.asarray(entry['rows'], int)] = np.asarray(entry['eligible'], bool)
        return mask


def primary_family_providers(store):
    return {family: FamilyProvider(family) for family in store.design['families']}


def control_providers(store, primary_family):
    """Every prospectively enumerated control, keyed by its registry name."""
    providers = {
        'n0_geometry': FamilyProvider('M0'),
        'n1_edit_descriptors': EditDescriptorProvider(),
        'n2_geometry_source_slopes': SourceSlopeProvider(),
        'n3_parent_identity': ParentIdentityProvider(),
        'n4_random_kmer_delta': RandomKmerProvider(),
        'n5_bijection_global': BijectionProvider(primary_family, strata=(), name='n5_bijection_global'),
        'n5_bijection_source': BijectionProvider(primary_family, strata=('dataset',), name='n5_bijection_source'),
        'n5_bijection_edit_band': BijectionProvider(primary_family, strata=('edit_band',), name='n5_bijection_edit_band'),
        'n5_bijection_parent': BijectionProvider(primary_family, strata=('biological_unit',), name='n5_bijection_parent'),
        'n8_bijection_source_edit_band': BijectionProvider(
            primary_family, strata=('dataset', 'edit_band'), name='n8_bijection_source_edit_band'),
        'n6_absolute_mutant': AbsoluteAlleleProvider('mutant'),
        'n6_absolute_reference': AbsoluteAlleleProvider('reference'),
        'm1_parent_aware_comparator': ParentAwareProvider(),
        'n7_broken_reference': BrokenReferenceProvider(),
        'n9_structure_bijection': BijectionProvider(
            primary_family, strata=('dataset', 'edit_band'), blocks=('structure_delta',),
            name='n9_structure_bijection'),
    }
    if 'structure_delta' not in store.design['families'][primary_family]:
        providers.pop('n9_structure_bijection')
    return providers


def block_removal_providers(store, primary_family):
    blocks = list(store.design['families'][primary_family])
    return {f'removal_{b}': BlockRemovalProvider(primary_family, b) for b in blocks if len(blocks) > 1}


BLOCK_REMOVAL_FAMILY = ('rbp_delta', 'bert_pooled_delta', 'structure_delta', 'processing_delta',
                        'motif_delta', 'trans_aligned', 'ranking_heads')
