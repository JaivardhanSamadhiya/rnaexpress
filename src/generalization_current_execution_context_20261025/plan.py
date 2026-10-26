"""Historical scientific BoundPlan; no old current-context PASS is created."""
from dataclasses import dataclass
from . import contracts as c,spec
from src.generalization_knowncell_joint_campaign_20261023 import contracts as legacy
from src.generalization_knowncell_joint_engine_20261023.adapter import PreparedPools
from src.generalization_knowncell_prefit_projection_20261024 import projection as old_view
from src.generalization_knowncell_prefit_projection_20261024 import spec as old_schema
from src.generalization_knowncell_prefit_projection_v2_20261024 import spec as stable_schema


def historical_bindings(prefit_raw,admission_raw,reference):
    c.reference_contract(reference)
    assert c.digest(prefit_raw)==reference['file_sha256']['prefit']
    assert c.digest(admission_raw)==reference['file_sha256']['projection']
    # _view is the original PURE one-field scientific compatibility projection.
    # No old binder, current context, resource probe or native guard is called.
    actual,view=old_view._view(prefit_raw)
    admission=c.decode(admission_raw)
    assert set(admission)==old_schema.ADMISSION_FIELDS
    assert admission['status']==old_schema.ADMISSION_STATUS and admission['schema_version']==1
    assert admission['prefit_relative_path']==reference['actual_prefit_relative_path']
    assert admission['prefit_commit']==reference['actual_prefit_commit']
    assert admission['prefit_sha256']==c.digest(prefit_raw)
    assert admission['runtime_binding_sha256']==actual['runtime_binding_sha256']==reference['historical_runtime_anchor_sha256']
    assert admission['projection_source_manifest_sha256']==spec.PROJECTION_SOURCE_SHA
    for key,want in (('approved_policy_manifest_sha256',spec.HISTORICAL_POLICY_SHA),
            ('authorization_sha256',spec.HISTORICAL_AUTH_SHA),('approval_scope_sha256',spec.HISTORICAL_SCOPE_SHA)):
        assert admission[key]==want
    assert admission['input_admission_bindings_sha256']==legacy.hash_value(actual['input_admission_bindings'])
    c.sha(admission['prefit_owner_receipt_sha256'])
    extra=admission['additional_top_level_provenance_fields']
    assert type(extra) is list and extra==sorted(set(extra)) and all(type(k) is str and k in actual for k in extra)
    assert old_schema.FIELD not in extra and admission['permitted_projection']==old_schema.PROJECTION
    assert admission['scientific_settings_changed'] is admission['actual_stage_authority_granted_here'] is False
    return actual,view,admission


