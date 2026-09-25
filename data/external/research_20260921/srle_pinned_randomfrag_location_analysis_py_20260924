#%%
from collections import defaultdict
from Bio import SeqIO
import argparse
import os
from itertools import product
import pysam
import re
import yaml
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import csv

parse = argparse.ArgumentParser(description="K-mer counting and plotting script for nuc/cyto comparison")
parse.add_argument('-nuc_fq1', type=str, required=True, help="nuclear sample R1 fastq file")
parse.add_argument('-nuc_fq2', type=str, required=True, help="nuclear sample R2 fastq file")
parse.add_argument('-cyto_fq1', type=str, required=True, help="cytoplasmic sample R1 fastq file")
parse.add_argument('-cyto_fq2', type=str, required=True, help="cytoplasmic sample R2 fastq file")
parse.add_argument('-s', type=str, required=True, help="Path to save result figures or tables")
parse.add_argument('-up_flanking', type=str, required=True, help="Upstream primer sequence (z)")
parse.add_argument('-down_flanking', type=str, required=True, help="Downstream primer sequence (z)")
parse.add_argument('-gene_chr', type=str, required=True, help="Chromosome name of the gene locus (e.g., chr11)	")
parse.add_argument('-gene_region_start', type=int, required=True, help="	Start coordinate of the target gene region (1-based)")
parse.add_argument('-gene_region_end', type=int, required=True, help="End coordinate of the target gene region (1-based)")
parse.add_argument('-config', type=str, default='./config.yaml', help="Path to a configuration file containing parameter presets")
parse.add_argument('-thread', type=int,default=4,help='Number of threads to use for parallel processing')
args = parse.parse_args()

up_flanking_region = args.up_flanking
down_flanking_region= args.down_flanking
nuc_fq1_file = args.nuc_fq1
nuc_fq2_file = args.nuc_fq2
cyto_fq1_file = args.cyto_fq1
cyto_fq2_file = args.cyto_fq2
save_path = args.s
gene_chr = args.gene_chr
gene_region_start = args.gene_region_start
gene_region_end = args.gene_region_end
thread = args.thread
config_file = args.config


# up_flanking_region = 'ATTATGAT'
# down_flanking_region='GCTTAGTG'
# nuc_fq1_file = '/mnt/dfc_data1/home/linyusen/tmp/xinquan/cell/MALAT1_Nuc_Sample1/test_1.fq'
# nuc_fq2_file = '/mnt/dfc_data1/home/linyusen/tmp/xinquan/cell/MALAT1_Nuc_Sample1/test_2.fq'
# cyto_fq1_file = '/mnt/dfc_data1/home/linyusen/tmp/xinquan/cell/MALAT1_Cyto_Sample1/test_1.fq'
# cyto_fq2_file = '/mnt/dfc_data1/home/linyusen/tmp/xinquan/cell/MALAT1_Cyto_Sample1/test_2.fq'
# save_path = '/mnt/dfc_data1/home/linyusen/tmp/xinquan/cell/test'
# gene_chr = 'chr11'
# gene_region_start = 65497688
# gene_region_end = 65506516
# thread = 64
# config_file = '/mnt/dfc_data2/project/linyusen/project/72_xinquan_rnaloc/github/config.yaml'

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

fq1_file = nuc_fq1_file
fq2_file = nuc_fq2_file
pear_out = os.path.join(save_path,'cyto')
cmd = f'{pear} -f {fq1_file} -r {fq2_file} -j {thread} -o {pear_out}'
os.system(cmd)
fq1_file = cyto_fq1_file
fq2_file = cyto_fq2_file
pear_out = os.path.join(save_path,'nuc')
cmd = f'{pear} -f {fq1_file} -r {fq2_file} -j {thread} -o {pear_out}'
os.system(cmd)
#%%
single_nuc_fastq = os.path.join(save_path,'nuc.assembled.fastq')
single_cyto_fastq = os.path.join(save_path,'cyto.assembled.fastq')
pattern = re.compile(f"{up_flanking_region}([ACGT]+?){down_flanking_region}")
pattern_re = re.compile(f"{down_flanking_region_re}([ACGT]+?){up_flanking_region_re}")

def qual_list_to_string(fq_qual):
    return ''.join([chr(q + 33) for q in fq_qual])

#%%
log = '''
---------------------------------------------------------------
Step 02: Searching for valid sequences.
---------------------------------------------------------------
'''
print(log)
def search_fastq(save_fq,single_fastq):
    name_list = set()
    effected_fragment_length_list = []
    kmer_count = defaultdict(int)
    total_count = 0
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
    return name_list,effected_fragment_length_list,kmer_count,total_count

nuc_save_fq = os.path.join(save_path,"effected.nuc.reads.fastq")
single_fastq = os.path.join(save_path,'nuc.assembled.fastq')
nuc_name_list,nuc_effected_fragment_length_list,nuc_kmer_count,nuc_total_count = search_fastq(nuc_save_fq,single_fastq)

cyto_save_fq = os.path.join(save_path,"effected.cyto.reads.fastq")
single_fastq = os.path.join(save_path,'cyto.assembled.fastq')
cyto_name_list,cyto_effected_fragment_length_list,cyto_kmer_count,cyto_total_count = search_fastq(cyto_save_fq,single_fastq)

