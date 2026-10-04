"""Independent synthetic contract checks; no application import and no provider.
Set REVIEW16_CODE to a successor harness directory to replay unchanged.
"""
import importlib.util,os
from pathlib import Path
import pytest
S=Path(os.environ.get('REVIEW16_CODE','C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review15/evidence/r15'))
spec=importlib.util.spec_from_file_location('contract_under_review',S/'boq_contract.py')
bc=importlib.util.module_from_spec(spec);spec.loader.exec_module(bc)
def rows():
 truth=[dict(page=1,ordinal=1,description='Manual call point',part_number='MCP',quantity=1),dict(page=1,ordinal=2,y=200,description='Control panel',part_number='PANEL',quantity=1),dict(page=1,ordinal=3,description='Manual call point with cover',part_number='MCP',quantity=2)]
 anchor=dict(page=1,id='anchor',y=200,description='Control panel',part_number='PANEL',quantity=1)
 below=dict(page=1,id='below-anchor',y=300,description='Manual call point',part_number='MCP',quantity=1)
 return truth,anchor,below
@pytest.mark.parametrize('anchor_emitted',[True,False])
def test_verified_source_position_constrains_all_fallback_matches(anchor_emitted):
 truth,anchor,below=rows()
 result=bc.join_rows(([anchor] if anchor_emitted else [])+[below],truth)
 accepted=[(eid,ordinal) for eid,ordinal,state in result['pairs'] if state.startswith('matched')]
 assert ('below-anchor',1) not in accepted, result
@pytest.mark.parametrize('reverse',[False,True])
def test_above_anchor_positive_control(reverse):
 truth,anchor,above=rows();above.update(id='above-anchor',y=100)
 emitted=[above,anchor]
 if reverse:truth.reverse();emitted.reverse()
 result=bc.join_rows(emitted,truth)
 assert ('above-anchor',1,'matched') in result['pairs']
 assert ('anchor',2,'matched_geometry') in result['pairs']
def test_scored_values_still_cannot_choose_a_truth_row():
 truth,anchor,below=rows(); first=bc.join_rows([anchor,below],truth)
 for qty,part in [(2,'MCP'),(0,'OTHER'),(None,None)]:
  below.update(quantity=qty,part_number=part)
  assert bc.join_rows([anchor,below],truth)==first
