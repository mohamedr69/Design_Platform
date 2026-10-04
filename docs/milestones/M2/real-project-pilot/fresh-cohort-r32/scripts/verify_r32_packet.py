"""Checker for fresh-cohort-r32/: manifest complete and matching; markdown links; every staged file, render and crop re-hashed
against SOURCE-MANIFEST / RENDERS / CROPS; OneDrive originals unchanged (size and modified time by stat only, no read);
the draft binds the packaged selection, source manifest, renders, crop log, conventions and drafts; the drafts re-validated;
reviewer columns blank; FIELD-POPULATION not counted; the ledger, candidate and baseline trees and earlier packages
unchanged; no authorization beyond the recorded one; no response file of the reviewer is fabricated. Writes
evidence/PACKAGE-CHECK.json."""
import csv
import datetime
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import subprocess

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32")
PIL = PKG.parent
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()  # noqa: E731
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))  # noqa: E731
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True).stdout.strip()  # noqa: E731
res = {}
mf = load(PKG / "evidence/EVIDENCE-MANIFEST.json")
man = mf["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
                                and p.relative_to(PKG).as_posix() not in ("evidence/EVIDENCE-MANIFEST.json", "evidence/PACKAGE-CHECK.json") and "__pycache__" not in p.parts]}
links, broken = 0, []
for md in PKG.glob("*.md"):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists():
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
SM, RD, CR = load(PKG / "SOURCE-MANIFEST.json"), load(PKG / "RENDERS.json"), [json.loads(l) for l in (PKG / "CROPS.jsonl").read_text(encoding="utf-8").splitlines()]
SEL = load(PKG / "FROZEN-SELECTION.json")
LONG = "\\\\?\\"
bad_stage, bad_orig = [], []
for f in SM["files"]:
    if f["state"] != "staged" or sha(f["staged_path"]) != f["staged_sha256"] or f["staged_sha256"] != f["source_sha256"]:
        bad_stage.append(f["pool_id"])
    st = os.stat(LONG + SEL["project_folders"][f["ep"]] + "\\" + f["relative_path"].replace("/", "\\"))
    if st.st_size != f["bytes"] or datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat(timespec="seconds") != f["source_modified_utc"]:
        bad_orig.append(f["pool_id"])
bad_render = [f"{d['pool_id']}-p{r['page']}" for d in RD["documents"] for r in d["rendered"] if sha(f"{RD['render_dir']}/{r['png']}") != r["png_sha256"]]
bad_crop = [c["png"] for c in CR if sha(f"C:/t/r2x/r32-stage/crops/{c['png']}") != c["sha256"] or c["staged_sha256"] != next(f["staged_sha256"] for f in SM["files"] if f["pool_id"] == c["pool_id"])]
res["evidence"] = {"staged": len(SM["files"]), "bad_staged": bad_stage, "originals_changed": bad_orig, "renders": sum(len(d["rendered"]) for d in RD["documents"]), "bad_renders": bad_render,
                   "crops": len(CR), "bad_crops": bad_crop, "selection_bound_by_source_manifest": SM["selection_sha256"] == sha(PKG / "FROZEN-SELECTION.json"),
                   "renders_bound_to_source_manifest": RD["source_manifest_sha256"] == sha(PKG / "SOURCE-MANIFEST.json")}
D = load(PKG / "labels/R32-LABELS-DRAFT-1.json")
b = D["bindings"]
res["draft"] = {"sha256": sha(PKG / "labels/R32-LABELS-DRAFT-1.json"), "status_ai_not_human": "NOT human-signed" in D["status"] and "NOT independently reviewed" in D["status"],
                "model_requests_0": D["model_requests"] == 0,
                "binds_packaged_files": all(b[k] == sha(PKG / k) for k in ("FROZEN-SELECTION.json", "SOURCE-MANIFEST.json", "RENDERS.json", "CROPS.jsonl", "LABEL-CONVENTIONS-R32.md")),
                "binds_drafts": all(b["drafts"][pid] == sha(PKG / "labels/drafts" / f"{pid}.json") for pid in b["drafts"]),
                "documents": len(D["documents"]), "conventions_frozen_hash": (PKG / "LABEL-CONVENTIONS-R32.sha256").read_text(encoding="utf-8").split()[0] == sha(PKG / "LABEL-CONVENTIONS-R32.md")}
v = subprocess.run(["C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe", "C:/t/iso/work/r2x/r32/validate_drafts_r32.py"], capture_output=True, text=True,
                   env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
res["draft"]["validation"] = v.stdout.strip().splitlines()[-1] if v.stdout.strip() else v.stderr[-200:]
blank = True
for f in ("PAGE-FIELD-WORKLIST.csv", "DOCUMENT-FIELD-WORKLIST.csv"):
    with open(PKG / "review" / f, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if any(row[k] for k in row if k.startswith("reviewer_")):
                blank = False
FP = load(PKG / "FIELD-POPULATION.json")
res["review"] = {"reviewer_columns_blank": blank, "field_population_not_counted": all(v is None for v in FP["gate_counts"].values()) and FP["gate_action"] is None,
                 "no_reviewer_response_present": not any("RESPONSE" in k and "TEMPLATE" not in k for k in man)}
con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
res["ledger"] = {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0]}
con.close()
res["frozen"] = {"ledger_483_17": (res["ledger"]["entries"], res["ledger"]["scopes"]) == (483, 17),
                 "candidate": git("C:/t/iso/cand-r29", "rev-parse", "HEAD") == "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d" and not git("C:/t/iso/cand-r29", "status", "--porcelain"),
                 "baseline": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                 "review31_manifest": sha(PIL / "review31/evidence/EVIDENCE-MANIFEST.json") == "d5fe164918741014ded7425cda7679bd310a97b07511dd85bb65ec642077c460",
                 "review31_files": all(sha(PIL / "review31" / k) == x["sha256"] for k, x in load(PIL / "review31/evidence/EVIDENCE-MANIFEST.json")["files"].items()),
                 "labels_r26_2": sha("C:/t/iso/work/r2x/r27/labels-r26.2/LABEL-MANIFEST.r26.2.json") == "ed3c88e40daadaee6e4a7271d7dd9be430773a8c1b0976030d1bfb2a27a9a72d"}
res["authorization"] = {"recorded": (PKG / "AUTHORIZATION-2026-10-02.md").exists() and "> I authorize this" in (PKG / "AUTHORIZATION-2026-10-02.md").read_text(encoding="utf-8"),
                        "no_other_authorization_document": [k for k in man if re.match(r"(.*/)?AUTHORIZATION", k.upper())] == ["AUTHORIZATION-2026-10-02.md"]}
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and not bad_stage and not bad_orig and not bad_render and not bad_crop
             and res["evidence"]["selection_bound_by_source_manifest"] and res["evidence"]["renders_bound_to_source_manifest"]
             and all(v for k, v in res["draft"].items() if isinstance(v, bool)) and res["draft"]["validation"].endswith("problems 0")
             and all(res["review"].values()) and all(res["frozen"].values()) and all(bool(v) for v in res["authorization"].values()))
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1, default=str)[:4000])
print("OK" if res["ok"] else "NOT OK")
