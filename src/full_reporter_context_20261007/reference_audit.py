"""Bounded public reference retrieval; no outcomes, fits or production inputs.

Reference sequence mappings constrain a plausible construct design. They never
certify the authors' physical clone, transcription endpoints or RNA isoforms.
"""
from pathlib import Path
import datetime,hashlib,json,re,sys,urllib.request,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
NS='full_reporter_context_20261007'
ART=ROOT/'artifacts'/NS
EXT=ROOT/'data/external'/NS
OLIGOS=ROOT/'artifacts/generalization_20261007/reporter_context_metadata.json'


def digest(data):return hashlib.sha256(data).hexdigest()


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data
    else:path.write_bytes(data)


def jsave(path,data):save(path,(json.dumps(data,sort_keys=True,indent=2)+'\n').encode())


def methods():
    article=ROOT/'data/external/research_20260921/srle_article'
    known=json.loads(OLIGOS.read_text())
    assert digest(article.read_bytes())==known['source_files']['srle_article']['sha256']
    root=ET.fromstring(article.read_bytes())
    selected=[]
    for sec in root.findall('.//sec'):
        title=sec.find('title')
        if title is None:continue
        name=''.join(title.itertext())
        if any(word in name.lower() for word in ('plasmid','construction','qpcr','fractionation','library preparation')):
            selected.append({'section':name,'paragraph_count':len(sec.findall('p'))})
            print(name,flush=True)
    reference=next(ref for ref in root.findall('.//ref') if ref.attrib.get('id')=='B39')
    citation_doi=next(e.attrib.get('{http://www.w3.org/1999/xlink}href') for e in reference.findall('.//ext-link')
        if e.attrib.get('ext-link-type')=='doi')
    jsave(ART/'srle_construction_methods.json',{'status':'AUTHOR_METADATA_ONLY',
        'source_sha256':digest(article.read_bytes()),'sections':selected,
        'construction_reference39_doi':citation_doi,'outcomes_opened':False,
        'methods_summary':{'backbone':'pEGFP-N1 (Clontech)',
            'assembly':'PCR linearization and Gibson assembly of amplified genomic HBB or spliced blood cDNA',
            'library':'Random six-base insert placed downstream of the HBB coding region using TableS1 overlaps',
            'sequencing_scope':'RNA reverse transcription followed by PCR of six-mer and its local flanks; transcript ends and splice junctions are not sequenced by this design',
            'cell_fractionation':'HEK293T nuclear and cytoplasmic fractions'}})
    print('Construction reference39 DOI:',citation_doi,flush=True)


def retrieve():
    # These are pinned public reference records, not the experimental clones.
    for accession in ('U55762.1','NM_000518.5','NG_000007.3'):
        path=EXT/(accession+'.gb')
        url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id='+accession+'&rettype=gb&retmode=text'
        if path.exists():
            receipt=json.loads((EXT/(accession+'.receipt.json')).read_text())
            assert receipt['sha256']==digest(path.read_bytes())
            print('Cached',accession,flush=True);continue
        request=urllib.request.Request(url,headers={'User-Agent':'RNAExpress-author-metadata-audit/1.0'})
        with urllib.request.urlopen(request,timeout=30) as response:
            data=response.read(1000000);final=response.url;status=response.status
        assert len(data)<1000000 and data.startswith(b'LOCUS') and b'ORIGIN' in data
        assert ('VERSION     '+accession).encode() in data
        save(path,data)
        jsave(EXT/(accession+'.receipt.json'),{'accession_version':accession,
            'url':url,'final_url':final,'status':status,'bytes':len(data),'sha256':digest(data),
            'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'repository':'NCBI Nucleotide public reference record','authentication':False,
            'payment_or_account_required':False,'scope':'Reference sequence/annotation only; not author clone certification'})
        print('Retrieved',accession,len(data),'bytes',flush=True)


def rc(sequence):return sequence.translate(str.maketrans('ACGTN','TGCAN'))[::-1]


def read_record(accession):
    path=EXT/(accession+'.gb');payload=path.read_bytes()
    receipt=json.loads((EXT/(accession+'.receipt.json')).read_text())
    assert digest(payload)==receipt['sha256']
    text=payload.decode()
    sequence=re.sub('[^a-z]','',text.split('ORIGIN',1)[1].split('//',1)[0]).upper()
    length=int(re.search(r'^LOCUS\s+\S+\s+(\d+)\s+bp',text,re.M).group(1))
    assert len(sequence)==length and not set(sequence)-set('ACGTN')
    return sequence,text


