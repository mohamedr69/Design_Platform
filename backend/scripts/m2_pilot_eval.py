"""M2 real-project pilot evaluator, v2 (M2 review 05, R5-02 / R5-03).

Replaces the submitted scorer (`real-project-pilot/outputs/scripts/score.py`, kept unchanged as historical evidence).
What changed, and why:

* Truth categories are distinct. `unknown`, `illegible`, `ambiguous`, `unlabelled` are unscorable. `absent` (the page
  prints no such field) and `n/a` (no consultant decision applies) are NEGATIVE CONTROLS that can fail: an invented
  reference on a page labelled `absent`, or an accepted decision on a page labelled `n/a`, is a false positive.
* Decisions have separate denominators: accepted-positive precision (every non-UR decision the reader accepted, on
  scorable truth), negative-control specificity (truth UR / n/a), readable-field recovery (truth a positive decision
  of high/medium label confidence), abstention, held-evidence recovery (the right decision kept as a candidate but not
  accepted -- evidence, never an accepted approval), and conflict evidence (truth `conflict` needs the
  `decision_conflict` flag or two disagreeing candidates; a bare UR is not credited).
* Records are matched, not first-record fields. Expected records (page, component, reference, printed revision,
  decision) are matched to emitted records on the same page by identity; reference, revision and decision are judged
  on the same matched pair. Every emitted record is scored: matched, substituted (wrong identity), extra (a page whose
  truth is "no record"), duplicate (the same identity again), or unvalidated (a page with no truth). Missing expected
  register records are counted.
* Word transmittals are scored like any other document.
* Raw extraction is separated from projection: `printed_revision` (or a revision whose `revision_source` is printed /
  cover / suffix) is the raw revision; a folder/default revision is the legacy projection, reported apart, and a raw
  revision the reader did not extract is an abstention, not a misread. A decision held back by the default profile's
  gate with the right candidate is evidence recovery, not a misread.
* System uses a documented field-equivalence table (`SYSTEM_EQUIVALENCE`), not substring matching. Production
  effective-system rules are untouched.

Usage: python -m scripts.m2_pilot_eval --labels GOLDEN-LABELS.json --page-labels page_labels.json
       --rows rows-default.json [--rows-name default] --out report.json"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

# .3: a reference the reader itself marks incomplete or uncertain is held (evidence, not an accepted value); a
# sheet labelled as contradicting itself (REV cell vs revision history) is scored on whether the reader said so.
EVALUATOR_VERSION = "m2-pilot-eval-2026-09-28.3"
UNCERTAIN_REFERENCE_FLAGS = ("reference_incomplete", "reference_uncertain")
UNSCORABLE = ("unknown", "illegible", "ambiguous", "unlabelled")
NEGATIVE = ("absent", "n/a")
POSITIVE_DECISIONS = ("approved", "ANN", "rejected")
DECISION_WORDS = {"approved": "approved", "ann": "ANN", "approved as noted": "ANN", "rejected": "rejected", "ur": "UR",
                  "conflict": "conflict", "n/a": "n/a", "none": "n/a", "ambiguous": "ambiguous", "unknown": "unknown",
                  "illegible": "illegible", "unlabelled": "unlabelled", "absent": "absent"}
RAW_REVISION_SOURCES = ("printed", "cover", "suffix")

# Evaluation-only field equivalence: a label names systems in words; the reader emits a platform code (or a raw
# discipline). Each label token maps to the codes that count as the same field value. "other" (a discipline the
# platform does not track) expects no tracked code.
SYSTEM_EQUIVALENCE = {
    "FAS": {"FAS"}, "FIRE ALARM": {"FAS"}, "VES": {"FAS", "VES"}, "VOICE EVACUATION": {"FAS", "VES"},
    "FIRE TELEPHONE": {"FAS"}, "LIFE SAFETY": {"FAS"}, "FLAME": {"FAS"}, "ASD": {"FAS", "ASD"},
    "ELS": {"ELS"}, "EMERGENCY LIGHT": {"ELS"}, "CBS": {"ELS", "CBS"}, "CENTRAL BATTERY": {"ELS", "CBS"},
    "PA/VA": {"PAVA"}, "PAVA": {"PAVA"}, "PUBLIC ADDRESS": {"PAVA"}, "FRC": {"FRC"}, "CABLE": {"FRC", "FAS"},
}
TRACKED = {"FAS", "VES", "ELS", "CBS", "PAVA", "FRC", "ASD"}


# --- normalisation -----------------------------------------------------------------------------------------------


def literal(value) -> str | None:
    """A label's literal value: the text before a parenthetical note; a leading non-value word wins."""
    if value is None:
        return None
    text = str(value).strip()
    low = text.lower()
    for word in UNSCORABLE + NEGATIVE:
        if low == word or re.match(re.escape(word) + r"[\s(;:,]", low):
            return word
    return re.split(r"\s\(", text, 1)[0].strip()


