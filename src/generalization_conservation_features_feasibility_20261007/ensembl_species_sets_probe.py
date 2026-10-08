"""One documented comparative species-set metadata request; no aligned bases."""
from pathlib import Path
import datetime, hashlib, json, time, urllib.request, urllib.error
ROOT=Path('D:/rnaexpress')
DEST=ROOT/'artifacts/generalization_conservation_features_feasibility_20261007/ensembl_metadata'
name='lastz_net_species_sets'
body=DEST/(name+'.json')
receipt=DEST/(name+'.receipt.json')
if body.exists() or receipt.exists():
    raise FileExistsError('Immutable metadata body/receipt exists')
CAP=4*1024*1024
url='https://grch37.rest.ensembl.org/info/compara/species_sets/LASTZ_NET'
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if urllib.parse.urlparse(newurl).hostname!='grch37.rest.ensembl.org':
            raise ValueError('Cross-host redirect rejected')
        return super().redirect_request(req,fp,code,msg,headers,newurl)
rec={'url':url,'scope':'species_assembly_method_metadata_only','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cap_bytes':CAP,'retry_count':0,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
data=None
time.sleep(1.05)
try:
    req=urllib.request.Request(url,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'RNA-localization-metadata-audit/1.0'})
    with urllib.request.build_opener(Redirect).open(req,timeout=30) as resp:
        rec.update(http_status=resp.status,final_url=resp.url,headers=dict(resp.headers))
        if int(resp.headers.get('Content-Length','0'))>CAP:
            raise ValueError('Declared response exceeds cap')
        data=resp.read(CAP+1)
        if len(data)>CAP:
            raise ValueError('Response exceeds cap')
    parsed=json.loads(data)
    rec.update(status='PUBLIC_METADATA_RESPONSE_OBSERVED',json_top_level=type(parsed).__name__)
except Exception as err:
    rec.setdefault('http_status',getattr(err,'code',0))
    rec.update(status='UNRESOLVED_METADATA_RESPONSE',error=type(err).__name__+': '+str(err))
if data is not None and len(data)<=CAP:
    body.write_bytes(data)
    rec.update(body_bytes=len(data),body_sha256=hashlib.sha256(data).hexdigest())
else:
    rec.update(body_bytes=0,body_sha256=None)
receipt.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(rec['status'],rec['http_status'],rec['body_bytes'],flush=True)
if data is not None and len(data)<=CAP:
    print(data.decode('utf-8')[:12000],flush=True)