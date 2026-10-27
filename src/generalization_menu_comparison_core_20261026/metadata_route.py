"""Parse already supplied streams into outcome-free four-assay metadata.

No path opening, gzip handling, project loader, admission or fitting. The caller
must separately admit/hash the exact original archives and enforce resources.
CSV tokenization traverses unused outcome fields, without converting/returning
them. This is not annotation-only byte I/O.
"""
import csv
from collections import Counter
from .layout import FIELDS, STUDIES, metadata, require

INDEX_FIELDS = ('intervention_id','dataset','parent_context_id','biological_component')
ARCHIVE_FIELDS = ('candidate_id','dataset','parent_context_id','biological_component',
                  'parent_sequence','mutant_sequence','feature_row','replicate_slot','replicate_id')
REPLICATE_IDS = {
    STUDIES[0]:(1,2,3,4,5,6,7,8,9,11,12,13,14,15),
    STUDIES[1]:(1,2,3), STUDIES[2]:(1,2,3,4), STUDIES[3]:(1,2),
}


def _header(reader, wanted, exact=False):
    header = next(reader)
    require(len(header) == len(set(header)), 'duplicate CSV header')
    require(set(wanted) <= set(header), 'missing declared metadata column')
    if exact:require(set(header) == set(wanted), 'row index must contain only four metadata fields')
    return header, {key:header.index(key) for key in wanted}


def _index(raw, name):
    require(isinstance(raw,str) and 0 < len(raw) <= 10 and
            all('0' <= c <= '9' for c in raw), 'invalid '+name)
    return int(raw)


def parse_streams(row_index_text, archive_text, *, expected_rows=26258):
    """Return metadata only. Small expected_rows values support invented tests.

    This parameter is not an admission switch. Future actual controllers must
    hard-bind26258 rows, original archive hashes and the fixed per-study counts.
    No values from measured_localization_value or other outcome columns are
    inspected, converted, reconstructed or returned.
    """
    require(isinstance(expected_rows,int) and expected_rows > 0, 'bad expected row count')
    reader = csv.reader(row_index_text,strict=True)
    header,positions = _header(reader,INDEX_FIELDS,exact=True)
    index = []; seen = set()
    for values in reader:
        require(len(values) == len(header), 'bad row-index width')
        row = {key:values[pos] for key,pos in positions.items()}
        require(row['intervention_id'] and row['intervention_id'] not in seen, 'empty/duplicate row-index ID')
        require(row['dataset'] in STUDIES, 'unknown row-index study')
        seen.add(row['intervention_id']);index.append(row)
        require(len(index) <= expected_rows, 'too many row-index records')
    require(len(index) == expected_rows, 'row-index count differs')
    reader = csv.reader(archive_text,strict=True)
    header,positions = _header(reader,ARCHIVE_FIELDS)
    rows = [None]*expected_rows;slots = [set() for _ in index];count = 0
    for values in reader:
        require(len(values) == len(header), 'bad archive width')
        raw = {key:values[pos] for key,pos in positions.items()}
        i = _index(raw['feature_row'],'feature row')
        require(0 <= i < expected_rows, 'feature-row index out of range')
        row = {'intervention_id':raw['candidate_id'],
               **{key:raw[key] for key in FIELDS if key != 'intervention_id'}}
        require({key:row[key] for key in INDEX_FIELDS} == index[i], 'archive/index order or metadata mismatch')
        if rows[i] is None:rows[i] = row
        else:require(rows[i] == row, 'repeated candidate metadata differs')
        labels = REPLICATE_IDS[row['dataset']]
        slot = _index(raw['replicate_slot'],'replicate slot')
        rep = _index(raw['replicate_id'],'replicate ID')
        require(0 <= slot < len(labels) and labels[slot] == rep, 'unexpected replicate alias')
        require(slot not in slots[i], 'duplicate candidate/replicate slot')
        slots[i].add(slot);count += 1
    require(all(row is not None for row in rows), 'candidate metadata missing from archive')
    require(all(slots[i] == set(range(len(REPLICATE_IDS[row['dataset']])))
                for i,row in enumerate(rows)), 'incomplete recorded replicate-slot metadata')
    rows = metadata(rows)
    counts = dict(Counter(row['dataset'] for row in rows))
    require(set(counts) == set(STUDIES), 'all four assays required')
    return {'status':'PARSED_SUPPLIED_STREAMS_NOT_PROJECT_ADMISSION',
            'rows':rows,'study_counts':counts,'archive_records_tokenized':count,
            'unused_outcome_tokens_traversed':True,'numeric_outcome_columns_parsed':False,
            'numeric_outcomes_returned':False,'feature_values_read':False,'fits':0}
