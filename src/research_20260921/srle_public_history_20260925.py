"""Archive source text/metadata from the already-admitted public SRLE repository."""
from .common import ROOT, sha256, write_json, write_new
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import base64
import hashlib
import json
import urllib.request

DEST = ROOT / 'data/external/research_20260921/srle_provenance_20260925'
API = 'https://api.github.com/repos/lysovosyl/SRLE-seq/'
BLOBS = {
    'infer_sequence.py': '046e01815cec8f1f95fdcf55ac4e25e8b97fe6da',
    'model.py': 'fa201cf7284a57ebc2f25a46582044d3a332ae6c',
    'train_model.py': '1f11854b4865be12c1f7d4f0e971799ad74cca8e',
    'historical_kmer_count.py': '555a41ac9005a37d8c6747df33f7cddf821bf9d9',
    'historical_makeshell.py': 'b90797a83310a732fc5f7893ca803dd2a8abac7a',
    'historical_library_location_analysis.py': 'be84cb6c8d84b893674d3cc037917c7ba5b7c02d',
}


def retrieve(item):
    name, suffix, git_blob = item
    path = DEST / name
    if path.exists():
        receipt = json.loads(path.with_name(name + '.receipt.json').read_text())
        if sha256(path) != receipt['sha256']:
            raise ValueError('Cached public source changed')
        return receipt
    url = API + suffix
    request = urllib.request.Request(url, headers={'User-Agent': 'RNA-project-provenance-audit',
                                                  'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Metadata response exceeds fixed bound')
        resolved, link = response.url, response.headers.get('Link', '')
    obj = json.loads(raw)
    if git_blob:
        payload = base64.b64decode(obj['content'])
        actual = hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
        if obj['encoding'] != 'base64' or obj['sha'] != git_blob or actual != git_blob or len(payload) != obj['size']:
            raise ValueError('Official Git blob identity failed')
    else:
        payload = raw
    write_new(path, payload)
    receipt = {'url': url, 'resolved_url': resolved, 'bytes': len(payload), 'sha256': sha256(path),
               'git_blob': git_blob, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
               'pagination_link': link, 'public_free': True,
               'scope': 'Known SRLE source provenance only; no new dataset, outcome CSV or model weights.'}
    write_json(path.with_name(name + '.receipt.json'), receipt)
    return receipt


def run():
    items = [(n, 'git/blobs/' + h, h) for n, h in BLOBS.items()]
    items += [('commits.json', 'commits?per_page=100', None)]
    items += [(r + '.tree.json', 'git/trees/' + r + '?recursive=1', None) for r in
              ('620411cae4a236cef8a333a3b117a69fdce97bbd', 'ebef7a015d87e93c54b1223a0323c073e74f0cb7')]
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(retrieve, items))
    print(json.dumps([{'bytes': r['bytes'], 'sha256': r['sha256'], 'url': r['url']} for r in receipts], indent=2))


if __name__ == '__main__':
    run()
