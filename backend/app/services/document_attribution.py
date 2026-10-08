"""Document attribution: whose document this is (M6, ORCH-043).

A classification says what a file appears to contain (its type, at a
stage of evidence). Attribution says whose it is, relative to this
project's scope: a separate field on the same classification row, never a
fifth stage string, with its own version and its own evidence.

  OUR_SCOPE         ours, on evidence that names us: the project's own DRF or
                    Design Sheet (the intake association), or a stored
                    title-block originator that is this company
  LIKELY_OUR_SCOPE  a shop drawing (by the rules' type, hinted or supported)
                    outside any folder of drawings given to us, on a project
                    whose DRF does not say we do not draw: the proxy the
                    Drawings Log already uses (document_control.is_shop_drawing),
                    not proof
  RELATED_EXTERNAL  another party's document that bears on a system of ours:
                    a drawing given to us (IFC / tender / enquiry folder) with
                    system evidence, another originator with system evidence,
                    or a shop drawing on a project whose DRF says another party
                    draws
  REFERENCE_ONLY    another party's document with no evidence of a system of
                    ours, or of a system / discipline this project does not have
  UNKNOWN           nothing to go on, or evidence that disagrees (kept in
                    `conflict`, never resolved by a guess). UNKNOWN is neither
                    in nor out of scope (M3 P-07): `in_scope` answers None.

The rules are deterministic, weigh only what is already stored (the path,
the classification's type, stage and system, the project's systems and
`drawings_in_scope`, a title block's originator / discipline when a reader
stored one -- none does yet, see `title_block_facts`) and are ordered:
intake association, originator, discipline, folder, type. Claims on the
same side (ours / not ours) resolve to the first; claims on opposite sides
resolve to UNKNOWN with the conflict kept, except that the intake
association is authoritative (the conflict is still kept).

Nothing here changes a role, a state, a register, `drawings_in_scope`,
`is_shop_drawing` or a confirmed row: attribution is an observation. It
never fails the classification: `attribute_safely` answers UNKNOWN with
the error in the basis.
"""

from __future__ import annotations

import enum
import logging
import re
from dataclasses import dataclass, field

from app.core.config import get_settings

log = logging.getLogger(__name__)

#   attribution-2026-10-08.1  the first rules: intake, originator, discipline, folder, type
ATTRIBUTION_VERSION = "attribution-2026-10-08.1"


class Attribution(str, enum.Enum):
    OUR_SCOPE = "OUR_SCOPE"
    LIKELY_OUR_SCOPE = "LIKELY_OUR_SCOPE"
    RELATED_EXTERNAL = "RELATED_EXTERNAL"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"


OURS = frozenset({Attribution.OUR_SCOPE, Attribution.LIKELY_OUR_SCOPE})
EXTERNAL = frozenset({Attribution.RELATED_EXTERNAL, Attribution.REFERENCE_ONLY})


def in_scope(state: str | Attribution | None) -> bool | None:
    """True only for OUR_SCOPE, False only for RELATED_EXTERNAL and
    REFERENCE_ONLY; None (not established) for LIKELY_OUR_SCOPE, UNKNOWN or
    anything else -- an unknown is never in or out of scope (P-07)."""
    value = getattr(state, "value", state)
    if value == Attribution.OUR_SCOPE.value:
        return True
    if value in (Attribution.RELATED_EXTERNAL.value, Attribution.REFERENCE_ONLY.value):
        return False
    return None


def scope_reading(state: str | Attribution | None) -> str:
    """The attribution as a reader of the inspector sees it: "in_scope",
    "likely_in_scope", "out_of_scope" or "unknown"."""
    value = getattr(state, "value", state)
    if value == Attribution.LIKELY_OUR_SCOPE.value:
        return "likely_in_scope"
    answer = in_scope(value)
    return "unknown" if answer is None else ("in_scope" if answer else "out_of_scope")


# Whole folder names, as document_control.GIVEN_TO_US reads them: a drawing we were given.
GIVEN_TO_US = ("enquiry", "enquiries", "tender", "ifc", "issued for construction")
# Disciplines that are this company's systems (a title block's discipline, normalised).
OUR_DISCIPLINES = frozenset({"fa", "fas", "fire alarm", "fire alarm system", "elv", "els", "eml", "emergency lighting",
                             "cbs", "central battery", "pava", "pa va", "public address", "voice evacuation", "ves",
                             "life safety", "frc", "fire rated cable"})
