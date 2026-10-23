"""Prospective immutable-plan selector guard; original adapter stays unchanged."""
from . import adapter as original

# The numerical pool and fitting code are EXACT original objects, with no
# altered resource, sampler, loss, feature, configuration or scoring behavior.
prepare_pools = original.prepare_pools
make_fit_callback = original.make_fit_callback
PreparedPools = original.PreparedPools


def select_outer(prepared, campaign, arm, outer_fold, *, probe, environment):
    """Bind source-only selection to immutable prefit inputs BEFORE delegation."""
    original.gate(probe, environment)
    assert isinstance(campaign, original.Campaign)
    assert prepared.prefit_document == campaign.plan.document(), 'Prepared document differs from immutable plan'
    task = next(task for task in campaign.tasks.values()
                if task['arm'] == arm and task['outer_fold'] == outer_fold and task['phase'] == 'outer')
    pool = prepared.pools[original.lifecycle.pool_key(outer_fold, None)]
    bound = campaign.plan.pool(task)
    assert pool['binding'] == bound, 'Mutable selector binding differs from immutable bound pool'
    rows, effects = pool['rows'], pool['effects']
    assert [row['intervention_id'] for row in rows] == bound['training_ids'], 'Source ID order differs from immutable pool'
    assert original.reference.ids_sha(rows) == bound['training_ids_sha256'], 'Source ID digest differs from immutable pool'
    assert original.reference.metadata_sha(rows) == bound['training_metadata_sha256'], 'Source metadata differs from immutable pool'
    assert len(rows) == len(effects) == bound['training_rows'], 'Incomplete source row/effect population'
    assert original.lifecycle.hash_value(effects) == bound['training_effects_json_sha256'], 'Source effects differ from immutable pool'
    return original.select_outer(prepared, campaign, arm, outer_fold, probe=probe, environment=environment)
