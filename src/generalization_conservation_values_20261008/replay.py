"""Reconstruct sites and complete-parent policy independently of producer arrays."""
from collections import defaultdict
from src.generalization_conservation_native_20261007 import parser
from . import common as c


def direct_scores(payload, query):
    obj = parser.pairs(payload)
    result = {}
    for track in c.old.TRACKS:
        entries = [parser.regular(row) for row in parser.one(obj, track)]
        for pos in range(query['start0'], query['end0']):
            matches = [row['value'] for row in entries if row['chrom'] == query['chrom'] and row['start'] <= pos < row['end']]
            assert len(matches) <= 1
            result[query['chrom'], pos, track] = float(matches[0]) if matches else None
    return result


def parent_status(rows, scores):
    coordinate_complete = True
    required = set()
    for row in rows:
        if row['mapping_status'] != c.old.MAPPED or len(row['edited_site_coordinates']) != len(row['edit_positions0']):
            coordinate_complete = False
        for site in row['edited_site_coordinates']:
            required.add((site['chrom'], site['genomic_position0']))
    missing = {key for key in required if any(scores.get((*key, track)) is None for track in c.old.TRACKS)}
    return {'coordinates_complete_parent': coordinate_complete, 'required_unique_sites': len(required),
        'missing_unique_sites': len(missing), 'native_annotation_complete_parent': coordinate_complete and bool(required) and not missing}


def run():
    c.certify()
    done = c.old.read(c.OUT / 'value_extraction_receipt.json')
    assert done['status'] == 'COMPLETED_OBSERVED_HEADER_SITE_EXTRACTION_NO_FEATURES_OR_MODELS'
    assert done['value_manifest_sha256'] == c.old.sha(c.MANIFEST)
    for name, digest in done['files'].items(): assert c.old.sha(c.ROOT / name) == digest, name
    roster = c.old.read(c.old.OUT / 'value_query_roster.json')
    pilot = c.old.read(c.pilot.OUT / 'pilot_receipt.json')
    pilots = {row['key']: row for row in pilot['records']}
    headers = {row['chrom']: row['observed_source_headers'] for row in pilot['records']}
    records = done['response_records']
    assert len(records) == len(roster) == 3003 and [r['key'] for r in records] == [q['key'] for q in roster]
    scores = {}
    for query, record in zip(roster, records):
        reused = query['key'] in pilots
        assert record['url'] == query['url'] and record['reused_pilot'] == reused
        assert record['expected_observed_headers'] == headers[query['chrom']]
        path = c.ROOT / pilots[query['key']]['body_path'] if reused else c.ART / 'values' / (query['key'] + '.json')
        receipt = path.with_name(path.name + '.receipt.json')
        assert record['response_receipt'] == receipt.relative_to(c.ROOT).as_posix()
        assert c.old.sha(receipt) == record['response_receipt_sha256']
        birth = receipt.with_name(receipt.name + '.sha256.json')
        assert c.old.sha(birth) == record['response_receipt_birth_sha256']
        assert c.old.read(birth)['receipt_sha256'] == c.old.sha(receipt)
        response = c.old.read(receipt)
        assert response['url'] == query['url']
        if response['sha256'] is None:
            assert not path.exists() and record['body_path'] is None and record['body_sha256'] is None
        else:
            assert record['body_path'] == path.relative_to(c.ROOT).as_posix()
            assert c.old.sha(path) == response['sha256'] == record['body_sha256'] and path.stat().st_size == response['bytes']
        if response.get('oversize_prefix_path'):
            prefix = path.with_name(path.name + '.oversize_prefix.bin')
            assert response['oversize_prefix_path'] == prefix.name and c.old.sha(prefix) == response['oversize_prefix_sha256']
        direct = {}
        if response['http_status'] == 200 and not response.get('failure'):
            payload = path.read_bytes()
            try:
                _, groups = parser.values(payload, query, headers[query['chrom']])
                assert record['status'] == 'ADMITTED_EXACT_ORDERED_DUAL_TRACK_RESPONSE'
                assert record['source_metadata_groups'] == groups
                direct = direct_scores(payload, query)
            except parser.SchemaError:
                assert record['status'] == 'UNAVAILABLE_VALUE_RESPONSE'
        else:
            assert record['status'] == 'UNAVAILABLE_VALUE_RESPONSE'
        for pos in range(query['start0'], query['end0']):
            for track in c.old.TRACKS:
                key = (query['chrom'], pos, track)
                assert key not in scores
                scores[key] = direct.get(key)
    sites, rows = c.old.reference_inventory()
    saved = c.old.read(c.OUT / 'site_annotation_values.json')
    assert [(s['chrom'], s['position0'], s['reference'], s['alternates']) for s in saved] == [(s['chrom'], s['position0'], s['reference'], s['alternates']) for s in sites]
    for site in saved:
        assert site['scores'] == {track: scores[site['chrom'], site['position0'], track] for track in c.old.TRACKS}
    groups = defaultdict(list)
    for row in rows: groups[row['dataset'], row['parent_id']].append(row)
    parents = c.old.read(c.OUT / 'parent_annotation_availability.json')
    assert [(p['dataset'], p['parent_id']) for p in parents] == sorted(groups)
    for parent in parents:
        members = groups[parent['dataset'], parent['parent_id']]
        check = parent_status(members, scores)
        for key, actual in check.items(): assert parent[key] == actual, key
        assert parent['all_native_covariates_unavailable_for_entire_parent'] == (not check['native_annotation_complete_parent'])
        assert parent['original_rows'] == len(members)
        assert parent['original_intervention_ids'] == sorted(row['intervention_id'] for row in members)
        assert parent['original_menus'] == sorted({row['parent_context_id'] for row in members})
    assert len(rows) == 26258 and len(parents) == 3022 and len(sites) == 15132
    assert len({row['parent_context_id'] for row in rows}) == 5436
    assert done['complete_annotation_parents'] == sum(p['native_annotation_complete_parent'] for p in parents)
    c.certify()
    c.jsave(c.OUT / 'independent_extraction_replay_receipt.json', {'status': 'PASS_INDEPENDENT_OBSERVED_HEADER_SITE_AND_PARENT_REPLAY',
        'value_manifest_sha256': c.old.sha(c.MANIFEST), 'extraction_receipt_sha256': c.old.sha(c.OUT / 'value_extraction_receipt.json'),
        'original_rows': 26258, 'original_menus': 5436, 'parents': 3022, 'exact_sites': 15132,
        'source_envelope_parser_shared': True, 'site_joins_and_parent_policy_independently_reconstructed': True,
        'features_produced': False, 'outcomes_read': False, 'models_fit': 0,
        'source_headers_not_learned_or_updated_from_remaining_responses': True})
    print('PASS independent site-join and whole-parent policy replay; no features or models', flush=True)


if __name__ == '__main__':
    run()
