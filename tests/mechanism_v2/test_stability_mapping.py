from src.mechanism_v2.stability_mapping import sequence_index,map_variant,gc
from src.mechanism_v2.stability_recovery import FORWARD,REVERSE,reverse_complement


def test_variant_mapping_both_strands_and_gc_guard():
    wt='ACGTGCTAGTCAGTACGATCGATCGTACGATGCAGTACGACTAGCATGCTAGCACTGA'
    position=22;alt='A' if wt[position]!='A' else 'G'
    mutant=wt[:position]+alt+wt[position+1:]
    row={'strand':'+','Start':100+position,'Stop':101+position,
        'ReferenceAllele':wt[position],'AlternateAllele':alt,
        'GCcontent_WT':gc(FORWARD+wt+REVERSE),'GCcontent_mt':gc(FORWARD+mutant+REVERSE)}
    index=sequence_index([wt,mutant]);supported={wt,mutant}
    matches,reason=map_variant(row,wt,100,index,supported)
    assert matches==[(wt,mutant,position)] and reason=='matched'
    row.update(strand='-',Start=100+len(wt)-position-1,Stop=100+len(wt)-position)
    assert map_variant(row,reverse_complement(wt),100,index,supported)[0]==matches
    row['GCcontent_WT']=0.9
    assert not map_variant(row,reverse_complement(wt),100,index,supported)[0]
