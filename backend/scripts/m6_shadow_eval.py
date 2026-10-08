"""M6 offline shadow evaluation of document classification and attribution
(ORCH-043). Reads a *copy* of a platform database, read-only, and scores
one arm against the M2 golden labels; writes nothing anywhere but the
report it is told to write.

    python scripts/m6_shadow_eval.py --database C:/clones/ep_platform.db --arm rules --out report.json
    python scripts/m6_shadow_eval.py --database ... --arm stored
    python scripts/m6_shadow_eval.py --database ... --arm ai --scripted-answers answers.json

Arms
  rules   the rules of this checkout (document_classification.assess and
          document_attribution.attribute) re-run on each joined row's stored
          reading -- no file opened, nothing written
  stored  the current classification rows the clone already holds
  ai      the rules, with every weak answer (hint / unknown / ambiguous) put to
          a *scripted* provider (app.ai.provider.RecordingProvider, answers
          from a file or handed in by a test). No real model is ever called:
          any other provider is refused. It validates the harness and the
          AI-arm accounting, not a model. Review-only (A-15 item 1): a model
          answer is read exactly as the live pass reads it
          (document_classification_ai._assessment) -- at most a hint
          (moderate when the model is sure), never supported.

Per source. Every report has `by_source`: the metrics of the answers each
source gave -- rules / ai for the rules and ai arms; stored / ai / engineer
for the stored arm (the clone's `source` column: hint, assessment and
backfill rows are "stored"). The stored arm reads a stored model answer as
review-only too: an "ai" row stored as supported (written before A-15) is
counted as a hint, and how many were is reported (`stored.ai_supported_capped`).

Join. A label is joined to `project_documents` by (project EP number,
sha256), the row whose relative path matches the label's path when the
same content is filed twice. Removed rows are not joined.

Truth.
  type        the label's `kind` through the reviewed table
              app/services/classification_kind_map.json; an unmapped kind is
              left out of the type metrics, and counted
  system      the label's `system` through the same file's `systems` table
              (FAS / PAVA / ELS / FRC / NONE); multi-system and unknown
              labels are left out, and counted
  attribution DERIVED AND PROVISIONAL (`derive_attribution`): from the
              labelled originator literal and system. Ours when a party named
              in the originator -- outside a stamp and outside a recipient
              ("... to M/s X") -- is this company (Al Arabia for Safety &
              Security / Al Arabia SSD / Juma Al Majid; never Al Arabia
              Electro Mechanical, a different company); otherwise
              RELATED_EXTERNAL when the labelled system is one of ours, and
              REFERENCE_ONLY when it is labelled as another discipline; no
              truth when the originator is unknown or the system is not
              labelled. Nobody has labelled attribution: these numbers are a
              harness check until an engineer does.

Metrics (per cohort -- regression / exploration / holdout -- and all, each
with its numerator and denominator): per-type precision and recall, type
accuracy, system accuracy, attribution accuracy (exact, on answered rows,
and by side: ours / not ours), false-supported rate (stage supported, type
wrong) and false-OUR_SCOPE rate (attribution OUR_SCOPE, truth not
OUR_SCOPE; and with LIKELY_OUR_SCOPE counted as ours). UNKNOWN attribution
is never counted as in or out of scope.

Never: the live database (the clone is opened read-only, and the path the
platform's settings point at is refused), a provider other than the scripted
one, the network, a write to the clone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
REPO = BACKEND.parent

DEFAULT_LABELS = REPO / "docs" / "milestones" / "M2" / "real-project-pilot" / "GOLDEN-LABELS.json"
DEFAULT_KIND_MAP = BACKEND / "app" / "services" / "classification_kind_map.json"
COHORTS = ("regression", "exploration", "holdout")
HARNESS_VERSION = "m6-shadow-eval-2026-10-08.2"   # .2: AI arm review-only (A-15 item 1), per-source breakdown
TRUTH_VERSION = "attribution-truth-provisional-2026-10-08.1"
AI_PROMPT_VERSION = "m6-shadow-scripted-2026-10-08.1"
WEAK_STAGES = ("hint", "unknown", "ambiguous")
NON_VALUES = ("absent", "illegible", "unknown", "n/a", "unlabelled", "")

# This company, as an originator literal names it (truth derivation only; the rules use settings).
_OWN = re.compile(r"al\s*-?\s*arabia(?!\s*(?:electro|emw|e\.m\.w))|juma(?:a)?\s+al\s+majid", re.I)
_STAMP = re.compile(r"[^;()]*\bstamp\b[^;()]*", re.I)
_RECIPIENT = re.compile(r"\s(?:to|via)\s.*$", re.I)


class LiveDatabaseRefused(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_kind_map(path: Path = DEFAULT_KIND_MAP) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    from app.services.document_classification import DocumentType

    valid = {t.value for t in DocumentType}
    for kind, entry in data["kinds"].items():
        if entry["type"] is not None and entry["type"] not in valid:
            raise ValueError(f"kind map: {kind!r} maps to {entry['type']!r}, not a DocumentType")
    return data


def kind_map_coverage(kind_map: dict, documents: list[dict] | None = None) -> dict:
    kinds = kind_map["kinds"]
    out = {"kinds": len(kinds), "mapped_kinds": sum(1 for v in kinds.values() if v["type"]),
           "unmapped_kinds": sum(1 for v in kinds.values() if not v["type"]), "unmapped": list(kind_map["unmapped"])}
    if documents is not None:
        out["documents"] = len(documents)
        out["mapped_documents"] = sum(1 for d in documents if (kinds.get(d["labels"].get("kind")) or {}).get("type"))
    return out


def derive_attribution(originator: str | None, system_truth: str | None) -> tuple[str | None, str]:
    """The provisional attribution truth for one label (see the module
    docstring): (state or None, why)."""
    text = (originator or "").strip()
    if text.casefold().split(" (")[0].strip() in NON_VALUES or text.casefold().startswith("unknown"):
        return None, "originator not labelled"
    for segment in text.split(";"):
        segment = _STAMP.sub("", segment)
        segment = _RECIPIENT.sub("", f" {segment}")
        if _OWN.search(segment):
            return "OUR_SCOPE", "the originator names this company"
    if system_truth is None:
        return None, "another originator; the system is not labelled"
    if system_truth == "NONE":
        return "REFERENCE_ONLY", "another originator; labelled as another discipline"
    return "RELATED_EXTERNAL", "another originator; a system of ours"


# --- the clone ---------------------------------------------------------------------------------------


def _sqlite_path(url: str) -> Path | None:
    if not url.startswith("sqlite"):
        return None
    raw = url.split(":///", 1)[-1].split("?", 1)[0]
    if raw.startswith("file:"):
        raw = raw[5:]
    if not raw or raw == ":memory:":
        return None
    path = Path(raw)
    return (BACKEND / path).resolve() if not path.is_absolute() else path.resolve()


def open_clone(database: str | Path, *, live_url: str | None = None):
    """A read-only engine on the clone. Refuses the database the platform's
    settings point at, and anything that is not an existing SQLite file."""
    from sqlalchemy import create_engine

    path = Path(database).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"no database clone at {path}")
    if live_url is None:
        from app.core.config import get_settings

        live_url = get_settings().database_url
    live = _sqlite_path(live_url)
    if live is not None and live == path:
        raise LiveDatabaseRefused(f"{path} is the platform's own database ({live_url}); copy it and point at the copy")
    return create_engine(f"sqlite:///file:{path.as_posix()}?mode=ro&uri=true", connect_args={"uri": True})


def _json(value):
    if value is None or isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _columns(conn, table: str) -> set[str]:
    from sqlalchemy import text

    return {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}


def read_clone(engine) -> dict:
    """Projects, rows (as row-like objects) and current classification rows, by raw SQL."""
    from sqlalchemy import text

    with engine.connect() as conn:
        projects = {r.id: r.ep_number for r in conn.execute(text("SELECT id, ep_number FROM projects"))}
        rows = []
        for r in conn.execute(text("SELECT id, project_id, role, system_code, relative_path, filename, sha256, state, extracted "
                                   "FROM project_documents WHERE state != 'removed'")):
            rows.append(SimpleNamespace(id=r.id, project_id=r.project_id, role=r.role, system_code=r.system_code,
                                        relative_path=r.relative_path, filename=r.filename, sha256=r.sha256, state=r.state,
                                        extracted=_json(r.extracted)))
        stored = {}
        if "document_classifications" in {t[0] for t in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}:
            cols = _columns(conn, "document_classifications")
            wanted = [c for c in ("document_id", "primary_type", "stage", "system_code", "attribution", "source") if c in cols]
            for r in conn.execute(text(f"SELECT {', '.join(wanted)} FROM document_classifications WHERE superseded_at IS NULL")):
                values = dict(zip(wanted, r))
                stored[values["document_id"]] = {"type": values.get("primary_type"), "stage": values.get("stage"),
                                                  "system": values.get("system_code"),
                                                  "attribution": values.get("attribution") or "UNKNOWN",
                                                  "source": values.get("source")}
    return {"projects": projects, "rows": rows, "stored": stored}


def project_facts_of(engine, project_id: int, ep_number: str | None):
    """The project's facts through the ORM on the read-only clone; unknown when its schema differs."""
    from sqlalchemy.orm import Session

    from app.models import Project
    from app.services import document_attribution

    try:
        with Session(engine) as session:
            project = session.get(Project, project_id)
            return document_attribution.project_facts(project) if project is not None else document_attribution.ProjectFacts(ep_number)
    except Exception:  # noqa: BLE001 -- an older clone's schema: the facts are unknown, said so in the report
        return document_attribution.ProjectFacts(ep_number)


