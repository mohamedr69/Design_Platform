"""ORCH-08 (A-09 point 2; R38-10): pinned FULL model identities, the CLI version and the provider identity of every
invocation, and the per-response identity check.

The identifier strings (read-only evidence): the claude-code adapter (candidate app/ai/provider.py ClaudeCodeProvider)
passes the configured AI_MODEL_SMALL / AI_MODEL_STANDARD to `claude -p --model <id>` and records as the response's model
the first non-haiku key of the CLI's reported modelUsage (else the configured id: a timeout or transport failure echoes
it). The AI ledger's entries recorded by that adapter (mode=ro, 483 entries) carry 'claude-sonnet-5' (457) and
'claude-opus-5' (5, r2x-small-2026-09-29 escalations) for the aliases 'sonnet' / 'opus'; 'sonnet' (13) only on
timeouts, '' (8) only on ledger refusals. The full ids the adapter accepts (config.py: "a Claude Code alias ... or the
full id both work") and records are therefore:
    AI_MODEL_SMALL    = "claude-sonnet-5"      (small tier: every C / R read, B's form read)
    AI_MODEL_STANDARD = "claude-opus-5"        (standard tier: EV2 escalations only; not reached under EV1)
Aliases (sonnet, opus, haiku, fable, default, best, opusplan, ...) are refused in a declaration: they resolve through
whatever CLI is installed.

The declaration's model_identity block (validate_pins):
  {"provider": "claude-code", "models": {"small": "claude-sonnet-5", "standard": "claude-opus-5"},
   "cli": {"path": <AI_CLAUDE_CLI>, "version": <the exact `claude --version` line, or null = recorded and held equal
           across the run's invocations>}}
Runtime:
  * before any lane of an invocation the runner records `<cli> --version` and the provider identity in
    <run folder>/inv-<n>/PROVIDER-IDENTITY.json and appends <run folder>/CLI-VERSIONS.jsonl; a version different from
    the declared one, or (when the declaration records it) from the run's first invocation, refuses the invocation
    before any dispatch;
  * IdentityGuard wraps the dispatch path of every lane: every response that a provider returned is checked -- the
    returned model must equal the declared full id of the request's tier (or its explicit model) and the provider must
    be the declared adapter. A difference writes <run folder>/IDENTITY-INVALID.json once (O_EXCL; the offending request:
    lane, invocation, task, tier, document, page, expected and returned identity), the response is turned into the
    failure 'identity_mismatch' (its answer is never used), the run is INVALID and every later request is refused
    ('identity_invalid') -- in this invocation and in any resume (the marker is never removed; resume is refused).
  * every response's check is appended to <run folder>/inv-<n>/IDENTITY-LOG-<lane>.jsonl.
No provider is built here and no model is called; `claude --version` is the only process this module can start.

ORCH-10 (R42; contract 5, A-11): the CLI is pinned by ABSOLUTE PATH, by the file's sha256 and by the exact version line:
  model_identity.cli = {"path": <absolute path of the CLI file, equal to AI_CLAUDE_CLI>, "sha256": <64 hex>,
                        "version": <the exact `claude --version` line>}      (a bare name such as 'claude' is refused)
  * verify_cli_file(path, sha256) reads the file AS BYTES and refuses a missing file or another sha256 (no process);
  * check_version(run_folder, pins, version) is the pure comparison (declared line; the run's first recorded line) that
    the runner makes BEFORE it creates or re-opens anything (R41-09 / R41-11); record_invocation repeats it and writes
    the records afterwards (now with the file's sha256)."""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import re
import subprocess

PINNED = {"small": "claude-sonnet-5", "standard": "claude-opus-5"}
PROVIDER = "claude-code"
ALIASES = {"sonnet", "opus", "haiku", "fable", "default", "best", "opusplan", "sonnet[1m]", "opus[1m]", "claude", "latest"}
FULL_ID = re.compile(r"claude-(?:sonnet|opus|haiku|fable)-\d+(?:-\d+)*")
MARKER = "IDENTITY-INVALID.json"
CLI_LOG = "CLI-VERSIONS.jsonl"
NOT_DISPATCHED = ("budget", "dispatch_refused", "dry_refused", "identity_invalid", "allowance_refused", "stopped")
NO_REPLY = ("timeout", "transport")
SHA256 = re.compile(r"[0-9a-f]{64}")


class IdentityRefused(RuntimeError):
    pass


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def is_full_id(value) -> bool:
    return isinstance(value, str) and value not in ALIASES and bool(FULL_ID.fullmatch(value))


