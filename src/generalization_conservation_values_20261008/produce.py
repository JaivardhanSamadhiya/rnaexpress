"""Preserve all 3,003 fixed intervals, pilot bytes, sites and complete-parent policy."""
import sys
from src.generalization_conservation_native_20261007 import parser
from src.generalization_conservation_native_20261007.produce import parent_availability
from src.generalization_conservation_native_20261007.transport import cached
from . import common as c


def add_interval(values, query, arrays, reason):
    for pos in range(query['start0'], query['end0']):
        key = (query['chrom'], pos)
        assert key not in values, 'Duplicate requested coordinate'
        scores = {track: arrays[track].get(pos) if arrays is not None else None for track in c.old.TRACKS}
        values[key] = {'scores': scores, 'query_key': query['key'],
            'missing_reason': None if all(v is not None for v in scores.values()) else ('source_score_absent' if arrays is not None else reason)}


def run(root_start=False):
    assert root_start, 'Root explicitly starts separately frozen full annotations'
    manifest = c.certify()
    assert not (c.OUT / 'value_extraction_receipt.json').exists()
    roster = c.old.read(c.old.OUT / 'value_query_roster.json')
    pilot = c.old.read(c.pilot.OUT / 'pilot_receipt.json')
    assert pilot['available_chromosomes'] == 20 and len(pilot['records']) == 20
    pilot_records = {record['key']: record for record in pilot['records']}
    headers = {record['chrom']: record['observed_source_headers'] for record in pilot['records']}
    remaining = [query for query in roster if query['key'] not in pilot_records]
    assert remaining == c.old.read(c.OUT / 'remaining_query_roster.json') and len(remaining) == 2983
    from .transport import Client
    client = Client([q['url'] for q in remaining], manifest['previous_schema_and_pilot_acquired_bytes'])
    values, records = {}, []
    for index, query in enumerate(roster):
        is_pilot = query['key'] in pilot_records
        path = c.ROOT / pilot_records[query['key']]['body_path'] if is_pilot else c.ART / 'values' / (query['key'] + '.json')
        body, response = cached(path, query['url']) if is_pilot else client.get(query['url'], path)
        assert response is not None
        record = {**query, 'reused_pilot': is_pilot, 'status': 'UNAVAILABLE_VALUE_RESPONSE',
            'expected_observed_headers': headers[query['chrom']],
            'body_path': path.relative_to(c.ROOT).as_posix() if response['sha256'] else None, 'body_sha256': response['sha256'],
            'response_receipt': path.with_name(path.name + '.receipt.json').relative_to(c.ROOT).as_posix(),
            'response_receipt_sha256': c.old.sha(path.with_name(path.name + '.receipt.json')),
            'response_receipt_birth_sha256': c.old.sha(path.with_name(path.name + '.receipt.json.sha256.json'))}
        arrays = None
        reason = response.get('failure', 'Missing complete public body')
        if body is not None:
            try:
                arrays, groups = parser.values(body, query, headers[query['chrom']])
                record.update(status='ADMITTED_EXACT_ORDERED_DUAL_TRACK_RESPONSE', source_metadata_groups=groups)
            except parser.SchemaError as error:
                reason = 'Unavailable strict values or source-header drift: ' + str(error)
        if arrays is None: record['missing_reason'] = reason
        add_interval(values, query, arrays, reason)
        records.append(record)
        if index % 100 == 0 or index == len(roster) - 1:
            print('Fixed native annotations', index + 1, '/', len(roster), 'last', record['status'], flush=True)
    sites, rows = c.old.reference_inventory()
    assert len(roster) == 3003 and set(values) == {(s['chrom'], s['position0']) for s in sites}
    parents = parent_availability(rows, values)
    assert len(parents) == 3022 and sum(p['original_rows'] for p in parents) == 26258
    assert len({r['parent_context_id'] for r in rows}) == 5436
    c.jsave(c.OUT / 'site_annotation_values.json', [{**s, **values[s['chrom'], s['position0']]} for s in sites])
    c.jsave(c.OUT / 'parent_annotation_availability.json', parents)
    c.certify()
    c.jsave(c.OUT / 'value_extraction_receipt.json', {'status': 'COMPLETED_OBSERVED_HEADER_SITE_EXTRACTION_NO_FEATURES_OR_MODELS',
        'value_manifest_sha256': c.old.sha(c.MANIFEST), 'response_records': records,
        'pilot_receipt_sha256': c.old.sha(c.pilot.OUT / 'pilot_receipt.json'),
        'original_rows': 26258, 'original_menus': 5436, 'parents': 3022, 'exact_sites': 15132,
        'complete_annotation_parents': sum(p['native_annotation_complete_parent'] for p in parents),
        'new_value_requests_this_execution': client.new_requests, 'reused_pilot_responses': 20,
        'acquired_bytes_including_schemas_and_pilots': client.total,
        'source_headers_learned_or_updated_from_remaining_responses': False,
        'parent_policy_shared_with_preserved_original_implementation': True,
        'features_produced': False, 'outcomes_read': False, 'models_fit': 0,
        'physical_SQL_storage_certified': False, 'atomic_provider_snapshot_certified': False,
        'values_are_browser_API_representation_not_original_full_precision': True,
        'files': {p.relative_to(c.ROOT).as_posix(): c.old.sha(p) for p in (c.OUT / 'site_annotation_values.json', c.OUT / 'parent_annotation_availability.json')}})
    print('Complete original site inventory extracted; independent join and parent-policy replay pending', flush=True)


if __name__ == '__main__':
    run('--root-start' in sys.argv[1:])
