"""Truthful separated declarations. This class is not a software/Job token."""
from dataclasses import dataclass
from . import contracts as c,spec,current


@dataclass(frozen=True)
class CurrentExecutionContext:
    historical_reference_sha256:str
    scientific_plan_identity_sha256:str

    def __post_init__(self):
        c.sha(self.historical_reference_sha256);c.sha(self.scientific_plan_identity_sha256)

    def declaration(self):
        return {'status':'SOURCE_ONLY_CURRENT_CONTEXT_DECLARATION_NOT_VERIFIED_RUNTIME_OWNER_OR_FIT',
            'historical_scientific_reference':{
                'reference_sha256':self.historical_reference_sha256,
                'scientific_plan_identity_sha256':self.scientific_plan_identity_sha256,
                'old_runtime_anchor_sha256':spec.HISTORICAL_ARRAY_ANCHOR,
                'old_native_profile_origin_sha256':spec.HISTORICAL_PROFILE_ORIGIN,
                'meaning':'historical scientific provenance, not present runtime identity'},
            'current_software_identity':{'inventory_sha256':spec.INVENTORY_SHA,
                'profile_source_sha256':spec.PROFILE_MANIFEST_SHA,'profile_receipt_sha256':spec.PROFILE_RECEIPT_SHA,
                'independent_certificate_sha256':spec.PROFILE_CERTIFICATE_SHA,'actual_current_process_native_origins_verified_here':False,
                'historical_runtime_PASS_reused_for_current_runtime':False},
            'current_owned_execution':{'real_owned_Job_verified':False,'fresh_manual_FIT_authorization':None,
                'actual_stage_authority_granted':False,'controller_implemented':False},
            'readiness':'PENDING_FIXED_CURRENT_PROVIDER_OWNED_CONTROLLER_AND_NEW_MANUAL_FIT_AUTHORIZATION'}

    def require_fit_authority(self):
        return current.require_real_owned_fit_context(self)
