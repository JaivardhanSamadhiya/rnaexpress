"""Reporter sequence metadata only: no outcome columns, raw counts, or fits."""
from pathlib import Path
from collections import Counter
import gzip, hashlib, json
import pandas as pd

ROOT = Path('D:/rnaexpress')
OUT = ROOT / 'artifacts/full_reporter_context_20261007/mikl_moffatt_metadata_certificate.json'
SEQ = 'full library sequence (primers-barcode-test sequence)'
MIKL = ROOT / 'data/raw/mikl_gse173098/supplementary/files/SupplementaryData_NAR_Final/SupplementaryTables/TableS2.csv'
CORE = ROOT / 'results/probabilistic_ranking_20260928/candidate_index.csv'
LINEAGE = ROOT / 'results/v4_phaseA/mikl_interventions.csv.gz'
AUTHOR = ROOT / 'data/external/RNAloc_MPRA/dataframes/library_varseq_FINAL.csv'
FASTA = ROOT / 'data/raw/moffatt_gse334718/supplementary/supplementary_file_1.txt'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def cutting_certificate(prefix, suffix):
    rc = lambda text: text.translate(str.maketrans('ACGTacgt', 'TGCAtgca'))[::-1]
    synthetic = prefix + 'A' * 12 + 'A' * 150 + suffix
    forward = 'cacaGGCGCGCCa' + prefix
    reverse = 'cacaCCTGCAGGa' + rc(suffix)
    full = forward[:13] + synthetic + rc(reverse[:13])
    left, right = full.upper().index('GGCGCGCC'), full.upper().index('CCTGCAGG')
    # Manufacturer sense cuts after site offsets2 and6 respectively.
    strand, duplex = full[left + 2:right + 6], full[left:right + 8]
    assert len(full) == 224 and (left, right) == (4, 212)
    assert len(strand) == 212 and len(duplex) == 216
    assert duplex[9:-9] == synthetic
    assert duplex[9:27] == prefix and duplex[189:207] == suffix
    assert duplex[39:189] == 'A' * 150
    return {'PCR_sense_length': len(full), 'site_starts0': [left, right],
            'sense_cut_offsets0': [left + 2, right + 6], 'retained_sense_strand_length': len(strand),
            'restored_local_DNA_length': len(duplex), 'variable_interval0_halfopen': [39, 189],
            'restored_template': 'GGCGCGCCa + prefix18 + barcode12 + variable150 + suffix18 + tCCTGCAGG',
            'forward_primer': forward, 'reverse_primer': reverse,
            'condition': 'same-site oriented reference digestion/ligation, no subsequent sequence change; not mature RNA'}


def records(path):
    key, parts = None, []
    with path.open() as stream:
        for line in stream:
            line = line.strip()
            if line.startswith('>'):
                if key is not None:
                    yield key, ''.join(parts)
                key, parts = line[1:], []
            elif line:
                parts.append(line)
        if key is not None:
            yield key, ''.join(parts)


