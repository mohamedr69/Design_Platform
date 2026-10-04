"""ORCH-05.1 (Review 33 C-5 / C-6 scorer rules, R33-09): literal comparison for the r32 scorer and tripwire.

compare(truth_literal, predicted_literal, field, *, alternates=(), truth_class=None, resubmission_required=False)
  -> {"match": bool, "kind": str, "truth_norm": str, "predicted_norm": str}

Rules (each one names its source):
  * whitespace-insensitive ((i2) "the scorer compares whitespace-insensitively"): every Unicode whitespace character
    is removed before comparison ('MEP 2 1 7' == 'MEP217'; 'FA- 6001' == 'FA-6001'; '... -0002- R00' == '...-0002-R00');
  * hyphen variants: U+2010 hyphen, U+2011 non-breaking hyphen, U+2012 figure dash, U+2013 en dash, U+2014 em dash,
    U+2015 horizontal bar, U+2212 minus sign, U+FE58, U+FE63, U+FF0D are read as '-' ('MAT – 116' == 'MAT-116');
  * identity: case-insensitive (as evaluator .10's norm_ref upper-cases);
  * either-form labelled tails ((g)(1)): the row's `alternates` (from the adapter: the printed form with its own
    labelled 'Rev.' tail, and the base form of an unlabelled '- R0n' suffix carried from evaluator .10's 'suffix'
    identity equivalence) are accepted under the same normalisation; kind says which form matched;
  * revision: numbers by value with an optional R / REV / REV. / REVISION prefix ('00' == '0' == 'R0' == 'Rev. 0'),
    letters and mixed tokens as written (evaluator .10 norm_rev parity);
  * decision: compared by CLASS. Truth classes: approved, approved as noted, revise and resubmit, rejected, other.
    A prediction in the application vocabulary maps to classes: approved -> {approved}; ANN / approved as noted /
    approved with comments -> {approved as noted}; rejected -> {revise and resubmit, rejected} (the application files
    'revise and resubmit', 'resubmit' and 'not approved' all as 'rejected': evidence_reader.EVIDENCE_OPTIONS,
    document_control._OPTIONS). Negative words (UR, n/a, none, absent, empty) assert no decision -> never a match.
    (d1) resubmission tolerance: on a row with resubmission_required yes (class approved as noted, a printed option
    such as 'Approved as noted / Resubmit' or 'B+R'), a prediction whose classes include 'revise and resubmit' also
    matches (kind 'd1_resubmission_tolerance'); 'approved' alone never does. A prediction equal to the truth literal
    after normalisation also matches (kind 'decision_literal');
  * Arabic literals (any character in the Arabic blocks): compared BYTE FOR BYTE (UTF-8) after whitespace removal
    only: no case folding, no dash folding, Arabic-Indic digits are NOT mapped to ASCII digits.
Pure functions; nothing is read or written."""
from __future__ import annotations

import re
import unicodedata

