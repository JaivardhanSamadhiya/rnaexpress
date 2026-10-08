"""Additive direct-reference coordinate replay; frozen v1 code stays untouched."""
from . import audit as a
from collections import Counter
import hashlib, json

def read(path): return json.loads(path.read_text())

def exon_coordinate_order(record):
    """Independent ordered intervals; admit only coding-transcript 3UTR bases."""
    left=[int(v) for v in record['exonStarts'].split(',') if v]
    right=[int(v) for v in record['exonEnds'].split(',') if v]
    assert len(left)==len(right)==record['exonCount'] and record['cdsStart']<record['cdsEnd']
    assert all(x<y for x,y in zip(left,right)) and all(right[i]<=left[i+1] for i in range(len(left)-1))
    intervals=list(zip(left,right))
    if record['strand']=='-': intervals.reverse()
    positions=[]
    for start,end in intervals:
        if record['strand']=='+': positions.extend(range(max(start,record['cdsEnd']),end))
        else: positions.extend(range(min(end,record['cdsStart'])-1,start-1,-1))
    return positions

def direct_reference(genomic,start,positions,strand):
    assert strand in ('+','-') and all(start<=p<start+len(genomic) for p in positions)
    complement={'A':'T','C':'G','G':'C','T':'A','N':'N'}
    return ''.join(genomic[p-start] if strand=='+' else complement[genomic[p-start]] for p in positions)

