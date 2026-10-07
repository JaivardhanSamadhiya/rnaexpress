# Independent replay supplement

This additive diagnostic does not modify the production-frozen experiment,
perform fits, admit datasets, tune models, or change a scientific gate. Run
only after all tracks in the selected namespace have completed. Inputs are
the already exposed four-study frame, committed feature matrices, immutable
checkpoints, saved inner-selection table, and outer fold selections.

For each outer source roster, independently exclude every component touching
the held study and assert original parent/mutant allele disjointness. Repeat
within each of the three training-assay holdouts. Reconstruct ordered training
and validation identifiers; verify saved configuration, studies, components,
and row counts. Use saved mean, scale and coefficients to compute validation
scores in batches of 1,024 rows, retaining only one track matrix. Check both an
explicit coefficient sum and affine reparameterization against the frozen
prediction API within absolute 1e-9. Retain the original dot-product arithmetic
for exact lexical score-tie handling.

Independently reconstruct both directions' extreme choices and normalized
regrets, equal-average directions within context, contexts within component,
components within study, and studies. Require saved inner regrets and all
three configuration means within absolute 1e-12. Verify the exact first-in-grid
configuration within 1e-12 of the minimum, and the selected outer checkpoint's
training roster. This checks 108 inner checkpoints/12 choices for RBP and 216/24
for the next-generation experiment. It complements the existing outer replay.

The receipt records every checkpoint, matrix and selection-table hash,
validation-roster/choice digests, arithmetic differences, selected penalty,
prefit manifest hash, and whether the helper itself was pinned in that
manifest. A helper added after an experiment freeze remains an explicitly
post-freeze verification supplement; it is never presented as pre-registered
scientific analysis. Existing receipt files are preserved, and discrepancies
stop the diagnostic rather than silently updating selections or tolerances.

Outcome-free tests cover analytic score calculations, unequal numbers of
contexts and candidates, lexical ties, direction changes, row permutations,
malformed component closure, fixed selection tolerance, training-ID reorder,
configuration corruption, and held-source contamination.

Scoped tests:
`python -u -m unittest src.generalization_rbp_20261007.test_inner_replay`

After completion:
`python -u -m src.generalization_rbp_20261007.inner_replay rbp`
or
`python -u -m src.generalization_rbp_20261007.inner_replay next`.
