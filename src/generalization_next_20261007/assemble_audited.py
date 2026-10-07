"""Bind assembled features to independently audited structure cache bytes.

This additive wrapper leaves both production-frozen numerical producers and
the previously reviewed assembler unchanged. The index certifies observed
post-production bytes, not creation-time history.
"""
from .common import ROOT, ART, OUT, sha256, readj, jsave
from pathlib import Path


def structure_check():
    receipt_path = OUT / 'structure_postproduction_audit_receipt.json'
    receipt = readj(receipt_path)
    assert receipt['status'] == 'PASS' and receipt['fresh_fold_count'] == 32
    assert receipt['outcomes_used'] is False and receipt['retrospective_creation_proof'] is False
    index_path = ART / 'structure_postproduction_sha256_index.json'
    assert sha256(index_path) == receipt['index_sha256']
    index = readj(index_path)
    assert index['status'] == 'PASS' and len(index['alleles']) == 18220
    assert index['source_production_receipt_sha256'] == sha256(OUT / 'structure_cache_production_receipt.json')
    for number, entry in enumerate(index['alleles'], 1):
        path = (ROOT / entry['path']).resolve()
        assert path.is_relative_to(ART / 'structure_ensemble_cache')
        assert sha256(path) == entry['sha256'], entry['path']
        if number % 5000 == 0:
            print('Assembly structure SHA check', number, 'of', len(index['alleles']), flush=True)
    return sha256(receipt_path), sha256(index_path)


def run():
    before = structure_check()
    from .assemble_verified import run as assemble
    assemble()
    assert structure_check() == before
    jsave(OUT / 'assembly_structure_integrity_receipt.json', {
        'status': 'PASS', 'structure_audit_receipt_sha256': before[0],
        'structure_observed_index_sha256': before[1],
        'structure_files_checked_before_and_after': 18220,
        'existing_frozen_numerical_producers_modified': False,
        'retrospective_creation_proof': False, 'models_fit': 0,
        'code_sha256': sha256(Path(__file__))})
    print('Assembled features match the independently audited structure index', flush=True)


if __name__ == '__main__':
    run()
