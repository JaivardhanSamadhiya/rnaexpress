"""Outcome-blind feature transformations for frozen FinalShot controls."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from src.modeling.finalshot_models import FeatureLayout, FinalShotFeatureStore
from src.modeling.v4_phaseB2_context import edit_band, operation_signature


CONTROL_SEED = 42_017
CONTROL_NAMES = (
    "rbp_identity_permutation",
    "delta_rbp_shuffle",
    "cell_context_permutation",
    "parent_binding_knockout",
    "trans_interaction_knockout",
)
DELTA_OFFSETS = np.asarray([0, 1, 2, 3, 4, 5, 8], dtype=np.int32)
PARENT_OFFSETS = np.asarray([6, 7], dtype=np.int32)


def stable_seed(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def delta_shuffle_map(rows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Return deterministic cross-unit delta donors and frozen eligibility.

    Complete delta blocks are reassigned from a different biological unit in
    the same frozen stratum.  Unit sizes need not match, so donor rows cycle
    deterministically within the next hash-ordered unit.  This preserves each
    donor block intact and never consults an outcome.
    """
    work = pd.DataFrame({
        "dataset": rows["dataset"].astype(str),
        "cell_type": rows["cell_type"].astype(str),
        "operation_signature": operation_signature(rows).to_numpy(),
        "edit_band": edit_band(rows["edit_cost"]).to_numpy(),
        "motif_family": rows["motif_family"].fillna("none").astype(str),
        "biological_unit": rows["biological_unit"].astype(str),
        "candidate_id": rows["candidate_id"].astype(str),
    })
    keys = ["dataset", "cell_type", "operation_signature", "edit_band", "motif_family"]
    donor = np.full(len(rows), -1, dtype=np.int32)
    records = []
    for key, raw_indices in work.groupby(keys, sort=True, dropna=False).indices.items():
        indices = np.asarray(raw_indices, dtype=np.int32)
        units = work.iloc[indices]["biological_unit"].to_numpy(str)
        eligible = len(indices) >= 5 and len(set(units)) >= 2
        record = {name: str(value) for name, value in zip(keys, key)}
        record.update({"rows": int(len(indices)), "biological_units": int(len(set(units))), "eligible": eligible})
        records.append(record)
        if not eligible:
            continue
        unit_order = sorted(set(units), key=lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest())
        for unit_index, unit in enumerate(unit_order):
            source_rows = indices[units == unit]
            donor_unit = unit_order[(unit_index + 1) % len(unit_order)]
            donor_rows = indices[units == donor_unit]
            source_rows = np.asarray(sorted(
                source_rows,
                key=lambda idx: hashlib.sha256(work.iloc[int(idx)]["candidate_id"].encode("utf-8")).hexdigest(),
            ), dtype=np.int32)
            donor_rows = np.asarray(sorted(
                donor_rows,
                key=lambda idx: hashlib.sha256(work.iloc[int(idx)]["candidate_id"].encode("utf-8")).hexdigest(),
            ), dtype=np.int32)
            offset = stable_seed("||".join(map(str, key)) + "||" + unit) % len(donor_rows)
            for position, source_index in enumerate(source_rows):
                donor[int(source_index)] = donor_rows[(position + offset) % len(donor_rows)]
    eligible_mask = donor >= 0
    if np.any(
        work.loc[eligible_mask, "biological_unit"].to_numpy()
        == work.iloc[donor[eligible_mask]]["biological_unit"].to_numpy()
    ):
        raise RuntimeError("Delta-RBP shuffle assigned a same-unit donor")
    return donor, eligible_mask, pd.DataFrame(records)


