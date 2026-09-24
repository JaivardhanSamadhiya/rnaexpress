# DNA barcode and alignment feasibility criteria

AI-authored, fixed before execution in commit 3ff287f. Split from the DNA download
specification afterward to preserve the original download-receipt hash.

The initial feasibility calculation uses exact matches to the two published
20-nt barcode flanks, a 17–23-nt barcode with every base at Q10 or higher, and a
single unambiguous occurrence in either read orientation. Inventory all verified
DNA reads, but attempt full construct classification only on the first 5,000
FASTQ records. This is a fixed scope, not the first 5,000 successful records.

Locate each of eight fragment regions with position-specific 15-mers, requiring
at least eight matches; pad the anchored region by 50 nt on each side and reject
windows over 1,200 nt. Align all four existing publisher fragment alternatives
with local alignment (match +2, mismatch -3, gap open -5, extension -1). Accept
the highest score only if its margin is at least 20, at least 95% of its reference
is aligned, score per reference base is at least 1.3, and fragment intervals are
ordered with no overlap greater than 20 nt. Reject if any of eight positions
fails. These conservative feasibility thresholds are not estimates of mapping
accuracy. Report all rejection categories. Reference recovery tests are software
checks, not independent real-read validation.

Biopython 1.88 is installed from a SHA-256-verified PyPI Windows wheel in a new
isolated research runtime. Its license is Biopython's open-source license; no
paid service is used. Existing frozen analysis runtimes remain unchanged.
