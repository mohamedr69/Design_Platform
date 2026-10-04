"""Build RD-M2 evidence/, PACKAGE-MANIFEST.json and PACKAGE-CHECK.json.

Reads the isolated area (ISO) and the live tree read-only; writes only into the
RD-M2 package folder given. Private names are redacted from everything copied in."""
import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.abspath(os.path.join(HERE, ".."))
SCRATCH = os.path.abspath(os.path.join(ISO, ".."))
PKG = os.path.abspath(sys.argv[1])
EP = r"G:\dev (2)\dev\ep-platform"
RD1 = os.path.join(EP, "docs", "milestones", "redesign", "RD-M1")
EV = os.path.join(PKG, "evidence")
LIVE_DB = os.path.join(EP, "backend", "ep_platform.db")
USER = os.environ.get("USERNAME", "")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _private_names():
    """Names never to publish, read from data at run time (never written here)."""
    snap = os.path.join(SCRATCH, "rdm1", "db", "ep_platform.audit-snapshot.db")
    c = sqlite3.connect("file:" + urllib.parse.quote(snap.replace("\\", "/")) + "?mode=ro", uri=True)
    c.execute("PRAGMA query_only=ON")
    hosts = {w[0].split(":")[1] for w in c.execute("SELECT DISTINCT worker_id FROM background_jobs WHERE worker_id IS NOT NULL")}
    hosts = {h for h in hosts if h and not h.isdigit()}
    pname = c.execute("SELECT project_name FROM projects WHERE id=5").fetchone()[0] or ""
    libs = json.loads(c.execute("SELECT changes FROM project_redesign WHERE id=1").fetchone()[0])
    paths = [(ch.get("insert") or {}).get("library") or "" for ch in libs]
    office = {m.group(1) for p in paths for m in [re.match(r"C:/Users/([^/]+)/", p)] if m}
    orgs = {m.group(1) for p in paths for m in [re.search(r"OneDrive - <org>/\\]+)", p)] if m}
    c.close()
    # the project's full name (its words appear on their own in the repository's own test data)
    phrase = " ".join(re.findall(r"[A-Z]{5,}", pname))
    return hosts, {phrase} if phrase else set(), office, orgs


HOSTS, PWORDS, OFFICE, ORGS = _private_names()
SUBS = [(re.compile(re.escape(SCRATCH.replace("\\", "/")), re.I), "<SCRATCH>"),
        (re.compile(re.escape(SCRATCH), re.I), "<SCRATCH>"),
        (re.compile(r"OneDrive - <org>\\/\"\n]+", re.I), "OneDrive - <org>"),
        (re.compile(r"[A-Z]{4,}-AL-[A-Z]{4,}---AI-PLATFORM"), "<sibling clone folder>")]
SUBS += [(re.compile(r"C:(\\\\|\\|/)+Users(\\\\|\\|/)+" + re.escape(u) + r"(?=[\\/])", re.I), "<office PC user profile>") for u in OFFICE]
SUBS += [(re.compile(r"C:(\\\\|\\|/)+Users(\\\\|\\|/)+" + re.escape(USER) + r"(?=[\\/])", re.I), "<PC-B user profile>"),
         (re.compile(r"/c/Users/" + re.escape(USER) + r"(?=/)", re.I), "<PC-B user profile>"),
         (re.compile(r"pytest-of-" + re.escape(USER) + r"\b", re.I), "pytest-of-<PC-B user>")]
SUBS += [(re.compile(re.escape(h)), "PC-A" if i == 0 else f"PC-{chr(65 + i)}") for i, h in enumerate(sorted(HOSTS))]


def red(text):
    for p, r in SUBS:
        text = p.sub(r, text)
    return text


def put(name, text):
    p = os.path.join(EV, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(red(text))


def junit(path):
    root = ET.parse(path).getroot()
    out = {}
    for tc in root.iter("testcase"):
        name = f"{tc.get('classname')}::{tc.get('name')}"
        state, msg = "passed", ""
        for tag in ("failure", "error", "skipped"):
            el = tc.find(tag)
            if el is not None:
                state, msg = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag], (el.get("message") or "")[:300]
        out[name] = {"state": state, "message": msg, "time": float(tc.get("time") or 0)}
    return out


