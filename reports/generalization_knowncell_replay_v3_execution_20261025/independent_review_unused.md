# Independent source review: preserve unused; do not execute

The 665 execution and 176 runtime pins rehash successfully. The separate
supplied-checkpoint replay, fixed source-only selections and journal binding
remain source preparations, with no actual admission or attempt birth.

Independent review identified two operational defects before use. The journal
validator checks pending_failure and exit-code types but does not independently
reject all adverse resource/counter samples or a contradictory earlier nonzero
exit followed by final zero. The live monitoring clock also starts after setup,
instead of receiving the parent's total-stage start; terminal validation would
reject a total overrun but cannot stop the child at the total deadline.

Keep this generation and its frozen manifests unchanged and UNUSED. A later
additive controller must validate all fixed resource predicates and exit
ordering and propagate the total-stage start into the live monitor, with
invented contradiction cases. The user needs existing browser tabs retained;
the separately frozen 4 GiB-startup FIT target has likewise never started.
No scientific settings, outcomes or tolerances were changed for this review.
