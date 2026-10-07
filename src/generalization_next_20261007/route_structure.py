"""Prespecified local ensemble-accessibility edit features; no supervised fit.

RNA folding concerns the exact available insert/local construction sequence,
not the unknown complete reporter. Motif weights are means of constituent
nucleotide unpaired marginals, not joint motif-opening or binding probabilities.
"""

from functools import lru_cache
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "data/interim/mechanism_v2/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
import numpy as np
import RNA

NS = "generalization_next_20261007"
SRC, OUT, REP, ART = [ROOT / folder / NS for folder in ("src", "results", "reports", "artifacts")]
CONTEXT_SOURCE = ROOT / "artifacts/generalization_20261007/reporter_context_metadata.json"
CONTEXT_SHA256 = "e7ee4fea706d3b7e611f63d491304cfe835efcd3c9b6a9a4f0282abf384f725c"
STUDIES = ("astrocyte_gse330741", "mikl_gse173098", "moffatt_gse334718", "srle")
TEMPERATURE = 37.
RADIUS = 10
FEATURE_NAMES = (
    "delta_changed_site_mean_unpaired", "delta_changed_site_min_unpaired", "delta_changed_site_max_unpaired",
    "delta_neighborhood_mean_unpaired", "delta_changed_site_mean_pairing_entropy_bits",
    "delta_changed_site_mean_expected_pairing_distance_fraction",
    "delta_neighborhood_accessible_AG_nucleotide_fraction",
    "delta_neighborhood_accessible_AG_dinucleotide_density",
    "delta_neighborhood_accessible_GA_dinucleotide_density",
    "delta_neighborhood_accessible_CCTCCC_density", "delta_neighborhood_max_CCTCCC_accessibility",
)
RAW_FEATURE_NAMES = (
    "delta_neighborhood_raw_AG_nucleotide_fraction",
    "delta_neighborhood_raw_AG_dinucleotide_density",
    "delta_neighborhood_raw_GA_dinucleotide_density",
    "delta_neighborhood_raw_CCTCCC_density",
    "delta_neighborhood_raw_CCTCCC_presence",
)
CONFIGS = [{"id": "structure_l2_005", "penalty": .005},
           {"id": "structure_l2_05", "penalty": .05},
           {"id": "structure_l2_5", "penalty": .5}]
SPEC = {
    "version": "local_ensemble_accessibility_v2_matched_raw_control",
    "ViennaRNA_version": "2.7.2", "temperature_C": TEMPERATURE,
    "parameter_set": "explicit RNA Turner2004", "dangles": 2, "minimum_loop_size": 3,
    "GU_pairs": True, "GU_closures": True, "circular": False, "salt_M": 1.021,
    "maximum_pair_span": "unrestricted within exact available input",
    "partition_ensemble": "global equilibrium partition function of exact insert/local construction sequence",
    "feature_names": list(FEATURE_NAMES), "raw_control_feature_names": list(RAW_FEATURE_NAMES),
    "additional_columns": 16, "base_columns": 246,
    "feature_neighborhood": "union of corresponding-coordinate changed sites +/-10nt; truncate to exact input bounds; no padding",
    "SRLE_input": "certified20ntleft+exact6mer+certified20ntright,46nt; not complete mature HBB",
    "SRLE_metadata_sha256": CONTEXT_SHA256,
    "other_input": "exact admitted insert sequence, not fabricated whole reporter",
    "motif_accessibility": "arithmetic mean of per-base unpaired marginals across the complete motif; not joint opening probability",
    "normalization": "actual neighborhood nucleotide count or eligible fully-contained motif-start count",
    "raw_control": "same exact inputs, changed coordinates, masks, motifs and normalization; all unpaired weights1; append raw5 before ensemble11",
    "outcome_inputs": False, "physical_folds_alone_claim": False,
    "supervised_configurations": CONFIGS, "selection": "future source-only nested selection; no target-label tuning",
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, payload):
    path = Path(path).resolve()
    if not any(path.is_relative_to(root) for root in (SRC, OUT, REP, ART)):
        raise PermissionError("Output outside additive structure namespace")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError("Preserving existing artifact " + str(path))
    else:
        path.write_bytes(payload)


