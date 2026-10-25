"""Pure compatibility on supplied bytes, with externally verified authority.

There is no file reader, scientific import, probe, writer, resource override or
execution entry point. A future reviewed controller must supply its fixed real
exact-commit reader and context verifier. Passing declarations here is not a
substitute for independently checking that controller or its native origins.
"""
from dataclasses import dataclass
from src.generalization_knowncell_joint_campaign_20261023 import contracts as legacy
from src.generalization_knowncell_joint_engine_20261023.adapter import PreparedPools
from .spec import (
    ADMISSION_STATUS, CONTEXT_STATUS, VIEW_STATUS, ADMISSION_FIELDS,
    CONTEXT_FIELDS, POLICY_SHA, AUTH_SHA, SCOPE_SHA, FIELD, PROJECTION,
)


def _copy(value):
    return legacy.strict_json(legacy.canonical_bytes(value))


def _relative(name):
    assert isinstance(name, str) and name.startswith('results/')
    assert name == name.replace('\\', '/') and ':' not in name
    assert all(part not in ('', '.', '..') for part in name.split('/'))
    assert name.endswith('.json')
    return name


def _view(raw):
    actual = legacy.strict_json(raw)
    assert isinstance(actual, dict) and actual[FIELD] is True, 'Require truthful actual calibrated prefit'
    legacy.canonical_bytes(actual)  # Reject overflow-to-infinity as well as JSON NaN.
    result = _copy(actual)
    result[FIELD] = False
    assert set(result) == set(actual)
    assert all(legacy.canonical_bytes(result[key]) == legacy.canonical_bytes(actual[key])
               for key in actual if key != FIELD), 'More than the sole generic flag changed'
    legacy.validate_prefit(result)  # The original scientific validator is unchanged.
    return actual, result


def _bindings(prefit_raw, admission_raw, context_raw):
    actual, view = _view(prefit_raw)
    admission = legacy.strict_json(admission_raw)
    context = legacy.strict_json(context_raw)
    assert isinstance(admission, dict) and set(admission) == ADMISSION_FIELDS
    assert isinstance(context, dict) and set(context) == CONTEXT_FIELDS
    assert admission['status'] == ADMISSION_STATUS and type(admission['schema_version']) is int
    assert admission['schema_version'] == 1 and context['status'] == CONTEXT_STATUS
    _relative(admission['prefit_relative_path']); _relative(context['root_admission_relative_path'])
    legacy.valid_hash(admission['prefit_commit'], 40)
    legacy.valid_hash(context['root_admission_commit'], 40)
    assert admission['prefit_sha256'] == context['prefit_sha256'] == legacy.digest(prefit_raw)
    assert context['root_admission_sha256'] == legacy.digest(admission_raw)
    assert admission['runtime_binding_sha256'] == context['current_runtime_binding_sha256'] == actual['runtime_binding_sha256']
    for key, expected in (('approved_policy_manifest_sha256', POLICY_SHA),
                          ('authorization_sha256', AUTH_SHA), ('approval_scope_sha256', SCOPE_SHA)):
        assert admission[key] == context[key] == expected
    for key in ('projection_source_manifest_sha256', 'prefit_owner_receipt_sha256',
                'input_admission_bindings_sha256'):
        assert legacy.valid_hash(admission[key]) == legacy.valid_hash(context[key])
    legacy.valid_hash(context['current_owner_receipt_sha256'])
    assert isinstance(actual.get('input_admission_bindings'), dict)
    assert admission['input_admission_bindings_sha256'] == legacy.hash_value(actual['input_admission_bindings'])
    extra = admission['additional_top_level_provenance_fields']
    assert isinstance(extra, list) and all(isinstance(name, str) and name for name in extra)
    assert extra == sorted(set(extra)) and FIELD not in extra
    assert all(name in actual for name in extra)
    assert admission['permitted_projection'] == PROJECTION
    assert admission['scientific_settings_changed'] is False
    assert admission['actual_stage_authority_granted_here'] is False
    assert context['actual_owner_resource_runtime_and_source_closure_verified'] is True
    assert context['actual_stage_authority_granted_by_this_library'] is False
    legacy.canonical_bytes(admission); legacy.canonical_bytes(context)
    return actual, view, admission, context


