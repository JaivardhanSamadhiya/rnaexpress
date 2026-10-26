"""Deferred historical saved-declaration reader, never current admission."""
from pathlib import Path
from src.generalization_knowncell_fit_paged_execution_20261025.terminal import ReadOnlySavedCampaign
from src.generalization_knowncell_joint_campaign_20261023 import contracts as lc


def check_saved_declarations(directory, historical_plan, campaign_birth_raw, filename_pins, *, fresh):
    """Future NEW controller must authorize/bind this exact C-only read set.

    The validated old reader is used only for check_saved. Neither its writer
    nor finish is called. The missing campaign completion is preserved.
    Historical identity is never presented as the current forensic owner.
    """
    fresh()
    directory = Path(directory)
    assert directory.resolve().drive.casefold() == 'c:' and directory.is_dir() and not directory.is_symlink()
    tasks = lc.task_roster()
    expected = {'campaign_birth.json'} | {lc.task_key(task)+suffix for task in tasks
                 for suffix in ('.birth.json','.model.json','.complete.json')}
    assert len(expected) == 190 and set(filename_pins) == expected
    assert {path.name for path in directory.iterdir()} == expected
    assert not (directory/'campaign_complete.json').exists()
    def check_bytes():
        for name,want in filename_pins.items():
            fresh()
            assert Path(name).name == name and '/' not in name and '\\' not in name
            path = directory/name
            assert path.is_file() and not path.is_symlink() and path.stat().st_size <= 16*2**20
            assert lc.digest(path.read_bytes()) == want
    check_bytes()
    assert (directory/'campaign_birth.json').read_bytes() == campaign_birth_raw
    reader = ReadOnlySavedCampaign(directory,historical_plan,lc.digest(campaign_birth_raw))
    checked = 0
    for task in tasks:
        fresh()
        receipt = reader.check_saved(lc.task_key(task))
        assert receipt['optimizer_units'] == task['optimizer_units']
        checked += receipt['optimizer_units']
    assert checked == 84
    check_bytes()
    return {'status':'PASS190_SAVED_DECLARATIONS_NOT_CAMPAIGN_OR_CURRENT_OWNER',
        'saved_checkpoints':63,'recorded_completed_optimizer_units':84,
        'old_campaign_complete_missing':True,'current_owner_or_runtime_admission_granted':False,
        'saved_filename_sha256':dict(filename_pins),'new_optimizer_calls':0}
