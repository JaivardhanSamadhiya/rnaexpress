"""Exactly reproduce the post-gate diagnostic; write nothing, fit nothing.

Run with bundled Python -S -B -m <this module>. Only fixed source/static and
already exposed saved report paths are opened. This is not original-input
admission, an independent biological replication or a native fitting profile.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = 'results/generalization_menu_comparison_core_20261026/source_manifest.json'
MANIFEST_SHA = 'be83d0a8aaddda6959475a6c86241b99624aa300fe71940e10d5b60ed4c02fd9'
REPORT = 'results/generalization_current_study_verification_20261026/evaluate/worker_report.json'
REPORT_SHA = 'be53e8c02be6ae444ec67bd231532571bd97d00a4c92b4f52bc8ec15969f462a'
OUT = 'results/generalization_menu_feasibility_20261026/saved_decision_diagnostic.json'


def read_exact(name, want):
    path = (ROOT/name).resolve()
    if not path.is_relative_to(ROOT) or name.startswith(('artifacts/','data/')):
        raise ValueError('unapproved replay path')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != want:raise ValueError('hash mismatch: '+name)
    return raw


def main():
    manifest = json.loads(read_exact(MANIFEST,MANIFEST_SHA))
    for name,want in manifest['files'].items():read_exact(name,want)
    from .analyze import analyze
    saved = json.loads(read_exact(OUT,manifest['files'][OUT]))
    result = json.loads(read_exact(REPORT,REPORT_SHA))['result']
    got = analyze(result)
    for key,value in got.items():
        if saved[key] != value:raise ValueError('diagnostic replay differs: '+key)
    for arm,value in got['arms'].items():
        if abs(value['macro_regret_recomputed']-result['primary_summaries'][arm]['macro_regret'])>1e-12:
            raise ValueError('original primary summary differs')
    print(json.dumps({'status':'PASS_EXACT_SAVED_MENU_DIAGNOSTIC_REPRODUCTION',
                      'source_or_static_pins_verified':len(manifest['files']),
                      'diagnostic_fields_reproduced':len(got),'saved_report_sha256':REPORT_SHA,
                      'menus_per_arm':got['menus_per_arm'],'project_fit_calls':0,
                      'original_feature_or_label_inputs_reopened':False}))


if __name__=='__main__':main()