def norm_ref(value: str | None) -> str:
    return re.sub(r"\s+", "", value or "").upper()


def alnum(value: str | None) -> str:
    return re.sub(r"[^0-9A-Z]", "", (value or "").upper())


def norm_rev(value: str | None) -> str | None:
    """A revision token as printed, compared: numbers by value (00 == R0 == Rev.0), letters and mixed as written."""
    if value is None:
        return None
    text = literal(value)
    if text is None or text in UNSCORABLE + NEGATIVE:
        return text
    token = re.split(r"[\s;]", text.strip().upper(), 1)[0]
    number = re.fullmatch(r"(?:R|REV\.?|REVISION|R\.)?0*(\d+)", token)
    return f"R{int(number.group(1))}" if number else token


def split_suffix(reference: str) -> tuple[str, str | None]:
    """'X-R3' -> ('X', 'R3'); the reader files a trailing revision suffix as the revision."""
    found = re.search(r"-\s*R\.?\s*0*(\d+)\s*$", reference or "", re.I)
    return ((reference[:found.start()], f"R{int(found.group(1))}") if found else (reference, None))


def same_identity(expected: str, actual: str | None) -> str:
    """'exact' | 'suffix' (the expected reference's revision suffix is filed as the revision) | 'near' | 'different'."""
    if not actual:
        return "different"
    if norm_ref(expected) == norm_ref(actual):
        return "exact"
    base, _ = split_suffix(expected)
    if norm_ref(base) == norm_ref(actual):
        return "suffix"
    if alnum(expected) == alnum(actual):
        return "near"
    return "different"


def expected_systems(label) -> set[str] | None:
    """The platform codes a system label accepts; set() for an untracked discipline; None when unscorable."""
    text = literal(label)
    if text is None or text in UNSCORABLE:
        return None
    upper = str(label).upper()
    if upper.startswith("OTHER"):
        return set()
    codes: set[str] = set()
    for token, accepted in SYSTEM_EQUIVALENCE.items():
        if re.search(r"(?<![A-Z])" + re.escape(token) + r"(?![A-Z])", upper):
            codes |= accepted
    return codes or None


def floor_key(text: str | None) -> str | None:
    """A floor's comparable key: L<n>, B<n>, P<n>, GF, RF, MEZ, or the upper-case words (raw names kept)."""
    if not text:
        return None
    t = str(text).upper()
    words = {"FIRST": 1, "SECOND": 2, "THIRD": 3, "FOURTH": 4, "FIFTH": 5, "1ST": 1, "2ND": 2, "3RD": 3}
    if re.search(r"\bGROUND\b|\bGF\b|\bGFL\b", t):
        return "GF"
    if re.search(r"\bROOF\b", t):
        return "RF"
    found = re.search(r"\bBASEMENT[\s-]*0*(\d+)|\bB0*(\d+)\b", t)
    if found:
        return f"B{int(found.group(1) or found.group(2))}"
    found = re.search(r"\bPODIUM[\s-]*0*(\d+)|\bP0*(\d+)\b", t)
    if found:
        return f"P{int(found.group(1) or found.group(2))}"
    found = re.search(r"\bL(?:EVEL)?[\s-]*0*(\d+)\b|\b0*(\d+)(?:ST|ND|RD|TH)\b", t)
    if found:
        return f"L{int(found.group(1) or found.group(2))}"
    for word, n in words.items():
        if re.search(r"\b" + word + r"\b", t):
            return f"L{n}"
    if "MEZZ" in t:
        return "MEZ"
    return re.sub(r"\s+", " ", t).strip()


# --- field judgements ---------------------------------------------------------------------------------------------


