"""Independent supplied CORE text parser. Opens/closes no input and parses no effects."""
import csv
from decimal import Decimal,InvalidOperation
import hashlib
import io
import json
from . import verify as v
from .spec import *

STATUS_CORE='PASS_INDEPENDENT_SUPPLIED_CORE_AND_METADATA_CONTRACT_NOT_IO_OR_FIT_ADMISSION'


def _fold(token):
    assert type(token) is str and 0<len(token)<=32,'Invalid supplied fold token'
    try:value=Decimal(token)
    except InvalidOperation as error:raise AssertionError('Invalid supplied fold token') from error
    assert value.is_finite() and value==value.to_integral_value() and value in (0,1,2)
    return int(value)


def _parse_core(source,expected_core_rows):
    """Private row-count argument is used only by invented tests."""
    if type(source) is str:source=io.StringIO(source,newline='')
    assert hasattr(source,'__iter__'),'Supply CORE text or a caller-owned text stream'
    extra=object();missing=object()
    reader=csv.DictReader(source,restkey=extra,restval=missing,strict=True)
    header=reader.fieldnames
    assert type(header) is list and header and len(header)==len(set(header)),'Unique complete CORE header required'
    assert all(type(name) is str for name in header) and set(COLUMNS).issubset(header)
    previous=reader.reader.line_num
    assert previous==1,'One physical CORE header record required'
    all_ids=set();all_id_hash=hashlib.sha256();rows=[];positions=[];count=0
    for record in reader:
        physical=reader.reader.line_num
        assert physical==previous+1,'Exactly one physical record per original CORE row'
        previous=physical
        assert extra not in record and all(value is not missing for value in record.values()),'Exact original CORE row width required'
        assert set(record)==set(header)
        assert count<expected_core_rows,'Unexpected extra original CORE record'
        identity=record['intervention_id']
        assert type(identity) is str and identity and identity not in all_ids,'Unique nonempty full CORE IDs required'
        if count:all_id_hash.update(b'|')
        all_id_hash.update(identity.encode());all_ids.add(identity)
        if record['dataset']=='mikl_gse173098':
            selected={column:record[column] for column in COLUMNS}
            selected['held_parent_fold']=_fold(selected['held_parent_fold'])
            rows.append(selected);positions.append(count)
        count+=1
    assert count==expected_core_rows,'Incomplete original CORE record roster'
    assert reader.reader.line_num==count+1,'Blank or extra physical CORE records are not permitted'
    ids_hash=hashlib.sha256('|'.join(row['intervention_id'] for row in rows).encode()).hexdigest()
    projected=[[row[column] for column in COLUMNS] for row in rows]
    metadata_hash=hashlib.sha256(json.dumps(projected,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
    return {'rows':rows,'original_core_rows':positions,'all_core_rows':count,
        'all_core_ids_sha256':all_id_hash.hexdigest(),'row_ids_sha256':ids_hash,'metadata_sha256':metadata_hash,
        'one_csv_record_per_physical_line':True,'logical_metadata_fields':list(COLUMNS),
        'whole_file_raw_bytes_traversed':True,'unused_csv_fields_tokenized':True,
        'numeric_outcome_columns_parsed':False,'outcome_values_returned':False}


def _verify_core(value,source,counts,expected_ids,expected_core_rows):
    bundle,_=v._supplied(value)
    rebuilt=_parse_core(source,expected_core_rows)
    assert v._canonical(rebuilt)==v._canonical(bundle['metadata']),'Independent full CORE metadata/positions/ID roster differs from acquisition'
    result=v._check_supplied(value,counts,expected_ids,expected_core_rows)
    result.update({'original_core_position_alignment_independently_verified':True,
        'nonMikl_full_core_ID_roster_independently_verified':True,
        'source_CSV_metadata_derivation_independently_verified':True,
        'author_biological_lineage_independently_verified':False,
        'all_core_rows_independently_parsed':rebuilt['all_core_rows'],
        'all_core_ids_sha256':rebuilt['all_core_ids_sha256'],
        'independent_parser':'stdlib_csv_DictReader_selected_metadata_only',
        'unused_outcome_fields_numerically_converted':False,'supplied_stream_closed_here':False,
        'raw_CORE_byte_SHA_proven_here':False,'requires_guarded_original_CORE_SHA_and_Git_ownership_from_caller':True})
    return result


def verify_bundle_and_core(value,core_text_or_text_stream):
    """Fixed full CORE+Mikl verifier; no path, probe, loader or existing parser."""
    result=_verify_core(value,core_text_or_text_stream,COUNTS,ROW_IDS_SHA,ALL_CORE_ROWS)
    result['status']=STATUS_CORE
    result['requires_separate_owned_worker_admission_and_committed_result']=True
    return result
