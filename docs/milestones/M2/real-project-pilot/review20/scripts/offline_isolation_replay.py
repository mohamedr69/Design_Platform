"""OFFLINE isolation replay (exposed-data diagnostic; no model request, no application change): the SAME stored S model
responses (every own identity / revision observation of the accepted-reader S arms: ai-accuracy-pilot S and continuation
S) re-validated under nested support policies, ONE change per step, everything else held fixed:

  P0  guard off, accepted region text      (the accepted clip on the displayed rectangle; S as it ran)
  P1  guard ON,  accepted region text      (G only)
  P2  guard ON,  rotation-correct clip     (text layer clipped through the derotation matrix; NO local OCR)
  P3  guard ON,  rotation-correct clip + local OCR fallback when the region has no text   (= region_texts_v2)

Held fixed in every policy: the stored readings (discovery + blind; identical responses), the stored region, the
validation rule (validate_value of the candidate tree, whose rule equals the accepted one apart from the guard), and
the OCR-line input (none: the processing sandbox's cached title-block OCR lines are not replayed, for every policy alike).
Each outcome is judged against the labels (v2 for the pilot; the continuation labels): validated_correct /
validated_wrong / held (candidate / conflict / unreadable). Writes isolation/OFFLINE-ISOLATION-REPLAY.json."""
import collections
import hashlib
import json
import os
import pathlib
import sys

os.environ["AI_ENABLED"] = "false"
for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT"):
    os.environ.pop(k, None)
sys.path.insert(0, "C:/t/iso/cand-ai3/backend")
os.chdir("C:/t/iso/cand-ai3/backend")
import pymupdf  # noqa: E402

from app.ai import evidence_reader as er  # noqa: E402

LONG = "\\\\?\\"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
SETS = {
    "pilot-S": {"rows": "C:/t/r2x/runs/ai-pilot-S/out/rows.json", "sample": "C:/t/iso/work/r2x/ai-pilot/PILOT-SAMPLE.json",
                "labels": "C:/t/iso/work/r2x/ai-pilot-r18/labels-v2/PILOT-REGISTER-LABELS.v2.json",
                "uncertainty": "C:/t/iso/work/r2x/ai-pilot-r18/labels-v2/PILOT-UNCERTAINTY-AND-EXPOSURE.v2.json"},
    "continuation-S": {"rows": "C:/t/r2x/runs/cont-S/out/rows.json", "sample": "C:/t/iso/work/r2x/ai-pilot-r18/CONTINUATION-SAMPLE.json",
                       "labels": "C:/t/iso/work/r2x/ai-pilot-r18/labels-continuation/CONT-REGISTER-LABELS.json",
                       "uncertainty": "C:/t/iso/work/r2x/ai-pilot-r18/labels-continuation/CONT-UNCERTAINTY-AND-EXPOSURE.json"},
}


def rotation_clip_only(page, region):
    clip = er.crop_clip(page, region, pad=0.35)
    try:
        text = page.get_text("text", clip=clip * page.derotation_matrix)
    except Exception:  # noqa: BLE001
        text = ""
    return [("text", text)] if text.strip() else []


POLICIES = {"P0": (False, lambda pg, r: er.region_texts(pg, r, [])),
            "P1": (True, lambda pg, r: er.region_texts(pg, r, [])),
            "P2": (True, rotation_clip_only),
            "P3": (True, lambda pg, r: er.region_texts_v2(pg, r, [], ocr_timeout=30.0))}


def judge(state, value, truth, field):
    if state != "validated":
        return f"held:{state}"
    if truth in (None, "", "absent", "n/a"):
        return "validated_no_truth"
    return "validated_correct" if er.literal_key(field, value) == er.literal_key(field, truth) else "validated_wrong"


out = {"mode": "OFFLINE, exposed data, identical stored responses (no model request)", "policies": {k: v for k, v in {
    "P0": "guard off, accepted region text", "P1": "guard on, accepted region text", "P2": "guard on, rotation-correct clip only",
    "P3": "guard on, rotation-correct clip + local OCR fallback"}.items()}, "sets": {}, "inputs": {}}
for name, s in SETS.items():
    out["inputs"][name] = {k: sha(v) for k, v in s.items()}
    rows = json.loads(pathlib.Path(s["rows"]).read_text(encoding="utf-8"))
    docs = {d["doc_key"]: d for d in json.loads(pathlib.Path(s["sample"]).read_text(encoding="utf-8"))["documents"]}
    labels = {d["doc"]: d for d in json.loads(pathlib.Path(s["labels"]).read_text(encoding="utf-8"))["documents"]}
    unc = {u["doc"] for u in json.loads(pathlib.Path(s["uncertainty"]).read_text(encoding="utf-8"))["uncertainty"]}
    cases = []
    for key, row in rows.items():
        env = (((row.get("extracted") or {}).get("ai_evidence") or {}).get("envelopes") or {}).get("default|EV1") or {}
        for pno, pg in sorted((env.get("pages") or {}).items()):
            for fk in ("own:identity", "own:revision"):
                for o in (pg.get("fields") or {}).get(fk, {}).get("observations") or []:
                    if not o.get("region"):
                        continue          # no region: nothing to support (the policies cannot differ)
                    d = docs[key]
                    data = open(LONG + d["staged_path"].replace("/", "\\"), "rb").read()
                    assert hashlib.sha256(data).hexdigest() == d["sha256"]
                    page = pymupdf.open(stream=data, filetype="pdf")[int(pno) - 1]
                    field = o["field"]
                    lab = labels[key]
                    truth = lab["labels"].get("reference" if field == "identity" else "revision")
                    readings = [r for r in o.get("readings") or [] if not r.get("excluded")]
                    res = {}
                    for p, (guard, texts_of) in POLICIES.items():
                        er.GUARD_ENABLED = guard
                        texts = texts_of(page, tuple(o["region"]))
                        v = er.validate_value(field, readings, texts, o.get("deterministic"))
                        res[p] = {"state": v["state"], "support": v.get("support"), "judged": judge(v["state"], v.get("value"), truth, field)}
                    cases.append({"doc": key, "page": pno, "field": field, "value": o.get("value"), "truth": truth, "rotation": page.rotation,
                                  "label_status": "unresolved" if (key in unc or lab.get("confidence") != "high") else "resolved",
                                  "blind_read": any(str(r.get("source", "")).startswith("blind") and r.get("legible") for r in readings), **res})
    summary = {p: dict(collections.Counter(c[p]["judged"] for c in cases)) for p in POLICIES}
    steps = {f"{a}->{b}": [{"doc": c["doc"].split("/")[-1], "field": c["field"], "rotation": c["rotation"], a: c[a]["judged"], b: c[b]["judged"]}
                           for c in cases if c[a]["judged"] != c[b]["judged"]] for a, b in (("P0", "P1"), ("P1", "P2"), ("P2", "P3"))}
    out["sets"][name] = {"cases": cases, "summary": summary, "changes_by_step": steps}
d = pathlib.Path("C:/t/iso/work/r2x/review20/isolation")
d.mkdir(parents=True, exist_ok=True)
(d / "OFFLINE-ISOLATION-REPLAY.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
for name, v in out["sets"].items():
    print(name, "cases", len(v["cases"]))
    for p, s in v["summary"].items():
        print("  ", p, s)
    for step, ch in v["changes_by_step"].items():
        print("   step", step, ch)
