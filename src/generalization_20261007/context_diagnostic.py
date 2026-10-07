"""Postfit descriptive context ambiguity diagnostic; no models or selection."""

from .common import *
from scipy.special import betainc
from scipy.stats import spearmanr, kendalltau
import itertools
import unittest

TOL = 1e-12
THRESHOLD = .9
CONTEXTS = [("mikl_gse173098", "cell_type", "CAD", "Neuro-2a"),
            ("moffatt_gse334718", "reporter", "GFP", "Firefly")]
MATCH_KEYS = ["parent_sequence", "mutant_sequence"]


def strict_matches(frame, domain_column, left, right):
    """Exclude ambiguous aliases rather than averaging distinct measurements."""
    frame = frame.copy()
    counts = frame.groupby([domain_column] + MATCH_KEYS)["intervention_id"].transform("size")
    unique = frame[counts.eq(1)]
    a, b = unique[unique[domain_column].eq(left)], unique[unique[domain_column].eq(right)]
    result = a.merge(b, on=MATCH_KEYS, suffixes=("_left", "_right"), validate="one_to_one")
    return result, {"input_rows": len(frame), "ambiguous_alias_rows_excluded": int(counts.gt(1).sum()),
                    "matched_edits": len(result), "left_unique_edits": len(a), "right_unique_edits": len(b)}


def support(differences):
    """Fixed weak symmetric Beta(.5,.5) directional support, not calibration."""
    d = np.asarray(differences, dtype=float)
    if d.ndim == 1:
        d = d[None, :]
    n = np.isfinite(d).sum(1)
    wins, losses = (d > TOL).sum(1), (d < -TOL).sum(1)
    ties = n - wins - losses
    tail = 1 - betainc(wins + .5 * ties + .5, losses + .5 * ties + .5, .5)
    signed = np.where((n >= 2) & (tail >= THRESHOLD), 1,
                      np.where((n >= 2) & (tail <= 1 - THRESHOLD), -1, 0))
    return n, tail, signed


