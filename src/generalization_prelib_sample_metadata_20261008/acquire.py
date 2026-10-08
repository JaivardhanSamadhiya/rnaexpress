"""One bounded public ENA study metadata request, no sequence/count download."""
from pathlib import Path
import csv,datetime,hashlib,io,json,subprocess,urllib.request,urllib.parse
ROOT=Path(__file__).resolve().parents[2];NS='generalization_prelib_sample_metadata_20261008';OUT=ROOT/'results'/NS;RAW=ROOT/'data/raw'/NS

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2)+'\n').encode())
def run():
 p=OUT/'request_manifest.json';m=json.loads(p.read_text())
 assert subprocess.check_output(['git','show','HEAD:'+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 for name,digest in m['files'].items():assert sha(ROOT/name)==digest,name
 try:
  request=urllib.request.Request(m['URL'],headers={'User-Agent':'rnaexpress-public-sample-metadata/1.0','Accept':'text/tab-separated-values'})
  with urllib.request.urlopen(request,timeout=45) as response:
   assert response.status==200 and urllib.parse.urlparse(response.geturl()).hostname=='www.ebi.ac.uk'
   body=response.read(m['response_cap_bytes']+1);assert len(body)<=m['response_cap_bytes']
   http={'URL':m['URL'],'response_URL':response.geturl(),'HTTP_status':response.status,'headers':dict(response.headers),'bytes':len(body),'SHA256':hashlib.sha256(body).hexdigest(),'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  with (RAW/'public_study_sample_metadata.tsv').open('xb') as f:f.write(body)
  save(RAW/'public_study_sample_metadata.http.json',http)
  reader=csv.DictReader(io.StringIO(body.decode('utf-8-sig')),delimiter='\t')
  assert reader.fieldnames==m['fields'],'Unexpected metadata fields/order'
  rows=list(reader);assert 1<=len(rows)<=500 and all(set(row)==set(m['fields']) and all(isinstance(v,str) and len(v)<=20000 for v in row.values()) for row in rows)
  assert len({row['run_accession'] for row in rows})==len(rows)
  save(OUT/'sample_metadata_rows.json',{'rows':rows,'only_requested_metadata_fields':True,'pairing_certificate_inferred':False,'actual_count_values_or_FASTQ_requested':False})
  save(OUT/'sample_metadata_receipt.json',{'status':'PASS_ONE_BOUNDED_PUBLIC_ENA_SAMPLE_METADATA_REQUEST','manifest_sha256':sha(p),'http':http,'metadata_rows':len(rows),'fields':m['fields'],'rows_sha256':sha(OUT/'sample_metadata_rows.json'),'cost':0,'models_fit':0,'training_pairs_admitted':0,'sample_pairing_not_automatically_certified':True})
  print('PUBLIC_SAMPLE_METADATA',len(rows),'rows; bytes',len(body),flush=True)
  for row in rows:
   if any('prelibb' in row[field].lower() or 'prelib_b' in row[field].lower() or 'libb' in row[field].lower() for field in ('sample_title','experiment_title','library_name','sample_alias')):
    print(json.dumps({field:row[field] for field in ('run_accession','experiment_accession','sample_accession','sample_alias','sample_title','experiment_title','library_name','cell_line')},sort_keys=True),flush=True)
 except Exception as error:
  save(OUT/'metadata_failure.json',{'status':'BOUNDED_PUBLIC_METADATA_REQUEST_OR_PARSE_FAILURE','exception_type':type(error).__name__,'error':str(error),'URL':m['URL'],'no_retries_or_substitution':True,'no_RAW_FASTQ_or_counts_requested':True})
  raise
if __name__=='__main__':run()
