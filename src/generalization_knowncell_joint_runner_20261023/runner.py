"""Exactly63 supplied-pool checkpoints; lifecycle completion only.

A future root-owned controller must separately admit actual data/runtime,
freeze the BoundPlan, and supply a certified integrity hook and live probe.
Nothing in this module imports a numerical library or supplies those inputs.
"""
from pathlib import Path
from src.generalization_knowncell_joint_campaign_20261023.contracts import (
    BoundPlan,canonical_bytes,strict_json,task_key,task_roster,
)
from src.generalization_knowncell_joint_campaign_20261023.writer_v2 import Campaign
from src.generalization_knowncell_joint_campaign_20261023.writer import write_new
from src.generalization_knowncell_joint_engine_20261023 import adapter_v2 as adapter


def _copy(value):return strict_json(canonical_bytes(value))


def run_campaign(prepared,plan,np,minimize,expit,*,probe,environment,directory,
                 before_checkpoint_integrity):
    """One exclusive new run, with checkpoint files in directory/checkpoints.

    Hook signature is keyword-only task_key, task, plan, prepared, campaign;
    return the Python singleton True only after actual runtime/source checks.
    A mere caller declaration is not itself an integrity certificate.

    No reuse/resume/refit path exists. A known failure never reaches finish.
    A partial finish write, like any partial artifact, is retained on failure.
    """
    directory=Path(directory)
    assert directory.is_absolute() and directory.parent.is_dir()
    # Establish ownership before any callback; an existing path is untouched.
    directory.mkdir(parents=False,exist_ok=False)
    campaign=None;completed=[];units=0;stage='start';current=None
    try:
        adapter.original.gate(probe,environment)
        assert isinstance(plan,BoundPlan) and isinstance(prepared,adapter.PreparedPools)
        assert callable(minimize) and callable(expit) and callable(before_checkpoint_integrity)
        assert prepared.prefit_document==plan.document()
        assert set(prepared.pools)==set(plan.document()['source_pools'])
        expected=[(task_key(task),task) for task in task_roster()]
        assert len(expected)==63 and sum(task['phase']=='inner' for _,task in expected)==54
        assert sum(task['optimizer_units'] for _,task in expected)==84
        stage='campaign_birth'
        campaign=Campaign(directory/'checkpoints',plan)
        assert list(campaign.tasks.items())==expected
        callback=None
        for key,task in expected:
            current=key;stage='checkpoint_resource'
            adapter.original.gate(probe,environment)
            assert not campaign.failed and list(campaign.tasks.items())==expected
            stage='integrity_hook'
            result=before_checkpoint_integrity(task_key=key,task=_copy(task),plan=plan,
                                              prepared=prepared,campaign=campaign)
            assert result is True,'Mandatory runtime/source integrity hook did not certify this checkpoint'
            assert list(campaign.tasks.items())==expected and prepared.prefit_document==plan.document()
            adapter.original.gate(probe,environment)
            selected=None
            if task['phase']=='outer':
                stage='selection'
                inners=[inner_key for inner_key,inner in expected if inner['phase']=='inner'
                        and inner['arm']==task['arm'] and inner['outer_fold']==task['outer_fold']]
                assert len(inners)==6 and all(inner_key in completed for inner_key in inners)
                selected=adapter.select_outer(prepared,campaign,task['arm'],task['outer_fold'],
                                              probe=probe,environment=environment)
            stage='checkpoint_resource'
            adapter.original.gate(probe,environment)
            if callback is None:
                stage='callback_construction'
                callback=adapter.make_fit_callback(np,minimize,expit,prepared,plan,
                                                   probe=probe,environment=environment)
            stage='checkpoint'
            receipt=campaign.write_checkpoint(key,callback,selected)
            assert receipt['optimizer_units']==task['optimizer_units']
            completed.append(key);units+=receipt['optimizer_units']
        assert completed==[key for key,_ in expected] and len(completed)==63 and units==84
        stage='finish'
        # No further write or validation is done after a successful finish.
        # Return the exact existing writer result, which disclaims replay/gate.
        return campaign.finish()
    except BaseException as error:
        if campaign is not None:campaign.failed=True
        failure={'status':'FAILED_FINITE_RUN_NO_RESUME','stage':stage,'task_key':current,
                 'error_type':type(error).__name__,'error':str(error),
                 'completed_checkpoint_keys':list(completed),'completed_optimizer_units':units,
                 'prefit_sha256':plan.prefit_sha256 if isinstance(plan,BoundPlan) else None,
                 'partial_outputs_retained':True,'independent_numeric_selection_replay_complete':False,
                 'biological_or_gate_claim':False}
        try:write_new(directory/'runner_failure.json',failure)
        except BaseException as logging_error:
            error.add_note('Exclusive runner failure evidence could not be saved: '
                           +type(logging_error).__name__+': '+str(logging_error))
        raise
