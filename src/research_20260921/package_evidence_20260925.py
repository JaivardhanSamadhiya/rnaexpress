"""Assemble immutable evidence, scripts, source receipts and existing figures.

Does not include raw reads, protected outcomes, model weights or unrelated files.
"""
from .evidence_io_20260925 import ROOT, ART, sha256, read_json, save, save_json
from pathlib import Path
import hashlib
import io
import json
import zipfile


def run():
    if read_json(ART/'srle_lineage_result.json')['determination'] != 'PARTIAL':
        raise ValueError('Unexpected provenance conclusion')
    verification = read_json(ART/'clean_verification.json')
    if verification['status'] != 'PASS' or verification['tests'] != 69:
        raise ValueError('Verification not complete')
    claims = read_json(ART/'claim_evidence_ledger_final.json')
    for row in claims:
        if sha256(ROOT/row['artifact_path']) != row['artifact_sha256']:
            raise ValueError('Claim source changed: '+row['artifact_path'])
    names = [
        'lineage_config.json', 'srle_lineage_result.json', 'srle_samples.csv', 'srle_measurement_lineage.csv',
        'clean_verification.json', 'scoped_tests.txt', 'srle_prediction_class_metrics.csv',
        'claim_evidence_ledger.csv', 'claim_evidence_ledger.json', 'catalogue_receipt.json',
        'claim_evidence_ledger_final.csv', 'claim_evidence_ledger_final.json', 'claim_evidence_ledger_final.md',
        'final_ledger_receipt.json', 'srle_comparator_table.csv',
        'validation_resource_inventory.csv', 'independent_validation_decision.json',
    ]
    paths = [ART/n for n in names] + [ROOT/'CURRENT_STATE.md']
    paths += [ROOT/'reports/research_20260921'/n for n in (
        'provenance_work_scope_20260925.md','srle_provenance_final.md',
        'srle_provenance_questions_20260925.md','research_synthesis_20260925.md')]
    paths += [Path(__file__).with_name(n) for n in (
        'evidence_io_20260925.py','srle_public_history_20260925.py','srle_measurement_lineage_20260925.py',
        'test_measurement_lineage_20260925.py','srle_clean_verification_20260925.py',
        'evidence_catalogue_20260925.py','evidence_ledger_final_20260925.py','package_evidence_20260925.py')]
    paths += [ROOT/'results/research_20260921'/n for n in (
        'srle_uniform_risk_20260924.png','srle_uniform_risk_20260924.svg',
        'srle_aggregate_replay_20260924.zip','srle_risk_replay_20260924.zip')]
    # Only the explicitly scoped source-only acquisition folder; no broad data glob.
    paths += sorted((ROOT/'data/external/research_20260921/srle_provenance_20260925').iterdir())
    paths += sorted({ROOT/r['artifact_path'] for r in claims})
    paths = sorted(set(paths))
    members = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in paths}
    readme = '''# RNA-localization evidence delivery, 25 September 2026

Start with reports/research_20260921/research_synthesis_20260925.md.
The result is bounded Outcome B, with PARTIAL SRLE source provenance.
No novel mechanism, independent confirmation or competition outcome is claimed.
This package is an AI-authored audit; it is not student submission prose.

Tables are under artifacts/research_20260925. Use claim_evidence_ledger_final.*;
the initial catalogue is preserved for audit. The finalizer corrects one SEERS
citation and adds historical controls plus exact-uniform comparisons.
CSV paths are relative to the project root. Markdown uses local D:/rnaexpress
links for the originating workspace; use matching archive paths elsewhere.

Portable replay (Python standard library only): extract either nested
results/research_20260921/srle_*replay_20260924.zip into a fresh directory, then
run `python -I -S -B replay.py` there. These independently implement aggregate
arithmetic only; they do not re-fit models, recount reads or verify source biology.

Full provenance/prediction verification requires the original repository and
its pinned public source files, saved predictions, count matrix and raw-file
receipts; large raw reads and historical runtime dependencies are not bundled.
Use the bundled Codex Python and the isolated runtime documented in common.py.
No installation, payment or unfiltered pytest is needed in the current workspace.

From D:/rnaexpress, with PYTHONDONTWRITEBYTECODE=1, PYTHONIOENCODING=utf-8,
OPENBLAS_NUM_THREADS=2 and OMP_NUM_THREADS=2:
python -m src.research_20260921.srle_measurement_lineage_20260925
python -m src.research_20260921.srle_clean_verification_20260925
python -m src.research_20260921.evidence_catalogue_20260925
python -m src.research_20260921.evidence_ledger_final_20260925
python -m src.research_20260921.package_evidence_20260925

Use a fresh output workspace for a full rebuild; writers preserve differing
existing records. Keep the delivered lineage_config.json for replay: it pins
the existing inputs and code. Do not regenerate the freeze to bless changes.
The scoped test log contains elapsed time and can differ on another machine.
Downloading historical SRLE source is optional: cached files/receipts are bundled.
No downloaded author code is executed by any replay.

Protected outcomes, old gates and unrelated edits remain unchanged. Discovery
of new datasets was blocked by prior automatic review and was not retried.
The inventory is not a global absence finding. No new external protocol or
outcome evaluation was executed without a qualified independent dataset.
'''
    members['README_EVIDENCE.md'] = readme.encode()
    integrity = {n: hashlib.sha256(v).hexdigest() for n,v in members.items()}
    members['PACKAGE_INTEGRITY.json'] = (json.dumps(integrity, indent=2, sort_keys=True)+'\n').encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name, payload in sorted(members.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,9,25,0,0,0))
            info.external_attr=0o100644<<16
            archive.writestr(info,payload,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    saved=save('research_evidence_20260925.zip',buffer.getvalue())
    with zipfile.ZipFile(saved) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(members):
            raise ValueError('Package verification failed')
        for name, expected in integrity.items():
            if hashlib.sha256(archive.read(name)).hexdigest()!=expected:
                raise ValueError('Package member failed: '+name)
    receipt={'status':'PASS','zip_sha256':sha256(saved),'zip_bytes':saved.stat().st_size,
        'members':len(members),'member_hashes':integrity,'claims':len(claims),
        'source_raw_reads_included':False,'protected_outcomes_included':False,
        'scope':'Evidence package; full provenance replay needs pinned original repository inputs'}
    save_json('package_receipt.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='member_hashes'},indent=2))


if __name__=='__main__':
    run()
