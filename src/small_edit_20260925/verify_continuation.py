"""Verify additive provenance artifacts and prior evidence, without scoring."""
from .common import ROOT, OUT, REPORT, sha256, readj, jsave
import ast
from datetime import datetime, timezone
import hashlib


def run():
    from .provenance_continuation import DEST, API
    downloaded=[]
    for receipt_path in sorted(DEST.glob('*.receipt.json')):
        receipt=readj(receipt_path)
        path=DEST/receipt_path.name.removesuffix('.receipt.json')
        payload=path.read_bytes()
        assert sha256(path)==receipt['sha256']
        assert len(payload)==receipt['bytes'] and receipt['public_free'] is True
        assert receipt['url'].startswith(API)
        if receipt['git_blob']:
            assert hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()==receipt['git_blob']
        downloaded.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(path),
            'git_blob':receipt['git_blob'],'url':receipt['url'],'bytes':len(payload)})
    assert len(downloaded)==4 and sum(bool(r['git_blob']) for r in downloaded)==3
    prior=readj(ROOT/'artifacts/small_edit_20260925/delivery_receipt.json')
    for name,meta in prior['manifest'].items():
        assert sha256(ROOT/name)==meta['sha256'], name
    assert sha256(ROOT/prior['archive'])==prior['sha256']
    freeze=readj(OUT/'prediction_freeze.json')
    for name,expected in freeze['files'].items():
        assert sha256(ROOT/name)==expected, name
    from src.research_20260921.srle_clean_verification_20260925 import preservation
    preserved=preservation()
    intake=readj(OUT/'independent_source_intake_template.json')
    assert intake['status']=='UNFILLED_NOT_ADMITTED'
    assert intake['outcome_access_authorized'] is False and intake['evaluation_authorized'] is False
    assert intake['target_specific_protocol_commit'] is None
    sources=[ROOT/'src/small_edit_20260925'/name for name in ('provenance_continuation.py','verify_continuation.py')]
    for path in sources: ast.parse(path.read_text(encoding='utf-8'))
    files=sources+[REPORT/name for name in ('provenance_continuation_scope.md','provenance_continuation_findings.md','independent_confirmation_admission.md')]
    files+=[OUT/'independent_source_intake_template.json']
    result={'status':'PASS','created_utc':datetime.now(timezone.utc).isoformat(),
        'downloaded':downloaded,'new_artifacts':{p.relative_to(ROOT).as_posix():sha256(p) for p in files},
        'prior_bundle_member_files_unchanged':len(prior['manifest']),'prior_bundle_sha256_unchanged':prior['sha256'],
        'prediction_freeze_unchanged':True,'preservation':preserved,'provenance_status':'PARTIAL',
        'models_fit':0,'outcomes_loaded':0,'downloaded_code_executed':False,
        'new_dataset_discovery':False,'new_source_admitted':False,
        'checks':'Source hashes/Git blob IDs, JSON validity, local script syntax, archive preservation; no new model test claim'}
    jsave('continuation_verification.json',result)
    print({k:v for k,v in result.items() if k not in ('new_artifacts','downloaded','preservation')})


if __name__=='__main__': run()
