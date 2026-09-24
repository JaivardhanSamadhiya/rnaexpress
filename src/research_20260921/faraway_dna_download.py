"""Retrieve and fully verify one allowlisted official plasmid-DNA file."""
from .common import ROOT, sha256, write_new, write_json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import csv, gzip, hashlib, json, shutil, time
from urllib.request import Request, urlopen

DATA = ROOT/'data/external/research_20260921'
RUN = 'ERR12019311'
SIZE = 341076082
MD5 = '591291d31db03888856f11dbfb6d0981'
CHUNK = 4*1024**2


def run():
    for name in ['faraway2025_longread_ena', 'faraway2025_longread_sdrf']:
        receipt = json.loads((DATA/(name+'.receipt.json')).read_text())
        if sha256(DATA/name) != receipt['sha256']: raise ValueError('Cached official metadata changed')
    records = list(csv.DictReader((DATA/'faraway2025_longread_ena').open(), delimiter='\t'))
    record = next(r for r in records if r['run_accession'] == RUN)
    if record['library_source'] != 'SYNTHETIC' or record['library_name'] != 'plasmid_sequencing_s':
        raise ValueError('Not the admitted plasmid DNA run')
    if int(record['fastq_bytes']) != SIZE or record['fastq_md5'] != MD5:
        raise ValueError('Official archive identity changed')
    sdrf = list(csv.DictReader((DATA/'faraway2025_longread_sdrf').open(), delimiter='\t'))
    sample = next(r for r in sdrf if r['Comment[ENA_RUN]'] == RUN)
    if sample['Material Type'] != 'DNA' or sample['Source Name'] != 'plasmid_sequencing' or sample['Comment[BioSD_SAMPLE]'] != record['sample_accession']:
        raise ValueError('SDRF does not identify admitted plasmid DNA')
    url = 'https://'+record['fastq_ftp']
    if not url.startswith('https://ftp.sra.ebi.ac.uk/'): raise ValueError('Unexpected archive host')
    dest = DATA/(RUN+'.fastq.gz')
    if not dest.exists():
        if shutil.disk_usage(DATA).free < 2*SIZE+1024**3: raise ValueError('Insufficient free disk space')
        def fetch(start):
            end = min(start+CHUNK, SIZE)
            p = DATA/'faraway_dna_chunks'/f'{start}-{end}.bin'
            if p.exists():
                if p.stat().st_size != end-start: raise ValueError('Saved range length changed')
                return p
            payload = bytearray(); last = None
            for attempt in range(4):
                offset = start+len(payload)
                try:
                    request = Request(url, headers={'User-Agent': 'RNAddress-provenance/1.0', 'Range': f'bytes={offset}-{end-1}'})
                    begun = time.monotonic()
                    with urlopen(request, timeout=20) as response:
                        if response.status != 206 or response.headers.get('Content-Range') != f'bytes {offset}-{end-1}/{SIZE}':
                            raise ValueError('Archive range mismatch')
                        while len(payload) < end-start:
                            if time.monotonic()-begun > 60: raise TimeoutError('Range deadline')
                            part = response.read1(min(65536, end-start-len(payload)))
                            if not part: break
                            payload.extend(part)
                    if len(payload) == end-start: break
                except (OSError, TimeoutError) as error:
                    last = str(error)
                    time.sleep(min(.5*2**attempt, 4))
            if len(payload) != end-start: raise RuntimeError(f'Incomplete range {start}: {last}')
            write_new(p, bytes(payload)); return p
        spans = list(range(0, SIZE, CHUNK))
        with ThreadPoolExecutor(max_workers=4) as pool:
            paths = []
            for i, p in enumerate(pool.map(fetch, spans)):
                paths.append(p)
                if (i+1)%8 == 0 or i+1 == len(spans):
                    print(json.dumps({'completed_ranges': i+1, 'ranges': len(spans)}), flush=True)
        # Assemble only after all ranges exist. No partial final file is admitted.
        body = b''.join(p.read_bytes() for p in paths)
        if len(body) != SIZE or hashlib.md5(body).hexdigest() != MD5:
            raise ValueError('Full archive MD5/size mismatch')
        write_new(dest, body)
    digest = hashlib.md5()
    with dest.open('rb') as f:
        for part in iter(lambda: f.read(8*1024**2), b''): digest.update(part)
    if dest.stat().st_size != SIZE or digest.hexdigest() != MD5:
        raise ValueError('Existing final file failed archive verification')
    count = bases = 0
    with gzip.open(dest, 'rb') as f:
        while True:
            header = f.readline()
            if not header: break
            seq = f.readline().rstrip(b'\r\n'); plus = f.readline(); quality = f.readline().rstrip(b'\r\n')
            if not header.startswith(b'@') or not plus.startswith(b'+') or not seq or len(seq) != len(quality):
                raise ValueError('Malformed or truncated FASTQ')
            count += 1; bases += len(seq)
    if count != int(record['read_count']) or bases != int(record['base_count']):
        raise ValueError('Read/base totals differ from official metadata')
    receipt = DATA/(dest.name+'.receipt.json')
    file_sha = sha256(dest)
    if receipt.exists() and json.loads(receipt.read_text())['sha256'] != file_sha:
        raise ValueError('Saved receipt differs from fully verified file')
    if not receipt.exists():
        write_json(receipt, {'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                   'bytes': SIZE, 'archive_md5': MD5, 'sha256': file_sha,
                   'reads': count, 'bases': bases, 'full_gzip_and_fastq_validated': True,
                   'provenance_files': {str(p.relative_to(ROOT)): sha256(p) for p in [
                       DATA/'faraway2025_longread_ena', DATA/'faraway2025_longread_sdrf',
                       ROOT/'reports/research_20260921/faraway_dna_provenance_spec.md',
                       ROOT/'src/research_20260921/faraway_dna_download.py']},
                   'scope': 'DNA-only genotype provenance; no RNA outcome files accessed.'})
    print(json.dumps({'verified_DNA_file': dest.name, 'reads': count, 'bases': bases, 'MD5': MD5}), flush=True)


if __name__ == '__main__': run()
