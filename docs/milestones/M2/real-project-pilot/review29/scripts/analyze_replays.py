"""Offline replay analysis (diagnostic: the corpus is exposed; this is NOT fresh accuracy). For each arm L1..L4:
  - the frozen stored rows scored by .9 (must equal the final experiment) and by .10 (the evaluator change alone);
  - the flags-off replay (the OLD policy under identical replay conditions) and each switch set IG / CA / DR / PA / ALL
    (the NEW policies), each scored by .9 and by .10;
  - every changed fact between OLD and NEW under the same evaluator (key: document, page, field, own component);
  - new false acceptances: a NEW asserted fact (validated / accepted) with a critical outcome that OLD did not have;
  - decision coverage changes per page (e.g. absent_by_discovery -> unknown / read).
Runs score_replay.py in a fresh process per (rows, evaluator). Writes replay/REPLAY-ANALYSIS.json. No model request."""
import collections
import json
import pathlib
import subprocess
import sys

R = pathlib.Path(__file__).resolve().parent
PY = sys.executable
DECL = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
REG = json.loads((pathlib.Path(DECL["harness_dir"]) / DECL["labels"]["dir"] / DECL["labels"]["register"]).read_text(encoding="utf-8"))
UNC = json.loads((pathlib.Path(DECL["harness_dir"]) / DECL["labels"]["dir"] / DECL["labels"]["uncertainty"]).read_text(encoding="utf-8"))
did = {x["doc"]: x["draft_id"] for x in REG["documents"]}
resolved = {x["doc"]: x["confidence"] == "high" and x["doc"] not in {u["doc"] for u in UNC["uncertainty"]} for x in REG["documents"]}
CRIT = ("wrong", "fp", "accepted_on_conflict", "wrong_unassociated")
CONFIGS = ["IG", "CA", "DR", "PA", "ALL"]
arms = sys.argv[1:] or ["L1", "L2", "L3", "L4"]