class FinalShotControlledFeatureStore(FinalShotFeatureStore):
    """Materialize one frozen mechanism-breaking control design."""

    def __init__(
        self,
        rows: pd.DataFrame,
        rbp_matrix_path: str | Path,
        dictionary_path: str | Path,
        expression_path: str | Path,
        control: str,
    ) -> None:
        if control not in CONTROL_NAMES:
            raise ValueError(f"Unknown FinalShot control: {control}")
        super().__init__(rows, rbp_matrix_path, dictionary_path, expression_path)
        self.control = control
        self.eligible_mask = np.ones(len(self.rows), dtype=bool)
        self.delta_donor = np.full(len(self.rows), -1, dtype=np.int32)
        self.delta_strata = pd.DataFrame()
        self.identity_permutations: np.ndarray | None = None
        self.control_context = self.context

        if control == "rbp_identity_permutation":
            permutation_by_feature = np.empty((self.rbp.shape[0], 103), dtype=np.int16)
            representatives = self.rows.drop_duplicates("feature_row").set_index("feature_row")
            if len(representatives) != self.rbp.shape[0]:
                raise RuntimeError("RBP identity control lacks one representative per feature row")
            for feature_row in range(self.rbp.shape[0]):
                row = representatives.loc[feature_row]
                key = f"{row['parent_sequence']}||{row['mutant_sequence']}"
                permutation_by_feature[feature_row] = np.random.default_rng(stable_seed(key)).permutation(103)
            self.identity_permutations = permutation_by_feature
        elif control == "delta_rbp_shuffle":
            self.delta_donor, self.eligible_mask, self.delta_strata = delta_shuffle_map(self.rows)
        elif control == "cell_context_permutation":
            swapped = self.context.copy()
            mikl = self.rows["dataset"].eq("mikl_gse173098").to_numpy()
            cell = self.rows["cell_type"].replace({"Neuro-2a": "N2A"}).astype(str).to_numpy()
            for group_index in np.flatnonzero(self.context_eligible):
                cad = float(self.context[np.flatnonzero(cell == "CAD")[0], group_index])
                n2a = float(self.context[np.flatnonzero(cell == "N2A")[0], group_index])
                swapped[mikl & (cell == "CAD"), group_index] = n2a
                swapped[mikl & (cell == "N2A"), group_index] = cad
            self.control_context = swapped

    def layout(self, family: str) -> FeatureLayout:
        if self.control == "trans_interaction_knockout" and family == "M2":
            return super().layout("M1")
        return super().layout(family)

    def materialize(self, indices: np.ndarray, family: str) -> tuple[np.ndarray, FeatureLayout]:
        indices = np.asarray(indices, dtype=np.int64)
        if self.control == "delta_rbp_shuffle" and not self.eligible_mask[indices].all():
            raise ValueError("Delta-RBP control received an ineligible row")
        effective_family = "M1" if self.control == "trans_interaction_knockout" and family == "M2" else family
        layout = super().layout(effective_family)
        output = np.empty((len(indices), layout.feature_count), dtype=np.float32)
        output[:, layout.geometry] = self.geometry[indices]
        if effective_family == "M0":
            return output, layout

        feature_rows = self.feature_rows[indices]
        selected = np.asarray(self.rbp[feature_rows], dtype=np.float32)
        donor_selected = None
        if self.control == "delta_rbp_shuffle":
            donor_feature_rows = self.feature_rows[self.delta_donor[indices]]
            donor_selected = np.asarray(self.rbp[donor_feature_rows], dtype=np.float32)
        permutations = None
        if self.control == "rbp_identity_permutation":
            assert self.identity_permutations is not None
            permutations = self.identity_permutations[feature_rows]

        row_index = np.arange(len(indices))[:, None]
        for group_index in range(103):
            if permutations is not None:
                source_group = permutations[:, group_index]
                source_columns = source_group[:, None] * 9 + np.arange(9)[None, :]
                source = selected[row_index, source_columns]
            else:
                source = selected[:, group_index * 9:(group_index + 1) * 9]
            if donor_selected is not None:
                source = source.copy()
                donor_block = donor_selected[:, group_index * 9:(group_index + 1) * 9]
                source[:, DELTA_OFFSETS] = donor_block[:, DELTA_OFFSETS]
            if self.control == "parent_binding_knockout":
                source = source.copy()
                source[:, PARENT_OFFSETS] = 0.0
            output[:, layout.base_columns[group_index]] = source
            interaction = layout.interaction_columns[group_index]
            if len(interaction):
                output[:, interaction] = source * self.control_context[indices, group_index, None]
        if not np.isfinite(output).all():
            raise ValueError("Controlled FinalShot design contains non-finite values")
        return output, layout