randomfrag_cyto_out_dict = {}
for kmer in cyto_kmer_count:
    randomfrag_cyto_out_dict[kmer] = {}
    cpm = cyto_kmer_count[kmer] / cyto_total_count * 1000000
    randomfrag_cyto_out_dict[kmer]['cpm']= cpm
    randomfrag_cyto_out_dict[kmer]['count'] = cyto_kmer_count[kmer]

randomfrag_nuc_out_dict = {}
for kmer in nuc_kmer_count:
    randomfrag_nuc_out_dict[kmer] = {}
    cpm = nuc_kmer_count[kmer] / nuc_total_count * 1000000
    randomfrag_nuc_out_dict[kmer]['cpm']= cpm
    randomfrag_nuc_out_dict[kmer]['count'] = cyto_kmer_count[kmer]

#%%
log = '''
---------------------------------------------------------------
Step 03: Aligning valid sequences using Bowtie.
---------------------------------------------------------------
'''

def Aligning(save_fq,save_path,head):
    bam_file = os.path.join(save_path, f'{head}.alignment.bam')
    cmd = f'{bowtie} -v 2 -a -k 10 -p {thread} -S {genome_index} {save_fq} | {samtools} view -bS > {bam_file}'
    os.system(cmd)
    sorted_bam_file = os.path.join(save_path, f'{head}.alignment.sorted.bam')
    cmd = f'{samtools} sort -@ {thread} -o {sorted_bam_file} {bam_file} '
    os.system(cmd)
    cmd = f'{samtools} index {sorted_bam_file}'
    os.system(cmd)
    bam = pysam.AlignmentFile(sorted_bam_file, "rb")
    coverage = [0] * (gene_region_end - gene_region_start)
    coverage_x = []
    target_region_reads_count = 0
    for read in bam.fetch(gene_chr, gene_region_start, gene_region_end):
        if read.is_unmapped:
            continue
        target_region_reads_count += 1
        for pos in read.get_reference_positions():
            if gene_region_start <= pos < gene_region_end:
                coverage[pos - gene_region_start] += 1

    output_bed = os.path.join(save_path, f'{head}.coverage.bed')
    with open(output_bed, "w") as out:
        for i, cov in enumerate(coverage):
            chrom_start = gene_region_start + i
            chrom_end = chrom_start + 1
            coverage_x.append(gene_region_start + i)
            out.write(f"{gene_chr}\t{chrom_start}\t{chrom_end}\t{cov}\n")
    return coverage,coverage_x

nuc_coverage,nuc_coverage_x = Aligning(nuc_save_fq,save_path,'nuc')
cyto_coverage,cyto_coverage_x = Aligning(cyto_save_fq,save_path,'cyto')
#%%




log = '''
---------------------------------------------------------------
Step 03: Saving result.
---------------------------------------------------------------
'''
print(log)

def save_result(kmer_count,total_count,name_list,effected_fragment_length_list,coverage_x, coverage,save_path):
    sorted_data = dict(sorted(kmer_count.items(), key=lambda item: item[1], reverse=True))


    f = open(os.path.join(save_path,f'randomfrag_diversity.tsv'),'w')
    w = csv.writer(f,delimiter='\t')
    w.writerow([f'# total sequence count:{total_count}'])
    w.writerow([f'# effected sequence count:{len(name_list)}\tpercentage:{len(name_list)/total_count}'])
    w.writerow(['kmer','count','CPM'])
    for i in sorted_data:
        w.writerow([i,sorted_data[i],sorted_data[i]/total_count*1000000])
    f.close()

    bwith = 3
    fig, (ax1) = plt.subplots(1, 1, figsize=(16, 3), dpi=300)
    labelsize = 14
    ax1.bar(coverage_x, coverage, width=1)
    ax1.set_title('{}:{}-{}'.format(gene_chr, gene_region_start, gene_region_end))
    ax1.set_xlim([gene_region_start, gene_region_end])
    ax1.spines['left'].set_linewidth(bwith)
    ax1.spines['top'].set_linewidth(bwith)
    ax1.spines['right'].set_linewidth(bwith)
    ax1.spines['bottom'].set_linewidth(bwith)
    ax1.tick_params(axis='both', which='major', width=bwith, length=bwith * 3, labelsize=labelsize)
    figure_save_path = os.path.join(save_path, 'dna_fragment.coverage.png')
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

if os.path.exists(os.path.join(save_path,'nuc_result')) == False:
    os.mkdir(os.path.join(save_path,'nuc_result'))
save_result(kmer_count=nuc_kmer_count,
            total_count=nuc_total_count,
            name_list=nuc_name_list,
            effected_fragment_length_list=nuc_effected_fragment_length_list,
            coverage=nuc_coverage,
            coverage_x=nuc_coverage_x,
            save_path=os.path.join(save_path,'nuc_result'))
if os.path.exists(os.path.join(save_path,'cyto_result')) == False:
    os.mkdir(os.path.join(save_path,'cyto_result'))
save_result(kmer_count=cyto_kmer_count,
            total_count=cyto_total_count,
            name_list=cyto_name_list,
            effected_fragment_length_list=cyto_effected_fragment_length_list,
            coverage=cyto_coverage,
            coverage_x=cyto_coverage_x,
            save_path=os.path.join(save_path,'cyto_result'))

print('Done!')