def validate_pins(model_identity: dict, provider_env: dict) -> dict:
    """The declaration's model_identity block against its provider_env (refuses aliases and any disagreement)."""
    if not isinstance(model_identity, dict):
        raise IdentityRefused("refused: the declaration binds no model_identity (full model ids are required)")
    models = model_identity.get("models") or {}
    for tier, key in (("small", "AI_MODEL_SMALL"), ("standard", "AI_MODEL_STANDARD")):
        v = models.get(tier)
        if not is_full_id(v):
            raise IdentityRefused(f"refused: model_identity.models.{tier} must be a full model id, not an alias ({v!r})")
        if provider_env.get(key) != v:
            raise IdentityRefused(f"refused: provider_env {key} {provider_env.get(key)!r} differs from model_identity.models.{tier} {v!r}")
    if model_identity.get("provider") != provider_env.get("AI_PROVIDER") or model_identity.get("provider") != PROVIDER:
        raise IdentityRefused(f"refused: model_identity.provider must be {PROVIDER!r} and equal AI_PROVIDER")
    cli = model_identity.get("cli") or {}
    if cli.get("path") != provider_env.get("AI_CLAUDE_CLI"):
        raise IdentityRefused("refused: model_identity.cli.path must equal AI_CLAUDE_CLI")
    # ORCH-10 (contract 5): the CLI is pinned by absolute path, file sha256 and exact version line
    path = cli.get("path")
    if not isinstance(path, str) or not re.fullmatch(r"[A-Za-z]:[\\/].+", path) or path.strip() != path:
        raise IdentityRefused(f"refused: model_identity.cli.path must be the ABSOLUTE path of the CLI file, not a name on PATH ({path!r})")
    if not isinstance(cli.get("sha256"), str) or not SHA256.fullmatch(cli["sha256"]):
        raise IdentityRefused("refused: model_identity.cli.sha256 must pin the CLI file (64 lower-case hex)")
    if not (isinstance(cli.get("version"), str) and cli["version"].strip() and cli["version"] == cli["version"].strip()):
        raise IdentityRefused("refused: model_identity.cli.version must be the exact version line (contract 5: never null)")
    return {"provider": PROVIDER, "small": models["small"], "standard": models["standard"], "cli_path": cli["path"],
            "cli_version": cli.get("version"), "cli_sha256": cli["sha256"]}


def verify_cli_file(path, sha256: str) -> dict:
    """ORCH-10: the pinned CLI file, READ AS BYTES (never executed): it must exist and hash to the pinned sha256."""
    p = pathlib.Path(str(path))
    if not p.is_file():
        raise IdentityRefused(f"refused: the pinned CLI file {p.as_posix()} does not exist")
    import hashlib

    h, n = hashlib.sha256(), 0
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    got = h.hexdigest()
    if got != sha256:
        raise IdentityRefused(f"refused: the CLI file {p.as_posix()} hashes to {got}, the declaration pins {sha256}")
    return {"cli_path": p.as_posix(), "cli_sha256": got, "cli_bytes": n, "executed": False}


def check_version(run_folder, pins: dict, version: str) -> dict:
    """ORCH-10 (R41-09 / R41-11): the pure version comparison -- the declared line, and the run's first recorded line when
    the run folder holds one. Writes nothing; the runner calls it before it creates or re-opens anything."""
    if pins.get("cli_version") is not None and version != pins["cli_version"]:
        raise IdentityRefused(f"refused: CLI version {version!r} differs from the declared {pins['cli_version']!r}")
    log = pathlib.Path(run_folder) / CLI_LOG if run_folder else None
    previous = []
    if log is not None and log.is_file():
        for x in log.read_text(encoding="utf-8").splitlines():
            try:
                previous.append(json.loads(x))
            except ValueError:
                continue                            # a line cut by an interruption (disk full) is no record
    if previous and previous[0]["cli_version"] != version:
        raise IdentityRefused(f"refused: CLI version {version!r} differs from this run's first invocation ({previous[0]['cli_version']!r}); "
                              "the CLI stays unchanged during a run")
    return {"cli_version": version, "first_recorded": previous[0]["cli_version"] if previous else None}


