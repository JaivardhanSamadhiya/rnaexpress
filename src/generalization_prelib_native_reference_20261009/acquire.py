"""Frozen tiny public reference queries, no assay outcomes or executed code."""
from pathlib import Path
import ctypes,datetime,hashlib,json,re,subprocess,time,urllib.request,urllib.parse
ROOT=Path(__file__).resolve().parents[2];NS='generalization_prelib_native_reference_20261009';OUT=ROOT/'results'/NS;RAW=ROOT/'data/raw'/NS
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def fresh():
 class M(ctypes.Structure):
  _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
 m=M();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
 assert m.available>=1.3*2**30,'Bounded metadata1.3GiB floor; original feature/model3GiB unchanged'
 return m.available
def gb(body,accession):
 text=body.decode('ascii');versions=re.findall(r'^VERSION\s+(\S+)',text,re.M);assert versions==[accession]
 assert text.count('\nORIGIN')==1 and text.strip().endswith('//')
 origin=text.split('\nORIGIN',1)[1].split('//',1)[0]
 seq=re.sub(r'[\s0-9]','',origin).upper();assert seq and set(seq)<=set('ACGT')
 return seq
def hits(haystack,needle):
 starts=[];start=0
 while True:
  i=haystack.find(needle,start)
  if i<0:return starts
  starts.append(i);start=i+1
def rc(seq):return seq.translate(str.maketrans('ACGT','TGCA'))[::-1]
def run():
 fresh();mpath=OUT/'request_manifest.json';m=read(mpath)
 assert subprocess.check_output(['git','show','HEAD:'+mpath.relative_to(ROOT).as_posix()],cwd=ROOT)==mpath.read_bytes()
 for rel,h in m['files'].items():assert sha(ROOT/rel)==h
 start=time.monotonic();responses={};http=[];failures=[]
 for req in m['requests']:
  name=req['name']
  try:
   fresh();remaining=150-(time.monotonic()-start);assert remaining>0
   request=urllib.request.Request(req['URL'],headers={'User-Agent':'rnaexpress-free-native-reference-audit/1.0'})
   with urllib.request.urlopen(request,timeout=min(10,remaining)) as response:
    assert response.status==200 and urllib.parse.urlparse(response.geturl()).hostname in m['allowed_hosts']
    body=response.read(131073);assert len(body)<=131072
    record={'URL':req['URL'],'response_URL':response.geturl(),'status':response.status,'headers':dict(response.headers),'bytes':len(body),'SHA256':hashlib.sha256(body).hexdigest(),'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
   with (RAW/(name+req['suffix'])).open('xb') as f:f.write(body)
   save(RAW/(name+'.http.json'),record);http.append(record)
   if req['kind']=='RefSeq':responses[name]=gb(body,req['accession'])
   else:
    x=json.loads(body);assert x['genome']==req.get('genome','hg19') and x['chrom']==req['chrom']
    if req['kind']=='sequence':
     assert x['start']==req['start'] and x['end']==req['end'] and len(x['dna'])==req['end']-req['start']
     assert set(x['dna'].upper())<=set('ACGTN');responses[name]=x['dna'].upper()
    else:
     assert isinstance(x['refGene'],list) and len(x['refGene'])<=500
     responses[name]=x['refGene']
   print(name,'REFERENCE_METADATA',len(body),'bytes',flush=True)
  except Exception as error:
   x={'name':name,'error_class':type(error).__name__,'message':str(error),'URL':req['URL']};failures.append(x);save(OUT/(name+'_failure.json'),x);print(name,'PRESERVED_FAILURE',type(error).__name__,flush=True)
 source={x['source_excel_row']:x for x in read(ROOT/m['design'])['rows']};parents=read(ROOT/m['parents']);matches=[];missing=[]
 for parent in parents:
  if parent['mPRE_background'] or parent['lineage']=='IRF2BP1':continue
  seq=source[parent['source_excel_row']]['Sequence'];assert len(seq)==140 and set(seq)<=set('ACGT')
  if parent['lineage']=='NORAD':
   for accession in m['NORAD_accessions']:
    if accession not in responses:continue
    locations=hits(responses[accession],seq)
    matches.append({'lineage':'NORAD','prefix':parent['prefix'],'source_excel_row':parent['source_excel_row'],'reference_accession':accession,'reference_length':len(responses[accession]),
     'exact_forward140nt_intervals0based':[[i,i+140] for i in locations],'matches':len(locations),'full_reporter_RNA_certified':False})
  else:
   request=next(x for x in m['requests'] if x['name']==parent['lineage']+'_sequence')
   if request['name'] not in responses:missing.append(parent['prefix']);continue
   reference=responses[request['name']];query=seq if request['strand']=='+' else rc(seq);locations=hits(reference,query);annotations=responses.get(parent['lineage']+'_refGene',[])
   for location in locations:
    a=request['start']+location;b=a+140;covering=[]
    for item in annotations:
     if item['strand']!=request['strand']:continue
     starts=[int(x) for x in item['exonStarts'].strip(',').split(',')];ends=[int(x) for x in item['exonEnds'].strip(',').split(',')]
     if any(u<=a and b<=v for u,v in zip(starts,ends)):covering.append({k:item[k] for k in ('name','name2','chrom','strand','txStart','txEnd')})
    matches.append({'lineage':parent['lineage'],'prefix':parent['prefix'],'source_excel_row':parent['source_excel_row'],'reference':'hg19','chrom':request['chrom'],'strand':request['strand'],'exact140nt_interval0based':[a,b],
     'reference_window_match_count':len(locations),'covering_refGene_exon_annotations':covering,'genome_assembly_uniqueness_or_full_reporter_RNA_certified':False})
   if not locations:missing.append(parent['prefix'])
 comparison=[]
 if 'SMARCA2_hg38_sequence' in responses:
  parent=next(x for x in parents if x['lineage']=='SMARCA2' and not x['mPRE_background'])
  seq=source[parent['source_excel_row']]['Sequence'];request=next(x for x in m['requests'] if x['name']=='SMARCA2_hg38_sequence')
  comparison=[{'lineage':'SMARCA2','reference':'hg38_same_numeric_coordinate_comparison','whole140nt_hits0based':[[request['start']+i,request['start']+i+140] for i in hits(responses['SMARCA2_hg38_sequence'],seq)],'unique_source_assembly_not_inferred':True}]
 save(OUT/'literal_native_reference_matches.json',{'SMARCA2_hg38_fixed_comparison':comparison,'matches':matches,'genomic_no_exact_match_or_unavailable':missing,'all_match_locations_retained':True,'no_mutant_or_engineered_reference_identity_inferred':True})
 save(OUT/'reference_receipt.json',{'status':'COMPLETE_FIXED_REFERENCE_QUERIES_REVIEW_MATCHES' if not failures else 'PARTIAL_FIXED_REFERENCE_QUERY_FAILURES_PRESERVED',
  'manifest_sha256':sha(mpath),'http_records':http,'failures':failures,'match_record_count':len(matches),'genomic_no_exact_match_or_unavailable':missing,
  'matches_sha256':sha(OUT/'literal_native_reference_matches.json'),'elapsed_seconds':time.monotonic()-start,'cost':0,'assay_outcomes_read':False,'models_fit':0,
  'hg19_is_fixed_comparison_not_uniquely_certified_source_assembly':True,'versioned_NORAD_records_not_silently_substituted':True})
if __name__=='__main__':run()
