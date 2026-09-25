#%%
import os
import numpy as np
from collections import defaultdict
from Bio import SeqIO
import argparse
import os
from itertools import product
import csv
from scipy.stats import ttest_ind
from tqdm import tqdm
from multiprocessing import Pool
import re
import matplotlib.pyplot as plt
import pysam
from Bio.SeqIO.QualityIO import FastqGeneralIterator
from itertools import islice
import yaml

#%%
parse = argparse.ArgumentParser(description="K-mer counting and plotting script for nuc/cyto comparison")
parse.add_argument('-fq1', type=str, required=True, help="R1 fastq file")
parse.add_argument('-fq2', type=str, required=True, help="R2 fastq file")
parse.add_argument('-s', type=str, required=True, help="Path to save result tables")
parse.add_argument('-up_flanking', type=str, required=True, help="Upstream primer sequence (z)")
parse.add_argument('-down_flanking', type=str, required=True, help="Downstream primer sequence (z)")
parse.add_argument('-gene_chr', type=str, required=True, help="Chromosome name of the gene locus (e.g., chr11)	")
parse.add_argument('-gene_region_start', type=int, required=True, help="	Start coordinate of the target gene region (1-based)")
parse.add_argument('-gene_region_end', type=int, required=True, help="End coordinate of the target gene region (1-based)")
parse.add_argument('-config', type=str, default='./config.yaml', help="Path to a configuration file containing parameter presets")
parse.add_argument('-thread', type=int,default=4,help='Number of threads to use for parallel processing')
args = parse.parse_args()

fq1_file = args.fq1
fq2_file = args.fq2
save_path = args.s
up_flanking_region = args.up_flanking
down_flanking_region = args.down_flanking
gene_chr = args.gene_chr
gene_region_start = args.gene_region_start
gene_region_end = args.gene_region_end
thread = args.thread
config_file = args.config
#%%
# fq1_file = '/mnt/dfc_data1/home/linyusen/tmp/malat1_fq1.fastq'
# fq2_file = '/mnt/dfc_data1/home/linyusen/tmp/malat1_fq2.fastq'
# save_path = '/mnt/dfc_data1/home/linyusen/tmp/'
# up_flanking_region = 'ATTATGAT'
# down_flanking_region='GCTTAGTG'
# gene_chr = 'chr11'
# gene_region_start = 65497688
# gene_region_end = 65506516
# thread = 64
# config_file = '/mnt/dfc_data2/project/linyusen/project/72_xinquan_rnaloc/github/config.yaml'

#%%

with open(config_file, 'r') as file:
    config_data = yaml.safe_load(file)

bowtie = config_data['software']['bowtie']
genome_index = config_data['database']['genome_index']
samtools = config_data['software']['samtools']
pear = config_data['software']['pear']


def reverse_complement(seq):
    complement = str.maketrans("ACGTacgt", "TGCAtgca")
    return seq.translate(complement)[::-1]
up_flanking_region_re = reverse_complement(up_flanking_region)
down_flanking_region_re = reverse_complement(down_flanking_region)
#%%
log = '''
---------------------------------------------------------------
Step 01: Using PEAR to merge paired-end sequences.
---------------------------------------------------------------
'''
print(log)
pear_out = os.path.join(save_path,'pear')
cmd = f'{pear} -f {fq1_file} -r {fq2_file} -j {thread} -o {pear_out}'
os.system(cmd)

single_fastq = os.path.join(save_path,'pear.assembled.fastq')
pattern = re.compile(f"{up_flanking_region}([ACGT]+?){down_flanking_region}")
pattern_re = re.compile(f"{down_flanking_region_re}([ACGT]+?){up_flanking_region_re}")
save_fq = os.path.join(save_path,"effected.reads.fastq")
effected_fragment_length_list = []
kmer_count = defaultdict(int)
name_list = set()
def qual_list_to_string(fq_qual):
    return ''.join([chr(q + 33) for q in fq_qual])
total_count = 0

log = '''
---------------------------------------------------------------
Step 02: Searching for valid sequences.
---------------------------------------------------------------
'''
print(log)

