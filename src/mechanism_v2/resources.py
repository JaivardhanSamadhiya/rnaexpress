"""Bounded, provenance-recorded retrieval of public resource metadata/source only.

No arbitrary links or local outcome files are followed. Downloaded source is
untrusted evidence, never automatically executed. Checkpoints require a separate
inspection/admission step. Failed attempts are retained, not called exclusions.
"""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from .io import ROOT, output_path, sha256, write_json, write_once

REPOS = {
    'ir_ipscs': ('marsico-lab/IR_iPSCs', '6587f57dbe9a11c8e62336f808175c66258537bb'),
    'parnet_author': ('lambosaur/parnet', '2e142786ffcec7ea5e23a28e1ec916c7524e6069'),
    'parnet_package': ('marsico-lab/parnet-marsico-lab', '0.3.0'),
    'parnet_paper': ('marsico-lab/parnet--paper', 'main'),
    'stability_utr': ('chienlinglin/modeling-UTR-variants-stability', 'main'),
}


def fetch(url, label, max_bytes=10_000_000):
    directory = 'data/external/mechanism_v2/resource_audit'
    identity = hashlib.sha256(url.encode()).hexdigest()[:16]
    relative = f'{directory}/{label}_{identity}.bin'
    path = output_path(relative)
    receipt_path = output_path(relative + '.json')
    if receipt_path.exists():
        result = json.loads(receipt_path.read_text())
        if path.exists() and sha256(path) == result['sha256']:
            return result
        raise ValueError(f'Resource cache integrity failure: {label}')
    request = Request(url, headers={'User-Agent':'RNAddress-research-resource-audit',
                                   'Accept':'application/vnd.github+json' if 'api.github.com' in url else '*/*'})
    with urlopen(request, timeout=25) as response:
        payload = response.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise ValueError('Resource exceeded explicitly allowed size')
        result = {'url':url, 'resolved_url':response.url, 'path':relative,
                  'bytes':len(payload), 'sha256':hashlib.sha256(payload).hexdigest(),
                  'retrieved_utc':datetime.now(timezone.utc).isoformat(), 'label':label}
    write_once(relative,payload)
    write_json(relative+'.json',result)
    return result


def audit_resources():
    records, errors = [], []
    def attempt(url,label):
        try:
            record=fetch(url,label)
            records.append(record)
            return json.loads((ROOT/record['path']).read_text(encoding='utf-8'))
        except Exception as error:
            errors.append({'url':url,'label':label,'error':str(error)})
            return None
    for label,(repo,ref) in REPOS.items():
        commit=attempt(f'https://api.github.com/repos/{repo}/commits/{ref}',label+'_commit')
        if not commit:
            continue
        pinned=commit['sha']
        tree=attempt(f'https://api.github.com/repos/{repo}/git/trees/{pinned}?recursive=1',label+'_tree')
        attempt(f'https://api.github.com/repos/{repo}/releases',label+'_releases')
        attempt(f'https://api.github.com/repos/{repo}/tags',label+'_tags')
        if not tree:
            continue
        if tree.get('truncated'):
            errors.append({'label':label, 'error':'Incomplete tree inventory; cannot declare checkpoint absent'})
        selected=[]
        for item in tree['tree']:
            p=item['path']
            if item['type']!='blob':
                continue
            if p in ('README.md','requirements.txt','environment.yml','LICENSE','pyproject.toml') or (
                label=='ir_ipscs' and p.startswith('configs/') and p.endswith('.json')) or (
                label=='parnet_author' and p.startswith(('parnet/','configs/','examples/')) and p.endswith(('.py','.json','.gin','.yml'))):
                selected.append((f'https://raw.githubusercontent.com/{repo}/{pinned}/{p}',
                                 label+'_'+p.replace('/','_')))
        def source_job(item):
            try:
                return fetch(*item)
            except Exception as error:
                return {'url':item[0], 'label':item[1], 'error':str(error)}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for record in pool.map(source_job,selected):
                (errors if 'error' in record else records).append(record)
        print(f'{label}: source inventory retrieved at {pinned}',flush=True)
    attempt('https://zenodo.org/api/records/21135982','ir_ipscs_zenodo')
    result={'records':records,'errors':errors,'scope':'Source and metadata only; no model admission yet',
            'astrocyte_data_accessed':False,'nzip_outcomes_accessed':False}
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    write_json(f'results/mechanism_v2/manifests/resource_retrieval_{stamp}.json',result)
    print(f'Resource audit: {len(records)} receipts, {len(errors)} unresolved retrievals',flush=True)
    return result