DASHES = "‐‑‒–—―−﹘﹣－"
_DASH_RE = re.compile("[" + DASHES + "]")
_WS_RE = re.compile(r"\s+", re.UNICODE)
_ARABIC_RE = re.compile("[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
NEGATIVE_DECISION_WORDS = {"", "ur", "n/a", "na", "none", "absent", "no decision", "not applicable", "unknown"}
CLASSES = ("approved", "approved as noted", "revise and resubmit", "rejected", "other")
# longest phrase first; the same readings as the application's option words, mapped to the label classes
_PHRASES = (("approved as noted", {"approved as noted"}), ("no objection as noted", {"approved as noted"}),
            ("approved with comments", {"approved as noted"}), ("with comments", {"approved as noted"}),
            ("as noted", {"approved as noted"}), ("ann", {"approved as noted"}),
            ("revise and resubmit", {"revise and resubmit"}), ("revise & resubmit", {"revise and resubmit"}),
            ("revise resubmit", {"revise and resubmit"}), ("resubmit", {"revise and resubmit"}), ("revise", {"revise and resubmit"}),
            ("not approved", {"revise and resubmit", "rejected"}), ("rejected", {"revise and resubmit", "rejected"}),
            ("no objection", {"approved"}), ("approved", {"approved"}))


def is_arabic(text) -> bool:
    return bool(text) and bool(_ARABIC_RE.search(str(text)))


def norm_text(value) -> str:
    """Whitespace removed; for a non-Arabic literal also dash variants -> '-'. (Case is the caller's.)"""
    s = "" if value is None else str(value)
    s = _WS_RE.sub("", s)
    if not is_arabic(s):
        s = _DASH_RE.sub("-", s)
    return s


def norm_identity(value) -> str:
    s = norm_text(value)
    return s if is_arabic(s) else s.upper()


def norm_revision(value) -> str:
    """A revision compared by value. Arabic literals: norm_text only (whitespace removed; no case or dash folding).
    Otherwise dash variants are read as '-' and the value is upper-cased; then, after an optional REVISION / REV /
    REV. / R / R. prefix, EVERY whitespace character inside the value is removed before the number is matched ((i2);
    ORCH-06C, Verification 36 R36-08), and a number is read by value: '0 1' == '01' == 'REV 0 1' == 'R 01' -> 'R1',
    '0 0' -> 'R0', 'Rev. 0 2' -> 'R2'. A value that is not a number keeps its own characters with every whitespace
    character removed ('A 1' -> 'A1')."""
    s = "" if value is None else str(value).strip()
    if is_arabic(s):
        return norm_text(s)
    s = _DASH_RE.sub("-", s).upper()
    s = _WS_RE.sub(" ", s).strip()
    prefix = re.match(r"(?:REVISION|REV\.?|R\.?)?", s)
    m = re.fullmatch(r"0*(\d+)", _WS_RE.sub("", s[prefix.end():]))
    if m:
        return f"R{int(m.group(1))}"
    return _WS_RE.sub("", s)


def decision_classes(predicted) -> set:
    """The label classes a predicted decision value can mean (empty set: no decision asserted / unrecognised)."""
    if predicted is None:
        return set()
    s = str(predicted).strip()
    low = _WS_RE.sub(" ", _DASH_RE.sub("-", s.lower())).strip()
    if low in NEGATIVE_DECISION_WORDS:
        return set()
    if low == "rejected":                 # the application's word for revise-and-resubmit, not-approved and rejected
        return {"revise and resubmit", "rejected"}
    if low in CLASSES:
        return {low}
    if s == "ANN":
        return {"approved as noted"}
    for phrase, classes in _PHRASES:
        if re.search(r"(^|[^a-z])" + re.escape(phrase) + r"($|[^a-z])", low):
            return set(classes)
    return set()


def compare(truth_literal, predicted_literal, field: str, *, alternates=(), truth_class=None, resubmission_required=False) -> dict:
    if field == "decision":
        return _compare_decision(truth_literal, predicted_literal, truth_class, resubmission_required)
    if predicted_literal is None or str(predicted_literal).strip() == "":
        return {"match": False, "kind": "no_prediction", "truth_norm": None, "predicted_norm": None}
    norm = norm_identity if field == "identity" else norm_revision
    tn, pn = norm(truth_literal), norm(predicted_literal)
    if is_arabic(truth_literal) or is_arabic(predicted_literal):
        same = norm_text(truth_literal).encode("utf-8") == norm_text(predicted_literal).encode("utf-8")
        return {"match": same, "kind": "arabic_bytes" if same else "different", "truth_norm": norm_text(truth_literal),
                "predicted_norm": norm_text(predicted_literal)}
    if tn == pn:
        exact = str(truth_literal) == str(predicted_literal)
        return {"match": True, "kind": "exact" if exact else "normalised", "truth_norm": tn, "predicted_norm": pn}
    for alt in alternates or ():
        if norm(alt) == pn:
            return {"match": True, "kind": "alternate_form", "alternate": alt, "truth_norm": tn, "predicted_norm": pn}
    return {"match": False, "kind": "different", "truth_norm": tn, "predicted_norm": pn}


def _compare_decision(truth_literal, predicted, truth_class, resubmission_required) -> dict:
    pc = decision_classes(predicted)
    out = {"truth_class": truth_class, "predicted_classes": sorted(pc), "truth_norm": norm_text(truth_literal),
           "predicted_norm": norm_text(predicted)}
    if predicted is not None and truth_literal is not None and norm_text(predicted) and \
            (norm_text(predicted) == norm_text(truth_literal) if is_arabic(truth_literal) or is_arabic(predicted)
             else norm_text(predicted).lower() == norm_text(truth_literal).lower()):
        return {**out, "match": True, "kind": "decision_literal"}
    if not pc:
        negative = predicted is None or str(predicted).strip().lower() in NEGATIVE_DECISION_WORDS
        return {**out, "match": False, "kind": "no_decision_asserted" if negative else "unrecognised"}
    if truth_class in pc:
        return {**out, "match": True, "kind": "class" if len(pc) == 1 else "class_application_vocabulary"}
    if resubmission_required and "revise and resubmit" in pc:
        return {**out, "match": True, "kind": "d1_resubmission_tolerance"}
    return {**out, "match": False, "kind": "different_class"}


def compare_row(rec: dict, predicted) -> dict:
    """compare() with the adapter row's own literal, class, alternates and resubmission flag."""
    return compare(rec.get("literal"), predicted, rec["field"], alternates=rec.get("alternates") or (),
                   truth_class=rec.get("class"), resubmission_required=bool(rec.get("resubmission_required")))


def asserts_decision(predicted) -> bool:
    """Whether a predicted decision value asserts a decision at all (a negative word or empty asserts none)."""
    return bool(decision_classes(predicted)) or (predicted is not None and str(predicted).strip().lower() not in NEGATIVE_DECISION_WORDS)


def nfc(text) -> str:
    return unicodedata.normalize("NFC", str(text))
