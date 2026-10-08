"""Outcome-free fixed-column and missingness contracts."""
import math
def addon(track,raw,native):
    assert len(raw)==len(native)==8
    if track=='raw':return list(raw)
    if track=='native':return list(native)
    if track=='duplicate_raw':return list(raw)+list(raw)
    assert track=='combined'
    return list(raw)+list(native)

def validate_blocks(rows,blocks):
    assert len(rows)==len(blocks)
    assert len({r['intervention_id'] for r in rows})==len(rows)
    assert [r['intervention_id'] for r in rows]==[b['intervention_id'] for b in blocks]
    policies={}
    for row,block in zip(rows,blocks):
        assert isinstance(block['annotation_complete_parent'],bool)
        key=(row['dataset'],block['parent_id']);flag=block['annotation_complete_parent']
        assert key not in policies or policies[key]==flag;policies[key]=flag
        for name in ('raw_position8','reference_conservation8'):
            value=block[name];assert len(value)==8
            assert all(type(x) in (int,float) and math.isfinite(x) for x in value)
            assert all(abs(sum(value[k:k+4]))<1e-12 for k in (0,4))
            if not flag:assert all(x==0 for x in value)
    return policies
