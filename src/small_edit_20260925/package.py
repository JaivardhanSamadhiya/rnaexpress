"""Build and verify an immutable local evidence bundle, excluding old raw data."""
from .common import *
import hashlib
import re
import zipfile


def run():
    required=['small_edit_dataset_inventory.md','small_edit_prediction_protocol.md','small_edit_prediction_results.md','small_edit_final_claim.md','reproduction.md']
    for name in required:
        assert (REPORT/name).is_file(), name
    for path in REPORT.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if not target.startswith(('http:','https:','#')):
                assert (path.parent/target.split('#')[0]).is_file(), (path,target)
    verify=readj(OUT/'verification_receipt.json')
    assert verify['status']=='PASS' and verify['tests']==76
    files=[]
    for folder in (ROOT/'src/small_edit_20260925',REPORT,OUT):
        files.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files=sorted(files)
    manifest={p.relative_to(ROOT).as_posix():{'sha256':sha256(p),'bytes':p.stat().st_size} for p in files}
    directory=ROOT/'artifacts/small_edit_20260925'; directory.mkdir(exist_ok=True)
    archive=directory/'small_edit_evidence_20260925.zip'
    assert not archive.exists(), 'Preserve previous archive'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
        for p in files:
            info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(2026,9,25,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(info,p.read_bytes())
        info=zipfile.ZipInfo('BUNDLE_MANIFEST.json',date_time=(2026,9,25,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        bundle.writestr(info,(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist())==len(set(bundle.namelist()))==len(manifest)+1
        for name,item in manifest.items():
            payload=bundle.read(name)
            assert hashlib.sha256(payload).hexdigest()==item['sha256']
            assert len(payload)==item['bytes']
    receipt={'status':'PASS','archive':archive.relative_to(ROOT).as_posix(),'sha256':sha256(archive),
        'bytes':archive.stat().st_size,'files':len(manifest),'manifest':manifest,
        'scope':'New analysis evidence and source only; no old raw data or protected outcomes',
        'report_links_verified':True,'archive_crc_and_all_member_sha256_verified':True,
        'pre_fit_commit':'6e793d7','verification':{'tests':verify['tests'],'prediction_replay_max_error':verify['prediction_replay_max_error']}}
    path=directory/'delivery_receipt.json';assert not path.exists()
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (directory/'.gitattributes').write_text('* -text\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='manifest'},indent=2))


if __name__=='__main__': run()
