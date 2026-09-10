# RBP model compatibility checkpoint

Reviewed 9 September 2026 (retrieval receipts use UTC). No RNAddress outcomes
were used to choose a checkpoint. Parnet is documented separately.

## BRIDGE: fresh official-resource check

The [official repository](https://github.com/wangyb97/BRIDGE) remains at
`b5d886557e58f896c975ab290ad77a38df629658`. The freshly retrieved
[author-hosted Figshare inventory](https://doi.org/10.6084/m9.figshare.29819843)
is version 6. It provides a 18,449,357,955-byte model archive, a 72,173,369-byte
RBPformer archive, data and motif priors, with published checksums. These are
available resources, not missing weights. The model archive itself has not been
downloaded or admitted. The repository is MIT-licensed.

Source inspection establishes a more consequential compatibility issue. In
`main.py`, training consumes transformer embeddings/attention, one-channel
structure reactivity, motif priors and biochemical features. In
`variant_aware.py`, the GWAS scoring route explicitly supplies zero attention,
zero structure and zero motif tensors. The network's forward pass actively uses
these branches. The 101-nt position convention also differs from the native
RNAddress reporter lengths.

Some inputs can be generated from sequence, but predicted equilibrium pairing
is not interchangeable with a measured icSHAPE-reactivity channel. The official
zero-input variant route is executable in principle; that alone does not validate
its mutation-sensitive output for this task. BRIDGE is **not currently admitted**
as a validated full mechanism predictor. This is not an assertion that BRIDGE
is generally unusable, nor that all its modalities require unavailable data.
Admission would require a justified missing-modality protocol and independent
validation, or compatible measurements. Human-to-mouse inference would need an
additional explicit qualification. No unsupported RBP channels have been filled
with zeros and presented as predictions.

## Independently pretrained fallback

The hash-verified original RBPNet reconstruction remains available: 103 human
HepG2 checkpoints, with no TARDBP channel. Mechanism-v2 extracts only four signed
paired summaries per checkpoint (412 columns), excluding absolute parent
summaries and edit geometry. It also retains a separately identified 128-column
3UTRBERT contextual-delta comparator. Neither is called paper-matching Parnet
or BRIDGE. Their incremental value and necessity have not yet been evaluated in
the new localization experiment.

Fresh metadata receipts and content hashes are under the new resource-audit
namespace; original FinalShot code and reports remain unmodified.