def _norm_path(value: str | None) -> str:
    return (value or "").replace("\\", "/").strip().casefold()


def join(labels: list[dict], clone: dict) -> dict[int, object]:
    """Label index -> clone row, by (EP number, sha256)."""
    by_key: dict[tuple, list] = {}
    for row in clone["rows"]:
        by_key.setdefault((str(clone["projects"].get(row.project_id)), (row.sha256 or "").lower()), []).append(row)
    out = {}
    for i, label in enumerate(labels):
        candidates = by_key.get((str(label.get("ep")), (label.get("sha256") or "").lower()), [])
        if not candidates:
            continue
        wanted = _norm_path(label.get("doc", "")).split("/", 1)[-1]
        match = next((r for r in candidates if _norm_path(r.relative_path) == wanted), None)
        out[i] = match or sorted(candidates, key=lambda r: r.id)[0]
    return out


# --- the arms ----------------------------------------------------------------------------------------


def rules_answer(row, facts) -> dict:
    from app.services import document_attribution
    from app.services import document_classification as dc

    intake_role = row.role if row.role in ("drf", "design_sheet") else None
    intake_system = row.system_code if intake_role else None
    assessment = dc.assess(row, intake_role=intake_role, intake_system=intake_system, project_ep=facts.ep_number)
    attributed = document_attribution.attribute(row, assessment, facts)
    return {"type": assessment.primary_type.value, "stage": assessment.stage.value, "system": assessment.system_code,
            "attribution": attributed.state.value, "source": "rules", "_assessment": assessment}


