"""Outcome-free corrected baseline and original-sequence inventory."""
from .common import *
from .route_structure import CONTEXT_SOURCE, CONTEXT_SHA256

INVENTORY_COLUMNS = ['intervention_id', 'dataset', 'biological_component',
                     'parent_context_id', 'parent_sequence', 'mutant_sequence']

def run():
    from src.generalization_20261007.verify import preservation
    preservation()
    assert not any((OUT / t / 'fits').exists() for t in TRACKS)
    assert sha256(CONTEXT_SOURCE) == CONTEXT_SHA256
    frame, historical = load()
    baseline, names = corrected_base(frame, historical)
    matrixsave(ART / 'base_features.npz', baseline)
    inventory = frame[INVENTORY_COLUMNS].copy()
    assert not inventory.intervention_id.duplicated().any()
    csvsave(ART / 'sequence_inventory.csv.gz', inventory, True)
    encoded = encoded_frame(inventory)
    csvsave(ART / 'encoded_sequence_inventory.csv.gz', encoded, True)
    rowhash = hashlib.sha256('|'.join(frame.intervention_id).encode()).hexdigest()
    jsave(OUT / 'short_feature_receipt.json', {
        'status':'PASS', 'rows':len(frame), 'columns':246, 'feature_names':names,
        'row_ids_sha256':rowhash, 'original_alleles_retained_for_purge':True,
        'source_outcomes_used_for_features':False, 'metadata_correction':'SRLE HEK293T; old annotation preserved',
        'srle_rows_recomputed':1744, 'other_rows_exactly_unchanged':24514,
        'context_sha256':CONTEXT_SHA256,
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in (
            ART/'base_features.npz', ART/'sequence_inventory.csv.gz', ART/'encoded_sequence_inventory.csv.gz')},
    })
    jsave(OUT / 'initial_state.json', {
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'previous_delivery_sha256':sha256(ROOT/'artifacts/generalization_20261007/delivery_receipt.json'),
        'original_modified_files_receipt':'results/generalization_20261007/initial_state.json',
        'new_supervised_sources':False, 'protected_outcomes_opened':False,
    })
    print('Corrected baseline and outcome-free inventory', baseline.shape, flush=True)

if __name__ == '__main__': run()
