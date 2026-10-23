"""Invented CSVs and original deferred pandas expression; no package imports."""
import csv
import io
import math
import struct

TRICKY = ('0.1', '0.30000000000000004', '1.0000000000000002',
          '2.2250738585072014e-308', '1.7976931348623157e308', '5e-324',
          '-0.0', '-2.5e+12', '9007199254740993', '1e-300')


def csv_text(rows, newline='\n'):
    text = io.StringIO(newline='')
    writer = csv.writer(text, lineterminator=newline)
    writer.writerow(('intervention_id', 'measured_delta', 'unused'))
    writer.writerows(rows)
    return text.getvalue()


def metadata(text, positions):
    """Invented metadata prerequisite; never numerically converts CSV values."""
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    header = next(reader)
    assert len(set(header)) == len(header) and set(header) == {'intervention_id', 'measured_delta', 'unused'}
    assert reader.line_num == 1
    previous = 1; rows = []; seen = set()
    for row in reader:
        assert reader.line_num == previous + 1, 'Original mask requires one physical line per record'
        previous = reader.line_num
        assert len(row) == len(header), 'Malformed width'
        intervention = row[header.index('intervention_id')]
        assert intervention and intervention not in seen, 'Empty/duplicate original IDs'
        seen.add(intervention); rows.append(intervention)
    assert positions == sorted(set(positions)) and positions
    assert all(type(i) is int and 0 <= i < len(rows) for i in positions)
    return {'rows': [{'intervention_id': rows[i]} for i in positions],
            'original_core_rows': positions, 'one_csv_record_per_physical_line': True}


def original_pandas(text, pandas_module, selected):
    """The original common.load(outcomes=True) parsing call, on invented text."""
    keep = set(value + 1 for value in selected['original_core_rows'])
    values = pandas_module.read_csv(io.StringIO(text), usecols=['intervention_id', 'measured_delta'],
                                   low_memory=False,
                                   skiprows=lambda number: number > 0 and number not in keep)
    assert list(values.intervention_id) == [r['intervention_id'] for r in selected['rows']]
    effects = values.measured_delta.to_numpy(float)
    assert all(math.isfinite(value) for value in effects)
    return list(values.intervention_id), effects


def float_bytes(values):
    return b''.join(struct.pack('<d', value) for value in values)


def successful_cases():
    # Disallowed selected numeric strings remain harmless when outside the old
    # physical-row keep mask; they are deliberately not converted by metadata.
    rows = [('skip_first', 'not_a_number', 'comma,quoted')]
    for i, value in enumerate(TRICKY):
        rows.extend([(f'kept_{i:02}', value, 'unused'), (f'skip_{i:02}', 'Infinity', 'unused')])
    rows.append(('last_kept', '2.5', 'tail'))
    positions = list(range(1, 2 * len(TRICKY), 2)) + [len(rows)-1]
    return [('tricky_lf', csv_text(rows), positions),
            ('tricky_crlf', csv_text(rows, '\r\n'), positions),
            ('first_and_last', csv_text([('first', '1.25', 'x'), ('middle', 'bad', 'x'), ('last', '-2.5', 'x')]), [0, 2])]


def rejected_csv_cases():
    return [
        ('duplicate_ids', csv_text([('a','1','x'),('a','2','x')]), [0]),
        ('empty_id', csv_text([('','1','x')]), [0]),
        ('multiline', csv_text([('a','1','multi\nline')]), [0]),
        ('duplicate_header', 'intervention_id,measured_delta,intervention_id\na,1,a\n', [0]),
        ('bad_width', 'intervention_id,measured_delta,unused\na,1\n', [0]),
        ('bad_quote', 'intervention_id,measured_delta,unused\na,1,"unterminated\n', [0]),
    ]


def rejected_numeric_cases():
    return [(word, csv_text([('a', word, 'x')]), [0]) for word in
            ('bad_float', 'NaN', 'inf', '-inf', '', '1e309')]
