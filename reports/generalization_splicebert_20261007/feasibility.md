# Single-base SpliceBERT route: prospective feasibility

Preparation only,7October2026. No encoder import, conversion, inference,
supervised fit, new model download, or old outcome-cache access occurred.
All files belong to a separate additive namespace.

The cached SpliceBERT.1024nt checkpoint and five configuration/tokenizer files
match the original archive linked by the [authors' repository](https://github.com/chenkenbio/SpliceBERT).
The public [Zenodo release7995778](https://zenodo.org/records/7995778) is CC BY4.0;
repository code is BSD3. The217,605,407-byte archive matches published MD5
`a51911d7d59fa6f0b07db4abaa820d84`, actual SHA256
`2d07fb041c3784a538559c368805ae84ca3daeb888772aa3bbe82f48dd576662`.
Checkpoint:78,883,755bytes, SHA256
`2ad91428c318e6c49233154073ca7a35f5f7899c9f4be3444775bae3dba0149d`.
Safe archive-member hashing established identity without pickle execution.

Local JSON confirms six Transformer layers,512hidden dimensions and a
single-base vocabulary with A/C/G/T plus N and special tokens. The
[primary study](https://pubmed.ncbi.nlm.nih.gov/38605640/) pretrained on primary
RNA from72vertebrates and demonstrated splicing-related transfer. This offers
a different corpus and tokenization hypothesis; localization-edit transfer is
unproven, and those two factors cannot be causally separated by one encoder
comparison. The author warns that lengths below64nt may fail. SRLE's certified
46nt local construction context is therefore outside the reported training
length range. No fabricated context or omission of SRLE is permitted.

No cached SpliceBERT OpenVINO XML or ONNX file was found; the only IR filename
in the searched data/interim and artifacts trees was the earlier3UTRBERT XML.
Old feature/outcome-cache contents were not opened. A fresh resource snapshot
at20:47:32UTC found1,333,346,304available RAM bytes(~1.24GiB), with~1385GiB free
on D:. Conversion is deferred. A conservative proposed startup guard is
at least3GiB free RAM and5GiB disk, checked freshly before model work; this is
a planning margin, not a measured converter requirement.

Official PyTorch CPU2.6.0 for CPython3.12/Windows is indexed publicly with SHA256
`4027d982eb2781c93825ab9527f17fbbb12dbabf422298e4b954be60016f87d8`.
[Official installation guidance](https://pytorch.org/get-started/previous-versions/)
provides that CPU release. The selected CDN's HEAD request returned403; GET
availability is untested. No runtime wheel was downloaded or installed. Future
preparation must verify the actual wheel, tagged license, dependencies and
extracted-file integrity. Any future checkpoint load must use explicit
restricted `weights_only=True`, the author-verified local file, and no remote
code. Torch/OpenVINO numerical equivalence must be established on synthetic
sequences before any full-core production.

The proposed feature block has256columns: last-layer mutant-minus-parent global
single-base mean and mean over exactly changed single-base tokens, each
projected512→128. Both exclude special/padding tokens. Two fixed Gaussian
matrices use seed20261007, global then local float64 draws/division bysqrt128,
followed by float32 storage. Exact arrays/hashes are saved. A single-base
one-hot control occupies the first4of512 dimensions with the same matrices and
pools; its rank is at most4per block, so it is not a full capacity match.
Three synthetic analytic tests passed for projection/pooling commutation,
no-edit/reversal, and exact lookup/boundary/special-token handling.

Full production requires a committed namespace-specific manifest, verified
runtime/model/tokenizer/conversion hashes, fresh resource admission and admitted
synthetic numerical/batching tests. Preserve the same26258original core IDs and
original allele/component purging. Use the same corrected available reporter
contexts and base246 control. Before fitting, commit separate feature/row hashes
and a fixed source-only whole-assay3L2 design; compare against base and matched
lookup and retain the strict gate. No fine tuning,PCA,target calibration,
outcome-selected layer/seed or protected outcome is admitted. No positive
generalization result is claimed at this preparation stage.

Receipts: `resource_audit.json`, `cpu_wheel_metadata.json`, `initial_headroom.json`,
and `feature_proposal.json`. Source: `resources.py`, `features.py`,
`test_features.py`. Large cached resources remain in their original locations;
only small metadata, license copies and projection arrays were added.
