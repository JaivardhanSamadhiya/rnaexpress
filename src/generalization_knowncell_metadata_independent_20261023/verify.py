"""Independent algorithms on supplied metadata only. No path, loader or probe.

No reference builder/parser is imported or called. Public counts and original
ID/order digest are fixed; small-count access is private and used only by tests.
"""
from collections import Counter
import hashlib
import json
import math
from .spec import *


def _sha(raw):return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()


def _hash(value):
    assert isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    return value


def _copy(value):
    if isinstance(value,dict):
        assert all(type(key) is str for key in value),'Supplied JSON keys must be strings'
        return {key:_copy(item) for key,item in value.items()}
    if isinstance(value,list):return [_copy(item) for item in value]
    assert value is None or type(value) in (str,int,float,bool),'Supplied JSON data only'
    if type(value) is float:assert math.isfinite(value),'Nonfinite supplied JSON number'
    return value


def _supplied(value):
    raw_sha=None
    if isinstance(value,bytes):
        assert len(value)<=MAX_SUPPLIED_BYTES,'Bounded supplied metadata JSON'
        raw_sha=_sha(value)
        def unique(pairs):
            result={}
            for key,item in pairs:
                assert key not in result,'Duplicate supplied JSON key'
                result[key]=item
            return result
        def nonfinite(value):raise AssertionError('Nonfinite supplied JSON token')
        value=json.loads(value.decode('utf-8-sig'),object_pairs_hook=unique,parse_constant=nonfinite)
    else:assert type(value) is dict,'Supply bundle bytes or a JSON dictionary, never a path'
    value=_copy(value)
    assert type(value) is dict
    assert len(_canonical(value))<=MAX_SUPPLIED_BYTES,'Bounded supplied metadata dictionary'
    return value,raw_sha


def _identity(rows):
    identifiers=[row['intervention_id'] for row in rows]
    ordered=[[row[column] for column in COLUMNS] for row in rows]
    # These are declared original hash formats, implemented independently.
    return _sha('|'.join(identifiers).encode()),_sha(json.dumps(ordered,separators=(',',':'),ensure_ascii=True).encode())


def _validate_rows(rows):
    assert type(rows) is list and rows
    identifiers=set();groups={};component_fold={};per_cell={cell:set() for cell in CELLS}
    for index,row in enumerate(rows):
        assert type(row) is dict and set(row)==set(COLUMNS),'Exactly metadata fields; no labels/scores'
        assert row['dataset']=='mikl_gse173098' and row['endpoint_class']=='projection'
        assert row['cell_type'] in CELLS
        assert type(row['held_parent_fold']) is int and row['held_parent_fold'] in FOLDS
        for key in COLUMNS:
            if key!='held_parent_fold':assert type(row[key]) is str and row[key].strip()
        identifier=row['intervention_id'];assert identifier not in identifiers,'Duplicate original ID'
        identifiers.add(identifier)
        component=row['biological_component'];fold=row['held_parent_fold']
        assert component not in component_fold or component_fold[component]==fold,'Component spans inherited folds'
        component_fold[component]=fold;per_cell[row['cell_type']].add(component)
        groups.setdefault(row['parent_context_id'],[]).append(index)
    assert per_cell[CELLS[0]]==per_cell[CELLS[1]],'Represented cells have different component rosters'
    for indices in groups.values():
        assert len(indices)>=2,'Every original menu needs at least two candidates'
        first=rows[indices[0]];mutants=set()
        for index in indices:
            row=rows[index]
            assert all(row[key]==first[key] for key in ('cell_type','biological_component','held_parent_fold','parent_sequence')),'Ambiguous original menu'
            assert row['mutant_sequence'] not in mutants,'Duplicate candidate sequence in menu'
            mutants.add(row['mutant_sequence'])
    return groups,component_fold