@dataclass(frozen=True)
class HistoricalScientificPlan(legacy.BoundPlan):
    """Generic original runner compatibility, explicitly not an execution token."""
    root_admission_raw:bytes
    historical_reference_raw:bytes

    def __post_init__(self):
        reference=c.decode(self.historical_reference_raw)
        actual,_,admission=historical_bindings(self.prefit_raw,self.root_admission_raw,reference)
        assert self.prefit_sha256==c.digest(self.prefit_raw)==admission['prefit_sha256']
        assert self.prefit_relative_path==admission['prefit_relative_path'] and self.prefit_commit==admission['prefit_commit']
        assert self.runtime_binding_sha256==actual['runtime_binding_sha256']

    def _parts(self):
        reference=c.decode(self.historical_reference_raw)
        return (*historical_bindings(self.prefit_raw,self.root_admission_raw,reference),reference)

    def actual_document(self):return self._parts()[0]
    def document(self):return self._parts()[1]

    def identity(self):
        actual,view,admission,reference=self._parts()
        value=super().identity()
        value['calibrated_resource_compatibility_view']={
            'status':stable_schema.VIEW_STATUS,'actual_prefit_raw_sha256':self.prefit_sha256,
            'actual_document_canonical_sha256':legacy.hash_value(actual),'legacy_view_canonical_sha256':legacy.hash_value(view),
            'sole_projection':dict(old_schema.PROJECTION),'document_is_actual_persisted_prefit_provenance':False,
            'original_resource_guards_unchanged':False,'projection_source_manifest_sha256':admission['projection_source_manifest_sha256'],
            'root_admission_relative_path':reference['projection_admission_relative_path'],
            'root_admission_commit':reference['projection_admission_commit'],'root_admission_sha256':c.digest(self.root_admission_raw),
            'approved_policy_manifest_sha256':spec.HISTORICAL_POLICY_SHA,'authorization_sha256':spec.HISTORICAL_AUTH_SHA,
            'approval_scope_sha256':spec.HISTORICAL_SCOPE_SHA,'prefit_owner_receipt_sha256':admission['prefit_owner_receipt_sha256'],
            'input_admission_bindings_sha256':admission['input_admission_bindings_sha256'],
            'actual_context_verifier_is_external_controller_precondition':True,'actual_execution_authority_granted_here':False,
            'compatibility_identity_version':2,'current_stage_context_recorded_separately':True,
            'current_context_is_not_campaign_creation_identity':True}
        return value

    def historical_descriptor(self):
        return {'status':'HISTORICAL_SCIENTIFIC_PLAN_NOT_CURRENT_OWNER_OR_SOFTWARE_AUTHORITY',
            'scientific_identity_sha256':legacy.hash_value(self.identity()),
            'historical_runtime_anchor_sha256':self.runtime_binding_sha256,
            'current_native_identity_verified_here':False,'actual_stage_authority_granted_here':False}


def from_supplied(prefit_raw,admission_raw,reference_raw):
    reference=c.decode(reference_raw)
    actual,_,admission=historical_bindings(prefit_raw,admission_raw,reference)
    return HistoricalScientificPlan(admission['prefit_relative_path'],admission['prefit_commit'],prefit_raw,
        c.digest(prefit_raw),actual['runtime_binding_sha256'],admission_raw,reference_raw)


def rebind_prepared(plan,prepared):
    assert isinstance(plan,HistoricalScientificPlan) and isinstance(prepared,PreparedPools)
    old=prepared.prefit_document;legacy.validate_prefit(old);view=plan.document()
    _,_,admission,_=plan._parts()
    assert set(old)<=set(view)
    for key in old:assert legacy.canonical_bytes(old[key])==legacy.canonical_bytes(view[key]),key
    assert sorted(set(view)-set(old))==admission['additional_top_level_provenance_fields']
    assert set(prepared.pools)==set(view['source_pools'])
    for name,pool in prepared.pools.items():
        assert legacy.canonical_bytes(pool['binding'])==legacy.canonical_bytes(view['source_pools'][name])
    return PreparedPools(prepared.metadata,prepared.pools,view)


SCIENCE_FIELDS=('status','counts','arms','configs','numerical_threads','all_row_ids','all_row_folds','source_pools',
    'metadata_admission_sha256','feature_admission_sha256','label_admission_sha256','fit_source_manifest_sha256')
EPOCH_FIELDS={'runtime_binding_sha256','native_profile_receipt_sha256'}


def current_epoch_reference():
    """A genuine new evidence reference hash, never a current-origin proof."""
    value={'status':'CURRENT_SOFTWARE_EPOCH_REFERENCE_NOT_CURRENT_OWNER_OR_RUNTIME_ADMISSION',
        'current_inventory_sha256':spec.INVENTORY_SHA,'current_profile_source_sha256':spec.PROFILE_MANIFEST_SHA,
        'current_profile_receipt_sha256':spec.PROFILE_RECEIPT_SHA,
        'independent_current_profile_certificate_sha256':spec.PROFILE_CERTIFICATE_SHA}
    for key,want in value.items():
        if key.endswith('_sha256'):c.sha(want)
    return value


