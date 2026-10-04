"""Review 07: re-validate the stored real-model readings (AI-EV1 / AI-EV2, review 06) under evidence-policy .2 -- no
model call. Every stored reading (discovery, blind, escalated) is kept; support is rebuilt from the staged PDF page
inside the stored read region (and the title-block OCR words the EV0 run cached); decisions get the page's replayed
own identity as their target. What a replay cannot reproduce: identities discovery referenced (not stored in .1), and
any prompt / model change. Usage: replay_policy2.py <rows.json> <out rows.json>"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("AI_ENABLED", "false")
os.environ["CACHE_ROOT"] = r"C:\t\r6\ai-ev0\cache"
sys.path.insert(0, r"C:\t\iso\ep-platform\backend")
os.chdir(r"C:\t\iso\ep-platform\backend")
import pymupdf  # noqa: E402

from app.ai import evidence_reader as er  # noqa: E402

STAGE = Path(r"C:\t\pilot\stage")
rows = json.load(open(sys.argv[1], encoding="utf-8"))
changes = {}
out = {}
for key, row in rows.items():
    ex = (row or {}).get("extracted") or {}
    ai = ex.get("ai_evidence") or {}
    obs = ai.get("observations") or []
    if not obs:
        out[key] = row
        continue
    path = STAGE / key.replace("\\", "/")
    new_obs = []
    try:
        pdf = pymupdf.open(path)
    except Exception as exc:  # noqa: BLE001
        out[key] = {**row, "replay_error": str(exc)}
        continue
    by_page = {}
    for o in obs:
        by_page.setdefault(int(o.get("page") or 1), []).append(o)
    for page_no, items in sorted(by_page.items()):
        page = pdf[page_no - 1]
        boxes = er.cached_ocr_lines(row.get("sha256") or "", page_no - 1)
        own = None
        for o in items:
            if o.get("field") not in ("identity", "revision"):
                continue
            region = tuple(o["region"]) if o.get("region") else None
            texts = er.region_texts(page, region, boxes)
            verdict = er.validate_value(o["field"], o.get("readings") or [], texts, o.get("deterministic"))
            if o["field"] == "identity" and verdict["state"] in ("validated", "candidate"):
                own = verdict.get("value")
            n = {**o, "policy": er.EVIDENCE_POLICY_VERSION + " (replay of stored readings)", "state": verdict["state"],
                 "value": verdict.get("value"), "reasons": verdict["reasons"], "support": verdict.get("support"),
                 "component": "own", "role": "own", "policy_1_state": o.get("state")}
            new_obs.append(n)
            changes.setdefault(f"{o['field']}:{o.get('state')}->{verdict['state']}", []).append((key, page_no, o.get("value")))
        for o in items:
            if o.get("field") != "decision":
                continue
            target = own or o.get("deterministic_identity") or next((r.get("reference") for r in ex.get("records") or [] if int(r.get("page") or 1) == page_no), None)
            verdict = er.validate_decision(o.get("readings") or [], target)
            n = {**o, "policy": er.EVIDENCE_POLICY_VERSION + " (replay of stored readings)", "state": verdict["state"],
                 "value": verdict.get("decision"), "reasons": verdict["reasons"], "target": target, "component": "own",
                 "role": "own", "policy_1_state": o.get("state"), "policy_1_value": o.get("value")}
            new_obs.append(n)
            changes.setdefault(f"decision:{o.get('state')}->{verdict['state']}", []).append((key, page_no, o.get("value")))
    out[key] = {**row, "extracted": {**ex, "ai_evidence": {**ai, "policy": er.EVIDENCE_POLICY_VERSION + " (replay)", "observations": new_obs}}}
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1, default=str)
summary = {k: len(v) for k, v in sorted(changes.items())}
json.dump({"transitions": summary, "detail": changes}, open(sys.argv[2].replace(".json", "-transitions.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(summary, indent=1))