# Open the output FASTQ file for writing matched reads
with open(save_fq, "w") as fq_out:
    # Iterate through each record in the single-end FASTQ file
    for record in tqdm(SeqIO.parse(single_fastq, 'fastq'), desc="Processing FASTQ", unit="reads"):
        total_count+=1
        title = record.id
        seq = str(record.seq)
        qual = record.letter_annotations["phred_quality"]

        seq = str(seq)  # Convert sequence to string format

        # Try matching the sequence using both the forward and reverse flanking region patterns
        match1 = pattern.search(seq)
        match1_re = pattern_re.search(seq)

        fq_seq = False  # Initialize a flag to store matched sequence

        # If forward-direction match is found
        if match1:
            start = match1.start(1)
            end = match1.end(1)
            fq_seq = match1.group(1)            # Extract matched inner sequence
            fq_qual = qual[start:end]          # Extract corresponding quality scores
            kmer_count[fq_seq] += 1             # Count this k-mer

        # If reverse-direction match is found
        if match1_re:
            start = match1_re.start(1)
            end = match1_re.end(1)
            fq_seq = match1_re.group(1)         # Extract matched inner sequence
            fq_qual = qual[start:end]          # Extract corresponding quality scores
            kmer_count[fq_seq] += 1             # Count this k-mer

        # If a valid k-mer is extracted and it's longer than 10 bases
        if fq_seq:
            if len(fq_seq) > 24:
                # Write the read to the output FASTQ file
                qual_str = qual_list_to_string(fq_qual)
                fq_out.write(f"@{title}\n{fq_seq}\n+\n{qual_str}\n")
                effected_fragment_length_list.append(len(fq_seq))
                # Save the base read name (remove /1 or /2) for downstream usage
                name_list.add(title.split('/')[0])
#%%
log = '''
---------------------------------------------------------------
Step 03: Aligning valid sequences using Bowtie.
---------------------------------------------------------------
'''
print(log)
bam_file = os.path.join(save_path,'dna_fragment.alignment.bam')
cmd = f'{bowtie} -v 2 -a -k 10 -p {thread} -S {genome_index} {save_fq} | {samtools} view -bS > {bam_file}'
os.system(cmd)
sorted_bam_file = os.path.join(save_path,'dna_fragment.alignment.sorted.bam')
cmd = f'{samtools} sort -@ {thread} -o {sorted_bam_file} {bam_file} '
os.system(cmd)
cmd = f'{samtools} index {sorted_bam_file}'
os.system(cmd)
target_region_bam_file = os.path.join(save_path,'target_region.alignment.bam')
cmd = f'{samtools} view -b -h -o {target_region_bam_file} {sorted_bam_file} {gene_chr}:{gene_region_start}-{gene_region_end}'
os.system(cmd)

bam = pysam.AlignmentFile(sorted_bam_file, "rb")
coverage = [0] * (gene_region_end - gene_region_start)
coverage_x = []
target_region_reads_count = 0
for read in bam.fetch(gene_chr, gene_region_start, gene_region_end):
    if read.is_unmapped:
        continue
    target_region_reads_count+=1
    for pos in read.get_reference_positions():
        if gene_region_start <= pos < gene_region_end:
            coverage[pos - gene_region_start] += 1

output_bed = os.path.join(save_path,'dna_fragment.coverage.bed')
with open(output_bed, "w") as out:
    for i, cov in enumerate(coverage):
        chrom_start = gene_region_start + i
        chrom_end = chrom_start + 1
        coverage_x.append(gene_region_start + i)
        out.write(f"{gene_chr}\t{chrom_start}\t{chrom_end}\t{cov}\n")
#%%
log = '''
---------------------------------------------------------------
Step 04: Saving result.
---------------------------------------------------------------
'''
print(log)
sorted_data = dict(sorted(kmer_count.items(), key=lambda item: item[1], reverse=True))


f = open(os.path.join(save_path,f'kmer_diversity.validation.tsv'),'w')
w = csv.writer(f,delimiter='\t')
w.writerow([f'# total sequence count:{total_count}'])
w.writerow([f'# effected sequence count:{len(name_list)}\tpercentage:{len(name_list)/total_count}'])
w.writerow([f'# target region reads_count:{target_region_reads_count}\tpercentage:{target_region_reads_count/total_count}'])
w.writerow(['kmer','count','CPM'])
for i in sorted_data:
    w.writerow([i,sorted_data[i],sorted_data[i]/total_count*1000000])
f.close()




bwith = 3
fig, (ax1) = plt.subplots(1, 1, figsize=(16, 3),dpi=300)
labelsize = 14
ax1.bar(coverage_x,coverage,width=1)
ax1.set_title('{}:{}-{}'.format(gene_chr,gene_region_start,gene_region_end))
ax1.set_xlim([gene_region_start,gene_region_end])
ax1.spines['left'].set_linewidth(bwith)
ax1.spines['top'].set_linewidth(bwith)
ax1.spines['right'].set_linewidth(bwith)
ax1.spines['bottom'].set_linewidth(bwith)
ax1.tick_params(axis='both', which='major', width=bwith, length=bwith*3,labelsize=labelsize)
figure_save_path = os.path.join(save_path,'dna_fragment.coverage.png')
plt.tight_layout()
plt.savefig(figure_save_path)

plt.figure(figsize=(8, 5))
plt.hist(effected_fragment_length_list, bins=100, edgecolor='black')  # 你可以调整 bins 的数量
plt.xlabel("Fragment Length")
plt.ylabel("Number of Fragment")
plt.title(f"Fragment Length Distribution")
plt.tight_layout()
figure_save_path = os.path.join(save_path,'Fragment.length.distribution.png')
plt.savefig(figure_save_path)

print('Done!')