def judge_decision(expected, actual_status: str | None, candidates=(), flags=(), has_record: bool = True) -> str:
    """One decision outcome:
    tp (accepted, correct) | wrong (accepted, a different positive) | fp (accepted where truth is UR / n/a) |
    tn (UR / no record where truth is UR / n/a) | held (right decision kept as a candidate, not accepted) |
    missed (positive truth, nothing accepted, not held) | conflict_ok | conflict_missing (truth conflict) |
    unscorable."""
    truth = DECISION_WORDS.get((literal(expected) or "unlabelled").lower(), literal(expected))
    status = actual_status if (has_record and actual_status not in (None, "")) else "UR"
    accepted = status in POSITIVE_DECISIONS
    if truth in UNSCORABLE or truth == "absent" or truth is None:
        return "unscorable"
    if truth == "conflict":
        statuses = {c[0] for c in candidates or () if c}
        return "conflict_ok" if not accepted and ("decision_conflict" in (flags or ()) or len(statuses) > 1) else "conflict_missing"
    if truth in ("UR", "n/a"):
        return "fp" if accepted else "tn"
    if truth in POSITIVE_DECISIONS:
        if accepted:
            return "tp" if status == truth else "wrong"
        if any(c and c[0] == truth for c in candidates or ()):
            return "held"
        return "missed"
    return "unscorable"


def judge_reference(expected, actual: str | None) -> str:
    """tp | near | wrong | fp (invented where truth is absent / n/a) | tn | missed | unscorable."""
    truth = literal(expected)
    if truth is None or truth in UNSCORABLE:
        return "unscorable"
    if truth in NEGATIVE:
        return "fp" if actual else "tn"
    if not actual:
        return "missed"
    same = same_identity(truth, actual)
    return {"exact": "tp", "suffix": "tp", "near": "near"}.get(same, "wrong")


def raw_revision(record: dict) -> str | None:
    if record.get("printed_revision"):
        return record["printed_revision"]
    if record.get("revision_source") in RAW_REVISION_SOURCES:
        return record.get("revision")
    return None


def judge_revision(expected, record: dict | None, expected_reference: str | None = None) -> str:
    """Raw printed revision: tp | wrong | fp (a revision where truth is absent) | tn | missed (not extracted) |
    unscorable. A reference whose suffix carries the revision ('...-R3') is judged by the suffix."""
    truth_raw = expected
    if expected_reference:
        _, suffix = split_suffix(literal(expected_reference) or "")
        if suffix and (literal(expected) in (None, "absent") or str(expected).upper().startswith("R")):
            truth_raw = suffix
    truth = norm_rev(truth_raw)
    got = norm_rev(raw_revision(record)) if record else None
    if truth is None or truth in UNSCORABLE:
        return "unscorable"
    if truth in NEGATIVE:
        return "fp" if got else "tn"
    if not got:
        return "missed"
    return "tp" if got == truth else "wrong"


def judge_system(expected, record: dict | None) -> str:
    accepted = expected_systems(expected)
    if accepted is None:
        return "unscorable"
    got = (record or {}).get("system_code")
    if not accepted:
        return "fp" if got in TRACKED else "tn"
    if not got:
        return "missed"
    return "tp" if got in accepted else "wrong"


def judge_floor(expected, record: dict | None) -> str:
    truth = literal(expected)
    got = (record or {}).get("floor")
    if truth is None or truth in UNSCORABLE:
        return "unscorable"
    if truth in NEGATIVE:
        return "fp" if got else "tn"
    if not got:
        return "missed"
    return "tp" if floor_key(truth) == floor_key(got) else "wrong"


def judge_title(expected, record: dict | None) -> str:
    truth = literal(expected)
    got = (record or {}).get("name")
    if truth is None or truth in UNSCORABLE or truth in NEGATIVE:
        return "unscorable"
    if not got:
        return "missed"
    a = set(re.findall(r"[A-Z0-9]{2,}", truth.upper()))
    b = set(re.findall(r"[A-Z0-9]{2,}", str(got).upper()))
    if not a:
        return "unscorable"
    return "tp" if len(a & b) / len(a) >= 0.6 else "wrong"


# --- record matching ------------------------------------------------------------------------------------------------


def match_page(expected: list[dict], emitted: list[dict]) -> list[tuple[dict | None, dict | None, str]]:
    """Pair expected and emitted records of one page by identity. Returns (expected, emitted, how) with how in
    matched | substituted (an emitted record takes an unmatched expected slot) | missing | extra | duplicate."""
    pairs: list[tuple[dict | None, dict | None, str]] = []
    left = list(emitted)
    open_expected = []
    for exp in expected:
        best = next((r for r in left if same_identity(exp["reference"], r.get("reference")) in ("exact", "suffix")), None)
        if best is None:
            best = next((r for r in left if same_identity(exp["reference"], r.get("reference")) == "near"), None)
        if best is not None:
            left.remove(best)
            pairs.append((exp, best, "matched"))
        else:
            open_expected.append(exp)
    for exp in open_expected:
        if left:
            pairs.append((exp, left.pop(0), "substituted"))
        else:
            pairs.append((exp, None, "missing"))
    seen = {norm_ref(p[1].get("reference")) for p in pairs if p[1] is not None}
    for r in left:
        pairs.append((None, r, "duplicate" if norm_ref(r.get("reference")) in seen else "extra"))
    return pairs