AI_SCHEMA = {"type": "object", "properties": {"primary_type": {"type": "string"}, "system_code": {"type": ["string", "null"]},
                                              "confidence": {"type": "string", "enum": ["high", "medium", "low"]}},
             "required": ["primary_type", "confidence"]}


def review_only_assessment(row, base, verdict: dict):
    """A model answer read the way the live pass reads it
    (document_classification_ai._assessment, A-15 item 1): review-only -- a
    hint at most (moderate when the model is sure), unknown for UNKNOWN or a
    low OTHER, never supported. `base`: the rules' Assessment of the row."""
    from app.services import document_classification as dc
    from app.services import document_classification_ai as live

    entry = SimpleNamespace(primary_type=base.primary_type.value, stage=base.stage.value, evidence=list(base.evidence),
                            evidence_sources=list(base.evidence_sources), system_code=base.system_code,
                            discipline=base.discipline, assessment={"flags": list(base.flags)})
    assessment = live._assessment(SimpleNamespace(row=row, entry=entry), verdict)
    if assessment.stage is dc.Stage.SUPPORTED:   # never by the live rule; the harness does not depend on it
        assessment.stage = dc.Stage.HINT
    return assessment


def ai_answer(row, facts, rules: dict, provider, counts: dict) -> dict:
    """The rules' answer, or for a weak one the scripted provider's, read as
    the live pass reads it (`review_only_assessment`: never supported). The
    attribution is the rules' attribution of the answered type."""
    from app.ai.provider import AiRequest, RecordingProvider, TextPart
    from app.services import document_attribution
    from app.services import document_classification as dc

    if not isinstance(provider, RecordingProvider):
        raise RuntimeError("the ai arm runs only with a scripted RecordingProvider; no real provider is called here")
    base = rules["_assessment"]
    if rules["stage"] not in WEAK_STAGES or base.basis is dc.Basis.INTAKE_ASSOCIATION:
        counts["not_asked"] += 1
        return {**rules, "source": "rules"}
    request = AiRequest(task="m6_shadow_classify", system="Classify the document (offline harness; scripted answers only).",
                        parts=[TextPart("document", json.dumps({"path": row.relative_path or row.filename,
                                                    "rules_guess": f"{rules['type']} ({rules['stage']})"}))],
                        schema=AI_SCHEMA, max_output_tokens=200)
    response = provider.complete(request)
    counts["asked"] += 1
    data = response.data if response.ok else None
    try:
        kind = dc.DocumentType(str((data or {}).get("primary_type")))
        confidence = (data or {}).get("confidence")
        if confidence not in ("high", "medium", "low"):
            raise ValueError(confidence)
    except ValueError:
        counts["failed"] += 1
        return {**rules, "source": "rules (model answer unusable)"}
    assessment = review_only_assessment(row, base, {**(data or {}), "primary_type": kind.value, "confidence": confidence})
    attributed = document_attribution.attribute(row, assessment, facts)
    counts["answered"] += 1
    counts["stages"][assessment.stage.value] = counts["stages"].get(assessment.stage.value, 0) + 1
    return {"type": assessment.primary_type.value, "stage": assessment.stage.value, "system": assessment.system_code,
            "attribution": attributed.state.value, "source": "ai", "needs_review": True, "model": response.model,
            "prompt_version": AI_PROMPT_VERSION, "page_chars": 0}


