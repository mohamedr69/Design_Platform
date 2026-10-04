"""Legacy compatibility (review 25): every provider-outcome journal the v4.2 writer produced for review24 (read-only, under
C:/t/r2x/dry-runs/r24-*) is loaded by the review24 validator (validator-1, from the frozen review24 package copy) and by
the v4.3 validator (validator-2); the results must be identical (state, streak, why), i.e. no existing valid journal is
reinterpreted (the damaged P6 journals stay indeterminate for the same reason). Each journal is loaded with its own header
binding and the documents it names, since the comparison is between validators. Writes neutral-evidence/LEGACY-RECHECK.json."""
import hashlib
import importlib.util
import json
import pathlib

import provider_journal as v2

HERE = pathlib.Path(__file__).resolve().parent
OLD = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review24/harness-v4.2/provider_journal.py")
spec = importlib.util.spec_from_file_location("provider_journal_v1", OLD)
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
rows, same = [], True
for base in sorted(pathlib.Path("C:/t/r2x/dry-runs").glob("r24-*")):
    for jf in sorted(base.rglob("PROVIDER-OUTCOMES.jsonl")):
        raw = jf.read_bytes()
        try:
            recs = [json.loads(l) for l in raw.decode("utf-8").splitlines()]
            binding = recs[0].get("binding") if recs and isinstance(recs[0], dict) else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            recs, binding = [], None
        planned = {r.get("sha256") for r in recs if isinstance(r, dict) and r.get("type") == "attempt"}
        a = v1.load(jf, binding, planned_sha256=planned)
        b = v2.load(jf, binding, planned_sha256=planned)
        key = lambda x: (x["state"], x.get("streak"), x.get("why"))
        eq = key(a) == key(b)
        same &= eq
        rows.append({"journal": str(jf.relative_to("C:/t/r2x/dry-runs")), "sha256": hashlib.sha256(raw).hexdigest(), "validator_1": key(a), "validator_2": key(b), "equal": eq,
                     "result_counts": b.get("result_counts")})
out = {"old_validator_file": str(OLD), "old_validator_sha256": hashlib.sha256(OLD.read_bytes()).hexdigest(), "new_validator": v2.VALIDATOR_REVISION,
       "journals": len(rows), "all_equal": same, "kinds_seen": {k: sum((r["result_counts"] or {}).get(k, 0) for r in rows) for k in v2.KINDS}, "rows": rows}
(HERE.parent / "neutral-evidence").mkdir(exist_ok=True)
(HERE.parent / "neutral-evidence/LEGACY-RECHECK.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
print("journals", len(rows), "all equal", same, "kinds seen", out["kinds_seen"])
