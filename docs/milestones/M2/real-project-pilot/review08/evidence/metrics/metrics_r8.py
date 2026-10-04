"""Review 08 metrics: frozen-label results (evaluator .7, declared AI contexts) with automatic-acceptance precision and
raw-observation precision kept apart, and the pending disputes of the 13 Review 07 findings counted separately.
Two views, both declared: `frozen` scores against labels v2 as frozen (a pending dispute counts as the labels say);
`unresolved_excluded` removes judgements on finding pages from the denominators and lists them as unresolved truth.
Neither view calls a pending dispute an AI success or a confirmed error."""
import collections
import json
from pathlib import Path

E7 = Path(r"C:\t\iso\work\r8\eval7")
INDEX = json.load(open(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\review08\human-review-packet-v2\FINDINGS-INDEX.json", encoding="utf-8"))
# only the groups that need a decision are unresolved truth; a confirm-only group (the label is not disputed; the
# reading was a raw-observation error) stays counted under the frozen labels in both views
FINDING = {(i["doc"].replace("\\", "/"), int(i["page"])): g["group"] for g in INDEX["groups"] if g["status"] == "unresolved" for i in g["items"]}
RUNS = {"frozen deterministic, pilot (r7-det9, default)": "r7-det9-pilot-default.json",
        "frozen deterministic, holdout (r7-det9, default)": "r7-det9-holdout-default.json",
        "matched run: model-disabled (det9, 12 docs)": "matched-model-disabled.json",
        "matched run: AI-EV1 (default|EV1)": "matched-AI-EV1.json",
        "matched run: AI-EV2 (default|EV2)": "matched-AI-EV2.json",
        "review 06 AI-EV1, eligible projects (default|EV1, legacy profile declared)": "r6-ai-ev1-eligible-default.json"}
AUTO = ("accepted", "validated")
ERR = ("fp", "wrong")


def ratio(a, b):
    return round(a / b, 4) if b else None


out = {"evaluator": None, "views": ["frozen", "unresolved_excluded"], "unresolved_groups": sorted(set(FINDING.values())), "unresolved_pages": len(FINDING), "runs": {}}
for label, name in RUNS.items():
    r = json.load(open(E7 / name, encoding="utf-8"))
    out["evaluator"] = r["evaluator"]
    t = r["totals"]
    run = {"ai_context": r.get("ai_context"), "ai_evidence_states": t.get("ai_evidence_states"), "fields": {}, "pending_disputes": []}
    for layer in ("raw", "evidence"):
        counts = collections.defaultdict(collections.Counter)
        for d in r["documents"]:
            for j in d["layers"][layer]["judged"]:
                group = FINDING.get((d["doc"].replace("\\", "/"), int(j.get("page") or 0)))
                kind = "auto" if j.get("state") in AUTO else "observed" if j.get("state") == "observed" else "held" if j.get("state") == "held" else None
                if kind is None or j["outcome"] in ("not_scored", "unscored_page", "unscorable", "redundant"):
                    continue
                counts[j["field"]][f"{kind}:{j['outcome']}"] += 1
                if group:
                    counts[j["field"]][f"{kind}:on_finding_page:{j['outcome']}"] += 1
                    if layer == "evidence" and (j["outcome"] in ERR or j["outcome"] == "held_wrong"):
                        run["pending_disputes"].append({"group": group, "doc": d["doc"], "page": j.get("page"), "field": j["field"], "value": j.get("value"),
                                                        "label": j.get("truth"), "state": j.get("state"), "frozen_outcome": j["outcome"]})
        for field, c in counts.items():
            f = run["fields"].setdefault(field, {})
            view = {}
            for kind in ("auto", "observed"):
                ok, bad = c[f"{kind}:correct"], sum(c[f"{kind}:{e}"] for e in ERR)
                ok_u = ok - c[f"{kind}:on_finding_page:correct"]
                bad_u = bad - sum(c[f"{kind}:on_finding_page:{e}"] for e in ERR)
                view[kind] = {"frozen": {"correct": ok, "errors": bad, "precision": ratio(ok, ok + bad)},
                              "unresolved_excluded": {"correct": ok_u, "errors": bad_u, "precision": ratio(ok_u, ok_u + bad_u),
                                                      "unresolved": (ok - ok_u) + (bad - bad_u)}}
            view["held"] = {"held_correct": c["held:held_correct"], "held_wrong": c["held:held_wrong"]}
            if layer == "evidence":
                tf = t["evidence"]["fields"].get(field, {})
                view["recovery"] = {"recovery": tf.get("recovery"), "clean_recovery": tf.get("clean_recovery"), "readable": tf.get("readable")}
            f[layer] = view
    reg = t["register"]["register"]
    run["register"] = {f: {"precision_of_accepted": reg[f]["precision_of_accepted"], "accepted": reg[f]["accepted"], "tp": reg[f]["tp"],
                           "recovery_of_readable": reg[f]["recovery_of_readable"], "readable": reg[f]["readable"], "held": reg[f]["held"]}
                       for f in ("reference", "revision", "decision")}
    run["register_critical"] = len(t["register"]["critical"])
    run["introduced_ai_errors"] = [{k: c.get(k) for k in ("doc", "page", "field", "value", "truth")} for c in t["introduced_ai_errors"]]
    out["runs"][label] = run

Path(r"C:\t\iso\work\r8\METRICS-R8.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
for label, run in out["runs"].items():
    print("==", label, run["ai_evidence_states"], "reg-crit", run["register_critical"], "introduced", len(run["introduced_ai_errors"]))
    for f in ("identity", "revision", "decision"):
        v = run["fields"].get(f, {}).get("evidence")
        if not v:
            continue
        a, o = v["auto"], v["observed"]
        print(f"   {f:9s} auto {a['frozen']['correct']}/{a['frozen']['correct'] + a['frozen']['errors']} p={a['frozen']['precision']} (excl. unresolved p={a['unresolved_excluded']['precision']}, unresolved {a['unresolved_excluded']['unresolved']})"
              f" | observed p={o['frozen']['precision']} ({o['frozen']['errors']} err; excl p={o['unresolved_excluded']['precision']}, unresolved {o['unresolved_excluded']['unresolved']})"
              f" | held {v['held']} | recovery {v['recovery']['recovery']} (n={v['recovery']['readable']})")
    for p in run["pending_disputes"]:
        print("   pending:", p["group"], p["field"], p["value"], "| label", p["label"], "|", p["state"], p["frozen_outcome"])
