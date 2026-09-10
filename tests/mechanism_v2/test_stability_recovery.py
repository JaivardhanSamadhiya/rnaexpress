import io
import pytest
from src.mechanism_v2.stability_recovery import (merge_exact,extract_insert,
    FORWARD,REVERSE,reverse_complement,fastq_records)


def test_exact_paired_overlap_and_primers():
    insert='ACGTGCTAGTCAGTACGATCGATCGTACGATGCAGTACGACTAGCATGCTAGCACTGA'
    whole=FORWARD+insert+REVERSE
    r1=whole[:-8];r2=reverse_complement(whole[30:])
    merged,reason=merge_exact(r1,'I'*len(r1),r2,'I'*len(r2))
    assert reason=='merged' and merged==whole
    assert extract_insert(merged)==(insert,'accepted')


def test_disagreement_is_not_silently_corrected():
    s='ACGTGCTAGTCAGTACGATCGATCGTACGATGCAGTACGACTAGCATGCTAGCACTGA'
    r2=reverse_complement(s[10:])
    r2=r2[:24]+('A' if r2[24]!='A' else 'C')+r2[25:]
    assert merge_exact(s,'I'*len(s),r2,'I'*len(r2))[0] is None


def test_missing_reverse_primer_rejected():
    assert extract_insert(FORWARD+'A'*115)[0] is None
    assert merge_exact('A'*80,'I'*80,'T'*80,'I'*80)[1]=='ambiguous_overlap'


def test_fastq_truncation_rejected():
    with pytest.raises(ValueError):list(fastq_records(io.StringIO('@id\nACG\n+\nII\n')))
