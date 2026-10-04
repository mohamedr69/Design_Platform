"""Read-only dump of the stored evidence behind each Review 29 defect (frozen four-arm outputs): observation readings,
regions, discovery answers (io.jsonl) and frozen evaluator outcomes. No model request."""
import json, pathlib, sys
RUNS = pathlib.Path("C:/t/r2x/runs")
L = pathlib.Path("C:/t/iso/work/r2x/r27/labels-r26.2")
reg = json.loads((L / "R26.2-REGISTER-LABELS.json").read_text(encoding="utf-8"))
doc = {x["draft_id"]: x["doc"] for x in reg["documents"]}
sha = {x["draft_id"]: x["sha256"] for x in reg["documents"]}
want = {"D03": ["L4"], "D04": ["L3", "L4"], "D06": ["L3", "L4"], "D12": ["L3", "L4"], "D16": ["L1", "L2", "L3", "L4"], "D17": ["L1", "L2", "L3", "L4"],
        "D18": ["L1", "L2", "L3", "L4"], "D26": ["L1", "L2", "L3", "L4"]}
only = sys.argv[1:] or list(want)
for d in only:
    for arm in want[d]:
        rows = json.loads((RUNS / f"final-{arm}/out/rows.json").read_text(encoding="utf-8"))
        r = rows[doc[d]]
        ai = r["extracted"]["ai_evidence"]
        obs = ai["envelopes"]["default|EV1"]["observations"]
        att = ai["attempts"][-1]
        print(f"===== {d} {arm}")
        for pn, pg in sorted(att["pages"].items()):
            print(" page", pn, {k: v for k, v in (pg.get("fields") or {}).items() if not k.startswith("ref")}, "outcome", pg.get("outcome"))
        for o in obs:
            if o.get("component") in ("own", "revtok"):
                print("  obs p", o["page"], o["field"], o.get("component"), o.get("state"), repr(o.get("value")), "region", o.get("region"), "support", o.get("support"),
                      "read", o.get("read"), "tgt", o.get("target"), "assoc", (o.get("association") or {}).get("status"))
                print("     readings", [(x.get("source"), x.get("value"), x.get("label"), x.get("role")) for x in o.get("readings") or []][:6])
                print("     reasons", o.get("reasons"))
        for line in open(RUNS / f"final-{arm}/out/io.jsonl", encoding="utf-8"):
            x = json.loads(line)
            if x["sha256"] == sha[d] and x["task"] in ("discover_page", "discover_region"):
                a = x.get("answer") or {}
                print("  DISC p", x["page"], x["task"], {k: a.get(k) for k in ("page_kind", "own_identity", "own_identity_label", "own_identity_region", "own_revision", "own_revision_label", "own_revision_region",
                                                                            "decision_options_printed", "decision_marked_option", "decision_mark_type", "decision_actor", "decision_region")})
                print("     other", a.get("other_numbers"))
            elif x["sha256"] == sha[d]:
                print("  CALL p", x["page"], x["task"], json.dumps(x.get("answer"), ensure_ascii=False)[:300], [l.get("outcome") for l in x.get("log") or []])
