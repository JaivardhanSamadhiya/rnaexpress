"""Fetch official versioned text for inspection, never execute remote code."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
NS = 'generalization_gquad_feasibility_20261007'
ART = ROOT / 'artifacts' / NS
OUT = ROOT / 'results' / NS
BASE = 'https://raw.githubusercontent.com/ViennaRNA/ViennaRNA/'
API = 'https://api.github.com/repos/ViennaRNA/ViennaRNA/git/trees/v2.7.2?recursive=1'


def save(path, payload):
    path = Path(path).resolve()
    if not (path.is_relative_to(ART) or path.is_relative_to(OUT)):
        raise PermissionError('New feasibility text namespace only')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError('Preserving existing official-source text')
    else:
        path.write_bytes(payload)


def get(url):
    if not (url.startswith(BASE) or url == API):
        raise PermissionError('Fixed official ViennaRNA GitHub URLs only')
    request = urllib.request.Request(url, headers={'User-Agent': 'RNAexpress-synthetic-source-audit'})
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError('Official source GET did not succeed')
        return response.read()


def run():
    payload = get(API)
    tree = json.loads(payload)
    assert not tree.get('truncated') and len(tree['sha']) == 40
    save(ART / 'official_git_tree.json', payload)
    selected = [item for item in tree['tree'] if item['type'] == 'blob' and (
        'gquad' in item['path'] or item['path'] in {
            'COPYING', 'src/ViennaRNA/partfunc/partfunc.c',
            'src/ViennaRNA/partfunc/exterior.c', 'src/ViennaRNA/partfunc/internal.c',
            'src/ViennaRNA/partfunc/multibranch.c', 'src/ViennaRNA/params/params.c',
            'doc/source/tutorial/RNAfold.rst', 'src/ViennaRNA/subopt/subopt.c'}
        or item['path'].endswith('/RNAfold.rst'))]
    files = {}
    for item in selected:
        name = item['path']
        if not name.endswith(('.c', '.h', '.rst', '.i', '.inc')) and name != 'COPYING':
            continue
        url = BASE + tree['sha'] + '/' + name
        content = get(url)
        # Bind the downloaded bytes to the GitHub tree's Git blob object too.
        blob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        assert blob == item['sha'], name
        local = ART / 'official_source' / name
        save(local, content)
        files[local.relative_to(ROOT).as_posix()] = {
            'url': url, 'sha256': hashlib.sha256(content).hexdigest(),
            'git_blob_sha1': blob, 'bytes': len(content)}
    assert files and any(name.endswith('COPYING') for name in files)
    receipt = {'status': 'PASS', 'requested_tag': 'v2.7.2', 'official_tree_sha': tree['sha'],
        'tree_url': API, 'tree_sha256': hashlib.sha256(payload).hexdigest(),
        'source_files': files, 'remote_code_executed': False,
        'public_free_official_source_only': True, 'labels_read': False,
        'project_alleles_folded': False, 'models_fit': 0}
    save(OUT / 'official_source_receipt.json', (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode())
    print(json.dumps({'status': 'PASS', 'official_tree_sha': tree['sha'], 'files': len(files)}))


if __name__ == '__main__':
    run()
