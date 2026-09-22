"""Resume identified truncated public files using verified HTTP byte ranges."""
from .download_reads import DATA
from .common import write_json, sha256
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
import urllib.request


def resume(name):
    if name not in ('HRR3059163_f1.fq.gz', 'HRR3059163_r2.fq.gz', 'HRR3059164_r2.fq.gz'):
        raise ValueError('Only the three failed nuclear transfers are allowed')
    path = DATA / 'srle_reads' / name
    if path.exists():
        raise FileExistsError(path)
    partial = path.with_suffix('.gz.part')
    if not partial.exists():
        raise FileNotFoundError(partial)
    run = name.split('_')[0]
    url = f'https://download.cncb.ac.cn/gsa-human/HRA016642/{run}/' + name
    start = partial.stat().st_size
    total = None
    while total is None or start < total:
        end = start + 4*1024*1024 - 1
        if total is not None:
            end = min(end, total-1)
        request = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}'})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range',''))
                    if response.status != 206 or not match:
                        raise ValueError('Server did not honor byte range')
                    first,last,size = map(int, match.groups())
                    if first != start or last > end or size > 300_000_000 or (total is not None and total != size):
                        raise ValueError('Invalid response range')
                    chunk = response.read(4*1024*1024+1)
                    if len(chunk) != last-first+1:
                        raise ValueError('Incomplete range')
                    total = size
                break
            except Exception as exc:
                print(json.dumps({'file':name,'offset':start,'attempt':attempt+1,'error':str(exc)}),flush=True)
                if attempt == 2:
                    raise
        with partial.open('ab') as stream:
            stream.write(chunk)
        start += len(chunk)
        print(json.dumps({'file':name,'bytes':start,'total':total}),flush=True)
    md5 = hashlib.md5()
    with partial.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8*1024*1024), b''):
            md5.update(chunk)
    checks = {line.split()[1].split('/')[-1]:line.split()[0] for line in (DATA/'srle_raw_checksums').read_text().splitlines()}
    if md5.hexdigest() != checks[name]:
        raise ValueError('Full-file archive MD5 failed')
    digest = sha256(partial)
    partial.rename(path)
    rep = 1 if run == 'HRR3059163' else 2
    receipt = dict(url=url, sample=f'6mer_Nuc_Sample{rep}', sample_accession=f'HRS225620{rep+4}',
                   bytes=total, md5=md5.hexdigest(), sha256=digest,
                   retrieved_utc=datetime.now(timezone.utc).isoformat(), resumed_with_verified_ranges=True)
    write_json(path.with_suffix('.gz.receipt.json'),receipt)
    print(json.dumps(receipt),flush=True)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(resume, sys.argv[1:]))
