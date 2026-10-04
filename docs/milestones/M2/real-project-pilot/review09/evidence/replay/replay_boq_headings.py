"""Review 09 (R9-04): the stored Review 06 BOQ verifier results whose recorded reason names a heading, re-validated
under the prior policy (e02a8c1, pinned as frozen-r8) and the candidate policy (frozen-r9). No model call. The stored
results keep the blind part / quantity / description but not the heading flag or legibility: the flag is restored
only where the stored reason records the heading answer; legibility is taken as recorded (a stored verdict of an
illegible reading would carry that reason)."""
import importlib.util
import json
import sys

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

sys.path.insert(0, "C:/t/iso/frozen-r9/backend")
prior = load("er_prior_r8", "C:/t/iso/frozen-r8/backend/app/ai/evidence_reader.py")
cand = load("er_cand_r9", "C:/t/iso/frozen-r9/backend/app/ai/evidence_reader.py")
out = []
for run in ("boq-ev1", "boq-ev1b"):
    d = json.load(open(f"C:/t/r6/{run}/out/BOQ-EV1.json", encoding="utf-8"))
    items = []
    def walk(x):
        if isinstance(x, dict):
            if "state" in x and "row" in x:
                items.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(d)
    for i in items:
        if not any("heading" in str(r) for r in i.get("reasons") or []):
            continue
        row = {k: i["row"].get(k) for k in ("part_number", "quantity", "description")}
        blind = {**(i.get("blind") or {}), "row_is_heading": True, "legible": True}
        out.append({"run": run, "page": i.get("page"), "row": row, "blind": i.get("blind"), "stored_state": i["state"],
                    "stored_reasons": i.get("reasons"), "truth": i.get("truth"),
                    "prior_policy": {k: v for k, v in prior.validate_boq_row(dict(row), dict(blind)).items() if k in ("state", "row_type", "reasons")},
                    "candidate_policy": {k: v for k, v in cand.validate_boq_row(dict(row), dict(blind)).items() if k in ("state", "row_type", "reasons")}})
json.dump(out, open("C:/t/iso/work/r9/replay-boq-headings.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for o in out:
    print(o["run"], o["row"], "| stored", o["stored_state"], "| prior", o["prior_policy"]["state"], o["prior_policy"].get("row_type"), "| candidate", o["candidate_policy"]["state"], o["candidate_policy"].get("row_type"), "| truth", o["truth"])
