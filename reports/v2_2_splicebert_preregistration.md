# RNAddress v2.2 SpliceBERT contextual-delta preregistration

Frozen on 2026-08-27 after the v2.1 stability ensemble failed and before embedding any RNAddress project sequence or fitting this candidate. TDP-43 locked outcomes and Astrocyte outcomes remain sealed.

## Evidence and rationale

The v2.1 experiment showed that the handcrafted nonconvex context ranker is seed-sensitive and that unweighted stabilization does not preserve inverse-design performance. The new candidate changes both representation and optimization rather than tuning that failed model.

SpliceBERT was pretrained by masked language modeling on more than two million primary RNA sequences from 72 vertebrates. Its released variable-length model covers 64-1024 nt sequences and supports contextual single-nucleotide variant analysis. Recent localization work also supports pretrained RNA language-model and RBP-aware representations when localization labels are limited. The selected checkpoint is the official multi-species `SpliceBERT.1024nt` release; exact source and runtime hashes are frozen in `data/frozen/splicebert_v2_2_source_manifest.json`.

## Frozen representation

- The pretrained checkpoint is evaluation-only: no fine-tuning, dropout, layer selection, or task-label update.
- Input uses the authors' tokenizer: uppercase DNA spelling with one whitespace-separated nucleotide per token, `[CLS]` and `[SEP]` added by the tokenizer.
- Use only the final pretrained `last_hidden_state`; the untrained BERT pooler is never used.
- For each parent/mutant pair, subtract the parent hidden state from the mutant hidden state at every aligned nucleotide.
- Concatenate four 512-dimensional summaries in this order: `[CLS]` difference; mean difference over all nucleotide positions; mean difference at changed positions; mean difference over the union of radius-10 windows around changed positions.
- Append the existing outcome-independent v2 edit vector. Do not append the parent vector or any identifier.
- Cache the resulting float32 feature matrix by exact source-row order and record its SHA-256. Embedding generation must not read outcomes beyond the already spent N-zip development labels.

## Frozen downstream model

- Strict leave-one-parent-out evaluation over all 15 N-zip parents.
- Within each training parent, convert measured delta localization to average percentile rank from 0 to 1. This gives every parent the same target scale.
- Fit `StandardScaler` on training rows only, followed by deterministic `sklearn.linear_model.Ridge` with intercept and `alpha = number of input features`.
- There is one candidate only: no layer, pool, regularization, feature, seed, or model selection.
- Convert no predictions during evaluation; raw ridge scores rank both increase and decrease recommendations.
- Shuffled-edit control permutes final candidate scores within each parent with seed `20260826`.
- Only if every primary criterion passes, repeat the entire downstream LOPO fit with outcomes permuted within parent using seed `20260826`. Pretrained features remain fixed and outcome-blind.

## Unchanged gate

Rank percentile must be at least 0.630; gain must be at least 0.030 over the strongest forward model and 0.020 over metadata; the candidate must improve on at least 9/15 parents and retain positive mean gain after removing its two best parents; shuffled edit must be at most 0.540; and the conditional shuffled-label model must be at most 0.530.

Only a complete pass authorizes freezing TDP-43 lock predictions, code, environment and hashes before opening its 1,006 outcomes. This is an adaptive fifth development-stage rescue after nested, structure, TDP-auxiliary and seed-ensemble failures and must be disclosed in any claim.
