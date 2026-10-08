"""Exact original nonlinear source masks and complete same-cell target menus."""
from .common import np, TASKS, FOLDS
from src.generalization_nonlinear_crosscell_20261007.splits import outer_masks
from src.generalization_knowncell_20261007.splits import exact_menu_pairs

def masks(frame, task, fold):
    assert task in TASKS and fold in FOLDS
    cell, source_task = TASKS[task]
    train, opposite = outer_masks(frame, source_task, fold)
    target = (frame.cell_type.eq(cell) & frame.held_parent_fold.eq(fold)).to_numpy()
    assert target.any() and not (train & target).any()
    source, held = frame.loc[train], frame.loc[target]
    assert not set(source.biological_component) & set(held.biological_component)
    assert not set(source.gene_transcript.str.strip().str.upper()) & set(held.gene_transcript.str.strip().str.upper())
    assert not (set(source.parent_sequence) | set(source.mutant_sequence)) & (set(held.parent_sequence) | set(held.mutant_sequence)), 'Same-cell allele overlap blocks reuse; no new purge/refit'
    sizes = frame.groupby('parent_context_id').size(); target_sizes = held.groupby('parent_context_id').size()
    assert (target_sizes == sizes.reindex(target_sizes.index)).all(), 'No partial candidate menus'
    assert set(source.cell_type) == set(held.cell_type) == {cell}
    return train, target, opposite
