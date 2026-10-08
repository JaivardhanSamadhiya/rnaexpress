from pathlib import Path
import json,hashlib,subprocess,urllib.request,urllib.parse,re,csv,io,concurrent.futures
ROOT=Path(__file__).resolve().parents[2];NS="generalization_pum2_parameter_metadata_20261008";OUT=ROOT/"results"/NS;RAW=ROOT/"data/raw"/NS
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 with p.open("xb") as f:f.write((json.dumps(x,sort_keys=True,indent=2)+"\n").encode())
def request(url,cap):
 host=urllib.parse.urlsplit(url).hostname;assert host in ("api.github.com","raw.githubusercontent.com") and url.startswith("https://")
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"RNA-localization free computational research parameter metadata"}),timeout=40) as response:
  assert response.status==200 and urllib.parse.urlsplit(response.geturl()).hostname==host
  body=response.read(cap+1);assert len(body)<=cap
  receipt={"url":url,"response_url":response.geturl(),"http_status":response.status,"headers":dict(response.headers.items()),
     "bytes":len(body),"sha256":hashlib.sha256(body).hexdigest()}
 return body,receipt
def run():
 p=OUT/"request_manifest.json";plan=json.loads(p.read_bytes())
 assert subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT)==p.read_bytes()
 frozen=OUT/"source_manifest_v2.json";pins=json.loads(frozen.read_bytes())
 assert subprocess.check_output(["git","show","HEAD:"+frozen.relative_to(ROOT).as_posix()],cwd=ROOT)==frozen.read_bytes()
 for name,digest in pins["files"].items():assert sha(ROOT/name)==digest,name
 assert not (OUT/"acquisition_receipt_v2.json").exists()
 try:
  body=(RAW/"official_branch_ref.json").read_bytes()
  reference=json.loads((OUT/"official_branch_ref_receipt.json").read_bytes())
  assert hashlib.sha256(body).hexdigest()==reference["sha256"] and reference["http_status"]==200
  obj=json.loads(body)
  assert obj["ref"]=="refs/heads/master" and obj["object"]["type"]=="commit"
  commit=obj["object"]["sha"];assert re.fullmatch("[0-9a-f]{40}",commit)
  
  def one(filename):
   url="https://raw.githubusercontent.com/pufmodel/Pumilio_occupancy_predictions/"+commit+"/"+filename
   payload,receipt=request(url,64*1024)
   with (RAW/filename).open("xb") as f:f.write(payload)
   save(OUT/(filename+"_HTTP_receipt_v2.json"),receipt)
   text=payload.decode("utf-8-sig");rows=list(csv.reader(io.StringIO(text)))
   assert 1<len(rows)<=50 and all(len(row)<=6 for row in rows)
   return {"filename":filename,"receipt":receipt,"CSV_header":rows[0],"CSV_body_rows":len(rows)-1}
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(one,plan["parameter_filenames"]))
  save(OUT/"acquisition_receipt_v2.json",{"status":"PASS_FOUR_FIXED_PUBLIC_PARAMETER_BYTES_AT_RESOLVED_COMMIT","resolved_author_commit":commit,
   "branch_ref":reference,"records":records,"request_manifest_sha256":sha(p),"source_manifest_sha256":sha(frozen),
   "reused_already_certified_ref_no_repeat_ref_request":True,"preserved_original_encoding_failure":True,"author_code_downloaded_or_executed":False,"fixed_energies_represent_operational_author_model_including_censor_bounds":True,
   "CSV_parameter_schema_or_published_math_parity_certified":False,"features_built":0,"models_fit":0,"cost":0})
  print("PASS author commit",commit,"four public parameter CSVs",[(r["filename"],r["receipt"]["bytes"],r["CSV_body_rows"]) for r in records],flush=True)
 except Exception as error:
  save(OUT/"acquisition_failure_v2.json",{"status":"FAILED_FIXED_PARAMETER_METADATA_ACQUISITION","exception_type":type(error).__name__,
    "error":str(error),"source_manifest_sha256":sha(frozen),"preserve_partial_downloads":True,"automatic_retry":False,"models_fit":0})
  raise
if __name__=="__main__":run()
