"""Fixed original C bytes and new committed prefit, without old model reuse."""
from types import SimpleNamespace
from . import common as c
from src.generalization_cdrive_forensic_execution_20261026 import inputs as original
from src.generalization_current_execution_context_20261025 import contracts as hc
from src.generalization_current_execution_context_20261025.inputs import validate_supplied


def load(np,*,fresh):
    pins=c.original_inputs()
    raws={name:c.read_exact(name,want,fresh=fresh) for name,want in pins.items()}
    s=original.saved
    matrix=original.matrix_from_bytes(np,raws[s.NPZ],fresh=fresh)
    supplied={'metadata':raws[s.METADATA_BUNDLE],'array':raws[s.ARRAY_CERTIFICATE],
        'labels':raws[s.LABEL_CERTIFICATE],'prefit':raws[original.spec.HISTORICAL_PREFIT],
        'projection':raws[original.spec.HISTORICAL_PROJECTION]}
    fresh();value=validate_supplied(np,matrix,supplied,hc.canonical(original.historical_reference()));fresh()
    return SimpleNamespace(metadata=value['metadata'],matrix=matrix,effects=value['effects'],historical_plan=value['plan'])


def new_plan(run,inp,*,fresh):
    from src.generalization_current_fixed_fit_core_20261026.plan import bind_current_plan
    name=run['current_prefit_relative_path'];raw=c.read_exact(name,run['current_prefit_sha256'],fresh=fresh)
    commit=run['current_prefit_commit']
    fresh()
    plan=bind_current_plan(name,raw,commit,inp.historical_plan,
        committed_reader=lambda path,revision:c.committed(path,revision))
    fresh();return plan