def ordering_counts(a, b):
    """All exact-nontied pair agreement using tau-b and explicit tie counts."""
    a, b = np.asarray(a), np.asarray(b)
    total = len(a) * (len(a) - 1) // 2
    ties_a = sum(n * (n - 1) // 2 for n in pd.Series(a).value_counts())
    ties_b = sum(n * (n - 1) // 2 for n in pd.Series(b).value_counts())
    ties_both = sum(n * (n - 1) // 2 for n in pd.DataFrame({"a": a, "b": b}).value_counts())
    comparable = total - ties_a - ties_b + ties_both
    if not comparable:
        return total, comparable, 0, 0, np.nan
    tau = kendalltau(a, b).statistic
    net = int(round(tau * np.sqrt((total - ties_a) * (total - ties_b))))
    concordant = (comparable + net) // 2
    return total, comparable, concordant, comparable - concordant, tau


def run():
    manifest = freeze_check()
    from src.probabilistic_ranking_20260928.common import load as original_load
    frame, _, replicates, _ = original_load()
    assert len(frame) == 26258
    assert set(frame.dataset) == set(STUDIES)
    frame["diagnostic_row"] = np.arange(len(frame))
    candidates, parent_sets, pairs, inventories = [], [], [], []
    for study, domain_column, left_context, right_context in CONTEXTS:
        source = frame[frame.dataset.eq(study) & frame[domain_column].isin([left_context, right_context])].copy()
        matched, inventory = strict_matches(source, domain_column, left_context, right_context)
        inventory.update({"dataset": study, "left_context": left_context, "right_context": right_context})
        inventories.append(inventory)
        assert (matched.biological_component_left == matched.biological_component_right).all()
        matched = matched.sort_values(MATCH_KEYS).reset_index(drop=True)
        for parent, group in matched.groupby("parent_sequence", sort=True):
            group = group.reset_index(drop=True)
            a, b = group.measured_delta_left.to_numpy(float), group.measured_delta_right.to_numpy(float)
            li, ri = group.diagnostic_row_left.to_numpy(int), group.diagnostic_row_right.to_numpy(int)
            lr, rr = replicates[li], replicates[ri]
            nl, pl, sl = support(lr); nr, pr, sr = support(rr)
            both_signs = (np.abs(a) > TOL) & (np.abs(b) > TOL)
            both_supported = (sl != 0) & (sr != 0)
            component = group.biological_component_left.iloc[0]
            genes = sorted(set(group.gene_transcript_left) | set(group.gene_transcript_right))
            gene = "|".join(genes)
            parent_hash = hashlib.sha256(parent.encode()).hexdigest()[:20]
            for j, row in enumerate(group.itertuples()):
                candidates.append({"dataset": study, "biological_component": component, "gene_transcript": gene,
                    "parent_sequence_sha256_prefix": parent_hash, "left_context": left_context, "right_context": right_context,
                    "left_id": row.intervention_id_left, "right_id": row.intervention_id_right,
                    "left_effect": a[j], "right_effect": b[j], "aggregate_both_nonneutral": bool(both_signs[j]),
                    "aggregate_opposing_effect_sign": bool(both_signs[j] and np.sign(a[j]) != np.sign(b[j])),
                    "left_finite_replicate_slots": nl[j], "right_finite_replicate_slots": nr[j],
                    "left_direction_support": pl[j], "right_direction_support": pr[j],
                    "both_direction_supported": bool(both_supported[j]),
                    "replicate_supported_opposing_effect_sign": bool(both_supported[j] and sl[j] != sr[j])})
            total, comparable, concordant, discordant, tau = ordering_counts(a, b)
            pair_supported_count = pair_opposing_count = pair_evidence_count = 0
            # Moffatt has no admitted paired contrasts. Do not construct pseudo
            # replicates or regard its aggregate disagreement as reproducible.
            if np.isfinite(lr).any() and np.isfinite(rr).any():
                indexes = list(itertools.combinations(range(len(group)), 2))
                if indexes:
                    ia, ib = np.asarray(indexes).T
                    dl, dr = lr[ia] - lr[ib], rr[ia] - rr[ib]
                    pn_l, pp_l, ps_l = support(dl); pn_r, pp_r, ps_r = support(dr)
                    available = (pn_l >= 2) & (pn_r >= 2)
                    supported = (ps_l != 0) & (ps_r != 0)
                    opposing = supported & (ps_l != ps_r)
                    pair_evidence_count, pair_supported_count, pair_opposing_count = int(available.sum()), int(supported.sum()), int(opposing.sum())
                    for j, (i, k) in enumerate(indexes):
                        pairs.append({"dataset": study, "biological_component": component, "gene_transcript": gene,
                            "parent_sequence_sha256_prefix": parent_hash, "left_context": left_context, "right_context": right_context,
                            "candidate_a_left_id": group.intervention_id_left.iloc[i], "candidate_b_left_id": group.intervention_id_left.iloc[k],
                            "candidate_a_right_id": group.intervention_id_right.iloc[i], "candidate_b_right_id": group.intervention_id_right.iloc[k],
                            "left_finite_paired_slots": pn_l[j], "right_finite_paired_slots": pn_r[j],
                            "left_preference_support": pp_l[j], "right_preference_support": pp_r[j],
                            "available_2plus_in_both": bool(available[j]), "both_preferences_supported": bool(supported[j]),
                            "replicate_supported_opposing_preferences": bool(opposing[j])})
            parent_sets.append({"dataset": study, "biological_component": component, "gene_transcript": gene,
                "parent_sequence_sha256_prefix": parent_hash, "matched_candidates": len(group),
                "aggregate_nonneutral_candidates": int(both_signs.sum()),
                "aggregate_effect_sign_concordance": float((np.sign(a[both_signs]) == np.sign(b[both_signs])).mean()) if both_signs.any() else np.nan,
                "effect_spearman": float(spearmanr(a, b).statistic) if len(group) >= 2 and np.ptp(a) > 0 and np.ptp(b) > 0 else np.nan,
                "all_pairs": total, "aggregate_comparable_pairs": comparable, "aggregate_concordant_pairs": concordant,
                "aggregate_discordant_pairs": discordant, "pair_order_concordance": concordant / comparable if comparable else np.nan,
                "kendall_tau_b": tau, "both_effect_directions_supported": int(both_supported.sum()),
                "supported_opposing_effect_directions": int((both_supported & (sl != sr)).sum()),
                "supported_opposing_effect_fraction": float((sl[both_supported] != sr[both_supported]).mean()) if both_supported.any() else np.nan,
                "pair_evidence_2plus_both": pair_evidence_count, "both_pair_preferences_supported": pair_supported_count,
                "supported_opposing_pair_preferences": pair_opposing_count,
                "supported_opposing_pair_fraction": pair_opposing_count / pair_supported_count if pair_supported_count else np.nan})
    candidate_frame, parent_frame, pair_frame = pd.DataFrame(candidates), pd.DataFrame(parent_sets), pd.DataFrame(pairs)
    metrics = ["aggregate_effect_sign_concordance", "effect_spearman", "pair_order_concordance", "kendall_tau_b",
               "supported_opposing_effect_fraction", "supported_opposing_pair_fraction"]
    genes = parent_frame.groupby(["dataset", "gene_transcript"])[metrics].mean().reset_index()
    components = parent_frame.groupby(["dataset", "biological_component"])[metrics].mean().reset_index()
    study_rows = []
    for study, group in parent_frame.groupby("dataset"):
        counts = group[["matched_candidates", "aggregate_comparable_pairs", "aggregate_discordant_pairs",
                        "both_effect_directions_supported", "supported_opposing_effect_directions",
                        "pair_evidence_2plus_both", "both_pair_preferences_supported", "supported_opposing_pair_preferences"]].sum().to_dict()
        study_genes, study_components = genes[genes.dataset.eq(study)], components[components.dataset.eq(study)]
        study_rows.append({"dataset": study, "matched_parent_sets": len(group), "genes": len(study_genes),
            "components": len(study_components), **counts,
            **{"gene_macro_" + key: study_genes[key].mean() for key in metrics},
            **{"component_macro_" + key: study_components[key].mean() for key in metrics}})
    summary_frame = pd.DataFrame(study_rows)
    csvsave(OUT / "context_diagnostic_candidates.csv.gz", candidate_frame, True)
    csvsave(OUT / "context_diagnostic_parent_sets.csv", parent_frame)
    csvsave(OUT / "context_diagnostic_pair_evidence.csv.gz", pair_frame, True)
    csvsave(OUT / "context_diagnostic_gene_macro.csv", genes)
    csvsave(OUT / "context_diagnostic_component_macro.csv", components)
    csvsave(OUT / "context_diagnostic_summary.csv", summary_frame)
    tests = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContextDiagnosticTests))
    assert tests.wasSuccessful()
    sources = [ROOT / "results/probabilistic_ranking_20260928/candidate_index.csv",
               ROOT / "artifacts/probabilistic_ranking_20260928/data.npz"]
    receipt = {"status": "PASS", "role": "POSTFIT_DESCRIPTIVE_DIAGNOSTIC_NOT_MODEL_SELECTION",
        "source_sha256": {path.relative_to(ROOT).as_posix(): sha256(path) for path in sources},
        "code_sha256": sha256(SRC / "context_diagnostic.py"), "inventory": inventories,
        "matched_candidate_rows": len(candidate_frame), "matched_parent_sets": len(parent_frame), "pair_evidence_rows": len(pair_frame),
        "support_rule": "at least two finite within-context contrast slots; Beta(.5,.5) posterior tail >=.9 or <=.1; ties tolerance1e-12 receive half credit",
        "replicate_pairing": "candidateA-minus-candidateB in corresponding recorded within-context slots only; CAD and Neuro2a slots are not paired to each other",
        "missing_replicates": "Moffatt has no admitted paired contrast records; reproducibility unavailable",
        "summary_denominators": "support fractions conditional on both contexts meeting support; gene/component macros average parent-set fractions, omitting unavailable values",
        "tests_passed": tests.testsRun, "models_fit": 0, "prefit_files_unchanged": len(freeze_check()["files"]),
        "independence_claim": False, "prospective_confirmation": False, "reserved_outcomes_opened": False}
    jsave(OUT / "context_diagnostic_receipt.json", receipt)
    lines = ["# Exact-sequence context diagnostic", "", "This is a postfit descriptive diagnostic, separate from model selection and the generalization gate.", "",
        "Exact parent+mutant sequence pairs were matched between CAD/Neuro-2a in Mikl and GFP/Firefly in Moffatt. Ambiguous duplicate aliases were excluded without averaging. Parent sets use only candidates observed uniquely in both contexts. Candidate effect sign concordance and exhaustive aggregate pair ordering compare recorded contrasts; ranks are therefore assessed on the same candidate set.", "",
        "Directional support uses at least two finite recorded within-context slots and a fixed Beta(.5,.5) tail rule of .9/.1. Within-cell pair preferences subtract candidate contrasts in corresponding slots. Cross-cell slots are never assumed paired. These support values are working binomial summaries, not calibrated biological probabilities or proof that replicate slots are independent. Shared WT measurements and correlations among mutants also prevent treating all pairs as independent observations. Moffatt reproducibility is unavailable because its admitted paired contrast matrix is missing.", "",
        "| Study | Matched edits | Parent sets | Genes | Gene-macro effect sign agreement | Gene-macro pair-order agreement | Supported opposing effects | Supported opposing preferences |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary_frame.itertuples():
        lines.append(f"| {row.dataset} | {int(row.matched_candidates)} | {row.matched_parent_sets} | {row.genes} | {row.gene_macro_aggregate_effect_sign_concordance:.4f} | {row.gene_macro_pair_order_concordance:.4f} | {int(row.supported_opposing_effect_directions)} / {int(row.both_effect_directions_supported)} | {int(row.supported_opposing_pair_preferences)} / {int(row.both_pair_preferences_supported)} |")
    lines += ["", "Supported opposing directions/preferences are conditional counts, with overlapping candidates and pairs. Full counts, denominators, and gene/component summaries accompany this report. They cannot distinguish causal context dependence from systematic measurement/context artifacts without independent reconstruction or confirmation.", "",
        "A reproducible opposing preference for the same two edits supplies an input ambiguity for an unconditioned deterministic sequence-only model: it cannot give both contexts opposite orderings. Conversely, weak aggregate agreement alone does not establish a biological context effect because sampling noise may generate disagreement. Endpoint conditioning separates nuclear retention from projection enrichment but does not separate CAD from Neuro-2a or GFP from Firefly; this diagnostic addresses that remaining gap.", "",
        "Matched sequences are already exposed development observations. Any later cross-cell generalization experiment must exclude the matched gene/parent and all exact alleles from every training source. No model was fitted, no new source was discovered, no reserved outcome was opened, and no frozen input was changed.", "",
        f"Verification: {tests.testsRun} synthetic tests passed; all {len(manifest['files'])} prefit files remain unchanged. Source and code hashes are in context_diagnostic_receipt.json.", ""]
    save(REP / "context_diagnostic.md", "\n".join(lines).encode())
    print(summary_frame.to_string(index=False), flush=True)
    print("Context diagnostic PASS", flush=True)


class ContextDiagnosticTests(unittest.TestCase):
    def test_unique_exact_matching_excludes_aliases(self):
        frame = pd.DataFrame({"intervention_id": ["a", "alias", "b", "c", "d"], "cell": ["L", "L", "R", "L", "R"],
            "parent_sequence": ["AAAA"] * 5, "mutant_sequence": ["AAAC", "AAAC", "AAAC", "AAAG", "AAAG"]})
        matches, inventory = strict_matches(frame, "cell", "L", "R")
        self.assertEqual(inventory["ambiguous_alias_rows_excluded"], 2)
        self.assertEqual(matches.mutant_sequence.tolist(), ["AAAG"])

    def test_fixed_support_and_all_pair_counts(self):
        n, tail, sign = support([[1., 2., 3.], [-1., -2., -3.], [1., -1., np.nan], [1., np.nan, np.nan]])
        np.testing.assert_array_equal(n, [3, 3, 2, 1])
        np.testing.assert_array_equal(sign, [1, -1, 0, 0])
        self.assertGreater(tail[0], .9)
        self.assertLess(tail[1], .1)
        total, comparable, agreeing, disagreeing, tau = ordering_counts([0., 1., 1., 2.], [2., 1., 1., 0.])
        self.assertEqual((total, comparable, agreeing, disagreeing), (6, 5, 0, 5))
        self.assertEqual(tau, -1.)


if __name__ == "__main__":
    run()
