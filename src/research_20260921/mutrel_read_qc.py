"""Bounded public FASTQ-prefix genotype QC; no fraction/outcome association."""
from .common import ROOT,sha256,write_new,write_json
import json,urllib.request,zlib,hashlib
from collections import Counter
from datetime import datetime,timezone

DATA=ROOT/'data/external/research_20260921'
OUT=ROOT/'results/research_20260921'

def prefix(url,name,size=2*1024*1024):
    path=DATA/name;receipt=DATA/(name+'.receipt.json')
    if receipt.exists():
        if sha256(path)!=json.loads(receipt.read_text())['sha256']:raise ValueError('Prefix changed')
        return path.read_bytes()
    request=urllib.request.Request(url,headers={'Range':f'bytes=0-{size-1}','User-Agent':'RNAddress-public-genotype-QC/1.0'})
    with urllib.request.urlopen(request,timeout=45) as r:
        if r.status!=206 or not r.headers.get('Content-Range','').startswith(f'bytes 0-{size-1}/'):
            raise ValueError('Server did not honor bounded range request')
        payload=r.read(size+1)
        if len(payload)!=size:raise ValueError('Unexpected prefix size')
        crange=r.headers['Content-Range']
    write_new(path,payload)
    write_json(receipt,{'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                        'bytes':size,'sha256':sha256(path),'partial':True,'content_range':crange,
                        'full_archive_MD5_verified':False,'purpose':'Genotype co-occurrence QC only; no compartment labels'})
    return payload

def reads(payload):
    lines=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(payload).decode('ascii').splitlines()
    result=[]
    for i in range(0,len(lines)-3,4):
        h,s,plus,q=lines[i:i+4]
        if not h.startswith('@') or not plus.startswith('+') or len(s)!=len(q):raise ValueError('Malformed complete FASTQ record')
        result.append((h.split()[0].removesuffix('/1').removesuffix('/2'),s,q))
    return result

def align(sequence,quality,reference):
    candidates=[]
    for reverse in [False,True]:
        s=sequence.translate(str.maketrans('ACGTN','TGCAN'))[::-1] if reverse else sequence
        q=quality[::-1] if reverse else quality
        offsets=set()
        # Four fixed exact seeds; deliberately a subset/QC, not an exhaustive mapper.
        for start in [0,40,80,120]:
            seed=reference[start:start+15];p=s.find(seed)
            while p>=0:
                offsets.add(p-start);p=s.find(seed,p+1)
        for offset in offsets:
            calls={i:(s[i+offset],ord(q[i+offset])-33) for i in range(len(reference)) if 0<=i+offset<len(s)}
            high={i:b for i,(b,phred) in calls.items() if phred>=30 and b in 'ACGT'}
            matches=sum(b==reference[i] for i,b in high.items())
            mismatches=len(high)-matches
            if len(high)>=60 and mismatches<=.1*len(high):
                candidates.append((matches,-mismatches,high,reverse,offset))
    if not candidates:return None
    candidates.sort(key=lambda c:(c[0],c[1]),reverse=True)
    return candidates[0][2]

def run():
    reference=json.loads((OUT/'mutrel_reference_inventory.json').read_text())['sequence']
    metadata=json.loads((DATA/'mutrel_ena_runs.json').read_text())[0]
    urls=['https://'+u for u in metadata['fastq_ftp'].split(';')]
    a=reads(prefix(urls[0],'SRR6308285_1.first2MiB.gz'))
    b=reads(prefix(urls[1],'SRR6308285_2.first2MiB.gz'))
    count=min(2000,len(a),len(b));hist=Counter(); mapped=0;discordant=0;examples=[]
    for (ha,sa,qa),(hb,sb,qb) in zip(a[:count],b[:count]):
        if ha!=hb:raise ValueError('Mate identifiers differ')
        aa=align(sa,qa,reference);bb=align(sb,qb,reference)
        if aa is None or bb is None:continue
        shared=set(aa)&set(bb)
        if len(shared)<40:continue
        if any(aa[i]!=bb[i] for i in shared):discordant+=1;continue
        mapped+=1
        variants=[f'{i+1}{reference[i]}>{aa[i]}' for i in sorted(shared) if aa[i]!=reference[i]]
        hist[len(variants)]+=1
        if len(variants)>=2 and len(examples)<10:examples.append({'read_id_sha256':hashlib.sha256(ha.encode()).hexdigest(),'mate_confirmed_variants':variants,'shared_Q30_bases':len(shared)})
    result={'source_run':'SRR6308285','inspected_read_pairs':count,'both_mates_aligned_with_40_shared_Q30_bases':mapped,
            'discordant_pairs_excluded':discordant,'mate_confirmed_substitution_counts':dict(sorted(hist.items())),
            'pairs_with_multiple_confirmed_substitutions':sum(v for k,v in hist.items() if k>=2),'examples':examples,
            'scope':'Convenience prefixes, exact-seed ungapped subset alignment, Q30 on both mates. Not an unbiased library mutation-rate estimate; indels unassessed. No compartment labels or localization count outcomes used.',
            'interpretation':'Multiple confirmed substitutions show co-occurrence in sampled library molecules if present; this alone cannot establish whether the authors filtered to isolated mutants when making their processed table.',
            'full_file_md5_verified':False,'code_sha256':sha256(ROOT/'src/research_20260921/mutrel_read_qc.py')}
    write_json(OUT/'mutrel_read_prefix_qc.json',result);print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':run()
