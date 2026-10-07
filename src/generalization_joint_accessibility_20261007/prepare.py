"""Sequence/request plan only. No project folding, feature arrays or labels."""
from .common import *
from .runtime import check as runtime_check
from .production import requests, sequence_hash, request_hash, spec_hash

def run():
    runtime_check()
    assert not (OUT / 'feature_production_manifest.json').exists()
    original, encoded = sequence_frames(); roster, positions = requests(encoded)
    assert len(roster) == 18220 and len(positions) == 26258
    jsave(ART / 'sequence_request_manifest.json', {'rows': 26258, 'alleles': 18220,
        'original_metadata_sha256': metadata_identity(original), 'encoded_metadata_sha256': metadata_identity(encoded),
        'requests': {sequence_hash(sequence): request_hash(requested) for sequence, requested in roster.items()},
        'length_counts': {str(length): sum(len(value) == length for value in roster) for length in (46, 150, 190, 260)},
        'spec_sha256': spec_hash(), 'labels_read': False, 'project_alleles_folded': False})
    csvsave(OUT / 'row_index.csv.gz', original, True)
    jsave(OUT / 'preparation_receipt.json', {'status': 'PASS', 'rows': 26258, 'alleles': 18220,
        'row_index_sha256': sha256(OUT / 'row_index.csv.gz'), 'sequence_request_manifest_sha256': sha256(ART / 'sequence_request_manifest.json'),
        'runtime_binding_sha256': sha256(OUT / 'runtime_binding_receipt.json'), 'labels_read': False, 'models_fit': 0})

if __name__ == '__main__':
    run()