# Legal suffixes and connectives an originator literal carries or drops.
_NOISE = frozenset({"llc", "l", "c", "ltd", "co", "the", "for", "and", "m", "s"})


def _norm(text: str | None) -> str:
    words = re.sub(r"[^a-z0-9]+", " ", (text or "").casefold()).split()
    return " ".join(w for w in words if w not in _NOISE)


def own_originators() -> tuple[str, ...]:
    """This company's names, normalised: `company_name` and the
    semicolon-separated `attribution_own_originators`."""
    settings = get_settings()
    names = [settings.company_name] + [n for n in (settings.attribution_own_originators or "").split(";")]
    return tuple(dict.fromkeys(n for n in (_norm(name) for name in names) if n))


def is_own_originator(originator: str | None, aliases: tuple[str, ...] | None = None) -> bool:
    text = f" {_norm(originator)} "
    return any(f" {alias} " in text for alias in (aliases if aliases is not None else own_originators()))


@dataclass(frozen=True)
class ProjectFacts:
    """What the project says that attribution may weigh. Empty systems and
    None for drawings_in_scope mean not known."""

    ep_number: str | None = None
    system_codes: tuple[str, ...] = ()
    drawings_in_scope: bool | None = None


def project_facts(project) -> ProjectFacts:
    """The project's systems and `drawings_in_scope`, as system_rules
    answers them; unknown (empty / None) when they cannot be read."""
    if project is None:
        return ProjectFacts()
    from app.services import system_rules

    try:
        codes = tuple(system_rules.project_codes(project))
    except Exception:  # noqa: BLE001 -- an unreadable project is an unknown, never an error here
        codes = ()
    try:
        drawn = bool(system_rules.drawings_in_scope(project)) if list(getattr(project, "systems", None) or []) else None
    except Exception:  # noqa: BLE001
        drawn = None
    return ProjectFacts(getattr(project, "ep_number", None), codes, drawn)


def title_block_facts(row) -> dict:
    """The originator and the discipline a reader stored for the row's title
    block (`extracted["observations"]`, kind "title_block", keys
    "originator" / "discipline"). The title-block reader of today
    (title_block.TITLE_BLOCK_VERSION "titleblock-2") stores neither: this
    is the slot the rules read when one does."""
    found: dict = {"originator": None, "discipline": None, "page": None}
    for observation in ((getattr(row, "extracted", None) or {}).get("observations") or []):
        if not isinstance(observation, dict) or observation.get("kind") != "title_block":
            continue
        for key in ("originator", "discipline"):
            value = observation.get(key)
            if isinstance(value, str) and value.strip() and found[key] is None:
                found[key] = value.strip()[:120]
                found["page"] = found["page"] or observation.get("page")
    return found


def _folders(row) -> list[str]:
    path = str(getattr(row, "relative_path", None) or getattr(row, "filename", None) or "").replace("\\", "/")
    return [part.strip().casefold() for part in path.split("/")[:-1] if part.strip()]


@dataclass
class Result:
    state: Attribution
    basis: dict
    conflict: dict | None = None
    version: str = ATTRIBUTION_VERSION
    claims: list[dict] = field(default_factory=list)


def _claim(claims: list[dict], state: Attribution, rule: str, why: str) -> None:
    claims.append({"state": state.value, "rule": rule, "why": why})


