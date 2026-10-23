"""In-memory CSV parsing only; never open project paths or import pandas."""
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import math
import struct
from src.generalization_knowncell_joint_implementation_20261022.contracts import ids_sha, metadata_sha
from .spec import METADATA_COLUMNS


def fold_value(value):
    assert isinstance(value, str) and 0 < len(value) <= 32
    try: number = Decimal(value)
    except InvalidOperation as error: raise AssertionError('Invalid inherited fold') from error
    assert number.is_finite() and number == number.to_integral_value() and number in (0, 1, 2)
    return int(number)


def header_indices(header, required):
    assert header and len(header) == len(set(header)), 'Duplicate CSV header'
    assert set(required) <= set(header), 'Missing declared column'
    return {key: header.index(key) for key in required}


def metadata_csv(text):
    """Traverse raw CSV tokens, retaining only ten metadata fields for Mikl.

    No unused column is numerically converted. Raw byte traversal and CSV
    tokenization include unused fields: this is not annotation-only byte IO.
    The physical-line assertion preserves the old skiprows(row+1) convention.
    """
    reader = csv.reader(text, strict=True)
    header = next(reader); indices = header_indices(header, METADATA_COLUMNS)
    assert reader.line_num == 1, 'Original skiprows requires one physical header line'
    previous_line = reader.line_num; seen = set(); all_ids = []; rows = []; positions = []; count = 0
    for source_index, values in enumerate(reader):
        assert reader.line_num == previous_line + 1, 'Multiline CSV is incompatible with original physical-row skiprows'
        previous_line = reader.line_num
        assert len(values) == len(header), 'Malformed CSV row width'
        intervention = values[indices['intervention_id']]
        assert intervention and intervention not in seen, 'Empty/duplicate original intervention ID'
        seen.add(intervention); all_ids.append(intervention); count += 1
        if values[indices['dataset']] != 'mikl_gse173098': continue
        row = {key: values[index] for key, index in indices.items()}
        row['held_parent_fold'] = fold_value(row['held_parent_fold'])
        rows.append(row); positions.append(source_index)
    return {'rows': rows, 'original_core_rows': positions, 'all_core_rows': count,
            'all_core_ids_sha256': hashlib.sha256('|'.join(all_ids).encode()).hexdigest(),
            'row_ids_sha256': ids_sha(rows), 'metadata_sha256': metadata_sha(rows),
            'one_csv_record_per_physical_line': True,
            'logical_metadata_fields': list(METADATA_COLUMNS),
            'whole_file_raw_bytes_traversed': True, 'unused_csv_fields_tokenized': True,
            'numeric_outcome_columns_parsed': False, 'outcome_values_returned': False}


def metadata_inventory_csv(text):
    reader = csv.DictReader(text, strict=True)
    assert reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames))
    rows = list(reader)
    assert all(None not in row and None not in row.values() for row in rows)
    return rows


def inventory_contract(metadata_rows, pairs, unmatched_contexts, saved_pairs, saved_unmatched):
    contexts = {}
    for row in metadata_rows: contexts.setdefault(row['parent_context_id'], []).append(row)
    expected = []
    for pair in pairs:
        groups = [contexts[pair['contexts'][cell]] for cell in ('CAD', 'Neuro-2a')]
        orders = [tuple(row['mutant_sequence'] for row in sorted(group, key=lambda r: r['intervention_id'])) for group in groups]
        expected.append((pair['biological_component'], pair['gene_fold'], pair['contexts']['CAD'],
                         pair['contexts']['Neuro-2a'], len(pair['mutant_sequences']), orders[0] == orders[1]))
    actual = []
    keys = {'biological_component', 'gene_fold', 'CAD_context', 'N2A_context', 'candidates', 'lexical_allele_order_matches'}
    for row in saved_pairs:
        assert set(row) == keys and row['lexical_allele_order_matches'] in ('True', 'False')
        actual.append((row['biological_component'], fold_value(row['gene_fold']), row['CAD_context'],
                       row['N2A_context'], int(row['candidates']), row['lexical_allele_order_matches'] == 'True'))
    assert len(actual) == len(set(actual)) and sorted(actual) == sorted(expected), 'Original exact-menu roster mismatch'
    expected_unmatched = [(contexts[context][0]['cell_type'], context, len(contexts[context])) for context in unmatched_contexts]
    actual_unmatched = []
    for row in saved_unmatched:
        assert set(row) == {'cell', 'parent_context_id', 'rows'}
        actual_unmatched.append((row['cell'], row['parent_context_id'], int(row['rows'])))
    assert len(actual_unmatched) == len(set(actual_unmatched)) and sorted(actual_unmatched) == sorted(expected_unmatched)
    return True


def pandas_effects(binary, pandas_module, metadata):
    """EXACT original deferred parser/options; no Python replacement float parser.

    The caller must admit unchanged pandas2.2.3 bytes, current-Python origins
    and invented original-parser options/results tests separately. Historical
    interpreter bitwise output parity is NOT claimed or required.
    """
    assert metadata['one_csv_record_per_physical_line'] is True
    rows = metadata['rows']; positions = metadata['original_core_rows']
    assert len(rows) == len(positions) and positions == sorted(set(positions))
    assert all(isinstance(value, int) and value >= 0 for value in positions)
    keep = set(value + 1 for value in positions)
    values = pandas_module.read_csv(binary, usecols=['intervention_id', 'measured_delta'],
                                    low_memory=False,
                                    skiprows=lambda number: number > 0 and number not in keep)
    ids = list(values.intervention_id)
    assert ids == [row['intervention_id'] for row in rows], 'Original selected ID/order mismatch'
    effects = values.measured_delta.to_numpy(float)
    assert len(effects) == len(rows) and all(math.isfinite(value) for value in effects)
    # Hash actual ORIGINAL-parser float64 values in their preserved row order.
    raw = b''.join(struct.pack('<d', value) for value in effects)
    return {'intervention_ids': ids, 'measured_delta': effects,
            'parsed_effects_float64_sha256': hashlib.sha256(raw).hexdigest(),
            'numeric_outcome_rows_admitted': len(rows),
            'parser': 'original_pandas_default_read_csv_low_memory_False_then_to_numpy_float',
            'pinned_pandas_currentPython_and_invented_original_parser_test_certificate_required': True,
            'old_interpreter_bitwise_parity_established': False,
            'original_truth_orientation': True}
