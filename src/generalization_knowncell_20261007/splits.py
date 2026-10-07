"""Prove same-cell target safety for the exact already-fitted source mask."""
from .common import np, TASKS, FOLDS
from src.generalization_crosscell_20261007.splits import outer_masks


def masks(frame, task, fold):
    assert task in TASKS and fold in FOLDS
    cell, source_task = TASKS[task]
    train, opposite = outer_masks(frame, source_task, fold)
    target = (frame.cell_type.eq(cell) & frame.held_parent_fold.eq(fold)).to_numpy()
    assert target.any() and not (train & target).any()
    training, held = frame.loc[train], frame.loc[target]
    assert not set(training.biological_component) & set(held.biological_component)
    assert not set(training.gene_transcript.str.strip().str.upper()) & set(held.gene_transcript.str.strip().str.upper())
    assert not (set(training.parent_sequence) | set(training.mutant_sequence)) & (set(held.parent_sequence) | set(held.mutant_sequence)), "Same-cell allele overlap: reuse ineligible; union-purge needs separate fits"
    global_sizes, target_sizes = frame.groupby("parent_context_id").size(), held.groupby("parent_context_id").size()
    assert (target_sizes == global_sizes.reindex(target_sizes.index)).all(), "No partial candidate menu"
    assert set(training.cell_type) == set(held.cell_type) == {cell}
    return train, target, opposite


def exact_menu_pairs(frame):
    """Sequence-only pairing, with no intersection trimming or outcomes."""
    index = {}
    for context, group in frame.groupby("parent_context_id", sort=True):
        assert group.parent_sequence.nunique() == group.biological_component.nunique() == group.cell_type.nunique() == 1
        assert group.mutant_sequence.is_unique, "Duplicate alleles make pairing ambiguous"
        key = (group.biological_component.iloc[0], group.parent_sequence.iloc[0], tuple(sorted(group.mutant_sequence)))
        cell = group.cell_type.iloc[0]
        assert cell not in index.setdefault(key, {}), "Duplicate exact menus in one cell"
        index[key][cell] = (context, group)
    records, excluded = [], []
    for (component, parent, alleles), cells in sorted(index.items()):
        if set(cells) != {"CAD", "Neuro-2a"}:
            excluded.extend({"cell": cell, "parent_context_id": context, "rows": len(group)} for cell, (context, group) in cells.items())
            continue
        cad, n2a = cells["CAD"], cells["Neuro-2a"]
        assert cad[1].held_parent_fold.nunique() == n2a[1].held_parent_fold.nunique() == 1
        assert cad[1].held_parent_fold.iloc[0] == n2a[1].held_parent_fold.iloc[0]
        lexical = [tuple(group.sort_values("intervention_id").mutant_sequence) for _, group in (cad, n2a)]
        records.append({"biological_component": component, "gene_fold": int(cad[1].held_parent_fold.iloc[0]),
            "CAD_context": cad[0], "N2A_context": n2a[0], "candidates": len(alleles),
            "lexical_allele_order_matches": lexical[0] == lexical[1]})
    return records, excluded
