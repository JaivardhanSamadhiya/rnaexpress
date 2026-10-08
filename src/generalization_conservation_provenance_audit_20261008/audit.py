"""Additive binding of every site to its fixed query and original missing reason."""
from pathlib import Path
import json
from src.generalization_conservation_values_20261008 import common as c
from src.generalization_conservation_native_20261007 import parser

NS='generalization_conservation_provenance_audit_20261008'
OUT=c.ROOT/'results'/NS


def reconstruct(payload,response,query,headers):
    arrays=None;groups=None
    reason=response.get('failure','Missing complete public body')
    if response['http_status']==200 and not response.get('failure') and payload is not None:
        try:arrays,groups=parser.values(payload,query,headers)
        except parser.SchemaError as error:reason='Unavailable strict values or source-header drift: '+str(error)
    status='UNAVAILABLE_VALUE_RESPONSE' if arrays is None else 'ADMITTED_EXACT_ORDERED_DUAL_TRACK_RESPONSE'
    per_site={}
    for pos in range(query['start0'],query['end0']):
        scores={track:arrays[track].get(pos) if arrays is not None else None for track in c.old.TRACKS}
        per_site[query['chrom'],pos]={'scores':scores,'query_key':query['key'],
            'missing_reason':None if all(value is not None for value in scores.values()) else
                ('source_score_absent' if arrays is not None else reason)}
    return status,groups,reason,per_site


def run():
    c.certify();done_path=c.OUT/'value_extraction_receipt.json';done=c.old.read(done_path)
    replay_path=c.OUT/'independent_extraction_replay_receipt.json';replay=c.old.read(replay_path)
    assert replay['status']=='PASS_INDEPENDENT_OBSERVED_HEADER_SITE_AND_PARENT_REPLAY'
    assert replay['extraction_receipt_sha256']==c.old.sha(done_path)
    assert done['value_manifest_sha256']==c.old.sha(c.MANIFEST)
    for name,digest in done['files'].items():assert c.old.sha(c.ROOT/name)==digest
    roster=c.old.read(c.old.OUT/'value_query_roster.json')
    pilot=c.old.read(c.pilot.OUT/'pilot_receipt.json')
    pilots={r['key']:r for r in pilot['records']};headers={r['chrom']:r['observed_source_headers'] for r in pilot['records']}
    assert len(done['response_records'])==len(roster)==3003
    assert [r['key'] for r in done['response_records']]==[q['key'] for q in roster]
    site_values={};files={};remaining_bytes=0;reused=0;available=0;failed=0
    for query,record in zip(roster,done['response_records']):
        reused_pilot=query['key'] in pilots;reused+=int(reused_pilot)
        path=c.ROOT/pilots[query['key']]['body_path'] if reused_pilot else c.ART/'values'/(query['key']+'.json')
        receipt=path.with_name(path.name+'.receipt.json');response=c.old.read(receipt)
        assert record['response_receipt']==receipt.relative_to(c.ROOT).as_posix()
        assert c.old.sha(receipt)==record['response_receipt_sha256'] and response['url']==query['url']==record['url']
        assert record['reused_pilot']==reused_pilot and record['expected_observed_headers']==headers[query['chrom']]
        files[receipt.relative_to(c.ROOT).as_posix()]=c.old.sha(receipt)
        if not reused_pilot:remaining_bytes+=response['acquired_bytes']
        payload=None
        if response['sha256'] is not None:
            assert c.old.sha(path)==response['sha256']==record['body_sha256']
            assert path.stat().st_size==response['bytes'] and record['body_path']==path.relative_to(c.ROOT).as_posix()
            payload=path.read_bytes();files[path.relative_to(c.ROOT).as_posix()]=c.old.sha(path)
        else:assert record['body_path'] is None and record['body_sha256'] is None and not path.exists()
        status,groups,reason,local=reconstruct(payload,response,query,headers[query['chrom']])
        assert record['status']==status
        if groups is None:
            assert record['missing_reason']==reason;failed+=1
        else:
            assert record['source_metadata_groups']==groups and 'missing_reason' not in record;available+=1
        assert not set(local)&set(site_values);site_values.update(local)
    assert reused==done['reused_pilot_responses']==20 and available+failed==3003
    assert done['acquired_bytes_including_schemas_and_pilots']==c.old.read(c.MANIFEST)['previous_schema_and_pilot_acquired_bytes']+remaining_bytes
    assert 0<=done['new_value_requests_this_execution']<=2983
    saved=c.old.read(c.OUT/'site_annotation_values.json');assert len(saved)==len(site_values)==15132
    for site in saved:
        expected=site_values[site['chrom'],site['position0']]
        for key in ('query_key','scores','missing_reason'):assert site[key]==expected[key],key
    for p in (done_path,replay_path,c.MANIFEST,c.pilot.OUT/'pilot_receipt.json',c.OUT/'site_annotation_values.json'):
        files[p.relative_to(c.ROOT).as_posix()]=c.old.sha(p)
    own=c.ROOT/'src'/NS/'audit.py';files[own.relative_to(c.ROOT).as_posix()]=c.old.sha(own)
    c.certify();OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'provenance_audit_receipt.json').open('xb') as f:
        f.write((json.dumps({'status':'PASS_ALL_SITE_QUERY_AND_MISSING_REASON_BINDINGS','files':files,
            'visited_fixed_intervals':3003,'reused_pilot_responses':20,'remaining_fixed_responses':2983,
            'new_requests_this_production_execution':done['new_value_requests_this_execution'],
            'admitted_intervals':available,'unavailable_response_intervals':failed,
            'exact_site_query_score_and_reason_bindings':15132,
            'acquired_bytes_including_schema_and_pilot':done['acquired_bytes_including_schemas_and_pilots'],
            'models_fit':0,'features_produced':False,'localization_outcomes_read':False,
            'source_envelope_parser_shared':True,'independent_envelope_parser_certified':False,
            'status_missing_reason_query_keys_and_byte_totals_reconstructed':True},indent=2,sort_keys=True)+'\n').encode())
    print('PASS all15132site query/missing reasons,3003status and acquisition-byte bindings',flush=True)


if __name__=='__main__':run()
