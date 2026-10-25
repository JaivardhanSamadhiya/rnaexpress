"""Prospective supplied-byte contract; no actual admission is fabricated."""

NS = 'generalization_knowncell_prefit_projection_20261024'
ADMISSION_STATUS = 'ROOT_FROZEN_CALIBRATED_PREFIT_COMPATIBILITY_ADMISSION'
CONTEXT_STATUS = 'ROOT_VERIFIED_CALIBRATED_PREFIT_COMPATIBILITY_CONTEXT'
VIEW_STATUS = 'DECLARED_TRANSIENT_LEGACY_PREFIT_RESOURCE_VIEW_NOT_ACTUAL_PROVENANCE'
POLICY_SHA = 'a49b82f965dd6e389f908764d2bf1c331eb3441fe8a0d683b0fca2466c847ba9'
AUTH_SHA = 'b67d5d45abdd6812997d3b84f6cbd5ff2abaf68cd8786638f5312d2744ab24e3'
SCOPE_SHA = 'c40b929187a35199e88523ab5c6b351789c45fddb3aebe6dcf68172684ce6495'
FIELD = 'resource_exception_applies'
ADMISSION_FIELDS = {
    'status', 'schema_version', 'prefit_relative_path', 'prefit_sha256', 'prefit_commit',
    'runtime_binding_sha256', 'projection_source_manifest_sha256',
    'approved_policy_manifest_sha256', 'authorization_sha256', 'approval_scope_sha256',
    'prefit_owner_receipt_sha256', 'input_admission_bindings_sha256',
    'additional_top_level_provenance_fields', 'scientific_settings_changed',
    'permitted_projection', 'actual_stage_authority_granted_here',
}
CONTEXT_FIELDS = {
    'status', 'root_admission_relative_path', 'root_admission_commit',
    'root_admission_sha256', 'prefit_sha256', 'current_runtime_binding_sha256',
    'projection_source_manifest_sha256', 'approved_policy_manifest_sha256',
    'authorization_sha256', 'approval_scope_sha256', 'prefit_owner_receipt_sha256',
    'current_owner_receipt_sha256', 'input_admission_bindings_sha256',
    'actual_owner_resource_runtime_and_source_closure_verified',
    'actual_stage_authority_granted_by_this_library',
}
PROJECTION = {'top_level_field': FIELD, 'actual_value': True, 'legacy_view_value': False}
