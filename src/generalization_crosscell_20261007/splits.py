"""No held target cell, gene/component or exact allele enters training."""
from .common import np,TASKS,FOLDS
from src.cross_assay_20260927.models import purge


def strict_purge(frame,train,test):
    selected=purge(frame,train,test)
    held=frame.loc[test];training=frame.loc[selected]
    held_genes=set(held.gene_transcript.astype(str).str.strip().str.upper())
    train_genes=set(training.gene_transcript.astype(str).str.strip().str.upper())
    assert not train_genes&held_genes,'Gene identities must be globally grouped'
    assert not (set(training.parent_sequence)|set(training.mutant_sequence)) & (set(held.parent_sequence)|set(held.mutant_sequence))
    return selected


def outer_masks(frame,task,fold):
    assert task in TASKS and fold in FOLDS
    source,target=TASKS[task]
    test=(frame.cell_type.eq(target)&frame.held_parent_fold.eq(fold)).to_numpy()
    train=(frame.cell_type.eq(source)&frame.held_parent_fold.ne(fold)).to_numpy()
    train=strict_purge(frame,train,test)
    assert test.any() and train.any()
    assert set(frame.loc[train,'cell_type'])=={source}
    assert set(frame.loc[test,'cell_type'])=={target}
    return train,test


def inner_masks(source,fold):
    assert source.cell_type.nunique()==1
    validation=source.held_parent_fold.eq(fold).to_numpy()
    training=strict_purge(source,~validation,validation)
    assert training.any() and validation.any()
    return training,validation
