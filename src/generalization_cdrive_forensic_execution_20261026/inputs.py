"""Fixed C-only saved inputs; historical bytes never confer current authority."""
from dataclasses import dataclass
import io
import zipfile
from . import common as c, spec
from src.generalization_knowncell_fit_paged_execution_20261025 import spec as saved
from src.generalization_current_execution_context_20261025 import contracts as hc
from src.generalization_current_execution_context_20261025 import inputs as supplied
from src.generalization_current_execution_context_20261025 import spec as historical
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc


def declared_data_pins():
    # Only literals from source. This function does not open biological payloads.
    return {**saved.INPUT_PINS, saved.NPZ:saved.NPZ_SHA,
        spec.HISTORICAL_PREFIT:spec.HISTORICAL_PREFIT_SHA,
        spec.HISTORICAL_PROJECTION:spec.HISTORICAL_PROJECTION_SHA,
        spec.SAVED_AUDIT.relative_to(c.ROOT).as_posix():spec.SAVED_AUDIT_SHA}


def checkpoint_pins():
    # Hash metadata from the already published interruption audit, not models.
    raw=spec.SAVED_AUDIT.read_bytes()
    assert c.digest(raw)==spec.SAVED_AUDIT_SHA
    audit=c.decode(raw)
    pins={name:want for name,want in audit['files_sha256'].items()
          if name.startswith(spec.CHECKPOINT_PREFIX)}
    expected={spec.CHECKPOINT_PREFIX+'campaign_birth.json'} | {
        spec.CHECKPOINT_PREFIX+lc.task_key(task)+suffix for task in lc.task_roster()
        for suffix in ('.birth.json','.model.json','.complete.json')}
    assert len(pins)==190 and set(pins)==expected
    assert all(len(want)==64 and all(x in '0123456789abcdef' for x in want) for want in pins.values())
    return pins


def historical_reference():
    return {'status':'FROZEN_HISTORICAL_SCIENTIFIC_REFERENCE_NOT_CURRENT_RUNTIME_ADMISSION',
        'file_sha256':{**historical.DATA_PINS,'prefit':spec.HISTORICAL_PREFIT_SHA,
                      'projection':spec.HISTORICAL_PROJECTION_SHA},
        'actual_prefit_relative_path':spec.HISTORICAL_PREFIT,
        'actual_prefit_commit':spec.HISTORICAL_PREFIT_COMMIT,
        'projection_admission_relative_path':spec.HISTORICAL_PROJECTION,
        'projection_admission_commit':'28e3f8dc915378ea9837654c536dbb5759475f88',
        'historical_runtime_anchor_sha256':historical.HISTORICAL_ARRAY_ANCHOR,
        'historical_native_profile_origin_sha256':historical.HISTORICAL_PROFILE_ORIGIN,
        'input_authority_granted_here':False}


def matrix_from_bytes(np,raw,*,fresh):
    assert type(raw) is bytes and c.digest(raw)==saved.NPZ_SHA
    fresh()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members=archive.infolist()
        assert len(members)==1 and members[0].filename=='features.npy'
        assert members[0].file_size<=32*2**20 and not members[0].flag_bits&1
    with np.load(io.BytesIO(raw),allow_pickle=False) as archive:
        assert archive.files==['features']
        fresh();matrix=archive['features'].astype(float)
    fresh()
    assert type(matrix) is np.ndarray and matrix.shape==(13781,102)
    assert matrix.dtype.kind=='f' and matrix.dtype.itemsize==8 and matrix.dtype.isnative and not matrix.dtype.hasobject
    assert np.isfinite(matrix).all()
    assert c.digest(matrix.tobytes(order='C'))==historical.FEATURE_BYTES_SHA
    return matrix


@dataclass(frozen=True)
class Inputs:
    metadata:list
    matrix:object
    effects:dict
    historical_plan:object
    checkpoint_hashes:dict
    campaign_birth_raw:bytes


def read_inputs(np,*,fresh):
    c.old_absences();pins=declared_data_pins()
    raw={name:c.read_exact(name,want,fresh=fresh,maximum=64*2**20) for name,want in pins.items()}
    matrix=matrix_from_bytes(np,raw[saved.NPZ],fresh=fresh)
    supplied_raw={'metadata':raw[saved.METADATA_BUNDLE], 'array':raw[saved.ARRAY_CERTIFICATE],
        'labels':raw[saved.LABEL_CERTIFICATE], 'prefit':raw[spec.HISTORICAL_PREFIT],
        'projection':raw[spec.HISTORICAL_PROJECTION]}
    fresh()
    checked=supplied.validate_supplied(np,matrix,supplied_raw,hc.canonical(historical_reference()))
    bundle=c.decode(supplied_raw['metadata'])
    from src.generalization_knowncell_joint_implementation_20261022 import contracts as reference
    assert hc.canonical(reference.full_metadata_contract(checked['metadata']))==hc.canonical(bundle['contract'])
    # Historical terminal receipts are exact pinned evidence, never current owners.
    for name in (saved.ARRAY_SUPERVISOR,saved.LABEL_SUPERVISOR):
        assert c.decode(raw[name])['failure'] is None
    checkpoints=checkpoint_pins()
    birth_name=spec.CHECKPOINT_PREFIX+'campaign_birth.json'
    birth=c.read_exact(birth_name,checkpoints[birth_name],fresh=fresh)
    assert lc.strict_json(birth)=={'status':'LIFECYCLE_STARTED_NOT_SCIENTIFIC_PASS',**checked['plan'].identity()}
    fresh();c.old_absences()
    return Inputs(checked['metadata'],matrix,checked['effects'],checked['plan'],checkpoints,birth)


def load_records(inp,*,fresh):
    assert inp.checkpoint_hashes==checkpoint_pins()
    result=[]
    for task in lc.task_roster():
        key=lc.task_key(task);record={'task_key':key}
        for field,suffix in (('birth_raw','.birth.json'),('checkpoint_raw','.model.json'),('completion_raw','.complete.json')):
            name=spec.CHECKPOINT_PREFIX+key+suffix
            record[field]=c.read_exact(name,inp.checkpoint_hashes[name],fresh=fresh,maximum=16*2**20)
        result.append(record)
    assert len(result)==63
    fresh();c.old_absences()
    return result
