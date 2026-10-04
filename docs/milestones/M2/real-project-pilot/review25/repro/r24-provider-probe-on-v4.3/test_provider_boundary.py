"""Assertions over fresh runs of the unchanged v4.1 runner, scripted provider only."""
from pathlib import Path
import json
R=Path(__file__).parent

def results():
    return json.loads((R/'PROVIDER-BOUNDARY-PROBE.json').read_text())

def test_control_three_completed_failures_preceded_the_before_file_kill():
    p=results()['before_file']
    assert p['initial_exit']==98 and p['initial_recorded_sends']==3
    assert p['initial_outcomes']==['transport','transport','transport']
    assert p['stop_file_before_resume'] is None and p['manifest_stop_before_resume'] is None

def test_provider_terminal_stop_survives_kill_before_stop_file():
    p=results()['before_file']
    assert p['new_sends']==0
    assert p['resume_status']=='stopped' and p['resume_exit']==4

def test_control_kill_after_file_already_preserves_provider_stop():
    p=results()['after_file']
    assert p['initial_exit']==98 and p['new_sends']==0 and p['resume_exit']==4
    assert p['stop_file_after_resume']['kind']=='provider_failures'
    assert p['resume_status']=='stopped'
