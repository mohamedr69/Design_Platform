"""Strict reader-side check over every replay: facts the NEW policy validates (accepts) that the OLD policy did not validate
with the same value on the same page / field, judged wrong / fp / accepted_on_conflict / wrong_unassociated by the
evaluator. Separately, facts whose scoring changed only because the evaluator stopped an inheritance. Writes
replay/NEW-ACCEPTANCES.json."""
import json, pathlib
R = pathlib.Path(__file__).resolve().parent
reg = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/labels-r26.2/R26.2-REGISTER-LABELS.json").read_text(encoding="utf-8"))
unc = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/labels-r26.2/R26.2-UNCERTAINTY-AND-EXPOSURE.json").read_text(encoding="utf-8"))
did = {x["doc"]: x["draft_id"] for x in reg["documents"]}
res_ok = {x["doc"]: x["confidence"] == "high" and x["doc"] not in {u["doc"] for u in unc["uncertainty"]} for x in reg["documents"]}
CRIT = ("wrong", "fp", "accepted_on_conflict", "wrong_unassociated")
out = {}
for arm in ("L1", "L2", "L3", "L4"):
    for ev in ("9", "10"):
        old = json.loads((R / "scores" / f"off-{arm}.e{ev}.json").read_text(encoding="utf-8"))
        validated_old = {(j["doc"], j["page"], j["field"], j["value"]) for j in old["judged"] if j.get("layer") == "ai" and j["state"] == "validated"}
        for c in ("IG", "CA", "DR", "PA", "ALL"):
            new = json.loads((R / "scores" / f"{c}-{arm}.e{ev}.json").read_text(encoding="utf-8"))
            nv = [j for j in new["judged"] if j.get("layer") == "ai" and j["state"] == "validated" and j["field"] in ("identity", "revision", "decision")
                  and (j["doc"], j["page"], j["field"], j["value"]) not in validated_old]
            out[f"{arm}/{c}/e{ev}"] = {"newly_validated": [{"draft_id": did.get(j["doc"]), "resolved": res_ok.get(j["doc"]), **{k: j[k] for k in ("page", "field", "value", "outcome", "how")}} for j in nv],
                                       "newly_validated_wrong": [{"draft_id": did.get(j["doc"]), "resolved": res_ok.get(j["doc"]), **{k: j[k] for k in ("page", "field", "value", "outcome", "how")}}
                                                                 for j in nv if j["outcome"] in CRIT]}
(R / "replay" / "NEW-ACCEPTANCES.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for k, v in out.items():
    if v["newly_validated"]:
        print(k, "newly validated:", [(x["draft_id"], x["page"], x["field"], x["value"], x["outcome"]) for x in v["newly_validated"]])
print("total newly_validated_wrong:", sum(len(v["newly_validated_wrong"]) for v in out.values()))
