"""Fixed outcome-free motif score hypotheses, not occupancy probabilities."""

from functools import lru_cache
import json

from .catalog import np, ART, BASE_ORDER, matrix_digest

PSEUDOCOUNT = 1e-4
BACKGROUND = np.full(4, .25)
FEATURE_POOLS = ("global_mean", "global_max", "affected_mean", "affected_max")
PLAN = {
    "version": "direct_human_experimental_pfm_v1",
    "motif_inclusion": "Official human main evidence table; D protein plus experimental motif type; nonempty supplied PFM; exact normalized-matrix dedup",
    "fixed_pseudocount_per_probability": PSEUDOCOUNT,
    "background_ACGU": [0.25] * 4,
    "score": "exp(mean_position(log(((row_normalized_PFM+1e-4)/(1+4e-4))/0.25)))",
    "score_interpretation": "Geometric-mean likelihood ratio to uniform background; computational specificity proxy, not physical affinity or occupancy",
    "feature_order": "Lexical representative motif ID, then global_mean/global_max/affected_mean/affected_max",
    "global_pool": "All complete forward-strand motif windows in exact available encoded allele",
    "affected_pool": "Union of complete motif windows overlapping any changed nucleotide, identical corresponding start coordinates for parent and mutant",
    "empty_pool": "Zero; complete motif windows only, no sequence padding",
    "reverse_complement_scanning": False,
    "allele_feature": "Mutant pool summary minus corresponding parent pool summary",
    "accessibility_candidate": "Window specificity score times arithmetic mean of per-base ensemble unpaired marginals; same pools; not joint opening probability",
    "accessibility_off_control": "Exactly same scores/pools with all unpaired marginals set to one",
    "SRLE_context": "Certified author20+6+20 local synthesis window; not complete mature HBB",
    "other_context": "Exact admitted inserts; no invented full transcript",
    "representation_routes_proposed": ["corrected_base246+raw1684", "corrected_base246+raw1684+accessible1684"],
    "selection_proposed": "Same whole-assay/component/allele purge and source-only nested L2 .005/.05/.5, training-pair RMS; future separate root freeze required",
    "outcome_selection": False,
    "full_project_feature_generation_authorized": False,
    "biological_fit_authorized": False,
}


def normalize(sequence):
    sequence = str(sequence).upper().replace("T", "U")
    if not sequence or set(sequence) - set(BASE_ORDER):
        raise ValueError("Exact nonempty A/C/G/U sequence required")
    return sequence


def smooth_log_odds(pfm):
    pfm = np.asarray(pfm, dtype=float)
    if pfm.ndim != 2 or pfm.shape[1] != 4 or not np.isfinite(pfm).all() or np.any(pfm < 0):
        raise ValueError("Finite nonnegative four-base matrix required")
    total = pfm.sum(1)
    if np.any(total <= 0):
        raise ValueError("Positive PFM row sums required")
    probability = pfm / total[:, None]
    return np.log((probability + PSEUDOCOUNT) / (1 + 4 * PSEUDOCOUNT) / BACKGROUND)


@lru_cache(maxsize=1)
def load_groups():
    manifest = json.loads((ART / "direct_human_manifest.json").read_text())
    motifs = manifest["motifs"]
    assert len(motifs) == 421 and manifest["unique_normalized_pfms"] == len(motifs)
    grouped = {}
    for index, motif in enumerate(motifs):
        pfm = np.asarray(motif["probabilities_ACGU"], dtype="<f8")
        assert matrix_digest(pfm) == motif["normalized_pfm_sha256"]
        grouped.setdefault(len(pfm), []).append((index, smooth_log_odds(pfm)))
    return [(width, np.asarray([item[0] for item in values], int),
             np.stack([item[1] for item in values])) for width, values in sorted(grouped.items())]


def scan(sequence, groups=None):
    """Return all motif-window scores in width groups; no project frame input."""
    sequence = normalize(sequence)
    codes = np.asarray([BASE_ORDER.index(base) for base in sequence], int)
    result = []
    for width, indices, logs in (load_groups() if groups is None else groups):
        count = max(0, len(sequence) - width + 1)
        values = np.zeros((len(indices), count))
        for position in range(width):
            values += logs[:, position, codes[position:position + count]]
        values = np.exp(values / width)
        assert np.isfinite(values).all() and np.all((values > 0) & (values <= 4 + 1e-12))
        result.append((width, indices, values))
    return result


def summaries(sequence, changed, unpaired=None, groups=None):
    sequence = normalize(sequence)
    changed = np.asarray(changed, int)
    if changed.ndim != 1 or np.any(changed < 0) or np.any(changed >= len(sequence)):
        raise ValueError("Valid corresponding-coordinate changed sites required")
    if unpaired is None:
        unpaired = np.ones(len(sequence))
    unpaired = np.asarray(unpaired, dtype=float)
    if unpaired.shape != (len(sequence),) or not np.isfinite(unpaired).all() or np.any((unpaired < 0) | (unpaired > 1)):
        raise ValueError("Per-base unpaired marginals in [0,1] required")
    blocks = scan(sequence, groups)
    dimension = max((int(indices.max()) + 1 for _, indices, _ in blocks if len(indices)), default=0)
    result = np.zeros((dimension, len(FEATURE_POOLS)))
    prefix = np.r_[0., np.cumsum(unpaired)]
    for width, indices, values in blocks:
        count = values.shape[1]
        if not count:
            continue
        starts = np.arange(count)
        weights = (prefix[starts + width] - prefix[starts]) / width
        weighted = values * weights[None, :]
        affected = np.any((starts[:, None] <= changed[None, :]) &
                          (changed[None, :] < (starts + width)[:, None]), axis=1)
        result[indices, 0] = weighted.mean(1)
        result[indices, 1] = weighted.max(1)
        if affected.any():
            result[indices, 2] = weighted[:, affected].mean(1)
            result[indices, 3] = weighted[:, affected].max(1)
    return result.ravel()


def allele_delta(parent, mutant, parent_unpaired=None, mutant_unpaired=None, groups=None):
    parent, mutant = normalize(parent), normalize(mutant)
    if len(parent) != len(mutant):
        raise ValueError("Aligned corresponding-coordinate substitutions required")
    changed = np.flatnonzero([left != right for left, right in zip(parent, mutant)])
    if not len(changed):
        return np.zeros_like(summaries(parent, (), parent_unpaired, groups))
    return (summaries(mutant, changed, mutant_unpaired, groups)
            - summaries(parent, changed, parent_unpaired, groups))