# --- the evaluation -------------------------------------------------------------------------------------------------


def page1_expectation(doc: dict, in_scope: bool) -> list[dict]:
    """A v1 (page-1) label as an expected record set for page 1: one record when it names a reference, none when the
    reference is absent / n/a; unscorable when the reference is unknown."""
    lab = doc["labels"]
    ref = literal(lab.get("reference"))
    if ref is None or ref in UNSCORABLE:
        return [{"page": 1, "component": "page1", "reference": None, "unscorable": True, "labels": lab, "register": in_scope}]
    if ref in NEGATIVE:
        return []
    return [{"page": 1, "component": "page1", "reference": ref, "printed_revision": lab.get("revision"), "decision": lab.get("decision"),
             "system": lab.get("system"), "floor": lab.get("floor"), "title": lab.get("title"), "register": in_scope,
             "confidence": doc.get("confidence"), "revision_conflict": bool(lab.get("revision_conflict"))}]


SCOPE_PREFIXES = ("shop-drawing cover", "shop-drawing transmittal", "material submittal", "material approval", "material / equipment approval",
                  "material sample", "sample approval", "reply", "drawing sheet (shop drawing", "drawing sheet (contractor shop drawing",
                  "shop drawing sheet", "stamped shop drawing", "commented shop drawing", "technical submission", "document submittal",
                  "pre-qualification", "transmittal", "word transmittal", "drawing sheet (scanned")


def in_scope(kind) -> bool:
    return any(str(kind or "").lower().startswith(p) for p in SCOPE_PREFIXES)


def records_of(row: dict | None) -> list[dict]:
    return list(((row or {}).get("extracted") or {}).get("records") or [])


