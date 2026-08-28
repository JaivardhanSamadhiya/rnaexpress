"""Run the prespecified post-lock RNAddress v3 TDP-43 failure diagnosis."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import re
import sys
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import seaborn as sns
from scipy.stats import pearsonr, rankdata, spearmanr, theilslopes

from src.pairing.audit_tdp43_v3_sources import (
    FIG4_ZIP,
    FIG6_ZIP,
    SUPP,
    _read_repaired_structure,
    _read_zip_table,
    audit as source_audit,
    sha256,
)


ROOT = Path(__file__).resolve().parents[2]
PAIRS = ROOT / "data" / "processed" / "tdp43_motif_intervention_pairs.csv.gz"
DEV = ROOT / "data" / "processed" / "tdp43_v2_development_pairs.csv.gz"
PREDICTIONS = ROOT / "results" / "v2_tdp43_lock" / "tdp43_v2_frozen_predictions.csv.gz"
OUTCOMES = ROOT / "data" / "frozen" / "outcomes" / "tdp43_v2_locked_outcomes.csv.gz"
HISTORICAL_METRICS = (
    ROOT / "results" / "v2_tdp43_lock" / "tdp43_v2_lock_gene_direction_metrics.csv"
)
CONTEXT = ROOT / "data" / "interim" / "tdp43_v2_splicebert_features.npy"
CONTEXT_ROWS = ROOT / "data" / "interim" / "tdp43_v2_splicebert_rows.csv.gz"
STRUCTURE_CACHE = ROOT / "data" / "interim" / "tdp43_v2_structure_cache.json"
OUT_DIR = ROOT / "results" / "v3_phase2"
FIG_DIR = OUT_DIR / "figures"
PROCESSED_MASTER = ROOT / "data" / "processed" / "tdp43_v3_diagnostic_pairs.csv.gz"

SEED = 20260828
BOOTSTRAPS = 2_000
MOTIFS = ("GTGTG", "TGTGT", "GTATG")
LOCK_GENES = ("Fam160b2", "Lars2", "Diras1", "Synj2bp")
MODELS = (
    "nested_context_external_stack",
    "forward_lightgbm",
    "motif_accessibility_ridge",
)
PRED_COLUMNS = {
    "nested_context_external_stack": "pred_nested_context_external_stack",
    "forward_lightgbm": "pred_forward_lightgbm",
    "motif_accessibility_ridge": "pred_motif_accessibility_ridge",
}
MODEL_LABELS = {
    "nested_context_external_stack": "RNAddress v2.6",
    "forward_lightgbm": "Forward LightGBM",
    "motif_accessibility_ridge": "Motif/accessibility Ridge",
}
MODEL_COLORS = {
    "nested_context_external_stack": "#176B87",
    "forward_lightgbm": "#D95F02",
    "motif_accessibility_ridge": "#7570B3",
}


def _sequence_key(sequence: str) -> str:
    return hashlib.sha256(sequence.encode()).hexdigest()


def _motif_hits(sequence: str) -> list[tuple[str, int, int]]:
    sequence = sequence.upper().replace("U", "T")
    hits: list[tuple[str, int, int]] = []
    for motif in MOTIFS:
        hits.extend(
            (motif, match.start(), match.start() + len(motif))
            for match in re.finditer(f"(?={motif})", sequence)
        )
    return sorted(hits, key=lambda item: (item[1], item[0]))


def _edited_positions(text: str) -> set[int]:
    return {int(value) - 1 for value in str(text).split(";") if value}


def _local_mean(values: np.ndarray, center: int, radius: int) -> float:
    start = max(0, center - radius)
    stop = min(len(values), center + radius + 1)
    return float(np.mean(values[start:stop]))


def _safe_corr(x: pd.Series | np.ndarray, y: pd.Series | np.ndarray, kind: str) -> float:
    pair = pd.DataFrame({"x": x, "y": y}).dropna()
    pair = pair[np.isfinite(pair["x"]) & np.isfinite(pair["y"])]
    if len(pair) < 3 or pair["x"].nunique() < 2 or pair["y"].nunique() < 2:
        return math.nan
    if kind == "spearman":
        return float(spearmanr(pair["x"], pair["y"]).statistic)
    return float(pearsonr(pair["x"], pair["y"]).statistic)


def _bootstrap_corr(
    x: np.ndarray,
    y: np.ndarray,
    *,
    groups: np.ndarray | None = None,
    seed_offset: int = 0,
) -> tuple[float, float]:
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    if groups is not None:
        groups = groups[valid]
    if len(x) < 4:
        return math.nan, math.nan
    rng = np.random.default_rng(SEED + seed_offset)
    estimates: list[float] = []

    def sampled_spearman(left: np.ndarray, right: np.ndarray) -> float:
        if len(left) < 3 or np.ptp(left) == 0 or np.ptp(right) == 0:
            return math.nan
        left_rank = rankdata(left, method="average")
        right_rank = rankdata(right, method="average")
        left_rank -= np.mean(left_rank)
        right_rank -= np.mean(right_rank)
        denominator = math.sqrt(
            float(np.dot(left_rank, left_rank) * np.dot(right_rank, right_rank))
        )
        return float(np.dot(left_rank, right_rank) / denominator) if denominator else math.nan

    if groups is None:
        for _ in range(BOOTSTRAPS):
            take = rng.integers(0, len(x), len(x))
            value = sampled_spearman(x[take], y[take])
            if np.isfinite(value):
                estimates.append(value)
    else:
        unique = np.unique(groups)
        group_indices = {group: np.flatnonzero(groups == group) for group in unique}
        for _ in range(BOOTSTRAPS):
            sampled = rng.choice(unique, size=len(unique), replace=True)
            take = np.concatenate([group_indices[group] for group in sampled])
            value = sampled_spearman(x[take], y[take])
            if np.isfinite(value):
                estimates.append(value)
    if not estimates:
        return math.nan, math.nan
    return tuple(float(value) for value in np.quantile(estimates, [0.025, 0.975]))


def _rank_percentile(values: pd.Series) -> np.ndarray:
    if len(values) <= 1:
        return np.full(len(values), 0.5)
    return (rankdata(values.to_numpy(float), method="average") - 1.0) / (len(values) - 1.0)


def _nanmedian(values: pd.Series) -> float:
    finite = values[np.isfinite(values.to_numpy(float))]
    return float(finite.median()) if len(finite) else math.nan


def _nearest_distance(
    query: np.ndarray,
    reference: np.ndarray,
    metric: str,
    block: int = 256,
) -> np.ndarray:
    output = np.empty(len(query), dtype=np.float64)
    if metric == "cosine":
        reference_norm = np.linalg.norm(reference, axis=1)
        reference_norm[reference_norm == 0] = 1.0
        normalized_reference = reference / reference_norm[:, None]
        for start in range(0, len(query), block):
            current = query[start : start + block]
            current_norm = np.linalg.norm(current, axis=1)
            current_norm[current_norm == 0] = 1.0
            similarity = (current / current_norm[:, None]) @ normalized_reference.T
            output[start : start + len(current)] = 1.0 - np.max(similarity, axis=1)
        return output
    reference_sq = np.sum(reference * reference, axis=1)
    for start in range(0, len(query), block):
        current = query[start : start + block]
        distances_sq = (
            np.sum(current * current, axis=1)[:, None]
            + reference_sq[None, :]
            - 2.0 * (current @ reference.T)
        )
        output[start : start + len(current)] = np.sqrt(
            np.maximum(0.0, np.min(distances_sq, axis=1))
        )
    return output


def _fit_descriptive_ols(y: np.ndarray, design: pd.DataFrame) -> dict[str, float]:
    valid = np.isfinite(y) & np.isfinite(design.to_numpy(float)).all(axis=1)
    yv = y[valid]
    xv = design.loc[valid].to_numpy(float)
    xv = np.column_stack([np.ones(len(xv)), xv])
    coef, _, _, _ = np.linalg.lstsq(xv, yv, rcond=None)
    fitted = xv @ coef
    ss_res = float(np.sum((yv - fitted) ** 2))
    ss_total = float(np.sum((yv - np.mean(yv)) ** 2))
    return {
        "n": int(len(yv)),
        "stability_coefficient": float(coef[1]),
        "r_squared": float(1.0 - ss_res / ss_total) if ss_total else 0.0,
    }


def _load_master() -> pd.DataFrame:
    pairs = pd.read_csv(PAIRS)
    pairs["fractional_edit_size"] = pairs["edited_base_count"] / pairs[
        "parent_sequence"
    ].str.len()
    structure_cache = json.loads(STRUCTURE_CACHE.read_text())

    mechanism_rows: list[dict[str, object]] = []
    for row in pairs.itertuples(index=False):
        parent_hits = _motif_hits(row.parent_sequence)
        mutant_hits = _motif_hits(row.mutant_sequence)
        edited = _edited_positions(row.edit_positions_1based)
        edited_hits = [
            hit for hit in parent_hits if edited.intersection(range(hit[1], hit[2]))
        ]
        unedited_hits = [
            hit for hit in parent_hits if not edited.intersection(range(hit[1], hit[2]))
        ]
        motif_positions = sorted(
            {position for _, start, stop in parent_hits for position in range(start, stop)}
        )
        parent_fold = structure_cache[_sequence_key(row.parent_sequence)]
        mutant_fold = structure_cache[_sequence_key(row.mutant_sequence)]
        parent_unpaired = np.asarray(parent_fold["unpaired"], dtype=float)
        mutant_unpaired = np.asarray(mutant_fold["unpaired"], dtype=float)
        edited_sorted = sorted(edited)
        center = int(round(float(np.mean(edited_sorted))))
        record: dict[str, object] = {
            "canonical_motif_count_parent": len(parent_hits),
            "canonical_motif_count_mutant": len(mutant_hits),
            "canonical_motifs_destroyed": len(edited_hits),
            "remaining_unedited_motif_count": len(unedited_hits),
            "edited_motif_identities": ";".join(hit[0] for hit in edited_hits),
            "parent_motif_identities": ";".join(hit[0] for hit in parent_hits),
            "motif_multiplicity": len(parent_hits),
            "vienna_parent_motif_access_mean": float(np.mean(parent_unpaired[motif_positions])),
            "vienna_parent_motif_access_min": float(np.min(parent_unpaired[motif_positions])),
            "vienna_parent_motif_access_max": float(np.max(parent_unpaired[motif_positions])),
            "vienna_parent_edit_access_mean": float(np.mean(parent_unpaired[edited_sorted])),
            "vienna_mutant_edit_access_mean": float(np.mean(mutant_unpaired[edited_sorted])),
            "vienna_edit_access_delta": float(
                np.mean(mutant_unpaired[edited_sorted]) - np.mean(parent_unpaired[edited_sorted])
            ),
            "vienna_mfe_delta_per_nt": float(
                mutant_fold["mfe_per_nt"] - parent_fold["mfe_per_nt"]
            ),
        }
        for radius in (5, 10, 20):
            parent_local = _local_mean(parent_unpaired, center, radius)
            mutant_local = _local_mean(mutant_unpaired, center, radius)
            record[f"vienna_parent_local_access_r{radius}"] = parent_local
            record[f"vienna_mutant_local_access_r{radius}"] = mutant_local
            record[f"vienna_local_access_delta_r{radius}"] = mutant_local - parent_local
        mechanism_rows.append(record)
    master = pd.concat([pairs, pd.DataFrame(mechanism_rows)], axis=1)

    fig4d = _read_zip_table(FIG4_ZIP, "Figure4/4D/Fig4Dsource.txt")
    clip = fig4d[["oligo", "CLIP"]].rename(
        columns={"oligo": "parent_id", "CLIP": "source_clip_overlap"}
    )
    master = master.merge(clip, on="parent_id", how="left", validate="one_to_one")
    master["clip_supported"] = master["source_clip_overlap"].eq("yes")
    if not (
        master["clip_supported"]
        == master["tdp43_clip_overlap"].astype(str).str.lower().eq("yes")
    ).all():
        raise ValueError("CLIP source contradicts historical reconstruction")

    source_structure = _read_repaired_structure()
    source_structure = source_structure[
        source_structure["motiftype.2"].isin(["GUGUG", "UGUGU"])
    ].copy()
    parent_sequences = master.set_index("parent_id")["parent_sequence"].to_dict()
    source_structure = source_structure[
        source_structure["oligo"].isin(parent_sequences)
    ].copy()
    matched_vienna_access = []
    for position, row in enumerate(source_structure.itertuples(index=False)):
        sequence = parent_sequences[row.oligo]
        start = int(row.kmerpos)
        motif = str(source_structure.iloc[position]["motiftype.2"])
        if sequence[start : start + 5].replace("T", "U") != motif:
            raise ValueError("Figure 4F motif coordinate contradicts EV8 sequence")
        unpaired = np.asarray(
            structure_cache[_sequence_key(sequence)]["unpaired"], dtype=float
        )
        matched_vienna_access.append(float(np.mean(unpaired[start : start + 5])))
    source_structure["vienna_source_matched_access"] = matched_vienna_access
    source_structure["source_motif_access"] = 1.0 - source_structure["bpprob.mean"]
    source_agg = source_structure.groupby("oligo", as_index=False).agg(
        source_parent_motif_pairing_mean=("bpprob.mean", "mean"),
        source_parent_motif_access_mean=("source_motif_access", "mean"),
        source_parent_motif_access_min=("source_motif_access", "min"),
        source_parent_motif_access_max=("source_motif_access", "max"),
        source_parent_motif_records=("motifid", "size"),
        vienna_source_matched_motif_access_mean=("vienna_source_matched_access", "mean"),
    )
    source_agg = source_agg.rename(columns={"oligo": "parent_id"})
    master = master.merge(source_agg, on="parent_id", how="left", validate="one_to_one")

    ev4 = pd.read_excel(
        SUPP / "44318_2025_653_MOESM5_ESM.xlsx", sheet_name="allcounts"
    )
    ev4["rbns_r500"] = (
        ev4["rep1_500nM_norm"] / ev4["rep1_Input_norm"]
        + ev4["rep2_500nM_norm"] / ev4["rep1_Input_norm"]
    ) / 2.0
    rbns = ev4.set_index("oligo")["rbns_r500"]
    master["rbns_parent_r500"] = master["parent_id"].map(rbns)
    master["rbns_mutant_r500"] = master["mutant_id"].map(rbns)
    master["rbns_delta_r500"] = master["rbns_mutant_r500"] - master["rbns_parent_r500"]
    master["rbns_parent_log2_r500"] = np.log2(master["rbns_parent_r500"])
    master["rbns_mutant_log2_r500"] = np.log2(master["rbns_mutant_r500"])
    master["rbns_intervention_log2_delta"] = (
        master["rbns_mutant_log2_r500"] - master["rbns_parent_log2_r500"]
    )

    stability = _read_zip_table(
        FIG6_ZIP, "Figure6/6C/paired_mut_clip_vs_stab_6c.tsv", sep="\t"
    )
    stability_wide = stability.pivot(
        index="name", columns="oligotype", values="log_ko_wt_stb_delta"
    ).rename(
        columns={
            "TDP-43 motif": "stability_parent_log2_ko_wt",
            "Mutant motif": "stability_mutant_log2_ko_wt",
        }
    )
    master["natural_oligo_id"] = master["parent_id"].str.split("|", regex=False).str[0]
    master = master.merge(
        stability_wide,
        left_on="natural_oligo_id",
        right_index=True,
        how="left",
        validate="one_to_one",
    )
    master[["stability_parent_log2_ko_wt", "stability_mutant_log2_ko_wt"]] = master[
        ["stability_parent_log2_ko_wt", "stability_mutant_log2_ko_wt"]
    ].replace([np.inf, -np.inf], np.nan)
    master["stability_intervention_delta"] = (
        master["stability_mutant_log2_ko_wt"]
        - master["stability_parent_log2_ko_wt"]
    )

    predictions = pd.read_csv(PREDICTIONS)
    outcomes = pd.read_csv(OUTCOMES)
    frozen = predictions.merge(
        outcomes,
        on=["parent_id", "mutant_id"],
        how="inner",
        validate="one_to_one",
        suffixes=("", "_revealed"),
    )
    keep = ["parent_id", "mutant_id", *PRED_COLUMNS.values()]
    master = master.merge(frozen[keep], on=["parent_id", "mutant_id"], how="left")
    master["historical_status"] = np.where(
        master[PRED_COLUMNS["nested_context_external_stack"]].notna(),
        "former_locked_post_lock_diagnostic",
        "historical_development",
    )

    for gene, indices in master.groupby("gene_name", sort=True).groups.items():
        indices = list(indices)
        truth_pct = _rank_percentile(master.loc[indices, "delta_localization"])
        master.loc[indices, "measured_effect_percentile"] = truth_pct
        if gene in LOCK_GENES:
            for model, column in PRED_COLUMNS.items():
                predicted_pct = _rank_percentile(master.loc[indices, column])
                master.loc[indices, f"{model}_percentile"] = predicted_pct
                master.loc[indices, f"{model}_rank_error"] = predicted_pct - truth_pct
                master.loc[indices, f"{model}_abs_rank_error"] = np.abs(
                    predicted_pct - truth_pct
                )
    master["custom_minus_forward_rank_advantage"] = (
        master["forward_lightgbm_abs_rank_error"]
        - master["nested_context_external_stack_abs_rank_error"]
    )
    percentile_columns = [f"{model}_percentile" for model in MODELS]
    master["model_disagreement_sd"] = master[percentile_columns].std(axis=1, ddof=0)
    master["model_disagreement_range"] = (
        master[percentile_columns].max(axis=1) - master[percentile_columns].min(axis=1)
    )
    return master


def _add_support_distances(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = pd.read_csv(CONTEXT_ROWS, dtype=str)
    context = np.load(CONTEXT, mmap_mode="r")
    keys = ["gene_id", "parent_id", "mutant_id", "source_figure4e_row"]
    master_keys = master[keys].astype(str)
    row_lookup = rows.reset_index().rename(columns={"index": "context_row"})
    mapped = master_keys.merge(row_lookup, on=keys, how="left", validate="one_to_one")
    if mapped["context_row"].isna().any() or len(set(mapped["context_row"])) != len(master):
        raise ValueError("Frozen contextual cache cannot be mapped one-to-one")
    x = np.asarray(context[mapped["context_row"].to_numpy(int)], dtype=np.float64)

    dev_ids = set(pd.read_csv(DEV)["parent_id"].astype(str))
    is_dev = master["parent_id"].astype(str).isin(dev_ids).to_numpy()
    mean = x[is_dev].mean(axis=0)
    scale = x[is_dev].std(axis=0)
    scale[scale < 1e-8] = 1.0
    x_scaled = (x - mean) / scale
    genes = master["gene_name"].to_numpy(str)
    cosine = np.empty(len(master), dtype=float)
    euclidean = np.empty(len(master), dtype=float)
    for gene in sorted(set(genes)):
        query = np.flatnonzero(genes == gene)
        if gene in LOCK_GENES:
            reference = np.flatnonzero(is_dev)
        else:
            reference = np.flatnonzero(is_dev & (genes != gene))
        cosine[query] = _nearest_distance(x[query], x[reference], "cosine")
        euclidean[query] = _nearest_distance(
            x_scaled[query], x_scaled[reference], "euclidean"
        )
    master["context_nearest_dev_cosine"] = cosine
    master["context_nearest_dev_euclidean"] = euclidean

    mech_columns = [
        "fractional_edit_size",
        "canonical_motif_count_parent",
        "canonical_motif_count_mutant",
        "canonical_motifs_destroyed",
        "remaining_unedited_motif_count",
        "clip_supported",
        "vienna_parent_motif_access_mean",
        "vienna_edit_access_delta",
        "vienna_local_access_delta_r5",
        "vienna_local_access_delta_r10",
        "vienna_local_access_delta_r20",
    ]
    mech = master[mech_columns].astype(float).to_numpy()
    mech_mean = mech[is_dev].mean(axis=0)
    mech_scale = mech[is_dev].std(axis=0)
    mech_scale[mech_scale < 1e-8] = 1.0
    mech_scaled = (mech - mech_mean) / mech_scale
    mech_distance = np.empty(len(master), dtype=float)
    for gene in sorted(set(genes)):
        query = np.flatnonzero(genes == gene)
        if gene in LOCK_GENES:
            reference = np.flatnonzero(is_dev)
        else:
            reference = np.flatnonzero(is_dev & (genes != gene))
        mech_distance[query] = _nearest_distance(
            mech_scaled[query], mech_scaled[reference], "euclidean"
        )
    master["mechanism_nearest_dev_euclidean"] = mech_distance

    dev_cosine_threshold = float(np.quantile(cosine[is_dev], 0.95))
    dev_euclidean_threshold = float(np.quantile(euclidean[is_dev], 0.95))
    dev_mechanism_threshold = float(np.quantile(mech_distance[is_dev], 0.95))
    master["context_cosine_outside_dev95"] = cosine > dev_cosine_threshold
    master["context_euclidean_outside_dev95"] = euclidean > dev_euclidean_threshold
    master["mechanism_outside_dev95"] = mech_distance > dev_mechanism_threshold

    records = []
    for gene, group in master.groupby("gene_name", sort=True):
        records.append(
            {
                "gene_name": gene,
                "historical_role": "former_lock" if gene in LOCK_GENES else "development",
                "n": len(group),
                "median_context_cosine": group["context_nearest_dev_cosine"].median(),
                "p90_context_cosine": group["context_nearest_dev_cosine"].quantile(0.9),
                "fraction_context_cosine_outside_dev95": group[
                    "context_cosine_outside_dev95"
                ].mean(),
                "median_context_euclidean": group[
                    "context_nearest_dev_euclidean"
                ].median(),
                "p90_context_euclidean": group[
                    "context_nearest_dev_euclidean"
                ].quantile(0.9),
                "fraction_context_euclidean_outside_dev95": group[
                    "context_euclidean_outside_dev95"
                ].mean(),
                "median_mechanism_euclidean": group[
                    "mechanism_nearest_dev_euclidean"
                ].median(),
                "fraction_mechanism_outside_dev95": group[
                    "mechanism_outside_dev95"
                ].mean(),
                "dev95_context_cosine_threshold": dev_cosine_threshold,
                "dev95_context_euclidean_threshold": dev_euclidean_threshold,
                "dev95_mechanism_threshold": dev_mechanism_threshold,
            }
        )
    return master, pd.DataFrame(records)


def _stability_metrics(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    complete = master.dropna(
        subset=["stability_intervention_delta", "delta_localization"]
    ).copy()
    records: list[dict[str, object]] = []
    groups: list[tuple[str, pd.DataFrame, bool]] = [
        ("all_16_genes", complete, True),
        (
            "former_lock_4_genes",
            complete[complete["gene_name"].isin(LOCK_GENES)],
            True,
        ),
    ]
    groups.extend(
        (gene, group, False) for gene, group in complete.groupby("gene_name", sort=True)
    )
    for offset, (label, group, clustered) in enumerate(groups):
        x = group["stability_intervention_delta"].to_numpy(float)
        y = group["delta_localization"].to_numpy(float)
        ci = _bootstrap_corr(
            x,
            y,
            groups=group["gene_name"].to_numpy(str) if clustered else None,
            seed_offset=offset * 17,
        )
        if len(group) >= 3 and np.ptp(x) > 0:
            slope = float(theilslopes(y, x, method="separate").slope)
        else:
            slope = math.nan
        records.append(
            {
                "analysis_level": "intervention_mutant_minus_parent",
                "scope": label,
                "n": len(group),
                "genes": group["gene_name"].nunique(),
                "spearman": _safe_corr(x, y, "spearman"),
                "spearman_ci_low": ci[0],
                "spearman_ci_high": ci[1],
                "pearson": _safe_corr(x, y, "pearson"),
                "theil_sen_slope": slope,
                "median_localization_delta": float(np.median(y)),
                "median_stability_delta": float(np.median(x)),
                "same_direction_fraction": float(np.mean(np.sign(x) == np.sign(y))),
            }
        )

    construct_parts = []
    for construct in ("parent", "mutant"):
        part = master[
            [
                "natural_oligo_id",
                "gene_name",
                f"{construct}_localization_log2_neurite_soma",
                f"stability_{construct}_log2_ko_wt",
            ]
        ].copy()
        part.columns = ["pair_id", "gene_name", "localization", "stability"]
        part["construct"] = construct
        construct_parts.append(part)
    constructs = pd.concat(construct_parts, ignore_index=True)
    constructs = constructs[
        np.isfinite(constructs["localization"]) & np.isfinite(constructs["stability"])
    ]
    construct_groups: list[tuple[str, pd.DataFrame, str]] = []
    for subset_name, subset in [
        ("all_16_genes", constructs),
        ("former_lock_4_genes", constructs[constructs["gene_name"].isin(LOCK_GENES)]),
    ]:
        construct_groups.extend(
            [
                (subset_name, subset, "both"),
                (subset_name, subset[subset["construct"] == "parent"], "parent"),
                (subset_name, subset[subset["construct"] == "mutant"], "mutant"),
            ]
        )
    for gene, group in constructs.groupby("gene_name", sort=True):
        construct_groups.extend(
            [
                (gene, group, "both"),
                (gene, group[group["construct"] == "parent"], "parent"),
                (gene, group[group["construct"] == "mutant"], "mutant"),
            ]
        )
    for offset, (label, group, construct) in enumerate(construct_groups, start=100):
        x = group["stability"].to_numpy(float)
        y = group["localization"].to_numpy(float)
        clustered = label in {"all_16_genes", "former_lock_4_genes"}
        paired = construct == "both" and not clustered
        ci = _bootstrap_corr(
            x,
            y,
            groups=(
                group["gene_name"].to_numpy(str)
                if clustered
                else group["pair_id"].to_numpy(str)
                if paired
                else None
            ),
            seed_offset=offset * 17,
        )
        records.append(
            {
                "analysis_level": f"construct_ko_wt_{construct}",
                "scope": label,
                "n": len(group),
                "genes": group["gene_name"].nunique(),
                "spearman": _safe_corr(x, y, "spearman"),
                "spearman_ci_low": ci[0],
                "spearman_ci_high": ci[1],
                "pearson": _safe_corr(x, y, "pearson"),
                "theil_sen_slope": float(theilslopes(y, x, method="separate").slope)
                if len(group) >= 3 and np.ptp(x) > 0
                else math.nan,
                "median_localization_delta": float(np.median(y)),
                "median_stability_delta": float(np.median(x)),
                "same_direction_fraction": float(np.mean(np.sign(x) == np.sign(y))),
            }
        )

    y = complete["delta_localization"].to_numpy(float)
    gene_dummies = pd.get_dummies(
        complete["gene_name"], prefix="gene", drop_first=True, dtype=float
    )
    base = pd.DataFrame(
        {"stability_delta": complete["stability_intervention_delta"].to_numpy(float)}
    )
    mechanism = pd.DataFrame(
        {
            "stability_delta": complete["stability_intervention_delta"].to_numpy(float),
            "clip_supported": complete["clip_supported"].astype(float).to_numpy(),
            "motif_multiplicity": complete["motif_multiplicity"].to_numpy(float),
            "remaining_motifs": complete["remaining_unedited_motif_count"].to_numpy(float),
            "access_delta": complete["vienna_edit_access_delta"].to_numpy(float),
        }
    )
    regression_records = []
    for label, design in [
        ("stability_only", base),
        ("stability_plus_gene", pd.concat([base, gene_dummies.reset_index(drop=True)], axis=1)),
        (
            "stability_plus_gene_and_mechanism",
            pd.concat([mechanism, gene_dummies.reset_index(drop=True)], axis=1),
        ),
    ]:
        result = _fit_descriptive_ols(y, design)
        result["model"] = label
        regression_records.append(result)
    return pd.DataFrame(records), pd.DataFrame(regression_records)


def _binding_metrics(master: pd.DataFrame) -> pd.DataFrame:
    records = []
    definitions = [
        ("parent_construct", "rbns_parent_log2_r500", "parent_localization_log2_neurite_soma"),
        ("mutant_construct", "rbns_mutant_log2_r500", "mutant_localization_log2_neurite_soma"),
        ("intervention_mutant_minus_parent", "rbns_intervention_log2_delta", "delta_localization"),
    ]
    scopes = [
        ("all_16_genes", master),
        ("former_lock_4_genes", master[master["gene_name"].isin(LOCK_GENES)]),
        *((gene, group) for gene, group in master.groupby("gene_name", sort=True)),
    ]
    for level, xcol, ycol in definitions:
        for scope, group in scopes:
            valid = np.isfinite(group[xcol]) & np.isfinite(group[ycol])
            subset = group[valid]
            records.append(
                {
                    "analysis_level": level,
                    "scope": scope,
                    "n": len(subset),
                    "genes": subset["gene_name"].nunique(),
                    "spearman": _safe_corr(subset[xcol], subset[ycol], "spearman"),
                    "pearson": _safe_corr(subset[xcol], subset[ycol], "pearson"),
                    "median_binding": _nanmedian(subset[xcol]),
                    "median_localization": _nanmedian(subset[ycol]),
                }
            )
    return pd.DataFrame(records)


def _structure_metrics(master: pd.DataFrame) -> pd.DataFrame:
    records = []
    features = [
        "source_parent_motif_access_mean",
        "vienna_source_matched_motif_access_mean",
        "vienna_parent_motif_access_mean",
        "vienna_edit_access_delta",
        "vienna_local_access_delta_r5",
        "vienna_local_access_delta_r10",
        "vienna_local_access_delta_r20",
    ]
    targets = [
        "delta_localization",
        "nested_context_external_stack_abs_rank_error",
        "custom_minus_forward_rank_advantage",
    ]
    scopes = [
        ("all_16_genes", master),
        ("former_lock_4_genes", master[master["gene_name"].isin(LOCK_GENES)]),
        *((gene, group) for gene, group in master.groupby("gene_name", sort=True)),
    ]
    for feature in features:
        for target in targets:
            for scope, group in scopes:
                valid = np.isfinite(group[feature]) & np.isfinite(group[target])
                records.append(
                    {
                        "feature": feature,
                        "target": target,
                        "scope": scope,
                        "n": int(valid.sum()),
                        "spearman": _safe_corr(
                            group.loc[valid, feature], group.loc[valid, target], "spearman"
                        ),
                    }
                )
    valid = np.isfinite(master["source_parent_motif_access_mean"]) & np.isfinite(
        master["vienna_source_matched_motif_access_mean"]
    )
    records.append(
        {
            "feature": "source_parent_motif_access_mean",
            "target": "vienna_source_matched_motif_access_mean",
            "scope": "sanity_check_exact_matched_motifs",
            "n": int(valid.sum()),
            "spearman": _safe_corr(
                master.loc[valid, "source_parent_motif_access_mean"],
                master.loc[valid, "vienna_source_matched_motif_access_mean"],
                "spearman",
            ),
        }
    )
    return pd.DataFrame(records)


def _mechanism_metrics(master: pd.DataFrame) -> pd.DataFrame:
    frame = master.copy()
    frame["clip_stratum"] = np.where(frame["clip_supported"], "motif + CLIP", "motif, no CLIP")
    frame["edited_motif_stratum"] = np.where(
        frame["canonical_motifs_destroyed"] > 1, "multiple edited motifs", "single edited motif"
    )
    frame["remaining_motif_stratum"] = np.where(
        frame["remaining_unedited_motif_count"] > 0,
        "remaining unedited motif",
        "no remaining motif",
    )
    frame["accessibility_quartile"] = pd.qcut(
        frame["vienna_parent_motif_access_mean"],
        4,
        labels=["Q1 paired", "Q2", "Q3", "Q4 accessible"],
        duplicates="drop",
    ).astype(str)
    records = []
    for variable in [
        "clip_stratum",
        "edited_motif_stratum",
        "remaining_motif_stratum",
        "accessibility_quartile",
    ]:
        for (gene, value), group in frame.groupby(["gene_name", variable], observed=True):
            records.append(
                {
                    "stratum_variable": variable,
                    "stratum_value": value,
                    "gene_name": gene,
                    "n": len(group),
                    "median_localization_delta": group["delta_localization"].median(),
                    "median_abs_localization_delta": group["delta_localization"].abs().median(),
                    "median_stability_delta": group["stability_intervention_delta"].median(),
                    "median_custom_abs_rank_error": _nanmedian(
                        group["nested_context_external_stack_abs_rank_error"]
                    ),
                    "median_custom_minus_forward_rank_advantage": _nanmedian(
                        group["custom_minus_forward_rank_advantage"]
                    ),
                }
            )
        for value, group in frame.groupby(variable, observed=True):
            records.append(
                {
                    "stratum_variable": variable,
                    "stratum_value": value,
                    "gene_name": "ALL",
                    "n": len(group),
                    "median_localization_delta": group["delta_localization"].median(),
                    "median_abs_localization_delta": group["delta_localization"].abs().median(),
                    "median_stability_delta": group["stability_intervention_delta"].median(),
                    "median_custom_abs_rank_error": _nanmedian(
                        group["nested_context_external_stack_abs_rank_error"]
                    ),
                    "median_custom_minus_forward_rank_advantage": _nanmedian(
                        group["custom_minus_forward_rank_advantage"]
                    ),
                }
            )
    return pd.DataFrame(records)


def _regret_metrics(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    locked = master[master["gene_name"].isin(LOCK_GENES)].copy()
    records: list[dict[str, object]] = []
    quantile_records: list[dict[str, object]] = []
    for gene, group in locked.groupby("gene_name", sort=True):
        measured = group["delta_localization"].to_numpy(float)
        for direction, sign in [("increase", 1.0), ("decrease", -1.0)]:
            utility = sign * measured
            oracle = int(np.argmax(utility))
            best, worst = float(np.max(utility)), float(np.min(utility))
            for model, column in PRED_COLUMNS.items():
                predicted_utility = sign * group[column].to_numpy(float)
                order = np.argsort(-predicted_utility, kind="stable")
                selected = int(order[0])
                oracle_rank = int(np.flatnonzero(order == oracle)[0] + 1)
                selected_utility = float(utility[selected])
                record = {
                    "gene_name": gene,
                    "direction": direction,
                    "model": model,
                    "n_candidates": len(group),
                    "selected_parent_id": str(group.iloc[selected]["parent_id"]),
                    "selected_mutant_id": str(group.iloc[selected]["mutant_id"]),
                    "selected_measured_effect": float(measured[selected]),
                    "selected_utility": selected_utility,
                    "oracle_measured_effect": float(measured[oracle]),
                    "oracle_utility": best,
                    "oracle_predicted_rank": oracle_rank,
                    "oracle_predicted_percentile": 1.0
                    - (oracle_rank - 1.0) / max(1.0, len(group) - 1.0),
                    "regret": best - selected_utility,
                    "normalized_regret": (best - selected_utility) / (best - worst)
                    if best > worst
                    else 0.0,
                    "selected_rank_percentile": float(
                        np.mean(utility <= selected_utility)
                    ),
                    "top3_oracle_coverage": bool(oracle_rank <= 3),
                    "top5_oracle_coverage": bool(oracle_rank <= 5),
                    "selected_model_disagreement": float(
                        group.iloc[selected]["model_disagreement_sd"]
                    ),
                }
                records.append(record)
                predicted_pct = _rank_percentile(pd.Series(predicted_utility))
                measured_pct = _rank_percentile(pd.Series(utility))
                for top_fraction in (0.05, 0.10, 0.20):
                    threshold = float(np.quantile(utility, 1.0 - top_fraction))
                    mask = utility >= threshold
                    quantile_records.append(
                        {
                            "gene_name": gene,
                            "direction": direction,
                            "model": model,
                            "top_fraction": top_fraction,
                            "n": int(mask.sum()),
                            "mean_abs_percentile_error": float(
                                np.mean(np.abs(predicted_pct[mask] - measured_pct[mask]))
                            ),
                            "spearman_within_tail": _safe_corr(
                                predicted_utility[mask], utility[mask], "spearman"
                            ),
                            "top1_selected_in_tail": bool(utility[selected] >= threshold),
                        }
                    )
    return pd.DataFrame(records), pd.DataFrame(quantile_records)


def _disagreement_metrics(master: pd.DataFrame, regret: pd.DataFrame) -> pd.DataFrame:
    locked = master[master["gene_name"].isin(LOCK_GENES)].copy()
    records = []
    disagreement_groups = [("ALL", locked)] + list(locked.groupby("gene_name", sort=True))
    for gene, group in disagreement_groups:
        for label, subset in [
            ("all", group),
            ("low_q25", group[group["model_disagreement_sd"] <= group["model_disagreement_sd"].quantile(0.25)]),
            ("high_q25", group[group["model_disagreement_sd"] >= group["model_disagreement_sd"].quantile(0.75)]),
        ]:
            records.append(
                {
                    "gene_name": gene,
                    "disagreement_stratum": label,
                    "n": len(subset),
                    "median_disagreement": subset["model_disagreement_sd"].median(),
                    "median_custom_abs_rank_error": subset[
                        "nested_context_external_stack_abs_rank_error"
                    ].median(),
                    "mean_custom_abs_rank_error": subset[
                        "nested_context_external_stack_abs_rank_error"
                    ].mean(),
                    "spearman_disagreement_vs_custom_error": _safe_corr(
                        subset["model_disagreement_sd"],
                        subset["nested_context_external_stack_abs_rank_error"],
                        "spearman",
                    ),
                }
            )
    for _, row in regret.iterrows():
        records.append(
            {
                "gene_name": row["gene_name"],
                "disagreement_stratum": f"selected_{row['model']}_{row['direction']}",
                "n": 1,
                "median_disagreement": row["selected_model_disagreement"],
                "median_custom_abs_rank_error": math.nan,
                "mean_custom_abs_rank_error": math.nan,
                "spearman_disagreement_vs_custom_error": math.nan,
            }
        )
    return pd.DataFrame(records)


def _ranking_failure_metrics(master: pd.DataFrame) -> pd.DataFrame:
    locked = master[master["gene_name"].isin(LOCK_GENES)].copy()
    locked["custom_rank_error_direction"] = np.where(
        locked["nested_context_external_stack_rank_error"] >= 0,
        "overpromoted",
        "oversuppressed",
    )
    delta = (
        locked["nested_context_external_stack_abs_rank_error"]
        - locked["forward_lightgbm_abs_rank_error"]
    )
    locked["rank_winner"] = np.select(
        [delta < -1e-12, delta > 1e-12],
        ["custom_better", "forward_better"],
        default="tie",
    )
    records = []
    for (gene, winner, direction), group in locked.groupby(
        ["gene_name", "rank_winner", "custom_rank_error_direction"], sort=True
    ):
        records.append(
            {
                "gene_name": gene,
                "rank_winner": winner,
                "custom_error_direction": direction,
                "n": len(group),
                "median_delta_localization": group["delta_localization"].median(),
                "median_abs_effect": group["delta_localization"].abs().median(),
                "median_edited_bases": group["edited_base_count"].median(),
                "clip_supported_fraction": group["clip_supported"].mean(),
                "median_custom_abs_rank_error": group[
                    "nested_context_external_stack_abs_rank_error"
                ].median(),
                "median_forward_abs_rank_error": group[
                    "forward_lightgbm_abs_rank_error"
                ].median(),
            }
        )
    return pd.DataFrame(records)


def _gene_profiles(
    master: pd.DataFrame,
    stability: pd.DataFrame,
    ood: pd.DataFrame,
    regret: pd.DataFrame,
) -> pd.DataFrame:
    historical = pd.read_csv(HISTORICAL_METRICS)
    gene_historical = historical.groupby(["gene_name", "model"], as_index=False).agg(
        rank_percentile=("rank_percentile", "mean"),
        normalized_regret=("normalized_regret", "mean"),
        spearman=("spearman", "mean"),
    )
    records = []
    for gene in LOCK_GENES:
        group = master[master["gene_name"] == gene]
        custom = gene_historical[
            (gene_historical["gene_name"] == gene)
            & (gene_historical["model"] == "nested_context_external_stack")
        ].iloc[0]
        forward = gene_historical[
            (gene_historical["gene_name"] == gene)
            & (gene_historical["model"] == "forward_lightgbm")
        ].iloc[0]
        stab = stability[stability["scope"] == gene].iloc[0]
        support = ood[ood["gene_name"] == gene].iloc[0]
        gene_regret = regret[
            (regret["gene_name"] == gene)
            & (regret["model"] == "nested_context_external_stack")
        ]
        records.append(
            {
                "gene_name": gene,
                "n_interventions": len(group),
                "custom_rank_percentile": custom["rank_percentile"],
                "forward_rank_percentile": forward["rank_percentile"],
                "custom_minus_forward_rank_gain": custom["rank_percentile"]
                - forward["rank_percentile"],
                "custom_normalized_regret": custom["normalized_regret"],
                "forward_normalized_regret": forward["normalized_regret"],
                "custom_spearman": custom["spearman"],
                "stability_pairs": int(stab["n"]),
                "stability_localization_spearman": stab["spearman"],
                "stability_localization_ci_low": stab["spearman_ci_low"],
                "stability_localization_ci_high": stab["spearman_ci_high"],
                "clip_supported_fraction": group["clip_supported"].mean(),
                "median_parent_motif_count": group["motif_multiplicity"].median(),
                "multiple_motif_fraction": (group["motif_multiplicity"] > 1).mean(),
                "remaining_unedited_motif_fraction": (
                    group["remaining_unedited_motif_count"] > 0
                ).mean(),
                "median_parent_motif_accessibility": group[
                    "vienna_parent_motif_access_mean"
                ].median(),
                "median_context_cosine": support["median_context_cosine"],
                "fraction_context_outside_dev95": support[
                    "fraction_context_cosine_outside_dev95"
                ],
                "median_mechanism_distance": support["median_mechanism_euclidean"],
                "median_model_disagreement": group["model_disagreement_sd"].median(),
                "disagreement_error_spearman": _safe_corr(
                    group["model_disagreement_sd"],
                    group["nested_context_external_stack_abs_rank_error"],
                    "spearman",
                ),
                "mean_custom_oracle_rank": gene_regret[
                    "oracle_predicted_rank"
                ].mean(),
                "custom_top5_oracle_coverage": gene_regret[
                    "top5_oracle_coverage"
                ].mean(),
            }
        )
    return pd.DataFrame(records)


def _publication_style() -> None:
    sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "figure.constrained_layout.use": True,
        }
    )


def _save_figure(fig: plt.Figure, name: str) -> None:
    fig.savefig(FIG_DIR / f"{name}.png", bbox_inches="tight", facecolor="white")
    svg_path = FIG_DIR / f"{name}.svg"
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    # Matplotlib leaves spaces after SVG path commands. Normalize them so generated
    # figures are deterministic and pass repository whitespace validation.
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n"
    )
    plt.close(fig)


def _figures(
    master: pd.DataFrame,
    stability: pd.DataFrame,
    mechanism: pd.DataFrame,
    ood: pd.DataFrame,
    regret: pd.DataFrame,
    profiles: pd.DataFrame,
) -> None:
    _publication_style()
    historical = pd.read_csv(HISTORICAL_METRICS)
    by_gene = historical.groupby(["gene_name", "model"], as_index=False).agg(
        rank_percentile=("rank_percentile", "mean"),
        normalized_regret=("normalized_regret", "mean"),
    )
    by_gene["model_label"] = by_gene["model"].map(MODEL_LABELS)
    palette = {MODEL_LABELS[key]: value for key, value in MODEL_COLORS.items()}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7))
    sns.barplot(
        data=by_gene,
        x="gene_name",
        y="rank_percentile",
        hue="model_label",
        hue_order=list(palette),
        palette=palette,
        ax=axes[0],
    )
    axes[0].axhline(0.5, color="black", linestyle="--", linewidth=0.8)
    axes[0].set(title="Directional rank percentile", xlabel="", ylabel="Rank percentile")
    axes[0].legend_.remove()
    sns.barplot(
        data=by_gene,
        x="gene_name",
        y="normalized_regret",
        hue="model_label",
        hue_order=list(palette),
        palette=palette,
        ax=axes[1],
    )
    axes[1].set(title="Selected-edit normalized regret", xlabel="", ylabel="Normalized regret")
    axes[1].legend(title="", loc="upper left", bbox_to_anchor=(1.01, 1.0))
    fig.suptitle("Figure 1. Frozen model performance is heterogeneous across TDP-43 genes")
    _save_figure(fig, "figure1_frozen_model_comparison")

    complete = master.dropna(subset=["stability_intervention_delta"])
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.8))
    former = complete[complete["gene_name"].isin(LOCK_GENES)]
    sns.scatterplot(
        data=former,
        x="stability_intervention_delta",
        y="delta_localization",
        hue="gene_name",
        s=12,
        alpha=0.6,
        ax=axes[0, 0],
    )
    axes[0, 0].axhline(0, color="grey", linewidth=0.6)
    axes[0, 0].axvline(0, color="grey", linewidth=0.6)
    lock_metric = stability[stability["scope"] == "former_lock_4_genes"].iloc[0]
    axes[0, 0].set_title(f"Former lock genes (rho={lock_metric['spearman']:.2f})")
    axes[0, 0].legend(title="", fontsize=7)
    for axis, gene in zip(axes.flat[1:5], LOCK_GENES):
        group = former[former["gene_name"] == gene]
        sns.regplot(
            data=group,
            x="stability_intervention_delta",
            y="delta_localization",
            scatter_kws={"s": 12, "alpha": 0.55},
            line_kws={"color": "black", "linewidth": 1},
            ci=None,
            ax=axis,
        )
        metric = stability[stability["scope"] == gene].iloc[0]
        axis.set_title(f"{gene} (rho={metric['spearman']:.2f}, n={metric['n']})")
        axis.axhline(0, color="grey", linewidth=0.5)
        axis.axvline(0, color="grey", linewidth=0.5)
    axes[1, 2].axis("off")
    fig.suptitle("Figure 2. Motif mutation couples reporter localization and stability")
    _save_figure(fig, "figure2_localization_vs_stability")

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    plot_data = master[master["gene_name"].isin(LOCK_GENES)].copy()
    plot_data["CLIP"] = np.where(plot_data["clip_supported"], "CLIP-supported", "No CLIP")
    plot_data["motif_architecture"] = np.where(
        plot_data["canonical_motifs_destroyed"] > 1, "Multiple motifs", "Single motif"
    )
    sns.boxplot(
        data=plot_data,
        x="gene_name",
        y="delta_localization",
        hue="CLIP",
        showfliers=False,
        ax=axes[0],
    )
    axes[0].set(title="Localization effect by CLIP", xlabel="", ylabel="Mutant - parent localization")
    axes[0].legend(title="", fontsize=7)
    sns.boxplot(
        data=plot_data,
        x="gene_name",
        y="delta_localization",
        hue="motif_architecture",
        showfliers=False,
        ax=axes[1],
    )
    axes[1].set(title="Effect by motif multiplicity", xlabel="", ylabel="")
    axes[1].legend(title="", fontsize=6)
    plot_data["access_quartile"] = pd.qcut(
        plot_data["vienna_parent_motif_access_mean"], 4, labels=["Q1", "Q2", "Q3", "Q4"]
    )
    sns.boxplot(
        data=plot_data,
        x="access_quartile",
        y="delta_localization",
        hue="gene_name",
        showfliers=False,
        ax=axes[2],
    )
    axes[2].set(title="Effect by motif accessibility", xlabel="Parent accessibility quartile", ylabel="")
    axes[2].legend(title="", fontsize=6)
    fig.suptitle("Figure 3. Motif context, occupancy, and local accessibility")
    _save_figure(fig, "figure3_mechanism_stratification")

    lock_ood = ood[ood["gene_name"].isin(LOCK_GENES)].merge(
        profiles[["gene_name", "custom_minus_forward_rank_gain"]], on="gene_name"
    )
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.8))
    for axis, xcol, title in [
        (axes[0], "median_context_cosine", "Contextual nearest-development distance"),
        (axes[1], "median_mechanism_euclidean", "Mechanistic nearest-development distance"),
    ]:
        axis.scatter(lock_ood[xcol], lock_ood["custom_minus_forward_rank_gain"], s=55, color="#176B87")
        for row in lock_ood.itertuples(index=False):
            axis.annotate(row.gene_name, (getattr(row, xcol), row.custom_minus_forward_rank_gain), xytext=(4, 4), textcoords="offset points")
        axis.axhline(0, color="black", linestyle="--", linewidth=0.8)
        axis.set(title=title, xlabel="Median support distance", ylabel="Custom - forward rank gain")
    fig.suptitle("Figure 4. Outcome-free distance does not automatically identify transfer failure")
    _save_figure(fig, "figure4_performance_vs_ood")

    comparison = regret[regret["model"].isin(["nested_context_external_stack", "forward_lightgbm"])].copy()
    comparison["label"] = comparison["gene_name"] + "\n" + comparison["direction"]
    comparison["model_label"] = comparison["model"].map(MODEL_LABELS)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    sns.barplot(
        data=comparison,
        x="label",
        y="normalized_regret",
        hue="model_label",
        palette=palette,
        ax=axes[0],
    )
    axes[0].tick_params(axis="x", rotation=35)
    axes[0].set(title="Top-1 normalized regret", xlabel="", ylabel="Normalized regret")
    axes[0].legend(title="", fontsize=7)
    sns.scatterplot(
        data=comparison,
        x="oracle_predicted_rank",
        y="normalized_regret",
        hue="model_label",
        style="direction",
        palette=palette,
        s=65,
        ax=axes[1],
    )
    for row in comparison.itertuples(index=False):
        axes[1].annotate(row.gene_name, (row.oracle_predicted_rank, row.normalized_regret), xytext=(3, 3), textcoords="offset points", fontsize=7)
    axes[1].set(title="Missing the oracle drives regret", xlabel="Predicted rank of experimental oracle", ylabel="Normalized regret")
    axes[1].legend(title="", fontsize=7)
    fig.suptitle("Figure 5. Regret decomposes into extreme-edit coverage failures")
    _save_figure(fig, "figure5_regret_decomposition")

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    locked = master[master["gene_name"].isin(LOCK_GENES)]
    sns.scatterplot(
        data=locked,
        x="model_disagreement_sd",
        y="nested_context_external_stack_abs_rank_error",
        hue="gene_name",
        s=14,
        alpha=0.6,
        ax=axes[0],
    )
    axes[0].set(title="Intervention-level disagreement", xlabel="SD of model percentiles", ylabel="RNAddress absolute rank error")
    axes[0].legend(title="", fontsize=7)
    selected = regret[regret["model"] == "nested_context_external_stack"]
    sns.scatterplot(
        data=selected,
        x="selected_model_disagreement",
        y="normalized_regret",
        hue="gene_name",
        style="direction",
        s=75,
        ax=axes[1],
    )
    axes[1].set(title="Disagreement of selected edits", xlabel="Selected-edit disagreement", ylabel="Normalized regret")
    axes[1].legend(title="", fontsize=7)
    fig.suptitle("Figure 6. Frozen-model disagreement as a diagnostic trust signal")
    _save_figure(fig, "figure6_disagreement_vs_error")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    audit = source_audit()
    if audit["historical_pairing_error_found"]:
        raise RuntimeError("STOP: historical TDP-43 pairing error found")
    master = _load_master()
    master, ood = _add_support_distances(master)
    stability, stability_regression = _stability_metrics(master)
    binding = _binding_metrics(master)
    structure = _structure_metrics(master)
    mechanism = _mechanism_metrics(master)
    regret, effect_quantiles = _regret_metrics(master)
    disagreement = _disagreement_metrics(master, regret)
    ranking_failures = _ranking_failure_metrics(master)
    profiles = _gene_profiles(master, stability, ood, regret)

    outputs = {
        "tdp_diagnostic_master.csv.gz": master,
        "gene_failure_profiles.csv": profiles,
        "stability_localization_metrics.csv": stability,
        "stability_regression_metrics.csv": stability_regression,
        "binding_localization_metrics.csv": binding,
        "structure_metrics.csv": structure,
        "mechanism_strata_metrics.csv": mechanism,
        "ood_metrics.csv": ood,
        "model_disagreement_metrics.csv": disagreement,
        "regret_decomposition.csv": regret,
        "effect_quantile_metrics.csv": effect_quantiles,
        "ranking_failure_metrics.csv": ranking_failures,
    }
    for name, frame in outputs.items():
        frame.to_csv(
            OUT_DIR / name,
            index=False,
            compression={"method": "gzip", "mtime": 0} if name.endswith(".gz") else None,
        )
    master.to_csv(
        PROCESSED_MASTER,
        index=False,
        compression={"method": "gzip", "mtime": 0},
    )
    _figures(master, stability, mechanism, ood, regret, profiles)

    source_access = master.dropna(
        subset=[
            "source_parent_motif_access_mean",
            "vienna_source_matched_motif_access_mean",
        ]
    )
    manifest = {
        "phase": "v3_phase2_post_lock_diagnostic",
        "seed": SEED,
        "bootstrap_replicates": BOOTSTRAPS,
        "historical_pairs_preserved": len(master),
        "historical_pairing_error_found": False,
        "former_lock_rows_with_frozen_predictions": int(
            master[PRED_COLUMNS["nested_context_external_stack"]].notna().sum()
        ),
        "stability_pairs_both_finite": int(master["stability_intervention_delta"].notna().sum()),
        "rbns_pairs_both_finite": int(master["rbns_delta_r500"].notna().sum()),
        "source_vs_vienna_accessibility_spearman": _safe_corr(
            source_access["source_parent_motif_access_mean"],
            source_access["vienna_source_matched_motif_access_mean"],
            "spearman",
        ),
        "package_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "matplotlib": plt.matplotlib.__version__,
            "seaborn": sns.__version__,
        },
        "source_hashes": audit["source_sha256"],
        "output_hashes": {
            name: sha256(OUT_DIR / name) for name in outputs
        },
        "protected_data_access": audit["protected_data_access"],
        "deviations": [
            "Raw EV5 stability reconstruction was quarantined because 10,935 sample+oligo keys duplicate WT_t0_1 and WT_t0_3 is absent.",
            "Figure 4F parsing repairs only the publisher's literal unquoted newline inside two CLIP labels.",
            "No post-lock refitting was used merely to create historical predictions for the 12 development genes; leave-one-gene-out support is outcome-free.",
        ],
    }
    (OUT_DIR / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
