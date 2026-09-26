from .core import *
from src.research_20260921.srle_uniform_risk import existing_candidates


def run():
    manifest=readj(OLD/'checkpoint_receipt.json')['artifact_hashes']
    for name in ('robustness_predictions.csv','robustness_result.json','raw_replication_scores.csv','raw_swap_evaluation.csv'):
        expected=manifest.get('results/research_20260921/'+name)
        if expected is not None:assert sha256(OLD/name)==expected
    source=pd.read_csv(OLD/'robustness_predictions.csv',float_precision='round_trip')
    raw=pd.read_csv(OLD/'raw_replication_scores.csv',float_precision='round_trip').set_index('kmer')
    original=pd.read_csv(OLD/'raw_swap_evaluation.csv')
    source['group']=keys(source.kmer)
    grouped=source.groupby('group').test.agg(['sum','count'])
    usable=set(grouped.index[(grouped['sum']>=2)&((grouped['count']-grouped['sum'])>=2)])
    source['scored']=source.test & source.group.isin(usable)
    for field in ('NRS1','NRS2','eligible'):source[field]=source.kmer.map(raw[field])
    assert len(source)==4096 and source.kmer.nunique()==4096 and source.scored.sum()==855
    source['biological_context']='shared_HBB_reporter_SRLE'
    source['full_reporter_sequence']=None
    source['full_sequence_status']='not established in admitted row-level input; local six-mer only'
    source['provenance_status']='PARTIAL raw-to-author-table chain; exact published-score mapping verified'
    roster=[]
    for parent in sorted(original.parent.unique()):
        group=keys([parent])[0]
        candidates=existing_candidates(parent,source.loc[source.scored & source.group.eq(group),'kmer'].tolist())
        assert all(raw.loc[[parent,*candidates],'eligible'])
        for mutant in candidates:
            a=source[source.kmer.eq(parent)].iloc[0]; b=source[source.kmer.eq(mutant)].iloc[0]
            pos=[i+1 for i,(x,y) in enumerate(zip(parent,mutant)) if x!=y]
            assert len(pos)==2 and counts([parent]).tolist()==counts([mutant]).tolist()
            roster.append({'parent':parent,'candidate':mutant,'original_local_sequence':parent,'edited_local_sequence':mutant,
                'full_parent_sequence':None,'full_mutant_sequence':None,'biological_context':'shared_HBB_reporter_SRLE',
                'edit_class':'composition-preserving six-nucleotide sequence swap / localized six-mer edit',
                'edited_window_length':6,'changed_bases':2,'changed_positions_1based':';'.join(map(str,pos)),
                'changed_position_span':max(pos)-min(pos)+1,'composition_before':group,'composition_after':group,'group':group,
                'parent_published':a.nrs,'candidate_published':b.nrs,'published_delta':b.nrs-a.nrs,
                'parent_rep1':a.NRS1,'candidate_rep1':b.NRS1,'rep1_delta':b.NRS1-a.NRS1,
                'parent_rep2':a.NRS2,'candidate_rep2':b.NRS2,'rep2_delta':b.NRS2-a.NRS2,
                'provenance_status':a.provenance_status,'roster_status':'original 592-anchor raw-covered roster; outcome-conditioned historical eligibility preserved'})
    roster=pd.DataFrame(roster)
    assert len(roster)==1744 and roster.parent.nunique()==592 and roster.group.nunique()==60
    splits=[]
    encoded=np.array([list(s) for s in source.kmer])
    for scheme in SCHEMES:
        for group in ([None] if scheme=='sequence_holdout' else sorted(usable)):
            train=training_mask(source,scheme,group)
            test=source.scored.to_numpy() & (True if group is None else source.group.eq(group).to_numpy())
            heldclass=source.test.to_numpy() if group is None else source.group.eq(group).to_numpy()
            distances=np.min((encoded[train,None,:]!=encoded[None,test,:]).sum(2),axis=0)
            assert not np.any(train & test)
            if scheme=='purged_composition_holdout':assert distances.min()>=3
            assert train.sum()>=200, 'Insufficient predefined training minimum'
            splits.append({'scheme':scheme,'held_group':group or 'original_hash','train_sequences':int(train.sum()),
                'scored_test_sequences':int(test.sum()),'excluded_held_group_sequences':int(heldclass.sum()),
                'train_composition_groups':source.loc[train,'group'].nunique(),'test_composition_groups':source.loc[test,'group'].nunique(),
                'composition_overlap':len(set(source.loc[train,'group'])&set(source.loc[test,'group'])),
                'exact_sequence_overlap':0,'minimum_train_test_hamming':int(distances.min()),
                'test_sequences_with_neighbor_within_two':int((distances<=2).sum()),
                'train_biological_contexts':1,'test_biological_contexts':1,'biological_context_overlap':1,
                'mask_sha256':hashlib.sha256(train.tobytes()+test.tobytes()).hexdigest()})
    csvsave(OUT/'sequence_inventory.csv',source)
    csvsave(ART/'srle_observation_inventory.csv',roster)
    csvsave(OUT/'split_inventory.csv',pd.DataFrame(splits))
    jsave(OUT/'inventory_receipt.json',{'sequences':4096,'scored_sequences':855,'score_groups':70,'candidate_edges':1744,'anchors':592,
        'candidate_groups':60,'biological_contexts':1,'constituent_replicate_pairs':2,
        'independent_biological_parent_contexts':1,'independent_candidate_edges':'not established; overlapping and reversed edges',
        'whole_library_hamming_one_connected_components':1,'component_basis':'complete ACGT^6 library; any sequence reaches AAAAAA by single-base steps',
        'full_sequence_available':False,'biological_family_ids_available':False,
        'inputs':{str((OLD/name).relative_to(ROOT)).replace('\\','/'):sha256(OLD/name) for name in ('robustness_predictions.csv','robustness_result.json','raw_replication_scores.csv','raw_swap_evaluation.csv')},
        'outputs':{str(p.relative_to(ROOT)).replace('\\','/'):sha256(p) for p in (OUT/'sequence_inventory.csv',ART/'srle_observation_inventory.csv',OUT/'split_inventory.csv')}})
    print(pd.DataFrame(splits).groupby('scheme').agg({'train_sequences':['min','max'],'minimum_train_test_hamming':'min','composition_overlap':'max'}).to_string())


if __name__=='__main__':run()
