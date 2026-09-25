"""Retrieve narrowly scoped official SRLE source text; never execute it."""
from src.research_20260921.common import ROOT, sha256, write_new, write_json
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import urllib.request

DEST=ROOT/'data/external/research_20260921/srle_provenance_continuation_20260925'
API='https://api.github.com/repos/lysovosyl/SRLE-seq/'
COMMIT='2255946636e755c1551f81c4ce32270ce5616f63'


def fetch(name,suffix,blob=None):
    path=DEST/name
    if path.exists():
        receipt=json.loads(path.with_name(name+'.receipt.json').read_text())
        assert sha256(path)==receipt['sha256']
        return path
    url=API+suffix
    request=urllib.request.Request(url,headers={'User-Agent':'RNA-project-source-provenance-audit','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request,timeout=40) as response:
        assert response.url.startswith(API), response.url
        payload=response.read(2_000_001)
        assert len(payload)<=2_000_000
    obj=json.loads(payload)
    if blob:
        payload=base64.b64decode(obj['content'])
        assert obj['encoding']=='base64' and obj['sha']==blob and len(payload)==obj['size']
        assert hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()==blob
        payload.decode('utf-8')
    write_new(path,payload)
    write_json(path.with_name(name+'.receipt.json'),{'url':url,'sha256':sha256(path),'git_blob':blob,
        'bytes':len(payload),'retrieved_utc':datetime.now(timezone.utc).isoformat(),
        'public_free':True,'scope':'Official source-text provenance only; no outcomes or models; not executed'})
    return path


def run():
    cached=ROOT/'data/external/research_20260921/srle_provenance_20260925/commits.json'
    receipt=json.loads(cached.with_name('commits.json.receipt.json').read_text())
    assert sha256(cached)==receipt['sha256']
    assert COMMIT in [r['sha'] for r in json.loads(cached.read_text())]
    tree=json.loads(fetch(COMMIT+'.tree.json','git/trees/'+COMMIT+'?recursive=1').read_text())
    assert not tree.get('truncated')
    matches=[r for r in tree['tree'] if r['path']=='analyse_kmer_library.py' and r['type']=='blob']
    assert len(matches)==1, 'Named historical helper absent; stop'
    items=[('historical_analyse_kmer_library.py',matches[0]['sha']),
           ('historical_library_split.py','7a5f9befe8f8740c0e75d84612ea44fa31d70795'),
           ('earlier_kmer_location_analysis.py','8de217f358a08525bcb1eeb6f2cfba3c706fd567')]
    with ThreadPoolExecutor(max_workers=3) as pool:
        files=list(pool.map(lambda item:fetch(item[0],'git/blobs/'+item[1],item[1]),items))
    for path in files: print(json.dumps({'path':str(path),'sha256':sha256(path),'bytes':path.stat().st_size}))


if __name__=='__main__': run()
