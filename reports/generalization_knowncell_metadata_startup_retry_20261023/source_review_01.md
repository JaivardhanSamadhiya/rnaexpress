# Frozen startup-addon source recheck

Result: no concrete source or byte-binding blocker identified for the declared
single pre-worker startup opportunity. This is an author recheck: the reviewing
agent also authored the addon. The file hashes and dependency inclusion were
recomputed in a separate standard-library-only inspection, but this is not an
independent-author review or independent execution of the controller.

The execution manifest has SHA
`325cdd1eb3f271e4fbda78f8ac370dae5f9e74f3a0c7be32615639ffafe9bc3a`.
All 88 current file hashes match. All 75 entries of the original V2 manifest
remain present with identical expected hashes. The V2 manifest itself remains
`dccab5219dcc6a82e015a31e248748cef160ee2e0408105ddfd8e2a0c86e35f7`,
and its original no-worker blocked receipt remains
`071e5c006c5af60b752e249964b766596f271fa9aa6e296dc101ad003d3ac89a`.
The three declared current-interpreter executable/DLL hashes also match; this
file does not certify a newly executed native runtime.

The five addon Python sources parse and exactly match the source hashes in the
13-test receipt
`ab5af25a04028379dfe6983a89b526c59b7ad97c0ac7f38f16a7696ff747f4db`.
There are exactly 13 defined test methods, and the preserved log records 13
passing invented tests. This review did not rerun them. The cases exercise the
original no-worker receipt contract, prior/partial-output rejection, exclusive
attempt consumption, explicit root start, low-memory rejection without a Job,
bounded resource sampling, a fresh post-Job floor, immutable initial manifest
identity, unchanged worker command and absence of module-global patching.

The resource function is an alias through V2 to the original
`generalization_knowncell_metadata_execution_20261023.common.resource_failure`.
Its physical floor is still 3 GiB, disk floor 1 GiB, system-commit reserve 1 GiB,
metadata-stage lifetime 300 seconds and active-process cap two. The separate
selective loader's original per-open resource gate remains unchanged. The addon
checks these resources before its sole spawn and reuses the original monitor
and final live-process-handle peak query. Its Job limit assertion remains
768 MiB per process and 896 MiB total. The optional explicit readiness wait is
separate, defaults to zero and requests at most 60 seconds of resource sampling;
it does not launch repeated workers. All four numerical thread variables are
still required to be one by the original admission.

The addon requires its manifest, the original V2 manifest and the first blocked
receipt to equal HEAD bytes. Captured initial SHA values remain expected values
through completion. It does not derive a replacement expected identity from
late bytes. The exact old V2 worker receives only its original manifest SHA and
uses the original absent cache prefix, bundle, log and completion paths. The
separate parent birth and supervisor receipts bind the addon and preserved
blocked-receipt identities. No original source, admission, resource callback or
module global is patched. An exclusive new birth consumes this opportunity,
including a subsequent resource block. Source, birth and result hashes precede
the final lifetime/resource check; partial outputs are preserved.

At this inspection the addon has no attempt birth or supervisor result. No
actual Job, worker, scientific import, metadata payload, numerical label,
feature array or model checkpoint was opened or executed by this review.
The tests are pre-worker controls, not proof of a successful native Job or
complete real metadata loading. A future successful worker still needs the
separate independent metadata reconstruction. This report adds no execution
authorization, lower-memory policy, biological admission or generalization
claim. It is a new review file outside the unchanged 88-pin input manifest.
