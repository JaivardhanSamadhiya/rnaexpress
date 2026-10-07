"""Frozen contextual and matched three-mer lookup edit features.

Feature APIs accept exact sequences and identifiers only. No outcome enters
encoding, projection, pooling, cache construction, or row assembly.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
import hashlib
import io
import json
import sys
import time
import zipfile

from .bert_backend_probe import Encoder, MODEL, IR, CHECKPOINT_SHA, RUNTIME, WHEEL_NAME, WHEEL_SHA, TOKENIZER_WHEEL, TOKENIZER_SHA
from .common import ART, OUT, ROOT, SEED, np, pd, sha256, save, jsave, matrixsave, production_check
from .route_structure import encoded_pair

INVENTORY = ART/'sequence_inventory.csv.gz'
GLOBAL_PROJECTION = ART/'bert_global_projection.npy'
LOCAL_PROJECTION = ART/'bert_local_projection.npy'
THREADS = 4
BATCH = 8
SHARD_ALLELES = 256


def projections(create=False):
    if create:
        rng = np.random.default_rng(SEED)
        # Explicit float64 draw and division, then float32 storage, in fixed order.
        matrices = [(rng.standard_normal((768,128))/np.sqrt(128)).astype(np.float32) for _ in range(2)]
        for path,matrix in zip((GLOBAL_PROJECTION,LOCAL_PROJECTION),matrices):
            buffer=io.BytesIO();np.save(buffer,matrix,allow_pickle=False);save(path,buffer.getvalue())
    matrices = [np.load(path,allow_pickle=False) for path in (GLOBAL_PROJECTION,LOCAL_PROJECTION)]
    assert all(matrix.shape==(768,128) and matrix.dtype==np.float32 and np.isfinite(matrix).all() for matrix in matrices)
    return matrices


def affected_starts(parent,mutant):
    assert len(parent)==len(mutant) and len(parent)>=3
    assert not set(parent+mutant)-set('ACGT')
    changed=[index for index,pair in enumerate(zip(parent,mutant)) if pair[0]!=pair[1]]
    return np.asarray(sorted({start for index in changed for start in range(max(0,index-2),min(index,len(parent)-3)+1)}),dtype=np.int16)


def projected_pair(parent,mutant,parent_hidden,mutant_hidden,pglobal,plocal):
    starts=affected_starts(parent,mutant)
    if not len(starts):return np.zeros(256,dtype=np.float32)
    global_delta=(mutant_hidden[1:len(parent)-1].mean(0)-parent_hidden[1:len(parent)-1].mean(0))@pglobal
    local_delta=(mutant_hidden[starts+1]-parent_hidden[starts+1]).mean(0)@plocal
    return np.r_[global_delta,local_delta].astype(np.float32)


@lru_cache(maxsize=1)
def vocabulary():
    tokens=(MODEL/'vocab.txt').read_text().splitlines()
    kmers=[token for token in tokens if len(token)==3 and not set(token)-set('ACGU')]
    assert len(kmers)==64 and len(set(kmers))==64
    return {token.replace('U','T'):index for index,token in enumerate(kmers)}


def lookup_pair(parent,mutant,pglobal,plocal):
    starts=affected_starts(parent,mutant)
    if not len(starts):return np.zeros(256,dtype=np.float32)
    ids=vocabulary()
    parent_ids=np.asarray([ids[parent[start:start+3]] for start in range(len(parent)-2)])
    mutant_ids=np.asarray([ids[mutant[start:start+3]] for start in range(len(mutant)-2)])
    # One-hot vectors occupy the first64 dimensions of the same768 inputs.
    global_delta=pglobal[mutant_ids].mean(0)-pglobal[parent_ids].mean(0)
    local_delta=plocal[mutant_ids[starts]].mean(0)-plocal[parent_ids[starts]].mean(0)
    return np.r_[global_delta,local_delta].astype(np.float32)


def sequence_frame():
    frame=pd.read_csv(INVENTORY,usecols=['intervention_id','dataset','parent_sequence','mutant_sequence'])
    assert len(frame)==26258 and frame.intervention_id.is_unique
    pairs=[encoded_pair(p,m,d) for p,m,d in zip(frame.parent_sequence,frame.mutant_sequence,frame.dataset)]
    frame['parent_sequence']=[pair[0] for pair in pairs]
    frame['mutant_sequence']=[pair[1] for pair in pairs]
    return frame


def row_identity(frame):
    text='\n'.join(f'{i}\t{p}\t{m}' for i,p,m in zip(frame.intervention_id,frame.parent_sequence,frame.mutant_sequence))
    return hashlib.sha256(text.encode()).hexdigest()


def prepare():
    projections(True)
    provenance=json.loads((OUT/'bert_checkpoint_provenance.json').read_text())
    lineage=json.loads((OUT/'bert_tokenizer_ir_audit.json').read_text())
    throughput=json.loads((OUT/'bert_synthetic_throughput.json').read_text())
    prior=json.loads((ROOT/'results/v4_phaseB/openvino_backend_equivalence.json').read_text())
    assert provenance['author_weight_identity']=='CERTIFIED_BYTE_IDENTICAL'
    assert lineage['status']=='PASS' and lineage['all_nonscalar_f32_constants_from_checkpoint']
    assert prior['accepted'] and prior['ir_xml_sha256']==sha256(IR) and prior['ir_bin_sha256']==sha256(IR.with_suffix('.bin'))
    setting=next(row for row in throughput['settings'] if row['threads']==THREADS and row['batch_size']==BATCH)
    assert setting['numerical_pass']
    spec={'version':'global_and_affected_token_projected_3utrbert_v1','seed':SEED,'threads':THREADS,'batch_size':BATCH,
          'input':'exact admitted inserts; certified SRLE20+6+20 window; no complete mature reporter claim',
          'encoder_hidden':768,'projected_per_pool':128,'columns':256,'shard_alleles':SHARD_ALLELES,
          'projection_generation':'NumPy default_rng(20261007); global then local; each standard_normal((768,128)) float64, divide sqrt(128) float64, cast float32',
          'global_projection_sha256':sha256(GLOBAL_PROJECTION),'local_projection_sha256':sha256(LOCAL_PROJECTION),
          'global_pool':'last layer mean overlapping3mer tokens only, excluding CLS/SEP/padding; mutant minus parent',
          'local_pool':'same last layer positions at union of3mer starts overlapping changed nucleotides; mutant minus parent',
          'lookup':'vocabulary ordered64 RNA3mers, one-hot first64 of768, same two projections/pools; rank<=64 per block',
          'backend':'single consistent OpenVINO CPU FP32; no reused historical inference features',
          'cached_checkpoint_sha256':CHECKPOINT_SHA,'ir_xml_sha256':sha256(IR),'ir_bin_sha256':sha256(IR.with_suffix('.bin')),
          'prior_equivalence_receipt_sha256':sha256(ROOT/'results/v4_phaseB/openvino_backend_equivalence.json'),
          'outcome_inputs':False,'fine_tuning':False,'PCA':False,'layer_seed_feature_search':False,
          'cache':'projected globals and only required projected token positions; length-grouped shards; resume hash-verified completed shards'}
    jsave(OUT/'bert_feature_spec.json',spec)
    runtime_files={}
    for name,checksum in ((WHEEL_NAME,WHEEL_SHA),(TOKENIZER_WHEEL,TOKENIZER_SHA)):
        wheel=ART/'wheels'/name
        assert sha256(wheel)==checksum
        with zipfile.ZipFile(wheel) as archive:
            for item in archive.infolist():
                if item.is_dir():continue
                path=(RUNTIME/item.filename).resolve()
                assert path.is_relative_to(RUNTIME.resolve())
                expected=hashlib.sha256(archive.read(item.filename)).hexdigest()
                assert sha256(path)==expected
                runtime_files[path.relative_to(ROOT).as_posix()]=expected
    actual={path.relative_to(ROOT).as_posix() for path in RUNTIME.rglob('*') if path.is_file()}
    assert actual==set(runtime_files),'Unexpected runtime files must be reviewed before freeze'
    jsave(OUT/'bert_runtime_integrity.json',{'files':runtime_files,'scope':'Exact extracted official OpenVINO and Tokenizers wheels; no added runtime files'})
    print('Prepared exact projections and encoder feature specification',flush=True)


def produce():
    production_check()
    runtime_files=json.loads((OUT/'bert_runtime_integrity.json').read_text())['files']
    assert {path.relative_to(ROOT).as_posix() for path in RUNTIME.rglob('*') if path.is_file()}==set(runtime_files)
    for name,checksum in runtime_files.items():assert sha256(ROOT/name)==checksum,name
    spec=json.loads((OUT/'bert_feature_spec.json').read_text())
    assert spec['threads']==THREADS and spec['batch_size']==BATCH
    pglobal,plocal=projections()
    assert sha256(GLOBAL_PROJECTION)==spec['global_projection_sha256'] and sha256(LOCAL_PROJECTION)==spec['local_projection_sha256']
    frame=sequence_frame();identity=row_identity(frame)
    required=defaultdict(set)
    for parent,mutant in zip(frame.parent_sequence,frame.mutant_sequence):
        starts=affected_starts(parent,mutant)
        assert len(starts)
        required[parent].update(map(int,starts));required[mutant].update(map(int,starts))
    alleles=sorted(required,key=lambda value:(len(value),hashlib.sha256(value.encode()).hexdigest(),value))
    assert len(alleles)==18220
    cache=ART/'bert_compact_cache';cache.mkdir(parents=True,exist_ok=True)
    inventory=[{'index':index,'sequence_sha256':hashlib.sha256(sequence.encode()).hexdigest(),
                'length':len(sequence),'required_starts':sorted(required[sequence])} for index,sequence in enumerate(alleles)]
    jsave(cache/'index.json',{'row_identity_sha256':identity,'alleles':inventory,'spec_sha256':sha256(OUT/'bert_feature_spec.json')})
    summaries={};shard_receipts=[];encoder=None;started=time.perf_counter()
    groups=defaultdict(list)
    for index,sequence in enumerate(alleles):groups[len(sequence)].append(index)
    shard_number=0
    for length,indexes in sorted(groups.items()):
        for offset in range(0,len(indexes),SHARD_ALLELES):
            ids=indexes[offset:offset+SHARD_ALLELES]
            sequences=[alleles[index] for index in ids]
            positions=[np.asarray(sorted(required[sequence]),dtype=np.int16) for sequence in sequences]
            path=cache/f'shard_{shard_number:04d}.npz';shard_number+=1
            expected_hashes=np.asarray([inventory[index]['sequence_sha256'] for index in ids])
            offsets=np.r_[0,np.cumsum([len(position) for position in positions])]
            flat_positions=np.concatenate(positions)
            if path.exists():
                sidecar_path=path.with_suffix('.json')
                assert sidecar_path.is_file(),'Preserve unreceipted shard; do not reuse or overwrite: '+str(path)
                sidecar=json.loads(sidecar_path.read_text())
                assert sidecar['sha256']==sha256(path),'Cached shard content changed: '+str(path)
                assert sidecar['spec_sha256']==sha256(OUT/'bert_feature_spec.json')
                assert sidecar['allele_hashes']==expected_hashes.tolist()
                with np.load(path,allow_pickle=False) as data:
                    np.testing.assert_array_equal(data['allele_hashes'],expected_hashes)
                    np.testing.assert_array_equal(data['offsets'],offsets)
                    np.testing.assert_array_equal(data['positions'],flat_positions)
                    globals_=data['globals'].copy();tokens=data['tokens'].copy()
            else:
                if encoder is None:encoder=Encoder(THREADS)
                globals_=np.empty((len(ids),128),dtype=np.float32)
                tokens=np.empty((offsets[-1],128),dtype=np.float32)
                for batch_start in range(0,len(ids),BATCH):
                    batch=sequences[batch_start:batch_start+BATCH]
                    hidden=encoder.hidden(batch)
                    for local,values in enumerate(hidden):
                        index=batch_start+local
                        globals_[index]=values[1:length-1].mean(0)@pglobal
                        tokens[offsets[index]:offsets[index+1]]=values[positions[index]+1]@plocal
                buffer=io.BytesIO();np.savez_compressed(buffer,allele_hashes=expected_hashes,offsets=offsets,
                    positions=flat_positions,globals=globals_,tokens=tokens);save(path,buffer.getvalue())
                jsave(path.with_suffix('.json'),{'sha256':sha256(path),
                    'spec_sha256':sha256(OUT/'bert_feature_spec.json'),'allele_hashes':expected_hashes.tolist(),
                    'scope':'Immutable compact shard content receipt; required before resume reuse'})
            assert globals_.shape==(len(ids),128) and tokens.shape==(offsets[-1],128)
            assert np.isfinite(globals_).all() and np.isfinite(tokens).all()
            for index,sequence in enumerate(sequences):
                summaries[sequence]=(globals_[index].copy(),positions[index].copy(),tokens[offsets[index]:offsets[index+1]].copy())
            shard_receipts.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(path),'alleles':len(ids),
                'sidecar_path':path.with_suffix('.json').relative_to(ROOT).as_posix(),'sidecar_sha256':sha256(path.with_suffix('.json'))})
            print('BERT compact shard',shard_number,'alleles',len(summaries),'of',len(alleles),'elapsed_s',round(time.perf_counter()-started,1),flush=True)
    features=np.empty((len(frame),256),dtype=np.float32);lookup=np.empty_like(features)
    for index,(parent,mutant) in enumerate(zip(frame.parent_sequence,frame.mutant_sequence)):
        positions=affected_starts(parent,mutant)
        gp,pp,tp=summaries[parent];gm,pm,tm=summaries[mutant]
        pi=np.searchsorted(pp,positions);mi=np.searchsorted(pm,positions)
        np.testing.assert_array_equal(pp[pi],positions);np.testing.assert_array_equal(pm[mi],positions)
        features[index]=np.r_[gm-gp,(tm[mi]-tp[pi]).mean(0)]
        lookup[index]=lookup_pair(parent,mutant,pglobal,plocal)
    assert np.isfinite(features).all() and np.isfinite(lookup).all()
    matrixsave(ART/'bert_features.npz',features);matrixsave(ART/'lookup_features.npz',lookup)
    jsave(OUT/'bert_features_receipt.json',{'status':'PASS','scope':'outcome-free frozen feature production; no supervised fitting',
        'rows':len(frame),'columns_per_route':256,'unique_alleles':len(alleles),'row_identity_sha256':identity,
        'sequence_inventory_sha256':sha256(INVENTORY),'spec_sha256':sha256(OUT/'bert_feature_spec.json'),
        'bert_features_sha256':sha256(ART/'bert_features.npz'),'lookup_features_sha256':sha256(ART/'lookup_features.npz'),
        'compact_shards':shard_receipts,'required_projected_token_vectors':sum(len(required[sequence]) for sequence in alleles),
        'elapsed_seconds':time.perf_counter()-started,'threads':THREADS,'batch_size':BATCH})
    print('BERT and matched lookup features complete',len(frame),'rows',flush=True)


if __name__=='__main__':
    assert sys.argv[1:] in (['prepare'],['produce'])
    (prepare if sys.argv[1]=='prepare' else produce)()
