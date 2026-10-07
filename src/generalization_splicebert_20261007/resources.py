"""Lightweight, outcome-free SpliceBERT provenance and resource preparation.

No model deserialization, conversion, inference or supervised fitting occurs.
Only public authoritative metadata and existing model-archive members are read.
"""
from __future__ import annotations
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import tarfile
import ctypes
import shutil
from datetime import datetime,timezone
import urllib.parse
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parents[2]
NS='generalization_splicebert_20261007'
ART,OUT,REP=[ROOT/folder/NS for folder in ('artifacts','results','reports')]
MODEL=ROOT/'data/external/splicebert/models/SpliceBERT.1024nt'
ARCHIVE=ROOT/'data/external/splicebert/models.tar.gz'
AUTHOR='https://github.com/chenkenbio/SpliceBERT'
ZENODO='https://zenodo.org/api/records/7995778'
MD5='a51911d7d59fa6f0b07db4abaa820d84'
CPU_INDEX='https://download.pytorch.org/whl/cpu/torch/'
CPU_WHEEL='torch-2.6.0+cpu-cp312-cp312-win_amd64.whl'


def digest(path,algorithm='sha256'):
    h=hashlib.new(algorithm)
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def save(path,data):
    path=Path(path).resolve()
    assert any(path.is_relative_to(folder.resolve()) for folder in (ART,OUT,REP))
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data,'Preserve existing resource artifact: '+str(path)
    else:path.write_bytes(data)


def jsave(path,data):save(path,(json.dumps(data,indent=2,sort_keys=True)+'\n').encode())


def fetch(url):
    with urllib.request.urlopen(url,timeout=30) as response:return response.read()


def audit():
    metadata_bytes=fetch(ZENODO);metadata=json.loads(metadata_bytes)
    file=next(item for item in metadata['files'] if item['key']=='models.tar.gz')
    assert file['checksum']=='md5:'+MD5
    assert digest(ARCHIVE,'md5')==MD5 and ARCHIVE.stat().st_size==file['size']
    save(ART/'zenodo_7995778_metadata.json',metadata_bytes)
    files={name:{'bytes':(MODEL/name).stat().st_size,'sha256':digest(MODEL/name)}
           for name in ('pytorch_model.bin','config.json','tokenizer_config.json','tokenizer.json','special_tokens_map.json','vocab.txt')}
    official={}
    with tarfile.open(ARCHIVE,'r:gz') as archive:
        for member in archive:
            if not member.isfile() or not member.name.startswith('models/SpliceBERT.1024nt/'):continue
            name=member.name.rsplit('/',1)[-1]
            if name not in files:continue
            h=hashlib.sha256()
            with archive.extractfile(member) as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
            official[name]={'bytes':member.size,'sha256':h.hexdigest()}
    assert official==files,'Cached model/tokenizer must match author-linked archive exactly'
    config=json.loads((MODEL/'config.json').read_text())
    assert config['hidden_size']==512 and config['num_hidden_layers']==6 and config['vocab_size']==10
    vocabulary=(MODEL/'vocab.txt').read_text().splitlines()
    assert vocabulary==['[PAD]','[UNK]','[CLS]','[SEP]','[MASK]','N','A','C','G','T']
    license_url='https://raw.githubusercontent.com/chenkenbio/SpliceBERT/main/LICENSE'
    license_bytes=fetch(license_url)
    assert b'Redistribution and use in source and binary forms' in license_bytes
    save(ART/'SpliceBERT_author_LICENSE',license_bytes)
    receipt={'status':'PASS','scope':'Safe metadata and archive-member hashing only; no pickle/model execution',
             'author_repository':AUTHOR,'zenodo_model_release':'https://zenodo.org/records/7995778',
             'zenodo_metadata_sha256':hashlib.sha256(metadata_bytes).hexdigest(),
             'archive_published_md5':MD5,'archive_actual_md5':digest(ARCHIVE,'md5'),
             'archive_sha256':digest(ARCHIVE),'archive_bytes':ARCHIVE.stat().st_size,
             'author_archive_identity':'All selected checkpoint/tokenizer members byte-identical',
             'cached_files':files,'architecture':config,'vocabulary':vocabulary,
             'repository_license':'BSD-3-Clause','author_license_url':license_url,
             'author_license_sha256':hashlib.sha256(license_bytes).hexdigest(),
             'zenodo_license':metadata['metadata'].get('license'),
             'zenodo_access_right':metadata['metadata'].get('access_right'),
             'public_free':True,'checkpoint_variant':'SpliceBERT.1024nt',
             'short_sequence_limitation':'Author warns below64nt may fail; SRLE certified available context46nt is OOD; no fabricated padding/backbone',
             'comparative_scope':'Future four-core whole-assay utility ranking only; no localization transfer claimed yet'}
    jsave(OUT/'resource_audit.json',receipt)
    print(json.dumps({key:receipt[key] for key in ('status','archive_bytes','archive_sha256','zenodo_license','zenodo_access_right','cached_files')},indent=2),flush=True)


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href')
            if href:self.links.append(href)


