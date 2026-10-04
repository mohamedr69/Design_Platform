"""Assertions over a fresh execution of the unchanged submitted runner.
resume_stop_probe.py generates the evidence using a scripted provider only.
"""
from pathlib import Path
import json

R=Path(__file__).parent


def test_control_initial_tripwire_really_stopped_before_second_project():
    p=json.loads((R/'CRITICAL-STOP-PROBE.json').read_text())
    assert p['initial']['status']=='stopped'
    assert p['initial']['tripwire_errors']==[1]
    assert p['initial']['requests_this_invocation']=={'16830':12}
    assert p['initial']['not_attempted'][0]['ep']=='17428'


def test_terminal_critical_stop_cannot_be_cleared_by_plain_resume():
    p=json.loads((R/'CRITICAL-STOP-PROBE.json').read_text())
    assert sum(p['resume']['requests_this_invocation'].values())==0
    assert p['resume']['stopped']==p['initial']['stopped']


def test_control_same_sandbox_declaration_and_arm_on_both_invocations():
    a=json.loads((R/'CRITICAL-STOP-initial.json').read_text())
    b=json.loads((R/'CRITICAL-STOP-resume.json').read_text())
    assert (a['declaration_sha256'],a['arm'],a['tag'],a['allowance_key']) == (b['declaration_sha256'],b['arm'],b['tag'],b['allowance_key'])