# --- the metrics -------------------------------------------------------------------------------------


def _rate(num: int, den: int) -> dict:
    return {"numerator": num, "denominator": den, "value": round(num / den, 4) if den else None}


def _side(state: str | None) -> str:
    if state in ("OUR_SCOPE", "LIKELY_OUR_SCOPE"):
        return "ours"
    if state in ("RELATED_EXTERNAL", "REFERENCE_ONLY"):
        return "external"
    return "unknown"


def source_group(arm: str, pred: dict | None) -> str | None:
    """Which source an answer counts under in `by_source`."""
    if pred is None:
        return None
    source = pred.get("source")
    if arm == "stored":
        return source if source in ("ai", "engineer") else "stored"
    return "ai" if source == "ai" else "rules"


def metrics(items: list[dict]) -> dict:
    """`items`: {truth_type, truth_system, truth_attribution, pred (dict or None), joined}."""
    joined = [i for i in items if i["joined"]]
    answered = [i for i in joined if i["pred"] is not None]
    typed = [i for i in answered if i["truth_type"]]
    types = sorted({i["truth_type"] for i in typed} | {i["pred"]["type"] for i in typed})
    per_type = {}
    for t in types:
        tp = sum(1 for i in typed if i["pred"]["type"] == t and i["truth_type"] == t)
        predicted = sum(1 for i in typed if i["pred"]["type"] == t)
        actual = sum(1 for i in typed if i["truth_type"] == t)
        per_type[t] = {"true_positive": tp, "precision": _rate(tp, predicted), "recall": _rate(tp, actual)}
    systems = [i for i in answered if i["truth_system"]]
    attributed = [i for i in answered if i["truth_attribution"]]
    attributed_answered = [i for i in attributed if i["pred"]["attribution"] != "UNKNOWN"]
    supported = [i for i in typed if i["pred"]["stage"] == "supported"]
    ours = [i for i in attributed if i["pred"]["attribution"] == "OUR_SCOPE"]
    ours_or_likely = [i for i in attributed if i["pred"]["attribution"] in ("OUR_SCOPE", "LIKELY_OUR_SCOPE")]
    confusion: dict = {}
    for i in attributed:
        row = confusion.setdefault(i["truth_attribution"], {})
        row[i["pred"]["attribution"]] = row.get(i["pred"]["attribution"], 0) + 1
    return {
        "labelled": len(items), "joined": len(joined), "answered": len(answered),
        "type_truth": len(typed), "type_unmapped": sum(1 for i in answered if not i["truth_type"]),
        "type_accuracy": _rate(sum(1 for i in typed if i["pred"]["type"] == i["truth_type"]), len(typed)),
        "per_type": per_type,
        "system_accuracy": _rate(sum(1 for i in systems if (i["pred"]["system"] or "NONE") == i["truth_system"]), len(systems)),
        "system_excluded": len(answered) - len(systems),
        "attribution_accuracy": _rate(sum(1 for i in attributed if i["pred"]["attribution"] == i["truth_attribution"]), len(attributed)),
        "attribution_accuracy_answered": _rate(sum(1 for i in attributed_answered
                                                   if i["pred"]["attribution"] == i["truth_attribution"]), len(attributed_answered)),
        "attribution_side_accuracy": _rate(sum(1 for i in attributed if _side(i["pred"]["attribution"]) == _side(i["truth_attribution"])),
                                           len(attributed)),
        "attribution_unknown": _rate(len(attributed) - len(attributed_answered), len(attributed)),
        "attribution_confusion": confusion,
        "false_supported_rate": _rate(sum(1 for i in supported if i["pred"]["type"] != i["truth_type"]), len(supported)),
        "false_our_scope_rate": _rate(sum(1 for i in ours if i["truth_attribution"] != "OUR_SCOPE"), len(ours)),
        "false_our_scope_rate_incl_likely": _rate(sum(1 for i in ours_or_likely if i["truth_attribution"] != "OUR_SCOPE"),
                                                  len(ours_or_likely)),
    }


