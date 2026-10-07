"""Author-linked checkpoint audit using hashes and safe ZIP inspection only.

Never imports torch, unpickles model data, or executes downloaded model code.
"""
from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.request
import zipfile
import sys
import xml.etree.ElementTree as ET

from .bert_backend_probe import ART, OUT, MODEL, IR, CHECKPOINT_SHA, configure_runtime, digest, jsave, save

ARTICLE = 'https://api.figshare.com/v2/articles/22847354'
AUTHOR_LINK = 'https://github.com/yangyn533/3UTRBERT'
FILE_ID = 40597877
EXPECTED_MD5 = '5ec828f9f3a58639af05545a611eac69'
EXPECTED_BYTES = 322227069
COMMUNITY = 'https://huggingface.co/api/models/yangheng/3utrbert?blobs=true'


def storage_fingerprint(source):
    """Content-only comparison, never deserialize pickle or persistent IDs."""
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        storages = [name for name in names if '/data/' in name and name.rsplit('/', 1)[1].isdigit()]
        entries = []
        for name in storages:
            info = archive.getinfo(name)
            h = hashlib.sha256()
            with archive.open(name) as stream:
                for block in iter(lambda: stream.read(8*1024*1024), b''):
                    h.update(block)
            entries.append((info.file_size, h.hexdigest()))
        pickles = {name: hashlib.sha256(archive.read(name)).hexdigest()
                   for name in names if name.endswith('/data.pkl')}
        return {'storage_count': len(entries), 'storage_bytes': sum(item[0] for item in entries),
                'content_multiset_sha256': hashlib.sha256(json.dumps(sorted(entries)).encode()).hexdigest(),
                'data_pickle_sha256': pickles, 'zip_names': names}


def run():
    started = time.perf_counter()
    with urllib.request.urlopen(ARTICLE, timeout=30) as response:
        metadata_bytes = response.read()
    metadata = json.loads(metadata_bytes)
    assert metadata['is_public'] and not metadata['is_confidential'] and not metadata['download_disabled']
    assert metadata['license']['name'] == 'CC BY 4.0'
    files = [item for item in metadata['files'] if item['id'] == FILE_ID]
    assert len(files) == 1
    info = files[0]
    assert info['size'] == EXPECTED_BYTES and info['computed_md5'] == EXPECTED_MD5
    assert info['download_url'] == 'https://ndownloader.figshare.com/files/40597877'
    archive_path = ART / 'provenance' / '3-new-12w-0.zip'
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if not archive_path.exists():
        partial = archive_path.with_suffix('.zip.partial')
        assert not partial.exists(), 'Preserve existing partial; do not overwrite.'
        print('Downloading public author-linked CC BY 4.0 checkpoint:', EXPECTED_BYTES, 'bytes', flush=True)
        size = 0
        with urllib.request.urlopen(info['download_url'], timeout=60) as response, partial.open('xb') as stream:
            while block := response.read(8*1024*1024):
                stream.write(block)
                size += len(block)
                if size % (32*1024*1024) == 0:
                    print('Downloaded', size, 'bytes', flush=True)
        assert size == EXPECTED_BYTES
        partial.rename(archive_path)
    md5 = hashlib.md5(archive_path.read_bytes()).hexdigest()
    assert archive_path.stat().st_size == EXPECTED_BYTES and md5 == EXPECTED_MD5
    save(ART / 'provenance' / 'figshare_22847354_metadata.json', metadata_bytes)
    with urllib.request.urlopen(COMMUNITY, timeout=30) as response:
        community_bytes = response.read()
    community = json.loads(community_bytes)
    sibling = next(item for item in community['siblings'] if item['rfilename'] == 'pytorch_model.bin')
    assert sibling['lfs']['sha256'] == CHECKPOINT_SHA
    assert not community['private'] and not community['gated'] and not community['disabled']
    save(ART / 'provenance' / 'community_metadata.json', community_bytes)
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        for name in names:
            assert not name.startswith(('/', '\\')) and '..' not in name.replace('\\','/').split('/')
        checkpoints = [name for name in names if name.endswith('/pytorch_model.bin') or name == 'pytorch_model.bin']
        assert len(checkpoints) == 1
        official_bytes = archive.read(checkpoints[0])
        official_sha = hashlib.sha256(official_bytes).hexdigest()
        print('Official checkpoint size and SHA:', len(official_bytes), official_sha, flush=True)
        config_names = [name for name in names if name.endswith('/config.json')]
        assert len(config_names) == 1
        config = json.loads(archive.read(config_names[0]))
        official_storage = storage_fingerprint(io.BytesIO(official_bytes)) if zipfile.is_zipfile(io.BytesIO(official_bytes)) else None
    cached_storage = storage_fingerprint(MODEL/'pytorch_model.bin')
    bytes_equal = official_sha == CHECKPOINT_SHA and digest(MODEL/'pytorch_model.bin') == CHECKPOINT_SHA
    storages_equal = official_storage is not None and official_storage['content_multiset_sha256'] == cached_storage['content_multiset_sha256']
    receipt = {
        'scope': 'Public resource provenance only, no pickle deserialization or biological outcomes',
        'author_repository': AUTHOR_LINK, 'author_model_release': metadata['figshare_url'],
        'figshare_metadata_url': ARTICLE, 'figshare_metadata_sha256': hashlib.sha256(metadata_bytes).hexdigest(),
        'license': metadata['license'], 'public_free': True, 'archive_bytes': EXPECTED_BYTES,
        'archive_published_md5': EXPECTED_MD5, 'archive_actual_md5': md5,
        'archive_sha256': digest(archive_path), 'archive_members': names,
        'official_checkpoint_member': checkpoints[0], 'official_checkpoint_bytes': len(official_bytes),
        'official_checkpoint_sha256': official_sha, 'official_config': config,
        'community_model_id': community['id'], 'community_revision': community['sha'],
        'community_model_card_license': community['cardData']['license'],
        'community_metadata_sha256': hashlib.sha256(community_bytes).hexdigest(),
        'cached_checkpoint_sha256': CHECKPOINT_SHA, 'cached_equals_public_community_weights': True,
        'official_and_cached_checkpoint_bytes_identical': bytes_equal,
        'official_and_cached_storage_content_multisets_equal': storages_equal,
        'official_storage_audit': official_storage, 'cached_storage_audit': cached_storage,
        'author_weight_identity': 'CERTIFIED_BYTE_IDENTICAL' if bytes_equal else 'UNCERTIFIED',
        'storage_multiset_limitation': 'Storage equality alone does not certify tensor name, shape, or computation graph mapping',
        'download_and_audit_seconds': time.perf_counter()-started,
    }
    jsave(OUT/'bert_checkpoint_provenance.json', receipt)
    print(json.dumps({key:receipt[key] for key in ('author_weight_identity','official_and_cached_checkpoint_bytes_identical',
          'official_and_cached_storage_content_multisets_equal','official_checkpoint_sha256','download_and_audit_seconds')},indent=2),flush=True)


