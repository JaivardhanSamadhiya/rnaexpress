"""Context-conditioned v2 rankers and strong forward baselines."""

from __future__ import annotations

import random

import lightgbm as lgb
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch import nn

from .v2_features import V2Features, absolute_sequence_features


SEED = 20260826


def _relevance_bins(frame: pd.DataFrame, levels: int = 16) -> np.ndarray:
    labels = np.zeros(len(frame), dtype=np.int32)
    for _, indices in frame.groupby("parent_id", sort=True).indices.items():
        values = frame.iloc[indices]["delta_localization"].to_numpy(float)
        order = np.argsort(values, kind="stable")
        ranks = np.empty(len(values), dtype=int)
        ranks[order] = np.arange(len(values))
        labels[np.asarray(indices)] = np.minimum(levels - 1, ranks * levels // len(values))
    return labels


def fit_context_lambdamart(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    frame: pd.DataFrame,
    features: V2Features,
) -> np.ndarray:
    train = frame.iloc[train_indices].copy()
    train["_global_index"] = train_indices
    train = train.sort_values(["parent_id", "source_row"], kind="stable")
    ordered = train["_global_index"].to_numpy(int)
    labels = _relevance_bins(train)
    groups = train.groupby("parent_id", sort=True).size().to_numpy(int)
    model = lgb.LGBMRanker(
        objective="lambdarank",
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=15,
        min_child_samples=30,
        reg_lambda=1.0,
        subsample=1.0,
        colsample_bytree=0.7,
        random_state=SEED,
        n_jobs=-1,
        verbosity=-1,
    )
    model.fit(features.joint[ordered], labels, group=groups)
    return model.predict(features.joint[test_indices])


def fit_forward_lightgbm(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    frame: pd.DataFrame,
) -> np.ndarray:
    train = frame.iloc[train_indices]
    parent_first = ~train.duplicated("parent_id")
    train_sequences = pd.concat(
        [train["mutant_sequence"], train.loc[parent_first, "parent_sequence"]],
        ignore_index=True,
    )
    target = np.concatenate(
        [
            train["mutant_localization_log2_neurite_soma"].to_numpy(float),
            train.loc[parent_first, "parent_localization_log2_neurite_soma"].to_numpy(float),
        ]
    )
    model = lgb.LGBMRegressor(
        objective="regression_l2",
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=15,
        min_child_samples=30,
        reg_lambda=1.0,
        colsample_bytree=0.7,
        random_state=SEED,
        n_jobs=-1,
        verbosity=-1,
    )
    model.fit(absolute_sequence_features(train_sequences), target)
    test = frame.iloc[test_indices]
    return model.predict(absolute_sequence_features(test["mutant_sequence"])) - model.predict(
        absolute_sequence_features(test["parent_sequence"])
    )


class FactorizedContextRanker(nn.Module):
    def __init__(self, parent_dim: int, edit_dim: int, rank: int = 8, hidden: int = 32):
        super().__init__()
        self.parent = nn.Sequential(
            nn.Linear(parent_dim, hidden), nn.Tanh(), nn.Linear(hidden, rank)
        )
        self.edit = nn.Sequential(nn.Linear(edit_dim, hidden), nn.Tanh(), nn.Linear(hidden, rank))
        self.additive = nn.Linear(edit_dim, 1)

    def forward(self, parent: torch.Tensor, edit: torch.Tensor) -> torch.Tensor:
        interaction = (self.parent(parent) * self.edit(edit)).sum(dim=1)
        return interaction + self.additive(edit).squeeze(1)


class MultiTaskFactorizedContextRanker(nn.Module):
    def __init__(self, parent_dim: int, edit_dim: int, rank: int = 8, hidden: int = 32):
        super().__init__()
        self.parent = nn.Sequential(
            nn.Linear(parent_dim, hidden), nn.Tanh(), nn.Linear(hidden, rank)
        )
        self.edit = nn.Sequential(nn.Linear(edit_dim, hidden), nn.Tanh(), nn.Linear(hidden, rank))
        self.nzip_additive = nn.Linear(edit_dim, 1)
        self.aux_additive = nn.Linear(edit_dim, 1)

    def forward(
        self, parent: torch.Tensor, edit: torch.Tensor, task: str
    ) -> torch.Tensor:
        interaction = (self.parent(parent) * self.edit(edit)).sum(dim=1)
        head = self.nzip_additive if task == "nzip" else self.aux_additive
        return interaction + head(edit).squeeze(1)


def _pair_indices(frame: pd.DataFrame, pairs_per_parent: int = 600) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    high_indices: list[int] = []
    low_indices: list[int] = []
    for _, indices in frame.groupby("parent_id", sort=True).indices.items():
        indices = np.asarray(indices, int)
        y = frame.iloc[indices]["delta_localization"].to_numpy(float)
        order = np.argsort(y, kind="stable")
        quartile = max(1, len(order) // 4)
        low = indices[order[:quartile]]
        high = indices[order[-quartile:]]
        high_indices.extend(rng.choice(high, size=pairs_per_parent, replace=True))
        low_indices.extend(rng.choice(low, size=pairs_per_parent, replace=True))
    return np.asarray(high_indices, int), np.asarray(low_indices, int)


def fit_factorized_context_ranker(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    frame: pd.DataFrame,
    features: V2Features,
    rank: int = 8,
    hidden: int = 32,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-3,
    epochs: int = 200,
    pairs_per_parent: int = 600,
) -> np.ndarray:
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    train = frame.iloc[train_indices].reset_index(drop=True)
    p_scaler = StandardScaler().fit(features.parent[train_indices])
    e_scaler = StandardScaler().fit(features.edit[train_indices])
    parent_train = torch.tensor(
        p_scaler.transform(features.parent[train_indices]), dtype=torch.float32
    )
    edit_train = torch.tensor(e_scaler.transform(features.edit[train_indices]), dtype=torch.float32)
    high, low = _pair_indices(train, pairs_per_parent=pairs_per_parent)
    model = FactorizedContextRanker(parent_train.shape[1], edit_train.shape[1], rank, hidden)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=learning_rate, weight_decay=weight_decay
    )
    batch_size = 2048
    generator = torch.Generator().manual_seed(SEED)
    for _ in range(epochs):
        order = torch.randperm(len(high), generator=generator)
        for first in range(0, len(high), batch_size):
            batch = order[first : first + batch_size]
            hi = torch.as_tensor(high, dtype=torch.long)[batch]
            lo = torch.as_tensor(low, dtype=torch.long)[batch]
            high_score = model(parent_train[hi], edit_train[hi])
            low_score = model(parent_train[lo], edit_train[lo])
            loss = torch.nn.functional.softplus(-(high_score - low_score)).mean()
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
    model.eval()
    with torch.no_grad():
        parent_test = torch.tensor(
            p_scaler.transform(features.parent[test_indices]), dtype=torch.float32
        )
        edit_test = torch.tensor(
            e_scaler.transform(features.edit[test_indices]), dtype=torch.float32
        )
        return model(parent_test, edit_test).numpy()


def fit_factorized_context_with_tdp_auxiliary(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    nzip_frame: pd.DataFrame,
    nzip_features: V2Features,
    auxiliary_frame: pd.DataFrame,
    auxiliary_features: V2Features,
    rank: int = 8,
    hidden: int = 32,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-3,
    epochs: int = 200,
    pairs_per_group: int = 600,
) -> np.ndarray:
    """Equal-loss multitask training on N-zip and permitted TDP-43 genes."""
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    nzip_train_frame = nzip_frame.iloc[train_indices].reset_index(drop=True)
    aux_frame = auxiliary_frame.reset_index(drop=True).copy()
    aux_frame["parent_id"] = aux_frame["gene_id"].astype(str)

    parent_fit = np.vstack(
        [nzip_features.parent[train_indices], auxiliary_features.parent]
    )
    edit_fit = np.vstack([nzip_features.edit[train_indices], auxiliary_features.edit])
    p_scaler = StandardScaler().fit(parent_fit)
    e_scaler = StandardScaler().fit(edit_fit)
    nzip_parent = torch.tensor(
        p_scaler.transform(nzip_features.parent[train_indices]), dtype=torch.float32
    )
    nzip_edit = torch.tensor(
        e_scaler.transform(nzip_features.edit[train_indices]), dtype=torch.float32
    )
    aux_parent = torch.tensor(
        p_scaler.transform(auxiliary_features.parent), dtype=torch.float32
    )
    aux_edit = torch.tensor(e_scaler.transform(auxiliary_features.edit), dtype=torch.float32)
    nzip_high, nzip_low = _pair_indices(
        nzip_train_frame, pairs_per_parent=pairs_per_group
    )
    aux_high, aux_low = _pair_indices(aux_frame, pairs_per_parent=pairs_per_group)
    pair_tensors = {
        "nzip": (
            torch.as_tensor(nzip_high, dtype=torch.long),
            torch.as_tensor(nzip_low, dtype=torch.long),
        ),
        "aux": (
            torch.as_tensor(aux_high, dtype=torch.long),
            torch.as_tensor(aux_low, dtype=torch.long),
        ),
    }
    feature_tensors = {
        "nzip": (nzip_parent, nzip_edit),
        "aux": (aux_parent, aux_edit),
    }
    model = MultiTaskFactorizedContextRanker(
        nzip_parent.shape[1], nzip_edit.shape[1], rank=rank, hidden=hidden
    )
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=learning_rate, weight_decay=weight_decay
    )
    generator = torch.Generator().manual_seed(SEED)
    batch_size = 2048
    for _ in range(epochs):
        orders = {
            task: torch.randperm(len(pair_tensors[task][0]), generator=generator)
            for task in ["nzip", "aux"]
        }
        batches = max(
            (len(order) + batch_size - 1) // batch_size for order in orders.values()
        )
        for batch_number in range(batches):
            losses = []
            for task in ["nzip", "aux"]:
                order = orders[task]
                first = (batch_number * batch_size) % len(order)
                selection = order[first : first + batch_size]
                if len(selection) == 0:
                    selection = order[:batch_size]
                high_all, low_all = pair_tensors[task]
                high, low = high_all[selection], low_all[selection]
                parent, edit = feature_tensors[task]
                high_score = model(parent[high], edit[high], task)
                low_score = model(parent[low], edit[low], task)
                losses.append(torch.nn.functional.softplus(-(high_score - low_score)).mean())
            loss = 0.5 * losses[0] + 0.5 * losses[1]
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
    model.eval()
    with torch.no_grad():
        parent_test = torch.tensor(
            p_scaler.transform(nzip_features.parent[test_indices]), dtype=torch.float32
        )
        edit_test = torch.tensor(
            e_scaler.transform(nzip_features.edit[test_indices]), dtype=torch.float32
        )
        return model(parent_test, edit_test, "nzip").numpy()