def main():
    os.makedirs(EV, exist_ok=True)
    W = os.path.join(ISO, "work")
    # candidate identity
    shutil.copyfile(os.path.join(W, "rdm2-candidate.patch"), os.path.join(EV, "rdm2-candidate.patch"))
    cf = json.load(open(os.path.join(W, "candidate-files.json")))
    put("candidate-files.json", json.dumps(cf, indent=1))
    for ver in ("v1", "v2"):          # the AutoCAD-validated builds, for traceability
        if os.path.isfile(os.path.join(W, f"candidate-files-{ver}.json")):
            put(f"candidate-files-{ver}.json", open(os.path.join(W, f"candidate-files-{ver}.json"), encoding="utf-8").read())
        if os.path.isfile(os.path.join(W, f"rdm2-candidate-{ver}.patch")):
            shutil.copyfile(os.path.join(W, f"rdm2-candidate-{ver}.patch"), os.path.join(EV, f"rdm2-candidate-{ver}.patch"))
    # tests
    T = os.path.join(W, "tests")
    for p in glob.glob(os.path.join(T, "*.txt")):
        put("tests/" + os.path.basename(p), open(p, encoding="utf-8", errors="replace").read())
    reg = {}
    if os.path.isfile(os.path.join(T, "junit-base.xml")) and os.path.isfile(os.path.join(T, "junit-cand.xml")):
        b, c = junit(os.path.join(T, "junit-base.xml")), junit(os.path.join(T, "junit-cand.xml"))
        count = lambda d: {s: sum(1 for v in d.values() if v["state"] == s) for s in ("passed", "failed", "error", "skipped")}  # noqa: E731
        reg = {"base": count(b), "cand": count(c), "base_total": len(b), "cand_total": len(c),
               "only_in_cand": sorted(set(c) - set(b)), "only_in_base": sorted(set(b) - set(c)),
               "state_changed": {k: {"base": b[k], "cand": c[k]} for k in set(b) & set(c) if b[k]["state"] != c[k]["state"]},
               "failed_or_error_base": {k: v for k, v in b.items() if v["state"] in ("failed", "error")},
               "failed_or_error_cand": {k: v for k, v in c.items() if v["state"] in ("failed", "error")}}
        put("tests/regression-comparison.json", json.dumps(reg, indent=1))
        for ver in ("v1", "v2"):
            if os.path.isfile(os.path.join(T, f"junit-cand-{ver}.xml")):
                cv = junit(os.path.join(T, f"junit-cand-{ver}.xml"))
                put(f"tests/regression-comparison-{ver}.json", json.dumps({
                    f"cand_{ver}": count(cv), f"cand_{ver}_total": len(cv),
                    "state_changed_vs_base": {k: {"base": b[k], f"cand_{ver}": cv[k]} for k in set(b) & set(cv)
                                              if b[k]["state"] != cv[k]["state"]},
                    "failed_or_error": {k: v for k, v in cv.items() if v["state"] in ("failed", "error")}}, indent=1))
    for extra in ("flaky-reruns.txt", "focused.txt", "tsc-base.txt", "tsc-cand.txt"):
        for d in (T, os.path.join(ISO, "tscheck")):
            p = os.path.join(d, extra)
            if os.path.isfile(p):
                put("tests/" + extra, open(p, encoding="utf-8", errors="replace").read())
    # AutoCAD validation: session 1 (v1) in iso/, session 2 (v2) in iso2/main (A, B) and iso2/erase (C)
    sessions = {"session1-v1": os.path.join(ISO, "iso"), "session2-v2-main": os.path.join(ISO, "iso2", "main"),
                "session2-v2-erase": os.path.join(ISO, "iso2", "erase")}
    for label, root in sessions.items():
        for p in glob.glob(os.path.join(root, "evidence", "*.json")):
            put(f"autocad/{label}/{os.path.basename(p)}", open(p, encoding="utf-8").read())
        runs = os.path.join(root, "uploads", "EP-30880", "redesign", "runs")
        for run in sorted(os.listdir(runs)) if os.path.isdir(runs) else []:
            for fn in ("redesign.scr", "autocad.log", "verification.json"):
                p = os.path.join(runs, run, fn)
                if os.path.isfile(p):
                    put(f"autocad/{label}/{run}/{fn}", open(p, encoding="utf-8", errors="replace").read())
        outs = sorted(glob.glob(os.path.join(root, "uploads", "EP-30880", "redesign", "*.dwg")))
        put(f"autocad/{label}/published-outputs.json", json.dumps(
            {os.path.basename(p): {"sha256": sha(p), "size": os.path.getsize(p)} for p in outs}, indent=1))
    for p in glob.glob(os.path.join(ISO, "hash", "*.json")) + glob.glob(os.path.join(ISO, "hash", "*.txt")):
        if "T0" in os.path.basename(p) and p.endswith(".json"):
            continue                                    # the full baseline lists every project's uploads: hash only
        put("hash/" + os.path.basename(p), open(p, encoding="utf-8", errors="replace").read())
    for p in glob.glob(os.path.join(HERE, "*.py")) + glob.glob(os.path.join(HERE, "*.sh")):
        put("scripts/" + os.path.basename(p), open(p, encoding="utf-8").read())

    checks = {}

    def check(name, ok, **kw):
        checks[name] = {"pass": bool(ok), **kw}

    # 1 RD-M1 package unchanged
    m1 = json.load(open(os.path.join(RD1, "PACKAGE-MANIFEST.json")))
    bad = [k for k, v in m1["entries"].items() if sha(os.path.join(RD1, k)) != v["sha256"]]
    extra = [os.path.relpath(p, RD1).replace(os.sep, "/") for p in glob.glob(os.path.join(RD1, "**", "*"), recursive=True)
             if os.path.isfile(p) and os.path.relpath(p, RD1).replace(os.sep, "/") not in m1["entries"]
             and os.path.basename(p) != "PACKAGE-MANIFEST.json"]
    check("rd_m1_package_unchanged", not bad and not extra, entries=len(m1["entries"]), mismatched=bad, extra=extra)
    # 2/3 live tree and uploads vs RDM2-T0
    t0 = json.load(open(os.path.join(ISO, "hash", "RDM2-T0.json")))["groups"]
    t1p = os.path.join(ISO, "hash", "RDM2-T1.json")
    t1 = json.load(open(t1p))["groups"]
    g0, g1 = t0["ep_platform_git_visible"], t1["ep_platform_git_visible"]
    pkg_rel = "docs/milestones/redesign/RD-M2/"
    changed = [k for k in g0 if k in g1 and g0[k]["sha256"] != g1[k]["sha256"]]
    removed = [k for k in g0 if k not in g1]
    added_out = [k for k in g1 if k not in g0 and not k.startswith(pkg_rel)]
    check("no_application_file_changes_in_live_tree", not changed and not removed and not added_out,
          files_compared=len(g0), changed=changed, removed=removed, added_outside_package=added_out,
          added_inside_package=len([k for k in g1 if k not in g0 and k.startswith(pkg_rel)]))
    i0, i1 = t0["ep_platform_ignored_relevant"], t1["ep_platform_ignored_relevant"]
    live = {"backend/ep_platform.db", "backend/ep_platform.db-wal", "backend/ep_platform.db-shm"}
    diff_up = [k for k in i0 if k not in live and (k not in i1 or i0[k].get("sha256") != i1[k].get("sha256"))]
    new_up = [k for k in i1 if k not in i0 and k not in live]
    # The owner kept using the live platform during RD-M2 (user 5's Applies on the running worker).
    # Every live upload change must be attributable to that, and none may be the candidate's.
    c = sqlite3.connect("file:" + urllib.parse.quote(LIVE_DB.replace("\\", "/")) + "?mode=ro", uri=True)
    c.execute("PRAGMA query_only=ON")
    owner_jobs = [dict(zip(("id", "kind", "status", "created_by", "created_at", "worker", "result"), r)) for r in c.execute(
        "SELECT id, kind, status, created_by_id, created_at, worker_id, result FROM background_jobs WHERE id > 121 ORDER BY id")]
    owner_activity = [dict(zip(("id", "user", "at", "action"), r)) for r in c.execute(
        "SELECT id, user_id, at, action FROM activity_events WHERE id > 972 ORDER BY id")]
    live_changes_json = c.execute("SELECT changes FROM project_redesign WHERE id=1").fetchone()[0] or ""
    probe = {"redesign_updated_at": c.execute("SELECT updated_at FROM project_redesign WHERE id=1").fetchone()[0],
             "redesign_output_status": c.execute("SELECT output_status FROM project_redesign WHERE id=1").fetchone()[0],
             "max_job": c.execute("SELECT max(id) FROM background_jobs").fetchone()[0],
             "max_activity": c.execute("SELECT max(id) FROM activity_events").fetchone()[0],
             "max_ai_usage": c.execute("SELECT max(id) FROM ai_usage").fetchone()[0]}
    probe["total_changes"] = c.total_changes
    c.close()
    job_files = {json.loads(j["result"])["file"] for j in owner_jobs if j["kind"] == "fa_redesign_apply"
                 and j["status"] == "succeeded" and j["result"]}
    candidate_like = re.compile(r" d\d+ s[0-9a-f]{12} j\d+-[0-9a-f]{10}\.dwg$|/runs/|source-readback-")
    unexplained_added = [k for k in new_up if os.path.basename(k) not in job_files]
    old_work = [k for k in diff_up if "/redesign/work-" in k]          # the running (old) code's shared work folder
    unexplained_changed = [k for k in diff_up if k not in old_work]
    candidate_in_live = [k for k in i1 if candidate_like.search(k)]
    check("live_uploads_changed_only_by_owner_activity",
          not unexplained_added and not unexplained_changed and not candidate_in_live,
          files_compared=len([k for k in i0 if k not in live]), added=len(new_up), added_explained_by_owner_jobs=len(new_up) - len(unexplained_added),
          unexplained_added=unexplained_added, changed_in_old_work_folder=old_work, unexplained_changed=unexplained_changed,
          candidate_named_files_in_live_uploads=candidate_in_live)
    gc01_inputs = [k for k in diff_up if "/ifc/" in k or "/review/" in k or "/interfaces/" in k or "redesign/library" in k]
    check("source_drawings_and_library_unchanged", not gc01_inputs and not any("/ifc/" in k for k in new_up),
          changed=gc01_inputs)
    o0, o1 = t0["outer_repo_git_visible"], t1["outer_repo_git_visible"]
    o_changed = [k for k in o0 if k not in o1 or o0[k]["sha256"] != o1[k]["sha256"]]
    check("outer_repo_only_service_logs_changed", all(k.endswith(".log") for k in o_changed), changed=o_changed)
    live_src = os.path.join(EP, "backend", "uploads", "EP-30880", "ifc", "60de2a377daa.dwg")
    check("gc01_source_dwg_unchanged", sha(live_src) == "66043c11fab9eaf5a1768ba24ed924821baecec3b6726ee70f6c529300ceec21",
          sha256=sha(live_src))
    # 4 live DB: every change since RD-M1 is the owner's (signed-in user, live worker), none the candidate's
    markers = ("rdm2-missing-block", "rdm2-erase-control", '"confirmed"', "requires_confirmation")
    check("live_db_changed_only_by_owner_activity",
          probe["total_changes"] == 0
          and all(j["created_by"] is not None for j in owner_jobs)
          and all(a["user"] is not None for a in owner_activity)
          and all((j["worker"] or "").startswith("ifc:") for j in owner_jobs if j["status"] != "queued")
          and not any(m in live_changes_json for m in markers)
          and probe["max_ai_usage"] == 729,
          probe=probe, jobs_since_rd_m1=[{k: j[k] for k in ("id", "kind", "status", "created_by", "created_at")} for j in owner_jobs],
          activity_since_rd_m1=owner_activity, candidate_markers_in_live_redesign_row=[m for m in markers if m in live_changes_json],
          note="This audit never authenticated to the live API (no session); all access was mode=ro + query_only.")
    # 5 services
    ps = subprocess.run(["powershell", "-NoProfile", "-Command",
                         "Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 8000,8001,5173,5174,5175 } | "
                         "ForEach-Object { \"$($_.LocalPort) $($_.OwningProcess)\" }"], capture_output=True, text=True).stdout
    ports = dict(sorted(tuple(map(int, ln.split())) for ln in ps.split("\n") if ln.strip()))
    check("running_services_unchanged", ports == {8000: 22592, 8001: 3644, 5173: 7420, 5174: 38548, 5175: 22960}, ports=ports)
    # 6 candidate identity and isolation of the AutoCAD run
    check("candidate_patch_bound", sha(os.path.join(EV, "rdm2-candidate.patch")) == sha(os.path.join(W, "rdm2-candidate.patch")),
          patch_sha256=sha(os.path.join(W, "rdm2-candidate.patch")))
    cand = os.path.join(ISO, "cand")
    drift = []
    for rel, h in cf["all_candidate_sha256"].items():
        p = os.path.join(cand, rel)
        if not os.path.isfile(p) or sha(p) != h:
            drift.append(rel)
    check("candidate_unchanged_since_freeze", not drift, files=len(cf["all_candidate_sha256"]), drift=drift)
    archive_like = [p for d in ("iso", "iso2") for p in glob.glob(os.path.join(ISO, d, "**", "03- Drawings*"), recursive=True)]
    check("no_archive_path_in_isolated_run", not archive_like, found=[red(p) for p in archive_like])
    # 7 private names
    needles = [h for h in HOSTS] + list(PWORDS) + list(OFFICE) + list(ORGS) + ([USER] if USER else [])
    hits = []
    for p in glob.glob(os.path.join(PKG, "**", "*"), recursive=True):
        if os.path.isfile(p) and not p.endswith((".png", ".patch")) or (os.path.isfile(p) and p.endswith(".patch")):
            t = open(p, encoding="utf-8", errors="replace").read()
            for nd in needles:
                if nd and re.search(r"(?<![A-Za-z])" + re.escape(nd) + r"(?![A-Za-z])", t, re.I):
                    hits.append((os.path.relpath(p, PKG), "name"))
            if re.search(r"[A-Z]{4,}-AL-[A-Z]{4,}---AI-PLATFORM", t):
                hits.append((os.path.relpath(p, PKG), "org"))
    check("no_private_names_in_package", not hits, names_checked=len([n for n in needles if n]), hits=sorted(set(hits)))
    # 7b code references cited in the package, against the candidate (v2)
    REFS = [("backend/app/redesign/service.py", 704, "def requires_confirmation"),
            ("backend/app/redesign/service.py", 713, "def _drawn"),
            ("backend/app/redesign/service.py", 423, "def module_library"),
            ("backend/app/redesign/service.py", 1245, "def adjust"),
            ("backend/app/redesign/service.py", 1336, "def to_cad"),
            ("backend/app/redesign/service.py", 1450, "def content_fingerprint"),
            ("backend/app/redesign/service.py", 1475, "def _refusal"),
            ("backend/app/redesign/service.py", 1503, "def output_file_for"),
            ("backend/app/redesign/service.py", 1531, "def _unique_output"),
            ("backend/app/redesign/service.py", 1538, "def _publish"),
            ("backend/app/redesign/service.py", 1638, "cad_changes = to_cad(todo)"),
            ("backend/app/redesign/service.py", 1665, "db.expire_all()"),
            ("backend/app/redesign/service.py", 1668, "raise ApplyStale"),
            ("backend/app/redesign/cad.py", 88, "def script_lines"),
            ("backend/app/redesign/cad.py", 246, "def run("),
            ("backend/app/redesign/verify.py", 94, "def verify"),
            ("backend/app/routers/redesign.py", 106, "service.apply_request"),
            ("backend/app/routers/redesign.py", 121, "confirmed: bool | None = None"),
            ("backend/app/routers/redesign.py", 131, "confirmed=body.confirmed"),
            ("backend/app/ifc/services/runners.py", 279, "job_created_at=job.created_at")]
    bad_refs = []
    for rel, line, sub in REFS:
        lines = open(os.path.join(cand, rel), encoding="utf-8").read().splitlines()
        if line > len(lines) or sub not in lines[line - 1]:
            bad_refs.append(f"{rel}:{line}")
    check("code_line_references", not bad_refs, checked=len(REFS), failed=bad_refs)
    # 8 required files
    req = ["RD-M2-REPORT.md", "IMPLEMENTATION-CONTRACT.md", "CHANGE-MAP.md", "APPROVED-DRAWN-SET.md",
           "PORTABLE-LIBRARY-RESOLUTION.md", "CAD-FAIL-CLOSED-CONTRACT.md", "OUTPUT-VERIFICATION.md",
           "IDEMPOTENCY-AND-RECOVERY.md", "CONCURRENCY-GUARD.md", "AUTOCAD-VALIDATION.md", "REGRESSION.md",
           "DATA-SAFETY-REPORT.md", "COMMANDS.md", "NEXT-MILESTONE-HANDOFF.md", "evidence"]
    missing = [r for r in req if not os.path.exists(os.path.join(PKG, r))]
    check("required_files_present", not missing, missing=missing)
    result = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "all_pass": all(v["pass"] for v in checks.values()),
              "checks": checks, "regression": {k: reg.get(k) for k in ("base", "cand", "base_total", "cand_total")} if reg else None}
    json.dump(result, open(os.path.join(PKG, "PACKAGE-CHECK.json"), "w", encoding="utf-8", newline="\n"), indent=1, default=str)
    files = {}
    for p in sorted(glob.glob(os.path.join(PKG, "**", "*"), recursive=True)):
        if os.path.isfile(p) and os.path.basename(p) != "PACKAGE-MANIFEST.json":
            files[os.path.relpath(p, PKG).replace(os.sep, "/")] = {"sha256": sha(p), "size": os.path.getsize(p)}
    json.dump({"package": pkg_rel, "files": len(files), "bytes": sum(v["size"] for v in files.values()), "entries": files},
              open(os.path.join(PKG, "PACKAGE-MANIFEST.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(json.dumps({k: v["pass"] for k, v in checks.items()}, indent=1), "all_pass", result["all_pass"])


if __name__ == "__main__":
    main()