def hits(sequence,word):
    return [{'start_1based':m.start()+1,'end_1based_inclusive':m.start()+len(word)}
        for m in re.finditer('(?='+re.escape(word)+')',sequence)]


def feature_block(text,kind,qualifier):
    features=text.split('FEATURES',1)[1].split('ORIGIN',1)[0]
    blocks=re.split(r'(?m)(?=^     [A-Za-z_]+\s)',features)
    found=[block.strip() for block in blocks if re.match(kind+r'\s',block.strip()) and qualifier in block]
    assert len(found)==1,(kind,qualifier,len(found))
    return found[0]


def mapping():
    metadata=json.loads(OLIGOS.read_text())
    assert digest(OLIGOS.read_bytes())=='e7ee4fea706d3b7e611f63d491304cfe835efcd3c9b6a9a4f0282abf384f725c'
    primers={name:value['sequence_5prime_to_3prime_dna'] for name,value in metadata['primer_metadata'].items()}
    vector,vector_text=read_record('U55762.1')
    transcript,transcript_text=read_record('NM_000518.5')
    genome,genome_text=read_record('NG_000007.3')
    mapped={}
    for accession,sequence,names in [
        ('U55762.1',vector,['N1 linear Primers F','N1 linear Primers R','N1-HBB linear Primers F']),
        ('NG_000007.3',genome,['HBB Primers F','HBB Primers R','HBB_qPCR F','HBB_qPCR R']),
        ('NM_000518.5',transcript,['spliced HBB Primers F','spliced HBB Primers R','HBB Primers F','HBB Primers R','HBB_qPCR F','HBB_qPCR R']),
    ]:
        mapped[accession]={name:{'oligo_plus_hits':hits(sequence,primers[name]),
            'oligo_reverse_complement_hits':hits(sequence,rc(primers[name]))} for name in names}
    f=mapped['NG_000007.3']['HBB Primers F']['oligo_plus_hits']
    r=mapped['NG_000007.3']['HBB Primers R']['oligo_reverse_complement_hits']
    assert len(f)==len(r)==1 and f[0]['start_1based']<r[0]['start_1based']
    amplicon=genome[f[0]['start_1based']-1:r[0]['end_1based_inclusive']]
    tf=mapped['NM_000518.5']['spliced HBB Primers F']['oligo_plus_hits']
    tr=mapped['NM_000518.5']['spliced HBB Primers R']['oligo_reverse_complement_hits']
    assert len(tf)==len(tr)==1
    cDNA=transcript[tf[0]['start_1based']-1:tr[0]['end_1based_inclusive']]
    hbb_mrna=feature_block(genome_text,'mRNA','/transcript_id="NM_000518.5"')
    segments=[tuple(map(int,pair)) for pair in re.findall(r'(\d+)\.\.(\d+)',hbb_mrna.split('/gene=',1)[0])]
    assert len(segments)==3
    spliced=''.join(genome[a-1:b] for a,b in segments)
    assert spliced==transcript,'Pinned RefSeq genomic/transcript records disagree'
    spliced_amplicon=''.join(genome[max(a,f[0]['start_1based'])-1:min(b,r[0]['end_1based_inclusive'])]
        for a,b in segments if max(a,f[0]['start_1based'])<=min(b,r[0]['end_1based_inclusive']))
    assert spliced_amplicon==transcript[:496] and cDNA==transcript[:494]
    reference_CDS=feature_block(transcript_text,'CDS','/gene="HBB"')
    CDS_bounds=tuple(map(int,re.search(r'CDS\s+(\d+)\.\.(\d+)',reference_CDS).groups()))
    assert CDS_bounds==(51,494)
    vf=mapped['U55762.1']['N1 linear Primers F']['oligo_plus_hits']
    vr=mapped['U55762.1']['N1 linear Primers R']['oligo_reverse_complement_hits']
    assert len(vf)==len(vr)==1
    excluded=(vr[0]['end_1based_inclusive']+1,vf[0]['start_1based']-1)
    egfp=feature_block(vector_text,'CDS','/gene="egfp"')
    egfp_bounds=tuple(map(int,re.search(r'CDS\s+(\d+)\.\.(\d+)',egfp).groups()))
    assert excluded[0]<=egfp_bounds[0] and excluded[1]>=egfp_bounds[1]
    right=metadata['local_design']['right_20nt_dna']
    assert len(hits(vector,right))==1 and not hits(genome,right) and not hits(transcript,right)
    left=metadata['local_design']['left_20nt_dna']
    assert amplicon.endswith(left)
    native_site=feature_block(transcript_text,'polyA_site','/gene="HBB"')
    poly_signal=feature_block(transcript_text,'regulatory','/regulatory_class="polyA_signal_sequence"')
    context={
        'status':'REFERENCE_AND_AUTHOR_DESIGN_JUNCTIONS_CERTIFIED_NOT_EXPRESSED_TRANSCRIPT',
        'coordinate_convention':'All intervals 1-based inclusive in pinned accession orientation',
        'source_reference_records':{accession:{'length_nt':len(sequence),'sequence_sha256':digest(sequence.encode()),
            'genbank_sha256':digest((EXT/(accession+'.gb')).read_bytes())}
            for accession,sequence in [('U55762.1',vector),('NM_000518.5',transcript),('NG_000007.3',genome)]},
        'author_primer_certificate_sha256':digest(OLIGOS.read_bytes()),'primer_mappings':mapped,
        'HBB_reference_genomic_amplicon':{'start':f[0]['start_1based'],'end':r[0]['end_1based_inclusive'],
            'length_nt':len(amplicon),'sequence_sha256':digest(amplicon.encode()),
            'scope':'NG_000007.3 sequence between exact author primers; actual donor allele unverified'},
        'HBB_reference_cDNA_amplicon':{'start':tf[0]['start_1based'],'end':tr[0]['end_1based_inclusive'],
            'length_nt':len(cDNA),'sequence_sha256':digest(cDNA.encode()),
            'scope':'NM_000518.5 sequence between exact author primers; actual donor cDNA unverified'},
        'HBB_canonical_reference_exons':segments,'HBB_canonical_reference_exon_join_equals_NM_000518_5':True,
        'HBB_reference_CDS_1based':CDS_bounds,
        'HBB_genomic_amplicon_after_annotated_reference_splicing':{
            'NM_000518_5_interval_1based':[1,496],'length_nt':len(spliced_amplicon),
            'sequence_sha256':digest(spliced_amplicon.encode()),'native_3UTR_retained_nt':2},
        'HBB_cDNA_amplicon_native_3UTR_retained_nt':0,
        'native_HBB_reference_polyA_signal_and_site_outside_both_cloning_amplicons':True,
        'HBB_native_reference_polyA_site':native_site,'HBB_native_reference_polyA_signal':poly_signal,
        'N1_linearization_reference_removed_interval':excluded,'reference_EGFP_CDS':egfp_bounds,
        'EGFP_complete_CDS_removed_by_reference_design':True,
        'library_right_arm_unique_vector_match':hits(vector,right),
        'library_right_arm_absent_from_HBB_references':True,
        'library_left_arm_is_HBB_amplicon_endpoint':True,
        'inference':'The 46nt library oligo bridges HBB-to-vector; its right arm is downstream vector sequence, not native HBB UTR.',
        'full_author_clone_sequence_certified':False,'full_expressed_pre_or_mature_RNA_certified':False,
        'production_inputs_changed':False,'outcomes_opened':False,'fits_run':False,
    }
    jsave(ART/'reference_junction_certificate.json',context)
    save(ART/'HBB_NG_000007_3_author_primer_reference_amplicon.fasta',
         ('>NG_000007.3_author_primer_reference_amplicon_NOT_author_clone\n'+amplicon+'\n').encode())
    save(ART/'HBB_NM_000518_5_author_primer_reference_amplicon.fasta',
         ('>NM_000518.5_author_primer_reference_amplicon_NOT_author_clone\n'+cDNA+'\n').encode())
    print(json.dumps({'status':context['status'],'primer_mappings':mapped,
        'reference_genomic_length':len(amplicon),'reference_cDNA_length':len(cDNA),
        'removed_vector_interval':excluded,'right_arm_vector_match':hits(vector,right)},indent=2),flush=True)


if __name__=='__main__':{'methods':methods,'retrieve':retrieve,'mapping':mapping}[sys.argv[1]]()
