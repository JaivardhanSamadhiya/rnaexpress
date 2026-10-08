"""Metadata-only source feasibility; no genomic or aligned-site requests."""
from pathlib import Path
import datetime, hashlib, json, time, urllib.request, urllib.error
ROOT=Path('D:/rnaexpress')
DEST=ROOT/'artifacts/generalization_conservation_features_feasibility_20261007/ensembl_metadata'
DEST.mkdir(parents=True,exist_ok=True)
SPEC=[('mouse_assembly','/info/assembly/mus_musculus'),('species','/info/species'),('compara_methods','/info/compara/methods'),('data_release','/info/data')]
CAP=4*1024*1024
class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if urllib.parse.urlparse(newurl).hostname!='grch37.rest.ensembl.org':
            raise ValueError('Cross-host redirect rejected')
        return super().redirect_request(req,fp,code,msg,headers,newurl)
OPENER=urllib.request.build_opener(RestrictedRedirect)
for name, endpoint in SPEC:
    body=DEST/(name+'.json')
    receipt=DEST/(name+'.receipt.json')
    if body.exists() or receipt.exists():
        raise FileExistsError('Immutable metadata response or receipt already exists: '+name)
    url='https://grch37.rest.ensembl.org'+endpoint
    rec={'url':url,'scope':'metadata_only_no_site_values','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cap_bytes':CAP,'retry_count':0}
    data=None
    time.sleep(1.05)
    try:
        req=urllib.request.Request(url,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'RNA-localization-metadata-audit/1.0'})
        with OPENER.open(req,timeout=30) as resp:
            rec['http_status']=resp.status
            rec['final_url']=resp.url
            rec['headers']=dict(resp.headers)
            declared=resp.headers.get('Content-Length')
            if declared is not None and int(declared)>CAP:
                raise ValueError('Declared metadata response exceeds cap')
            data=resp.read(CAP+1)
            if len(data)>CAP:
                raise ValueError('Metadata response exceeds cap')
        parsed=json.loads(data)
        rec['json_top_level']=type(parsed).__name__
        rec['status']='PUBLIC_METADATA_RESPONSE_OBSERVED'
    except Exception as error:
        rec.setdefault('http_status',getattr(error,'code',0))
        rec['status']='UNRESOLVED_METADATA_RESPONSE'
        rec['error']=type(error).__name__+': '+str(error)
    if data is not None and len(data)<=CAP:
        body.write_bytes(data)
        rec['body_bytes']=len(data)
        rec['body_sha256']=hashlib.sha256(data).hexdigest()
    else:
        rec['body_bytes']=0
        rec['body_sha256']=None
    receipt.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(name,rec['status'],rec['http_status'],rec['body_bytes'],flush=True)