def evaluate(labels: dict, page_labels: dict | None, rows: dict, corrections: list[dict] | None = None) -> dict:
    """Score one profile's stored rows against the truth. Returns per-document results and totals."""
    rows = {k.replace("\\", "/"): v for k, v in rows.items()}
    plabels = {k.replace("\\", "/"): v for k, v in ((page_labels or {}).get("documents") or {}).items()}
    fixes = {}
    for c in corrections or ():
        fixes.setdefault(c["doc_suffix"], []).append(c)
    docs_out = []
    for doc in labels["documents"]:
        key = doc["doc"].replace("\\", "/")
        lab = dict(doc["labels"])
        for suffix, items in fixes.items():
            if key.endswith(suffix):
                for c in items:
                    lab[c["field"]] = c["new"]
        doc = {**doc, "labels": lab}
        row = rows.get(key)
        scope = in_scope(literal(lab.get("kind")) or lab.get("kind"))
        emitted = records_of(row)
        entry = {"doc": key, "ep": doc["ep"], "cohort": doc["cohort"], "stratum": doc["stratum"], "extension": doc["extension"],
                 "scan_like": doc.get("scan_like"), "confidence": doc.get("confidence"), "in_scope": scope,
                 "truth": "v2 page records" if key in plabels else "v1 page 1", "state": (row or {}).get("state"),
                 "outcome": (((row or {}).get("extracted") or {}).get("coverage") or {}).get("outcome"), "pairs": [], "unvalidated": []}
        if row is None:
            entry["outcome"] = "not-run"
            docs_out.append(entry)
            continue
        if key in plabels:
            pl = plabels[key]
            expected = [dict(r, confidence=r.get("confidence", "high")) for r in pl["records"]]
            no_record = {int(p) for p in (pl.get("no_record_pages") or {})}
            unvalidated = set(pl.get("unvalidated_pages") or [])
            labelled_pages = {r["page"] for r in expected} | no_record
        else:
            expected = page1_expectation(doc, scope)
            labelled_pages = {1}
            no_record, unvalidated = set(), set()
        by_page_exp = collections.defaultdict(list)
        for r in expected:
            by_page_exp[r["page"]].append(r)
        by_page_emit = collections.defaultdict(list)
        for r in emitted:
            by_page_emit[int(r.get("page") or 1)].append(r)
        doc_identities = {norm_ref(split_suffix(r["reference"])[0]) for r in expected if r.get("reference")}
        for page in sorted(set(by_page_exp) | set(by_page_emit)):
            if page not in labelled_pages or page in unvalidated:
                for r in by_page_emit.get(page, []):
                    entry["unvalidated"].append({"page": page, "reference": r.get("reference"), "status": r.get("status")})
                continue
            exp = [e for e in by_page_exp.get(page, []) if not e.get("unscorable")]
            if any(e.get("unscorable") for e in by_page_exp.get(page, [])):
                for r in by_page_emit.get(page, []):
                    entry["unvalidated"].append({"page": page, "reference": r.get("reference"), "status": r.get("status"), "why": "truth unknown"})
                continue
            for e, a, how in match_page(exp, by_page_emit.get(page, [])):
                p = {"page": page, "how": how, "expected": e and {k: e.get(k) for k in ("component", "reference", "printed_revision", "decision", "register", "confidence", "duplicate_of_page", "revision_conflict")},
                     "actual": a and {k: a.get(k) for k in ("reference", "revision", "printed_revision", "revision_source", "status", "system_code", "floor", "name", "flags", "decision_candidates", "category")}}
                if how in ("matched", "substituted") and e is not None and e.get("duplicate_of_page"):
                    p["duplicate_component"] = True
                if how == "extra" and norm_ref(split_suffix(a.get("reference") or "")[0]) in doc_identities:
                    how = p["how"] = "duplicate"      # the document's own identity again on a component page (a photo, a QA sheet)
                if how == "extra":
                    p["fields"] = {"reference": "fp", "decision": "fp" if a.get("status") in POSITIVE_DECISIONS else "tn"}
                elif how == "duplicate":
                    p["fields"] = {}
                else:
                    ref_state = judge_reference(e["reference"], a.get("reference") if a else None) if how != "substituted" else ("wrong" if a else "missed")
                    if how == "missing":
                        ref_state = "missed"
                    elif a is not None and set(a.get("flags") or ()) & set(UNCERTAIN_REFERENCE_FLAGS):
                        ref_state = "held"         # the reader said it could not settle the number: not an accepted value
                    p["fields"] = {"reference": ref_state,
                                   "revision": judge_revision(e.get("printed_revision"), a, e.get("reference")) if a else "missed",
                                   "decision": judge_decision(e.get("decision"), a.get("status") if a else None, (a or {}).get("decision_candidates") or (), (a or {}).get("flags") or (), a is not None)}
                    if "system" in e:
                        p["fields"]["system"] = judge_system(e.get("system"), a)
                    if "floor" in e or "floor_raw" in e:
                        p["fields"]["floor"] = judge_floor(e.get("floor", e.get("floor_raw")), a)
                    if "title" in e:
                        p["fields"]["title"] = judge_title(e.get("title"), a)
                    said = a is not None and "revision_conflict" in (a.get("flags") or ())
                    if e.get("revision_conflict"):
                        p["fields"]["revision_conflict"] = "conflict_ok" if said else "conflict_missing"
                    elif said:
                        p["fields"]["revision_conflict"] = "fp"
                    if a is not None and a.get("revision") and raw_revision(a) is None:
                        p["projection_revision"] = {"revision": a.get("revision"), "source": a.get("revision_source")}
                if how == "missing" and e is not None and not e.get("register", True):
                    # an untracked discipline or an evidence-only component: not a register miss; the raw evidence
                    # may still be held as an observation on the page
                    obs = [o for o in (((row or {}).get("extracted") or {}).get("observations") or []) if int(o.get("page") or 1) == page]
                    found = any(same_identity(e["reference"], o.get("reference") or (o.get("record") or {}).get("reference")) in ("exact", "suffix", "near") for o in obs)
                    p["how"] = "unregistered"
                    p["fields"] = {"raw_evidence": "tp" if found else "missed"}
                if how == "missing" and e is not None and e.get("duplicate_of_page"):
                    p["how"] = "component_not_repeated"      # a second page of the same identity: not a miss
                    p["fields"] = {}
                entry["pairs"].append(p)
        # page 1 truth that says "no reference" and nothing was emitted: a true negative, counted
        if key not in plabels and not expected and not by_page_emit.get(1):
            entry["pairs"].append({"page": 1, "how": "negative", "fields": {"reference": "tn", "decision": "tn"}})
        docs_out.append(entry)
    return {"evaluator": EVALUATOR_VERSION, "documents": docs_out, "totals": totals(docs_out)}


