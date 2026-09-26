from .core import *
import re
import zipfile


def run():
    reports=[REPORT/n for n in ('srle_small_edit_prediction_protocol.md','srle_small_edit_prediction_results.md','srle_final_predictive_claim.md','srle_prediction_reproduction.md')]
    artifacts=[ART/n for n in ('srle_observation_inventory.csv','srle_heldout_predictions.csv','srle_candidate_selection.csv',
        'heldout_candidate_predictions.csv','srle_small_edit_prediction_figure.png','srle_small_edit_prediction_figure.svg')]
    for report in reports:
        for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
            if not target.startswith(('https:','http:','#')):assert (report.parent/target).is_file(),target
    files=sorted(set([*reports,*artifacts,*OUT.glob('*'),*(ROOT/'src/srle_prediction_20260926').glob('*')]))
    files=[p for p in files if p.is_file()]
    manifest={p.relative_to(ROOT).as_posix():{'sha256':sha256(p),'bytes':p.stat().st_size} for p in files}
    path=ART/'srle_prediction_evidence_20260926.zip';assert not path.exists()
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
        for file in files:
            entry=zipfile.ZipInfo(file.relative_to(ROOT).as_posix(),date_time=(2026,9,26,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(entry,file.read_bytes())
        entry=zipfile.ZipInfo('BUNDLE_MANIFEST.json',date_time=(2026,9,26,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
        bundle.writestr(entry,(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
    with zipfile.ZipFile(path) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist())==len(set(bundle.namelist()))==len(manifest)+1
        for name,item in manifest.items():assert hashlib.sha256(bundle.read(name)).hexdigest()==item['sha256']
    jsave(ART/'srle_prediction_delivery_receipt.json',{'status':'PASS','archive':path.relative_to(ROOT).as_posix(),
        'bytes':path.stat().st_size,'sha256':sha256(path),'files':len(manifest),'manifest':manifest,
        'pre_fit_commit':'0023b01','freeze_sha256':sha256(OUT/'evaluation_freeze.json'),
        'archive_crc_all_member_hashes_and_report_links_verified':True})
    print({'files':len(manifest),'bytes':path.stat().st_size,'sha256':sha256(path)})


if __name__=='__main__':run()
