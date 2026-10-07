"""Separate common-shape/sequence-tie diagnostic; never change original gates."""
from .common import *
from .evaluate import features, source_model
from src.generalization_crosscell_20261007.routes import module
from src.generalization_crosscell_20261007.bootstrap import shared_bootstrap
from src.generalization_rbp_20261007.canonical_inner_replay import canonical_scores
import os


def shared_matrix(frame, matrix, pairs, fold):
    """Full exact menus; certify allele feature bytes before common-shape scoring."""
    assert matrix.shape[0] == len(frame) and frame.index.equals(pd.RangeIndex(len(frame)))
    rows, positions = [], []
    for pair in pairs[pairs.gene_fold.eq(fold)].itertuples():
        a = frame[frame.parent_context_id.eq(pair.CAD_context)]
        b = frame[frame.parent_context_id.eq(pair.N2A_context)]
        assert len(a) == len(b) == pair.candidates and a.mutant_sequence.is_unique and b.mutant_sequence.is_unique
        assert a.parent_sequence.nunique() == b.parent_sequence.nunique() == 1
        assert a.parent_sequence.iloc[0] == b.parent_sequence.iloc[0]
        assert set(a.biological_component) == set(b.biological_component) == {pair.biological_component}
        assert set(a.held_parent_fold) == set(b.held_parent_fold) == {fold}
        assert set(a.cell_type) == {"CAD"} and set(b.cell_type) == {"Neuro-2a"}
        a, b = [group.sort_values("mutant_sequence", kind="stable") for group in (a, b)]
        assert list(a.mutant_sequence) == list(b.mutant_sequence), "No allele intersection trimming"
        ax, bx = [np.ascontiguousarray(matrix[group.index], dtype=np.float64) for group in (a, b)]
        assert ax.tobytes() == bx.tobytes(), "Paired allele feature-byte inequality blocks canonical diagnostic"
        positions.extend(a.index)
        for ar, br in zip(a.itertuples(), b.itertuples()):
            rows.append({"biological_component": pair.biological_component, "gene_fold": fold,
                "pair_context": pair.CAD_context, "CAD_context": pair.CAD_context, "N2A_context": pair.N2A_context,
                "mutant_sequence": ar.mutant_sequence, "CAD_id": ar.intervention_id, "N2A_id": br.intervention_id,
                "CAD_effect": float(ar.measured_delta), "N2A_effect": float(br.measured_delta)})
    assert rows and len(positions) == len(set(positions))
    return pd.DataFrame(rows), np.asarray(matrix[positions], dtype=np.float64)


def common_choices(rows, scores, task):
    """One selected allele per direction, evaluated in both original truth menus."""
    scores = np.asarray(scores, dtype=float)
    assert scores.shape == (len(rows),) and np.isfinite(scores).all()
    known, crossed = ("CAD", "N2A") if TASKS[task][0] == "CAD" else ("N2A", "CAD")
    records = []
    for context, group in rows.assign(_score=scores).groupby("pair_context", sort=True):
        group = group.sort_values("mutant_sequence", kind="stable")
        assert group.mutant_sequence.is_unique and len(group) >= 2
        values = {cell: group[cell + "_effect"].to_numpy(float) for cell in ("CAD", "N2A")}
        assert all(np.isfinite(v).all() and float(np.ptp(v)) > 0 for v in values.values())
        for direction in (-1, 1):
            index = int(np.argmax(direction * group._score.to_numpy(float)))
            selected = group.iloc[index]
            regrets = {cell: float((np.max(direction * v) - direction * v[index]) / np.ptp(v)) for cell, v in values.items()}
            records.append({"task": task, "biological_component": selected.biological_component,
                "gene_fold": int(selected.gene_fold), "pair_context": context, "direction": direction,
                "selected_mutant_sequence": selected.mutant_sequence, "CAD_selected_id": selected.CAD_id,
                "N2A_selected_id": selected.N2A_id, "common_score": float(selected._score),
                "CAD_selected_effect": float(values["CAD"][index]), "N2A_selected_effect": float(values["N2A"][index]),
                "CAD_regret": regrets["CAD"], "N2A_regret": regrets["N2A"],
                "known_regret": regrets[known], "crossed_regret": regrets[crossed],
                "known_advantage": regrets[crossed] - regrets[known]})
    return pd.DataFrame(records)


