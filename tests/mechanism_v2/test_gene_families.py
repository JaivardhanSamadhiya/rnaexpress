import pandas as pd
from src.mechanism_v2.gene_families import memberships,map_units,merge_family_components


def test_distinct_orthology_sources_and_exact_mapping():
    human=pd.DataFrame({'hgnc_id':['H1','H2'],'gene_group_id':['1|2','3']})
    mouse=pd.DataFrame({'hgnc_id':['H1','H2','H2'],'mouse_ensembl_gene':['E1','E2','E2'],
        'mouse_symbol':['Foo1','Bar2','Bar2'],'support':['A,A,B','A,B','C']})
    lookup,orth=memberships(human,mouse,3)
    assert ('id','E1') not in lookup  # repeated A is not three independent sources
    assert lookup[('id','E2')]=={'3'}
    metadata=pd.DataFrame({'biological_unit':['u','v','w'],'gene_id':['missing','E2.1','missing'],
        'gene_name':['FOO1','missing','Bar2']})
    mapped=map_units(metadata,lookup,orth)
    assert mapped.mapped.tolist()==[False,True,True]
    assert mapped.group_ids.tolist()==['','3','3']


def test_transitive_family_links_and_unannotated_unit_coverage():
    inv=pd.DataFrame({'biological_unit':['a','b','c','d'],'component':['a','b','c','c']})
    annotations=pd.DataFrame({'biological_unit':['a','b','c','d'],
        'group_ids':['1','1|2','2',''],'mapped':[True,True,True,False]})
    result,edges=merge_family_components(inv,annotations)
    assert result.family_component.nunique()==1 and len(edges)==2
    assert not result.family_eligible.any()  # unknown annotation is NOT a singleton family
