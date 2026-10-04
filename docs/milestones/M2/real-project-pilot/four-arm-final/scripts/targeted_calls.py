"""Every targeted call (task read_field_context) of a targeted arm, read-only: reason, page, discovery route, source region
(page coordinates of the field's final region; the call record itself does not store the image crop), result, the first
reading and the targeted reading, whether the targeted reading changed the first reading, and the frozen evaluator's
outcome for that page / field (correct, wrong, held ..., or no scored emission). Calls on a page map to its fields in the
reader's fixed order (identity, then revision) among the fields that recorded a targeted state other than not_attempted.
Usage: targeted_calls.py <arm> <tag> <score_dir>  ->  TARGETED-<arm>.json"""
import json
import pathlib
import sys

arm, tag, score = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
HERE = pathlib.Path(__file__).resolve().parent
D = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
LD = pathlib.Path(D["harness_dir"]) / D["labels"]["dir"]
REG = json.loads((LD / D["labels"]["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((LD / D["labels"]["page"]).read_text(encoding="utf-8"))
UNC = json.loads((LD / D["labels"]["uncertainty"]).read_text(encoding="utf-8"))
did = {x["doc"]: x["draft_id"] for x in REG["documents"]}
conf = {x["doc"]: x["confidence"] for x in REG["documents"]}
unc = {u["doc"] for u in UNC["uncertainty"]}
EV = json.loads((score / f"eval-{arm}.json").read_text(encoding="utf-8"))
pol = D["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]
rows = json.loads((pathlib.Path("C:/t/r2x/runs") / tag / "out/rows.json").read_text(encoding="utf-8"))
norm = lambda v: " ".join(str(v or "").upper().split())


def truth(doc, page, field):
    recs = [r for r in PAGE["documents"].get(doc, {}).get("records", []) if r["page"] == page]
    if not recs:
        return None
    return recs[0].get("reference" if field == "identity" else "printed_revision")


def judged(doc, page, field):
    d = next((x for x in EV["documents"] if x["doc"] == doc), None)
    return [(j.get("state"), j.get("value"), j.get("outcome")) for j in ((d or {}).get("layers") or {}).get("evidence", {}).get("judged") or []
            if j.get("page") == page and j.get("field") == field and str(j.get("group", "")).endswith(":own")]


out = []
for doc, r in rows.items():
    ai = ((r.get("extracted") or {}).get("ai_evidence") or {})
    atts = [a for a in ai.get("attempts") or [] if a.get("policy") == pol]
    if not atts:
        continue
    a = atts[-1]
    obs = (ai.get("envelopes") or {}).get("default|EV1", {}).get("observations") or []
    by_page = {}
    for c in a.get("calls") or []:
        if c.get("task") == "read_field_context":
            by_page.setdefault(c.get("page"), []).append(c)
    for page, calls in by_page.items():
        pg = (a.get("pages") or {}).get(str(page)) or {}
        fl = pg.get("fields") or {}
        fields = [f for f in ("identity", "revision") if fl.get(f"own:{f}:targeted") and not str(fl[f"own:{f}:targeted"]).startswith("not_attempted")]
        for i, c in enumerate(calls):
            f = fields[i] if i < len(fields) else None
            o = next((x for x in obs if x.get("page") == page and x.get("field") == f and x.get("component") == "own"), None) if f else None
            rd = (o or {}).get("readings") or []
            first = next((x for x in rd if x.get("source") != "blind_context" and x.get("source") != "discovery"), None) or next((x for x in rd if x.get("source") == "discovery"), None)
            tgt = next((x for x in rd if x.get("source") == "blind_context"), None)
            t = truth(doc, page, f) if f else None
            ev = judged(doc, page, f) if f else []
            prim = fl.get(f"own:{f}:primary") if f else None
            if c.get("outcome") != "ok" or tgt is None:
                effect = "no reading (" + str(c.get("outcome"))[:60] + ")"
            elif first is not None and norm(first.get("value")) != norm(tgt.get("value")):
                effect = "changed the first reading"
            elif prim != "completed" and fl.get(f"own:{f}:targeted") == "completed":
                effect = "completed the field with the same value as the first (" + str((first or {}).get("source")) + ") reading"
            else:
                effect = "redundant: confirmed the first reading"
            out.append({"draft_id": did.get(doc), "doc": doc, "label_resolved": conf.get(doc) == "high" and doc not in unc, "page": page, "field": f,
                        "reason": c.get("reason"), "route": fl.get("discovery:route"), "source_region_pt": (o or {}).get("region"),
                        "call_outcome": c.get("outcome"), "model": c.get("model"), "input_tokens": c.get("input_tokens"), "output_tokens": c.get("output_tokens"),
                        "primary_state": fl.get(f"own:{f}:primary") if f else None, "targeted_state": fl.get(f"own:{f}:targeted") if f else None,
                        "first_reading": first and {k: first.get(k) for k in ("source", "value", "label")},
                        "targeted_reading": tgt and {k: tgt.get(k) for k in ("value", "label", "role", "excluded")},
                        "final_state": (o or {}).get("state"), "final_value": (o or {}).get("value"), "truth": t,
                        "targeted_value_matches_truth_literally": None if (tgt is None or t is None) else norm(tgt.get("value")) == norm(t),
                        "effect": effect, "evaluator": ev,
                        "classification": ("redundant" if effect.startswith("redundant") else "no effect" if effect.startswith("no reading") else
                                           ("correct" if any(x[2] == "correct" for x in ev) else "wrong" if any(x[2] in ("wrong", "fp") for x in ev) else
                                            "held" if any("held" in str(x[2]) for x in ev) else "no scored emission"))})
(HERE / f"TARGETED-{arm}.json").write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
for x in out:
    print(x["draft_id"], "p", x["page"], x["field"], "|", x["reason"], "|", x["route"], "|", x["call_outcome"], "| first", (x["first_reading"] or {}).get("value"),
          "| targeted", (x["targeted_reading"] or {}).get("value"), "| truth", x["truth"], "|", x["effect"], "|", x["classification"], x["evaluator"])
