"""ORCH-05C / ORCH-08: the ONE preflight of a live run, executed by runner_r32 before it consumes the owner's
authorization AND again by every live lane_r32 process. Also: the live declaration contract (version 3), the
ledger-scope check and the live ledger difference check.

Live declaration contract 3 (ORCH-09 writes the declaration; this task writes none). Every key is REQUIRED; a missing or
different value refuses the run before any folder exists (no silent default in live mode):
  contract                                   "r38-live-contract-3"
  binding_manifest_sha256, run_set_sha256    the binding manifest and the run-set file this run uses
  run.stamp, run.sandbox_base, run.folder    one run folder per declaration: run.folder == run.sandbox_base/<stamp>; the
                                             sandbox base is DECLARED (C:/t/r2x/r<NN>-sandbox), no longer a code constant
  authorization.path, .owner_token_sha256    the pinned authorization path (beside the declaration) and the token digest
  budget.parent {total 556, input_tokens, output_tokens, elapsed_s}
                                             the ONE immutable parent experiment budget (A-09 point 3)
  budget.lane_allowances {B 240, C 240, R 40, P 36}
                                             separately auditable lane allowances; no borrowing; sum == parent.total
  project_window {limit 1..60, window_s 86400}
                                             the harness per-project ROLLING-window limit, all lanes: it GOVERNS
  project_request_bounds {path, sha256}      PROJECT-REQUEST-BOUNDS.json (project_bounds_r32); the live preflight
                                             recomputes it from the run set, the truth and the bound code and refuses a
                                             difference
  lane_switches {"B": {...}, "C": {...}, "R": {...}, "P": {}}
  provider_env                               the ten provider keys of contract 2 plus AI_MAX_CALLS_PER_PROJECT_PER_DAY,
                                             AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY, AI_MAX_CALLS_PER_DOCUMENT,
                                             AI_MAX_ELAPSED_S_PER_JOB; COMPATIBLE LIMITS: the application's per-project
                                             limits must be >= the bounds' required minimum, so the application can
                                             never refuse before the harness window (refused otherwise)
  model_identity                             full model ids, no aliases (model_identity_r38.validate_pins), equal to
                                             AI_MODEL_SMALL / AI_MODEL_STANDARD; the provider and the CLI path
  ledger {path, scope, limits, wrap_provider: true}
                                             the single scope is the backstop: limits.requests == parent.total and the
                                             token / elapsed limits equal the parent's
Live ledger behaviour (RC-4, carried): read-only checks; the declared scope must ALREADY exist with exactly the declared
limits and a closed breaker (this harness never creates a scope); after the run the ledger may have grown only inside
the declared scope by at most parent.total dispatch entries.
Sandbox base: DEFAULT_SANDBOX_BASE (C:/t/r2x/r38-sandbox) for dry runs and tests, overridable by --sandbox-base or the
environment variable R38_SANDBOX_BASE (dry only); live mode uses only the declaration's run.sandbox_base."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import sqlite3
import subprocess

import dispatch_guard_r32 as DG
import inputs_r32 as I
import labels_adapter_r32 as A
import model_identity_r38 as MI
import project_bounds_r32 as PB
import score_bcr_r32 as S

CONTRACT = "r38-live-contract-3"
DEFAULT_SANDBOX_BASE = pathlib.Path("C:/t/r2x/r38-sandbox")
SANDBOX_BASE_ENV = "R38_SANDBOX_BASE"
_SANDBOX_BASE_RE = re.compile(r"C:/t/r2x/r\d{2}-sandbox")
HEADS = {"C:/t/iso/frozen-r12": I.BASELINE_HEAD, "C:/t/iso/cand-r29": I.CANDIDATE_HEAD}
PLAN_CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
PLAN_PARENT_TOTAL = 556
PLAN_WINDOW_LIMIT_MAX = 60
PLAN_WINDOW_S = 86400
LANES = ("B", "C", "R", "P")
REQUIRED_PROVIDER_ENV = ("AI_PROVIDER", "AI_MODEL_STANDARD", "AI_MODEL_SMALL", "AI_EFFORT", "AI_TIMEOUT_S", "AI_CLI_TIMEOUT_S",
                         "AI_CLAUDE_CLI", "AI_LEDGER_PATH", "AI_LEDGER_SCOPE", "AI_LEDGER_LIMITS", "AI_MAX_CALLS_PER_PROJECT_PER_DAY",
                         "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY", "AI_MAX_CALLS_PER_DOCUMENT", "AI_MAX_ELAPSED_S_PER_JOB")
KNOWN_PROVIDERS = ("claude-code", "claude_code", "subscription", "claude", "anthropic", "openai", "gpt")
# provider_env key -> (application setting, comparison)
SETTINGS_OF = {"AI_PROVIDER": ("ai_provider", str), "AI_MODEL_STANDARD": ("ai_model_standard", str), "AI_MODEL_SMALL": ("ai_model_small", str),
               "AI_EFFORT": ("ai_effort", str), "AI_TIMEOUT_S": ("ai_timeout_s", float), "AI_CLI_TIMEOUT_S": ("ai_cli_timeout_s", float),
               "AI_CLAUDE_CLI": ("ai_claude_cli", str), "AI_LEDGER_PATH": ("ai_ledger_path", str), "AI_LEDGER_SCOPE": ("ai_ledger_scope", str),
               "AI_MAX_CALLS_PER_PROJECT_PER_DAY": ("ai_max_calls_per_project_per_day", int),
               "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": ("ai_read_max_calls_per_project_per_day", int),
               "AI_MAX_CALLS_PER_DOCUMENT": ("ai_max_calls_per_document", int), "AI_MAX_ELAPSED_S_PER_JOB": ("ai_max_elapsed_s_per_job", float)}
DRY_LANE_SWITCHES_LABEL = "dry defaults (the DRAFT-DECLARATION.v2 arms); used in dry mode only, never in live mode"
_STAMP = re.compile(r"[A-Za-z0-9._-]{3,64}")


class Refused(RuntimeError):
    pass


def sha256(path) -> str:
    return I.sha256_file(path)


def _norm(p) -> str:
    return pathlib.Path(p).resolve().as_posix().lower()


def sandbox_base(value=None) -> pathlib.Path:
    """The sandbox base: the given value (a declaration's run.sandbox_base, or --sandbox-base), else R38_SANDBOX_BASE, else
    the default C:/t/r2x/r38-sandbox. It must be C:/t/r2x/r<NN>-sandbox (two digits)."""
    raw = value if value else os.environ.get(SANDBOX_BASE_ENV) or DEFAULT_SANDBOX_BASE.as_posix()
    s = str(raw).replace("\\", "/").rstrip("/")
    if not _SANDBOX_BASE_RE.fullmatch(s):
        raise Refused(f"refused: a sandbox base is C:/t/r2x/r<NN>-sandbox ({raw!r})")
    return pathlib.Path(s)


SANDBOX_BASE = sandbox_base()


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
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    for repo, want in HEADS.items():
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
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
def run_folder_of(stamp, base=None) -> pathlib.Path:
    if not stamp or not _STAMP.fullmatch(str(stamp)):
        raise Refused(f"refused: a stamp is 3-64 characters A-Z a-z 0-9 . _ - ({stamp!r})")
    return sandbox_base(base) / str(stamp)


def _posint(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def load_bounds(ref) -> dict:
    if not isinstance(ref, dict) or not ref.get("path") or not re.fullmatch(r"[0-9a-f]{64}", str(ref.get("sha256") or "")):
        raise Refused("refused: the declaration must bind project_request_bounds {path, sha256}")
    p = pathlib.Path(ref["path"])
    if not p.is_file() or sha256(p) != ref["sha256"]:
        raise Refused("refused: PROJECT-REQUEST-BOUNDS.json is missing or does not hash to the declared sha256")
    return json.loads(p.read_text(encoding="utf-8"))


def validate_declaration(decl, declaration_path) -> dict:
    """The live declaration contract 3 (module docstring). Returns the normalised values the runner and lanes use."""
    if not isinstance(decl, dict) or decl.get("dry_exercise"):
        raise Refused("refused: not a live declaration")
    for k in ("contract", "binding_manifest_sha256", "run_set_sha256", "run", "authorization", "budget", "project_window", "project_request_bounds",
              "lane_switches", "provider_env", "model_identity", "ledger"):
        if k not in decl or decl[k] in (None, "", {}):
            raise Refused(f"refused: the declaration does not bind '{k}' (live mode has no default)")
    if decl["contract"] != CONTRACT:
        raise Refused(f"refused: the declaration is not contract {CONTRACT} ({decl['contract']!r})")
    run = decl["run"]
    try:
        base = sandbox_base(run.get("sandbox_base") or "-")
    except Refused as exc:
        raise Refused(f"refused: run.sandbox_base must be declared as C:/t/r2x/r<NN>-sandbox ({run.get('sandbox_base')!r})") from exc
    folder = run_folder_of(run.get("stamp"), base)
    if not run.get("folder") or _norm(run["folder"]) != _norm(folder):
        raise Refused(f"refused: the declaration's run folder must be {folder.as_posix()} (one run folder per declaration)")
    pinned = DG.pinned_path(declaration_path)
    if _norm((decl["authorization"] or {}).get("path") or "") != _norm(pinned):
        raise Refused(f"refused: the declaration must bind the pinned authorization path {pinned.as_posix()}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(decl["authorization"].get("owner_token_sha256") or "")):
        raise Refused("refused: the declaration binds no owner token digest")
    budget = decl["budget"]
    caps, parent = (budget or {}).get("lane_allowances"), (budget or {}).get("parent")
    if caps != PLAN_CAPS:
        raise Refused(f"refused: the declared lane allowances {caps} are not the plan's {PLAN_CAPS}")
    if not isinstance(parent, dict) or set(parent) != {"total", "input_tokens", "output_tokens", "elapsed_s"} or not all(_posint(v) for v in parent.values()):
        raise Refused("refused: budget.parent must bind exactly {total, input_tokens, output_tokens, elapsed_s} as positive integers")
    if parent["total"] != PLAN_PARENT_TOTAL or sum(caps.values()) != parent["total"]:
        raise Refused(f"refused: the parent total must be {PLAN_PARENT_TOTAL} = the sum of the lane allowances")
    win = decl["project_window"]
    if not isinstance(win, dict) or set(win) != {"limit", "window_s"} or not _posint(win.get("limit")) or not win["limit"] <= PLAN_WINDOW_LIMIT_MAX \
            or win.get("window_s") != PLAN_WINDOW_S:
        raise Refused(f"refused: project_window must be {{limit 1..{PLAN_WINDOW_LIMIT_MAX}, window_s {PLAN_WINDOW_S}}} ({win!r})")
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
    try:
        pins = MI.validate_pins(decl["model_identity"], env)
    except MI.IdentityRefused as exc:
        raise Refused(str(exc)) from exc
    bounds = load_bounds(decl["project_request_bounds"])
    if bounds.get("project_window") and (bounds["project_window"].get("limit"), bounds["project_window"].get("window_s")) != (win["limit"], win["window_s"]):
        raise Refused("refused: PROJECT-REQUEST-BOUNDS was computed for another project window")
    if bounds.get("elapsed_bound_s") != parent["elapsed_s"]:
        raise Refused("refused: PROJECT-REQUEST-BOUNDS was computed for another elapsed bound")
    probs = PB.check_compatible(env, bounds)
    if probs:
        raise Refused("refused: incompatible limits -- the application could refuse before the harness: " + "; ".join(probs))
    led = decl["ledger"]
    if not isinstance(led, dict) or led.get("wrap_provider") is not True or not led.get("path") or not led.get("scope") or not isinstance(led.get("limits"), dict):
        raise Refused("refused: ledger must bind path, scope, limits and wrap_provider true (LedgerProvider writes to the declared scope)")
    try:
        env_limits = json.loads(env["AI_LEDGER_LIMITS"])
    except ValueError as exc:
        raise Refused(f"refused: AI_LEDGER_LIMITS is not JSON ({exc})") from exc
    if _norm(env["AI_LEDGER_PATH"]) != _norm(led["path"]) or env["AI_LEDGER_SCOPE"] != led["scope"] or env_limits != led["limits"]:
        raise Refused("refused: provider_env AI_LEDGER_PATH / AI_LEDGER_SCOPE / AI_LEDGER_LIMITS differ from the declared ledger")
    lim = led["limits"]
    if lim.get("requests") != parent["total"] or lim.get("input_tokens") != parent["input_tokens"] or lim.get("output_tokens") != parent["output_tokens"] \
            or lim.get("elapsed_s") != parent["elapsed_s"]:
        raise Refused("refused: the single ledger scope is the backstop of the parent budget: its requests / input_tokens / output_tokens / "
                      "elapsed_s limits must equal the parent's")
    return {"contract": CONTRACT, "stamp": run["stamp"], "sandbox_base": base.as_posix(), "run_folder": folder.as_posix(), "caps": dict(caps),
            "parent": dict(parent), "project_window": dict(win), "lane_switches": sw, "provider_env": env, "ledger": led,
            "authorization_path": pinned.as_posix(), "model_identity": pins, "bounds": bounds,
            "bounds_ref": dict(decl["project_request_bounds"])}


def load_declaration(path, expected_sha, *, binding_sha, run_set_sha) -> tuple[dict, dict]:
    if not path or not expected_sha or not pathlib.Path(path).is_file() or sha256(path) != expected_sha:
        raise Refused("refused: live mode needs the declaration and its exact sha256")
    decl = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if decl.get("binding_manifest_sha256") != binding_sha or decl.get("run_set_sha256") != run_set_sha:
        raise Refused("refused: the declaration does not bind this binding manifest and this run set")
    return decl, validate_declaration(decl, path)


def verify_bounds(v: dict, run_set: list, truth: dict) -> dict:
    """The bound PROJECT-REQUEST-BOUNDS.json must equal its recomputation from this run set, truth and code."""
    again = PB.compute(run_set, truth, v["lane_switches"], window_limit=v["project_window"]["limit"], window_s=v["project_window"]["window_s"],
                       elapsed_s=v["parent"]["elapsed_s"], caps=v["caps"])
    keys = ("projects", "lanes", "compatible_limits", "per_document", "per_page_maximum", "version")
    diff = [k for k in keys if again.get(k) != v["bounds"].get(k)]
    if diff:
        raise Refused(f"refused: PROJECT-REQUEST-BOUNDS.json differs from its recomputation in {diff}")
    return {"verified": True, "required_minimum": again["compatible_limits"]["required_minimum"]}


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


def ledger_live_check(before: dict, after: dict, ledger: dict, total=PLAN_PARENT_TOTAL) -> dict:
    """Live, after the run: growth only inside the declared scope and within the parent total."""
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
        if grown > total:
            problems.append(f"the declared scope grew by {grown} dispatch entries > {total}")
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
            ok = (float(got) == float(v)) if kind is float else (int(got) == int(v)) if kind is int else \
                (_norm(got) == _norm(v) if k == "AI_LEDGER_PATH" else str(got) == v)
            if not ok:
                raise Refused(f"refused: lane {lane}: setting {name} is {got!r}, the declaration binds {v!r}")
        elif k == "AI_LEDGER_LIMITS":
            if json.loads(getattr(settings, "ai_ledger_limits", None) or "null") != json.loads(v):
                raise Refused(f"refused: lane {lane}: setting ai_ledger_limits differs from the declaration")
        out["provider_env_verified"].append(k)
    return out


# ---- the shared live preflight (runner and every live lane) -----------------------------------------------------------
def live_preflight(cfg: dict, *, lane: str | None = None) -> dict:
    """binding, declaration contract, run set, HEADs, truth and population gate, the request bounds, ledger scope, and (for
    a lane) the runner-written configuration against the declaration. Raises Refused. The guard is called by the caller."""
    for k in ("binding", "binding_sha256", "declaration_path", "declaration_sha256", "run_set_path"):
        if not cfg.get(k):
            raise Refused(f"refused: live mode needs '{k}' in the run configuration")
    if "auth_path" in cfg:
        raise Refused("refused: an authorization path cannot be configured; it is pinned beside the declaration (RC-3)")
    if cfg.get("dry_fault") or cfg.get("dry_inject") or cfg.get("dry_ledger") or cfg.get("dry_application_limits"):
        raise Refused("refused: fault injection is a dry-mode drill only")
    rep = {"binding": verify_binding(cfg["binding"], cfg["binding_sha256"])}
    rs_sha = sha256(cfg["run_set_path"])
    decl, v = load_declaration(cfg["declaration_path"], cfg["declaration_sha256"], binding_sha=rep["binding"]["sha256"], run_set_sha=rs_sha)
    rep["declaration"] = {k: v[k] for k in v if k != "bounds"}
    rep["heads"] = heads()
    truth = build_truth()
    rep["truth_sha256"] = hashlib.sha256(truth_text(truth).encode("utf-8")).hexdigest()
    rep["population_gate"] = population(truth)
    run_set = load_run_set(cfg["run_set_path"], truth)
    rep["run_set"] = {"path": str(cfg["run_set_path"]), "sha256": rs_sha, "documents": len(run_set)}
    rep["request_bounds"] = verify_bounds(v, run_set, truth)
    rep["ledger_scope"] = verify_ledger_scope(v["ledger"])
    if lane is not None:
        folder = pathlib.Path(v["run_folder"])
        want = {"mode": "live", "run_key": cfg["declaration_sha256"], "run_folder": folder.as_posix(), "stamp": v["stamp"],
                "store": (folder / "capture.sqlite").as_posix(), "allowance": (folder / "allowance.sqlite").as_posix(),
                "caps": v["caps"], "parent": v["parent"], "project_window": v["project_window"], "lane_switches": v["lane_switches"],
                "provider_env": v["provider_env"], "model_identity": v["model_identity"], "run_set": run_set}
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
