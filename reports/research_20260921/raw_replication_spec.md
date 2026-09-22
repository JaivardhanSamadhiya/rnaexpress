# AI-authored raw-count reconstruction specification

Post-pilot consistency analysis; not independent biological confirmation.
The previously analyzed published table used these biological experiments.
Freeze this document and the counter before computing count/outcome associations.

Use only checksum-verified HRR3059160/61 (Cyto1/2) and HRR3059163/64 (Nuc1/2).
Process both mates, enforce matching read IDs and valid FASTQ lengths. Exact
10-base flanks in Gibson_6mer_Random_F orientation are ATCACTAAGC and ATCATAATCA;
the reverse orientation has TGATTATGAT and GCTTAGTGAT. These come from published
Supplementary Table S1. Require precisely six A/C/G/T bases between flanks and
Phred+33 quality >=20 at all six bases. Require a single eligible insert per mate;
if both mates yield an insert, their orientation-normalized sequences must agree.
Count each agreeing fragment once. Discard disagreements and report all QC.
Counts are PCR-amplified fragment counts, not unique RNA molecules or UMIs.

Store sequences in Gibson_6mer_Random_F orientation (the paper's named validation
inserts). The public Python script instead extracts the reverse-strand pattern
and does not reverse-complement it. Report association with the published table
in BOTH orientations, explicitly, without selecting orientation by performance.
The public script also assigns cyto CPM to nuc CPM in its NES calculation; this
does not by itself establish which code generated the published table.

Enumerate all 4096 six-mers including zeros. For each replicate compute
log2((nuc_count+0.5)/(sum_nuc+0.5*4096)) minus the corresponding cytoplasmic
quantity. Require >=20 accepted fragments in all four libraries for evaluation.
Report coverage, correlation between replicate NRS and with published scores,
including composition-centered correlations. Report the correlations of the
already fixed pilot predictions with each replicate under each orientation.
Do not fit new models or change the held-out set in this reconstruction step.
The primary diagnostic is whether the published sequence labels and ordering
can be reproduced. If not, stop promotion of the aggregate-table result and
retain discrepancies for investigation. Never select strand to make it positive.
