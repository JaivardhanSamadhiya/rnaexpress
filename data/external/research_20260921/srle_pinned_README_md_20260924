# 🧬 Tookit for SRLE-seq data analysis

RNA molecules localize to specific subcellular compartments to perform their functions. While most mRNAs are translated at the endoplasmic reticulum, many lncRNAs act within organelles. To better understand RNA localization mechanisms, we developed SRLE-seq (Screening RNA Localization Elements by Sequencing), a high-throughput method to identify functional localization elements. 

---
# 💻 Installation

Requires Python ≥ 3.8 and the following libraries:
```bash
pip install biopython numpy scipy tqdm
git clone https://github.com/lysovosyl/SRLE-seq.git
```

Please replace the setting information of your computer in [config.yaml](./config.yaml).

---
# ⚙️ Analysis modules

## 📚 1. Demultiplex

This script performs demultiplexing of paired-end FASTQ reads based on primer sequences. It identifies which library (or sample) each read pair belongs to by checking the beginning of R1 and R2 sequences for matching primer pairs, and then writes the matched reads into separate FASTQ files for each library.

### Input Requirements

The script accepts the following required command-line arguments:

| Argument   | Type    | Description                                                    | Default |
|------------|---------|----------------------------------------------------------------|---------|
| `-fq1`     | `str`   | Path to R1 FASTQ file                                          | -       |
| `-fq2`     | `str`   | Path to R2 FASTQ file                                          | -       |
| `-s`       | `str`   | Output directory for demultiplexed reads                       | -       |
| `-primer`  | `str`   | Primer list file containing library names and primer sequences | -       |


### Quick Start
Example of `primer.txt` (save this file in plain text format):
```text
lib1 TTCATACCTCTTATCTTCCTCCCACA TAAAACCTCTACAAATGTGGTATGGCTG
lib2 CTGGGCAACGTGCTGGTCTGT GGGGAGGTGTGGGAGGTTTTTTAAAG
lib3 TCATGTTCATACCTCTTATCTTCCT CCTCTACAAATGTGGTATGGCTGATT
```

Run the script with your FASTQ files and primer list:
```angular2html
python library_split.py \
  -fq1 /path/to/R1.fq \
  -fq2 /path/to/R2.fq \
  -s /path/to/output_dir \
  -primer /path/to/primer.txt
```

### Output

After the script finished, the output directory will contain:
```
output_dir
    └──lib1/
        ├── 1.fq   (R1 reads)
        └── 2.fq   (R2 reads)
    └──lib2/
        ├── 1.fq   (R1 reads)
        └── 2.fq   (R2 reads)
    └──lib3/
        ├── 1.fq   (R1 reads)
        └── 2.fq   (R2 reads)
```

## 📚 2. Library diversity analysis (for 6-mer library)

This section is designed to validate whether the constructed Kmer-based plasmid library is suitable for downstream experiments. The distribution of plasmid types corresponding to each k-mer should be relatively uniform. No single k-mer type should dominate the library in abundance, as this would indicate amplification bias or cloning artifacts.

### Input Requirements
The script accepts the following required command-line arguments:

| Argument         | Type     | Description                                              | Default |
|------------------|----------|----------------------------------------------------------|---------|
| `-fq1`           | `str`    | Path to the nuclear sample R1 (forward reads) FASTQ file | -       |
| `-fq2`           | `str`    | Path to the nuclear sample R2 (reverse reads) FASTQ file | -       |
| `-s`             | `str`    | Output directory for saving result figures and tables    | -       |
| `-up_flanking`   | `str`    | Sequence of the upstream (5') anchor primer              | -       |
| `-down_flanking` | `str`    | Sequence of the downstream (3') anchor primer            | -       |
| `-kmer_length`   | `str`    | Length of k-mers to count                                | -       |

### Quick Start
Follow these steps to quickly analyse library diversity:
```angular2html
python kmer_diversity_evaluation.py \
  -fq1 R1.fastq \
  -fq2 R2.fastq \
  -s ./ \
  -up_flanking ATTATGAT \
  -down_flanking GCTTAGTG \
  -kmer_length 6 \
```
### Output
After completion, the output directory will contain:

kmer_diversity.validation.tsv – records the raw count and CPM (counts per million) for each k-mer.

---

## 📚 3. Library diversity analysis (for MALAT1 library)

This section is designed to validate whether the constructed fragment-based plasmid library is suitable for downstream experiments. The inserted fragments should collectively achieve broad and uniform coverage across the full-length source sequence. Ideally, all regions of the original sequence should be represented within the library, ensuring comprehensive functional screening.

### Input Requirements
The script accepts the following required command-line arguments:

| Argument             | Type  | Description                                                | Default       |
|----------------------|-------|------------------------------------------------------------|---------------|
| `-fq1`               | `str` | Path to the nuclear sample R1 (forward reads) FASTQ file   | -             |
| `-fq2`               | `str` | Path to the nuclear sample R2 (reverse reads) FASTQ file   | -             |
| `-s`                 | `str` | Output directory for saving result figures and tables      | -             |
| `-up_flanking`       | `str` | Sequence of the upstream (5') anchor primer                | -             |
| `-down_flanking`     | `str` | Sequence of the downstream (3') anchor primer              | -             |
| `-gene_chr`          | `str` | Chromosome name of the gene locus (e.g., `chr11`)          | -             |
| `-gene_region_start` | `int` | Start coordinate of the target gene region (1-based)       | -             |
| `-gene_region_end`   | `int` | End coordinate of the target gene region (1-based)         | -             |
| `-config`            | `str` | Path to a configuration file containing parameter presets  | ./config.yaml |
| `-thread`            | `int` | Number of threads to use for parallel processing           | 4             |

### Quick Start
Follow these steps to quickly analyse library diversity:
```angular2html
python randomfrag_diversity_evaluation.py \
  -fq1 R1.fastq \
  -fq2 R2.fastq \
  -s ./ \
  -up_flanking ATTATGAT \
  -down_flanking GCTTAGTG \
  -gene_chr chr11 \
  -gene_region_start 65497688
  -gene_region_end 65506516
  -config ./config.yaml
  -thread 64
```
### Output
After completion, the output directory will contain:

dna_fragment.coverage.bed - BED-format file showing per-base coverage of extracted fragments across the specified gene region.

dna_fragment.coverage.png - Coverage plot visualizing the distribution of extracted fragments.

---
## 📚 4. NES calculation (for 6-mer library)

This section aims to investigate the subcellular localization preferences of individual k-mers following plasmid transfection into cells. As a prerequisite, quality control (QC) is performed on the post-transfection k-mer library. A k-mer is considered to pass QC if it shows a count-per-million (CPM) value greater than 1 in at least one of the three compartments: Total, Nuclear (Nuc), or Cytoplasmic (Cyto). This criterion ensures that the k-mer has been successfully transfected and exhibits sufficient expression for downstream analysis.

### Input Requirements
The script accepts the following required command-line arguments:

| Argument         | Type  | Description                                                 | Default  |
|------------------|-------|-------------------------------------------------------------|----------|
| `-nuc_fq1`       | `str` | Path to the nuclear sample R1 (forward reads) FASTQ file    | -        |
| `-nuc_fq2`       | `str` | Path to the nuclear sample R2 (reverse reads) FASTQ file    | -        |
| `-cyto_fq1`      | `str` | Path to the cytoplasm sample R1 (forward reads) FASTQ file  | -        |
| `-cyto_fq2`      | `str` | Path to the cytoplasm sample R2 (forward reads) FASTQ file  | -        |
| `-s`             | `str` | Output directory for saving result figures and tables       | -        |
| `-up_flanking`   | `str` | Sequence of the upstream (5') anchor primer                 | -        |
| `-down_flanking` | `str` | Sequence of the downstream (3') anchor primer               | -        |
| `-mode`          | `str` | Processing mode: `kmer_complexity` or `fragment_complexity` | -        |
| `-kmer_length`   | `int` | Length of k-mers to count                                   | 4        |

### Quick Start
Follow these steps to quickly analyse fragment location analysis:
```angular2html
python kmer_location_analysis.py \
  -nuc_fq1 nuc.R1.fastq \
  -nuc_fq2 nuc.R2.fastq \
  -cyto_fq1 cyto.R1.fastq \
  -cyto_fq2 cyto.R2.fastq \
  -s ./ \
  -up_flanking ATTATGAT \
  -down_flanking GCTTAGTG \
  -mode kmer_complexity \
  -kmer_length 6 \
```

### Output

After completion, the output directory will contain:

kmer_complexity.kmer.count.png – A scatter plot comparing the abundance (CPM) of each k-mer between the cytoplasmic (x-axis) and nuclear (y-axis) compartments. This plot reveals subcellular localization patterns of individual k-mers.

kmer_complexity.info.csv – A summary table listing each k-mer's cytoplasmic and nuclear counts, log₂ fold change (cytoplasm vs. nucleus), and Nuclear Enrichment Score (NES), providing quantitative metrics for assessing k-mer localization bias.

---
## 📚 5. NES calculation (for MALAT1 library)

This section focuses on the subcellular localization patterns of full-length or partial sequence fragments after plasmid transfection. Quality control of the fragment library requires each fragment to have a minimum sequencing coverage of 100×, ensuring reliable detection and quantification. Only fragments meeting this coverage threshold are included in subsequent analyses to evaluate their abundance, CPM, and nuclear enrichment score (NES), which together provide insights into their subcellular distribution characteristics.

### Input Requirements
The script accepts the following required command-line arguments:

| Argument             | Type   | Description                                                 | Default       |
|----------------------|--------|-------------------------------------------------------------|---------------|
| `-nuc_fq1`           | `str`  | Path to the nuclear sample R1 (forward reads) FASTQ file    | -             |
| `-nuc_fq2`           | `str`  | Path to the nuclear sample R2 (reverse reads) FASTQ file    | -             |
| `-cyto_fq1`          | `str`  | Path to the cytoplasm sample R1 (forward reads) FASTQ file  | -             |
| `-cyto_fq2 `         | `str`  | Path to the cytoplasm sample R2 (forward reads) FASTQ file  | -             |
| `-s`                 | `str`  | Output directory for saving result figures and tables       | -             |
| `-up_flanking`       | `str`  | Sequence of the upstream (5') anchor primer                 | -             |
| `-down_flanking`     | `str`  | Sequence of the downstream (3') anchor primer               | -             |
| `-gene_chr`          | `str`  | Chromosome name of the gene locus (e.g., `chr11`)           | -             |
| `-gene_region_start` | `int`  | Start coordinate of the target gene region (1-based)        | -             |
| `-gene_region_end`   | `int`  | End coordinate of the target gene region (1-based)          | -             |
| `-config`            | `str`  | Path to a configuration file containing parameter presets   | ./config.yaml |
| `-thread`            | `int`  | Number of threads to use for parallel processing            | 4             |

### Quick Start
Follow these steps to quickly analyse fragment location analysis:
```angular2html
python randomfrag_location_analysis.py \
  -nuc_fq1 nuc.R1.fastq \
  -nuc_fq2 nuc.R2.fastq \
  -cyto_fq1 cyto.R1.fastq \
  -cyto_fq2 cyto.R2.fastq \
  -s ./ \
  -up_flanking ATTATGAT \
  -down_flanking GCTTAGTG \
  -gene_chr chr11 \
  -gene_region_start 65497688 \
  -gene_region_end 65506516 \
  -config ./config.yaml \
  -thread 64 \
```

### Output

After completion, the output directory will contain:

randomfrag_diversity.tsv – The abundance (read count and CPM) of each random fragment derived from the target gene.

coverage.bed – Base-level coverage information for each specified gene region, indicating how many reads cover each genomic position.

dna_fragment.coverage.png – A visualization of base-level sequencing coverage across each specified gene region, illustrating the distribution and depth of coverage.

Fragment.length.distribution.png – A scatter plot comparing the abundance of each k-mer in the cytoplasm (x-axis) versus the nucleus (y-axis), highlighting their subcellular localization tendencies.

After the script finishes, the output file will contain:
results.csv - A table of predict location for each reads.

## 📚 6. RNA subcellular localization prediction

We implements a Transformer-based deep learning model for binary classification of RNAs using the NSE derived from SRLE-seq.

### Model training

We provides a PyTorch-based sequence classification pipeline using a Transformer architecture.

#### Input Requirements

| Argument       | Type    | Description                           | Default   |
|----------------|---------|---------------------------------------|-----------|
| `--file0`      | `str`   | TSV file containing class 0 samples   | -         |
| `--file1`      | `str`   | TSV file containing class 1 samples   | -         |
| `--out`        | `str`   | Output directory for results          | ./results |
| `--epochs`     | `int`   | Number of training epochs             | 20        |
| `--batch`      | `int`   | Batch size                            | 8         |
| `--lr`         | `float` | Learning rate                         | 1e-4      |
| `--test_size`  | `float` | Proportion of data used for testing   | 0.2       |


#### Quick Start
Follow these steps to train the model:
```angular2html
cd RNA_subcellular_localization_prediction/
python train.py \
  --file0 class0.tsv \
  --file1 class1.tsv \
  --out results \
  --epochs 20 \
  --batch 8 \
  --lr 1e-4
```
#### Output
After training completes, the output directory will contain:
```angular2html
model.pt
accuracy.csv
```

---
### RNA subcellular localization prediction

This script performs inference using a pre-trained sequence classifier.

#### Input Requirements
The script accepts the following required command-line arguments:

| Argument       | Type    | Description                                                            | Default          |
|----------------|---------|------------------------------------------------------------------------|------------------|
| `--input`      | `str`   | Input CSV file containing sequences with seq_id in the first column    | -                |
| `--model`      | `str`   | Pre-trained model file path (.pt / .pth)                               | -                |
| `--out`        | `str`   | Output CSV file for prediction results                                 | ./prediction.csv |
| `--device`     | `str`   | Device to run prediction (cuda or cpu)                                 | cuda             |


#### Quick Start
Run inference using the following command:
```angular2html
python infer_sequence.py \
  --input sequence.tsv \
  --model model.pt \
  --out results.csv \
  --device cuda \
```

#### Output

After the script finishes, the output file will contain:

```angular2html
results.csv - A table of predict location for each reads.
```

---


# 📝 Please Cite

If you use this script or parts of it in your research or project, please cite the repository or acknowledge the author appropriately. A suggested citation format:

> [Zeng. x. (2025). *SRLE-seq k-mer comparison and visualization pipeline*]()

---

# 👨‍💻 Maintainer

**[Lin Yusen](https://github.com/lysovosyl)**  
Email: `linyusen1688@gmail.com`  

Feel free to open an issue or pull request for improvements or bug fixes.

---

# 🤝 Contributors

> Current contributors:
> - Yusen Lin
> - Xingqaun Zeng
> - Jiajian Zhou
---

# 📄 License

This project is licensed under the [MIT License](LICENSE.txt).  
You are free to use, modify, and distribute it with attribution.




