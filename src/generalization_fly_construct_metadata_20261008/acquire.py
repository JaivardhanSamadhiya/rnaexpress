
"""Fixed public construct-metadata acquisition; no numerical localization workbook."""
from pathlib import Path
import hashlib,json,subprocess,time,urllib.request,urllib.parse,urllib.error,sys
ROOT=Path(__file__).resolve().parents[2]
NS="generalization_fly_construct_metadata_20261008"
OUT=ROOT/"results"/NS;RAW=ROOT/"data/raw"/NS;REP=ROOT/"reports"/NS
MANIFEST=OUT/"metadata_manifest.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding="utf8"))
def save(p,v):
    with Path(p).open("xb") as f:f.write(v)
def run(root_start=False):
    assert root_start
    assert subprocess.check_output(["git","show","HEAD:"+MANIFEST.relative_to(ROOT).as_posix()],cwd=ROOT)==MANIFEST.read_bytes()
    frozen=read(MANIFEST)
    assert frozen["status"]=="FROZEN_PUBLIC_FLY_CONSTRUCT_METADATA_ONLY"
    for name,digest in frozen["files"].items():assert sha(ROOT/name)==digest,name
    assert not (OUT/"metadata_acquisition_receipt.json").exists()
    RAW.mkdir(parents=True,exist_ok=True);records=[];total=0
    for row in frozen["requests"]:
        path=RAW/row["filename"];assert not path.exists() and not path.with_name(path.name+".receipt.json").exists()
        status=0;payload=b"";failure=None;url=None;ctype=None;headers={}
        try:
            request=urllib.request.Request(row["url"],headers={"User-Agent":"RNA-localization-construct-metadata-research/1.0 (public files only)"})
            with urllib.request.urlopen(request,timeout=30) as response:
                status=response.status;url=response.geturl();ctype=response.headers.get("Content-Type","")
                parsed=urllib.parse.urlsplit(url)
                assert parsed.scheme=="https" and parsed.hostname in frozen["allowed_hosts"],"Redirect outside fixed public metadata hosts"
                assert parsed.path==urllib.parse.urlsplit(row["url"]).path,"Changed metadata resource path"
                payload=response.read(row["max_bytes"]+1)
                assert len(payload)<=row["max_bytes"],"Per-file cap exceeded"
                headers={k:response.headers.get(k) for k in ("Content-Type","Content-Length","ETag","Last-Modified")}
                assert status==200
                if row["kind"]=="pdf":assert payload.startswith(b"%PDF-"),"Not a PDF"
                else:assert payload.startswith(b"LOCUS") and b"\nVERSION" in payload and payload.rstrip().endswith(b"//"),"Not a complete GenBank reference record"
        except urllib.error.HTTPError as error:
            status=error.code;url=error.geturl();ctype=error.headers.get("Content-Type","")
            payload=error.read(min(row["max_bytes"],4096));failure="HTTPError "+str(error.code)
        except Exception as error:
            failure=type(error).__name__+": "+str(error)
            if len(payload)>row["max_bytes"]:payload=payload[:row["max_bytes"]]
        total+=len(payload);assert total<=frozen["total_max_bytes"]
        if payload:save(path,payload)
        record={"requested_url":row["url"],"response_url":url,"http_status":status,"content_type":ctype,
            "bytes":len(payload),"sha256":sha(path) if payload else None,"failure":failure,"source_headers":headers,
            "filename":row["filename"],"kind":row["kind"],"request_retried":False,
            "admission":"PUBLIC_CONSTRUCT_METADATA_BYTES" if failure is None else "UNAVAILABLE_METADATA_REQUEST"}
        receipt=path.with_name(path.name+".receipt.json");save(receipt,(json.dumps(record,sort_keys=True,indent=2)+"\n").encode())
        save(receipt.with_name(receipt.name+".sha256"),(sha(receipt)+"\n").encode())
        records.append({**record,"receipt_path":receipt.relative_to(ROOT).as_posix(),"receipt_sha256":sha(receipt)})
        print(row["filename"],record["admission"],status,len(payload),flush=True)
        time.sleep(.7)
    for name,digest in frozen["files"].items():assert sha(ROOT/name)==digest,name
    save(OUT/"metadata_acquisition_receipt.json",(json.dumps({"status":"COMPLETED_FIXED_CONSTRUCT_METADATA_REQUESTS",
        "metadata_manifest_sha256":sha(MANIFEST),"records":records,"acquired_bytes":total,"requests":len(records),
        "numeric_source_workbooks_downloaded":False,"localization_models_fit":0,"protected_project_sources_read":False,
        "no_credentials_or_fee":True,"publication_qualitative_results_already_exposed":True},sort_keys=True,indent=2)+"\n").encode())
if __name__=="__main__":run("--root-start" in sys.argv[1:])
