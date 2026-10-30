"""Conditional mathematical bound from saved binary endpoints, without refits."""
from collections import Counter, defaultdict
import math

CELLS = ('CAD','Neuro-2a')


def require(condition,message):
    if not condition:raise ValueError(message)


def analyze(decisions):
    grouped = defaultdict(dict)
    counts = Counter()
    components = defaultdict(set)
    for row in decisions:
        cell = row['cell_type'];component = row['biological_component'];context = row['parent_context_id']
        require(cell in CELLS,'unexpected cell')
        marker = '|'+cell+'|'
        require(context.count(marker) == 1,'ambiguous cell/context key')
        key = (component,context.replace(marker,'|CELL|'))
        local = grouped[key].setdefault(cell,{})
        direction = row['direction']
        require(direction in (-1,1) and direction not in local,'duplicate direction')
        local[direction] = row
        components[cell].add(component)
    require(set(components) == set(CELLS),'both cells required')
    for (component,context),cells in grouped.items():
        require(set(cells) == set(CELLS),'unpaired context')
        for cell,dirs in cells.items():
            require(set(dirs) == {-1,1},'incomplete direction pair')
            require(dirs[-1]['candidates'] == dirs[1]['candidates'],'menu size mismatch')
            counts[cell,component] += 1
    discordant = same_order = 0
    binary_mass = discordant_mass = 0.
    observed_regret_contribution = 0.
    for (component,context),cells in grouped.items():
        sizes = {dirs[1]['candidates'] for dirs in cells.values()}
        require(len(sizes) == 1,'paired cell menu sizes differ')
        weight = {cell:1./(2*len(components[cell])*counts[cell,component]) for cell in CELLS}
        require(abs(weight[CELLS[0]]-weight[CELLS[1]]) < 1e-15,'unequal paired cell masses')
        if sizes != {2}:continue
        effects = {};orders = {};candidate_sets = []
        for cell,dirs in cells.items():
            low,high = dirs[-1],dirs[1]
            require(high['selected_score'] >= low['selected_score'],'reversed score extrema')
            require(math.isfinite(high['selected_score']) and math.isfinite(low['selected_score']),
                    'nonfinite selected score')
            # Binary endpoints reveal both measured effects only if scores differ.
            require(high['selected_score'] > low['selected_score'],
                    'binary full candidate roster unrecoverable from constant scores')
            a,b = low['selected_mutant_sequence'],high['selected_mutant_sequence']
            require(a != b,'distinct binary alleles required')
            local = {a:float(low['selected_effect']),b:float(high['selected_effect'])}
            require(all(math.isfinite(v) for v in local.values()) and local[a] != local[b],
                    'binary effects nonfinite or tied')
            ordered = tuple(sorted(local));candidate_sets.append(ordered)
            effects[cell] = local[ordered[1]] > local[ordered[0]]
            orders[cell] = b == ordered[1]
            mean_regret = (low['regret']+high['regret'])/2
            want = 0. if effects[cell] == orders[cell] else 1.
            require(abs(mean_regret-want) < 1e-12,'saved regret disagrees with binary endpoints')
            observed_regret_contribution += weight[cell]*mean_regret
        require(candidate_sets[0] == candidate_sets[1],'paired binary candidate alleles differ')
        mass = math.fsum(weight.values());binary_mass += mass
        if effects[CELLS[0]] != effects[CELLS[1]]:
            discordant += 1;discordant_mass += mass
        if orders[CELLS[0]] == orders[CELLS[1]]:same_order += 1
    pairs = sum(next(iter(cells.values()))[1]['candidates'] == 2 for cells in grouped.values())
    require(pairs > 0 and binary_mass > 0,'no informative binary pairs')
    return dict(status='POST_GATE_PAIRED_BINARY_TRUTH_DIAGNOSTIC_NOT_CONFIRMATION',
        paired_contexts=len(grouped),paired_binary_contexts=pairs,
        discordant_binary_contexts=discordant,
        unweighted_discordant_binary_fraction=discordant/pairs,
        binary_primary_weight=binary_mass,
        weighted_discordant_binary_fraction=discordant_mass/binary_mass,
        cell_invariant_oracle_binary_conditional_regret_floor=.5*discordant_mass/binary_mass,
        cell_invariant_oracle_binary_full_primary_contribution_floor=.5*discordant_mass,
        cell_invariant_oracle_binary_conditional_order_accuracy_ceiling=1-.5*discordant_mass/binary_mass,
        saved_predictor_same_order_binary_pairs=same_order,
        saved_predictor_binary_regret_contribution=observed_regret_contribution,
        scope='Only one shared ordering per exact paired binary menu, equal paired cell mass, observed aggregate effects treated as fixed. Other menus optimistically perfect for the full-primary contribution. Oracle uses target outcomes and is not an available predictor, noise ceiling, all-model bound or causal effect.',
        biological_fits=0,original_inputs_reopened=False,gate_changed=False)