def rates(counter: collections.Counter) -> dict:
    tp, wrong, near, fp = counter["tp"], counter["wrong"], counter["near"], counter["fp"]
    accepted = tp + wrong + near + fp
    positives = tp + wrong + near + counter["missed"] + counter["held"]
    negatives = counter["tn"] + fp
    out = {k: counter[k] for k in ("tp", "wrong", "near", "fp", "tn", "missed", "held", "conflict_ok", "conflict_missing", "unscorable")}
    out.update({"accepted": accepted,
                "precision_of_accepted": round(tp / accepted, 4) if accepted else None,
                "recovery_of_readable": round(tp / positives, 4) if positives else None,
                "specificity_of_negatives": round(counter["tn"] / negatives, 4) if negatives else None,
                "abstention_rate": round((counter["missed"] + counter["held"]) / positives, 4) if positives else None,
                "held_evidence": counter["held"]})
    return out


def totals(docs: list[dict], key=None) -> dict:
    fields = collections.defaultdict(collections.Counter)
    record_how = collections.Counter()
    unvalidated = 0
    critical = []
    for d in docs:
        unvalidated += len(d.get("unvalidated") or [])
        for p in d.get("pairs") or []:
            record_how[p["how"]] += 1
            for f, state in (p.get("fields") or {}).items():
                fields[f][state] += 1
            f = p.get("fields") or {}
            act = p.get("actual") or {}
            if f.get("decision") in ("fp", "wrong") and act.get("status") in ("approved", "ANN"):
                critical.append({"kind": "false approval", "doc": d["doc"], "page": p["page"], "expected": (p.get("expected") or {}).get("decision"), "actual": act.get("status")})
            elif f.get("decision") in ("fp", "wrong"):
                critical.append({"kind": "wrong decision accepted", "doc": d["doc"], "page": p["page"], "expected": (p.get("expected") or {}).get("decision"), "actual": act.get("status")})
            if f.get("reference") in ("wrong", "near", "fp") and act:
                critical.append({"kind": "wrong reference accepted" if f.get("reference") != "fp" else "record where truth has none", "doc": d["doc"], "page": p["page"],
                                 "expected": (p.get("expected") or {}).get("reference"), "actual": act.get("reference"), "how": p["how"]})
            if f.get("revision") in ("wrong", "fp") and act:
                critical.append({"kind": "wrong printed revision accepted", "doc": d["doc"], "page": p["page"], "expected": (p.get("expected") or {}).get("printed_revision"), "actual": raw_revision(act)})
    return {"records": dict(record_how), "unvalidated_emitted_records": unvalidated, "fields": {f: rates(c) for f, c in fields.items()}, "critical": critical}


def grouped(result: dict, keyfn) -> dict:
    groups = collections.defaultdict(list)
    for d in result["documents"]:
        groups[keyfn(d)].append(d)
    return {str(k): {"documents": len(v), "outcomes": dict(collections.Counter(d.get("outcome") for d in v)), **totals(v)} for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--page-labels")
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))
    page_labels = json.loads(Path(args.page_labels).read_text(encoding="utf-8")) if args.page_labels else None
    rows = json.loads(Path(args.rows).read_text(encoding="utf-8"))
    result = evaluate(labels, page_labels, rows, (page_labels or {}).get("page1_corrections"))
    result["by"] = {
        "project": grouped(result, lambda d: d["ep"]), "cohort": grouped(result, lambda d: d["cohort"]),
        "format": grouped(result, lambda d: "word" if d["extension"] != ".pdf" else ("scan" if d["scan_like"] else "text")),
        "scope": grouped(result, lambda d: "in scope" if d["in_scope"] else "out of scope"),
        "scope_cohort": grouped(result, lambda d: f"{'in' if d['in_scope'] else 'out'} / {d['cohort']}"),
        "truth": grouped(result, lambda d: d["truth"]), "label_confidence": grouped(result, lambda d: d.get("confidence")),
        "stratum": grouped(result, lambda d: d["stratum"]),
    }
    Path(args.out).write_text(json.dumps(result, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    t = result["totals"]
    print(json.dumps({"records": t["records"], "unvalidated": t["unvalidated_emitted_records"], "critical": len(t["critical"]),
                      **{f: {k: v[k] for k in ("accepted", "tp", "precision_of_accepted", "recovery_of_readable", "specificity_of_negatives")} for f, v in t["fields"].items()}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
