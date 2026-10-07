"""Pin actual cached thermodynamic wrappers/binary and pool/projection inputs."""
from pathlib import Path
from .common import ROOT, OUT, RBP_ART, RBP_OUT, jsave, readj, sha256, np
from .feasibility import RNA

def paths():
    package = Path(RNA.__file__).parent
    files = [package / '__init__.py', package / 'RNA.py', Path(np.__file__),
             ROOT / 'src/generalization_next_20261007/route_structure.py',
             ROOT / 'src/generalization_rbp_20261007/scoring.py',
             ROOT / 'src/generalization_rbp_20261007/catalog.py',
             ROOT / 'src/generalization_rbp_20261007/projection.py',
             RBP_ART / 'direct_human_manifest.json', RBP_OUT / 'projection_receipt.json']
    files += list(package.glob('_RNA*.pyd'))
    files += [RBP_ART / ('projection_' + pool + '.npy') for pool in ('global_mean', 'global_max', 'affected_mean', 'affected_max')]
    assert len(list(package.glob('_RNA*.pyd'))) == 1 and all(path.exists() for path in files)
    return files

def prepare():
    assert RNA.__version__ == '2.7.2' and np.__version__ == '1.26.4'
    from src.generalization_rbp_20261007.projection import load_projections
    from src.generalization_rbp_20261007.scoring import load_groups
    matrices = load_projections(); groups = load_groups()
    widths = [window for window, _, _ in groups]
    assert min(widths) == 4 and max(widths) == 25 and sum(len(indices) for _, indices, _ in groups) == 421
    jsave(OUT / 'runtime_binding_receipt.json', {'status': 'PASS', 'ViennaRNA': RNA.__version__, 'numpy': np.__version__,
        'PFMs': 421, 'motif_width_range': [min(widths), max(widths)],
        'projection_shapes': [list(matrix.shape) for matrix in matrices],
        'files': {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths()},
        'labels_read': False, 'project_alleles_folded': False, 'models_fit': 0})

def check():
    receipt = readj(OUT / 'runtime_binding_receipt.json')
    assert receipt['status'] == 'PASS' and receipt['ViennaRNA'] == RNA.__version__ == '2.7.2' and receipt['numpy'] == np.__version__ == '1.26.4'
    for name, expected in receipt['files'].items():
        assert sha256(ROOT / name) == expected, name
    return receipt

if __name__ == '__main__':
    prepare()
