"""Shared-gene gate plus required family-correlated draws, equal-gene estimand."""
from .experiment_common import *
from src.generalization_crosscell_20261007.bootstrap import shared_bootstrap

def family_bootstrap(gains_by_task,draws=5000,seed=SEED,family_map=None):
    if family_map is None:
        groups=pd.read_csv(ART/'similarity_components.csv')
        family_map=groups.set_index('biological_component').similarity_component.to_dict()
    components=sorted({component for values in gains_by_task.values() for component in values.index})
    assert all(component in family_map for component in components)
    families=sorted({family_map[component] for component in components});positions={family:i for i,family in enumerate(families)}
    weights=np.random.default_rng(seed).exponential(1,size=(draws,len(families)))
    result=np.zeros(draws)
    for _,values in sorted(gains_by_task.items()):
        assert values.index.is_unique and len(values) and np.isfinite(values.to_numpy()).all()
        chosen=weights[:,[positions[family_map[component]] for component in values.index]]
        # Each original gene still contributes one observation/weight to its cell.
        result+=(chosen/ chosen.sum(1,keepdims=True))@values.to_numpy()/len(gains_by_task)
    return result
