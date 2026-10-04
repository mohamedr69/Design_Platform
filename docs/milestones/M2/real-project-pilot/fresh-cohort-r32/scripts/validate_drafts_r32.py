"""Mechanical validation of the R32 drafts against LABEL-CONVENTIONS-R32 (no judgement of values): every pool document has a
draft; every in-scope page 1..min(pages,4) is labelled (except declared byte-identical duplicates); every field has a valid
state; present / illegible / ambiguous fields carry a region inside [0,1] and evidence; every crop named as evidence is
bound in CROPS.jsonl to the document's staged sha256 and exists with that hash; a decision 'present' has a class from the
convention; 'absent' decisions carry absent_kind. Prints problems and exits 1 if any."""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
R = {d["pool_id"]: d for d in json.loads((HERE / "RENDERS.json").read_text(encoding="utf-8"))["documents"]}
M = {r["pool_id"]: r for r in json.loads((HERE / "SOURCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]}
CROPS = {}
for line in (HERE / "CROPS.jsonl").read_text(encoding="utf-8").splitlines():
    c = json.loads(line)
    CROPS[c["png"]] = c
CROP_DIR = pathlib.Path("C:/t/r2x/r32-stage/crops")
STATES = {"present", "absent", "illegible", "ambiguous", "unsupported"}
CLASSES = {"approved", "approved as noted", "revise and resubmit", "rejected", "other"}
problems = []
for pid in sorted(R):
    f = HERE / "drafts" / f"{pid}.json"
    if not f.exists():
        problems.append((pid, "no draft"))
        continue
    d = json.loads(f.read_text(encoding="utf-8"))
    if d.get("duplicate_of"):
        if M[pid]["staged_sha256"] != M[d["duplicate_of"]]["staged_sha256"]:
            problems.append((pid, "duplicate_of a file with a different hash"))
        continue
    want = {str(i) for i in range(1, R[pid]["pages_in_scope"] + 1)}
    if set(d["pages"]) != want:
        problems.append((pid, f"pages {sorted(d['pages'])} != {sorted(want)}"))
    for pn, p in d["pages"].items():
        for fld in ("identity", "revision", "decision"):
            x = p.get(fld)
            if not x or x.get("state") not in STATES:
                problems.append((pid, pn, fld, "missing or invalid state"))
                continue
            if x["state"] in ("present", "illegible", "ambiguous"):
                reg = x.get("region")
                if not (isinstance(reg, list) and len(reg) == 4 and all(0 <= v <= 1 for v in reg) and reg[0] < reg[2] and reg[1] < reg[3]):
                    problems.append((pid, pn, fld, f"bad region {reg}"))
                ev = x.get("evidence") or []
                if not ev:
                    problems.append((pid, pn, fld, "no evidence"))
                for e in ev:
                    if e.startswith("render "):
                        if e[7:] not in {r["png"] for r in R[pid]["rendered"]}:
                            problems.append((pid, pn, fld, f"render {e} not bound"))
                        continue
                    c = CROPS.get(e)
                    if c is None:
                        problems.append((pid, pn, fld, f"crop {e} not in CROPS.jsonl"))
                    elif c["pool_id"] != pid or c["staged_sha256"] != M[pid]["staged_sha256"] or str(c["page"]) != pn:
                        problems.append((pid, pn, fld, f"crop {e} bound to {c['pool_id']} p{c['page']}"))
                    elif hashlib.sha256((CROP_DIR / e).read_bytes()).hexdigest() != c["sha256"]:
                        problems.append((pid, pn, fld, f"crop {e} hash differs"))
            if x["state"] == "present" and "literal" not in x:
                problems.append((pid, pn, fld, "present without literal"))
            if fld == "decision" and x["state"] == "present" and x.get("class") not in CLASSES:
                problems.append((pid, pn, fld, f"class {x.get('class')}"))
            if fld == "decision" and x["state"] == "absent" and x.get("absent_kind") not in ("blank_decision_area", "no_decision_area"):
                problems.append((pid, pn, fld, "absent decision without absent_kind"))
            if x["state"] in ("present", "illegible", "ambiguous") and x.get("association") not in ("resolved", "uncertain"):
                problems.append((pid, pn, fld, f"association {x.get('association')}"))
for p in problems:
    print(p)
print("drafts", len(list((HERE / "drafts").glob("F*.json"))), "problems", len(problems))
sys.exit(1 if problems else 0)
