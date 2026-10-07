"""Known-endpoint rankers with two already-exposed nuclear auxiliary parents.

Auxiliary SIRLOIN outcomes are training data only. Exclusion decisions use a
frozen core metadata table without localization or replicate outcomes. An
endpoint is specified by the requested measurement, not inferred from labels.
"""

from functools import lru_cache
import hashlib
import io

from .common import np, pd, ROOT, ART, OUT, csvsave, jsave, save, sha256, readj

CONFIGS = [{"id": "endpoint_l2_005", "penalty": .005},
           {"id": "endpoint_l2_05", "penalty": .05},
           {"id": "endpoint_l2_5", "penalty": .5}]
ENDPOINTS = {"projection": 0, "nuclear_cytoplasmic": 1}


def endpoint_flags(frame):
    values = frame["endpoint_class"].map(ENDPOINTS)
    if values.isna().any():
        raise ValueError("Endpoint must be prospectively known projection or nuclear_cytoplasmic")
    return values.to_numpy(dtype=int)


def build_features(frame, base246):
    matrix = np.asarray(base246, dtype=float)
    if matrix.shape != (len(frame), 246) or not np.isfinite(matrix).all():
        raise ValueError("Endpoint route requires finite row-aligned historical 246 features")
    return np.column_stack((matrix, endpoint_flags(frame)))


def prepare_auxiliary():
    """Run before freeze; only admitted exposed C1/C2 outcomes are copied."""
    from .common import load
    from src.cross_assay_20260927.features import build
    source = ROOT / "artifacts/cross_assay_20260927/canonical_interventions.csv"
    canonical = pd.read_csv(source, low_memory=False)
    auxiliary = canonical[canonical.dataset.eq("sirloin") & canonical.candidate_set_eligible].copy().reset_index(drop=True)
    assert len(auxiliary) == 223
    assert set(auxiliary.parent_id) == {"Jpx_9", "NICN1_53"}
    assert auxiliary.biological_component.nunique() == 2
    assert set(auxiliary.exposure_status) == {"EXPOSED_DEVELOPMENT"}
    assert set(auxiliary.admission_status) == {"ADMIT_SECONDARY"}
    assert set(auxiliary.endpoint_class) == {"nuclear_cytoplasmic"}
    assert np.isfinite(auxiliary.measured_delta.to_numpy(float)).all()
    features, _ = build(auxiliary)
    core, _ = load()
    columns = ["intervention_id", "biological_component", "parent_sequence", "mutant_sequence"]
    metadata = core[columns].copy()
    assert len(metadata) == 26258 and not metadata.intervention_id.duplicated().any()
    csvsave(ART / "endpoint_auxiliary.csv.gz", auxiliary, True)
    csvsave(OUT / "endpoint_auxiliary_core_exclusion.csv.gz", metadata, True)
    buffer = io.BytesIO()
    np.savez_compressed(buffer, features=features["interaction_3"])
    save(ART / "endpoint_auxiliary_features.npz", buffer.getvalue())
    paths = [ART / "endpoint_auxiliary.csv.gz", ART / "endpoint_auxiliary_features.npz", OUT / "endpoint_auxiliary_core_exclusion.csv.gz"]
    jsave(OUT / "endpoint_auxiliary_feature_receipt.json", {
        "source": source.relative_to(ROOT).as_posix(), "source_sha256": sha256(source),
        "files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths},
        "auxiliary_rows": 223, "auxiliary_parents": 2, "auxiliary_components": 2,
        "auxiliary_parent_ids": sorted(auxiliary.parent_id.unique()),
        "core_rows": len(metadata), "built_before_fitting": True,
        "use": "Previously exposed secondary SIRLOIN C1/C2 rows; nuclear head training only; never evaluated",
        "exclusion_metadata_has_outcomes": False, "new_or_reserved_outcomes_opened": False,
    })


