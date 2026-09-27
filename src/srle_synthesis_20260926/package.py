from .common import *
import zipfile,io,subprocess

def run():
    receipt=readj(OUT/'verification_receipt.json')
    for path,h in receipt['synthesis_hashes'].items():assert sha256(ROOT/path)==h,path
    files=[ROOT/p for p in receipt['synthesis_hashes']]+[OUT/'verification_receipt.json']
    # Also pin directory attributes/ignore rules, not raw data or unrelated files.
    files+=list(Path(__file__).parent.glob('.gitattributes'))+list(ART.glob('.gitignore'))
    files=sorted(set(files));manifest={p.relative_to(ROOT).as_posix():{'sha256':sha256(p),'bytes':p.stat().st_size} for p in files}
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name in sorted(manifest):
            info=zipfile.ZipInfo(name,(2026,9,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,(ROOT/name).read_bytes())
        info=zipfile.ZipInfo('MANIFEST.json',(2026,9,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,json.dumps(manifest,indent=2,sort_keys=True))
    path=ART/'srle_synthesis_evidence_20260926.zip';save(path,buffer.getvalue())
    with zipfile.ZipFile(path) as archive:
        import hashlib
        assert archive.testzip() is None
        for name,meta in manifest.items():assert hashlib.sha256(archive.read(name)).hexdigest()==meta['sha256']
    jsave(ART/'delivery_receipt.json',{'status':'PASS','archive':path.relative_to(ROOT).as_posix(),'sha256':sha256(path),'bytes':path.stat().st_size,'files':len(manifest),'manifest':manifest,'analysis_freeze_commit':'f875a02','original_result_commit':'e5b9288','self_contained_runtime':False,'requires':'Preserved repository/original input bundle and bundled Python dependencies for full reproduction; prototype runtime is bundled','no_raw_or_protected_outcomes_in_archive':True})
    print({'status':'PASS','files':len(manifest),'bytes':path.stat().st_size,'sha256':sha256(path)})

if __name__=='__main__':run()