def _menus(rows,groups):
    # Construct menu signatures directly from retained global row indices.
    by_signature={}
    for context in sorted(groups):
        indices=groups[context];first=rows[indices[0]]
        signature=(first['biological_component'],first['parent_sequence'],
                   tuple(sorted(rows[index]['mutant_sequence'] for index in indices)))
        cells=by_signature.setdefault(signature,{})
        assert first['cell_type'] not in cells,'Ambiguous duplicate full menu in a cell'
        cells[first['cell_type']]=(context,first['held_parent_fold'])
    paired=[];unmatched=[]
    for signature,cells in sorted(by_signature.items()):
        if len(cells)==2:
            assert set(cells)==set(CELLS) and cells[CELLS[0]][1]==cells[CELLS[1]][1]
            paired.append({'biological_component':signature[0],'parent_sequence':signature[1],
                'mutant_sequences':list(signature[2]),'gene_fold':cells[CELLS[0]][1],
                'contexts':{cell:cells[cell][0] for cell in CELLS}})
        else:
            assert len(cells)==1
            unmatched.append(next(iter(cells.values()))[0])
    return paired,sorted(unmatched)


def _partition(rows,universe,held_fold,groups):
    """Global-index masks; BOTH held cells establish component/allele exclusions."""
    held=[index for index in universe if rows[index]['held_parent_fold']==held_fold]
    assert held
    held_components={rows[index]['biological_component'] for index in held}
    source=[index for index in universe if rows[index]['held_parent_fold']!=held_fold
            and rows[index]['biological_component'] not in held_components]
    assert source and set(source).isdisjoint(held)
    assert set(source)|set(held)==set(universe),'No silent additional filtering'
    for indices in (source,held):
        assert {rows[index]['cell_type'] for index in indices}==set(CELLS)
        selected=set(indices)
        for menu in groups.values():
            overlap=selected.intersection(menu)
            assert not overlap or len(overlap)==len(menu),'Partial original menu'
    def genes(indices):return {rows[index]['gene_transcript'].strip().upper() for index in indices}
    def alleles(indices):return {rows[index][column] for index in indices for column in ('parent_sequence','mutant_sequence')}
    assert not genes(source).intersection(genes(held)),'Gene contradiction: stop, no extra purge'
    assert not alleles(source).intersection(alleles(held)),'Allele contradiction: stop, no extra purge'
    return source,held


def _rebuild(rows):
    groups,component_fold=_validate_rows(rows)
    paired,unmatched=_menus(rows,groups)
    universe=list(range(len(rows)));splits=[];outer_coverage=Counter()
    assert set(row['held_parent_fold'] for row in rows)==set(FOLDS)
    for outer in FOLDS:
        source,held=_partition(rows,universe,outer,groups);outer_coverage.update(held)
        inner=[];inner_coverage=Counter()
        for validation in FOLDS:
            if validation==outer:continue
            training,testing=_partition(rows,source,validation,groups)
            inner_coverage.update(testing)
            inner.append({'validation_fold':validation,'training_indices':training,'validation_indices':testing})
        assert set(inner_coverage)==set(source) and all(count==1 for count in inner_coverage.values()),'Source OOF coverage is not exactly once'
        splits.append({'outer_fold':outer,'training_indices':source,'target_indices':held,'inner':inner})
    assert set(outer_coverage)==set(universe) and all(count==1 for count in outer_coverage.values())
    paired_contexts={context for pair in paired for context in pair['contexts'].values()}
    assert paired_contexts.isdisjoint(unmatched) and paired_contexts|set(unmatched)==set(groups)
    assert {pair['biological_component'] for pair in paired}==set(component_fold),'Primary paired cohort must retain every component'
    counts={'all_rows':len(rows),'CAD_rows':sum(row['cell_type']==CELLS[0] for row in rows),
        'Neuro-2a_rows':sum(row['cell_type']==CELLS[1] for row in rows),'components':len(component_fold),
        'paired_menus':len(paired),'paired_rows':sum(len(groups[context]) for context in paired_contexts),
        'paired_contexts':len(paired_contexts),'paired_directional_decisions':2*len(paired_contexts),
        'unmatched_contexts':len(unmatched),'unmatched_rows':sum(len(groups[context]) for context in unmatched)}
    ids_sha,metadata_sha=_identity(rows)
    contract={'row_ids_sha256':ids_sha,'metadata_sha256':metadata_sha,'splits':splits,'pairs':paired,'unmatched_contexts':unmatched}
    return contract,counts


