"""Outcome-free immutable metadata and conservation matrix admission."""
from .common import *
import gzip,io
from .matrix_contracts import validate_blocks,addon
ORIGINAL_METADATA=ROOT/'results/generalization_rbp_cellaxis_20261007'
BLOCKS=ROOT/'results/generalization_conservation_feature_blocks_20261008'

def metadata(root_start=False):
    design_check(root_start)
    assert not (OUT/'metadata_receipt.json').exists()
    reference=readj(ORIGINAL_METADATA/'metadata_receipt.json');committed(ORIGINAL_METADATA/'metadata_receipt.json')
    assert reference['status']=='PASS' and reference['rows']==s.ROWS
    hash_files(reference['files'])
    paths=[]
    for name in ('row_index.csv.gz','split_roster.json','paired_menu_metadata.json'):
        path=ORIGINAL_METADATA/name;committed(path);save(OUT/name,path.read_bytes());paths.append(OUT/name)
    jsave(OUT/'metadata_receipt.json',{'status':'PASS','rows':s.ROWS,'components':s.COMPONENTS,
        'core_sha256':reference['core_sha256'],'source_metadata_receipt_sha256':sha256(ORIGINAL_METADATA/'metadata_receipt.json'),
        'files':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
        'original_metadata_copied_exactly':True,'outcome_columns_read':False,'arrays_read':False,'fits':0})

def matrices(root_start=False):
    design_check(root_start);thread_check();resource_check()
    from .runtime_guard import python_contract,SCIENTIFIC
    committed(SCIENTIFIC);python_contract(readj(SCIENTIFIC))
    assert not (OUT/'array_receipt.json').exists()
    meta=readj(OUT/'metadata_receipt.json');assert meta['status']=='PASS'
    hash_files(meta['files'])
    manifest=BLOCKS/'preparation_manifest.json';committed(manifest)
    initial=readj(manifest);hash_files(initial['files'])
    receipt=readj(BLOCKS/'production_receipt.json')
    assert receipt['status']=='PASS_CONSERVATION_FEATURE_BLOCKS_ONLY' and receipt['rows']==s.ROWS
    assert receipt['preparation_manifest_sha256']==sha256(manifest)
    assert receipt['identical_complete_parent_mask_for_both_blocks_and_cells'] and receipt['menus_filtered']==0
    assert not receipt['outcome_columns_read'] and not receipt['model_arrays_read'] and receipt['models_fit']==0
    hash_files(receipt['files'])
    np,pd,old,*_=runtime();frame,_=old.load(False)
    pd.testing.assert_frame_equal(frame,pd.read_csv(OUT/'row_index.csv.gz',low_memory=False))
    assert sha256(CORE)==meta['core_sha256']
    blocks=json.loads(gzip.decompress((BLOCKS/'feature_blocks.json.gz').read_bytes()))
    validate_blocks(frame.to_dict('records'),blocks)
    original=OLD_OUT/'prefit_manifest.json';committed(original);frozen=readj(original)
    assert frozen['status']=='FROZEN_PREFIT'
    assert sha256(CORE)==frozen['files'][CORE.relative_to(ROOT).as_posix()]
    paths={};hashes={};source_files={};base=None;simple=None
    for track in s.TRACKS:
        if track in s.REUSED_CONTROLS:
            path=old.ART/(track+'_model_features.npz');name=path.relative_to(ROOT).as_posix()
            assert sha256(path)==frozen['files'][name]
            with np.load(path,allow_pickle=False) as data:
                assert data.files==['features'];value=np.asarray(data['features'],dtype=float)
            assert value.shape==(s.ROWS,s.WIDTHS[track]) and np.isfinite(value).all()
            source_files[name]=sha256(path);paths[track]=name
            if track=='simple':simple=value.copy()
            else:
                base=value.copy();assert values_hash(base[:,:102])==values_hash(simple)
        else:
            assert base is not None
            tail=np.asarray([addon(track,r['raw_position8'],r['reference_conservation8']) for r in blocks],dtype=float)
            value=np.concatenate((base,tail),axis=1)
            assert value.shape==(s.ROWS,s.WIDTHS[track]) and np.isfinite(value).all()
            assert values_hash(value[:,:246])==values_hash(base)
            buffer=io.BytesIO();np.savez_compressed(buffer,features=value)
            path=ART/(track+'_model_features.npz');save(path,buffer.getvalue());paths[track]=path.relative_to(ROOT).as_posix()
        hashes[track]=values_hash(value);del value
    for path in (original,manifest,BLOCKS/'production_receipt.json',BLOCKS/'feature_blocks.json.gz'):
        source_files[path.relative_to(ROOT).as_posix()]=sha256(path)
    jsave(OUT/'array_receipt.json',{'status':'PASS','rows':s.ROWS,'widths':s.WIDTHS,'feature_paths':paths,
        'parsed_float64_matrix_sha256':hashes,'files':{name:sha256(ROOT/name) for name in paths.values()},
        'source_array_files':source_files,'metadata_receipt_sha256':sha256(OUT/'metadata_receipt.json'),
        'base_simple_exact_bytes':True,'every_new_track_has_exact_original_base_prefix':True,
        'menus_filtered':0,'same_parent_mask_and_original_row_order':True,'outcome_columns_read':False,
        'models_read':False,'fits':0,'control_checkpoint_reuse_not_yet_admitted':True})