def cli_version(cli: str, *, run=subprocess.run, timeout: float = 60) -> str:
    """`<cli> --version` (not a model request): its first output line; refuses when it fails."""
    try:
        r = run([cli, "--version"], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IdentityRefused(f"refused: `{cli} --version` failed: {exc}") from exc
    line = (r.stdout or "").strip().splitlines()[0].strip() if (r.stdout or "").strip() else ""
    if r.returncode or not line:
        raise IdentityRefused(f"refused: `{cli} --version` returned {r.returncode} with no version line")
    return line


def record_invocation(run_folder, invocation: int, pins: dict, version: str, *, mode: str) -> dict:
    """PROVIDER-IDENTITY.json of the invocation and one CLI-VERSIONS.jsonl line; refuses a version that differs from the
    declared one or from the run's first recorded version."""
    run_folder = pathlib.Path(run_folder)
    log = run_folder / CLI_LOG
    check_version(run_folder, pins, version)
    rec = {"invocation": int(invocation), "at_utc": _now(), "mode": mode, "cli_path": pins.get("cli_path"), "cli_version": version,
           "cli_sha256": pins.get("cli_sha256"),
           "provider": pins["provider"], "declared_models": {"small": pins["small"], "standard": pins["standard"]}}
    inv = run_folder / f"inv-{invocation}"
    inv.mkdir(parents=True, exist_ok=True)
    (inv / "PROVIDER-IDENTITY.json").write_text(json.dumps(rec, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    with open(log, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def invalid_marker(run_folder) -> dict | None:
    p = pathlib.Path(run_folder) / MARKER
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


class IdentityGuard:
    """allowance -> IdentityGuard -> the dispatch path (live: GuardedProvider; dry: the refusing stub)."""
    name, ready, status = "identity-guard", True, "r38 per-response model identity check"

    def __init__(self, inner, response_cls, *, declared: dict, run_folder, invocation: int, lane: str, log_path, ctx_fn=dict,
                 provider_name_fn=None):
        self.inner, self.response_cls, self.declared = inner, response_cls, declared
        self.run_folder, self.invocation, self.lane = pathlib.Path(run_folder), int(invocation), lane
        self.log_path, self.ctx_fn, self.provider_name_fn = pathlib.Path(log_path), ctx_fn, provider_name_fn
        self.checked, self.mismatches, self.refused = 0, 0, 0

    def _log(self, rec):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")

    def complete(self, request):
        ctx = self.ctx_fn() or {}
        tier = getattr(request, "tier", None) or "small"
        expected = getattr(request, "model", None) or self.declared.get(tier)
        base = {"at_utc": _now(), "lane": self.lane, "invocation": self.invocation, "task": getattr(request, "task", None), "tier": tier,
                "document_sha256": ctx.get("sha256"), "page": ctx.get("page"), "expected_model": expected, "expected_provider": self.declared.get("provider")}
        marker = invalid_marker(self.run_folder)
        if marker is not None:
            self.refused += 1
            self._log(base | {"check": "refused_run_invalid"})
            return self.response_cls(data=None, model="identity", error="identity_invalid",
                                     error_detail=f"the run is INVALID (model identity mismatch at {marker.get('lane')} {marker.get('task')}); no request is sent")
        resp = self.inner.complete(request)
        err = getattr(resp, "error", None)
        returned = getattr(resp, "model", "") or ""
        provider = self.provider_name_fn() if self.provider_name_fn else self.declared.get("provider")
        if err in NOT_DISPATCHED:
            self._log(base | {"check": "not_dispatched", "error": err, "returned_model": returned})
            return resp
        self.checked += 1
        source = "echo_no_reply" if err in NO_REPLY else "returned"
        ok = returned == expected and provider == self.declared.get("provider")
        self._log(base | {"check": "ok" if ok else "mismatch", "error": err, "returned_model": returned, "returned_provider": provider,
                          "identity_source": source})
        if ok:
            return resp
        self.mismatches += 1
        offending = base | {"returned_model": returned, "returned_provider": provider, "error": err, "rule": "A-09 point 2: the run is INVALID"}
        p = self.run_folder / MARKER
        try:
            fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, (json.dumps(offending, sort_keys=True, indent=1, default=str) + "\n").encode("utf-8"))
            os.close(fd)
        except FileExistsError:
            pass                                    # the first offending request stays recorded
        extra = {"usage": resp.usage} if getattr(resp, "usage", None) is not None else {}
        return self.response_cls(data=None, model=returned, error="identity_mismatch",
                                 error_detail=f"returned {provider}/{returned!r}, declared {self.declared.get('provider')}/{expected!r}: the run is INVALID", **extra)
