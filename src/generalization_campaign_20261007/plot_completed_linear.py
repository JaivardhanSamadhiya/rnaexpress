"""Show every track in the three completed linear comparisons; never fit."""
from src.research_20260921 import common as runtime_bootstrap
from pathlib import Path
import hashlib, io, json, os, sys, tempfile, subprocess
import numpy as np
import pandas as pd

ROOT = Path('D:/rnaexpress')
OUT = ROOT / 'artifacts/generalization_campaign_20261007'
os.environ['MPLCONFIGDIR'] = str(Path(tempfile.gettempdir()) / 'rnaexpress_campaign_mpl')
sys.path.append(str(ROOT / 'data/interim/research_20260921/plot_runtime'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

TRACKS = ['simple', 'base', 'raw', 'structure', 'lookup', 'bert', 'combined']
NAMES = ['Simple control*', 'Base sequence', 'Raw context', 'Structure', 'Token lookup', '3UTRBERT', 'Combined']

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, payload):
    path = Path(path)
    assert path.resolve().is_relative_to(OUT.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != payload:
        assert '--replace-unfrozen-render' in sys.argv
        assert path.name in {'completed_linear_comparisons_v1.png', 'completed_linear_comparisons_v1.svg',
                             'completed_linear_comparisons_v1.csv', 'completed_linear_plot_manifest_v1.json'}
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', path.relative_to(ROOT).as_posix()],
                                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert tracked.returncode == 1, 'Never replace tracked rendering'
        path.write_bytes(payload)
    elif not path.exists(): path.write_bytes(payload)

def main():
    from src.generalization_20261007.verify import preservation
    unchanged, _ = preservation()
    assert unchanged == 33
    specifications = [
        ('generalization_next_20261007', 'Whole-assay transfer',
         ['Astrocyte', 'Mikl', 'Moffatt', 'SRLE', 'Macro'], 'per_assay', 'dataset'),
        ('generalization_crosscell_20261007', 'Unseen genes and crossed cell',
         ['CAD → N2A', 'N2A → CAD', 'Macro'], 'per_crossed_cell', 'task'),
        ('generalization_knowncell_20261007', 'Unseen genes, represented cell',
         ['CAD', 'N2A', 'Macro'], 'per_known_cell', 'task'),
    ]
    expected_units = [
        ['astrocyte_gse330741', 'mikl_gse173098', 'moffatt_gse334718', 'srle'],
        ['CAD_to_N2A', 'N2A_to_CAD'], ['CAD_known', 'N2A_known'],
    ]
    refs, panels, rows = {}, [], []
    for index, (ns, title, columns, field, unit_field) in enumerate(specifications):
        result_root = ROOT / 'results' / ns
        gate_path = result_root / 'gate_verdict.json'
        gate = json.loads(gate_path.read_text())
        assert gate['status'] == 'NO-GO' and not any(t['passes'] for t in gate['tracks'])
        verify_path = result_root / 'verification_receipt.json'
        assert json.loads(verify_path.read_text())['status'] == 'PASS'
        for path in (gate_path, verify_path): refs[path.relative_to(ROOT).as_posix()] = sha(path)
        tracks = {t['track']: t for t in gate['tracks']}
        data = []
        for track in TRACKS:
            if index == 0 and track == 'simple':
                values = {r['dataset']: r['regret'] + r['gain_vs_simple'] for r in tracks['base']['per_assay']}
                origin = 'Frozen best historical simple per assay'
            else:
                values = {r[unit_field]: r['regret'] for r in tracks[track][field]}
                origin = 'Declared fitted track' if index != 2 else 'Same frozen crosscell predictor; zero new fits'
            assert set(values) == set(expected_units[index])
            numbers = [float(values[unit]) for unit in expected_units[index]]
            macro = float(np.mean(numbers))
            if track in tracks: assert abs(macro - tracks[track]['macro_regret']) < 1e-12
            data.append(numbers + [macro])
            for unit, value in zip(expected_units[index] + ['macro'], numbers + [macro]):
                rows.append({'stream': ns, 'track': track, 'unit': unit, 'normalized_regret': value,
                             'origin': origin, 'stream_gate': gate['status']})
        panels.append((title, columns, np.asarray(data)))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'svg.hashsalt': 'rnaexpress_completed_linear_20261007'})
    fig, axes = plt.subplots(1, 3, figsize=(16, 7.5), gridspec_kw={'width_ratios': [5, 3, 3]})
    norm = TwoSlopeNorm(vmin=.35, vcenter=.5, vmax=.60)
    for i, (ax, (title, columns, data)) in enumerate(zip(axes, panels)):
        shown = ax.imshow(data, norm=norm, cmap='RdYlBu_r', aspect='auto')
        ax.set_xticks(range(len(columns)), columns, rotation=25, ha='right')
        ax.set_yticks(range(len(TRACKS)), NAMES if i == 0 else [])
        ax.set_title(title + '\nNO-GO', fontweight='bold', pad=15)
        for r in range(len(TRACKS)):
            for c in range(len(columns)):
                label = f'{data[r,c]:.4f}' if c == len(columns)-1 else f'{data[r,c]:.3f}'
                ax.text(c, r, label, ha='center', va='center', color='#17202a',
                        fontweight='bold' if c == len(columns)-1 else 'normal')
        ax.set_xticks(np.arange(-.5, len(columns), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(TRACKS), 1), minor=True)
        ax.grid(which='minor', color='white', linewidth=1.5)
        ax.tick_params(which='minor', bottom=False, left=False)
        for spine in ax.spines.values(): spine.set_visible(False)
    fig.suptitle('Aggregate improvement has not produced reliable generalization', fontsize=18, fontweight='bold', y=.98)
    fig.subplots_adjust(left=.12, right=.94, top=.80, bottom=.30, wspace=.18)
    cax = fig.add_axes([.35, .17, .38, .022])
    fig.colorbar(shown, cax=cax, orientation='horizontal', label='Normalized regret — lower is better; uniform expected value = 0.500')
    fig.text(.12, .015, '*Whole-assay: frozen best simple per assay. Cell comparisons: matched additive 1–3-mer control.\n'
             'Repeated development data; all tracks shown. Macro thresholds are only part of each full gate. Other streams remain pending.',
             fontsize=9, color='#39434a')
    for suffix in ('png', 'svg'):
        buffer = io.BytesIO()
        metadata = {'Software': 'RNAexpress additive campaign report'} if suffix == 'png' else {'Date': None}
        fig.savefig(buffer, format=suffix, dpi=220, metadata=metadata, facecolor='white')
        save(OUT / ('completed_linear_comparisons_v1.' + suffix), buffer.getvalue())
    plt.close(fig)
    save(OUT / 'completed_linear_comparisons_v1.csv', pd.DataFrame(rows).to_csv(index=False, lineterminator='\n').encode())
    files = [OUT / ('completed_linear_comparisons_v1.' + ext) for ext in ('png', 'svg', 'csv')]
    manifest = {'status': 'NUMERICAL_OUTPUTS_VERIFIED_VISUAL_REVIEW_PENDING', 'new_fits': 0,
                'source_sha256': sha(__file__), 'observed_result_hashes': refs,
                'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in files},
                'all_tracks_shown': True, 'independent_confirmation': False,
                'unchanged_user_files': unchanged}
    save(OUT / 'completed_linear_plot_manifest_v1.json', (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode())
    print('Three completed linear comparisons plotted; all seven tracks retained', flush=True)

if __name__ == '__main__': main()
