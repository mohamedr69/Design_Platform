"""Recorded harness-v4 edits after the first runner-probe run (review 22): resume skips a document only when the scoring
contract binds it ('bound'); the arm's ledger scope is pre-checked before the durable document charge; the scripted
discovery answer carries a decision block (four required reads per page: a 4-page reading attempts 16 > 12); dry labels
carry the scripted decision; probe / test expectations corrected (cache hits of a reread equal every call of the first
run; a new tag may use only the remaining allowance; a resumed run skips a completed project at project level)."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def patch(fn, subs):
    p = HERE / fn
    s = p.read_text(encoding="utf-8")
    for o, n in subs:
        assert s.count(o) == 1, (fn, o[:70], s.count(o))
        s = s.replace(o, n)
    p.write_text(s, encoding="utf-8")


patch("arm_ev.py", [
    ('    return att is not None and reason == ""\n', '    return att is not None and reason == "bound"\n'),
    ('state = {"consecutive_failures": 0, "stopped": None, "xtrack_refusals": 0, "allowance_refusals": 0, "allowance_busy": 0, "per_ep": {}, "requests_io": 0,\n'
     '         "cache_hits": 0, "deferred": [], "skipped_completed": [], "interrupted_seen": []}',
     'state = {"consecutive_failures": 0, "stopped": None, "xtrack_refusals": 0, "allowance_refusals": 0, "allowance_busy": 0, "ledger_precheck_refusals": 0, "per_ep": {}, "requests_io": 0,\n'
     '         "cache_hits": 0, "deferred": [], "skipped_completed": [], "skipped_projects": [], "interrupted_seen": []}'),
    ('    took = False\n    if not self.exhausted:\n        took = xtrack.take(ep, track, kw.get("task", ""), LIMIT)',
     '    took = False\n'
     '    led = getattr(self.provider, "ledger", None)\n'
     '    if not self.exhausted and led is not None:\n'
     '        # the arm\'s ledger scope is checked BEFORE the durable document allowance is charged: a request the scope would\n'
     '        # refuse is never charged to the document (other ledger limits refuse after the charge; that charge stays)\n'
     '        lim, tot = led.effective_limits(), led.totals()\n'
     '        if tot.get("breaker") or (lim.requests is not None and tot["requests"] + 1 > lim.requests):\n'
     '            state["ledger_precheck_refusals"] += 1\n'
     '            self.exhausted = f"ledger scope cap ({lim.requests} requests)" if not tot.get("breaker") else f"ledger breaker: {tot[\'breaker\']}"\n'
     '    if not self.exhausted:\n        took = xtrack.take(ep, track, kw.get("task", ""), LIMIT)'),
    ('        if project.ep_number in done and not args.reread:\n            continue',
     '        if project.ep_number in done and not args.reread:\n            state["skipped_projects"].append(project.ep_number)\n            continue'),
])
patch("dry_provider2.py", [
    ('"decision_options_printed": [],\n                         "decision_marked_option": "", "decision_mark_type": "none", "decision_actor": "unknown", "decision_region": [], "other_numbers": [], "notes": ""},',
     '"decision_options_printed": ["A = APPROVED", "B = APPROVED AS NOTED"],\n                         "decision_marked_option": "B = APPROVED AS NOTED", "decision_mark_type": "tick", "decision_actor": "consultant", "decision_region": [700, 850, 990, 990], "other_numbers": [], "notes": ""},'),
    ('            "read_decision": {"options_printed": [], "marked_option": "", "mark_type": "none", "actor": "unknown", "legible": True},',
     '            "read_decision": {"options_printed": ["A = APPROVED", "B = APPROVED AS NOTED"], "marked_option": "B = APPROVED AS NOTED", "mark_type": "tick", "actor": "consultant", "legible": True},'),
    ('  PILOT_DRY_MODE=coherent   coherent answers that make the reader spend its reads: discovery names an own identity and\n'
     '                            revision with regions (never printed on the page, so support v2 cannot validate them and the\n'
     '                            optional targeted read fires), blind reads answer the same literals, the context read too',
     '  PILOT_DRY_MODE=coherent   coherent answers that make the reader spend its reads: discovery names an own identity,\n'
     '                            revision AND a decision block with regions (four required reads per triggered page, so a\n'
     '                            4-page reading attempts 16: more than the 12-per-document cap), blind reads answer the same\n'
     '                            literals, the context read too'),
])
patch("dry_labels_r22.py", [
    ('def rec(page, ref, rev, note="synthetic"):\n    return {"page": page, "component": "sheet", "category": "drawings", "reference": ref, "printed_revision": rev, "decision": "n/a",\n            "decision_actor": None, "decision_evidence": None,',
     'def rec(page, ref, rev, decision="n/a", actor=None, evidence=None, note="synthetic"):\n    return {"page": page, "component": "sheet", "category": "drawings", "reference": ref, "printed_revision": rev, "decision": decision,\n            "decision_actor": actor, "decision_evidence": evidence,'),
    ('spec = {"EP-16830/synth/raster-6pages.pdf": ("X-DRY-1", "01", [1, 2, 3, 4, 5, 6]), "EP-16830/synth/raster-1page.pdf": ("X-DRY-1", "01", [1]),\n'
     '        "EP-17428/synth/raster-2pages.pdf": ("X-DRY-1", "01", [1, 2]), "EP-17428/synth/text-sheet.pdf": ("X-SD-7", "02", [1])}\nfor key, (ref, rev, pnos) in spec.items():',
     'DEC = ("approved as noted", "consultant", "scripted legend B marked (synthetic)")\n'
     'spec = {"EP-16830/synth/raster-6pages.pdf": ("X-DRY-1", "01", [1, 2, 3, 4, 5, 6], DEC), "EP-16830/synth/raster-1page.pdf": ("X-DRY-1", "01", [1], DEC),\n'
     '        "EP-17428/synth/raster-2pages.pdf": ("X-DRY-1", "01", [1, 2], DEC), "EP-17428/synth/text-sheet.pdf": ("X-SD-7", "02", [1], ("n/a", None, None))}\nfor key, (ref, rev, pnos, dec) in spec.items():'),
    ('                 "labels": {"kind": "synthetic sheet", "reference": ref, "revision": rev, "decision": "n/a", "system": "other", "register": True}})\n'
     '    pages[key] = {"doc": key, "sha256": f["sha256"], "stratum": "synthetic", "records": [rec(p, ref, rev) for p in pnos], "no_record_pages": {}, "unvalidated_pages": [], "unresolved": []}',
     '                 "labels": {"kind": "synthetic sheet", "reference": ref, "revision": rev, "decision": dec[0], "system": "other", "register": True}})\n'
     '    pages[key] = {"doc": key, "sha256": f["sha256"], "stratum": "synthetic", "records": [rec(p, ref, rev, *dec) for p in pnos], "no_record_pages": {}, "unvalidated_pages": [], "unresolved": []}'),
    ('"labels_version": "r22-dry-labels-2026-09-30.1"', '"labels_version": "r22-dry-labels-2026-09-30.2"'),
])
patch("runner_probes.py", [
    ('ov = run(root, ["r22dry-A", "L3-newtag2", "L3"], env={"PILOT_DRY_NEW_TAG_OVERRIDE": "1"}, name="L3-newtag-override")',
     'six_before_override = al_nt[SIX]["charged"]\nov = run(root, ["r22dry-A", "L3-newtag2", "L3"], env={"PILOT_DRY_NEW_TAG_OVERRIDE": "1"}, name="L3-newtag-override")'),
    ('                                                      "cap_holds_across_tags": al_ov[SIX]["charged"] == CAP and io_ov.get(SIX, 0) == 0,',
     '                                                      "six_page_doc_charged_before_override": six_before_override,\n'
     '                                                      "cap_holds_across_tags": al_ov[SIX]["charged"] <= CAP and io_ov.get(SIX, 0) == CAP - six_before_override,'),
    ('R["scenarios"]["S5_cache_hit"] = {"first": first, "reread": re, "fresh_sends_in_reread": sum(io_by_doc(root, "L1", pid=pid2).values()), "cache_hits_in_reread": m["runner_state"]["cache_hits"],\n'
     '                                  "fresh_sends_first_run": sum(io_1.values()), "charged_unchanged": al_1 == al_2,',
     'first_state = json.loads((root / "runs/L1/out/RUN.json.first").read_text(encoding="utf-8"))["runner_state"]\n'
     'R["scenarios"]["S5_cache_hit"] = {"first": first, "reread": re, "fresh_sends_in_reread": sum(io_by_doc(root, "L1", pid=pid2).values()), "cache_hits_in_reread": m["runner_state"]["cache_hits"],\n'
     '                                  "fresh_sends_first_run": sum(io_1.values()), "cache_hits_first_run": first_state["cache_hits"],\n'
     '                                  "charged_unchanged": {s: v["charged"] for s, v in al_1.items()} == {s: v["charged"] for s, v in al_2.items()}, "attempts_after_reread": {s[:8]: v["attempts"] for s, v in al_2.items()},'),
    ('first = run(root, ["r22dry-A", "L1", "L1"], name="L1")\nal_1 = allowance(root, *key("L1"))',
     'first = run(root, ["r22dry-A", "L1", "L1"], name="L1")\nshutil.copyfile(root / "runs/L1/out/RUN.json", root / "runs/L1/out/RUN.json.first")\nal_1 = allowance(root, *key("L1"))'),
    ('"documents_budget_stopped": budget_stops, "exhaustion_is_a_budget_stop":',
     '"documents_budget_stopped": budget_stops, "ledger_precheck_refusals": m["runner_state"]["ledger_precheck_refusals"], "exhaustion_is_a_budget_stop":'),
    ('                                             "skipped_completed": [s[:8] for s in m2["runner_state"]["skipped_completed"]], "charged_17428_unchanged":',
     '                                             "skipped_completed": [s[:8] for s in m2["runner_state"]["skipped_completed"]], "skipped_projects": m2["runner_state"]["skipped_projects"], "charged_17428_unchanged":'),
])
patch("test_runner_v4.py", [
    ('    assert all(t["binding"]["rejected"] == 0 for t in s["tripwire_binding"])',
     '    last = s["tripwire_binding"][-1]["binding"]\n'
     '    assert last["rejected"] == 0 and all(v == "eligible" for d, v in last["eligibility"].items() if d.endswith(".pdf")) and last["eligibility"]["EP-17428/synth/note.docx"] == "ineligible"'),
    ('    assert o["cap_holds_across_tags"] and o["all_within_cap"] and o["allowance_refusals"] > 0',
     '    assert o["cap_holds_across_tags"] and o["all_within_cap"] and o["allowance_refusals"] > 0 and o["six_page_doc_charged"] == 12'),
    ('    assert s["reread"]["exit"] == 0 and s["fresh_sends_in_reread"] == 0 and s["cache_hits_in_reread"] == s["fresh_sends_first_run"] > 0',
     '    assert s["reread"]["exit"] == 0 and s["fresh_sends_in_reread"] == 0 and s["cache_hits_in_reread"] == s["fresh_sends_first_run"] + s["cache_hits_first_run"] > 0'),
    ('    assert s["charged_total"] == s["requests_sent"] == s["arm_cap"]', '    assert s["charged_total"] == s["requests_sent"] == s["arm_cap"] and s["ledger_precheck_refusals"] >= 1'),
    ('    assert r["charged_17428_unchanged"] and r["sent_17428_unchanged"] and len(r["skipped_completed"]) == 2',
     '    assert r["charged_17428_unchanged"] and r["sent_17428_unchanged"] and r["skipped_projects"] == ["17428"] and "17428" not in r["requests"]'),
])
print("patched")
