"""Future root-gated feature blocks only; no label, array, model or fit access."""
from pathlib import Path
import csv
import gzip
import hashlib
import json
import sys
from .blocks import compute

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_conservation_feature_blocks_20261008'
OUT=ROOT/'results'/NS
MANIFEST=OUT/'preparation_manifest.json'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))


def certify():
    import subprocess
    manifest=read(MANIFEST)
    assert manifest['status']=='FROZEN_CONSERVATION_FEATURE_BLOCK_PREPARATION_ONLY'
    assert subprocess.check_output(['git','show','HEAD:'+MANIFEST.relative_to(ROOT).as_posix()],cwd=ROOT)==MANIFEST.read_bytes()
    for name,digest in manifest['files'].items():assert sha(ROOT/name)==digest,name
    return manifest


def run(root_start=False):
    assert root_start,'Root explicit start after committed feature preparation required'
    certify()
    from src.generalization_rbp_cellaxis_downstream_20261007.common import resource_check
    resource_check(3.,1.)
    from src.generalization_rbp_cellaxis_downstream_20261007.runtime_guard import python_contract,SCIENTIFIC
    python_contract(read(SCIENTIFIC))
    from src.generalization_conservation_values_20261008 import common as c
    c.certify();extraction=read(c.OUT/'value_extraction_receipt.json')
    replay=read(c.OUT/'independent_extraction_replay_receipt.json')
    proof_path=ROOT/'results/generalization_conservation_provenance_audit_20261008/provenance_audit_receipt.json'
    proof=read(proof_path)
    assert extraction['status']=='COMPLETED_OBSERVED_HEADER_SITE_EXTRACTION_NO_FEATURES_OR_MODELS'
    assert replay['status']=='PASS_INDEPENDENT_OBSERVED_HEADER_SITE_AND_PARENT_REPLAY'
    assert replay['extraction_receipt_sha256']==sha(c.OUT/'value_extraction_receipt.json')
    assert proof['status']=='PASS_ALL_SITE_QUERY_AND_MISSING_REASON_BINDINGS'
    assert proof['exact_site_query_score_and_reason_bindings']==15132
    for name,digest in proof['files'].items():assert sha(ROOT/name)==digest,name
    for name,digest in extraction['files'].items():assert sha(ROOT/name)==digest,name
    sites,all_rows=c.old.reference_inventory()
    coordinates={r['intervention_id']:r for r in all_rows}
    annotation_rows=read(c.OUT/'site_annotation_values.json')
    annotations={(r['chrom'],r['position0']):r for r in annotation_rows};assert len(annotations)==15132
    parents={(r['dataset'],r['parent_id']):r for r in read(c.OUT/'parent_annotation_availability.json')}
    metadata=ROOT/'results/generalization_rbp_cellaxis_20261007/metadata_receipt.json'
    meta=read(metadata);assert meta['status']=='PASS' and meta['rows']==13781
    path=ROOT/'results/generalization_rbp_cellaxis_20261007/row_index.csv.gz'
    assert sha(path)==meta['files'][path.relative_to(ROOT).as_posix()]
    with gzip.open(path,'rt',encoding='utf8',newline='') as f:
        reader=csv.DictReader(f);assert not any('delta' in field or 'effect' in field for field in reader.fieldnames)
        rows=list(reader)
    assert len(rows)==13781 and len({r['intervention_id'] for r in rows})==13781
    assert {r['dataset'] for r in rows}=={'mikl_gse173098'}
    assert {r['cell_type'] for r in rows}=={'CAD','Neuro-2a'}
    assert len({r['biological_component'] for r in rows})==187
    blocks=[];availability={};groups={}
    for row in rows:
        coordinate=coordinates[row['intervention_id']]
        for key in ('dataset','biological_component','parent_context_id','gene_transcript'):
            assert coordinate[key]==row[key],key
        key=row['dataset'],coordinate['parent_id'];parent=parents[key]
        assert row['intervention_id'] in parent['original_intervention_ids']
        available=parent['native_annotation_complete_parent']
        raw,native=compute(row['parent_sequence'],row['mutant_sequence'],coordinate['edited_site_coordinates'],annotations,available)
        assert key not in groups or groups[key]==available
        groups[key]=available;availability[row['intervention_id']]=available
        blocks.append({'intervention_id':row['intervention_id'],'parent_id':coordinate['parent_id'],
            'annotation_complete_parent':available,'raw_position8':raw,'reference_conservation8':native})
    assert {r['intervention_id'] for r in blocks}=={r['intervention_id'] for r in rows}
    OUT.mkdir(parents=True,exist_ok=True)
    result=OUT/'feature_blocks.json.gz'
    with result.open('xb') as f:f.write(gzip.compress((json.dumps(blocks,allow_nan=False,separators=(',',':'))+'\n').encode(),mtime=0))
    bindings=[path,metadata,c.OUT/'value_extraction_receipt.json',c.OUT/'independent_extraction_replay_receipt.json',
        c.OUT/'site_annotation_values.json',c.OUT/'parent_annotation_availability.json',proof_path,result]
    certify()
    receipt={'status':'PASS_CONSERVATION_FEATURE_BLOCKS_ONLY','rows':13781,'gene_components':187,
        'preparation_manifest_sha256':sha(MANIFEST),'files':{p.relative_to(ROOT).as_posix():sha(p) for p in bindings},
        'identical_complete_parent_mask_for_both_blocks_and_cells':True,'menus_filtered':0,
        'same_original_metadata_row_order':True,'available_intervention_rows':sum(availability.values()),
        'parents_total':len(groups),'parents_annotation_complete':sum(groups.values()),
        'feature_formulas_fixed_before_remaining_annotation_distribution':True,
        'outcome_columns_read':False,'model_arrays_read':False,'models_read':False,'models_fit':0,
        'matrix_control_runtime_and_prefit_admission_still_required':True,
        'static_parent_reference_conservation_not_mutant_change':True,
        'source_envelope_parser_shared':True,'independent_confirmation':False}
    with (OUT/'production_receipt.json').open('xb') as f:f.write((json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode())
    print('PASS13781conservation/position blocks only; no matrix model fitting',flush=True)


if __name__=='__main__':run('--root-start' in sys.argv[1:])