def run():
    a.certify(); completed=read(a.OUT/'pilot_mapping_receipt.json')
    assert completed['status']=='COMPLETED_COORDINATE_FEASIBILITY_ONLY'
    for name,expected in completed['files'].items(): assert a.sha(a.ROOT/name)==expected
    remote=[]; sequence_records={}; annotation_records={}
    for path in sorted((a.ART/'public_metadata').glob('*.receipt.json')):
        item=read(path); target=path.with_name(path.name[:-len('.receipt.json')])
        assert item['http_status']==200 and a.sha(target)==item['sha256'] and target.stat().st_size==item['bytes']
        remote.append({'receipt':path.relative_to(a.ROOT).as_posix(),'url':item['url'],'http_status':200,'bytes':item['bytes'],'sha256':item['sha256']})
        data=read(target)
        if path.name.endswith('_sequence.json.receipt.json'):
            sequence_records[(data['chrom'],data['start'],data['end'])]=data['dna'].upper()
        if path.name.endswith('_knownGene.json.receipt.json'):
            annotation_records[(data['chrom'],data['start'],data['end'])]={r['name']:r for r in data['knownGene']}
    original={(r['dataset'],r['parent_id']):r for r in read(a.OUT/'pilot_parent_metadata.json')}
    mapped=read(a.OUT/'pilot_parent_mappings.json'); parent_index={}; matches=0; strands=Counter()
    for p in mapped:
        o=original[(p['dataset'],p['parent_id'])]; assert o['parent_sequence']==p['parent_sequence']
        vectors=set()
        for m in p['matches']:
            refs=[r for r in o['reference_candidates'] if r['transcript_id']==m['transcript'].split('.')[0]]
            assert refs and m['assembly']=='mm10'
            ref=refs[0]; key=(m['chrom'],ref['gene_start1']-1,ref['gene_end1'])
            record=annotation_records[key][m['transcript']]; positions=exon_coordinate_order(record)
            vector=m['positions0']; offset=positions.index(vector[0])
            assert positions[offset:offset+len(vector)]==vector and len(vector)==len(p['parent_sequence'])
            assert direct_reference(sequence_records[key],key[1],vector,record['strand'])==p['parent_sequence']
            assert record['strand']==m['strand']
            vectors.add((m['chrom'],m['strand'],tuple(vector))); matches+=1
        expected='reference_site_vector_unique' if len(vectors)==1 else ('ambiguous_reference_site_vectors' if vectors else o['status'] if not o['reference_candidates'] else 'no_exact_reference_vector')
        assert p['mapping_status']==expected
        if len(vectors)==1: strands[next(iter(vectors))[1]]+=1
        parent_index[(p['dataset'],p['parent_id'])]=(p,vectors)
    roster=a.pd.read_csv(a.OUT/'pilot_candidate_metadata.csv.gz',usecols=a.COLS+a.GENES[1:],low_memory=False)
    edited=read(a.OUT/'pilot_edited_site_metadata.json'); assert [r['intervention_id'] for r in edited]==list(roster.intervention_id)
    unique_sites=set(); site_count=0; row_counts=Counter(); parent_counts=Counter()
    for p in mapped: parent_counts[(p['dataset'],p['mapping_status'])]+=1
    for r,record in zip(roster.itertuples(index=False),edited):
        parent,vectors=parent_index[(r.dataset,r.parent_id)]
        assert record['mapping_status']==parent['mapping_status'] and record['dataset']==r.dataset and record['gene']==r.gene_transcript and record['parent_id']==r.parent_id
        changed=[i for i,(x,y) in enumerate(zip(r.parent_sequence,r.mutant_sequence)) if x!=y]
        assert record['edit_positions0']==changed and len(r.parent_sequence)==len(r.mutant_sequence)
        if len(vectors)!=1: assert not record['edited_site_coordinates']
        else:
            chrom,strand,positions=next(iter(vectors)); assert len(record['edited_site_coordinates'])==len(changed)
            complement={'A':'T','C':'G','G':'C','T':'A'}
            for i,site in zip(changed,record['edited_site_coordinates']):
                assert site['insert_position0']==i and site['chrom']==chrom and site['strand']==strand and site['genomic_position0']==positions[i]
                assert site['expressed_reference']==r.parent_sequence[i] and site['expressed_alternate']==r.mutant_sequence[i]
                assert site['genomic_reference']==(r.parent_sequence[i] if strand=='+' else complement[r.parent_sequence[i]])
                assert site['genomic_alternate']==(r.mutant_sequence[i] if strand=='+' else complement[r.mutant_sequence[i]])
                unique_sites.add((chrom,positions[i])); site_count+=1
        row_counts[(r.dataset,record['mapping_status'])]+=1
    assert matches and completed['coordinate_unique_interventions']==sum(count for (d,s),count in row_counts.items() if s=='reference_site_vector_unique')
    a.certify()
    a.jsave(a.OUT/'independent_coordinate_replay_receipt.json',{'status':'PASS_COORDINATE_REPLAY_ONLY','parents_checked':len(mapped),'candidate_rows_checked':len(roster),
        'transcript_match_vectors_checked':matches,'unique_parent_strand_counts':dict(strands),'candidate_edited_site_records_checked':site_count,'unique_forward_genome_edited_sites':len(unique_sites),
        'parent_status_by_dataset':{d:{s:c for (x,s),c in parent_counts.items() if x==d} for d in sorted({x for x,s in parent_counts})},
        'row_status_by_dataset':{d:{s:c for (x,s),c in row_counts.items() if x==d} for d in sorted({x for x,s in row_counts})},
        'pilot_mapping_receipt_sha256':a.sha(a.OUT/'pilot_mapping_receipt.json'),'replay_source_sha256':a.sha(__file__),
        'public_responses_verified':remote,'direct_genomic_sequence_exon_strand_and_every_edit_replay':True,'source_preservation_before_and_after':True,
        'outcomes_read':False,'conservation_scores_read':False,'models_fit':0,'global_genome_uniqueness_or_biological_isoform_certified':False,
        'v1_transport_resume_limitation':'HTTP0 receipt lacks cache bytes; original v1 resume would fail sha(path). Fresh first pilot allHTTP200; no retries performed. Any later retry requires additive corrected helper/tests/freeze.'})
    print(json.dumps({'parents':len(mapped),'rows':len(roster),'match_vectors':matches,'edited_site_records':site_count,'unique_genome_sites':len(unique_sites),'strands':dict(strands),'row_status':{d:{s:c for (x,s),c in row_counts.items() if x==d} for d in sorted({x for x,s in row_counts})}},indent=2),flush=True)

if __name__=='__main__':run()
