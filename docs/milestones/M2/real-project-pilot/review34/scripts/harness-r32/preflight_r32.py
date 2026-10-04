"""ORCH-05C (Review 34 RC-3, RC-4, RC-5): the ONE preflight of a live run, executed by runner_r32 before it consumes the
owner's authorization AND again by every live lane_r32 process (so a lane started directly runs the same checks and the
same guard). Also: the declaration contract of live mode, the ledger-scope check and the live ledger difference check.

Live declaration contract (ORCH-07 writes it; this task writes none). Every key is REQUIRED; a missing or different
value refuses the run (no silent default in live mode):
  binding_manifest_sha256, run_set_sha256        the binding manifest and the run-set file this run uses
  run.stamp, run.folder                          one run folder per declaration: run.folder == SANDBOX_BASE/<stamp>;
                                                 it holds the ONE allowance, project-day counter and capture store
  authorization.path, .owner_token_sha256        the pinned authorization path (beside the declaration) and the owner
                                                 token digest (dispatch_guard_r32)
  caps {"B": 240, "C": 240, "R": 40, "P": 36}    exactly the plan v2 section 7 caps (at most 556)
  project_day_limit                              an integer 1..60 (plan: 60 per project per UTC day, all lanes)
  lane_switches {"B": {...}, "C": {...}, "R": {...}, "P": {}}
                                                 the AI_EVIDENCE_* switches of each lane (P re-sends payloads: {})
  provider_env                                   AI_PROVIDER, AI_MODEL_STANDARD, AI_MODEL_SMALL, AI_EFFORT, AI_TIMEOUT_S,
                                                 AI_CLI_TIMEOUT_S, AI_CLAUDE_CLI, AI_LEDGER_PATH, AI_LEDGER_SCOPE,
                                                 AI_LEDGER_LIMITS (+ any other AI_* key, also verified); never AI_ENABLED
                                                 or an AI_EVIDENCE_* key
  ledger {path, scope, limits, wrap_provider: true}
                                                 LedgerProvider wraps the real provider and writes to this scope; the
                                                 scope must ALREADY exist with exactly these limits (this harness never
                                                 creates a scope); limits.requests <= sum(caps)
Live ledger behaviour (RC-4): the 'AI ledger unchanged' assertion is DRY ONLY. Live: before dispatch the declared scope
must exist with exactly the declared limits and a closed breaker; after the run the ledger may have grown only inside the
declared scope (no new scope, no limit amendment, every other scope unchanged) and by at most sum(caps) dispatch entries.
Read-only throughout: every ledger open is file:...?mode=ro with uri=True."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess

import dispatch_guard_r32 as DG
import inputs_r32 as I
import labels_adapter_r32 as A
import score_bcr_r32 as S

SANDBOX_BASE = pathlib.Path("C:/t/r2x/r34-sandbox")
HEADS = {"C:/t/iso/frozen-r12": I.BASELINE_HEAD, "C:/t/iso/cand-r29": I.CANDIDATE_HEAD}
PLAN_CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
PLAN_PROJECT_DAY_LIMIT = 60
LANES = ("B", "C", "R", "P")
REQUIRED_PROVIDER_ENV = ("AI_PROVIDER", "AI_MODEL_STANDARD", "AI_MODEL_SMALL", "AI_EFFORT", "AI_TIMEOUT_S", "AI_CLI_TIMEOUT_S",
                         "AI_CLAUDE_CLI", "AI_LEDGER_PATH", "AI_LEDGER_SCOPE", "AI_LEDGER_LIMITS")
KNOWN_PROVIDERS = ("claude-code", "claude_code", "subscription", "claude", "anthropic", "openai", "gpt")
# provider_env key -> (application setting, comparison)
SETTINGS_OF = {"AI_PROVIDER": ("ai_provider", str), "AI_MODEL_STANDARD": ("ai_model_standard", str), "AI_MODEL_SMALL": ("ai_model_small", str),
               "AI_EFFORT": ("ai_effort", str), "AI_TIMEOUT_S": ("ai_timeout_s", float), "AI_CLI_TIMEOUT_S": ("ai_cli_timeout_s", float),
               "AI_CLAUDE_CLI": ("ai_claude_cli", str), "AI_LEDGER_PATH": ("ai_ledger_path", str), "AI_LEDGER_SCOPE": ("ai_ledger_scope", str)}
DRY_LANE_SWITCHES_LABEL = "dry defaults (the DRAFT-DECLARATION.v2 arms); used in dry mode only, never in live mode"
_STAMP = re.compile(r"[A-Za-z0-9._-]{3,64}")


class Refused(RuntimeError):
    pass


def sha256(path) -> str:
    return I.sha256_file(path)


def _norm(p) -> str:
    return pathlib.Path(p).resolve().as_posix().lower()


# ---- bindings, trees, truth, run set ------------------------------------------------------------------------------------
def verify_binding(path, expected_sha) -> dict:
    got = sha256(path)
    if not expected_sha or got != expected_sha:
        raise Refused(f"refused: binding manifest {got} != {expected_sha}")
    man = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    bad = [p for files in (man.get("files") or {}).values() for p, want in files.items()
           if not pathlib.Path(p).exists() or sha256(p) != want]
    if bad:
        raise Refused(f"refused: {len(bad)} bound file(s) differ: {bad[:5]}")
    return {"binding_manifest": str(path), "sha256": got, "files_verified": sum(len(v) for v in (man.get("files") or {}).values())}


def heads() -> dict:
    out = {}
    for repo, want in HEADS.items():
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        if head != want or dirty:
            raise Refused(f"refused: {repo} HEAD {head} clean={not dirty}")
        out[repo] = head
    return out


def truth_text(truth) -> str:
    return json.dumps(truth, sort_keys=True, indent=1, ensure_ascii=False) + "\n"


def build_truth() -> dict:
    x = I.load_all()
    return A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])


def population(truth) -> dict:
    gate = S.population_gate(truth, 0)
    if gate["action"] != "DISPATCH_ELIGIBLE":
        raise Refused(f"stop: population gate {gate['action']} (no dispatch)")
    return gate


def load_run_set(path, truth) -> list:
    rs = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    run_set = [{"pool_id": d["pool_id"], "doc_key": d["doc_key"], "ep": d["ep"]} for d in rs["documents"]]
    if len(run_set) > 30 or any(d["pool_id"] not in truth["documents"] for d in run_set) or \
            any(truth["documents"][d["pool_id"]]["is_alias"] for d in run_set) or \
            any(truth["documents"][d["pool_id"]]["doc_key"] != d["doc_key"] for d in run_set):
        raise Refused("refused: the run set is not canonical, not keyed by the reference set, or holds more than 30 documents")
    return run_set


# ---- the live declaration -------------------------------------------------------------------------------------------------
def run_folder_of(stamp) -> pathlib.Path:
    if not stamp or not _STAMP.fullmatch(str(stamp)):
        raise Refused(f"refused: a stamp is 3-64 characters A-Z a-z 0-9 . _ - ({stamp!r})")
    return SANDBOX_BASE / str(stamp)


def validate_declaration(decl, declaration_path) -> dict:
    """The live declaration contract (module docstring). Returns the normalised values the runner and lanes use."""
    if not isinstance(decl, dict) or decl.get("dry_exercise"):
        raise Refused("refused: not a live ORCH-07 declaration")
    for k in ("binding_manifest_sha256", "run_set_sha256", "run", "authorization", "caps", "project_day_limit", "lane_switches", "provider_env", "ledger"):
        if k not in decl or decl[k] in (None, "", {}):
            raise Refused(f"refused: the declaration does not bind '{k}' (live mode has no default)")
    run = decl["run"]
    folder = run_folder_of(run.get("stamp"))
    if not run.get("folder") or _norm(run["folder"]) != _norm(folder):
        raise Refused(f"refused: the declaration's run folder must be {folder.as_posix()} (one run folder per declaration)")
    pinned = DG.pinned_path(declaration_path)
    if _norm((decl["authorization"] or {}).get("path") or "") != _norm(pinned):
        raise Refused(f"refused: the declaration must bind the pinned authorization path {pinned.as_posix()}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(decl["authorization"].get("owner_token_sha256") or "")):
        raise Refused("refused: the declaration binds no owner token digest")
    if decl["caps"] != PLAN_CAPS:
        raise Refused(f"refused: the declared caps {decl['caps']} are not the plan's {PLAN_CAPS}")
    lim = decl["project_day_limit"]
    if not isinstance(lim, int) or isinstance(lim, bool) or not 1 <= lim <= PLAN_PROJECT_DAY_LIMIT:
        raise Refused(f"refused: project_day_limit must be an integer 1..{PLAN_PROJECT_DAY_LIMIT} ({lim!r})")
    sw = decl["lane_switches"]
    if not isinstance(sw, dict) or set(sw) != set(LANES):
        raise Refused(f"refused: lane_switches must name exactly the lanes {LANES} ({sorted(sw) if isinstance(sw, dict) else sw!r})")
    for lane, d in sw.items():
        if not isinstance(d, dict) or any(not str(k).startswith("AI_EVIDENCE_") or not isinstance(v, str) for k, v in d.items()):
            raise Refused(f"refused: lane {lane} switches must map AI_EVIDENCE_* names to strings")
        if lane in ("B", "C", "R") and "AI_EVIDENCE_VARIANT" not in d:
            raise Refused(f"refused: lane {lane} must state AI_EVIDENCE_VARIANT explicitly")
    if sw["P"] != {}:
        raise Refused("refused: lane P re-sends captured payloads and takes no switches ({})")
    env = decl["provider_env"]
    if not isinstance(env, dict) or any(not isinstance(v, str) for v in env.values()):
        raise Refused("refused: provider_env must map names to strings")
    missing = [k for k in REQUIRED_PROVIDER_ENV if not env.get(k)]
    if missing:
        raise Refused(f"refused: provider_env does not bind {missing} (live mode has no default)")
    bad = [k for k in env if not k.startswith("AI_") or k.startswith("AI_EVIDENCE_") or k == "AI_ENABLED"]
    if bad:
        raise Refused(f"refused: provider_env may hold only AI_* provider settings, never {bad}")
    if env["AI_PROVIDER"].lower() not in KNOWN_PROVIDERS:
        raise Refused(f"refused: unknown AI_PROVIDER {env['AI_PROVIDER']!r}")
    led = decl["ledger"]
    if not isinstance(led, dict) or led.get("wrap_provider") is not True or not led.get("path") or not led.get("scope") or not isinstance(led.get("limits"), dict):
        raise Refused("refused: ledger must bind path, scope, limits and wrap_provider true (LedgerProvider writes to the declared scope)")
    try:
        env_limits = json.loads(env["AI_LEDGER_LIMITS"])
    except ValueError as exc:
        raise Refused(f"refused: AI_LEDGER_LIMITS is not JSON ({exc})") from exc
    if _norm(env["AI_LEDGER_PATH"]) != _norm(led["path"]) or env["AI_LEDGER_SCOPE"] != led["scope"] or env_limits != led["limits"]:
        raise Refused("refused: provider_env AI_LEDGER_PATH / AI_LEDGER_SCOPE / AI_LEDGER_LIMITS differ from the declared ledger")
    req = led["limits"].get("requests")
    if not isinstance(req, int) or isinstance(req, bool) or not 0 < req <= sum(PLAN_CAPS.values()):
        raise Refused(f"refused: the ledger limits must bind 'requests' between 1 and {sum(PLAN_CAPS.values())} (the caps)")
    return {"stamp": run["stamp"], "run_folder": folder.as_posix(), "caps": dict(decl["caps"]), "project_day_limit": lim,
            "lane_switches": sw, "provider_env": env, "ledger": led, "authorization_path": pinned.as_posix()}


def load_declaration(path, expected_sha, *, binding_sha, run_set_sha) -> tuple[dict, dict]:
    if not path or not expected_sha or not pathlib.Path(path).is_file() or sha256(path) != expected_sha:
        raise Refused("refused: live mode needs the ORCH-07 declaration and its exact sha256")
    decl = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if decl.get("binding_manifest_sha256") != binding_sha or decl.get("run_set_sha256") != run_set_sha:
        raise Refused("refused: the declaration does not bind this binding manifest and this run set")
    return decl, validate_declaration(decl, path)


# ---- the ledger (read-only) -----------------------------------------------------------------------------------------------
def _ro(path):
    p = pathlib.Path(path)
    if not p.is_file():
        raise Refused(f"refused: the ledger {p.as_posix()} does not exist (this harness never creates a ledger or a scope)")
    return sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)


def ledger_counts(path=I.AI_LEDGER) -> dict:
    con = _ro(path)
    try:
        return {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
                "scope_names_sha256": hashlib.sha256("|".join(r[0] for r in con.execute("select scope from scopes order by scope")).encode()).hexdigest()}
    finally:
        con.close()


def ledger_snapshot(path) -> dict:
    con = _ro(path)
    try:
        scopes = {}
        for scope, limits, breaker in con.execute("select scope, limits, breaker from scopes order by scope"):
            n, mx = con.execute("select count(*), coalesce(max(id), 0) from entries where scope = ?", (scope,)).fetchone()
            scopes[scope] = {"limits": json.loads(limits or "{}"), "breaker": breaker, "entries": n, "max_id": mx}
        return {"scopes": scopes, "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
                "entries": con.execute("select count(*) from entries").fetchone()[0]}
    finally:
        con.close()


def verify_ledger_scope(ledger: dict) -> dict:
    """Live, before dispatch: the declared scope exists with EXACTLY the declared limits and a closed breaker."""
    snap = ledger_snapshot(ledger["path"])
    s = snap["scopes"].get(ledger["scope"])
    if s is None:
        raise Refused(f"refused: the declared ledger scope {ledger['scope']!r} does not exist (it is created only under the owner's authorization, never by this harness)")
    if s["limits"] != ledger["limits"]:
        raise Refused(f"refused: the ledger scope {ledger['scope']!r} has limits {s['limits']}, the declaration binds {ledger['limits']}")
    if s["breaker"]:
        raise Refused(f"refused: the ledger scope {ledger['scope']!r} has an open breaker ({s['breaker']})")
    return {"scope": ledger["scope"], "limits": s["limits"], "entries": s["entries"], "breaker": None}


def ledger_live_check(before: dict, after: dict, ledger: dict, caps=PLAN_CAPS) -> dict:
    """Live, after the run: growth only inside the declared scope and within the caps."""
    problems = []
    if set(after["scopes"]) != set(before["scopes"]):
        problems.append(f"scopes changed: {sorted(set(after['scopes']) ^ set(before['scopes']))}")
    if after["limit_amendments"] != before["limit_amendments"]:
        problems.append("a limit amendment was recorded")
    for name, b in before["scopes"].items():
        a = after["scopes"].get(name)
        if a is None:
            continue
        if name != ledger["scope"] and (a["entries"] != b["entries"] or a["limits"] != b["limits"]):
            problems.append(f"scope {name!r} changed")
    grown = None
    if ledger["scope"] in before["scopes"] and ledger["scope"] in after["scopes"]:
        con = _ro(ledger["path"])
        try:
            grown = con.execute("select count(*) from entries where scope = ? and id > ? and coalesce(state, '') not in ('refused', 'cache_hit')",
                                (ledger["scope"], before["scopes"][ledger["scope"]]["max_id"])).fetchone()[0]
        finally:
            con.close()
        if grown > sum(caps.values()):
            problems.append(f"the declared scope grew by {grown} dispatch entries > {sum(caps.values())}")
        if after["scopes"][ledger["scope"]]["limits"] != ledger["limits"]:
            problems.append("the declared scope's limits changed")
    return {"ok": not problems, "problems": problems, "declared_scope_dispatch_entries_added": grown}


# ---- RC-5: the lane's switches and provider environment against the declaration ---------------------------------------
def verify_lane_environment(lane: str, switches: dict, provider_env: dict | None, environ, settings, *, mode: str) -> dict:
    """The lane's AI_EVIDENCE_* environment must equal its declared switches EXACTLY (nothing missing, nothing extra); in
    live mode every declared provider_env value must be in the environment AND in the application's settings."""
    if switches is None:
        raise Refused(f"refused: lane {lane} has no declared switches (no silent default)")
    have = {k: v for k, v in environ.items() if k.startswith("AI_EVIDENCE_")}
    if have != dict(switches):
        raise Refused(f"refused: lane {lane} switches differ from the declaration: environment {have}, declared {switches}")
    out = {"switches": have, "provider_env_verified": []}
    if mode != "live":
        return out
    if not provider_env:
        raise Refused(f"refused: lane {lane} has no declared provider environment (no silent default)")
    if str(environ.get("AI_ENABLED", "")).lower() != "true" or not getattr(settings, "ai_enabled", False):
        raise Refused(f"refused: lane {lane}: AI_ENABLED is not true")
    for k, v in provider_env.items():
        if environ.get(k) != v:
            raise Refused(f"refused: lane {lane}: {k} in the environment is {environ.get(k)!r}, the declaration binds {v!r}")
        if k in SETTINGS_OF:
            name, kind = SETTINGS_OF[k]
            if not hasattr(settings, name):
                raise Refused(f"refused: lane {lane}: the application has no setting {name} for {k}")
            got = getattr(settings, name)
            ok = (float(got) == float(v)) if kind is float else (_norm(got) == _norm(v) if k == "AI_LEDGER_PATH" else str(got) == v)
            if not ok:
                raise Refused(f"refused: lane {lane}: setting {name} is {got!r}, the declaration binds {v!r}")
        elif k == "AI_LEDGER_LIMITS":
            if json.loads(getattr(settings, "ai_ledger_limits", None) or "null") != json.loads(v):
                raise Refused(f"refused: lane {lane}: setting ai_ledger_limits differs from the declaration")
        out["provider_env_verified"].append(k)
    return out


