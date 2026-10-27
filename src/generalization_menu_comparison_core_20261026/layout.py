"""Pure metadata contracts. A returned plan is never an input admission."""
from collections import defaultdict
import hashlib
import json

STUDIES = ('astrocyte_gse330741', 'mikl_gse173098', 'moffatt_gse334718', 'srle')
ARMS = ('pairwise', 'margin_pair', 'menu_cost')
PENALTIES = (('pair_005', .005), ('pair_05', .05), ('pair_5', .5))
FIELDS = frozenset(('intervention_id', 'dataset', 'biological_component',
                    'parent_context_id', 'parent_sequence', 'mutant_sequence'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def metadata(rows):
    """Validate only explicit outcome-free dictionaries; retain supplied order."""
    rows = tuple(dict(row) for row in rows)
    require(bool(rows), 'empty metadata')
    contexts = defaultdict(list)
    ids = set()
    for i, row in enumerate(rows):
        require(set(row) == FIELDS, 'metadata must have exactly the six outcome-free fields')
        require(all(isinstance(v, str) and v for v in row.values()), 'empty/non-string metadata')
        require(row['dataset'] in STUDIES, 'unadmitted study name')
        require(row['intervention_id'] not in ids, 'duplicate intervention ID')
        ids.add(row['intervention_id'])
        parent, mutant = row['parent_sequence'], row['mutant_sequence']
        require(len(parent) == len(mutant) and set(parent+mutant) <= set('ACGT'),
                'expected corresponding-coordinate DNA alleles')
        require(1 <= sum(a != b for a, b in zip(parent, mutant)) <= 6,
                'expected one to six substitutions')
        contexts[row['parent_context_id']].append(i)
    for indices in contexts.values():
        require(len(indices) >= 2, 'a decision context needs at least two candidates')
        for field in ('dataset', 'biological_component', 'parent_sequence'):
            require(len({rows[i][field] for i in indices}) == 1, 'inconsistent context '+field)
    return rows


def menus(rows, indices):
    """Equal study/component/context masses; candidate order remains inherited."""
    indices = tuple(indices)
    require(len(set(indices)) == len(indices) and bool(indices), 'empty/duplicated row indices')
    require(all(isinstance(i, int) and 0 <= i < len(rows) for i in indices), 'bad row index')
    all_contexts, chosen = defaultdict(list), defaultdict(list)
    for i, row in enumerate(rows):all_contexts[row['parent_context_id']].append(i)
    for i in indices:chosen[rows[i]['parent_context_id']].append(i)
    components, contexts = defaultdict(set), defaultdict(set)
    for context, local in chosen.items():
        require(set(local) == set(all_contexts[context]), 'partial candidate menu')
        row = rows[local[0]]; study, component = row['dataset'], row['biological_component']
        components[study].add(component); contexts[study, component].add(context)
    result = []
    for context, local in sorted(chosen.items()):
        row = rows[local[0]]; study, component = row['dataset'], row['biological_component']
        weight = 1. / (len(components)*len(components[study])*len(contexts[study, component]))
        result.append({'context': context, 'dataset': study, 'component': component,
                       'indices': tuple(local), 'weight': weight})
    return tuple(result)


def _split(rows, eligible, held):
    target = tuple(i for i in eligible if rows[i]['dataset'] == held)
    require(bool(target), 'empty held assay')
    components = {rows[i]['biological_component'] for i in target}
    train = tuple(i for i in eligible if rows[i]['dataset'] != held and
                  rows[i]['biological_component'] not in components)
    expected = {rows[i]['dataset'] for i in eligible} - {held}
    require({rows[i]['dataset'] for i in train} == expected, 'purge removed an entire source assay')
    alleles = {rows[i][field] for i in target for field in ('parent_sequence', 'mutant_sequence')}
    require(not any(rows[i][field] in alleles for i in train
                    for field in ('parent_sequence', 'mutant_sequence')),
            'exact allele overlap despite component exclusion')
    # Match the original component purge followed by its explicit allele guard.
    # Do not silently repair bad components by trimming individual source rows.
    menus(rows, train); menus(rows, target)
    return {'train': train, 'target': target}


def comparison_plan(supplied_rows):
    rows = metadata(supplied_rows)
    require({row['dataset'] for row in rows} == set(STUDIES), 'all four assays are required')
    pools, tasks = {}, []
    for outer in STUDIES:
        final = _split(rows, tuple(range(len(rows))), outer)
        pools[outer] = {'outer': final, 'inner': {}}
        source_studies = sorted(set(STUDIES)-{outer})
        for inner in source_studies:
            pools[outer]['inner'][inner] = _split(rows, final['train'], inner)
        for arm in ARMS:
            for config, penalty in PENALTIES:
                for inner in source_studies:
                    tasks.append({'outer': outer, 'inner': inner, 'arm': arm,
                                  'config': config, 'penalty': penalty, 'phase': 'inner'})
            tasks.append({'outer': outer, 'inner': None, 'arm': arm,
                          'config': 'SOURCE_ONLY_SELECTION_REQUIRED', 'phase': 'outer'})
    encoded = json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()
    return {'status': 'PURE_METADATA_PLAN_NOT_INPUT_OR_EXECUTION_ADMISSION',
            'rows': len(rows), 'metadata_order_sha256': hashlib.sha256(encoded).hexdigest(),
            'pools': pools, 'tasks': tasks, 'planned_inner_tasks': 108,
            'planned_outer_tasks': 12, 'actual_fit_calls': 0}
