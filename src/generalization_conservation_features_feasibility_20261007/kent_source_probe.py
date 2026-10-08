"""Bounded official released-source inspection; never genomic values."""
from pathlib import Path
import datetime,hashlib,json,time,urllib.request,urllib.error,urllib.parse,sys
ROOT=Path('D:/rnaexpress');OUT=ROOT/'artifacts/generalization_conservation_features_feasibility_20261007/kent_source'
CAP=1024*1024
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  assert urllib.parse.urlparse(newurl).hostname in ('api.github.com','raw.githubusercontent.com')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(name,url):
 assert urllib.parse.urlparse(url).hostname in ('api.github.com','raw.githubusercontent.com')
 assert '/ucscGenomeBrowser/kent/' in url
 OUT.mkdir(parents=True,exist_ok=True);p=OUT/(name+'.body');r=OUT/(name+'.receipt.json')
 assert not p.exists() and not r.exists(),'Preserve existing source response'
 rec={'url':url,'scope':'official_code_or_release_metadata_only_no_annotation_values','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cap_bytes':CAP,'retry_count':0,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};data=None
 time.sleep(1.05)
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'RNA-localization-source-metadata-audit/1.0','Accept':'application/vnd.github+json'})
  with urllib.request.build_opener(Redirect).open(req,timeout=30) as resp:
   rec.update(http_status=resp.status,final_url=resp.url,headers=dict(resp.headers))
   assert int(resp.headers.get('Content-Length','0'))<=CAP,'Declared response exceeds source cap'
   data=resp.read(CAP+1);assert len(data)<=CAP,'Response exceeds source cap'
  rec['status']='PUBLIC_SOURCE_RESPONSE_OBSERVED'
 except urllib.error.HTTPError as err:
  rec.update(http_status=err.code,status='UNRESOLVED_SOURCE_RESPONSE',error=str(err))
  data=err.read(CAP+1)
 except Exception as err:
  rec.update(http_status=0,status='UNRESOLVED_SOURCE_RESPONSE',error=type(err).__name__+': '+str(err))
 if data is not None and len(data)<=CAP:
  p.write_bytes(data);rec.update(body_bytes=len(data),body_sha256=hashlib.sha256(data).hexdigest())
 else: rec.update(body_bytes=0,body_sha256=None)
 r.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps(rec,indent=2),flush=True)
 if data is not None and len(data)<=CAP:print(data.decode('utf-8')[:12000],flush=True)
if __name__=='__main__':fetch(sys.argv[1],sys.argv[2])