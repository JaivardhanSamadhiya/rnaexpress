"""Fixed-URL immutable capped public requests; no retry or overwrite."""
from pathlib import Path
from datetime import datetime,timezone
import time,urllib.request,urllib.error,urllib.parse
from . import common as c
class BudgetExceeded(RuntimeError):pass
def official(url):
 p=urllib.parse.urlsplit(url)
 return p.scheme=='https' and p.netloc=='api.genome.ucsc.edu' and p.path in ('/list/schema','/getData/track')
class ExactRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if not official(newurl) or newurl!=req.full_url:raise urllib.error.URLError('Refuse changed URL or untrusted redirect')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def cached(path,url,hasher=c.sha):
 p=Path(path);r=p.with_name(p.name+'.receipt.json')
 if not r.exists():
  assert not p.exists() and not r.with_name(r.name+'.sha256.json').exists() and not p.with_name(p.name+'.oversize_prefix.bin').exists(),'Orphaned response/creation receipt'
  return None,None
 birth=r.with_name(r.name+'.sha256.json');assert birth.is_file() and c.read(birth)['receipt_sha256']==hasher(r),'Changed receipt creation bytes'
 d=c.read(r);assert d['url']==url
 if d['sha256'] is None:
  assert not p.exists(),'Failed response acquired unbound bytes'
  if d.get('oversize_prefix_path'):
   prefix=p.parent/d['oversize_prefix_path'];assert prefix.resolve().parent==p.parent.resolve() and not prefix.is_symlink()
   assert hasher(prefix)==d['oversize_prefix_sha256']
  return None,d
 assert p.is_file() and not p.is_symlink() and hasher(p)==d['sha256'] and p.stat().st_size==d['bytes']
 return (p.read_bytes() if d['http_status']==200 and not d.get('failure') else None),d
class Client:
 def __init__(self,allowed,opener=None,sleep=time.sleep,total_used=None):
  self.allowed=set(allowed);assert self.allowed and all(official(u) for u in self.allowed)
  self.opener=urllib.request.build_opener(ExactRedirect()) if opener is None else opener
  self.sleep=sleep;self.new_requests=0
  self.total_used=sum(c.read(r).get('acquired_bytes',c.read(r).get('bytes',0)) for r in c.ART.rglob('*.receipt.json')) if total_used is None else total_used
  assert self.total_used<=c.MAX_TOTAL
 def get(self,url,path):
  assert url in self.allowed and official(url),'Only fixed source requests allowed'
  p=Path(path);assert p.resolve().is_relative_to(c.ART.resolve()) and not p.is_symlink()
  b,d=cached(p,url)
  if d is not None:return b,d
  remaining=c.MAX_TOTAL-self.total_used
  if remaining<=1:raise BudgetExceeded('Total public bytes exhausted before request')
  cap=min(c.MAX_RESPONSE,remaining-1)
  self.sleep(c.RATE);self.new_requests+=1
  d={'url':url,'http_status':0,'bytes':0,'sha256':None,'acquired_bytes':0,'public_free':True,'account_or_payment':False,'terms_url':'https://genome.ucsc.edu/license/','scope':'Frozen native conservation metadata/values only, no phenotypes','accessed_utc':datetime.now(timezone.utc).isoformat()}
  payload=None
  try:
   request=urllib.request.Request(url,headers={'User-Agent':'RNA-localization-academic-native-annotation-audit/1.0'})
   try:r=self.opener.open(request,timeout=45)
   except urllib.error.HTTPError as error:r=error
   with r:
    d.update(http_status=r.status if hasattr(r,'status') else r.code,final_url=r.geturl(),content_type=r.headers.get('Content-Type',''))
    if d['final_url']!=url or not official(d['final_url']):d['failure']='untrusted_or_changed_final_url'
    elif r.headers.get('Content-Length') and int(r.headers['Content-Length'])>cap:d['failure']='declared_byte_cap_exceeded_no_body_read'
    else:
     payload=r.read(cap+1);d['acquired_bytes']=len(payload);self.total_used+=len(payload)
     if len(payload)>cap:
      prefix=p.with_name(p.name+'.oversize_prefix.bin');c.save(prefix,payload[:cap])
      d.update(failure='byte_cap_exceeded',oversize_prefix_path=prefix.name,oversize_prefix_sha256=c.sha(prefix));payload=None
     elif payload is not None:
      c.save(p,payload);d.update(bytes=len(payload),sha256=c.sha(p))
      if d['http_status']!=200:d['failure']='HTTP_status_not_complete_200'
  except (urllib.error.URLError,TimeoutError,OSError,ValueError) as error:d['failure']='transport_failure:'+str(error);payload=None
  receipt=p.with_name(p.name+'.receipt.json');c.jsave(receipt,d)
  c.jsave(receipt.with_name(receipt.name+'.sha256.json'),{'receipt_sha256':c.sha(receipt),'birth_scope':'immutable first-creation raw public response receipt'})
  return (payload if d['http_status']==200 and not d.get('failure') else None),d
