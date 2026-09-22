"""Download only eight identified public amplicon files; verify archive MD5."""
from .common import ROOT, sha256, write_json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import urllib.request

DATA = ROOT / 'data/external/research_20260921'
RUNS = {'HRR3059160', 'HRR3059161', 'HRR3059163', 'HRR3059164'}


def download(row, attempt=1):
    run, name = row['runAcc'], row['runFileName']
    if run not in RUNS or name not in (run + '_f1.fq.gz', run + '_r2.fq.gz'):
        raise ValueError('Non-allowlisted read file')
    relative = f'/HRA016642/{run}/{name}'
    checksums = {line.split()[1]: line.split()[0] for line in
                 (DATA / 'srle_raw_checksums').read_text().splitlines()}
    expected = checksums[relative]
    path = DATA / 'srle_reads' / name
    path.parent.mkdir(exist_ok=True)
    receipt = path.with_suffix(path.suffix + '.receipt.json')
    if receipt.exists():
        old = json.loads(receipt.read_text())
        if path.exists() and sha256(path) == old['sha256']:
            print(json.dumps({'cached': name}), flush=True)
            return
        raise ValueError('Cached file differs')
    if path.exists():
        raise FileExistsError(path)
    partial = path.with_suffix(path.suffix + '.part')
    if partial.exists():
        preserved = partial.with_name(partial.name + '.failed-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
        partial.rename(preserved)
        print(json.dumps({'preserved_incomplete': preserved.name, 'bytes': preserved.stat().st_size}), flush=True)
    url = 'https://download.cncb.ac.cn/gsa-human' + relative
    md5, digest = hashlib.md5(), hashlib.sha256()
    count = 0
    with urllib.request.urlopen(url, timeout=60) as response, partial.open('xb') as stream:
        expected_length = response.headers.get('Content-Length')
        if expected_length and int(expected_length) > 300_000_000:
            raise ValueError('Unexpectedly large file')
        for chunk in iter(lambda: response.read(1024 * 1024), b''):
            count += len(chunk)
            if count > 300_000_000:
                raise ValueError('Size cap exceeded')
            stream.write(chunk)
            md5.update(chunk)
            digest.update(chunk)
    if expected_length and count != int(expected_length):
        raise ValueError('Truncated download: ' + name)
    if md5.hexdigest() != expected:
        raise ValueError('Archive MD5 mismatch: ' + name)
    partial.rename(path)
    record = dict(url=url, sample=row['runTitle'], sample_accession=row['sampleAcc'],
                  bytes=count, md5=md5.hexdigest(), sha256=digest.hexdigest(),
                  retrieved_utc=datetime.now(timezone.utc).isoformat())
    write_json(receipt, record)
    print(json.dumps(record), flush=True)


def retry(row):
    for attempt in range(1, 4):
        try:
            return download(row, attempt)
        except Exception as exc:
            print(json.dumps({'file': row['runFileName'], 'attempt': attempt, 'error': str(exc)}), flush=True)
    raise RuntimeError('Three attempts failed: ' + row['runFileName'])


if __name__ == '__main__':
    rows = json.loads((DATA / 'srle_gsa_runs_all').read_text())['runViews']
    selected = [r for r in rows if r['runAcc'] in RUNS]
    if len(selected) != 8 or len({r['runFileName'] for r in selected}) != 8:
        raise ValueError('Expected eight unique files')
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(retry, row) for row in selected]
        errors = []
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                errors.append(str(exc))
        if errors:
            raise RuntimeError(errors)