def _check_supplied(value,expected_counts,expected_ids_sha,expected_core_rows=ALL_CORE_ROWS):
    """Private count parameter exists only for the invented test fixture."""
    bundle,raw_sha=_supplied(value)
    assert bundle['status']=='PASS_GUARDED_MIKL_METADATA_NO_LABEL_OR_ARRAY_ADMISSION'
    for field in ('numeric_outcome_rows_admitted','actual_feature_reads','models_fitted'):
        assert type(bundle[field]) is int and bundle[field]==0
    assert bundle['metadata_admission_sha256']==METADATA_ADMISSION_SHA and bundle['core_sha256']==CORE_SHA
    assert bundle['declared_simple102_sha256_not_loaded']==NPZ_SHA
    supplied=bundle['metadata'];rows=supplied['rows']
    contract,counts=_rebuild(rows)
    assert counts==expected_counts,'Frozen full-project metadata counts differ'
    assert contract['row_ids_sha256']==_hash(expected_ids_sha),'Original fixed ID/order digest differs'
    assert supplied['row_ids_sha256']==contract['row_ids_sha256'] and supplied['metadata_sha256']==contract['metadata_sha256']
    assert _canonical(bundle['contract'])==_canonical(contract),'Saved metadata/menu/split contract differs from independent reconstruction'
    assert supplied['all_core_rows']==expected_core_rows
    _hash(supplied['all_core_ids_sha256']) # Declared full-core digest, not independently reconstructible here.
    positions=supplied['original_core_rows']
    assert type(positions) is list and len(positions)==len(rows)
    assert all(type(position) is int and 0<=position<expected_core_rows for position in positions)
    assert positions==sorted(set(positions)),'Original source positions must retain sorted unique order'
    assert supplied['logical_metadata_fields']==list(COLUMNS)
    for key in ('one_csv_record_per_physical_line','whole_file_raw_bytes_traversed','unused_csv_fields_tokenized'):
        assert supplied[key] is True
    assert supplied['numeric_outcome_columns_parsed'] is False and supplied['outcome_values_returned'] is False
    return {'counts':counts,'row_ids_sha256':contract['row_ids_sha256'],'metadata_sha256':contract['metadata_sha256'],
        'reconstructed_contract':contract,'canonical_contract_sha256':_sha(_canonical(contract)),
        'supplied_bytes_sha256':raw_sha,'supplied_canonical_bundle_sha256':_sha(_canonical(bundle)),
        'outer_masks_rebuilt':3,'inner_masks_rebuilt':6,'both_cells_used_for_every_purge':True,
        'source_and_target_full_menus_preserved':True,'original_row_order_preserved':True,
        'extra_filtering_or_gene_alias_repair':False,'reference_builder_or_parser_called':False,
        'metadata_rows_normalized_or_modified':False,'parsed_outcome_values':0,
        'original_core_position_alignment_independently_verified':False,
        'nonMikl_full_core_ID_roster_independently_verified':False,
        'source_CSV_metadata_derivation_independently_verified':False,
        'author_biological_lineage_independently_verified':False,
        'actual_source_bytes_Git_owner_and_resource_admission_verified':False,
        'array_label_or_FIT_permission_granted':False,'model_fits':0}


def verify_bundle(value):
    """Public fixed13781-row verifier. Accept supplied JSON only; never opens IO."""
    result=_check_supplied(value,COUNTS,ROW_IDS_SHA)
    result['status']=STATUS
    result['requires_separate_owned_worker_admission_and_committed_result']=True
    return result
