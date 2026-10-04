"""OFFLINE replay (no model call) that separates the deterministic support fix from model variability: every S
own-identity / own-revision observation that S held (candidate) is re-validated with ITS OWN captured readings and
region, only the region's source text recomputed by the successor's rotation-correct `region_texts_v2` (text layer
clipped through the derotation matrix; local OCR where the region has no text). Validation is the unchanged
validate_value. If the held value validates, the S->T2 gain on that fact is attributable to region support, not to a new
model read. Runs over the continuation S arm and the pilot S arm. Writes support/SUPPORT-REPLAY.json."""
import hashlib
import json
import os
import pathlib
import sys

os.environ["AI_ENABLED"] = "false"
sys.path.insert(0, "C:/t/iso/cand-ai2/backend")
os.chdir("C:/t/iso/cand-ai2/backend")
import pymupdf  # noqa: E402

from app.ai import evidence_reader as er  # noqa: E402

LONG = "\\\\?\\"
SETS = {"continuation-S": ("C:/t/r2x/runs/cont-S/out/rows.json", "C:/t/iso/work/r2x/ai-pilot-r18/CONTINUATION-SAMPLE.json"),
        "pilot-S": ("C:/t/r2x/runs/ai-pilot-S/out/rows.json", "C:/t/iso/work/r2x/ai-pilot/PILOT-SAMPLE.json")}
out = {"mode": "OFFLINE replay of captured S readings (no model call)", "sets": {}}
for name, (rows_f, sample_f) in SETS.items():
    rows = json.loads(pathlib.Path(rows_f).read_text(encoding="utf-8"))
    docs = {d["doc_key"]: d for d in json.loads(pathlib.Path(sample_f).read_text(encoding="utf-8"))["documents"]}
    res = []
    for key, row in rows.items():
        env = (((row.get("extracted") or {}).get("ai_evidence") or {}).get("envelopes") or {}).get("default|EV1") or {}
        for pno, pg in (env.get("pages") or {}).items():
            for fk in ("own:identity", "own:revision"):
                for o in (pg.get("fields") or {}).get(fk, {}).get("observations") or []:
                    if o.get("state") != "candidate" or not o.get("region"):
                        continue
                    d = docs[key]
                    data = open(LONG + d["staged_path"].replace("/", "\\"), "rb").read()
                    assert hashlib.sha256(data).hexdigest() == d["sha256"]
                    page = pymupdf.open(stream=data, filetype="pdf")[int(pno) - 1]
                    old_texts = er.region_texts(page, tuple(o["region"]), [])
                    new_texts = er.region_texts_v2(page, tuple(o["region"]), [], ocr_timeout=30.0)
                    readings = [r for r in o.get("readings") or [] if not r.get("excluded")]
                    again_old = er.validate_value(o["field"], readings, old_texts, o.get("deterministic"))
                    again_new = er.validate_value(o["field"], readings, new_texts, o.get("deterministic"))
                    res.append({"doc": key, "page": pno, "field": o["field"], "value": o.get("value"), "rotation": page.rotation,
                                "stored_reasons": o.get("reasons"), "read": o.get("read"),
                                "accepted_support": {"state": again_old["state"], "support": again_old.get("support")},
                                "rotation_correct_support": {"state": again_new["state"], "support": again_new.get("support"),
                                                             "sources": [t[0] for t in new_texts]}})
    out["sets"][name] = res
d = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18/support")
d.mkdir(exist_ok=True)
(d / "SUPPORT-REPLAY.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
for name, res in out["sets"].items():
    for r in res:
        print(name, r["doc"].split("/")[-1][:34], r["field"], r["value"], "rot", r["rotation"], "| read", r["read"], "| accepted:", r["accepted_support"]["state"],
              "-> rotation-correct:", r["rotation_correct_support"]["state"], r["rotation_correct_support"]["support"])