def main():
    assert not OUT.exists(), 'Additive immutable certificate already exists'
    metadata = pd.read_csv(MIKL, usecols=['gene name', 'position in 3UTR', 'subset', SEQ])
    core = pd.read_csv(CORE, usecols=['dataset', 'mutant_id'])
    ids = set(core.loc[core.dataset.eq('mikl_gse173098'), 'mutant_id'])
    lineage = pd.read_csv(LINEAGE, usecols=['source_row', 'mutant_id', 'parent_sequence', 'mutant_sequence', 'parent_barcode_construct_count'])
    selected = lineage[lineage.mutant_id.isin(ids)]
    assert selected.mutant_id.is_unique and set(selected.mutant_id) == ids and len(ids) == 6901
    metadata['insert'] = metadata[SEQ].str.upper().str.slice(30, 180)
    wt = metadata[metadata.subset.eq('wt scanning 50')]
    mutant = metadata[metadata.subset.eq('mut scanning 50')]
    assert len(wt) == 13753 and len(mutant) == 12909
    groups = {(str(gene), position): group for (gene, position), group in wt.groupby(['gene name', 'position in 3UTR'], dropna=False)}
    min_distances, max_distances, same_barcode = [], [], 0
    for row in selected.itertuples():
        source = metadata.loc[int(row.source_row)]
        assert source['subset'] == 'mut scanning 50' and source['insert'] == row.mutant_sequence
        parents = groups[(str(source['gene name']), source['position in 3UTR'])]
        parents = parents[parents['insert'].eq(row.parent_sequence)]
        assert len(parents) == row.parent_barcode_construct_count
        full = source[SEQ].upper()
        distances = [sum(a != b for a, b in zip(full, parent.upper())) for parent in parents[SEQ]]
        assert all(len(parent) == 198 for parent in parents[SEQ])
        min_distances.append(min(distances)); max_distances.append(max(distances))
        same_barcode += int(any(full[18:30] == parent.upper()[18:30] for parent in parents[SEQ]))
    core_constants = {name: {'prefix18': sorted(set(frame[SEQ].str.upper().str[:18])),
                            'suffix18': sorted(set(frame[SEQ].str.upper().str[-18:])), 'count': len(frame)}
                      for name, frame in [('WT_scanning50', wt), ('mutant_scanning50', mutant)]}
    assert core_constants['WT_scanning50']['prefix18'] == ['CGAAATGGGCCGCATTGC']
    assert core_constants['WT_scanning50']['suffix18'] == ['CACTGCGGCTGATGACGA']
    assert core_constants['mutant_scanning50']['prefix18'] == ['GACAGATGCGCCGTGGAT']
    assert core_constants['mutant_scanning50']['suffix18'] == ['AGCCACCCGATCCAATGC']
    author = pd.read_csv(AUTHOR, usecols=['varseq_final', 'barcode'])
    assert author.barcode.str.len().eq(14).all() and author.barcode.eq(author.varseq_final.str[16:30]).all()
    prefixes, suffixes, n = Counter(), Counter(), 0
    for key, seq in records(FASTA):
        if key.endswith('+mut'):
            seq = seq.upper()
            assert len(seq) == 300
            prefixes[seq[:20]] += 1; suffixes[seq[-20:]] += 1; n += 1
    assert n == 17294 and prefixes == Counter({'GCTTCGATATCCGCATGCTA': n})
    assert suffixes == Counter({'CTCTTGCGGTCGCACTAGTG': n})
    example = ROOT / 'data/external/RNAloc_MPRA/example_data/examplefastqfile_R2_001.fastq.gz'
    example_sequences = []
    with gzip.open(example, 'rt') as stream:
        for index in range(3):
            stream.readline(); seq = stream.readline().strip(); stream.readline(); stream.readline()
            example_sequences.append({'fixed_index0': index, 'sequence': seq,
                                      'anchor_start0': seq.find('GAGCGCACCCGTCCGAGC')})
    p = core_constants['WT_scanning50']['prefix18'][0]; q = core_constants['mutant_scanning50']['prefix18'][0]
    s = core_constants['WT_scanning50']['suffix18'][0]; t = core_constants['mutant_scanning50']['suffix18'][0]
    sources = [MIKL, CORE, LINEAGE, AUTHOR, FASTA, example,
               ROOT / 'data/raw/mikl_gse173098/PMC9561380.html',
               ROOT / 'data/external/RNAloc_MPRA/LibraryDesign.ipynb',
               ROOT / 'data/external/RNAloc_MPRA/mapping_barcodes_and_umis.ipynb',
               ROOT / 'data/raw/moffatt_gse334718/code/LE_SHAPE_Summary/basic_structure_mutation.qmd',
               ROOT / 'data/raw/moffatt_gse334718/code/LE_SHAPE_Summary/shaped_based_oligo_design.qmd', Path(__file__)]
    receipt = {'status': 'PASS metadata and conditional DNA construction only', 'date': '2026-10-07',
               'outcome_columns_read': False, 'raw_counts_read': False, 'protected_outcomes_read': False,
               'biological_fits': False, 'complete_mature_RNA_certified': False,
               'source_sha256': {str(path.relative_to(ROOT)): digest(path) for path in sources},
               'Mikl': {'layout': [18, 12, 150, 18], 'constants': core_constants,
                        'admitted_unique_mutants': len(ids), 'full198_min_distance_range': [min(min_distances), max(min_distances)],
                        'full198_max_distance_range': [min(max_distances), max(max_distances)],
                        'any_same_barcode_parent_mutants': same_barcode,
                        'prefix18_hamming': sum(a != b for a, b in zip(p, q)),
                        'suffix18_hamming': sum(a != b for a, b in zip(s, t)),
                        'WT_cut': cutting_certificate(p, s), 'mutant_cut': cutting_certificate(q, t),
                        'author_prototype_dictionary': {'rows': len(author), 'barcode_length': 14, 'slice0_halfopen': [16, 30],
                                                        'not_exact_measured_library': True},
                        'fixed_first3_example_R2_sequences': example_sequences,
                        'example_sample_RNA_or_DNA_identity_certified': False},
               'Moffatt': {'mutation_records': n, 'synthesis_length': 300, 'central_variable_length': 260,
                           'PCR_handle_left': dict(prefixes), 'PCR_handle_right': dict(suffixes),
                           'retained_in_mature_RNA_certified': False},
               'primary_URLs': ['https://doi.org/10.1093/nar/gkac806', 'https://github.com/martinmikl/RNAloc_MPRA',
                               'https://www.thermofisher.com/order/catalog/product/ER1891',
                               'https://www.thermofisher.com/order/catalog/product/ER1191',
                               'https://doi.org/10.64898/2026.06.09.731215',
                               'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE334718']}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'Mikl_admitted_unique_mutants': len(ids), 'Moffatt_mutation_metadata_records': n,
                      'complete_mature_RNA_certified': False, 'certificate': str(OUT)}))


if __name__ == '__main__':
    main()
