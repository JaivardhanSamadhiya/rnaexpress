"""Metadata-only access for public SRLE replicate availability."""
from .resources import URLS, fetch
from concurrent.futures import ThreadPoolExecutor
import json

URLS.update({
    'srle_gsa_metadata': 'https://ngdc.cncb.ac.cn/gsa-human/browse/HRA016642',
    'srle_gsa_directory': 'https://download.cncb.ac.cn/gsa-human/HRA016642/',
    'srle_gsa_runs': 'https://ngdc.cncb.ac.cn/gsa-human/ajaxb/runinstudy?accession=HRA016642',
    'srle_gsa_runs_all': 'https://ngdc.cncb.ac.cn/gsa-human/ajaxb/runinstudy?accession=HRA016642&pageNo=1&pageSize=200',
    'srle_author_count_code': 'https://raw.githubusercontent.com/lysovosyl/SRLE-seq/main/kmer_location_analysis.py',
    'srle_raw_checksums': 'https://download.cncb.ac.cn/gsa-human/HRA016642/md5sum.txt',
})

def retrieve(name):
    try:
        fetch(name)
    except Exception as exc:
        print(json.dumps({'name': name, 'error': str(exc)}), flush=True)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(retrieve, ['srle_gsa_runs_all', 'srle_author_count_code', 'srle_raw_checksums']))
