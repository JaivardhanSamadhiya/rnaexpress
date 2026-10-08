# Masked allele-likelihood: outcome-free feasibility preparation

Declared 7 October 2026 before any new numeric/model import, checkpoint load,
synthetic native probe or project inference. This namespace initially authorizes
only standard-library/mock arithmetic and existing metadata/source inspection.
It contains no biological loader, feature production, fit, selector or gate.
All previous sources, tests, manifests, candidate IR and results stay immutable.
No download, installation, payment, account, author contact or scheduled task.

The [official SpliceBERT author repository](https://github.com/chenkenbio/SpliceBERT)
demonstrates AutoModelForMaskedLM and nucleotide logits. Its vocabulary is
PAD0/UNK1/CLS2/SEP3/MASK4/N5/A6/C7/G8/T9. Its demo is an unmasked input; that does
not validate using an observed nucleotide's self-reconstruction as masked edit
evidence. The cached author-certified 78,883,755-byte SpliceBERT.1024nt checkpoint
has SHA256 2ad91428c318e6c49233154073ca7a35f5f7899c9f4be3444775bae3dba0149d.
No checkpoint is opened/deserialized during this preparation. BSD3 code and
CC-BY4 author release provenance are inherited by reference from the pinned
resource receipt; no new model is acquired or redistributed.

For an equal-length parent/mutant with 1–6 substituted nucleotide sites, mask
the union of ALL changed positions. The resulting token sequence must be
identical for both alleles. Run that shared context once, with CLS offset+1 and
SEP retained; evaluate each changed position's alternate/reference logits from
that one output. S=sum_i(logit_alt,i-logit_ref,i). Record every reference and
alternate log probability, per-edit ratio and sum. Stable log-softmax normalizes
the same ten-token vocabulary in both conditions; its denominator cancels.
The direct difference is retained to avoid subtraction of large normalizers.
No special/N/padding token can be an allele; no sequence or label identity is
passed to the predictor outside these token IDs/masks/type IDs. No-edit returns
exact zero without a model call; allele reversal shares the same masked context
and negates the score. Unknown/indel/>6-edit inputs fail, not silently remap.

This is a **block-masked conditional marginal surrogate**: each site's marginal
is conditional on the unedited context and other changed sites being masked.
The sum is NOT a jointly normalized multivariant likelihood, full pseudolikelihood,
single-site reference-conditioned score, evolutionary fitness probability,
localization probability, export probability or direction of a measured effect.
It discards interchanged-site conditional dependencies; different masking/context
recipes would be different hypotheses and cannot be chosen after outcomes.
Observed sequence corpora may overlap pretraining; masking is not independent
biological confirmation or absence of sequence homology/leakage.

Preserve exactly the earlier 16 invented parent/mutant inputs at46/150/190/260nt,
using the original hash recipe and certified20+6+20 junction only as a fixed
synthetic construction. The original eight one-site pairs supply eight shared
masked requests. An ADDITIONAL fixed twenty requests exercise2–6 edits at each
length, including first/last nucleotide boundaries, without replacing original
inputs. Group exact lengths, run batch2, duplicate the real tail context if odd
and discard its output. Add no fake nucleotide padding or invented mature flank.
Author training lengths are64–1024nt; 46nt remains explicitly out of domain.

## Minimal prospective native backend, not implemented/executed here

Reuse the accepted encoder IR rather than create another encoder/MLM conversion.
The candidate backend is that FP32 encoder followed by its original dense512×512,
exact GELU, LayerNorm epsilon1e-12 and decoder10×512 plus output bias, implemented
independently in NumPy using the original head tensors. A single local stock
BertForMaskedLM is the synthetic reference, restricted-loaded from the SAME
author checkpoint. This costs no new model download or parallel conversion.
No finetuning, arbitrary head, random initialized head, temperature or calibration.

Actual head availability and alias equality are **unverified at preparation**.
Before a stock load can overwrite tied aliases, verify the exact seven cls keys,
shapes, FP32 finite tensors, decoder-weight equality to input embeddings and
decoder-bias equality to cls.predictions.bias, using actual tensor bytes and
torch.equal. Config specifies BertForMaskedLM, six layers/hidden512/vocab10,
GELU, absolute positions and epsilon1e-12; its omitted tie_word_embeddings uses
the inspected stock True default. Verify model decoder/input parameter identity
and all post-load parameters equal the restricted checkpoint. Remove ONLY old
position/token-type buffers after exact canonical-value checks, as the original
probe does. Strict missing/unexpected keys, tied inequality or wrong shape stops
the probe; never ignore head keys, unpickle unsafely or fall back to remote code.

Stock head order is dense→exact GELU→LayerNorm(population variance)→decoder+bias.
NumPy uses the same orientation, epsilon, dtype and authoritative independent
head bytes. Compare stock logits, an independent head on stock encoder outputs,
and the independent head on existing IR outputs, on every declared masked input
and every token (including specials). Retain original parity thresholds unchanged:
max absolute difference<=.001, mean<=.0001, minimum token cosine>=.999999.
Also compare all per-edit/summed scores and exact no-edit/reversal identities;
record numerical bounds rather than infer identity from cosine alone. If logits
have zero norm, require exact both-zero equality and define cosine1 only there.
Failure preserves a new incident and blocks admission; no automatic alternate
model/conversion/relaxed tolerance. Native-only production would require a new
root-reviewed declaration, not be selected by target performance.

Before any actual model import, root must review and commit this preparation
and separately authorize a synthetic probe. A later new probe guard must require
original16-synthetic encoder PASS AND additive runtime-repair PASS; rehash the
complete frozen chains, actual checkpoint/config/vocab, encoder XML/BIN and
runtime bytes. Fresh process and fresh >=3GiB free RAM/>=5GiB disk are required
before imports and after verification; preserve original2 numerical threads.
Select the exact CP312 NumPy1.26.4 prefix before Torch, prove actual NumPy module,
native-core/BLAS DLL paths/SHAs using the repaired origin helper, and save a NEW
origin receipt. Check actual Torch CPU/Transformers/OpenVINO origins and bytes
against their completed chain; old receipt hashes alone do not certify the
current process. Do NOT re-run the old pre-conversion guard, which correctly
rejects the now-existing IR. Require existing accepted IR hashes; do not write
it or monkeypatch its old source. No model call is authorized by metadata PASS.

## Prior art, history and missing evidence

A bounded src/reports text search found old SpliceBERT/3UTRBERT wrappers using
AutoModelForMaskedLM merely to access model.bert hidden states; those functions
do not mask changed sites or evaluate MLM logits. That is not an exhaustive
history proof. The new 2026 encoder deliberately omits cls.* and cannot alone
emit masked nucleotide logits. This preparation tests that missing head path,
not a novel masked-language-model method or biological finding.

[Tomaz da Silva et al.2025](https://www.nature.com/articles/s41588-025-02347-3)
analyzes nucleotide dependencies and reconstruction likelihood ratios, including
SpliceBERT splice dependencies; these are prior art, not a localization claim.
Its [primary indexed abstract/figure descriptions](https://pubmed.ncbi.nlm.nih.gov/41073788/)
distinguish effects on other positions from same-site reconstruction. Our fixed
masked-allele surrogate does not reproduce their full dependency analysis.
Publisher/PMC full text was inaccessible during this review; no bypass attempted.
No novel generalization method or STS outcome is claimed.

Current missing evidence: actual restricted head/tie certificate; unchanged
native-vs-head-vs-IR logit/score parity; actual current-process runtime origin;
synthetic benchmark/resource receipt. Even a successful backend probe would
authorize neither project inference nor biological feature/gate design. Such
production, row identity, controls, purges and source-only selection require a
separate future review/freeze; no new outcome or held-source selection here.