def evaluate(engine, labels_doc: dict, kind_map: dict, *, arm: str = "rules", provider=None) -> dict:
    labels = labels_doc["documents"]
    clone = read_clone(engine)
    joined = join(labels, clone)
    facts_cache: dict = {}
    counts = {"asked": 0, "answered": 0, "failed": 0, "not_asked": 0, "stages": {}}
    stored_counts = {"ai_supported_capped": 0, "sources": {}}
    items = []
    for i, label in enumerate(labels):
        kind = label["labels"].get("kind")
        truth_type = (kind_map["kinds"].get(kind) or {}).get("type")
        truth_system = (kind_map["systems"].get(label["labels"].get("system")) or {}).get("code")
        truth_attribution, _why = derive_attribution(label["labels"].get("originator"), truth_system)
        row = joined.get(i)
        pred = None
        if row is not None:
            if arm == "stored":
                pred = clone["stored"].get(row.id)
                if pred is not None:
                    stored_counts["sources"][str(pred.get("source"))] = stored_counts["sources"].get(str(pred.get("source")), 0) + 1
                if pred is not None and pred.get("source") == "ai" and pred.get("stage") == "supported":
                    pred = {**pred, "stage": "hint"}   # A-15 item 1: a model answer alone is never supported
                    stored_counts["ai_supported_capped"] += 1
            else:
                if row.project_id not in facts_cache:
                    facts_cache[row.project_id] = project_facts_of(engine, row.project_id, clone["projects"].get(row.project_id))
                facts = facts_cache[row.project_id]
                pred = rules_answer(row, facts)
                if arm == "ai":
                    pred = ai_answer(row, facts, pred, provider, counts)
                pred = {k: v for k, v in pred.items() if not k.startswith("_")}
        items.append({"cohort": label.get("cohort"), "truth_type": truth_type, "truth_system": truth_system,
                      "truth_attribution": truth_attribution, "pred": pred, "joined": row is not None,
                      "source": source_group(arm, pred)})
    report = {
        "harness_version": HARNESS_VERSION, "truth_version": TRUTH_VERSION, "arm": arm,
        "labels": {"documents": len(labels), "at_utc": labels_doc.get("at_utc"), "labeller": labels_doc.get("labeller")},
        "kind_map": kind_map_coverage(kind_map, labels),
        "cohorts": {c: metrics([it for it in items if it["cohort"] == c]) for c in COHORTS},
        "all": metrics(items),
        "by_source": {s: metrics([it for it in items if it["source"] == s])
                      for s in sorted({it["source"] for it in items if it["source"] is not None})},
        "provisional": [
            "attribution truth is derived from the labelled originator and system (derive_attribution), not labelled",
            "the labels are a model's, from renders; the owner has not countersigned them",
            "type truth covers mapped kinds only; system truth single-system labels only",
        ],
    }
    if arm == "ai":
        report["ai"] = {**counts, "review_only": True, "prompt_version": AI_PROMPT_VERSION,
                        "provider": getattr(provider, "name", None)}
    if arm == "stored":
        report["stored"] = stored_counts
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--database", required=True, help="a COPY of a platform database (SQLite); opened read-only")
    parser.add_argument("--arm", choices=("rules", "stored", "ai"), default="rules")
    parser.add_argument("--labels", default=str(DEFAULT_LABELS))
    parser.add_argument("--kind-map", default=str(DEFAULT_KIND_MAP))
    parser.add_argument("--scripted-answers", help="ai arm: a JSON list of scripted answers for the RecordingProvider")
    parser.add_argument("--out", help="where to write the JSON report (default: print it)")
    args = parser.parse_args(argv)
    provider = None
    if args.arm == "ai":
        if not args.scripted_answers:
            parser.error("--arm ai needs --scripted-answers: no real model is called by this harness")
        from app.ai.provider import RecordingProvider

        provider = RecordingProvider(json.loads(Path(args.scripted_answers).read_text(encoding="utf-8")))
    engine = open_clone(args.database)
    labels_path = Path(args.labels)
    report = evaluate(engine, json.loads(labels_path.read_text(encoding="utf-8")), load_kind_map(Path(args.kind_map)),
                      arm=args.arm, provider=provider)
    report["labels"]["sha256"] = _sha256_file(labels_path)
    text = json.dumps(report, indent=1, default=str)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
