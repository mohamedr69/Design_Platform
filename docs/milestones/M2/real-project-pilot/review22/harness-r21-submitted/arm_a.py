# DERIVED from ai-pilot-r18/cont_a.py by derive_r21_runners.py -- four-arm A base (accepted app path, AI on, evidence off); every reader switch unset
# DERIVED from ai-accuracy-pilot/pilot_a.py by derive_runners.py -- continuation A base (accepted app path, AI on, evidence off); stage manifest name from the declaration; track cont-A
"""AI accuracy pilot, the common A base: the accepted application's own sync / processing / persistence path
(C:/t/iso/frozen-r12 at 3d5607d) over the pilot stage, AI enabled with the evidence reader OFF (the application's
existing AI path), in a disposable sandbox C:/t/r2x/runs/<tag>. S, G and T start from copies of its database.
Adapted from the Round 2 runner r2x_ev0.py; differences: the pilot declaration and its A ledger scope; no
"busy in the last 24 h" refusal -- instead the declared worst case (the A scope cap, 12) is asserted to fit every
project's remaining cross-track allowance before starting; actual requests are recorded to xtrack afterwards.

Usage: pilot_a.py <tag> --declaration PILOT-DECLARATION.json --declaration-sha SHA"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import sys
import time

a = argparse.ArgumentParser()
a.add_argument("tag"); a.add_argument("--declaration", required=True); a.add_argument("--declaration-sha", required=True)
args = a.parse_args()
assert hashlib.sha256(pathlib.Path(args.declaration).read_bytes()).hexdigest() == args.declaration_sha, "the declaration changed"
decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
STAGE = pathlib.Path(decl["stage"]["root"])
assert hashlib.sha256((STAGE / decl["stage"]["manifest"]).read_bytes()).hexdigest() == decl["stage"]["manifest_sha256"], "stage manifest changed"
LONG = "\\\\?\\"
for f in json.loads((STAGE / decl["stage"]["manifest"]).read_text(encoding="utf-8"))["files"]:
    assert hashlib.sha256(open(LONG + f["path"], "rb").read()).hexdigest() == f["sha256"] == decl["sources"]["sample"]["documents"][f["doc_key"]], f["doc_key"]
sys.path.insert(0, "C:/t/iso/work/r2x/ai-pilot")
import dry_provider as dry  # noqa: E402

RUNS = pathlib.Path(dry.DRY_RUNS if dry.DRY else "C:/t/r2x/runs")
ROOT = RUNS / args.tag
DB = ROOT / "db" / "default.db"
if ROOT.exists():
    sys.exit(f"{ROOT} exists: a run is never repeated over its own sandbox")
for d in ("db", "cache", "library", "uploads", "out"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)
scope = decl["ledger"]["scopes"]["A"]
if dry.DRY:
    scope = {**scope, "env": {**scope["env"], "AI_LEDGER_PATH": dry.DRY_LEDGER}}
env = {"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads"),
       "AI_ENABLED": "true", "AI_EVIDENCE_VARIANT": "off", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "",
       "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
       "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DOCUMENT_CLASSIFICATION_V2": "false", "SYNC_FILE_WORKERS": "0",
       "EXTRACTION_PROMOTE_OBSERVATIONS": "false", "LIBRARY_RESCAN_SECONDS": "0", **decl["provider"]["env"], **scope["env"]}
for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT", "AI_EVIDENCE_SUPPORT", "AI_EVIDENCE_SCHEDULING", "AI_EVIDENCE_DEADLINE", "AI_EVIDENCE_ROI"):
    os.environ.pop(k, None)
os.environ.update(env)
B = pathlib.Path(decl["code"]["accepted_app"]["tree"]) / "backend"
sys.path.insert(0, str(B)); os.chdir(B)
sys.path.insert(0, "C:/t/iso/work/r2x/run")
import xtrack  # noqa: E402

if dry.DRY:
    xtrack.PATH = dry.DRY_XTRACK
from app.core.config import Settings, get_settings  # noqa: E402

st = get_settings()
assert DB.as_posix() in st.database_url and str(ROOT) in st.cache_root and str(ROOT) in st.library_root and str(ROOT) in st.uploads_root, "sandbox roots not in force"
assert st.ai_enabled and st.ai_evidence_variant == "off" and not st.extraction_promote_observations and st.ai_ledger_scope == scope["scope"]
for k, v in decl["application_limits"].items():
    assert getattr(st, k) == v == Settings.model_fields[k].default, f"application limit {k} is not the frozen default"
import app  # noqa: E402

if dry.DRY:
    dry.install()

assert pathlib.Path(app.__file__).resolve().is_relative_to(B.resolve()), app.__file__
from fastapi.testclient import TestClient  # noqa: E402

import app.routers.jobs as jobs_router  # noqa: E402
from app.main import app as api  # noqa: E402
from app.services import document_control  # noqa: E402

jobs_router.RUN_INLINE = True
eps = sorted(p.name for p in STAGE.iterdir() if p.is_dir() and p.name.startswith("EP-"))
assert set(e[3:] for e in eps) <= set(decl["authorization"]["projects_resolved"]), "a stage project outside the declaration"
LIMIT = decl["application_limits"]["ai_max_calls_per_project_per_day"]
before = {e[3:]: xtrack.used(e[3:]) for e in eps}
assert all(LIMIT - n >= scope["limits"]["requests"] for n in before.values()), f"A's worst case would not fit a project's remaining day allowance: {before}"
manifest = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tag": args.tag, "track": "A",
            "declaration_sha256": args.declaration_sha, "dry_run": dry.DRY, "stage": str(STAGE), "database": str(DB), "parser": document_control.PARSER_VERSION,
            "project_day_before": before,
            "settings": {k: getattr(st, k) for k in ("ai_enabled", "ai_provider", "ai_model_small", "ai_model_standard", "ai_evidence_variant",
                                                     "ai_ledger_path", "ai_ledger_scope", "ai_ledger_limits", "sync_file_workers", "tesseract_cmd",
                                                     *decl["application_limits"])}, "projects": {}}
with TestClient(api) as client:
    login = client.post("/auth/login", json={"email": st.default_admin_email, "password": st.default_admin_password})
    assert login.status_code == 200, login.text
    for ep in eps:
        t0 = time.perf_counter()
        created = client.post("/projects", json={"ep_number": ep[3:], "project_name": ep, "source_folder_path": str(STAGE / ep), "design_sheets": []})
        assert created.status_code == 201, created.text
        pid = created.json()["id"]
        job = client.post(f"/projects/{pid}/jobs/sync-documents").json()
        result = client.get(f"/jobs/{job['id']}").json()
        processing = client.get(f"/jobs/{result['result']['processing_job_id']}").json() if (result.get("result") or {}).get("processing_job_id") else None
        manifest["projects"][ep] = {"project_id": pid, "seconds": round(time.perf_counter() - t0, 1), "sync_job": {k: result.get(k) for k in ("status", "error")},
                                    "processing_job": {k: (processing or {}).get(k) for k in ("status", "error")}, "processing_result": (processing or {}).get("result")}
        print(ep, "A processing", (processing or {}).get("status"),
              {k: ((processing or {}).get("result") or {}).get(k) for k in ("planned", "processed", "failed", "partial", "read_by_ai")},
              round(time.perf_counter() - t0, 1), "s", flush=True)
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
rows = {}
for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.size, d.reference, d.revision, d.status, d.system_code, d.extracted "
                     "from project_documents d join projects p on p.id = d.project_id"):
    rows[f"EP-{r['ep_number']}/{r['relative_path']}".replace("\\", "/")] = {
        "id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"], "size": r["size"],
        "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
        "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
usage = [dict(u) for u in con.execute("select u.id, p.ep_number, u.task, u.model, u.input_tokens, u.output_tokens, u.cached_input_tokens, u.reasoning_tokens, "
                                      "u.estimated_cost, u.latency_ms, u.cache_hit, u.escalated, u.outcome, u.at from ai_usage u left join projects p on p.id = u.project_id order by u.id")]
tables = {t: con.execute(f"select count(*) from {t}").fetchone()[0] for t in
          ("project_documents", "project_submittals", "project_shop_drawings", "background_jobs", "project_actions", "ai_usage", "document_readings")}
con.close()
fresh = [u for u in usage if not u["cache_hit"]]
by_ep = {}
for u in fresh:
    dt = datetime.datetime.fromisoformat(str(u["at"]))
    at = (dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)).timestamp()
    by_ep.setdefault(u["ep_number"], []).append((at, u["task"]))
for ep, items in by_ep.items():
    xtrack.record(ep, "r21-A", items)
manifest.update({"tables": tables, "rows": len(rows), "ai_usage_rows": len(usage), "fresh_requests": len(fresh),
                 "fresh_by_project": {ep: len(v) for ep, v in by_ep.items()}})
out = ROOT / "out"
json.dump(manifest, open(out / "RUN.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(rows, open(out / "rows.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(out / "usage.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", args.tag, "A", tables, "rows", len(rows), "fresh requests", len(fresh))
