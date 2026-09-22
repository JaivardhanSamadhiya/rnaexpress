"""Verify the isolated research record and preserve its environment/provenance."""
from .common import ROOT, sha256, write_json, write_new
from .pilots import verify
from datetime import datetime, timezone
import json
import platform
import sys
import numpy as np
import pandas as pd
import scipy
import sklearn
import openpyxl

OUT = ROOT / 'results/research_20260921'


def run():
    verify()
    snapshot = json.loads((OUT/'tracked_source_snapshot.json').read_text())
    changed = [p for p,h in snapshot['files'].items() if sha256(ROOT/p) != h]
    if changed:
        raise ValueError('Historical source snapshot changed: '+str(changed))
    for name in ('robustness_freeze','raw_counts_freeze','raw_swap_freeze'):
        frozen = json.loads((OUT/(name+'.json')).read_text())
        for p,h in frozen['files'].items():
            if sha256(ROOT/p) != h:
                raise ValueError('Analysis freeze differs: '+p)
    qc = json.loads((OUT/'raw_counts_qc.json').read_text())
    counts = pd.read_csv(OUT/'raw_sixmer_counts.csv')
    if len(counts) != 4096 or counts.kmer.duplicated().any():
        raise ValueError('Invalid count table')
    for record in qc.values():
        if counts[record['sample']].sum() != record['accepted']:
            raise ValueError('Count sum mismatch')
        if record['accepted'] + record['no_valid_insert'] + record.get('discordant',0) != record['pairs']:
            raise ValueError('Read accounting mismatch')
    paths = sorted(p for p in OUT.iterdir() if p.suffix in ('.csv','.json','.png','.svg') and p.name != 'checkpoint_receipt.json')
    data_receipts = list((ROOT/'data/external/research_20260921').rglob('*.receipt.json'))
    receipt = {'created_utc':datetime.now(timezone.utc).isoformat(),
        'python':sys.version,'python_executable':sys.executable,'platform':platform.platform(),
        'versions':{m.__name__:m.__version__ for m in (np,pd,scipy,sklearn,openpyxl)},
        'historical_source_files_verified_unchanged':len(snapshot['files']),
        'pilot_and_followup_freezes_verified':True,
        'raw_pairs':sum(r['pairs'] for r in qc.values()),
        'accepted_fragments':sum(r['accepted'] for r in qc.values()),
        'artifact_hashes':{p.relative_to(ROOT).as_posix():sha256(p) for p in paths},
        'download_receipts':{p.relative_to(ROOT).as_posix():json.loads(p.read_text()) for p in data_receipts},
        'no_spending':True,'scheduled_tasks_created':0}
    write_json(OUT/'checkpoint_receipt.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('artifact_hashes','download_receipts')},indent=2))


if __name__ == '__main__':
    run()