def cpu_metadata():
    index_bytes=fetch(CPU_INDEX);parser=Links();parser.feed(index_bytes.decode())
    matches=[href for href in parser.links if urllib.parse.unquote(urllib.parse.urlsplit(href).path.rsplit('/',1)[-1])==CPU_WHEEL]
    assert len(matches)==1
    published=urllib.parse.urljoin(CPU_INDEX,matches[0]);parsed=urllib.parse.urlsplit(published)
    assert parsed.hostname in ('download.pytorch.org','download-r2.pytorch.org')
    checksum=urllib.parse.parse_qs(parsed.fragment)['sha256'][0]
    assert len(checksum)==64 and not set(checksum)-set('0123456789abcdef')
    url=urllib.parse.urlunsplit(parsed._replace(fragment=''))
    request=urllib.request.Request(url,method='HEAD')
    size=None;final=None;head_error=None
    try:
        with urllib.request.urlopen(request,timeout=30) as response:
            size=response.headers.get('Content-Length');final=response.url
    except urllib.error.HTTPError as error:
        # HEAD is metadata only. Preserve its failure; do not infer GET access
        # or bypass the endpoint. Root decides a later public download probe.
        head_error={'http_status':error.code,'reason':str(error.reason)}
    save(ART/'official_cpu_index.html',index_bytes)
    receipt={'status':'METADATA_ONLY','package':'torch','version':'2.6.0+cpu','wheel_filename':CPU_WHEEL,
             'official_index':CPU_INDEX,'official_index_sha256':hashlib.sha256(index_bytes).hexdigest(),
             'published_sha256':checksum,'download_url':url,'final_url':final,
             'bytes_from_HEAD':int(size) if size else None,
             'HEAD_error':head_error,'GET_access_checked':False,
             'license_source':'https://github.com/pytorch/pytorch/blob/v2.6.0/LICENSE',
             'public_free':True,'system_install_modified':False,'downloaded':False,'imported':False,
             'selection':'Pinned official CPU CPython3.12 Windows wheel supporting restricted weights_only load; no latest-version claim',
             'planned_loading':'Local author-verified checkpoint only, torch.load(weights_only=True,map_location=cpu); no remote code',
             'heavy_work_guard':'No conversion or inference until fresh headroom inventory and root start signal'}
    jsave(OUT/'cpu_wheel_metadata.json',receipt)
    print(json.dumps(receipt,indent=2),flush=True)


def resource_state():
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_uint32),('load',ctypes.c_uint32),
                  ('total_phys',ctypes.c_uint64),('avail_phys',ctypes.c_uint64),
                  ('total_page',ctypes.c_uint64),('avail_page',ctypes.c_uint64),
                  ('total_virtual',ctypes.c_uint64),('avail_virtual',ctypes.c_uint64),
                  ('avail_extended',ctypes.c_uint64)]
    memory=Memory();memory.length=ctypes.sizeof(memory)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
    disk=shutil.disk_usage(ROOT)
    return {'timestamp_UTC':datetime.now(timezone.utc).isoformat(),
            'total_RAM_bytes':memory.total_phys,'available_RAM_bytes':memory.avail_phys,
            'workspace_disk_free_bytes':disk.free,
            'proposed_minimum_free_RAM_bytes_before_model_work':3*1024**3,
            'proposed_minimum_disk_free_bytes':5*1024**3,
            'resource_admission_now':memory.avail_phys>=3*1024**3 and disk.free>=5*1024**3,
            'model_conversion_or_inference_started':False,'requires_fresh_check_at_start':True}


def headroom():
    receipt=resource_state()
    jsave(OUT/'initial_headroom.json',receipt)
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':
    assert sys.argv[1:] in (['audit'],['cpu_metadata'],['headroom'])
    {'audit':audit,'cpu_metadata':cpu_metadata,'headroom':headroom}[sys.argv[1]]()
