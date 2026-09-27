"""Metadata-only reclassification of already catalogued resources."""
from .common import *

CLASSIFICATION={
 'SRLE':('ALREADY EXPOSED','One reporter, original source; no independent context'),
 'N-zip':('RESERVED / DO NOT OPEN','Quarantined uncertified truth; no outcome access'),
 'Mikl':('ALREADY EXPOSED','True paired small edits in CAD/N2A; extensive development exposure'),
 'Moffatt':('ALREADY EXPOSED','Paired small edits, few parents; prior development/lock exposure'),
 'TDP localization':('ALREADY EXPOSED','Previously analyzed localization; one mutant per exact parent, no decision sets; EV5 stability stays closed'),
 'Astrocyte':('RESERVED / DO NOT OPEN','Sealed, prior influence not established absent; cannot presume pristine'),
 'Arora':('ALREADY EXPOSED','Tiled alternatives do not establish small-edit parent lineage; reserved replicates remain closed'),
 'SIRLOIN':('ALREADY EXPOSED','Two SNV parents; discovery replicates used; reserved replicates not a new context'),
 'RNA-context':('ALREADY EXPOSED','Fragments across contexts, no admitted small-mutant lineage; prior model influence'),
 'Shukla':('PROVENANCE INSUFFICIENT','Tiled alternatives and unresolved raw/processed mapping; already exposed permitted subset'),
 'SEERS':('PROVENANCE INSUFFICIENT','Random inserts lack parent-mutant lineage; prior screen exposure and inadequate groups'),
 'Faraway':('ALREADY EXPOSED','Intron/configuration/barcode changes, not admitted pure small RNA substitutions'),
 'mutREL':('PROVENANCE INSUFFICIENT','Mutation-event counts do not establish isolated mutant genotypes; numeric outcomes unopened'),
 'Wen speckle':('PROVENANCE INSUFFICIENT','Unresolved transcribed RNA/outcome mapping; different endpoint; numeric outcomes unopened'),
 'External stability':('DOES NOT QUALIFY','RNA decay is not localization; exposed and admission failed'),
 'Pretrained model resources':('DOES NOT QUALIFY','Models/embeddings are not independently measured parent-edit outcomes'),
}

def run():
    paths=[ROOT/'artifacts/research_20260925/validation_resource_inventory.csv',ROOT/'data/manifests/acquisition_manifest.csv',
        ROOT/'data/manifests/file_inventory.csv',REPORT/'small_edit_dataset_inventory.md',REPORT/'independent_confirmation_admission.md',ROOT/'results/small_edit_20260925/inventory_receipt.json']
    inventory=pd.read_csv(paths[0]);assert set(inventory.resource)==set(CLASSIFICATION)
    rows=[]
    for row in inventory.to_dict('records'):
        status,why=CLASSIFICATION[row['resource']];evidence=ROOT/row['evidence_path']
        assert sha256(evidence)==row['evidence_sha256']
        row.update(classification=status,qualification_reason=why,qualifies_for_independent_test=False,outcomes_opened_this_audit=False,independent_admission_contract='reports/small_edit_20260925/independent_confirmation_admission.md')
        rows.append(row)
    csvsave(OUT/'local_resource_audit.csv',pd.DataFrame(rows))
    acquisition=pd.read_csv(paths[1]);files=pd.read_csv(paths[2])
    # Filenames and dataset labels only. Do not open any raw member, archive or outcome.
    directory_names=sorted(p.name for p in (ROOT/'data/raw').iterdir() if p.is_dir())
    jsave(OUT/'local_audit_receipt.json',{'status':'PASS','resources_classified':len(rows),'qualifying_untouched_resources':0,
        'metadata_inputs':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
        'acquisition_dataset_labels':sorted(acquisition.dataset.unique().tolist()),'acquisition_manifest_rows':len(acquisition),'file_inventory_rows':len(files),
        'raw_top_level_directory_names_only':directory_names,'archives_opened':0,'protected_or_reserved_files_opened':0,'new_external_requests':0,
        'scope':'Complete 16-resource admitted/exposure catalog plus central manifest and safe directory-name cross-check. Unknown/protected members not inspected. No claim of global dataset absence.'})
    print(readj(OUT/'local_audit_receipt.json'))

if __name__=='__main__':run()
