"""Twenty fixed intervals; observed headers are not physical SQL certification."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from src.generalization_conservation_native_20261007 import common as original, parser

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_conservation_header_pilot_20261008'
OUT, ART = ROOT / 'results' / NS, ROOT / 'artifacts' / NS
TRACKS = original.TRACKS


def save(path, payload):
    path = Path(path).resolve()
    assert any(path.is_relative_to(p.resolve()) for p in (OUT, ART))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(payload)


def jsave(path, value):
    save(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def logical_schema(payload, track, expected_type):
    obj = parser.pairs(payload)
    parser.check(not parser.occurrences(obj, 'error') and not parser.occurrences(obj, 'maxItemsLimit'), 'Schema error/truncation')
    parser.check(parser.one(obj, 'genome') == 'mm10' and parser.one(obj, 'track') == track, 'Wrong logical source')
    columns = parser.one(obj, 'columnTypes')
    parser.check(isinstance(columns, list) and not isinstance(columns, parser.Object), 'Invalid columns')
    rows = [parser.regular(row) for row in columns]
    parser.check([row.get('name') for row in rows] == ['chrom', 'start', 'end', 'value'], 'Wrong logical output names')
    parser.check([row.get('jsonType') for row in rows] == ['string', 'number', 'number', 'number'], 'Wrong logical output types')
    types = parser.occurrences(obj, 'type')
    parser.check(bool(types) and all(t == expected_type for t in types), 'Wrong exact logical track type')
    table = parser.occurrences(obj, 'table')
    parser.check(not table or all(t == track for t in table), 'Changed logical source table')
    tm, stamp = parser.one(obj, 'dataTime'), parser.one(obj, 'dataTimeStamp')
    parser.moment(tm, stamp)
    # This generation explicitly makes no splitTable or physical-SQL assertion.
    return {'track': track, 'trackType': expected_type, 'logical_dataTime': tm, 'logical_dataTimeStamp': stamp,
            'physical_SQL_storage_certified': False}


def observed(payload, query, types):
    obj = parser.pairs(payload)
    headers = {}
    fields = ('track', 'dataTime', 'dataTimeStamp', 'trackType')
    parts = {key: parser.occurrences(obj, key) for key in fields}
    parser.check(all(len(value) == 2 for value in parts.values()), 'Exactly two source header groups required')
    parser.check(parts['track'] == list(TRACKS), 'Wrong ordered tracks')
    for index, track in enumerate(TRACKS):
        header = {key: parts[key][index] for key in ('dataTime', 'dataTimeStamp', 'trackType')}
        parser.check(header['trackType'] == types[track], 'Changed exact logical type')
        parser.moment(header['dataTime'], header['dataTimeStamp'])
        headers[track] = header
    # Candidate headers are observed, not trusted as pre-existing facts. The
    # unchanged strict parser verifies their ordered binding to arrays/intervals.
    arrays, groups = parser.values(payload, query, headers)
    return headers, arrays, groups


def check_design():
    path = OUT / 'pilot_manifest.json'
    assert subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT) == path.read_bytes(), 'Commit exact value-pilot freeze'
    value = original.read(path)
    assert value['status'] == 'FROZEN_VALUE_BEARING_CONSERVATION_HEADER_PILOT'
    for name, expected in value['files'].items():
        candidate = (ROOT / name).resolve()
        assert candidate.is_relative_to(ROOT.resolve()) and original.sha(candidate) == expected, name
    for name in value['own_files']:
        assert subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT) == (ROOT / name).read_bytes(), name
    original.certify(original.SCHEMA_DESIGN)
    return value


def run(root_start=False):
    assert root_start, 'Root explicitly authorizes value-bearing fixed pilot'
    manifest = check_design()
    assert not (OUT / 'pilot_receipt.json').exists()
    queries = original.read(OUT / 'pilot_query_roster.json')
    all_queries = original.read(original.OUT / 'value_query_roster.json')
    selected = {}
    for query in all_queries:
        selected.setdefault(query['chrom'], query)
    assert queries == list(selected.values()) and len(queries) == 20 and len(all_queries) == 3003
    spec = original.read(original.OUT / 'extraction_spec.json')
    types = spec['expected_track_types']
    metadata = original.read(original.OUT / 'metadata_admission_receipt.json')
    schemas = {}
    for track in TRACKS:
        record = metadata['logical'][track]
        path = ROOT / record['body_path']
        assert original.sha(path) == record['body_sha256']
        schemas[track] = logical_schema(path.read_bytes(), track, types[track])
    from .transport import Client
    client = Client([q['url'] for q in queries], manifest['previous_schema_acquired_bytes'])
    records = []
    for query in queries:
        path = ART / 'pilot' / (query['key'] + '.json')
        body, response = client.get(query['url'], path)
        record = {**query, 'available': False, 'body_path': path.relative_to(ROOT).as_posix() if response['sha256'] else None,
            'body_sha256': response['sha256'], 'response_receipt': path.with_name(path.name + '.receipt.json').relative_to(ROOT).as_posix(),
            'response_receipt_sha256': original.sha(path.with_name(path.name + '.receipt.json')),
            'response_receipt_birth_sha256': original.sha(path.with_name(path.name + '.receipt.json.sha256.json'))}
        if body is not None:
            try:
                headers, arrays, groups = observed(body, query, types)
                record.update(available=True, observed_source_headers=headers,
                    score_positions={track: len(values) for track, values in arrays.items()}, ordered_source_groups=groups)
            except parser.SchemaError as error:
                record['failure'] = 'Strict pilot unavailable: ' + str(error)
        else:
            record['failure'] = response.get('failure', 'Missing complete public body')
        records.append(record)
        print('Fixed value-header pilot', query['chrom'], 'available' if record['available'] else 'unavailable', flush=True)
    check_design()
    jsave(OUT / 'pilot_receipt.json', {'status': 'COMPLETED_FIXED_VALUE_HEADER_PILOT', 'records': records,
        'logical_output_schemas': schemas, 'available_chromosomes': sum(row['available'] for row in records),
        'annotation_values_read': True, 'outcomes_read': False, 'models_fit': 0,
        'pilot_manifest_sha256': original.sha(OUT / 'pilot_manifest.json'),
        'new_requests': client.new_requests, 'acquired_bytes_including_old_schemas': client.total,
        'remaining_value_requests_authorized': False, 'physical_SQL_storage_certified': False,
        'atomic_provider_snapshot_certified': False, 'live_server_binary_version_certified': False,
        'values_are_browser_API_representation_not_original_full_precision': True,
        'no_retries_or_alternative_pilots': True, 'old_failed_schema_stage_unchanged': True})


if __name__ == '__main__':
    run('--root-start' in sys.argv[1:])
