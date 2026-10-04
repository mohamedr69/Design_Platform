"""ORCH-06 (Review 33 C-6), agent R35EVAL-IMPL: the SYNTHETIC prediction fixture generator.

Usage: fixtures_r32.py <out json abs>          (writes only <out json>; prints a coverage summary)

Builds SYNTHETIC-PREDICTIONS.json from TWO frozen inputs only, both re-hashed before they are read:
  review34/dry-run/TRUTH-R32.json            (4e237a4e...)  the adapter truth rows (literal, class, alternates, kind)
  review34/LABELS-R32-EVAL-INPUT.json         (4b2c73d5...)  the evaluator .10 input (the encoded truth per page)
No prediction, arm output, page image, earlier label set or cohort file is read. A file or folder name is never evidence.

Every fixture is ONE synthetic fact (or no fact) offered on ONE truth row (pool id, page, field):
  kind "SYNTHETIC", the truth key, a group, a variant name, the intent (what the reviewed conventions and the declared
  interpretations say the verdict should be, as this generator reads them), and the EXPECTED HARNESS VERDICT computed by
  the frozen review34 harness itself: literal_compare_r32.compare_row on the pair, and lane_judge_r32.judge_document on
  the document with that single fact (state 'accepted'). Nothing is assumed.

Groups:
  identity_value / revision_value / decision_value   every scorable value row of a canonical document: exact and
                                                     equivalent variants plus wrong-value controls and 'absent'
  absent_row                                         every ABSENT row: no fact, a negative word, foreign values
  not_scorable_row                                   every NOT_SCORABLE row: absent, its literal / candidates / class word,
                                                     a wrong value (expected: excluded, never read as absent)
  compilation_page_keyed                             F002, F035, F043: a value of one page offered on another page
  cross_page_identity                                non-compilation documents: another page's identity offered on a page
                                                     (drawing sets F014, F016, F038 and cover / enclosure packages)
Count-once aliases (F031, F052, F059, F070) are not in the evaluator input (converter exclusion); their rows are listed
under `excluded_rows` and are not fixtures.
Deterministic: no clock, no randomness; the output bytes depend only on the two inputs and this file."""
from __future__ import annotations

import collections
import pathlib
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import common_r35 as C  # noqa: E402

LC, J, A = C.import_harness()

SCHEMA = "r35-synthetic-predictions-1"
DASH_TARGETS = (("hyphen", "-"), ("en_dash", "–"), ("minus", "−"), ("figure_dash", "‒"),
                ("em_dash", "—"), ("nb_hyphen", "‑"))
DASH_CHARS = "-" + LC.DASHES
ARABIC_INDIC = "٠١٢٣٤٥٦٧٨٩"
PROJECT_JOB_NUMBER_SOURCE = "F069|1|identity"     # its candidate is the job number under 'Reference' (Review 33 D-004)
DECISION_WORD = {"approved": "approved", "approved as noted": "ANN", "revise and resubmit": "rejected", "rejected": "rejected"}
SYNONYMS = {
    "approved": ("approved", "Approved", "APPROVED", "No Objection"),
    "approved as noted": ("ANN", "approved as noted", "Approved as Noted", "approved with comments", "No objection with comments",
                          "B", "Code B", "Code B+R"),
    "revise and resubmit": ("rejected", "revise and resubmit", "Revise & Resubmit", "resubmit", "Code C", "C - Revise & Resubmit",
                            "Not Approved (Re-submit)"),
}
D1_EXTRAS = ("rejected", "Revise & Resubmit", "resubmit", "Approved as noted / Resubmit", "B+R")
WRONG_CLASS_WORDS = {"approved": ("ANN", "rejected"), "approved as noted": ("approved", "rejected"),
                     "revise and resubmit": ("approved", "ANN")}
CODE_D = "Code D - Rejected"


# --- string transformations (pure) -----------------------------------------------------------------------------------


def has_ws(s: str) -> bool:
    return bool(re.search(r"\s", s))


def dash_positions(s: str) -> list[int]:
    return [i for i, ch in enumerate(s) if ch in DASH_CHARS]


