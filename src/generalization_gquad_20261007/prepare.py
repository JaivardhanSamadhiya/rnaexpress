"""Standard-library metadata plan only; never import folding or numerical code."""
import csv
import gzip
import io
from .guards import *
from .spec import request_plan, sequence_hash, request_hash, spec_hash, SPEC

def run():
    assert not (OUT / 'feature_production_manifest.json').exists()
    backend = backend_check(); source_control_paths(); structure = structure_index_check(False)
    original, encoded = sequence_rows(); roster, positions = request_plan(encoded)
    assert len(roster) == 18220 and len(positions) == 26258
    jsave(ART / 'sequence_request_manifest.json', {'status': 'PASS', 'rows': 26258, 'alleles': 18220,
        'original_metadata_sha256': metadata_digest(original), 'encoded_metadata_sha256': metadata_digest(encoded),
        'requests': {sequence_hash(s): request_hash(r) for s, r in roster.items()},
        'length_counts': {str(n): sum(len(s) == n for s in roster) for n in (46, 150, 190, 260)},
        'spec': SPEC, 'spec_sha256': spec_hash(), 'labels_read': False, 'features_computed': False})
    buffer = io.StringIO(newline=''); writer = csv.DictWriter(buffer, fieldnames=IDENTITY, lineterminator='\n')
    writer.writeheader(); writer.writerows(original)
    save(OUT / 'row_index.csv.gz', gzip.compress(buffer.getvalue().encode(), mtime=0))
    jsave(OUT / 'preparation_receipt.json', {'status': 'PASS', 'rows': 26258, 'alleles': 18220,
        'row_index_sha256': sha256(OUT / 'row_index.csv.gz'),
        'sequence_request_manifest_sha256': sha256(ART / 'sequence_request_manifest.json'),
        'backend_feasibility_receipt_sha256': sha256(FEAS_OUT / 'backend_feasibility_receipt.json'),
        'precision_receipt_sha256': sha256(FEAS_OUT / 'single_event_precision_receipt.json'),
        'ordinary_structure_metadata': structure,
        'fold_only_estimate_minutes': backend['fold_only_extrapolation_minutes'],
        'fold_only_with_50pct_margin_minutes': backend['fold_only_with_50pct_margin_minutes'],
        'estimated_cost_excludes_raw_scan_IO_hashing_and_fits': True,
        'labels_read': False, 'models_read': False, 'models_fit': 0, 'project_alleles_folded': 0})
    print('GQ metadata-only preparation PASS; production still requires separately committed freeze and root start', flush=True)

if __name__ == '__main__':
    run()
