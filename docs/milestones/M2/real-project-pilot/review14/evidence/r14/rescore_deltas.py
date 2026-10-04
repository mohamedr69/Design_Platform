"""Per-document, per-component deltas between the original-label and amended-label scores of the same stored run
(rescore/<run>__original.json vs __amended-r14.1.json), including every changed component field and critical."""
import json
import pathlib

D = pathlib.Path("C:/t/iso/work/r2x/r14/rescore")
out = {}
for f in sorted(D.glob("*__original.json")):
    name = f.name[:-len("__original.json")]
    a = json.loads(f.read_text(encoding="utf-8"))
    b = json.loads((D / f"{name}__amended-r14.1.json").read_text(encoding="utf-8"))
    da = {d["doc"]: d for d in a["documents"]}
    rows = []
    for d in b["documents"]:
        o = da.get(d["doc"])
        ca = {(c["page"], json.dumps(c["expected"], sort_keys=True, default=str)): c["fields"] for c in (o or {"layers": {"evidence": {"components": []}}})["layers"]["evidence"]["components"]}
        cb = {(c["page"], json.dumps(c["expected"], sort_keys=True, default=str)): c["fields"] for c in d["layers"]["evidence"]["components"]}
        crit_a = [(c.get("page"), c.get("field"), c.get("value")) for c in (o or {"layers": {"evidence": {"critical": []}}})["layers"]["evidence"]["critical"]]
        crit_b = [(c.get("page"), c.get("field"), c.get("value")) for c in d["layers"]["evidence"]["critical"]]
        if ca != cb or crit_a != crit_b:
            rows.append({"doc": d["doc"], "components_before": [{"page": k[0], "expected": json.loads(k[1]), "fields": v} for k, v in ca.items() if k not in cb or cb[k] != v],
                         "components_after": [{"page": k[0], "expected": json.loads(k[1]), "fields": v} for k, v in cb.items() if k not in ca or ca[k] != v],
                         "critical_before": crit_a, "critical_after": crit_b})
    out[name] = rows
    print(name, len(rows), "documents changed")
    for r in rows:
        print("   ", r["doc"][-55:], "| crit", r["critical_before"], "->", r["critical_after"])
        for c in r["components_after"]:
            print("       after ", c["page"], c["expected"].get("reference"), c["fields"])
(D / "RESCORE-DELTAS.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
