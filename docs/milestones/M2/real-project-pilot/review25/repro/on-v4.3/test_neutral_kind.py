"""Three actual-runner regressions plus three writer-generated valid controls."""
import json
from pathlib import Path
import pytest
import provider_journal as pj

@pytest.mark.parametrize('kind',['budget','cache_hit','none'])
def test_contradictory_neutral_result_refuses_without_dispatch(kind):
    r=json.loads((Path(__file__).parent/'NEUTRAL-KIND-PROBE.json').read_text())[kind]
    assert r['initial_exit']==98 and r['initial_sends']==3
    assert r['original_load']['state']=='ok' and r['original_load']['streak']==3
    assert r['alteration']['from']['outcome']==r['alteration']['to']['outcome']=='transport'
    assert (r['load_before_resume']['state'],r['resume_exit'],r['new_sends'])==('indeterminate',5,0)

@pytest.mark.parametrize('entry',[{'outcome':'budget: calls_per_document','cache_hit':False},{'outcome':'ok','cache_hit':True},None],ids=['valid-budget','valid-cache-hit','valid-none'])
def test_valid_neutral_result_preserves_failure_streak(tmp_path,entry):
    binding={'run':'independent-synthetic-control'}
    j=pj.Journal(tmp_path/'journal.jsonl',binding)
    j.create(lifecycle='control',pid=1)
    for e in ({'outcome':'transport','cache_hit':False},entry,{'outcome':'transport','cache_hit':False}):
        seq=j.attempt(pid=1,sha256='a'*64,task='discover_page',page=1,tier='small')
        j.result(seq,pid=1,entry=e)
    result=pj.load(j.path,binding,planned_sha256={'a'*64})
    assert result['state']=='ok' and result['streak']==2
