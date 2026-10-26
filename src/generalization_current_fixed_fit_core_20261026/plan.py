"""New-epoch raw provenance and a single-field legacy scientific view."""
from dataclasses import dataclass
from src.generalization_current_execution_context_20261025 import plan as original
from src.generalization_current_execution_context_20261025 import contracts as c
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc
from src.generalization_knowncell_joint_engine_20261023.adapter import PreparedPools


def copy(value):return c.decode(c.canonical(value))


def make_current_prefit(historical_plan,current_execution_provenance):
    """Pure document construction, not verification of the supplied owner.

    The future fixed caller must actually verify this provenance. Neither a
    dictionary nor this library can authorize imports, reads, Jobs or fitting.
    No unknown future raw-prefit SHA or commit belongs in its own document.
    """
    assert isinstance(historical_plan,original.HistoricalScientificPlan)
    provenance=copy(current_execution_provenance)
    assert provenance and isinstance(provenance.get('status'),str)
    actual=copy(historical_plan.actual_document())
    actual['resource_exception_applies']=True
    actual['runtime_binding_sha256']=lc.hash_value(original.current_epoch_reference())
    actual['input_admission_bindings']=original.current_admission_references(actual['input_admission_bindings'])
    actual['prefit_execution']={
        'status':'NEW_CURRENT_PREFIT_PROVENANCE_SUPPLIED_BY_FIXED_CALLER',
        'creator_provenance':provenance,'creator_provenance_sha256':lc.hash_value(provenance),
        'historical_prefit_raw_sha256':historical_plan.prefit_sha256,
        'supplied_owner_provenance_verified_by_this_library':False}
    actual['current_execution']={
        'current_software_epoch_reference':original.current_epoch_reference(),
        'historical_reference_sha256':c.digest(historical_plan.historical_reference_raw),
        'historical_prefit_raw_sha256':historical_plan.prefit_sha256,
        'new_prefit_creator_provenance_sha256':lc.hash_value(provenance),
        'actual_stage_authority_granted_here':False}
    _,view=original.old_view._view(c.canonical(actual))
    assert original.scientific_projection(view)==original.scientific_projection(historical_plan.document())
    assert view['source_pools']==historical_plan.document()['source_pools']
    return actual


@dataclass(frozen=True)
class CurrentFitPlan(original.CurrentScientificPlan):
    """Stable new campaign identity; actual current-stage proof stays external."""
    def __post_init__(self):
        super().__post_init__()
        actual=self.actual_document()
        execution=actual['prefit_execution']
        assert execution['status']=='NEW_CURRENT_PREFIT_PROVENANCE_SUPPLIED_BY_FIXED_CALLER'
        assert execution['historical_prefit_raw_sha256']==self.historical_plan.prefit_sha256
        assert lc.hash_value(execution['creator_provenance'])==execution['creator_provenance_sha256']
        assert execution['supplied_owner_provenance_verified_by_this_library'] is False
        assert actual['current_execution']['new_prefit_creator_provenance_sha256']==execution['creator_provenance_sha256']

    def identity(self):
        value=super().identity()
        actual,view=self.actual_document(),self.document()
        value['current_resource_compatibility_view']={
            'status':'EXPLICIT_NEW_RAW_PREFIT_AND_SINGLE_FIELD_LEGACY_VIEW',
            'actual_prefit_raw_sha256':self.prefit_sha256,
            'actual_document_canonical_sha256':lc.hash_value(actual),
            'legacy_view_canonical_sha256':lc.hash_value(view),
            'sole_projection':{'field':'resource_exception_applies','actual':True,'legacy_view':False},
            'document_is_actual_persisted_resource_provenance':False,
            'new_prefit_creator_provenance_sha256':actual['prefit_execution']['creator_provenance_sha256'],
            'fresh_fit_or_replay_owner_included_in_campaign_identity':False,
            'actual_stage_authority_granted_here':False}
        return value


def bind_current_plan(prefit_relative_path,prefit_raw,prefit_commit,historical_plan,*,committed_reader):
    """Bind supplied bytes to an exact commit; reader certification is external."""
    c.relative(prefit_relative_path);lc.valid_hash(prefit_commit,40)
    assert callable(committed_reader) and type(prefit_raw) is bytes
    assert committed_reader(prefit_relative_path,prefit_commit)==prefit_raw,'New prefit must be exactly committed'
    actual=c.decode(prefit_raw)
    return CurrentFitPlan(prefit_relative_path,prefit_commit,prefit_raw,c.digest(prefit_raw),
                          actual['runtime_binding_sha256'],historical_plan)


def rebind_prepared(plan,prepared):
    """Preserve exact original pool/metadata objects after scientific equality."""
    assert isinstance(plan,CurrentFitPlan) and isinstance(prepared,PreparedPools)
    old=lc.validate_prefit(prepared.prefit_document);view=plan.document()
    assert original.scientific_projection(old)==original.scientific_projection(view)
    historical=plan.historical_plan.document()
    if old['runtime_binding_sha256']==historical['runtime_binding_sha256']:
        assert old['input_admission_bindings']==historical['input_admission_bindings']
    else:
        assert old['runtime_binding_sha256']==view['runtime_binding_sha256']
        assert old['input_admission_bindings']==view['input_admission_bindings']
    assert set(prepared.pools)==set(view['source_pools'])
    for key,pool in prepared.pools.items():assert pool['binding']==view['source_pools'][key]
    return PreparedPools(prepared.metadata,prepared.pools,view)
