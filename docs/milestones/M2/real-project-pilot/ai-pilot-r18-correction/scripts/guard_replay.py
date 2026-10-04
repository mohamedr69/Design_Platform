"""OFFLINE replay (no model call) of the earlier CONFIRMED Rev.0 acceptance through the guard: the captured readings of
the accepted EV1 run (review 13 package, r2x-small-B rows.json: EP-17428 'FA MS/Rev.01/1-7.pdf' page 4, discovery and
blind both 'Rev.0' under the printed label 'Submittal No.') with the region's source text recomputed from the
hash-checked staged source (accepted region_texts, the stored region), validated by the successor's validate_value with
the guard off (reproduces the acceptance) and on. Also the successor's positive controls (valid short identifiers).
Writes guard/GUARD-REPLAY.json."""
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

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review13/evidence/run/runs/r2x-small-B/rows.json")
KEY = "EP-17428/EP-17428 MS/FA MS/Rev.01/1-7.pdf"
SHA = "535ffbdabfcf0e50343da44cf5692d295e5ddda39824d2dd3ea75965d7e704ba"
rows = json.loads(PKG.read_text(encoding="utf-8"))
row = rows[KEY]
env = row["extracted"]["ai_evidence"]["envelopes"]["default|EV1"]
obs = env["pages"]["4"]["fields"]["own:identity"]["observations"][0]
assert obs["value"] == "Rev.0" and obs["state"] == "validated"
stage = json.loads(pathlib.Path("C:/t/r2x/small-stage/SMALL-STAGE.json").read_text(encoding="utf-8"))
f = [x for x in stage["files"] if x["sha256"] == SHA][0]
data = open("\\\\?\\" + f["path"].replace("/", "\\"), "rb").read()
assert hashlib.sha256(data).hexdigest() == SHA
page = pymupdf.open(stream=data, filetype="pdf")[3]
texts = er.region_texts(page, tuple(obs["region"]), [])
readings = [{k: v for k, v in r.items()} for r in obs["readings"]]
out = {"mode": "OFFLINE replay of a captured response (no model call)", "source": {"doc": KEY, "sha256": SHA, "page": 4, "rows_json": str(PKG).replace("\\", "/"),
                                                                                  "rows_json_sha256": hashlib.sha256(PKG.read_bytes()).hexdigest()},
       "captured_observation": {k: obs.get(k) for k in ("value", "state", "support", "readings", "region", "read")},
       "region_texts": texts}
er.GUARD_ENABLED = False
out["guard_off"] = er.validate_value("identity", readings, texts, None)
er.GUARD_ENABLED = True
out["guard_on"] = er.validate_value("identity", readings, texts, None)
controls = {}
for v in ("FAS-09", "3105", "P10781", "AR-101", "2836", "E", "EML-09", "819-TL-101", "ELEC-B16-EM-101", "EP-23091 R1", "25H-S202-NCC-SD-MEP-ELE-FA-003-R3"):
    rd = [{"source": "discovery", "value": v, "legible": True}, {"source": "blind_small", "value": v, "legible": True}]
    controls[v] = er.validate_value("identity", rd, [("text", f"No. {v}")], None)["state"]
out["positive_controls_guard_on"] = controls
assert out["guard_off"]["state"] == "validated" and out["guard_on"]["state"] == "candidate" and out["guard_on"]["guard"] == "bare_revision_token"
assert set(controls.values()) == {"validated"}
d = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18/guard")
d.mkdir(exist_ok=True)
(d / "GUARD-REPLAY.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
print("guard off:", out["guard_off"]["state"], "| guard on:", out["guard_on"]["state"], out["guard_on"].get("guard"), "| region text:", [t[:1] + (t[1][:60],) for t in texts])
print("controls:", controls)
