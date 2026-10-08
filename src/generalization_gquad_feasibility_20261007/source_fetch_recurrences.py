"""Additional exact tagged recurrence/constant text; never execute it."""
import hashlib
import json
from .source_fetch import ROOT, ART, OUT, BASE, save, get

NAMES = (
    'src/ViennaRNA/partfunc/pf_exterior.c',
    'src/ViennaRNA/partfunc/pf_internal.c',
    'src/ViennaRNA/partfunc/pf_multibranch.c',
    'src/ViennaRNA/eval/exp_eval_exterior.c',
    'src/ViennaRNA/eval/exp_eval_hairpin.c',
    'src/ViennaRNA/eval/exp_eval_internal.c',
    'src/ViennaRNA/eval/exp_eval_multibranch.c',
    'src/ViennaRNA/eval/eval_structures.c',
    'src/ViennaRNA/params/constants.h',
    'src/ViennaRNA/model.c',
    'src/ViennaRNA/model.h',
)


def run():
    tree = json.loads((ART / 'official_git_tree.json').read_text())
    byname = {item['path']: item for item in tree['tree'] if item['type'] == 'blob'}
    files = {}
    for name in NAMES:
        item = byname[name]
        url = BASE + tree['sha'] + '/' + name
        content = get(url)
        blob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        assert blob == item['sha'], name
        local = ART / 'official_source' / name
        save(local, content)
        files[local.relative_to(ROOT).as_posix()] = {
            'url': url, 'sha256': hashlib.sha256(content).hexdigest(),
            'git_blob_sha1': blob, 'bytes': len(content)}
    save(OUT / 'official_recurrence_source_receipt.json', (json.dumps({
        'status': 'PASS', 'official_tree_sha': tree['sha'], 'source_files': files,
        'remote_code_executed': False, 'labels_read': False,
        'project_alleles_folded': False, 'models_fit': 0}, indent=2, sort_keys=True) + '\n').encode())
    print(json.dumps({'status': 'PASS', 'files': len(files)}))


if __name__ == '__main__':
    run()