def scientific_projection(document):
    """Keep every scientific key/hash; separate only explicitly named epochs."""
    required=set(SCIENCE_FIELDS)|{'runtime_binding_sha256','resource_exception_applies','input_admission_bindings'}
    assert required<=set(document)<=required|{'prefit_execution','current_execution'}
    legacy.validate_prefit(document)
    result={key:document[key] for key in SCIENCE_FIELDS}
    result['input_admission_bindings']={key:value for key,value in document['input_admission_bindings'].items() if key not in EPOCH_FIELDS}
    return c.decode(c.canonical(result))


def current_admission_references(historical_admissions):
    """Same data/source references, with truthful NEW operational epoch fields."""
    result=c.decode(c.canonical(historical_admissions))
    assert result['runtime_binding_sha256']==spec.HISTORICAL_ARRAY_ANCHOR
    assert result['native_profile_receipt_sha256']==spec.HISTORICAL_PROFILE_ORIGIN
    result['runtime_binding_sha256']=legacy.hash_value(current_epoch_reference())
    result['native_profile_receipt_sha256']=spec.PROFILE_RECEIPT_SHA
    return result


@dataclass(frozen=True)
class CurrentScientificPlan(legacy.BoundPlan):
    """New operational identity plus separate byte-exact scientific equivalence."""
    historical_plan:HistoricalScientificPlan

    def __post_init__(self):
        assert isinstance(self.historical_plan,HistoricalScientificPlan)
        assert self.prefit_sha256==c.digest(self.prefit_raw)
        actual,view=old_view._view(self.prefit_raw)
        assert self.runtime_binding_sha256==actual['runtime_binding_sha256']==legacy.hash_value(current_epoch_reference())
        assert actual['input_admission_bindings']==current_admission_references(self.historical_plan.actual_document()['input_admission_bindings'])
        assert legacy.canonical_bytes(scientific_projection(view))==legacy.canonical_bytes(scientific_projection(self.historical_plan.document()))
        assert actual['current_execution']['current_software_epoch_reference']==current_epoch_reference()
        assert actual['current_execution']['historical_reference_sha256']==c.digest(self.historical_plan.historical_reference_raw)
        c.relative(self.prefit_relative_path);legacy.valid_hash(self.prefit_commit,40)

    def actual_document(self):return old_view._view(self.prefit_raw)[0]
    def document(self):return old_view._view(self.prefit_raw)[1]

    def stable_scientific_identity(self):
        return {'status':'SCIENTIFIC_EQUIVALENCE_ONLY_NOT_OPERATIONAL_RUNTIME_OR_OWNER_IDENTITY',
            'scientific_fields_sha256':legacy.hash_value(scientific_projection(self.document())),
            'historical_scientific_fields_sha256':legacy.hash_value(scientific_projection(self.historical_plan.document())),
            'all_nine_scientific_pool_bindings_equal':self.document()['source_pools']==self.historical_plan.document()['source_pools'],
            'old_full_operational_identity_required_equal':False,'actual_stage_authority_granted_here':False}

    def identity(self):
        value=super().identity()
        value['current_epoch_reference_sha256']=legacy.hash_value(current_epoch_reference())
        value['stable_scientific_identity']=self.stable_scientific_identity()
        return value


def rebind_current_prepared(plan,prepared):
    assert isinstance(plan,CurrentScientificPlan) and isinstance(prepared,PreparedPools)
    # Compare a genuinely rebuilt current prefit, not an old operational identity.
    old=prepared.prefit_document;legacy.validate_prefit(old);view=plan.document()
    assert legacy.canonical_bytes(scientific_projection(old))==legacy.canonical_bytes(scientific_projection(view))
    assert old['input_admission_bindings']==view['input_admission_bindings']
    assert old['runtime_binding_sha256']==view['runtime_binding_sha256']
    assert set(prepared.pools)==set(view['source_pools'])
    for name,pool in prepared.pools.items():assert pool['binding']==view['source_pools'][name]
    return PreparedPools(prepared.metadata,prepared.pools,view)
