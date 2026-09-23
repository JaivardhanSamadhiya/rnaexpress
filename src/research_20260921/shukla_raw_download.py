"""One official public ENA raw file, bounded by verified archive metadata."""
from .common import ROOT,sha256,write_json,write_new
from datetime import datetime,timezone
import hashlib,json,shutil,urllib.request,time,concurrent.futures


def finish_tail(partial,url,expected):
    """Finish a stalled small tail with bounded, independently verified ranges."""
    start=partial.stat().st_size
    spans=[(a,min(a+1024**2,expected)) for a in range(start,expected,1024**2)]
    def fetch(span):
        a,b=span;path=partial.parent/'shukla_raw_chunks'/f'{a}-{b}.bin'
        if path.exists():
            if path.stat().st_size!=b-a:raise ValueError('Invalid saved chunk')
            return path
        begun=time.monotonic();payload=bytearray()
        for attempt in range(6):
            offset=a+len(payload)
            request=urllib.request.Request(url,headers={'Range':f'bytes={offset}-{b-1}','User-Agent':'RNAddress-public-data-audit/1.0'})
            with urllib.request.urlopen(request,timeout=20) as response:
                if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {offset}-{b-1}/{expected}':
                    raise ValueError('Tail range mismatch')
                while len(payload)<b-a:
                    if time.monotonic()-begun>240:raise TimeoutError('Bounded tail download exceeded 240 seconds')
                    chunk=response.read1(min(65536,b-a-len(payload)))
                    if not chunk:break
                    payload.extend(chunk)
            if len(payload)==b-a:break
        if len(payload)!=b-a:raise ValueError(('Incomplete tail chunk',a,len(payload),b-a))
        write_new(path,bytes(payload));print(json.dumps({'verified_tail_range':[a,b]}),flush=True)
        return path
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        paths=list(pool.map(fetch,spans))
    if partial.stat().st_size!=start:raise ValueError('Another writer changed partial file')
    with partial.open('ab') as stream:
        for path in paths:stream.write(path.read_bytes())


def run():
    data=ROOT/'data/external/research_20260921'
    record=next(r for r in json.loads((data/'shukla2018_ena_runs.json').read_text()) if r['run_accession']=='SRR5528987')
    if record['sample_title']!='HeLa_BR_1_TR_1_Total':raise ValueError('Unexpected sample')
    expected=int(record['fastq_bytes']);md5=record['fastq_md5'];url='https://'+record['fastq_ftp']
    if expected!=581039199 or md5!='d3660208a08420ee2f0e65f48f478032':raise ValueError('Archive identity changed')
    destination=data/'SRR5528987.fastq.gz';partial=data/'SRR5528987.fastq.gz.part'
    if not destination.exists():
        if partial.exists() and 0<expected-partial.stat().st_size<128*1024**2:
            finish_tail(partial,url,expected)
        start=partial.stat().st_size if partial.exists() else 0
        if start>expected:raise ValueError('Oversized partial')
        if shutil.disk_usage(data).free<expected-start+1024**3:raise ValueError('Insufficient disk space')
        if start<expected:
            request=urllib.request.Request(url,headers={'User-Agent':'RNAddress-public-data-audit/1.0','Range':f'bytes={start}-{expected-1}'})
            with urllib.request.urlopen(request,timeout=45) as response:
                if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{expected-1}/{expected}':
                    raise ValueError('Range response does not match requested public file')
                total=start;report=start//(64*1024**2)
                with partial.open('ab' if start else 'xb') as stream:
                    while True:
                        chunk=response.read(1024**2)
                        if not chunk:break
                        total+=len(chunk)
                        if total>expected:raise ValueError('Server exceeded declared size')
                        stream.write(chunk)
                        if total//(64*1024**2)>report:
                            report=total//(64*1024**2);print(json.dumps({'downloaded_bytes':total,'expected_bytes':expected}),flush=True)
        if partial.stat().st_size!=expected:raise ValueError('Incomplete transfer; partial retained for resume')
        h=hashlib.md5()
        with partial.open('rb') as stream:
            for chunk in iter(lambda:stream.read(8*1024**2),b''):h.update(chunk)
        if h.hexdigest()!=md5:raise ValueError('Archive MD5 mismatch; partial not admitted')
        partial.rename(destination)
    h=hashlib.md5()
    with destination.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024**2),b''):h.update(chunk)
    if destination.stat().st_size!=expected or h.hexdigest()!=md5:raise ValueError('Existing full file fails archive verification')
    prefix=(data/'SRR5528987.first16MiB.gz').read_bytes()
    with destination.open('rb') as stream:
        if stream.read(len(prefix))!=prefix:raise ValueError('Previous raw prefix differs from verified full file')
    receipt=data/'SRR5528987.fastq.gz.receipt.json'
    if not receipt.exists():
        write_json(receipt,{'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),
            'bytes':expected,'archive_md5':md5,'sha256':sha256(destination),'full_archive_MD5_verified':True,
            'first16MiB_matches_previous_prefix':True,'sample':record['sample_title'],
            'purpose':'Raw/processed Total1 count reconciliation; no reserved replicate access'})
    print('Verified full raw file MD5, size, SHA256 and earlier prefix identity.',flush=True)


if __name__=='__main__':run()
