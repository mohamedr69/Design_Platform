"""OFFLINE replay: the stored ai-accuracy-pilot outputs (A / S / G / T rows.json, unchanged, hash-listed) scored by the
accepted evaluator .9 (frozen-r12, unchanged) under labels v1 and v2, with each arm's declared context. No model call;
nothing re-run. Reports per arm: evidence / AI-layer counts, critical acceptances split by label status, and the
per-case G->T changes with their v2 label status. Writes rescore/RESCORE-v1-v2.json."""
import hashlib
import json
import os
import pathlib
import sys

W = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
V1 = pathlib.Path("C:/t/iso/work/r2x/ai-pilot/labels")
V2 = W / "labels-v2"
RUNS = pathlib.Path("C:/t/r2x/runs")
decl = json.loads(pathlib.Path("C:/t/iso/work/r2x/ai-pilot/PILOT-DECLARATION.json").read_text(encoding="utf-8"))
os.environ.setdefault("AI_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/rescore-no-db.db")
for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT"):
    os.environ.pop(k, None)
sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
os.chdir("C:/t/iso/frozen-r12/backend")
from scripts import m2_eval5 as EV  # noqa: E402

sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(EV.__file__) == decl["code"]["evaluator"]["sha256"]
CTX = {"A": {"variant": None}}
for arm in ("S", "G", "T"):
    CTX[arm] = {"variant": "EV1", "profile": "default", "policies": [decl["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]]}
LABELS = {"v1": (V1 / "PILOT-REGISTER-LABELS.json", V1 / "PILOT-PAGE-LABELS.json", V1 / "PILOT-UNCERTAINTY-AND-EXPOSURE.json"),
          "v2": (V2 / "PILOT-REGISTER-LABELS.v2.json", V2 / "PILOT-PAGE-LABELS.v2.json", V2 / "PILOT-UNCERTAINTY-AND-EXPOSURE.v2.json")}
MATCHED = {"EP-16830/EP-16830 - PQ/EP-16830 Reply to Comments.pdf", "EP-16830/EP-16830-MS-ELV/CCTV/Nursery & Retail/Rev.01/Content 14.pdf",
           "EP-16830/EP-16830-MS-ELV/EM lighting system/Nursery & Retail/pdf/Al Arabia - Authorization.pdf"}
out = {"mode": "OFFLINE replay of stored outputs (no model call)", "evaluator": EV.EVALUATOR_VERSION,
       "rows_sha256": {a: sha(RUNS / f"ai-pilot-{a}" / "out/rows.json") for a in ("A", "S", "G", "T")},
       "labels_sha256": {v: {p.name: sha(p) for p in fs} for v, fs in LABELS.items()}, "versions": {}}
for v, (rf, pf, uf) in LABELS.items():
    reg, page, unc = (json.loads(pathlib.Path(f).read_text(encoding="utf-8")) for f in (rf, pf, uf))
    unresolved = {u["doc"] for u in unc["uncertainty"]} | {d["doc"] for d in reg["documents"] if d.get("confidence") != "high"}
    matched = MATCHED | {d["doc"] for d in reg["documents"] if "ST-SUB-BIND" in d["doc"]}
    res = {"unresolved_docs": sorted(unresolved), "arms": {}}
    per_case = {}
    for arm in ("A", "S", "G", "T"):
        rows = json.loads((RUNS / f"ai-pilot-{arm}" / "out/rows.json").read_text(encoding="utf-8"))
        ev = EV.evaluate(reg, page, rows, page.get("page1_corrections"), ai_context=CTX[arm])
        t = ev["totals"]
        crit = t["evidence"]["critical"]
        res["arms"][arm] = {
            "evidence": {f: {"recovery": x["recovery_counts"], "precision": x["precision_counts"], "accepted_precision": x["accepted_precision"],
                             "asserted_distinct": x["asserted_distinct"]} for f, x in t["evidence"]["fields"].items()},
            "ai": {f: {"recovery": x["recovery_counts"], "precision": x["precision_counts"]} for f, x in t["ai"]["fields"].items()},
            "critical_resolved": [c for c in crit if c["doc"] not in unresolved], "critical_unresolved": [c for c in crit if c["doc"] in unresolved]}
        for d in ev["documents"]:
            for f in EV.FIELDS:
                per_case.setdefault((d["doc"], f), {})[arm] = {
                    "evidence": {k: n for k, n in (d["layers"]["evidence"]["recovery"].get(f) or {}).items() if n},
                    "ai": {k: n for k, n in (d["layers"]["ai"]["recovery"].get(f) or {}).items() if n}}
    res["G_to_T_matched"] = [{"doc": doc, "field": f, "label_status": "unresolved" if doc in unresolved else "resolved", "G": a["G"], "T": a["T"]}
                             for (doc, f), a in sorted(per_case.items()) if doc in matched and a["G"] != a["T"]]
    out["versions"][v] = res
d1, d2 = out["versions"]["v1"], out["versions"]["v2"]
out["delta_v1_to_v2"] = {"resolved_status_changed": sorted(set(d1["unresolved_docs"]) ^ set(d2["unresolved_docs"])),
                         "scores_changed": {a: d1["arms"][a]["evidence"] != d2["arms"][a]["evidence"] for a in ("A", "S", "G", "T")}}
(W / "rescore").mkdir(exist_ok=True)
(W / "rescore/RESCORE-v1-v2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
print(json.dumps(out["delta_v1_to_v2"], ensure_ascii=False))
for v in ("v1", "v2"):
    print(v, [(x["doc"].split("/")[-1][:30], x["field"], x["label_status"], x["G"]["evidence"], "->", x["T"]["evidence"], "| ai", x["G"]["ai"], "->", x["T"]["ai"])
              for x in out["versions"][v]["G_to_T_matched"]])