def score(rows, policy, arm, ev, name):
    out = R / "scores" / f"{name}.e{ev}.json"
    if not out.exists():
        r = subprocess.run([PY, str(R / "score_replay.py"), str(rows), policy, arm, ev, str(out)], capture_output=True, text=True,
                           env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        if r.returncode:
            raise SystemExit(f"score failed {name} e{ev}: {r.stderr[-800:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def facts(s):
    by = collections.defaultdict(list)
    for j in s["judged"]:
        if j.get("layer") != "ai" or j.get("field") not in ("identity", "revision", "decision"):
            continue
        g = str(j.get("group") or "")
        if not g.split("@")[0].split("~")[0].endswith(":own"):
            continue
        by[(j["doc"], j["page"], j["field"])].append((j.get("value"), j.get("state"), j.get("outcome")))
    return {k: sorted(v, key=str) for k, v in by.items()}


def decisions(s):
    return {(d["doc"], int(p)): pc["own:decision"] for d in s["coverage"] for p, pc in d["pages"].items() if not pc["own:decision"].startswith("unsupported")}


def compare(old, new):
    fo, fn = facts(old), facts(new)
    changed = []
    for k in sorted(set(fo) | set(fn), key=str):
        if fo.get(k) != fn.get(k):
            changed.append({"draft_id": did.get(k[0]), "label_resolved": resolved.get(k[0]), "page": k[1], "field": k[2], "old": fo.get(k), "new": fn.get(k)})
    old_crit = {(c["doc"], c["page"], c["field"], c["value"]) for c in old["judged"] if c["state"] in ("validated", "accepted") and c["outcome"] in CRIT}
    new_false = [{"draft_id": did.get(c["doc"]), "label_resolved": resolved.get(c["doc"]), **{x: c[x] for x in ("page", "field", "value", "state", "outcome", "how")}}
                 for c in new["judged"] if c["state"] in ("validated", "accepted") and c["outcome"] in CRIT and (c["doc"], c["page"], c["field"], c["value"]) not in old_crit]
    do, dn = decisions(old), decisions(new)
    dchg = [{"draft_id": did.get(k[0]), "page": k[1], "old": do.get(k), "new": dn.get(k)} for k in sorted(set(do) | set(dn), key=str) if do.get(k) != dn.get(k)]
    return {"changed_facts": changed, "new_false_acceptances": new_false, "decision_coverage_changes": dchg,
            "recovery_old": old["recovery"], "recovery_new": new["recovery"], "precision_old": old["precision"], "precision_new": new["precision"],
            "critical_old": [(did.get(c["doc"]), c["page"], c["field"], c["value"], c["outcome"]) for c in old["critical"]],
            "critical_new": [(did.get(c["doc"]), c["page"], c["field"], c["value"], c["outcome"]) for c in new["critical"]]}


report = {"note": "diagnostic replay on the exposed four-arm corpus; not fresh accuracy; labels r26.2 frozen and unchanged", "arms": {}}
for arm in arms:
    pol = DECL["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]
    stored = R.parent.parent.parent.parent / "dummy"
    stored = pathlib.Path(f"C:/t/r2x/runs/final-{arm}/out/rows.json")
    off = pathlib.Path(f"C:/t/r2x/r29-replay/{arm}-off/out/rows.json")
    entry = {"stored": {}, "configs": {}}
    s9, s10 = score(stored, pol, arm, "9", f"stored-{arm}"), score(stored, pol, arm, "10", f"stored-{arm}")
    o9, o10 = score(off, pol, arm, "9", f"off-{arm}"), score(off, pol, arm, "10", f"off-{arm}")
    entry["stored"] = {"e9_recovery": s9["recovery"], "e9_critical": len(s9["critical"]), "e10_vs_e9_on_stored_rows": compare(s9, s10)}
    entry["off_replay_equals_stored_under_e9"] = facts(o9) == facts(s9) and o9["recovery"] == s9["recovery"]
    for c in CONFIGS:
        rows = pathlib.Path(f"C:/t/r2x/r29-replay/{arm}-{c}/out/rows.json")
        if not rows.exists():
            entry["configs"][c] = {"status": "not replayed"}
            continue
        man = json.loads((rows.parent / "REPLAY.json").read_text(encoding="utf-8"))
        n9, n10 = score(rows, man["policy_version"], arm, "9", f"{c}-{arm}"), score(rows, man["policy_version"], arm, "10", f"{c}-{arm}")
        entry["configs"][c] = {"policy": man["policy_version"], "provider": {k: v for k, v in man["provider"].items() if k != "unrecorded_requests"},
                               "unrecorded_by_task": dict(collections.Counter(u["task"] for u in man["provider"]["unrecorded_requests"])),
                               "business_hashes_equal_off": man["business_hashes"] == json.loads((off.parent / "REPLAY.json").read_text(encoding="utf-8"))["business_hashes"],
                               "e9": compare(o9, n9), "e10": compare(o10, n10)}
    report["arms"][arm] = entry
(R / "replay").mkdir(exist_ok=True)
(R / "replay" / "REPLAY-ANALYSIS.json").write_text(json.dumps(report, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
for arm, e in report["arms"].items():
    print(arm, "off==stored(e9):", e["off_replay_equals_stored_under_e9"], "| e10 vs e9 on stored: changed", len(e["stored"]["e10_vs_e9_on_stored_rows"]["changed_facts"]))
    for c, v in e["configs"].items():
        if "e9" not in v:
            print("  ", c, v)
            continue
        print("  ", c, "changed e9/e10:", len(v["e9"]["changed_facts"]), len(v["e10"]["changed_facts"]), "| new false e9/e10:", len(v["e9"]["new_false_acceptances"]),
              len(v["e10"]["new_false_acceptances"]), "| crit old->new e10:", len(v["e10"]["critical_old"]), "->", len(v["e10"]["critical_new"]),
              "| dec cov changes:", len(v["e10"]["decision_coverage_changes"]), "| unrecorded:", v["unrecorded_by_task"])
