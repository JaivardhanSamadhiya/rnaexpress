"""One exponential draw per biological component, shared across all assays."""
from .common import np, SEED

def shared_bootstrap(gains_by_study, draws=5000, seed=SEED):
    components=sorted({component for values in gains_by_study.values() for component in values.index})
    indexes={component:index for index,component in enumerate(components)}
    weights=np.random.default_rng(seed).exponential(1,size=(draws,len(components)))
    bootstrap=np.zeros(draws)
    for _,values in sorted(gains_by_study.items()):
        assert len(values) and values.index.is_unique and np.isfinite(values.to_numpy()).all()
        selected=weights[:,[indexes[component] for component in values.index]]
        selected=selected/selected.sum(1,keepdims=True)
        bootstrap+=selected@values.to_numpy()/len(gains_by_study)
    return bootstrap
