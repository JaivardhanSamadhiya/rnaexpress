"""Read exactly one closed exposed report, with fixed hash and size bound."""
import hashlib
import json
from pathlib import Path
from .analyze import analyze

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'results/generalization_current_study_verification_20261026/evaluate/worker_report.json'
SHA = 'be53e8c02be6ae444ec67bd231532571bd97d00a4c92b4f52bc8ec15969f462a'


def run():
    assert not SOURCE.is_symlink() and SOURCE.stat().st_size == 39549826
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA
    result = json.loads(raw)['result']
    rows = result['primary_decisions']
    values = {arm:analyze(decisions) for arm,decisions in rows.items()}
    invariant_keys = ('paired_contexts','paired_binary_contexts','discordant_binary_contexts',
                      'weighted_discordant_binary_fraction','binary_primary_weight')
    for key in invariant_keys:assert len({v[key] for v in values.values()}) == 1,key
    output = ROOT/'results/generalization_binary_cell_diagnostic_20261030'
    output.mkdir(parents=True,exist_ok=True)
    payload = dict(saved_report_sha256=SHA,primary_verdict_unchanged=result['status'],arms=values,
                   original_arrays_or_label_archives_read=False,model_fits_or_refits=0)
    with (output/'diagnostic.json').open('x',encoding='utf8',newline='\n') as stream:
        stream.write(json.dumps(payload,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps(payload,sort_keys=True))


if __name__ == '__main__':run()
