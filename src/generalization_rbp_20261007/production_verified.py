"""Bind accessible RBP extraction to the independently audited structure bytes.

Additive wrapper: the previously frozen producer and numerical specification
are unchanged. The index certifies observed post-production bytes, not missing
historical creation receipts.
"""
from .common import ROOT, NEXT_ART, NEXT_OUT, OUT, sha256, readj, jsave
from pathlib import Path


def verify_structure_index():
    receipt_path = NEXT_OUT / 'structure_postproduction_audit_receipt.json'
    receipt = readj(receipt_path)
    assert receipt['status'] == 'PASS' and receipt['fresh_fold_count'] == 32
    assert receipt['outcomes_used'] is False and receipt['retrospective_creation_proof'] is False
    index_path = NEXT_ART / 'structure_postproduction_sha256_index.json'
    assert sha256(index_path) == receipt['index_sha256']
    index = readj(index_path)
    assert index['status'] == 'PASS' and len(index['alleles']) == 18220
    assert index['source_production_receipt_sha256'] == sha256(NEXT_OUT/'structure_cache_production_receipt.json')
    for entry in index['alleles']:
        assert sha256(ROOT/entry['path']) == entry['sha256'], entry['path']
    return sha256(receipt_path), sha256(index_path)


def run():
    before = verify_structure_index()
    from .production import produce
    produce('access')
    assert verify_structure_index() == before
    jsave(OUT/'access_structure_integrity_receipt.json', {
        'status':'PASS','structure_audit_receipt_sha256':before[0],
        'structure_observed_index_sha256':before[1],
        'structure_files_checked_before_and_after':18220,
        'existing_frozen_producer_modified':False,'models_fit':0,
        'retrospective_creation_proof':False,'source_sha256':sha256(Path(__file__))})
    print('Accessible RBP extraction matches the independently audited structure index',flush=True)


if __name__ == '__main__': run()
