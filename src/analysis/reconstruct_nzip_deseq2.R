# Source-faithful modern DESeq2 reconstruction for the six untreated N-zip runs.
# This script is truth-layer processing only; it performs no predictive modeling.

suppressPackageStartupMessages(library(DESeq2))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
  stop("Usage: Rscript reconstruct_nzip_deseq2.R COUNTS.csv.gz OUT.csv.gz MODE")
}

counts_file <- args[[1]]
out_file <- args[[2]]
mode <- args[[3]]
if (!(mode %in% c("published_coverage", "all_sequences_sensitivity"))) {
  stop("MODE must be published_coverage or all_sequences_sensitivity")
}

tab <- read.csv(counts_file, stringsAsFactors = FALSE, check.names = FALSE)
count_names <- c(
  "replicate1_neurite_read_count", "replicate1_soma_read_count",
  "replicate2_neurite_read_count", "replicate2_soma_read_count",
  "replicate3_neurite_read_count", "replicate3_soma_read_count"
)
if (!all(count_names %in% names(tab))) stop("Expected count columns are missing")
if (anyDuplicated(tab$sequence_id)) stop("DESeq2 input has duplicate sequence IDs")

eligible <- if (mode == "published_coverage") {
  tab$coverage_state == "coverage_pass"
} else {
  rowSums(tab[, count_names, drop = FALSE]) > 0
}

matrix_counts <- as.matrix(tab[eligible, count_names, drop = FALSE])
storage.mode(matrix_counts) <- "integer"
rownames(matrix_counts) <- tab$sequence_id[eligible]

coldata <- data.frame(
  condition = factor(c("neurite", "soma", "neurite", "soma", "neurite", "soma")),
  replicate = factor(c("1", "1", "2", "2", "3", "3"))
)
rownames(coldata) <- count_names

dds <- DESeqDataSetFromMatrix(
  countData = matrix_counts,
  colData = coldata,
  design = ~ condition + replicate
)
dds <- DESeq(dds, quiet = TRUE)
res <- results(
  dds,
  alpha = 0.05,
  contrast = c("condition", "neurite", "soma"),
  independentFiltering = TRUE
)

out <- data.frame(
  sequence_id = tab$sequence_id,
  deseq_mode = mode,
  deseq_included = eligible,
  baseMean = NA_real_,
  log2FoldChange = NA_real_,
  lfcSE = NA_real_,
  stat = NA_real_,
  pvalue = NA_real_,
  padj = NA_real_,
  stringsAsFactors = FALSE
)
matched <- match(rownames(res), out$sequence_id)
out$baseMean[matched] <- res$baseMean
out$log2FoldChange[matched] <- res$log2FoldChange
out$lfcSE[matched] <- res$lfcSE
out$stat[matched] <- res$stat
out$pvalue[matched] <- res$pvalue
out$padj[matched] <- res$padj

gz <- gzfile(out_file, open = "wt", compression = 9)
write.table(out, gz, sep = ",", row.names = FALSE, col.names = TRUE, quote = TRUE, na = "NA")
close(gz)

session_file <- paste0(out_file, ".sessionInfo.txt")
sink(session_file)
print(sessionInfo())
sink()

cat(sprintf(
  "mode=%s sequences=%d included=%d finite_lfc=%d finite_padj=%d\n",
  mode, nrow(out), sum(eligible), sum(is.finite(out$log2FoldChange)), sum(is.finite(out$padj))
))