def ws_after_first_sep(s: str) -> str:
    pos = [i for i, ch in enumerate(s) if ch in DASH_CHARS + "/"]
    if pos:
        i = pos[0] + 1
        return s[:i] + " " + s[i:]
    mid = max(1, len(s) // 2)
    return s[:mid] + " " + s[mid:]


def ws_after_every_dash(s: str) -> str:
    return "".join(ch + (" " if ch in DASH_CHARS else "") for ch in s)


def ws_padding(s: str) -> str:
    return "  " + s.replace(" ", "  ") + " "


def replace_dashes(s: str, target: str) -> str:
    return "".join(target if ch in DASH_CHARS else ch for ch in s)


def hyphen_moved(s: str) -> str | None:
    pos = dash_positions(s)
    if not pos:
        return None
    i = pos[0]
    rest = s[:i] + s[i + 1:]
    j = next((k for k in range(i, len(rest)) if rest[k].isalnum()), None)
    if j is None:
        return None
    return rest[:j + 1] + s[i] + rest[j + 1:]


def hyphen_inserted(s: str) -> str:
    alnum = [i for i, ch in enumerate(s) if ch.isalnum()]
    k = alnum[len(alnum) // 2] if len(alnum) > 1 else len(s)
    return s[:k] + "-" + s[k:]


SEPARATORS = re.compile(r"[-/_.–−‒—‑]")


def segment_dropped(s: str) -> str:
    """The last separator-delimited segment dropped ('B01-ASC-SD-ELE-0102' -> 'B01-ASC-SD-ELE'); a single segment
    loses its last character ('K18' -> 'K1')."""
    found = list(SEPARATORS.finditer(s))
    if found:
        head = s[:found[-1].start()].rstrip()
        if head.strip():
            return head
    return s[:-1] if len(s) > 1 else s + "X"


def digit_changed(s: str) -> str:
    for i in range(len(s) - 1, -1, -1):
        ch = s[i]
        if ch in "0123456789":
            return s[:i] + str((int(ch) + 1) % 10) + s[i + 1:]
    for i in range(len(s) - 1, -1, -1):
        ch = s[i]
        if ch in ARABIC_INDIC:
            return s[:i] + ARABIC_INDIC[(ARABIC_INDIC.index(ch) + 1) % 10] + s[i + 1:]
    for i in range(len(s) - 1, -1, -1):
        if s[i].isalpha() and s[i].isascii():
            return s[:i] + ("B" if s[i].upper() != "B" else "C") + s[i + 1:]
    return s + "1"


def leading_zero_dropped(s: str) -> str | None:
    m = re.search(r"(?<![0-9])0+([0-9])", s)
    if not m:
        return None
    return s[:m.start()] + s[m.start() + 1:]


def leading_zero_added(s: str) -> str | None:
    m = re.search(r"(?<![0-9])([1-9][0-9]*)", s)
    if not m:
        return None
    return s[:m.start()] + "0" + s[m.start():]


def arabic_digits_to_ascii(s: str) -> str:
    return "".join(str(ARABIC_INDIC.index(ch)) if ch in ARABIC_INDIC else ch for ch in s)


def ws_normalised(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def ws_removed(s: str) -> str:
    return re.sub(r"\s+", "", s)


def revision_number(t: str) -> tuple[str, int] | None:
    m = re.fullmatch(r"(?:Rev\.\s*)?(\d+)", t.strip(), re.I)
    return (m.group(1), int(m.group(1))) if m else None


# --- the generator --------------------------------------------------------------------------------------------------


class Gen:
    def __init__(self, truth: dict, eval_input: dict):
        self.truth = truth
        self.ein = eval_input
        self.canon = sorted(pid for pid, d in truth["documents"].items() if not d["is_alias"])
        self.rows = truth["rows"]
        self.keys = sorted(self.rows, key=lambda k: (k.split("|")[0], int(k.split("|")[1]), C.FIELDS.index(k.split("|")[2])))
        self.fixtures: list[dict] = []
        self.baseline: dict = {}
        self.job_number = (self.rows[PROJECT_JOB_NUMBER_SOURCE].get("candidates") or [None])[0]
        assert self.job_number, "the D-004 job number candidate is missing from the truth"
        self.encoded = self._encoded_truth()

    # the evaluator .10 encoding of every canonical row (from LABELS-R32-EVAL-INPUT, the converter output)
    def _encoded_truth(self) -> dict:
        out = {}
        idx = self.ein["r32_sidecar"]["pool_index"]
        fk = {"identity": "reference", "revision": "printed_revision", "decision": "decision"}
        for key, pd in self.ein["page"]["documents"].items():
            pid = idx[key]
            for pg, why in pd["no_record_pages"].items():
                for f in C.FIELDS:
                    out[C.row_key(pid, pg, f)] = {"where": f"no_record_pages[{pg}]",
                                                  "encoded": why.get("decision") if f == "decision" else "absent"}
            for pg in pd["unvalidated_pages"]:
                for f in C.FIELDS:
                    out[C.row_key(pid, pg, f)] = {"where": f"unvalidated_pages[{pg}]", "encoded": None}
            for rec in pd["records"]:
                for f in C.FIELDS:
                    out[C.row_key(pid, rec["page"], f)] = {"where": f"records[page {rec['page']}].{fk[f]}", "encoded": rec[fk[f]]}
        return out

    def doc_rows(self, pid, field=None, kind=None):
        return [self.rows[k] for k in self.keys if self.rows[k]["pool_id"] == pid and (field is None or self.rows[k]["field"] == field)
                and (kind is None or self.rows[k]["truth_kind"] == kind)]

    def value_rows(self, field):
        return [self.rows[k] for k in self.keys if self.rows[k]["field"] == field and self.rows[k]["truth_kind"] == "value"
                and self.rows[k]["pool_id"] in self.canon]

    def matches(self, rec, value) -> bool:
        if rec["truth_kind"] != "value" or value is None:
            return False
        return bool(LC.compare_row(rec, value)["match"])

    def donor(self, rec, *, field=None) -> dict | None:
        """Another canonical document's value for the field that the harness does not equate with this row (and, for an
        identity, with no identity of this row's own document; for a decision, of another class; for a revision, of
        another number)."""
        field = field or rec["field"]
        pool = self.value_rows(field)
        keys = [C.row_key(r["pool_id"], r["page"], r["field"]) for r in pool]
        me = C.row_key(rec["pool_id"], rec["page"], rec["field"])
        start = next((i for i, k in enumerate(keys) if k > me), 0)
        own_ids = self.doc_rows(rec["pool_id"], "identity", "value")
        for i in range(len(pool)):
            r = pool[(start + i) % len(pool)]
            if r["pool_id"] == rec["pool_id"]:
                continue
            v = r["literal"]
            if self.matches(rec, v):
                continue
            if field == "identity" and any(LC.compare_row(o, v)["match"] for o in own_ids):
                continue
            if field == "decision" and rec.get("class") is not None and r.get("class") == rec.get("class"):
                continue
            if field == "decision" and rec.get("resubmission_required") and r.get("class") in ("revise and resubmit", "rejected"):
                continue
            if field == "revision" and rec["truth_kind"] == "value":
                a, b = revision_number(rec["literal"] or ""), revision_number(v or "")
                if a and b and a[1] == b[1]:
                    continue
            return r
        return None

    # --- the expected harness verdict ------------------------------------------------------------------------------

    def _baseline(self, pid):
        if pid not in self.baseline:
            self.baseline[pid] = C.harness_judge(J, self.truth, pid, [])
        return self.baseline[pid]

    def expected_harness(self, rec, value) -> dict:
        pid, page, field = rec["pool_id"], rec["page"], rec["field"]
        facts = [] if value is None else [{"page": str(page), "field": field, "value": value, "state": "accepted"}]
        judged = C.harness_judge(J, self.truth, pid, facts)
        base = self._baseline(pid)
        target = judged[(str(page), field)]
        others = {C.row_key(pid, pg, f): v for (pg, f), v in sorted(judged.items(), key=lambda kv: (int(kv[0][0]), C.FIELDS.index(kv[0][1])))
                  if (pg, f) != (str(page), field) and v != base[(pg, f)]}
        if value is None:
            lit = {"applicable": False, "why": "no fact offered"}
        elif rec["truth_kind"] == "value":
            c = LC.compare_row(rec, value)
            lit = {"applicable": True, "against": "row literal", "match": bool(c["match"]), "kind": c["kind"]}
        elif rec["truth_kind"] == "not_scorable":
            refs = [x for x in [rec.get("literal"), *(rec.get("candidates") or [])] if x not in (None, "")]
            res = [{"reference": r, **{k: v for k, v in LC.compare(r, value, field, alternates=rec.get("alternates") or (), truth_class=rec.get("class"),
                                                                  resubmission_required=rec.get("resubmission_required")).items()
                                       if k in ("match", "kind")}} for r in refs]
            lit = {"applicable": bool(refs), "against": "NOT_SCORABLE literal and candidates (reported only)", "results": res,
                   "match": any(r["match"] for r in res) if res else None}
        else:
            lit = {"applicable": False, "why": "ABSENT truth row: no literal",
                   "asserts_decision": LC.asserts_decision(value) if field == "decision" else None}
        return {"literal_compare": lit, "judge": target, "other_rows_changed": others}

    # --- fixture recording -------------------------------------------------------------------------------------------

    def add(self, rec, group, variant, value, intent, note, **extra):
        pid = rec["pool_id"]
        doc = self.truth["documents"][pid]
        key = C.row_key(pid, rec["page"], rec["field"])
        fx = {"kind": "SYNTHETIC", "not_a_model_prediction": True, "truth_key": key, "pool_id": pid, "page": str(rec["page"]),
              "field": rec["field"], "truth_kind": rec["truth_kind"], "truth_literal": rec.get("literal"), "truth_class": rec.get("class"),
              "truth_alternates": list(rec.get("alternates") or []), "truth_candidates": list(rec.get("candidates") or []),
              "resubmission_required": bool(rec.get("resubmission_required")), "not_scorable_reasons": list(rec.get("not_scorable_reasons") or []),
              "compilation": bool(doc.get("compilation")), "drawing_set": pid in C.DRAWING_SETS, "doc_key": doc["doc_key"],
              "evaluator_truth_encoding": self.encoded.get(key), "group": group, "variant": variant,
              "prediction": {"page": str(rec["page"]), "field": rec["field"], "value": value}, "intent": intent, "note": note,
              "expected_harness": self.expected_harness(rec, value), **extra}
        self.fixtures.append(fx)

    # --- variant families ----------------------------------------------------------------------------------------------

    def identity_value(self, rec):
        lit, pid = rec["literal"], rec["pool_id"]
        g = "identity_value"
        self.add(rec, g, "exact", lit, "correct", "the truth literal as printed")
        if LC.is_arabic(lit):
            self.add(rec, g, "arabic_ws_removed", ws_removed(lit), "correct", "(i2) Arabic literal, every space removed")
            self.add(rec, g, "arabic_ws_normalised", ws_normalised(re.sub(r"\s*/\s*", " / ", lit)), "correct",
                     "(i2) Arabic literal, spaces normalised to one around each slash")
            self.add(rec, g, "arabic_ws_extra", ws_padding(lit), "correct", "(i2) Arabic literal, spaces doubled and padded")
            self.add(rec, g, "arabic_indic_digits_as_ascii", arabic_digits_to_ascii(lit), "wrong",
                     "Arabic-Indic digits written as ASCII digits (the frozen harness compares Arabic literals byte for byte)")
        else:
            if has_ws(lit):
                self.add(rec, g, "ws_removed_all", ws_removed(lit), "correct", "(i2) every whitespace character removed")
            self.add(rec, g, "ws_inserted_after_first_separator", ws_after_first_sep(lit), "correct", "(i2) one space inserted")
            if len(dash_positions(lit)) >= 2:
                self.add(rec, g, "ws_inserted_after_every_dash", ws_after_every_dash(lit), "correct", "(i2) a space after every dash")
            self.add(rec, g, "ws_padded_and_doubled", ws_padding(lit), "correct", "(i2) leading/trailing space, inner spaces doubled")
            if "C001-" in lit:
                self.add(rec, g, "ws_gap_C001_01", lit.replace("C001-", "C001- "), "correct", "(i2) the printed 'C001- 01' letter-spacing gap")
            if "MEP 2 1 7" in lit:
                self.add(rec, g, "ws_removed_inside_MEP_2_1_7", lit.replace("MEP 2 1 7", "MEP217"), "correct",
                         "(i2) 'MEP 2 1 7' read without its letter-spacing")
            if lit.lower() != lit:
                self.add(rec, g, "case_lower", lit.lower(), "correct", "identity case-insensitive (evaluator .10 norm_ref upper-cases)")
            if dash_positions(lit):
                for name, ch in DASH_TARGETS:
                    v = replace_dashes(lit, ch)
                    if v != lit:
                        self.add(rec, g, f"dash_as_{name}", v, "correct", f"every dash written as {name} (U+{ord(ch):04X})")
            for alt in rec.get("alternates") or []:
                why = (rec.get("alternate_kinds") or {}).get(alt, "")
                if why.startswith("(g)(1)"):
                    self.add(rec, g, "g1_labelled_tail_present", alt, "correct", "(g)(1) either form: the printed number with its 'Rev.' tail")
                    self.add(rec, g, "g1_labelled_tail_present_ws", alt.replace("-Rev.", " - Rev. "), "correct",
                             "(g)(1) tail form with spaces (i2)")
                    self.add(rec, g, "g1_labelled_tail_lower", alt.lower(), "correct", "(g)(1) tail form, lower case")
                elif "suffix base form" in why:
                    self.add(rec, g, "suffix_base_form", alt, "correct",
                             "unlabelled '- R0n' suffix base form (interpretation, Review 34 item 13; evaluator .10 'suffix')")
                    m = re.search(r"(-\s*R)(\d+)\s*$", lit)
                    if m:
                        wrong_suffix = lit[:m.start(2)] + str(int(m.group(2)) + 1).zfill(len(m.group(2)))
                        self.add(rec, g, "suffix_wrong_number", wrong_suffix, "wrong", "the base with a different '- R0n' suffix")
                    self.add(rec, g, "suffix_base_digit_changed", digit_changed(alt), "wrong", "the base form with one digit changed")
            tails = sorted({a for r in self.doc_rows(pid, "identity", "value") for a in (r.get("alternates") or [])
                            if (r.get("alternate_kinds") or {}).get(a, "").startswith("(g)(1)")})
            if tails and not any((rec.get("alternate_kinds") or {}).get(a, "").startswith("(g)(1)") for a in rec.get("alternates") or []):
                tail = re.search(r"-Rev\.\d+$", tails[0]).group(0)
                self.add(rec, g, "labelled_tail_not_printed_on_this_page", lit + tail, "wrong",
                         "a 'Rev.' tail on a page whose own number prints none ((g)(1) applies only where the tail is printed)")
            v = leading_zero_dropped(lit)
            if v and v != lit:
                self.add(rec, g, "leading_zero_dropped", v, "wrong", "conventions section 3: leading zeros are part of the printed number")
            v = leading_zero_added(lit)
            if v and v != lit:
                self.add(rec, g, "leading_zero_added", v, "wrong", "conventions section 3: leading zeros are part of the printed number")
            v = hyphen_moved(lit)
            if v:
                self.add(rec, g, "hyphen_moved", v, "wrong", "the first dash moved one character to the right")
            else:
                self.add(rec, g, "hyphen_inserted", hyphen_inserted(lit), "wrong", "a hyphen inserted inside the number")
        self.add(rec, g, "digit_changed", digit_changed(lit), "wrong", "one digit changed")
        sd = segment_dropped(lit)
        while sd != lit and self.matches(rec, sd) and segment_dropped(sd) != sd:
            sd = segment_dropped(sd)          # e.g. a '- R00' suffix row: dropping only the suffix gives the accepted base form
        if sd != lit and not self.matches(rec, sd):
            self.add(rec, g, "segment_dropped", sd, "wrong", "the last segment dropped (beyond any accepted base form)")
        d = self.donor(rec)
        if d:
            self.add(rec, g, "other_document_value", d["literal"], "wrong",
                     f"the identity of {C.row_key(d['pool_id'], d['page'], d['field'])}")
        self.add(rec, g, "project_job_number", self.job_number, "wrong",
                 f"a job number in place of the identity (the candidate of {PROJECT_JOB_NUMBER_SOURCE}, Review 33 D-004)")
        self.add(rec, g, "absent", None, "no_assertion", "no fact offered")

    def revision_value(self, rec):
        t = rec["literal"]
        g = "revision_value"
        num = revision_number(t)
        assert num, f"non-numeric revision truth {rec}"
        digits, n = num
        self.add(rec, g, "exact", t, "correct", "the truth literal as printed")
        if digits != str(n):
            self.add(rec, g, "leading_zero_dropped", str(n), "correct", "revision compared by value ('01' == '1')")
        self.add(rec, g, "leading_zero_added", "0" + digits, "correct", "revision compared by value ('0' == '00')")
        if t != digits:
            self.add(rec, g, "bare_number", digits, "correct", "the number without its printed 'Rev.' label")
        self.add(rec, g, "prefix_R", "R" + digits, "correct", "R-prefixed")
        self.add(rec, g, "prefix_Rev_dot", "Rev." + digits, "correct", "'Rev.' prefix without a space")
        self.add(rec, g, "prefix_Rev_dot_space", "Rev. " + digits, "correct", "'Rev. ' prefix with a space")
        self.add(rec, g, "prefix_REV_space", "REV " + digits, "correct", "'REV ' prefix")
        self.add(rec, g, "prefix_Revision_word", f"Revision {n}", "correct", "'Revision n'")
        self.add(rec, g, "ws_padded", " " + t + " ", "correct", "(i2) surrounding whitespace")
        if len(digits) >= 2:
            self.add(rec, g, "ws_inside_number", digits[0] + " " + digits[1:], "correct", "(i2) a space inside the printed number")
        width = len(digits)
        self.add(rec, g, "digit_changed", str(n + 1).zfill(width), "wrong", "the number plus one")
        self.add(rec, g, "prefixed_wrong_number", "Rev. " + str(n + 1).zfill(width), "wrong", "'Rev. ' and the number plus one")
        self.add(rec, g, "prefixed_far_number", "Rev. " + str(n + 7), "wrong", "'Rev. ' and another number")
        self.add(rec, g, "letter_value", "A", "wrong", "a letter revision")
        d = self.donor(rec)
        if d:
            self.add(rec, g, "other_document_value", d["literal"], "wrong",
                     f"the revision of {C.row_key(d['pool_id'], d['page'], d['field'])}")
        self.add(rec, g, "absent", None, "no_assertion", "no fact offered")

    def decision_value(self, rec):
        lit, cls, resub = rec["literal"], rec["class"], bool(rec.get("resubmission_required"))
        g = "decision_value"
        seen = set()

        def add(variant, value, intent, note):
            if value in seen:
                return
            seen.add(value)
            self.add(rec, g, variant, value, intent, note)

        add("literal_exact", lit, "correct", "the printed decision literal")
        if LC.is_arabic(lit):
            add("arabic_literal_ws_normalised", ws_normalised(lit.replace("/", " / ")), "correct", "(i2) Arabic literal, spaces normalised")
            add("arabic_literal_ws_extra", lit.replace(" ", "  "), "correct", "(i2) Arabic literal, spaces doubled")
            add("arabic_literal_ws_removed", ws_removed(lit), "correct", "(i2) Arabic literal, spaces removed")
        else:
            if " " in lit:
                add("literal_ws_extra", lit.replace(" ", "  "), "correct", "(i2) literal with doubled spaces")
                add("literal_ws_removed", ws_removed(lit), "correct", "(i2) literal with spaces removed")
            if dash_positions(lit):
                add("literal_dash_variant", replace_dashes(lit, "–"), "correct", "literal with an en dash")
            if lit.lower() != lit:
                add("literal_case_lower", lit.lower(), "correct", "literal, lower case")
        add("application_word", DECISION_WORD[cls], "correct",
            "the application's own decision word for the class (evidence_reader.option_decision / m2_eval4.POSITIVE)")
        for s in SYNONYMS.get(cls, ()):
            add(f"synonym:{s}", s, "correct", f"class synonym for '{cls}' (conventions section 5, (e)/D-001)")
        if resub:
            for s in D1_EXTRAS:
                add(f"d1:{s}", s, "correct", "(d1) resubmission tolerance (Review 35 item 10: including the application's 'rejected')")
        add("code_D_with_legend", CODE_D, "wrong",
            "code D with its legend 'Rejected' = class rejected ((e)/D-001), not the truth class")
        for w in WRONG_CLASS_WORDS.get(cls, ()):
            if resub and w == "rejected":
                continue
            add(f"wrong_class:{w}", w, "wrong", f"an application word of another class than '{cls}'")
        d = self.donor(rec)
        if d:
            add("other_document_value", d["literal"], "wrong",
                f"the decision of {C.row_key(d['pool_id'], d['page'], d['field'])} (class {d['class']})")
        add("no_decision_word:UR", "UR", "no_assertion", "a negative word: asserts no decision")
        self.add(rec, g, "absent", None, "no_assertion", "no fact offered")

    def absent_row(self, rec):
        g = "absent_row"
        f = rec["field"]
        self.add(rec, g, "absent", None, "no_assertion", "no fact offered on an ABSENT row (expected true negative)")
        if f == "decision":
            self.add(rec, g, "no_decision_word:UR", "UR", "no_assertion", "a negative word on an ABSENT decision row")
            self.add(rec, g, "false_approval:approved", "approved", "wrong", "an approval where the page has none")
            self.add(rec, g, "false_approval:ANN", "ANN", "wrong", "an approved-as-noted where the page has none")
        else:
            d = self.donor(rec)
            if d:
                self.add(rec, g, "other_document_value", d["literal"], "wrong",
                         f"the {f} of {C.row_key(d['pool_id'], d['page'], d['field'])} on a page that prints none")
            if f == "identity":
                self.add(rec, g, "project_job_number", self.job_number, "wrong", "a job number on a page that prints no identity")
            if f == "revision":
                self.add(rec, g, "foreign_number:00", "00", "wrong", "a revision on a page that prints none")

    def not_scorable_row(self, rec):
        g = "not_scorable_row"
        f = rec["field"]
        why = "NOT_SCORABLE (" + ", ".join(rec.get("not_scorable_reasons") or []) + "): expected excluded, never read as absent"
        self.add(rec, g, "absent", None, "not_scorable", "no fact; " + why)
        offered = []
        if rec.get("literal") not in (None, ""):
            offered.append(("truth_literal", rec["literal"]))
        for i, c in enumerate(rec.get("candidates") or []):
            offered.append((f"candidate_{i + 1}", c))
        if f == "decision" and rec.get("class") in DECISION_WORD:
            offered.append(("class_application_word", DECISION_WORD[rec["class"]]))
        if f == "identity" and not offered:
            offered.append(("project_job_number", self.job_number))
        seen = set()
        for name, v in offered:
            if v in seen:
                continue
            seen.add(v)
            self.add(rec, g, name, v, "not_scorable", f"{name} offered; " + why)
        if f == "decision":
            wrong = "approved" if rec.get("class") != "approved" else "rejected"
        elif f == "revision":
            wrong = "07"
        else:
            d = self.donor(rec)
            wrong = d["literal"] if d else "ZZ-0000"
        self.add(rec, g, "wrong_value", wrong, "not_scorable", "a value that differs from every literal and candidate; " + why)

    def compilation_page_keyed(self):
        g = "compilation_page_keyed"
        for pid in C.COMPILATIONS_PAGE_KEYED:
            doc = self.truth["documents"][pid]
            assert doc["compilation"], pid
            for f in C.FIELDS:
                rows = self.doc_rows(pid, f)
                for target in rows:
                    for src in rows:
                        if src["page"] == target["page"] or src["truth_kind"] != "value":
                            continue
                        v = src["literal"]
                        if target["truth_kind"] == "value" and self.matches(target, v):
                            continue
                        intent = "not_scorable" if target["truth_kind"] == "not_scorable" else "page_keyed_wrong"
                        self.add(target, g, f"value_of_page_{src['page']}", v, intent,
                                 f"(h) compilation: the value of {C.row_key(pid, src['page'], f)} offered on page {target['page']} "
                                 f"(another document of the same file)", source_row=C.row_key(pid, src["page"], f))

    def cross_page_identity(self):
        g = "cross_page_identity"
        for pid in self.canon:
            doc = self.truth["documents"][pid]
            if doc["compilation"]:
                continue
            rows = self.doc_rows(pid, "identity")
            if len(rows) < 2:
                continue
            for target in rows:
                if target["truth_kind"] == "not_scorable":
                    continue
                done = set()
                for src in rows:
                    if src["page"] == target["page"] or src["truth_kind"] != "value":
                        continue
                    v = src["literal"]
                    if v in done or (target["truth_kind"] == "value" and self.matches(target, v)):
                        continue
                    done.add(v)
                    sub = "drawing_set" if pid in C.DRAWING_SETS else "cover_enclosure_package"
                    self.add(target, g, f"identity_of_page_{src['page']}", v, "cross_page_copy",
                             f"R34-06 / Review 35 item 10 ({sub}): the identity of {C.row_key(pid, src['page'], 'identity')} offered on "
                             f"page {target['page']} of the same non-compilation document", source_row=C.row_key(pid, src["page"], "identity"),
                             cross_page_subgroup=sub)

    def build(self) -> dict:
        excluded = []
        for k in self.keys:
            rec = self.rows[k]
            if rec["pool_id"] not in self.canon:
                excluded.append({"truth_key": k, "truth_kind": rec["truth_kind"],
                                 "why": f"count-once alias of {self.truth['documents'][rec['pool_id']]['canonical_id']}: not in the evaluator "
                                        f"input (converter_r32 exclusion); scored through the canonical id"})
                continue
            kind = rec["truth_kind"]
            if kind == "not_scorable":
                self.not_scorable_row(rec)
            elif kind == "absent":
                self.absent_row(rec)
            else:
                getattr(self, f"{rec['field']}_value")(rec)
        self.compilation_page_keyed()
        self.cross_page_identity()
        order = {k: i for i, k in enumerate(self.keys)}
        groups = ("identity_value", "revision_value", "decision_value", "absent_row", "not_scorable_row", "compilation_page_keyed",
                  "cross_page_identity")
        self.fixtures.sort(key=lambda x: (order[x["truth_key"]], groups.index(x["group"]), x["variant"]))
        for i, fx in enumerate(self.fixtures, 1):
            fx["id"] = f"FX-{i:05d}"
        return {"kind": "SYNTHETIC", "schema": SCHEMA, "statement": C.SYNTHETIC_STATEMENT,
                "reference_set_statement": C.REFERENCE_SET_STATEMENT,
                "inputs": {"truth_r32": {"path": str(C.FROZEN["truth_r32"][0]).replace("\\", "/"), "sha256": C.FROZEN["truth_r32"][1]},
                           "labels_eval_input": {"path": str(C.FROZEN["labels_eval_input"][0]).replace("\\", "/"),
                                                 "sha256": C.FROZEN["labels_eval_input"][1]}},
                "harness_modules": dict(sorted(C.HARNESS_MODULES.items())),
                "harness_fact_state": "accepted (an automatic acceptance; 'validated' gives the same harness verdicts)",
                "coverage": coverage(self), "excluded_rows": excluded, "fixtures": self.fixtures}


def coverage(g: Gen) -> dict:
    canon_rows = [k for k in g.keys if g.rows[k]["pool_id"] in g.canon]
    by_row = collections.Counter(fx["truth_key"] for fx in g.fixtures)
    by_kind = collections.Counter(g.rows[k]["truth_kind"] for k in canon_rows)
    return {"truth_rows_total": len(g.keys), "canonical_rows": len(canon_rows), "alias_rows_excluded": len(g.keys) - len(canon_rows),
            "canonical_rows_by_kind": dict(sorted(by_kind.items())),
            "canonical_rows_without_fixture": [k for k in canon_rows if not by_row.get(k)],
            "fixtures": len(g.fixtures),
            "fixtures_by_group": dict(sorted(collections.Counter(fx["group"] for fx in g.fixtures).items())),
            "fixtures_by_field": dict(sorted(collections.Counter(fx["field"] for fx in g.fixtures).items())),
            "fixtures_by_intent": dict(sorted(collections.Counter(fx["intent"] for fx in g.fixtures).items())),
            "wrong_value_controls": sum(1 for fx in g.fixtures if fx["intent"] in ("wrong", "page_keyed_wrong")),
            "illegible_rows": sum(1 for k in canon_rows if g.rows[k]["state"] == "illegible"),
            "unsupported_rows": sum(1 for k in canon_rows if g.rows[k]["state"] == "unsupported")}


def build() -> dict:
    truth = C.load_json("truth_r32")
    ein = C.load_json("labels_eval_input")
    return Gen(truth, ein).build()


def main(argv) -> int:
    out = pathlib.Path(argv[1])
    assert out.is_absolute(), out
    data = build()
    sha = C.write_json(data, out)
    cov = data["coverage"]
    print({"out": str(out).replace("\\", "/"), "sha256": sha, "fixtures": cov["fixtures"], "by_group": cov["fixtures_by_group"],
           "rows_without_fixture": cov["canonical_rows_without_fixture"]})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
