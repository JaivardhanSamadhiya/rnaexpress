"""Retrieve only explicitly allowlisted free research metadata and small archives."""
from .common import ROOT, sha256, write_json, write_new
import argparse
from datetime import datetime, timezone
import json
import urllib.request
import zipfile

BASE = ROOT / 'data/external/research_20260921'
URLS = {
    'srle_tree': 'https://api.github.com/repos/lysovosyl/SRLE-seq/git/trees/main?recursive=1',
    'seers_tree': 'https://api.github.com/repos/gao-lab/SEERS/git/trees/main?recursive=1',
    'srle_article': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13191086/fullTextXML',
    'arora_article': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9561290/fullTextXML',
    'arora_geo': 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE183192&targ=self&form=text&view=full',
    'arora_supplement': 'https://pmc.ncbi.nlm.nih.gov/articles/instance/9561290/bin/gkac763_supplemental_files.zip',
    'srle_supplement': 'https://pmc.ncbi.nlm.nih.gov/articles/instance/13191086/bin/csbj.0107.f1.zip',
    'srle_epmc_supplement': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13191086/supplementaryFiles',
    'arora_epmc_supplement': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9561290/supplementaryFiles',
    'arora_counts': 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE183nnn/GSE183192/suppl/GSE183192_RAW.tar',
}

def fetch(name):
    url = URLS[name]
    dest = BASE / name
    receipt = BASE / (name + '.receipt.json')
    if receipt.exists():
        r = json.loads(receipt.read_text())
        if sha256(dest) != r['sha256']:
            raise ValueError('Downloaded asset changed')
        print(json.dumps({'name': name, 'reused': True, 'bytes': dest.stat().st_size}))
        return dest
    request = urllib.request.Request(url, headers={'User-Agent': 'RNAddress-research/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        content = response.read(35 * 1024 * 1024 + 1)
        if len(content) > 35 * 1024 * 1024:
            raise ValueError('Asset exceeds metadata/processed-data download cap')
        record = {'name': name, 'url': url, 'resolved_url': response.url,
                  'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                  'content_type': response.headers.get('Content-Type'), 'bytes': len(content)}
    if name.endswith('supplement') and not content.startswith(b'PK'):
        raise ValueError('Expected ZIP, received another response (no asset accepted)')
    write_new(dest, content)
    record['sha256'] = sha256(dest)
    write_json(receipt, record)
    print(json.dumps(record), flush=True)
    return dest

def inspect(name):
    path = BASE / name
    if name.endswith('tree'):
        d = json.loads(path.read_text())
        print(json.dumps({'commit_tree': d.get('sha'), 'files': [
            {'path': x['path'], 'size': x.get('size')} for x in d.get('tree', [])
            if x['type'] == 'blob']}, indent=2))
    elif name.endswith('article'):
        import xml.etree.ElementTree as ET
        root = ET.parse(path).getroot()
        for node in root.iter():
            if node.tag in ('supplementary-material', 'ext-link'):
                text = ''.join(node.itertext()).strip()
                if node.tag == 'supplementary-material' or any(w in text for w in ('GSE', 'HRA', 'github')):
                    print(ET.tostring(node, encoding='unicode')[:5000])
    elif name.endswith('supplement'):
        with zipfile.ZipFile(path) as archive:
            print(json.dumps([{'path': x.filename, 'bytes': x.file_size}
                              for x in archive.infolist()], indent=2))
    else:
        for line in path.read_text(errors='replace').splitlines():
            if any(w in line for w in ('supplementary_file', '!Series_title', '!Series_summary', '!Series_overall_design')):
                print(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['fetch', 'inspect'])
    parser.add_argument('names', nargs='+', choices=list(URLS))
    args = parser.parse_args()
    for name in args.names:
        try:
            if args.stage == 'fetch':
                fetch(name)
            else:
                inspect(name)
        except Exception as exc:
            print(json.dumps({'name': name, 'error': type(exc).__name__, 'message': str(exc)}), flush=True)
