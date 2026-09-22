# AI-assisted literature and claim audit — 21 September 2026

This is a technical assistance record. The student must read the papers, decide
the scientific question, and independently interpret and write submitted work.
Targeted searches cannot establish that a claim is completely novel.

| Primary source | Prior contribution relevant here | Consequence for this project |
| --- | --- | --- |
| [Zeng et al., SRLE-seq, 2026](https://pubmed.ncbi.nlm.nih.gov/42179915/) | Exhaustive six-mer localization screen, experimental motif validation, and incorporation of NRS into localization prediction. | Neither discovering localization six-mers nor using their scores in a predictor is new. A reanalysis needs a distinct question and stronger evidence. |
| [Arora et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9561290/) | Tiled neuronal MPRA across reporters/cell contexts and sequence determinants of neurite localization. | Generic short-motif localization prediction is prior art. Our fixed transfer pilot failed, so it cannot support cross-compartment generality. |
| [Global pairwise RNA interaction landscapes, 2018](https://www.nature.com/articles/s41467-018-04729-0) | Models of pairwise sequence effects and mutation trajectories in RNA–protein recognition. | A positional interaction model is not a novel method by itself, and statistical interaction is not proof of a localization mechanism. |
| [RNA localization to nuclear speckles follows splicing logic, 2026](https://academic.oup.com/nar/article/54/5/gkag174/8508366) | Designed sequences, localization readouts and effects of disease-associated variants in a different compartment. | Claims to be the first sequence-design approach to RNA localization would be untenable. |

## Candidate contribution to evaluate, not a novelty claim

A reproducible, uncertainty-aware benchmark for selecting minimal,
composition-preserving sequence edits using measured experimental landscapes,
with explicit limits on transfer between assays. The useful question is whether
edits can be selected with consistent measured benefit after accounting for
composition, simple short-motif baselines, replicate noise and library artifacts.
The current six-mer swap result supplies exploratory feasibility only. It does
not show endogenous transcript control, therapeutic utility, unseen-parent
generalization, or superiority to ordinary short-motif features.

The strongest remaining requirements are verified sequence-to-count provenance,
replicate consistency, a second independently measured compatible landscape,
and a specific contribution absent from relevant prior work. Negative outcomes
remain part of the record. No protected source should be opened merely because
a new-source result is unfavorable.

## Public-script observations requiring caution

The downloaded SRLE counting script (SHA-256
5446a47b70d741ac78b9a06f4f06a98f3bfa2dd7e12ffd03974c7ac039c4911c)
uses cytoplasmic CPM as both terms in its `nes` ratio, making that field zero.
It also extracts the opposite strand from the named validation oligo inserts
without an explicit reverse complement. These are code observations, not a
finding that the published table or biological experiments are wrong. Reconstruct
the data and report both orientation mappings before deciding how to use it.

The archive labels six-mer replicate 3 with file sizes matching MALAT1 replicate
3. Sizes alone do not establish duplicate data; source identity remains unresolved.
Replicates 1 and 2 are being reconstructed from archive-verified paired files.