def attribute(row, assessment, facts: ProjectFacts | None = None, *, aliases: tuple[str, ...] | None = None) -> Result:
    """The attribution of a row, from its classification (`assessment`: the
    Assessment the rules or a later stage produced) and the project facts.
    Pure: reads no file, writes nothing, asks no model."""
    from app.services.document_classification import Basis, DocumentType, Stage

    facts = facts or ProjectFacts()
    primary = getattr(assessment.primary_type, "value", assessment.primary_type)
    stage = getattr(assessment.stage, "value", assessment.stage)
    system = assessment.system_code
    folders = _folders(row)
    given = next((f for f in folders if any(word in f for word in GIVEN_TO_US)), None)
    block = title_block_facts(row)
    discipline = _norm(block["discipline"]) if block["discipline"] else None
    discipline_ours = None if discipline is None else discipline in OUR_DISCIPLINES
    # Whether the evidence ties the document to a system of ours: the classification's system (the
    # rules name only this company's systems) that the project has, or a discipline that is ours.
    if system and facts.system_codes:
        related = system in facts.system_codes
    elif system:
        related = True
    else:
        related = bool(discipline_ours)
    if discipline_ours is False:
        related = False
    external = Attribution.RELATED_EXTERNAL if related else Attribution.REFERENCE_ONLY
    basis: dict = {
        "type": primary, "stage": stage,
        "originator": None, "title_block": None, "folder": None,
        "system": {"code": system, "project_systems": list(facts.system_codes), "related": related,
                   "discipline": block["discipline"], "discipline_ours": discipline_ours},
        "drawings_in_scope": facts.drawings_in_scope,
        "rule": None, "claims": [],
    }
    claims: list[dict] = []

    # 1. The intake association: the project's own DRF or Design Sheet.
    if getattr(assessment.basis, "value", assessment.basis) == Basis.INTAKE_ASSOCIATION.value:
        _claim(claims, Attribution.OUR_SCOPE, "intake", "the project's own DRF or Design Sheet (intake association)")
    # 2. A title block's originator, when a reader stored one.
    if block["originator"]:
        own = is_own_originator(block["originator"], aliases)
        basis["originator"] = {"value": block["originator"], "own": own, "page": block["page"]}
        if own:
            _claim(claims, Attribution.OUR_SCOPE, "originator", "the title block names this company as originator")
        else:
            _claim(claims, external, "originator", "the title block names another originator"
                   + (" for a system of ours" if related else "; nothing ties it to a system of ours"))
    if block["discipline"]:
        basis["title_block"] = {"discipline": block["discipline"], "ours": discipline_ours, "page": block["page"]}
    # 3. A title block's discipline that is not ours (alone, it never says ours).
    if discipline_ours is False and not block["originator"]:
        _claim(claims, Attribution.REFERENCE_ONLY, "discipline",
               f"the title block's discipline ({block['discipline']}) is not a system of ours")
    # 4. A folder of drawings given to us.
    if given is not None:
        basis["folder"] = {"given_to_us": True, "folder": given}
        _claim(claims, external, "folder", f"filed under “{given}”: a document given to us, not ours"
               + ("" if related else "; nothing ties it to a system of ours"))
    else:
        basis["folder"] = {"given_to_us": False}
    # 5. The type: a shop drawing (hinted or supported) outside the folders above.
    if given is None and stage in (Stage.HINT.value, Stage.SUPPORTED.value):
        if primary == DocumentType.SHOP_DRAWING.value:
            if facts.drawings_in_scope is False:
                _claim(claims, Attribution.RELATED_EXTERNAL, "type",
                       "a shop drawing on a project whose DRF says another party draws (drawings_in_scope false)")
            else:
                _claim(claims, Attribution.LIKELY_OUR_SCOPE, "type",
                       f"a shop drawing ({stage}) outside the folders of drawings given to us: likely ours, not proof")
        elif primary == DocumentType.IFC_DRAWING.value:
            _claim(claims, external, "type", "an issued-for-construction drawing: given to us")

    basis["claims"] = claims
    states = [Attribution(c["state"]) for c in claims]
    if not states:
        basis["rule"] = "no_evidence"
        return Result(Attribution.UNKNOWN, basis, None, claims=claims)
    sides = {("ours" if s in OURS else "external") for s in states}
    conflict = None
    if len(sides) > 1:
        conflict = {"claims": claims, "reason": "the evidence disagrees about whose document this is; kept for a person"}
    if claims[0]["rule"] == "intake":
        basis["rule"] = "intake"
        return Result(Attribution.OUR_SCOPE, basis, conflict, claims=claims)
    if conflict is not None:
        basis["rule"] = "conflict"
        return Result(Attribution.UNKNOWN, basis, conflict, claims=claims)
    basis["rule"] = claims[0]["rule"]
    return Result(states[0], basis, None, claims=claims)


def attribute_safely(row, assessment, project=None, *, facts: ProjectFacts | None = None) -> Result:
    """`attribute`, never raising: a failure is logged and answered UNKNOWN
    with the error in the basis, so the classification is still written."""
    try:
        return attribute(row, assessment, facts if facts is not None else project_facts(project))
    except Exception as exc:  # noqa: BLE001 -- attribution never fails the classification
        log.warning("Attribution failed for document %s: %s", getattr(row, "id", None), exc)
        return Result(Attribution.UNKNOWN, {"rule": "error", "error": f"{type(exc).__name__}: {exc}"[:300], "claims": []})
