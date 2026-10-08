# Synthetic parameter-snapshot correction

The first17 synthetic tests passed, but the broader backend audit stopped before
its final receipt at a direct equality assertion over all native ordinary
parameter fields. Nine higher-dimensional fields are opaque SWIG pointers;
Python equality compared addresses rather than thermodynamic values. The first
attempt to serialize those opaque objects also failed before output creation.

The preserved diagnostic `parameter_snapshot_diagnostic_first.json` records this
audit implementation error. The corrected helper compares exactly21 directly
exposed scalar/list ordinary fields and explicitly reports nine opaque fields
as not compared by value. Their flag independence is established by the tagged
parameter-generation source, supplemented by native ordinary-structure energy
parity, rather than by unsafe pointer reinterpretation. An added synthetic test
guards this distinction. No thermodynamic setting, tolerance, hypothesis, event
formula or synthetic sequence roster changed. The initial17-test receipt remains
untouched; the separately named18-test receipt binds the corrected source.

This is a backend diagnostic, not a negative biological result. No project
allele, label, feature value, model or fit was involved.