@dataclass(frozen=True)
class CalibratedBoundPlan(legacy.BoundPlan):
    """A BoundPlan with raw TRUE provenance and a declared FALSE legacy view.

    document() is NEVER the actual prefit serialization. actual_document() and
    prefit_raw retain all actual provenance/extras. Creating this object is not
    a resource or FIT capability; use only the reviewed binder/controller.
    """
    root_admission_raw: bytes
    verified_context_raw: bytes

    def __post_init__(self):
        actual, _, admission, context = _bindings(
            self.prefit_raw, self.root_admission_raw, self.verified_context_raw)
        assert self.prefit_sha256 == legacy.digest(self.prefit_raw)
        assert self.prefit_relative_path == admission['prefit_relative_path']
        assert self.prefit_commit == admission['prefit_commit']
        assert self.runtime_binding_sha256 == actual['runtime_binding_sha256']
        assert context['prefit_sha256'] == self.prefit_sha256

    def actual_document(self):
        assert legacy.digest(self.prefit_raw) == self.prefit_sha256
        actual, _ = _view(self.prefit_raw)
        return actual

    def document(self):
        assert legacy.digest(self.prefit_raw) == self.prefit_sha256
        _, view = _view(self.prefit_raw)
        return view

    def identity(self):
        actual, view, admission, context = _bindings(
            self.prefit_raw, self.root_admission_raw, self.verified_context_raw)
        result = super().identity()
        result['calibrated_resource_compatibility_view'] = {
            'status': VIEW_STATUS,
            'actual_prefit_raw_sha256': self.prefit_sha256,
            'actual_document_canonical_sha256': legacy.hash_value(actual),
            'legacy_view_canonical_sha256': legacy.hash_value(view),
            'sole_projection': _copy(PROJECTION),
            'document_is_actual_persisted_prefit_provenance': False,
            'original_resource_guards_unchanged': False,
            'projection_source_manifest_sha256': admission['projection_source_manifest_sha256'],
            'root_admission_relative_path': context['root_admission_relative_path'],
            'root_admission_commit': context['root_admission_commit'],
            'root_admission_sha256': context['root_admission_sha256'],
            'caller_verified_context_sha256': legacy.digest(self.verified_context_raw),
            'approved_policy_manifest_sha256': POLICY_SHA,
            'authorization_sha256': AUTH_SHA, 'approval_scope_sha256': SCOPE_SHA,
            'prefit_owner_receipt_sha256': admission['prefit_owner_receipt_sha256'],
            'current_owner_receipt_sha256': context['current_owner_receipt_sha256'],
            'input_admission_bindings_sha256': admission['input_admission_bindings_sha256'],
            'actual_context_verifier_is_external_controller_precondition': True,
            'actual_execution_authority_granted_here': False,
        }
        return result


def bind_calibrated_plan(prefit_raw, admission_raw, context_raw, *,
                         committed_reader, verify_root_context):
    """Compare supplied actual/admission bytes to exact commits and real context.

    The future controller must pin and review BOTH supplied callables. The
    verifier must actually check owner/resource approval/runtime/input/source
    evidence for this supplied binding, not return True from a declaration.
    No callback is supplied or manufactured by this library. Invented test
    callbacks are not valid production verifiers and confer no stage authority.
    """
    assert callable(committed_reader) and callable(verify_root_context)
    actual, _, admission, context = _bindings(prefit_raw, admission_raw, context_raw)
    assert committed_reader(context['root_admission_relative_path'], context['root_admission_commit']) == admission_raw
    assert committed_reader(admission['prefit_relative_path'], admission['prefit_commit']) == prefit_raw
    binding = {'admission': _copy(admission), 'context': _copy(context),
               'actual_prefit_raw_sha256': legacy.digest(prefit_raw),
               'root_admission_raw_sha256': legacy.digest(admission_raw),
               'context_raw_sha256': legacy.digest(context_raw)}
    binding_before = legacy.canonical_bytes(binding)
    assert verify_root_context(binding) is True, 'Real reviewed root context must certify this exact binding'
    assert legacy.canonical_bytes(binding) == binding_before, 'Context verifier mutated its bound request'
    return CalibratedBoundPlan(admission['prefit_relative_path'], admission['prefit_commit'],
        prefit_raw, legacy.digest(prefit_raw), actual['runtime_binding_sha256'], admission_raw, context_raw)


def rebind_prepared(plan, prepared):
    """Retain original metadata/pool objects; attach the exact projected view.

    This checks supplied declarations, not native pool hashes. The unchanged
    old engine still rehashes real pool arrays at its own admitted boundaries.
    """
    assert isinstance(plan, CalibratedBoundPlan) and isinstance(prepared, PreparedPools)
    old = prepared.prefit_document
    legacy.validate_prefit(old)
    view = plan.document()
    _, _, admission, _ = _bindings(plan.prefit_raw, plan.root_admission_raw, plan.verified_context_raw)
    assert set(old) <= set(view), 'An original scientific key was removed'
    for key in old:
        assert legacy.canonical_bytes(old[key]) == legacy.canonical_bytes(view[key]), 'Original prefit value changed: '+key
    assert sorted(set(view) - set(old)) == admission['additional_top_level_provenance_fields']
    assert set(prepared.pools) == set(view['source_pools'])
    for name, pool in prepared.pools.items():
        assert legacy.canonical_bytes(pool['binding']) == legacy.canonical_bytes(view['source_pools'][name])
    result = PreparedPools(prepared.metadata, prepared.pools, view)
    assert result.metadata is prepared.metadata and result.pools is prepared.pools
    assert result.prefit_document == plan.document()
    return result
