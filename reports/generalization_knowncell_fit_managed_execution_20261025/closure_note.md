# Reachability matters in a source-only import audit

An intentionally broad diagnostic followed every import inside every function
of every transitive production module, including historical profiling branches.
It visited 98 modules and found four source paths outside the new 587-pin
generation: old SpliceBERT resources and PRELib pipeline/contracts/package init.
No module or scientific package was executed by that diagnostic. Its assertion
failed; it is not reported as a successful full import-closure proof.

The relevant question is whether those old profiling branches are reachable
from the actual managed FIT call path. An independent source-only reachability
review was requested before any actual authorization/admission or job. The
generation's ordinary import preparation and fixed native/software admission
remain separate evidence. No missing source is silently ignored or patched
into frozen scientific code on the basis of this broad diagnostic alone.

Independent source review traced every reported edge. The four paths are
reached only through historical `launcher.run()` and the old/V2 PRELib profile
`invented.run()` entrypoints. Managed FIT instead follows its pinned provider
to `bootstrap_runtime`, `bootstrap.bootstrap`, `base_runtime.current_payload`
and the imported `current_numpy_payload()` helper. Those fixed functions never
invoke the three historical `run()` branches. The launcher helpers used for
import/native-origin checking do not invoke `launcher.run()` either.

Root repeated the AST walk excluding exactly those three reviewed dormant
function bodies; all resulting modules and regular package parents are pinned.
The original 98-module/four-gap diagnostic is retained in the same receipt,
not rewritten as successful. The reproducible review script is in the owned
artifacts directory and `root_source_closure.json` records both graphs and
remaining fixed-target dynamic imports. This proof applies only to the fixed
reviewed FIT entrypoints, not arbitrary calls into historical profiling code.
