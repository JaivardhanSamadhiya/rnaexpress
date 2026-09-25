#%%
from collections import defaultdict
from Bio import SeqIO
import argparse
import os
import csv
import matplotlib.pyplot as plt
from tqdm import tqdm
import re

parse = argparse.ArgumentParser(description="K-mer counting and plotting script for nuc/cyto comparison")
parse.add_argument('-fq1', type=str, required=True, help="R1 fastq file")
parse.add_argument('-fq2', type=str, required=True, help="R2 fastq file")
parse.add_argument('-s', type=str, required=True, help="Output directory for saving result figures and tables")
parse.add_argument('-up_flanking', type=str, required=True, help="Sequence of the upstream (5') anchor primer")
parse.add_argument('-down_flanking', type=str, required=True, help="Sequence of the downstream (3') anchor primer")
parse.add_argument('-kmer_length', type=int, required=True, help="Length of k-mers to count")
args = parse.parse_args()


fq1_file = args.fq1
fq2_file = args.fq2
save_path = args.s
up_flanking_region = args.up_flanking
down_flanking_region = args.down_flanking
kmer_length = args.kmer_length



def rev_seq(seq):
    # 反转
    rev = seq[::-1]
    # 互补
    comp_map = str.maketrans("ACGT", "TGCA")
    rev_comp = rev.translate(comp_map)
    return rev_comp

# fq1_file = '/mnt/dfc_data1/home/linyusen/tmp/xinquan/diversity/6mer/6mer.library.R1.fq'
# fq2_file = '/mnt/dfc_data1/home/linyusen/tmp/xinquan/diversity/6mer/6mer.library.R2.fq'
# save_path = '/mnt/dfc_data1/home/linyusen/tmp/xinquan/diversity/6mer/'
# up_flanking_region = 'ATTATGAT'
# down_flanking_region='GCTTAGTG'
# mode = 'kmer_diversity'
# kmer_length = 6
os.makedirs(save_path, exist_ok=True)

# Compile the regex pattern to extract the target sequence between flanking regions
pattern1 = re.compile(f"{up_flanking_region}([ACGT]+?){down_flanking_region}")
pattern2 = re.compile(f"{rev_seq(down_flanking_region)}([ACGT]+?){rev_seq(up_flanking_region)}")
# Initialize a dictionary to count k-mer occurrences
kmer_count = defaultdict(int)

# Initialize a set to store unique read names (without /1 or /2)

effective_count = 0
total_count = 0

f1 = open(fq1_file, "r")
f2 = open(fq2_file, "r")

while True:
    r1_block = [f1.readline() for _ in range(4)]
    r2_block = [f2.readline() for _ in range(4)]

    # 判断文件是否结束
    if not r1_block[0] or not r2_block[0]:
        break
    total_count += 1
    r1_id, r1_seq, r1_stata, r1_quality = r1_block
    r2_id, r2_seq, r2_stata, r2_quality = r2_block

    # Search for the k-mer pattern
    match_r1_f = pattern1.search(r1_seq)  # 正向的
    match_r1_r = pattern2.search(r1_seq)  # 正向的
    match_r2_f = pattern1.search(r2_seq)  # 正向的
    match_r2_r = pattern2.search(r2_seq)  # 正向的

    if match_r1_f or match_r1_r:
        if match_r1_f:
            kmer = match_r1_f.group(1)  # 正向匹配
            kmer_count[kmer] += 1  # Count k-mer occurrence
            effective_count += 1
        elif match_r1_r:
            kmer = match_r1_r.group(1)  # 反向匹配
            kmer = rev_seq(kmer)
            kmer_count[kmer] += 1  # Count k-mer occurrence
            effective_count += 1
    elif match_r2_f or match_r2_r:
        if match_r2_f:
            kmer = match_r2_f.group(1)  # 正向匹配
            kmer_count[kmer] += 1  # Count k-mer occurrence
            effective_count += 1
        elif match_r2_r:
            kmer = match_r2_r.group(1)  # 反向匹配
            kmer = rev_seq(kmer)
            kmer_count[kmer] += 1  # Count k-mer occurrence
            effective_count += 1



# Remove any k-mers that do not match the expected length
if kmer_length == None:
    # Rebuild a filtered dictionary with only valid-length k-mers
    filtered_data = {k: v for k, v in kmer_count.items()}
else:
    for i in list(kmer_count.keys()):
        if len(i) != kmer_length:
            kmer_count.pop(i)
    filtered_data = {k: v for k, v in kmer_count.items() if len(k) == kmer_length}
#%%
# Sort k-mers by descending count
sorted_data = dict(sorted(filtered_data.items(), key=lambda item: item[1], reverse=True))

f = open(os.path.join(save_path,f'kmer_diversity.validation.tsv'),'w')
w = csv.writer(f,delimiter='\t')
w.writerow([f'# total sequence count:{total_count}'])
w.writerow([f'# effective sequence count:{effective_count} percentage:{effective_count/total_count}'])
w.writerow([f'# k-mer diversity:{len(sorted_data.keys())}'])
w.writerow(['kmer','count','CPM'])
for i in sorted_data:
    w.writerow([i,sorted_data[i],sorted_data[i]/total_count*1000000])
f.close()


y = list(sorted_data.values())
x = range(len(y))
max_idx = y.index(max(y))
min_idx = y.index(min(y))
max_kmer = list(sorted_data.keys())[max_idx]
min_kmer = list(sorted_data.keys())[min_idx]
plt.figure(figsize=(10, 6))
plt.plot(x, y, label='K-mer Count')
plt.fill_between(x, y, alpha=0.3)
plt.xlabel("Ranked K-mers")
plt.ylabel("Count")
plt.title(f"{kmer_length}-mer Count Distribution")
plt.xticks([])
plt.text(max_idx, y[max_idx], f"Max: {max_kmer} ({y[max_idx]})",
         ha='left', va='bottom', fontsize=9, color='red')
plt.text(min_idx, y[min_idx], f"Min: {min_kmer} ({y[min_idx]})",
         ha='right', va='top', fontsize=9, color='blue')
plt.tight_layout()
figure_save_path = os.path.join(save_path,'kmer.count.png')
plt.savefig(figure_save_path)

counts = list(sorted_data.values())
plt.figure(figsize=(8, 5))
plt.hist(counts, bins=100, edgecolor='black')  # 你可以调整 bins 的数量
plt.xlabel("K-mer Count")
plt.ylabel("Number of K-mers")
plt.title(f"Kmers Count Distribution")
plt.tight_layout()
figure_save_path = os.path.join(save_path,'kmer.distribution.png')
plt.savefig(figure_save_path)

print('Done!')
