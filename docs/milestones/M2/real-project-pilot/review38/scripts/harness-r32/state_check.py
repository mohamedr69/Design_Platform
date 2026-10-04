"""Review 31 (R31-04): C starts from the intended B database state, without incompatible evidence.

check_c_start(b_db, b_recorded_sha256, c_db, c_policy_markers, evidence_tasks) verifies, read-only:
  1. B's database FILE still has the sha256 recorded when B finished (nothing wrote to B after it was frozen);
  2. C's copy has the same LOGICAL content as B (every table, ordered by rowid, hashed) -- a byte copy via the sqlite backup
     API can differ in page layout, so the logical hash is the binding one;
  3. the copy holds NO evidence of a C-only policy: no project_documents.extracted ai_evidence attempt whose policy or
     reader version carries any C marker, no evidence envelope without an attributing attempt, and no result_cache row for an evidence-reader task (B runs the accepted
     path with the evidence reader off, so any such row is of unverifiable provenance and is refused).
Returns {"ok": bool, "checks": {...}, "problems": [...]}; the runner refuses to start C unless ok."""
from __future__ import annotations

import hashlib
import json
import sqlite3


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ro(path):
    con = sqlite3.connect(f"file:{str(path).replace(chr(92), '/')}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def logical_sha256(path) -> str:
    con = _ro(path)
    h = hashlib.sha256()
    for (name,) in con.execute("select name from sqlite_master where type = 'table' and name not like 'sqlite_%' order by name"):
        h.update(name.encode())
        for row in con.execute(f'select * from "{name}" order by rowid'):
            h.update(json.dumps(list(row), default=str).encode())
    con.close()
    return h.hexdigest()


def _policies(extracted) -> list[str]:
    """Policy and reader-version strings of every evidence attempt; an envelope with no attempt is of unknown provenance
    and is reported as the string 'unattributed envelope' (refused like a C-policy envelope)."""
    ev = (extracted or {}).get("ai_evidence") or {}
    out = [f"{a.get('policy') or ''} {a.get('version') or ''}" for a in ev.get("attempts") or []]
    if ev.get("envelopes") and not ev.get("attempts"):
        out.append("unattributed envelope")
    return out


def check_c_start(b_db, b_recorded_sha256: str, c_db, c_policy_markers, evidence_tasks) -> dict:
    problems, checks = [], {}
    checks["b_file_sha256"] = file_sha256(b_db)
    if checks["b_file_sha256"] != b_recorded_sha256:
        problems.append("B database changed after it was frozen")
    checks["b_logical_sha256"], checks["c_logical_sha256"] = logical_sha256(b_db), logical_sha256(c_db)
    if checks["b_logical_sha256"] != checks["c_logical_sha256"]:
        problems.append("C copy differs from B")
    con = _ro(c_db)
    bad_env = []
    for r in con.execute("select id, extracted from project_documents where extracted like '%ai_evidence%'"):
        pols = _policies(json.loads(r["extracted"]))
        if any(m in p for p in pols for m in list(c_policy_markers) + ["unattributed envelope"]):
            bad_env.append(r["id"])
    q = ",".join("?" * len(evidence_tasks))
    bad_cache = [r[0] for r in con.execute(f"select key from result_cache where task in ({q})", list(evidence_tasks))] if evidence_tasks else []
    con.close()
    checks["documents_with_c_policy_evidence"], checks["evidence_task_cache_rows"] = bad_env, len(bad_cache)
    if bad_env:
        problems.append(f"{len(bad_env)} document(s) carry C-policy evidence")
    if bad_cache:
        problems.append(f"{len(bad_cache)} evidence-task cache row(s) of unverifiable provenance")
    return {"ok": not problems, "checks": checks, "problems": problems}