def run():
    freeze_check()
    assert all(os.environ.get(v) == "1" for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"))
    checked = readj(OUT / "verification_receipt.json"); assert checked["status"] == "PASS"
    assert checked["same_checkpoint_both_states_verified"] and checked["crossed_state_predictors_rechecked"] == 42
    assert checked["evaluation_manifest_sha256"] == sha256(OUT / "evaluation_manifest.json")
    for name, digest in checked["result_files"].items(): assert sha256(ROOT / name) == digest
    frame, pairs = load(True), pd.read_csv(OUT / "exact_menu_pairs.csv")
    assert len(pairs) == 2408 and pairs.biological_component.nunique() == 187
    summary, maximum, calls = [], 0., 0
    for track in TRACKS:
        x, pieces, roster = features(track), [], []
        for fold in FOLDS:
            rows, shared = shared_matrix(frame, x, pairs, fold)
            for task in TASKS:
                model, config, _, path = source_model(track, task, fold, frame, x)
                # Exactly one predictor call on the shared ordered matrix for
                # both contexts. Independent arithmetic may block rows only.
                score, error = canonical_scores(model, shared, np.arange(len(shared)), module(track).predict_model)
                maximum = max(maximum, error); calls += 1
                pieces.append(common_choices(rows, score, task))
                roster.append({"task": task, "fold": fold, "configuration": config,
                    "source_checkpoint": path.relative_to(ROOT).as_posix(), "checkpoint_sha256": sha256(path),
                    "ordered_pair_metadata_sha256": hashlib.sha256(rows.to_csv(index=False, lineterminator="\n").encode()).hexdigest(),
                    "common_matrix_sha256": hashlib.sha256(np.ascontiguousarray(shared).tobytes()).hexdigest(),
                    "paired_feature_bytes_equal": True, "predictor_calls": 1, "rows": len(rows)})
        data = pd.concat(pieces, ignore_index=True)
        assert len(data) == 2408 * 2 * 2 and not data.duplicated(["task", "pair_context", "direction"]).any()
        gains = {task: data[data.task.eq(task)].groupby("biological_component").known_advantage.mean() for task in TASKS}
        assert all(len(v) == 187 for v in gains.values())
        interval = shared_bootstrap(gains, 5000, SEED)
        summary.append({"track": track, "mean_known_advantage": float(np.mean([v.mean() for v in gains.values()])),
            "per_known_cell": {task: float(v.mean()) for task, v in gains.items()},
            "descriptive_ci": [float(np.quantile(interval, .025)), float(np.quantile(interval, .975))],
            "components": 187, "menus": 2408})
        csvsave(OUT / track / "canonical_paired_state_contrast.csv", data)
        jsave(OUT / track / "canonical_paired_state_roster.json", roster)
        del x
    assert calls == 42
    jsave(OUT / "canonical_paired_state_contrast.json", {"status": "DESCRIPTIVE", "tracks": summary,
        "predictor_calls": calls, "maximum_independent_score_error": maximum, "new_fits": 0,
        "all_paired_feature_bytes_equal": True, "tie_policy": "exact score tie, shared lexical mutant sequence",
        "shape_policy": "one identical ordered candidate matrix per source checkpoint/fold",
        "main_gate_and_original_id_policy_unchanged": True, "selects_nothing": True,
        "causal_cell_state_claim": False, "biological_confirmation": False,
        "evaluation_manifest_sha256": sha256(OUT / "evaluation_manifest.json")})


if __name__ == "__main__": run()
