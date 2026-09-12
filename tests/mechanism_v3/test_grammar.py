import numpy as np
import pandas as pd
import pytest

from src.mechanism_v3 import grammar
from src.mechanism_v3.io import open_holdout


def test_grammar_delta_is_mutant_minus_reference():
    elements = [{'id': 'x', 'motif': 'AT', 'polarity': 1}]
    assert grammar.grammar_delta('GG', 'ATAT', elements) == 2.0
    assert grammar.grammar_delta('ATAT', 'GG', elements) == -2.0


def test_scrambled_null_reverses_motif_and_flips_polarity():
    elements = [{'id': 'let', 'motif': 'ACGT', 'polarity': 1}]
    null = grammar.scrambled_elements(elements)
    assert null[0]['motif'] == 'TGCA'
    assert null[0]['polarity'] == -1


def test_size_baseline_prefers_smaller_edits():
    rows = pd.DataFrame({'edit_cost': [1, 10, 100]})
    scores = grammar.size_baseline(rows)
    assert scores[0] > scores[1] > scores[2]


def test_load_grammar_dictionary_is_nonempty_and_hashed():
    design = grammar.load_grammar()
    assert len(design['elements']) >= 3
    assert len(design['config_sha256']) == 64
    assert design['primary_estimator'] == 'outcome_free_grammar_finite_difference'


def test_holdout_remains_sealed():
    with pytest.raises(PermissionError, match='sealed'):
        open_holdout()


def test_non_overlapping_motif_count():
    assert grammar.count_motif('AAAA', 'AA') == 2
    assert grammar.count_motif('ACGT', 'AA') == 0
