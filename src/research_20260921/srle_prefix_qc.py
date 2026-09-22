"""Bounded public FASTQ prefix QC; no localization outcome calculation."""
from .common import ROOT,write_json,write_new,sha256
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,re,urllib.request,zlib

DATA=ROOT/'data/external/research_20260921'
OUT=ROOT/'results/research_20260921'
RUNS={'HRR3059162','HRR3059165','HRR3059175','HRR3059176'}


def inspect(row):
    name=row['runFileName']; run=row['runAcc']
    if run not in RUNS or name not in (run+'_f1.fq.gz',run+'_r2.fq.gz'):
        raise ValueError('Unexpected source')
    url=f'https://download.cncb.ac.cn/gsa-human/HRA016642/{run}/{name}'
    path=DATA/'srle_prefix_qc'/(name+'.prefix.bin')
    receipt=path.with_suffix('.bin.receipt.json')
    if not receipt.exists():
        request=urllib.request.Request(url,headers={'Range':'bytes=0-524287'})
        with urllib.request.urlopen(request,timeout=45) as response:
            content_range=response.headers.get('Content-Range','')
            if response.status !=206 or not content_range.startswith('bytes 0-524287/'):
                raise ValueError('Server did not honor prefix range')
            payload=response.read(524289)
            if len(payload)!=524288: raise ValueError('Incomplete prefix')
        write_new(path,payload)
        write_json(receipt,dict(url=url,bytes=len(payload),content_range=content_range,
            sha256=sha256(path),retrieved_utc=datetime.now(timezone.utc).isoformat(),
            partial_only=True,full_archive_checksum_verified=False))
    else:
        if sha256(path)!=json.loads(receipt.read_text())['sha256']: raise ValueError('Prefix changed')
    decoded=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(path.read_bytes(),16*1024*1024)
    lines=decoded.splitlines()
    records=[]
    for i in range(0,min((len(lines)//4)*4,4000),4):
        name_b,seq,plus,qual=lines[i:i+4]
        if not name_b.startswith(b'@') or not plus.startswith(b'+') or len(seq)!=len(qual): break
        records.append((name_b,seq))
    lengths=Counter(); six=0
    patterns=[re.compile(b'ATCACTAAGC([ACGT]+?)ATCATAATCA'),re.compile(b'TGATTATGAT([ACGT]+?)GCTTAGTGAT')]
    for _,seq in records:
        for pattern in patterns:
            for match in pattern.finditer(seq):
                lengths[len(match.group(1))]+=1
                six+=len(match.group(1))==6
    result={'run':run,'sample':row['runTitle'],'file':row['runFileName'],
        'prefix_bytes':len(path.read_bytes()),'reads_inspected':len(records),
        'six_base_flanked_hits':six,'all_flanked_insert_lengths':dict(lengths),
        'first_header':records[0][0].decode() if records else None,
        'ordered_read_sequence_sha256':hashlib.sha256(b'\n'.join(s for _,s in records)).hexdigest(),
        'ordered_read_header_sha256':hashlib.sha256(b'\n'.join(n for n,_ in records)).hexdigest(),
        'scope':'Technical prefix QC only; not complete-file validation or outcome scoring'}
    print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':
    rows=json.loads((DATA/'srle_gsa_runs_all').read_text())['runViews']
    selected=[r for r in rows if r['runAcc'] in RUNS]
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(inspect,selected))
    write_json(OUT/'srle_replicate3_prefix_qc.json',results)
