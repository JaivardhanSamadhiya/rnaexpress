"""Persist metadata-only findings; no localization outcome parsing."""
from .common import ROOT,sha256,write_json,write_new
import collections,csv,io,json,re,zipfile


def run():
    data=ROOT/'data/external/research_20260921';out=ROOT/'results/research_20260921'
    rows=list(csv.DictReader((out/'mutrel_sequence_metadata.tsv').open(),delimiter='\t'))
    internal=[r for r in rows if r['site'].isdigit() and 19<=int(r['site'])<=143]
    counts=collections.Counter('substitution' if '>' in r['mutation'] else 'deletion' for r in internal)
    assets=['mutrel_experiment.xml','mutrel_run.xml','mutrel_sample.xml','mutrel_submitted.json',
            'mutrel_sample_table.xlsx']
    write_json(out/'mutrel_admission_20260923.json',{
        'internal_positions_one_based':[19,143],'internal_event_entries':len(internal),
        'internal_mutation_types':dict(counts),'published_components_match':dict(counts)=={'substitution':374,'deletion':85},
        'caption_arithmetic_note':'Caption states 469 overall, but its 374 substitutions plus 85 deletions sum to 459; table agrees with the component counts.',
        'sample_table':'Official Supplementary Table 1 supplies reporter, cell type and insert size, but no barcode-to-fraction mapping.',
        'archive_metadata':'One paired run, two application reads, no supplied index reads or submitted-file download links. XML records have no recovered fraction barcode mapping.',
        'prefix_structure':'Observed forward reads begin GATGTC + T + 5AI exon-junction primer; reverse-oriented prefixes include ACTGAC/TGCTGA/CAGATG/GTACCT before the NXF1 reverse-primer region. These are sequence observations, not assigned compartment labels.',
        'admission':'Not admitted for isolated-mutation intervention scoring. Co-occurrence filtering and barcode-to-fraction mapping remain unresolved.',
        'numeric_compartment_counts_read':False,
        'files':{str((data/n).relative_to(ROOT)).replace('\\','/'):sha256(data/n) for n in assets}})
    z=zipfile.ZipFile(data/'speckle2026_epmc_supplement')
    zz=zipfile.ZipFile(io.BytesIO(z.read('gkag174_supplemental_files.zip')))
    gb=zipfile.ZipFile(io.BytesIO(zz.read('Supplementary Data S1.zip')))
    constructs=[]
    for name in gb.namelist():
        if not name.startswith('M_') or not name.endswith('.gb'):continue
        text=gb.read(name).decode();sequence=re.sub('[^a-zA-Z]','',text.split('ORIGIN')[1].split('//')[0]).upper()
        promoter=re.search(r'promoter\s+(\d+)\.\.(\d+)\s+/label="minimal CMV promoter"',text)
        poly=re.search(r'misc_feature\s+(\d+)\.\.(\d+)\s+/label="SV40 polyA sequence"',text)
        if promoter is None or poly is None or tuple(map(int,promoter.groups()))!=(322,360):raise ValueError('Unexpected construct annotation')
        end=int(poly[1])-1;insert=sequence[360:end]
        if not insert or set(insert)-set('ACGT'):raise ValueError('Invalid cassette')
        constructs.append({'construct':name[:-3],'plasmid_start_one_based':361,'plasmid_end_one_based':end,
                           'sequence':insert,'length':len(insert),
                           'interpretation':'promoter-downstream/pre-polyA interval; not a verified full RNA transcript'})
    collisions={}
    for k in (1,2,3):
        groups=collections.defaultdict(list)
        for row in constructs:
            s=row['sequence'];key=tuple(sorted(collections.Counter(s[j:j+k] for j in range(len(s)-k+1)).items()))
            groups[key].append(row['construct'])
        collisions[str(k)]=[v for v in groups.values() if len(v)>1]
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(constructs[0]),lineterminator='\n')
    w.writeheader();w.writerows(constructs)
    write_new(out/'speckle2026_prepolyA_intervals.csv',stream.getvalue().encode())
    write_json(out/'speckle_admission_20260923.json',{'minimal_constructs':len(constructs),
        'length_range':[min(r['length'] for r in constructs),max(r['length'] for r in constructs)],
        'exact_kmer_count_collision_groups':collisions,
        'outcome_values_read':False,'source_sha256':sha256(data/'speckle2026_epmc_supplement'),
        'decision':'Do not use as same-endpoint nuclear/cytoplasmic confirmation. Construct intervals recovered but true transcript ends/cryptic splicing and measurement mapping remain unresolved. No exact di-/trinucleotide count collisions support the considered representation-collision analysis.'})
    write_json(out/'shukla2018_ungapped_recovery_failure.json',{
        'admission':False,'reason':'Ungapped overlap assembly failed author-reference validation; no recovered full-length insert table admitted.',
        'FIRRE_reference_positions_compared':1479,'FIRRE_reference_mismatches':157,
        'FIRRE_demo_length':2928,'DANCR_demo_vs_metadata_lengths':[904,855],
        'XIST_demo_vs_metadata_lengths':[19275,19280],
        'numeric_localization_outcomes_read':False,
        'intermediate_file':'results/research_20260921/shukla2018_tile90_consensus.csv',
        'interpretation':'Many raw-read differences include apparent indels; high within-barcode consensus does not prove the intended oligo sequence. Reference-assisted admission is a separately recorded method.'})
    print('Recorded mutREL and speckle metadata admission findings and rejected ungapped recovery.',flush=True)


if __name__=='__main__':run()
