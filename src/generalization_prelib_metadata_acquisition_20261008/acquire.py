from pathlib import Path
import json,hashlib,subprocess,urllib.request,urllib.error,urllib.parse,zipfile,io,time
ROOT=Path(__file__).resolve().parents[2];NS="generalization_prelib_metadata_acquisition_20261008"
OUT=ROOT/"results"/NS;RAW=ROOT/"data/raw"/NS
HOSTS={"pmc.ncbi.nlm.nih.gov","www.ncbi.nlm.nih.gov","oup.silverchair-cdn.com","academic.oup.com"}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):
 with p.open("xb") as f:f.write((json.dumps(value,sort_keys=True,indent=2)+"\n").encode())
def run():
 path=OUT/"request_manifest.json";body=path.read_bytes();plan=json.loads(body)
 assert subprocess.check_output(["git","show","HEAD:"+path.relative_to(ROOT).as_posix()],cwd=ROOT)==body
 source=ROOT/"results"/NS/"source_manifest.json"
 pins=json.loads(source.read_bytes())
 assert subprocess.check_output(["git","show","HEAD:"+source.relative_to(ROOT).as_posix()],cwd=ROOT)==source.read_bytes()
 for name,digest in pins["files"].items():assert sha(ROOT/name)==digest,name
 assert plan["maximum_requests"]==2 and not plan["paid_access_or_purchase_allowed"]
 assert not (OUT/"acquisition_receipt.json").exists()
 attempts=[]
 for i,item in enumerate(plan["requests"],1):
  url=item["url"];assert urllib.parse.urlsplit(url).scheme=="https" and urllib.parse.urlsplit(url).hostname in HOSTS
  attempt={"request_url":url,"attempt":i,"response_url":None,"http_status":None,"body_SHA256":None,"bytes":0}
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"RNA-localization computational research metadata audit; Python urllib","Accept":"application/zip,application/octet-stream"})
   with urllib.request.urlopen(req,timeout=45) as response:
    final=response.geturl();assert urllib.parse.urlsplit(final).scheme=="https" and urllib.parse.urlsplit(final).hostname in HOSTS
    attempt.update(response_url=final,http_status=response.status,headers=dict(response.headers.items()))
    payload=response.read(plan["per_response_byte_cap"]+1)
   attempt.update(bytes=len(payload),body_SHA256=hashlib.sha256(payload).hexdigest())
   assert len(payload)<=plan["per_response_byte_cap"],"Response byte cap exceeded"
   assert payload.startswith(b"PK\x03\x04"),"Response is not ZIP archive bytes"
   with zipfile.ZipFile(io.BytesIO(payload)) as archive:
    infos=archive.infolist();assert 0<len(infos)<=plan["archive_member_cap"]
    assert sum(x.file_size for x in infos)<=plan["total_uncompressed_cap"]
    assert not any(x.flag_bits&1 for x in infos),"Encrypted archive forbidden"
    assert archive.testzip() is None,"Archive CRC mismatch"
    inventory=[{"member":x.filename,"stored_bytes":x.compress_size,"uncompressed_bytes":x.file_size,"CRC32":f"{x.CRC:08x}"} for x in infos]
   output=RAW/"gkae929_supplemental_files.zip"
   with output.open("xb") as f:f.write(payload)
   attempt["status"]="PASS_PRIMARY_PUBLIC_ARCHIVE_BYTES_CRC_AND_INVENTORY";attempts.append(attempt)
   save(OUT/"acquisition_receipt.json",{"status":attempt["status"],"request_manifest_sha256":sha(path),"source_manifest_sha256":sha(source),
      "attempts":attempts,"archive_path":output.relative_to(ROOT).as_posix(),"archive_sha256":sha(output),"archive_bytes":len(payload),
      "member_inventory":inventory,"bytewise_CRC_decompression_includes_outcome_bearing_files":True,
      "worksheet_or_count_values_semantically_analyzed":False,"downloaded_numerical_supplements_not_an_untouched_holdout_claim":True,
      "training_pairs_admitted":0,"models_fit":0,"cost":0})
   print("PASS fixed free supplement",len(payload),"bytes",len(inventory),"members; values not analyzed",flush=True)
   return
  except Exception as error:
   attempt["status"]="FAILED_FIXED_ENDPOINT";attempt["error_type"]=type(error).__name__;attempt["error"]=str(error);attempts.append(attempt)
   save(OUT/("attempt_"+str(i)+"_failure.json"),attempt)
   print("Preserved fixed endpoint failure",i,type(error).__name__,str(error),flush=True)
 save(OUT/"acquisition_receipt.json",{"status":"FAILED_BOTH_FIXED_PUBLIC_ENDPOINTS","attempts":attempts,"request_manifest_sha256":sha(path),
      "worksheet_values_analyzed":False,"models_fit":0,"no_further_automatic_retry":True})
 raise RuntimeError("No admitted public ZIP from fixed two-endpoint plan")
if __name__=="__main__":run()
