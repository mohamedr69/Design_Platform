"""M2 review 07 (R7-03): evidence lifecycle -- last-good evidence per page kept beside additive attempts; the actual
extraction profile bound through the entry point, the request cache and the envelope."""
import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\ai\evidence_reader.py")
s = p.read_text(encoding="utf-8")
i = s.index("def evidence_stage(")
LIFECYCLE = r'''MAX_ATTEMPTS_KEPT = 12


def envelope_key(profile: str, variant: str) -> str:
    return f"{profile}|{variant}"


def _normalise_ai(previous: dict | None) -> dict:
    """The stored `ai_evidence` in the lifecycle shape {envelopes, current_key, attempts}. A review 06 flat envelope
    becomes one envelope whose pages keep its observations -- its own profile / variant / hash, as recorded (a
    missing profile stays unknown, it is not assumed)."""
    if not previous:
        return {"envelopes": {}, "current_key": None, "attempts": []}
    if "envelopes" in previous:
        return {"envelopes": dict(previous["envelopes"]), "current_key": previous.get("current_key"),
                "attempts": list(previous.get("attempts") or [])}
    pages: dict = {}
    for o in previous.get("observations") or []:
        pages.setdefault(str(o.get("page") or 1), {"observations": [], "provenance": {
            "attempt": "legacy", "version": previous.get("version"), "policy": previous.get("policy"),
            "variant": previous.get("variant"), "profile": previous.get("profile"), "read_sha256": previous.get("read_sha256")}})["observations"].append(o)
    key = envelope_key(previous.get("profile") or "unknown", previous.get("variant") or "unknown")
    env = {"profile": previous.get("profile"), "variant": previous.get("variant"), "read_sha256": previous.get("read_sha256"),
           "pages": pages, "stale": None}
    return {"envelopes": {key: _flatten(env)}, "current_key": key,
            "attempts": [{"attempt": "legacy", "outcome": (previous.get("coverage") or {}).get("outcome"), "calls": previous.get("calls")}]}


def _flatten(env: dict) -> dict:
    env["observations"] = [dict(o, provenance=page["provenance"]) for _p, page in sorted(env.get("pages", {}).items(), key=lambda kv: int(kv[0]))
                           for o in page["observations"]]
    return env


def merge_evidence(previous: dict | None, attempt: dict, *, sha256: str, profile: str, variant: str) -> dict:
    """The row's `ai_evidence` after one attempt. Pages the attempt read completely ('evidence' / 'no_components')
    replace those pages; every other page keeps its last-good evidence with its own provenance (never restamped). A
    failed or budget-stopped attempt changes no evidence. The envelope of another profile or variant is untouched;
    one read from other bytes is marked stale, not current. The attempt itself is kept (bounded history)."""
    ai = _normalise_ai(previous)
    key = envelope_key(profile, variant)
    for k, env in ai["envelopes"].items():
        if env.get("read_sha256") and env.get("read_sha256") != sha256 and not env.get("stale"):
            ai["envelopes"][k] = {**env, "stale": "source bytes changed since this evidence was read"}
    env = ai["envelopes"].get(key)
    if env is None or env.get("stale"):
        retained = env
        env = {"profile": profile, "variant": variant, "read_sha256": sha256, "pages": {}, "stale": None}
        if retained is not None:
            ai.setdefault("superseded", []).append({"key": key, "stale": retained.get("stale"), "read_sha256": retained.get("read_sha256"),
                                                    "pages": sorted(retained.get("pages", {}))})
    provenance = {"attempt": attempt["attempt"], "version": attempt.get("version"), "policy": attempt.get("policy"),
                  "prompts": attempt.get("prompts"), "models": attempt.get("models"), "variant": variant, "profile": profile,
                  "read_sha256": sha256, "at": attempt.get("at")}
    by_page: dict = {}
    for o in attempt.get("observations") or []:
        by_page.setdefault(str(o.get("page") or 1), []).append(o)
    pages = dict(env.get("pages") or {})
    for entry in (attempt.get("coverage") or {}).get("pages") or []:
        if entry.get("outcome") in ("evidence", "no_components"):
            pages[str(entry["page"])] = {"observations": by_page.get(str(entry["page"]), []), "provenance": provenance,
                                         "coverage": entry}
    env = _flatten({**env, "pages": pages})
    ai["envelopes"][key] = env
    if pages or ai.get("current_key") is None:
        ai["current_key"] = key
    summary = {k: attempt.get(k) for k in ("attempt", "at", "outcome", "version", "policy", "variant", "profile", "error", "models")}
    summary.update(read_sha256=sha256, pages={str(e.get("page")): e.get("outcome") for e in (attempt.get("coverage") or {}).get("pages") or []},
                   calls=attempt.get("calls"))
    ai["attempts"] = (ai["attempts"] + [summary])[-MAX_ATTEMPTS_KEPT:]
    return ai


def current_evidence(ai: dict | None) -> dict:
    """The current, non-stale envelope (what an evaluator or a consumer may read as current evidence)."""
    ai = _normalise_ai(ai) if ai and "envelopes" not in ai else (ai or {})
    env = (ai.get("envelopes") or {}).get(ai.get("current_key"))
    return {} if not env or env.get("stale") else env


def cached_ocr_lines(sha256: str, index: int) -> list:
    """The title-block OCR words with their boxes (display coordinates), as the reader cached them -- region-bound
    support for a vector / scanned title block. Never a new OCR run here."""
    from app.services import document_control, page_cache

    try:
        cached = page_cache.get_ocr(sha256, index, document_control.TITLE_BLOCK_OCR_VARIANT)
        return json.loads(cached) if cached else []
    except Exception:  # noqa: BLE001 -- no cached boxes is no OCR support, not a failure
        return []


def evidence_stage(db, project, rows: list, *, provider=None, ctx=None, variant: str | None = None, profile: str | None = None) -> dict:
    """Background evidence reading for rows this processing run read (M2 review 06/07): after the deterministic
    reading and the existing AI stage, never from a GET handler. Writes only `extracted["ai_evidence"]`: last-good
    evidence per page beside the attempts (`merge_evidence`); the records, the row's reference / revision / status
    and any engineer value are left as they are. `profile`: the extraction profile the rows were read under (default
    `document_control.extraction_profile()`), bound into the cache key and the envelope."""
    import datetime

    from app.ai.budget import open_budget
    from app.services import document_control
    from app.ai import submittal_reader

    variant = variant or configured_variant()
    profile = profile or document_control.extraction_profile()
    counts = {"variant": variant, "profile": profile, "documents": 0, "calls": 0, "cache_hits": 0, "failed": 0, "budget_stopped": 0}
    if variant == "off" or not rows:
        return counts
    blocked = submittal_reader.available(project, provider)
    if blocked is not None:
        counts["not_run"] = blocked
        return counts
    provider = provider or submittal_reader.get_provider()
    for number, (row, path) in enumerate(rows, 1):
        if ctx is not None:
            ctx.progress(number, len(rows), f"Checking evidence with the AI — {number} of {len(rows)}", phase="ai_evidence")
            ctx.check()
        if not str(path).lower().endswith(".pdf") or not row.sha256 or not isinstance(row.extracted, dict):
            continue
        run = EvidenceRun(db=db, project_id=project.id, provider=provider, budget=open_budget(db, project.id), variant=variant,
                          profile=profile)
        previous = row.extracted.get("ai_evidence")
        attempt_no = len(_normalise_ai(previous)["attempts"]) + 1
        attempt = {"attempt": attempt_no, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                   "version": READER_VERSION, "policy": EVIDENCE_POLICY_VERSION, "prompts": dict(PROMPTS)}
        try:
            with document_control._open_pdf(path) as pdf:
                pages = range(min(pdf.page_count, MAX_PAGES_PER_DOCUMENT))
                ocr = {i: cached_ocr(row.sha256, i) for i in pages}
                boxes = {i: cached_ocr_lines(row.sha256, i) for i in pages}
                observations, coverage = read_document(run, pdf, sha256=row.sha256, records=row.extracted.get("records") or [],
                                                       observations=row.extracted.get("observations") or [], ocr_texts=ocr, ocr_lines=boxes)
            attempt.update(outcome=coverage.get("outcome"), coverage=coverage, observations=observations)
        except Exception as exc:  # noqa: BLE001 -- evidence is best effort: the row's reading and last-good evidence stand
            attempt.update(outcome="failed", error=f"{type(exc).__name__}: {exc}"[:300], coverage={"pages": []}, observations=[])
            counts["failed"] += 1
        attempt["calls"] = run.log
        attempt["models"] = sorted({c.get("model") for c in run.log if c.get("model")})
        row.extracted = {**row.extracted, "ai_evidence": merge_evidence(previous, attempt, sha256=row.sha256, profile=profile, variant=variant)}
        counts["documents"] += 1
        counts["calls"] += run.calls
        counts["cache_hits"] += run.cache_hits
        counts["budget_stopped"] += bool(run.exhausted)
        db.commit()
    return counts
'''
s = s[:i] + LIFECYCLE
p.write_text(s, encoding="utf-8")
print("ok")