def tokenizer_and_ir_audit():
    configure_runtime()
    import numpy as np
    with zipfile.ZipFile(ART/'provenance/3-new-12w-0.zip') as archive:
        names=('config.json','vocab.txt','tokenizer_config.json','special_tokens_map.json')
        records={name:{'official_sha256':hashlib.sha256(archive.read('3-new-12w-0/'+name)).hexdigest(),
                       'cached_sha256':digest(MODEL/name),
                       'byte_identical':archive.read('3-new-12w-0/'+name)==(MODEL/name).read_bytes()}
                 for name in names}
        official_config=json.loads(archive.read('3-new-12w-0/config.json'))
    cached_config=json.loads((MODEL/'config.json').read_text())
    differences={key:{'official':official_config.get(key),'cached':cached_config.get(key)}
                 for key in set(official_config)|set(cached_config) if official_config.get(key)!=cached_config.get(key)}
    assert differences=={'max_length':{'official':20,'cached':10}}
    assert all(records[name]['byte_identical'] for name in names if name!='config.json')
    with zipfile.ZipFile(MODEL/'pytorch_model.bin') as archive:
        storage_hashes={hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()
                        if '/data/' in name and name.rsplit('/',1)[1].isdigit()}
    matches=[]
    scalars=[]
    unmatched=[]
    with IR.with_suffix('.bin').open('rb') as stream:
        for node in ET.parse(IR).getroot().findall('./layers/layer'):
            if node.attrib['type']!='Const': continue
            info=node.find('data').attrib
            if info['element_type']!='f32': continue
            size=int(info['size']); stream.seek(int(info['offset'])); raw=stream.read(size)
            shape=tuple(map(int,info['shape'].split(','))) if info['shape'] else ()
            record={'name':node.attrib['name'],'shape':shape,'bytes':size}
            if size<=16:
                record['values']=np.frombuffer(raw,dtype='<f4').tolist();scalars.append(record);continue
            direct=hashlib.sha256(raw).hexdigest() in storage_hashes
            transposed=False
            if not direct and len(shape)==2:
                transposed=hashlib.sha256(np.frombuffer(raw,dtype='<f4').reshape(shape).T.copy().tobytes()).hexdigest() in storage_hashes
            record['direct_storage_match']=direct;record['transpose_storage_match']=transposed
            (matches if direct or transposed else unmatched).append(record)
    receipt={'scope':'Safe tokenizer, JSON configuration and raw IR constant audit; no pickle execution or outcomes',
             'tokenizer_file_comparison':records,'configuration_differences':differences,
             'max_length_difference_relevance':'Generation max_length is unused: encoder calls explicit supplied tokens <=512; no generate() call or truncation',
             'ir_xml_sha256':digest(IR),'ir_bin_sha256':digest(IR.with_suffix('.bin')),
             'matched_nonscalar_f32_constants':matches,'unmatched_nonscalar_f32_constants':unmatched,
             'scalar_f32_constants':scalars,'all_nonscalar_f32_constants_from_checkpoint':not unmatched,
             'torch_numerical_equivalence':'Not freshly retested; raw weight membership does not prove graph equivalence',
             'status':'PASS' if not unmatched else 'REVIEW_UNMATCHED_CONSTANTS'}
    jsave(OUT/'bert_tokenizer_ir_audit.json',receipt)
    print(json.dumps({key:receipt[key] for key in ('status','configuration_differences','all_nonscalar_f32_constants_from_checkpoint')},indent=2),flush=True)
    print('Matched non-scalar constants',len(matches),'unmatched',len(unmatched),flush=True)


if __name__ == '__main__':
    if sys.argv[1:]==['tokenizer_ir']: tokenizer_and_ir_audit()
    else:
        assert not sys.argv[1:]
        run()
