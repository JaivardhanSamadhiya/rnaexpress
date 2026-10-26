"""Exact scientific object reuse and a deliberately blocked actual FIT entry."""
from . import current
from src.generalization_knowncell_joint_engine_20261023 import adapter_v2 as adapter
from src.generalization_knowncell_joint_numeric_20261022 import numeric
from src.generalization_knowncell_joint_runner_20261023.runner import run_campaign
from src.generalization_knowncell_campaign_replay_20261023.replay import verify_campaign
from src.generalization_knowncell_joint_evaluation_20261023.evaluation import evaluate
from src.generalization_knowncell_joint_input_bridge_20261023 import sampler


def deferred_scientific_objects():
    """References only; supplying these objects is never an admission."""
    return {'sampler_extractor':sampler.extract_function,'sampler_wrapper_type':sampler.GuardedSampler,'prepare_pools':adapter.prepare_pools,
        'fit_callback_factory':adapter.make_fit_callback,'selector':adapter.select_outer,
        'numeric':numeric,'runner':run_campaign,'independent_replay':verify_campaign,'evaluator':evaluate}


def run_current_fixed_fit(*args,**kwargs):
    # Do not even reach software imports, input readers, aliases or a runner
    # before a fixed real current owner and new manual authorization exist.
    current.require_real_owned_fit_context(*args,**kwargs)
    raise AssertionError('Unreachable: actual current FIT orchestration is not implemented')
