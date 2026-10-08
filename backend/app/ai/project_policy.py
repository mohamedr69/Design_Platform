"""Whether a project's documents may be sent to an AI provider.

The platform-wide switch (AI_ENABLED) says whether a provider is configured;
this says whether a given client's documents may go to it. A project set to
"blocked" makes every AI feature on it unavailable -- reading a cell, checking
details against the DRF, reviewing or auto-filling a compliance clause --
with the reason shown, and the deterministic features carry on unchanged.

Two questions, answered differently on purpose (M3 contract B-04; ORCH-053):

- `allowed(project)` -- for read models and pages only: whether to show a
  project's AI features as available. A missing project (None) counts as
  allowed here, so a page about no project in particular shows nothing
  blocked. It never authorises a request.
- `require(project)` / `enforce(db, project_id, task=...)` -- before any
  request: FAIL CLOSED. A request is authorised only for a project that
  exists and whose `ai_policy` is exactly "allowed". A missing project, a
  project id with no row, a policy that is neither "allowed" nor "blocked"
  (ambiguous) and "blocked" are all refused with `AiPolicyRefused`, before
  anything is hashed, scanned, serialised or sent.

`enforce` re-reads the policy from the database on every call (and takes the
stricter of that and any copy the session holds), so a project blocked while
a job runs is refused at its next call, and a job over several projects is
checked per project per call. Every refusal leaves an audit row in
`ai_usage` -- the task, the project, `outcome` "policy_<reason>", model
"none", no tokens and no content -- which the daily call counts leave out.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

POLICIES = ("allowed", "blocked")
BLOCKED_MESSAGE = ("AI is switched off for this project (Project Info, AI use): its documents are not sent to an AI "
                   "provider. Everything else works as usual.")
# Why a request was refused, and what the engineer is told.
REASONS = ("missing", "unknown", "ambiguous", "blocked")
REFUSAL_MESSAGES = {
    "blocked": BLOCKED_MESSAGE,
    "missing": ("AI refused: the request names no project, and nothing is sent to an AI provider except for a "
                "project whose AI use is allowed."),
    "unknown": "AI refused: the project the request names is not on this platform. Nothing was sent to an AI provider.",
    "ambiguous": ("AI refused: this project's AI use is neither 'allowed' nor 'blocked' (Project Info, AI use). "
                  "Nothing is sent to an AI provider until it is set."),
}
# `ai_usage.outcome` of a refusal row; such rows are not calls (app.ai.budget.calls_today).
OUTCOME_PREFIX = "policy_"
REFUSED_MODEL = "none"


class AiBlocked(Exception):
    pass


class AiPolicyRefused(AiBlocked):
    """A request refused by the project AI policy before anything was sent."""

    def __init__(self, reason: str, *, project_id=None, task: str | None = None) -> None:
        self.reason = reason if reason in REASONS else "ambiguous"
        self.project_id = project_id
        self.task = task
        super().__init__(REFUSAL_MESSAGES[self.reason])


def allowed(project) -> bool:
    """For read models only (see the module docstring): None counts as allowed."""
    return project is None or getattr(project, "ai_policy", "allowed") != "blocked"


def _reason_for(policy) -> str | None:
    if policy == "allowed":
        return None
    if policy == "blocked":
        return "blocked"
    return "ambiguous"


def refusal(project) -> str | None:
    """Why a request for `project` (an object) is refused, or None when it may go. Fail closed."""
    if project is None:
        return "missing"
    return _reason_for(getattr(project, "ai_policy", None))


def require(project) -> None:
    """Raise `AiPolicyRefused` unless `project` exists and is "allowed" (no audit row; see `enforce`)."""
    reason = refusal(project)
    if reason is not None:
        raise AiPolicyRefused(reason, project_id=getattr(project, "id", None))


def _valid_id(project_id) -> bool:
    return isinstance(project_id, int) and not isinstance(project_id, bool) and project_id > 0


def refusal_for(db, project_id) -> str | None:
    """Why a request for the project with this id is refused, or None: the
    policy as the database holds it now and as this session holds it, the
    stricter of the two."""
    if project_id is None:
        return "missing"
    if not _valid_id(project_id):
        return "unknown"
    from sqlalchemy import select
    from sqlalchemy.orm.util import identity_key

    from app.models import Project

    row = db.execute(select(Project.ai_policy).where(Project.id == project_id)).first()
    if row is None:
        return "unknown"
    reason = _reason_for(row[0])
    if reason is None:
        held = db.identity_map.get(identity_key(Project, project_id))
        if held is not None:
            try:
                reason = _reason_for(held.__dict__.get("ai_policy", row[0]))
            except Exception:  # noqa: BLE001 -- the database's answer stands
                reason = None
    return reason


def audit(db, project_id, task: str | None, reason: str) -> None:
    """The refusal's audit row: the task, the project, the reason; no content,
    no tokens. Committed at once (as every usage row is, app.compliance.assist._log);
    a failure to write it is logged, never a reason to send."""
    from app.models import AiUsage

    known = reason not in ("missing", "unknown") and _valid_id(project_id)
    model = REFUSED_MODEL if known or project_id is None else f"{REFUSED_MODEL}; project_id={project_id}"
    try:
        db.add(AiUsage(project_id=project_id if known else None, run_id=None, task=(task or "unknown")[:32],
                       model=str(model)[:64], input_tokens=None, output_tokens=None, cached_input_tokens=None,
                       reasoning_tokens=None, estimated_cost=0, latency_ms=0, cache_hit=False, escalated=False,
                       outcome=f"{OUTCOME_PREFIX}{reason}"[:24]))
        db.commit()
    except Exception:  # noqa: BLE001 -- the refusal stands whatever happens to its record
        log.exception("The AI policy refusal could not be recorded (task %s, project %s, %s)", task, project_id, reason)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
    log.warning("AI request refused by the project AI policy: task=%s project_id=%s reason=%s", task, project_id, reason)


def enforce(db, project_id, *, task: str | None) -> None:
    """The gate before any AI request: re-read the project's policy, and when
    it does not allow the request, record the refusal and raise
    `AiPolicyRefused`. Returns None when the request may go."""
    reason = refusal_for(db, project_id)
    if reason is None:
        return
    audit(db, project_id, task, reason)
    raise AiPolicyRefused(reason, project_id=project_id, task=task)


def check(db, project_id, *, task: str | None) -> str | None:
    """`enforce` for a loop that stops rather than raises: the refusal's
    message (recorded like any refusal), or None when the request may go."""
    try:
        enforce(db, project_id, task=task)
    except AiPolicyRefused as exc:
        return str(exc)
    return None
