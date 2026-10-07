"""Publish every fixed polarity result and a byte-verified local evidence bundle."""
from .common import *
import zipfile


def run():
    freeze_check()
    audit=readj(OUT/'verification_receipt.json');assert audit['status']=='PASS'
    verdict=readj(OUT/'gate_verdict.json')
    control,candidate=[next(r for r in verdict['tracks'] if r['track']==name) for name in TRACKS]
    increment=candidate['incremental_comparisons'][0]
    comparisons={name:pd.read_csv(OUT/name/'comparison.csv').set_index('dataset') for name in TRACKS}
    lines=['# Fixed endpoint polarity results', '', '**NO-GO under the unchanged generalization gate.**', '',
        'The known endpoint orientation lowered equal-assay macro normalized regret from '
        f"{control['macro_regret']:.6f} to {candidate['macro_regret']:.6f}. The incremental gain is "
        f"{increment['mean_gain']:.6f}, with a descriptive shared-component interval "
        f"[{increment['descriptive_gain_ci'][0]:.6f}, {increment['descriptive_gain_ci'][1]:.6f}]. "
        'Three assays improve; Moffatt worsens. Uniform expected regret is 0.5.', '',
        '| held assay | matched unflipped | fixed polarity | regret improvement | polarity avoidable wrong |',
        '| --- | ---: | ---: | ---: | ---: |']
    labels={'astrocyte_gse330741':'Astrocyte','mikl_gse173098':'Mikl','moffatt_gse334718':'Moffatt','srle':'SRLE'}
    for source in STUDIES:
        a,b=[float(comparisons[name].loc[source].regret) for name in TRACKS]
        lines.append(f"| {labels[source]} | {a:.6f} | {b:.6f} | {a-b:+.6f} | {float(comparisons['polarity'].loc[source].avoidable_wrong):.6f} |")
    failed=[key for key,value in candidate['checks'].items() if not value]
    lines += ['', 'Failed unchanged criteria: '+', '.join('`'+key+'`' for key in failed)+'.', '',
        'This supports endpoint alignment as a development hypothesis, without establishing reliable four-assay generalization. '
        'The orientation is fixed from known endpoint metadata; no sign or penalty was selected using an outer assay outcome. '
        'For held SRLE, projection-only training is identical across arms and the nuclear scores are exactly inverted. '
        'Endpoint class remains confounded with source; cytoplasmic export and distal transport are different biological quantities.', '',
        f"Independent verification passed for {audit['models']} checkpoints, including "
        f"{audit['inner_checkpoints_and_original_truth_regret_replayed']} inner validation replays, "
        f"{audit['candidate_scores_replayed']:,} candidate scores and {audit['selected_decisions_checked']:,} decisions. "
        f"Maximum score error was {audit['maximum_score_error']:.3g}. All 33 preexisting modified files and the older evidence bundles were preserved.", '',
        'A separately frozen factorial follow-up may test the fixed alignment with the already declared structure and encoder features. '
        'It must retain matched unflipped controls and the original strict gate; this result does not authorize changing a failed threshold. '
        'All comparisons use repeatedly exposed development data, and no independent biological confirmation or calibrated benefit probability is claimed.', '']
    save(REP/'results.md','\n'.join(lines).encode())
    archive=ART/'polarity_evidence.zip';receipt_path=ART/'delivery_receipt.json'
    assert not archive.exists() and not receipt_path.exists(), 'Preserve completed delivery'
    paths=sorted(p for folder in (SRC,REP,OUT,ART) for p in folder.rglob('*') if p.is_file()
                 and '__pycache__' not in p.parts and p.suffix not in ('.log','.zip')
                 and p not in (archive,receipt_path))
    manifest={p.relative_to(ROOT).as_posix():{'sha256':sha256(p),'bytes':p.stat().st_size} for p in paths}
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(manifest)
        for name,entry in manifest.items():
            assert hashlib.sha256(z.read(name)).hexdigest()==entry['sha256']
    jsave(receipt_path,{'status':'PASS','archive':archive.relative_to(ROOT).as_posix(),
        'sha256':sha256(archive),'bytes':archive.stat().st_size,'members':len(paths),
        'manifest':manifest,'all_member_hashes_verified':True,'zip_CRC_checked':True,
        'generalization_verdict':verdict['status'],'independent_confirmation':False})
    print('Polarity results and verified evidence bundle saved:',len(paths),'members',flush=True)


if __name__=='__main__':run()
