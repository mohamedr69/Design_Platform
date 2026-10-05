"""Offline Review 19 regression contracts; imports run the synthetic probes (no model/network/database)."""
import pytest
import efficiency_probes as p

def test_unseen_raster_decision_is_incomplete_not_absent():
    actual=p.results['raster_stamp']
    assert actual['stamp_outside']
    assert actual['fields']['own:decision']==p.er.LOCATED_ABSENCE, actual

def test_matched_completed_does_not_include_incomplete_required_fields():
    assert not p.results['matched_with_incomplete_fields'], p.results['matched_with_incomplete_fields']

@pytest.mark.parametrize('angle',[0,90,180,270])
def test_actual_locator_coordinate_and_support_controls(angle):
    actual=next(x for x in p.results['actual_locator_rotation_controls'] if x['rotation']==angle)
    assert actual['contains'] and actual['source_supported'],actual

def test_partial_crop_identity_absence_control():
    facts=p.er.PageFacts(1,'PROJECT EXAMPLE '*10,[],[])
    assert p.er._absent({'located':True},'identity',facts)==p.er.LOCATED_ABSENCE

def test_full_page_absence_control():
    facts=p.er.PageFacts(1,'PROJECT EXAMPLE '*10,[],[])
    assert p.er._absent({'located':True,'whole_page':True},'decision',facts)==p.er.ABSENT_BY_DISCOVERY
