"""Flags-off fidelity: the replayed rows of an arm under the candidate with every Review 29 switch off, against the frozen
stored rows of that arm. Compared per document: the last attempt's observations, page fields, requests and outcomes, and
its call log (task, page, reason, tier, key, cache_hit, outcome); ignored: wall-clock fields (at, latency_ms, timeout_s),
token counts and cost (served from the record), attempt timestamps. Also: the merged envelope's observations.
Usage: compare_fidelity.py <arm>  -> FIDELITY-<arm>.json"""
import json
import pathlib
import sys

arm = sys.argv[1]
stored = json.loads(pathlib.Path(f"C:/t/r2x/runs/final-{arm}/out/rows.json").read_text(encoding="utf-8"))
replay = json.loads(pathlib.Path(f"C:/t/r2x/r29-replay/{arm}-off/out/rows.json").read_text(encoding="utf-8"))
CALL_KEYS = ("task", "page", "reason", "tier", "key", "cache_hit", "outcome", "model_requested")


def norm_attempt(a):
    if a is None:
        return None
    return {"outcome": a.get("outcome"), "version": a.get("version"), "policy": a.get("policy"), "prompts": a.get("prompts"),
            "observations": a.get("observations"), "pages": (a.get("coverage") or {}).get("pages") if a.get("coverage") else a.get("pages"),
            "calls": [{k: c.get(k) for k in CALL_KEYS} for c in a.get("calls") or []], "models": a.get("models")}


def last(row):
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    atts = ai.get("attempts") or []
    return atts[-1] if atts else None, ai


diffs = {}
same = 0
for k in sorted(set(stored) | set(replay)):
    sa, sai = last(stored.get(k))
    ra, rai = last(replay.get(k))
    a, b = norm_attempt(sa), norm_attempt(ra)
    strip = lambda obs: [{**o, "provenance": {pk: pv for pk, pv in (o.get("provenance") or {}).items() if pk != "at"}} for o in obs or []]
    env_s = {e: strip(v.get("observations")) for e, v in (sai.get("envelopes") or {}).items()}   # provenance.at is the wall clock
    env_r = {e: strip(v.get("observations")) for e, v in (rai.get("envelopes") or {}).items()}
    if a == b and env_s == env_r:
        same += 1
        continue
    d = {}
    if a != b:
        for f in set(a or {}) | set(b or {}):
            if (a or {}).get(f) != (b or {}).get(f):
                d[f] = {"stored": json.dumps((a or {}).get(f), default=str)[:600], "replay": json.dumps((b or {}).get(f), default=str)[:600]}
    if env_s != env_r:
        d["envelope_observations"] = "differ"
    diffs[k] = d
res = {"arm": arm, "documents": len(set(stored) | set(replay)), "identical": same, "different": len(diffs), "diffs": diffs}
pathlib.Path(f"C:/t/iso/work/r2x/r29/replay/FIDELITY-{arm}.json").parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(f"C:/t/iso/work/r2x/r29/replay/FIDELITY-{arm}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: res[k] for k in ("arm", "documents", "identical", "different")}))
for k, d in diffs.items():
    print(" ", k[:70], {f: (v if isinstance(v, str) else {kk: vv[:240] for kk, vv in v.items()}) for f, v in d.items()})