# ---- the shared live preflight (runner and every live lane) -----------------------------------------------------------
def live_preflight(cfg: dict, *, lane: str | None = None) -> dict:
    """binding, declaration contract, run set, HEADs, truth and population gate, ledger scope, and (for a lane) the
    runner-written configuration against the declaration. Raises Refused. The guard is called by the caller."""
    for k in ("binding", "binding_sha256", "declaration_path", "declaration_sha256", "run_set_path"):
        if not cfg.get(k):
            raise Refused(f"refused: live mode needs '{k}' in the run configuration")
    if "auth_path" in cfg:
        raise Refused("refused: an authorization path cannot be configured; it is pinned beside the declaration (RC-3)")
    if cfg.get("dry_fault"):
        raise Refused("refused: fault injection is a dry-mode drill only")
    rep = {"binding": verify_binding(cfg["binding"], cfg["binding_sha256"])}
    rs_sha = sha256(cfg["run_set_path"])
    decl, v = load_declaration(cfg["declaration_path"], cfg["declaration_sha256"], binding_sha=rep["binding"]["sha256"], run_set_sha=rs_sha)
    rep["declaration"] = v
    rep["heads"] = heads()
    truth = build_truth()
    rep["truth_sha256"] = hashlib.sha256(truth_text(truth).encode("utf-8")).hexdigest()
    rep["population_gate"] = population(truth)
    run_set = load_run_set(cfg["run_set_path"], truth)
    rep["run_set"] = {"path": str(cfg["run_set_path"]), "sha256": rs_sha, "documents": len(run_set)}
    rep["ledger_scope"] = verify_ledger_scope(v["ledger"])
    if lane is not None:
        folder = pathlib.Path(v["run_folder"])
        want = {"mode": "live", "run_key": cfg["declaration_sha256"], "run_folder": folder.as_posix(), "stamp": v["stamp"],
                "store": (folder / "capture.sqlite").as_posix(), "allowance": (folder / "allowance.sqlite").as_posix(),
                "caps": v["caps"], "project_day_limit": v["project_day_limit"], "lane_switches": v["lane_switches"],
                "provider_env": v["provider_env"], "run_set": run_set}
        diff = []
        for k, w in want.items():
            got = cfg.get(k)
            if k in ("run_folder", "store", "allowance"):
                if not got or _norm(got) != _norm(w):
                    diff.append(k)
            elif got != w:
                diff.append(k)
        if diff:
            raise Refused(f"refused: lane {lane}: the run configuration differs from the declaration in {diff}")
        if not cfg.get("truth") or sha256(cfg["truth"]) != rep["truth_sha256"]:
            raise Refused(f"refused: lane {lane}: the truth file is not the adapter's truth of the frozen reference set")
        if not isinstance(cfg.get("invocation"), int) or cfg["invocation"] < 1:
            raise Refused(f"refused: lane {lane}: no invocation number")
    return {"report": rep, "declaration": decl, "values": v, "truth": truth, "run_set": run_set}
