"""Additional global similarity-family purge; original held menus are retained."""
from .common import np,TASKS,FOLDS
from src.generalization_crosscell_20261007.splits import strict_purge as original_purge

def attach_groups(frame,groups):
    assert 'measured_delta' not in frame
    assert groups.biological_component.is_unique
    mapping=groups.set_index('biological_component').similarity_component
    result=frame.copy();result['similarity_component']=result.biological_component.map(mapping)
    assert result.similarity_component.notna().all()
    return result

def strict_purge(frame,train,test):
    original=original_purge(frame,train,test)
    held_groups=set(frame.loc[test,'similarity_component'])
    selected=original & ~frame.similarity_component.isin(held_groups).to_numpy()
    assert not set(frame.loc[selected,'similarity_component'])&held_groups
    assert not (set(frame.loc[selected,'parent_sequence'])|set(frame.loc[selected,'mutant_sequence']))&(set(frame.loc[test,'parent_sequence'])|set(frame.loc[test,'mutant_sequence']))
    return selected

def outer_masks(frame,task,fold):
    assert task in TASKS and fold in FOLDS
    source,target=TASKS[task]
    test=(frame.cell_type.eq(target)&frame.held_parent_fold.eq(fold)).to_numpy()
    candidate=(frame.cell_type.eq(source)&frame.held_parent_fold.ne(fold)).to_numpy()
    train=strict_purge(frame,candidate,test)
    assert test.any() # Empty training is a reported feasibility failure, never silently repaired.
    assert set(frame.loc[train,'cell_type'])<={source}
    return train,test

def inner_masks(source,fold):
    assert source.cell_type.nunique()<=1
    validation=source.held_parent_fold.eq(fold).to_numpy()
    return strict_purge(source,~validation,validation),validation
