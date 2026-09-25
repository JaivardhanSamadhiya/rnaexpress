#%%
from collections import defaultdict
from Bio import SeqIO
import argparse
import os
import csv
import matplotlib.pyplot as plt
from tqdm import tqdm
import re

# parse = argparse.ArgumentParser(description="K-mer counting and plotting script for nuc/cyto comparison")
# parse.add_argument('-fq1', type=str, required=True, help="R1 fastq file")
# parse.add_argument('-fq2', type=str, required=True, help="R2 fastq file")
# parse.add_argument('-s', type=str, required=True, help="Output directory for saving result figures and tables")
# parse.add_argument('-primer', type=str, required=True, help="primer file")
# args = parse.parse_args()
#
# fq1_file = args.fq1
# fq2_file = args.fq2
# save_path = args.s
# primer_file = args.primer


fq1_file = '/mnt/dfc_data3/project/linyusen/01.RawData/Cyto/Cyto_1.fq'
fq2_file = '/mnt/dfc_data3/project/linyusen/01.RawData/Cyto/Cyto_2.fq'
save_path = '/mnt/dfc_data3/project/linyusen/01.RawData/Cyto2'
primer_file = '/mnt/dfc_data2/project/linyusen/project/72_xinquan_rnaloc/github/primer.txt'

primer_dict = {}
f = open(primer_file)
for i in f.readlines():
    name,primer1,primer2 = i.strip('\n').split(' ')
    primer_dict[name] = [primer1,primer2]
def rev_seq(seq):
    # 反转
    rev = seq[::-1]
    # 互补
    comp_map = str.maketrans("ACGT", "TGCA")
    rev_comp = rev.translate(comp_map)
    return rev_comp
#%%

writer_dict = {}
lib_info = {}

for lib_name in primer_dict.keys():
    os.makedirs(os.path.join(save_path,lib_name), exist_ok=True)
    w1 = open(os.path.join(save_path,lib_name,'1.fq'), "w")
    w2 = open(os.path.join(save_path,lib_name,'2.fq'), "w")
    writer_dict[lib_name] = {'w1':w1, 'w2':w2}
    lib_info[lib_name] = {'match':0,'total':0,'fail':0}
#%%
f1 = open(fq1_file, "r")
f2 = open(fq2_file, "r")
count1 =0
count2 =0

while True:
    r1_block = [f1.readline() for _ in range(4)]
    r2_block = [f2.readline() for _ in range(4)]

    # 判断文件是否结束
    if not r1_block[0] or not r2_block[0]:
        break

    r1_id,r1_seq,r1_stata,r1_quality = r1_block
    r2_id,r2_seq,r2_stata,r2_quality = r2_block
    
    for lib_name in primer_dict.keys():
        primer1 = primer_dict[lib_name][0]
        primer2 = primer_dict[lib_name][1]
        lib_info[lib_name]['total'] +=1
        if primer1 == r1_seq[:len(primer1)] and primer2 == r2_seq[:len(primer2)]:
            writer_dict[lib_name]['w1'].write(r1_id)
            writer_dict[lib_name]['w1'].write(r1_seq)
            writer_dict[lib_name]['w1'].write(r1_stata)
            writer_dict[lib_name]['w1'].write(r1_quality)
            writer_dict[lib_name]['w2'].write(r2_id)
            writer_dict[lib_name]['w2'].write(r2_seq)
            writer_dict[lib_name]['w2'].write(r2_stata)
            writer_dict[lib_name]['w2'].write(r2_quality)
            lib_info[lib_name]['match'] += 1
        elif primer2 == r1_seq[:len(primer1)] and primer1 == r2_seq[:len(primer2)]:
            writer_dict[lib_name]['w1'].write(r1_id)
            writer_dict[lib_name]['w1'].write(r1_seq)
            writer_dict[lib_name]['w1'].write(r1_stata)
            writer_dict[lib_name]['w1'].write(r1_quality)
            writer_dict[lib_name]['w2'].write(r2_id)
            writer_dict[lib_name]['w2'].write(r2_seq)
            writer_dict[lib_name]['w2'].write(r2_stata)
            writer_dict[lib_name]['w2'].write(r2_quality)
            lib_info[lib_name]['match']  += 1
        else:
            lib_info[lib_name]['fail'] += 1

#%%
import csv
f = open(os.path.join(save_path,'lib.info'), "w")
w = csv.writer(f,delimiter='\t')
w.writerow(['lib','total','match','unmatch'])
print('lib','total','match','unmatch')
for lib_name in lib_info.keys():
    w.writerow([lib_name,lib_info[lib_name]['total'],lib_info[lib_name]['match'],lib_info[lib_name]['fail']])
    print(lib_name,lib_info[lib_name]['total'],lib_info[lib_name]['match'],lib_info[lib_name]['fail'])
f.close()
