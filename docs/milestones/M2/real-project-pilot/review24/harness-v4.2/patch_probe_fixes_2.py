"""Recorded harness-v4 edits after the second runner-probe run (review 22): (1) the synthetic sheet gets a per-page marker
INSIDE the scripted revision region too, so no read of a later page is a cache hit of an earlier one (the second probe
showed read_revision cache hits on pages 2-3, which kept a killed-and-resumed 6-page reading under the 12 cap by
construction); (2) the cache-hit control (S5) is accounted per document: a document whose first reading completed must
show zero fresh sends and an unchanged charge on reread, and every document's fresh sends on reread must equal its charge
delta (a cache hit charges nothing; a fresh send is charged exactly once; a reading that had stopped on the reader's
per-reading constant may continue into its remaining allowance)."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def patch(fn, subs):
    p = HERE / fn
    s = p.read_text(encoding="utf-8")
    for o, n in subs:
        assert s.count(o) == 1, (fn, o[:70], s.count(o))
        s = s.replace(o, n)
    p.write_text(s, encoding="utf-8")


patch("make_dry_stage_r22.py", [
    ('    page.insert_text(pymupdf.Point(W * 0.77, H * 0.775), f"SHEET {sheet}", fontsize=9)\n',
     '    page.insert_text(pymupdf.Point(W * 0.77, H * 0.775), f"SHEET {sheet}", fontsize=9)\n'
     '    page.insert_text(pymupdf.Point(W * 0.91, H * 0.93), f"S{sheet}", fontsize=9)      # inside the scripted revision region as well\n'),
])
patch("runner_probes.py", [
    ('first_state = json.loads((root / "runs/L1/out/RUN.json.first").read_text(encoding="utf-8"))["runner_state"]\n',
     'first_state = json.loads((root / "runs/L1/out/RUN.json.first").read_text(encoding="utf-8"))["runner_state"]\n'
     'first_rows = json.loads((root / "runs/L1/out/rows.json").read_text(encoding="utf-8"))\n'
     'io_2 = io_by_doc(root, "L1", pid=pid2)\n'
     'per_doc = {}\n'
     'for s_ in al_1:\n'
     '    att = next((v["extracted"]["ai_evidence"]["attempts"][-1] for v in first_rows.values() if v.get("sha256") == s_ and (v.get("extracted") or {}).get("ai_evidence")), None)\n'
     '    stopped = bool(att and any(str(c.get("outcome", "")).startswith("budget") for c in att.get("calls") or []))\n'
     '    per_doc[s_[:8]] = {"first_reading_budget_stopped": stopped, "charged_before": al_1[s_]["charged"], "charged_after": al_2[s_]["charged"], "fresh_sends_in_reread": io_2.get(s_, 0),\n'
     '                       "fresh_equals_charge_delta": io_2.get(s_, 0) == al_2[s_]["charged"] - al_1[s_]["charged"], "completed_doc_unchanged": (not stopped) and io_2.get(s_, 0) == 0 and al_1[s_]["charged"] == al_2[s_]["charged"]}\n'),
    ('                                  "charged_unchanged": {s: v["charged"] for s, v in al_1.items()} == {s: v["charged"] for s, v in al_2.items()}, "attempts_after_reread": {s[:8]: v["attempts"] for s, v in al_2.items()},',
     '                                  "charged_unchanged": {s: v["charged"] for s, v in al_1.items()} == {s: v["charged"] for s, v in al_2.items()}, "attempts_after_reread": {s[:8]: v["attempts"] for s, v in al_2.items()},\n'
     '                                  "per_document": per_doc, "counter_delta": sum(xtrack_used(root, ep) for ep in ("16830", "17428")) - sum(used_1.values()),'),
])
patch("test_runner_v4.py", [
    ('    assert s["reread"]["exit"] == 0 and s["fresh_sends_in_reread"] == 0 and s["cache_hits_in_reread"] == s["fresh_sends_first_run"] + s["cache_hits_first_run"] > 0\n'
     '    assert s["charged_unchanged"] and s["counter_unchanged"] and sum(s["requests_in_reread_process"].values()) == 0',
     '    assert s["reread"]["exit"] == 0 and s["cache_hits_in_reread"] >= s["fresh_sends_first_run"] > 0\n'
     '    docs = s["per_document"]\n'
     '    assert all(d["fresh_equals_charge_delta"] for d in docs.values()), "a cache hit charges nothing; a fresh send is charged once"\n'
     '    assert all(d["completed_doc_unchanged"] for d in docs.values() if not d["first_reading_budget_stopped"]) and any(not d["first_reading_budget_stopped"] for d in docs.values())\n'
     '    assert s["counter_delta"] == s["fresh_sends_in_reread"] == sum(s["requests_in_reread_process"].values()) and all(d["charged_after"] <= 12 for d in docs.values())'),
])
print("patched 2")