def select_auxiliary(auxiliary, core_metadata, training_ids):
    """Purge whole auxiliary components touching any excluded core allele/unit."""
    training_ids = set(training_ids)
    all_ids = set(core_metadata.intervention_id)
    if not training_ids <= all_ids:
        raise ValueError("Training frame contains IDs outside frozen core metadata")
    excluded = core_metadata[~core_metadata.intervention_id.isin(training_ids)]
    blocked_core_components = set(excluded.biological_component)
    blocked_alleles = set(excluded.parent_sequence) | set(excluded.mutant_sequence)
    touched = auxiliary.biological_component.isin(blocked_core_components)
    touched |= auxiliary.parent_sequence.isin(blocked_alleles) | auxiliary.mutant_sequence.isin(blocked_alleles)
    blocked_aux_components = set(auxiliary.loc[touched, "biological_component"])
    keep = ~auxiliary.biological_component.isin(blocked_aux_components).to_numpy()
    retained = auxiliary.loc[keep]
    assert not set(retained.biological_component) & blocked_core_components
    assert not (set(retained.parent_sequence) | set(retained.mutant_sequence)) & blocked_alleles
    return keep, {
        "excluded_core_rows": len(excluded),
        "excluded_core_components": len(blocked_core_components),
        "excluded_core_alleles": len(blocked_alleles),
        "purged_auxiliary_components": sorted(blocked_aux_components),
        "retained_auxiliary_rows": int(keep.sum()),
        "retained_auxiliary_components": sorted(retained.biological_component.unique()),
        "retained_auxiliary_ids": sorted(retained.intervention_id),
        "excluded_core_ids_sha256": hashlib.sha256("|".join(sorted(excluded.intervention_id)).encode()).hexdigest(),
    }


@lru_cache(maxsize=1)
def load_auxiliary():
    receipt = readj(OUT / "endpoint_auxiliary_feature_receipt.json")
    for name, checksum in receipt["files"].items():
        assert sha256(ROOT / name) == checksum, name
    auxiliary = pd.read_csv(ART / "endpoint_auxiliary.csv.gz", low_memory=False)
    metadata = pd.read_csv(OUT / "endpoint_auxiliary_core_exclusion.csv.gz", low_memory=False)
    with np.load(ART / "endpoint_auxiliary_features.npz") as archive:
        features = archive["features"].astype(float)
    assert features.shape == (len(auxiliary), 246) and np.isfinite(features).all()
    assert list(metadata) == ["intervention_id", "biological_component", "parent_sequence", "mutant_sequence"]
    return auxiliary, features, metadata, receipt


def fit_model(frame, x, config):
    from .route_scaling import fit_model as fit_shared
    frame = frame.reset_index(drop=True)
    x = np.asarray(x, dtype=float)
    if x.shape != (len(frame), 247) or not np.isfinite(x).all():
        raise ValueError("Endpoint feature schema mismatch")
    flags = endpoint_flags(frame)
    np.testing.assert_array_equal(x[:, -1], flags)
    auxiliary, auxiliary_x, metadata, receipt = load_auxiliary()
    keep, exclusion = select_auxiliary(auxiliary, metadata, frame.intervention_id)
    retained, retained_x = auxiliary.loc[keep].reset_index(drop=True), auxiliary_x[keep]
    heads = {}
    for endpoint in (0, 1):
        indexes = flags == endpoint
        training_frame, training_x = frame.loc[indexes].reset_index(drop=True), x[indexes, :246]
        if endpoint == 1:
            training_frame = pd.concat((training_frame, retained), ignore_index=True)
            training_x = np.vstack((training_x, retained_x))
        if len(training_frame) < 2 or not len(training_frame):
            # Explicit unsupported head: equal utilities, never projection-head
            # substitution and never fitting an endpoint on its target labels.
            heads[str(endpoint)] = {"unsupported": True, "training_rows": len(training_frame)}
        else:
            head = fit_shared(training_frame, training_x, {**config, "scaling": "pair"})
            head["training_ids_sha256"] = hashlib.sha256("|".join(training_frame.intervention_id).encode()).hexdigest()
            heads[str(endpoint)] = head
    return {"kind": "known_endpoint_separate_pair_RMS_heads", "config": dict(config), "heads": heads,
            "auxiliary_exclusion": exclusion, "auxiliary_receipt_sha256": sha256(OUT / "endpoint_auxiliary_feature_receipt.json"),
            "auxiliary_source_sha256": receipt["source_sha256"], "training_core_rows": len(frame),
            "endpoint_input_semantics": "prospectively known assay destination family, not study identity or fitted label",
            "calibrated_probability_claim": False}


def predict_model(model, x):
    from .route_scaling import predict_model as predict_shared
    matrix = np.asarray(x, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] != 247 or not np.isfinite(matrix).all():
        raise ValueError("Endpoint feature schema mismatch")
    flags = matrix[:, -1]
    if not set(np.unique(flags)) <= {0., 1.}:
        raise ValueError("Unknown endpoint flag at inference")
    score = np.zeros(len(matrix))
    for endpoint in (0, 1):
        indexes = flags == endpoint
        head = model["heads"][str(endpoint)]
        if indexes.any() and not head.get("unsupported", False):
            score[indexes] = predict_shared(head, matrix[indexes, :246])
    return score
