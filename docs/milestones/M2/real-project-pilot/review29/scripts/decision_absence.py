"""Decision absence per configuration (offline replay): on every in-scope page, an `absent_by_discovery` decision is a
VERIFIED absence when the frozen truth has no decision on that page (UR / n/a / no record) and a WRONG absence when it has
one. Unknown (failed / budget / not attempted / located only) is neither. Writes replay/DECISION-ABSENCE.json."""
import json, pathlib, collections
R = pathlib.Path(__file__).resolve().parent
L = pathlib.Path("C:/t/iso/work/r2x/r27/labels-r26.2")
reg = json.loads((L / "R26.2-REGISTER-LABELS.json").read_text(encoding="utf-8"))
page = json.loads((L / "R26.2-PAGE-LABELS.json").read_text(encoding="utf-8"))["documents"]
did = {x["doc"]: x["draft_id"] for x in reg["documents"]}
def has_decision(doc, p):
    recs = [r for r in page.get(doc, {}).get("records", []) if r["page"] == p]
    return bool(recs) and recs[0].get("decision") not in (None, "", "UR", "n/a")
out = {}
for arm in ("L1", "L2", "L3", "L4"):
    for c in ("off", "DR", "ALL"):
        s = json.loads((R / "scores" / f"{c}-{arm}.e10.json").read_text(encoding="utf-8"))
        cnt, wrong, dec_pages = collections.Counter(), [], {}
        for d in s["coverage"]:
            for pn, pc in d["pages"].items():
                cls = pc["own:decision"]
                if cls.startswith("unsupported"):
                    continue
                truth = has_decision(d["doc"], int(pn))
                if cls == "discovery_absent":
                    cnt["verified_absence" if not truth else "wrong_absence"] += 1
                    if truth:
                        wrong.append(f"{did[d['doc']]} p{pn}")
                elif cls == "completed_read":
                    cnt["completed_read"] += 1
                else:
                    cnt["unknown:" + cls] += 1
                if truth:
                    dec_pages[f"{did[d['doc']]} p{pn}"] = cls
        out[f"{arm}/{c}"] = {"counts": dict(cnt), "wrong_absence_pages": wrong, "decision_pages": dec_pages}
(R / "replay" / "DECISION-ABSENCE.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
for k, v in out.items():
    print(k, {x: v["counts"].get(x, 0) for x in ("completed_read", "verified_absence", "wrong_absence")}, "wrong:", v["wrong_absence_pages"], "| dec pages:", v["decision_pages"])
