"""Outcome-free new-library identity and overlap checks."""
from .common import ROOT, load_certified, write_json
from .inspect_assets import nested_zip
import json
from collections import Counter

def arora_sequences():
    archive = nested_zip('arora_epmc_supplement', 'gkac763_supplemental_files.zip')
    records = []
    identifier, parts = None, []
    for line in archive.read('SupplementaryFile1.txt').decode().splitlines():
        if line.startswith('>'):
            if identifier is not None:
                records.append((identifier, ''.join(parts).upper().replace('U', 'T')))
            identifier, parts = line[1:], []
        elif line.strip():
            parts.append(line.strip())
    if identifier is not None:
        records.append((identifier, ''.join(parts).upper().replace('U', 'T')))
    if len({r[0] for r in records}) != len(records):
        raise ValueError('Duplicate sequence identifiers')
    return records

def run():
    records = arora_sequences()
    old = load_certified()
    old_genes = set(old.gene_name.str.casefold())
    old_sequences = set(old.mutant_sequence) | set(old.parent_sequence)
    genes = sorted({name.split('|')[-1] for name, seq in records})
    out = {'rows': len(records), 'unique_sequences': len({s for _, s in records}),
        'length_counts': dict(Counter(str(len(s)) for _, s in records)),
        'non_ACGT_rows': sum(bool(set(s) - set('ACGT')) for _, s in records),
        'gene_counts': dict(Counter(name.split('|')[-1] for name, seq in records)),
        'genes_overlapping_old_benchmark': [g for g in genes if g.casefold() in old_genes],
        'genes_not_in_old_benchmark': [g for g in genes if g.casefold() not in old_genes],
        'exact_sequences_overlapping_old_benchmark': sum(s in old_sequences for _, s in records),
        'scope': 'New assay does not imply independent genes. No outcome values inspected.'}
    write_json(ROOT / 'results/research_20260921/arora_sequence_inventory.json', out)
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    run()