def jsave(path, data):
    save(path, (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def normalize(sequence):
    value = str(sequence).upper().replace("U", "T")
    if not value or set(value) - set("ACGT"):
        raise ValueError("Exact nonempty A/C/G/T sequence required")
    return value


@lru_cache(maxsize=1)
def certified_arms():
    assert sha256(CONTEXT_SOURCE) == CONTEXT_SHA256, "Certified local context metadata changed"
    metadata = json.loads(CONTEXT_SOURCE.read_text(encoding="utf-8"))
    design = metadata["local_design"]
    assert design["existing_counter_10nt_flank_match"] and design["reverse_oligo_complement_match"]
    left, right = normalize(design["left_20nt_dna"]), normalize(design["right_20nt_dna"])
    assert len(left) == len(right) == 20 and design["length_nt"] == 46
    assert design["template_dna"] == left + "N" * 6 + right
    return left, right


def model_details():
    if RNA.__version__ != SPEC["ViennaRNA_version"]:
        raise RuntimeError("Prespecified ViennaRNA2.7.2 runtime required")
    RNA.params_load_RNA_Turner2004()
    md = RNA.md()
    md.temperature, md.dangles, md.min_loop_size = TEMPERATURE, 2, 3
    md.noGU, md.noGUclosure, md.circ = 0, 0, 0
    md.salt, md.max_bp_span, md.betaScale = 1.021, -1, 1.
    return md


def partition(sequence, forced_unpaired=()):
    """The forced argument is reserved for independent synthetic probability QA."""
    sequence = normalize(sequence).replace("T", "U")
    compound = RNA.fold_compound(sequence, model_details(), RNA.OPTION_MFE | RNA.OPTION_PF)
    for index in forced_unpaired:
        compound.hc_add_up(int(index) + 1, RNA.CONSTRAINT_CONTEXT_ALL_LOOPS)
    _, minimum_energy = compound.mfe()
    compound.exp_params_rescale(minimum_energy)
    _, ensemble_energy = compound.pf()
    if not np.isfinite(ensemble_energy):
        raise ArithmeticError("Nonfinite partition energy")
    return compound, float(ensemble_energy)


@lru_cache(maxsize=20000)
def ensemble(sequence):
    sequence = normalize(sequence)
    compound, energy = partition(sequence)
    upper = np.asarray(compound.bpp(), dtype=float)[1:, 1:]
    # ViennaRNA bpp exposes only upper-triangle probabilities. Both row and
    # column contributions are needed for each nucleotide's paired marginal.
    paired = upper + upper.T
    if not np.isfinite(paired).all() or np.any(paired < -1e-10) or np.any(paired.sum(1) > 1 + 1e-6):
        raise ArithmeticError("Invalid ensemble pairing probabilities")
    unpaired = np.clip(1 - paired.sum(1), 0., 1.)
    entropy = np.zeros(len(sequence))
    positive = paired > 0
    logs = np.zeros_like(paired); logs[positive] = np.log2(paired[positive])
    entropy -= (paired * logs).sum(1)
    positive_unpaired = unpaired > 0
    entropy[positive_unpaired] -= unpaired[positive_unpaired] * np.log2(unpaired[positive_unpaired])
    indexes = np.arange(len(sequence))
    distance = (paired * np.abs(indexes[:, None] - indexes[None, :])).sum(1) / max(1, len(sequence) - 1)
    return unpaired, entropy, distance, energy


def local_mask(length, positions):
    mask = np.zeros(length, dtype=bool)
    for position in positions:
        mask[max(0, position - RADIUS):min(length, position + RADIUS + 1)] = True
    return mask


def accessible_motif(sequence, unpaired, mask, motif):
    starts = [start for start in range(len(sequence) - len(motif) + 1)
              if mask[start:start + len(motif)].all()]
    weights = [float(unpaired[start:start + len(motif)].mean()) for start in starts
               if sequence[start:start + len(motif)] == motif]
    return sum(weights) / max(1, len(starts)), max(weights, default=0.)


def summaries(sequence, positions, summary_provider=None):
    sequence = normalize(sequence)
    unpaired, entropy, distance, _ = (ensemble if summary_provider is None else summary_provider)(sequence)
    positions = np.asarray(positions, dtype=int)
    if not len(positions) or positions.min() < 0 or positions.max() >= len(sequence):
        raise ValueError("Nonempty valid changed-site coordinates required")
    mask = local_mask(len(sequence), positions)
    ag = np.fromiter((base in "AG" for base in sequence), dtype=float)
    motif_ag, _ = accessible_motif(sequence, unpaired, mask, "AG")
    motif_ga, _ = accessible_motif(sequence, unpaired, mask, "GA")
    core_density, core_max = accessible_motif(sequence, unpaired, mask, "CCTCCC")
    return np.array([unpaired[positions].mean(), unpaired[positions].min(), unpaired[positions].max(),
        unpaired[mask].mean(), entropy[positions].mean(), distance[positions].mean(),
        np.mean((ag * unpaired)[mask]), motif_ag, motif_ga, core_density, core_max])


def encoded_pair(parent, mutant, dataset):
    parent, mutant = normalize(parent), normalize(mutant)
    if len(parent) != len(mutant) or dataset not in STUDIES:
        raise ValueError("Corresponding-coordinate substitutions in an admitted source required")
    changed = np.flatnonzero([left != right for left, right in zip(parent, mutant)])
    if dataset == "srle":
        if len(parent) != 6:
            raise ValueError("SRLE local context must start from an exact sixmer")
        left, right = certified_arms()
        parent, mutant = left + parent + right, left + mutant + right
        changed = changed + len(left)
    return parent, mutant, changed


def structure_delta(parent, mutant, dataset, summary_provider=None):
    parent, mutant, changed = encoded_pair(parent, mutant, dataset)
    if not len(changed):
        return np.zeros(len(FEATURE_NAMES))
    result = summaries(mutant, changed, summary_provider) - summaries(parent, changed, summary_provider)
    if not np.isfinite(result).all():
        raise ArithmeticError("Nonfinite structure features")
    return result


def unit_unpaired_summary(sequence):
    """Accessibility-off control; no partition function or physical assumption."""
    length = len(normalize(sequence))
    return np.ones(length), np.zeros(length), np.zeros(length), 0.


def raw_delta(parent, mutant, dataset):
    return structure_delta(parent, mutant, dataset, summary_provider=unit_unpaired_summary)[6:]


def build_raw_features(frame, base246):
    baseline = np.asarray(base246, dtype=float)
    if baseline.shape != (len(frame), 246) or not np.isfinite(baseline).all():
        raise ValueError("Expected finite row-aligned corrected 246 features")
    raw = np.array([raw_delta(parent, mutant, dataset) for parent, mutant, dataset in
                    zip(frame["parent_sequence"], frame["mutant_sequence"], frame["dataset"])])
    if not len(frame):
        raw = np.zeros((0, len(RAW_FEATURE_NAMES)))
    return np.column_stack((baseline, raw))


def build_features(frame, base246, summary_provider=None):
    baseline = build_raw_features(frame, base246)
    block = np.array([structure_delta(parent, mutant, dataset, summary_provider) for parent, mutant, dataset in
                      zip(frame["parent_sequence"], frame["mutant_sequence"], frame["dataset"])])
    if not len(frame):
        block = np.zeros((0, len(FEATURE_NAMES)))
    return np.column_stack((baseline, block))


def fit_model(frame, x, config):
    from src.generalization_20261007.route_scaling import fit_model as fit_shared
    return fit_shared(frame, x, {**config, "scaling": "pair"})


def predict_model(model, x):
    from src.generalization_20261007.route_scaling import predict_model as predict_shared
    return predict_shared(model, x)
