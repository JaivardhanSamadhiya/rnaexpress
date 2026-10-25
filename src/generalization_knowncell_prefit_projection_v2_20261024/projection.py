"""Keep actual raw provenance; separate stable and freshly verified identities.

V1 remains unchanged. Its exact-byte, context-verifier and scientific checks
are delegated before this subtype is returned. No reader, probe, native call,
alias, lifecycle patch or actual stage authorization is supplied by V2.
"""
from dataclasses import dataclass
from src.generalization_knowncell_prefit_projection_20261024 import projection as original
from .spec import VIEW_STATUS, OPERATIONAL_STATUS


@dataclass(frozen=True)
class CalibratedBoundPlan(original.CalibratedBoundPlan):
    """Stable scientific campaign identity with a separate current context."""
    def identity(self):
        value = super().identity()
        detail = value['calibrated_resource_compatibility_view']
        del detail['caller_verified_context_sha256']
        del detail['current_owner_receipt_sha256']
        detail['status'] = VIEW_STATUS
        detail['compatibility_identity_version'] = 2
        detail['current_stage_context_recorded_separately'] = True
        detail['current_context_is_not_campaign_creation_identity'] = True
        return value

    def operational_context(self):
        """Snapshot verified at binding, for the current owned-stage receipt.

        This method performs no fresh state check. A future controller must
        continue its actual current-stage checks and persist this descriptor
        separately, never insert it into the old campaign birth identity.
        """
        _, _, admission, context = original._bindings(
            self.prefit_raw, self.root_admission_raw, self.verified_context_raw)
        return {
            'status': OPERATIONAL_STATUS,
            'stable_campaign_identity_sha256': original.legacy.hash_value(self.identity()),
            'actual_prefit_raw_sha256': self.prefit_sha256,
            'root_admission_sha256': context['root_admission_sha256'],
            'projection_source_manifest_sha256': admission['projection_source_manifest_sha256'],
            'current_owner_receipt_sha256': context['current_owner_receipt_sha256'],
            'caller_verified_context_sha256': original.legacy.digest(self.verified_context_raw),
            'supplied_verified_context': original._copy(context),
            'current_stage_context_excluded_from_stable_campaign_identity': True,
            'fresh_state_checks_performed_by_this_method': False,
            'actual_stage_authority_granted_here': False,
        }


def bind_calibrated_plan(prefit_raw, admission_raw, context_raw, *,
                         committed_reader, verify_root_context):
    """Run unchanged actual-byte/current-context checks for EVERY owned stage.

    A real replay must supply its own newly verified context, not relabel the
    fit-time owner as current. The stable root prefit admission remains the
    same document/commit across fit and replay. Both callables must be fixed
    reviewed real implementations in the future root execution controller.
    """
    bound = original.bind_calibrated_plan(prefit_raw, admission_raw, context_raw,
        committed_reader=committed_reader, verify_root_context=verify_root_context)
    return CalibratedBoundPlan(bound.prefit_relative_path, bound.prefit_commit,
        bound.prefit_raw, bound.prefit_sha256, bound.runtime_binding_sha256,
        bound.root_admission_raw, bound.verified_context_raw)


def rebind_prepared(plan, prepared):
    assert isinstance(plan, CalibratedBoundPlan), 'V2 rebinding requires the replay-stable V2 type'
    return original.rebind_prepared(plan, prepared)
