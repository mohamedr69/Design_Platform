"""ORCH-06 (Review 33 C-6), agent R35EVAL-IMPL: feed the SYNTHETIC fixtures to the frozen evaluator .10 OFFLINE and
compare its verdict with the frozen r32 harness verdict on the same pair.

Usage (cwd inside C:/t/iso/work/r2x/r35; every path absolute; writes only under the work folder):
  run_evaluator_offline_r32.py --fixtures <SYNTHETIC-PREDICTIONS.json> --out <run json> [--limit N] [--normaliser none]

How the evaluator is invoked (format learned from review31/scripts/harness/score_lane.py and review34 score_lane_r32.py /
tripwire_r32.py, read-only): scripts.m2_eval6 of C:/t/iso/cand-r29/backend is imported IN PLACE, read-only (no bytecode
written, the working directory is the work folder), and called exactly as score_lane.py does:
    EV.evaluate(register, page, rows, page["page1_corrections"], ai_context)
with register / page = LABELS-R32-EVAL-INPUT.json (the frozen converter output, 68 canonical documents) and `rows` = ONE
synthetic application row for the fixture's document. The scored layer is `layers.evidence` (what score_lane.py reads).

Two channels per fixture (the two ways a fact reaches evaluator .10 in the r32 lanes):
  register      B-like: one register record in extracted.records (state 'accepted'), ai_context None (B's reader is off)
  ai_validated  C-like: one validated AI evidence observation in an 'ai-evidence-2' envelope bound to the document's staged
                sha256, ai_context {"variant": "EV1", "profile": "default", "policies": [EVIDENCE_POLICY_VERSION]} as
                lane_r32.py builds it (state 'validated')
Each row carries exactly one fact on the fixture's page (no other fact), so the verdict is the verdict of that fact.

Harness verdicts for the same case:
  harness_pair   lane_judge_r32 (literal_compare_r32) on the offered value itself (the fixture's pair), state per channel
  harness_wired  lane_judge_r32 on the facts that tripwire_r32.facts_from_row(EV, row, ai_context) extracts from the same
                 row through evaluator .10's own emission functions -- what score_lane_r32 would actually judge

Safety (no provider, no model, no network): AI_* / provider variables are removed and AI_ENABLED=false; socket connects,
DNS, subprocesses and os.system are blocked; the provider classes and get_provider/set_provider of the candidate's
app.ai.provider are replaced by raising stubs before any evaluation; an audit hook records every file opened for writing
and refuses a write outside the work folder. The counters are written to the run output."""
from __future__ import annotations

import argparse
import collections
import importlib
import json
import os
import pathlib
import socket
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_r35 as C  # noqa: E402

FIELDS = C.FIELDS
POLICY_STATE = {"register": "accepted", "ai_validated": "validated"}
WRITE_ALLOWED = [os.path.normcase(os.path.abspath(str(C.WORK)))]
PROTECTED = [os.path.normcase(os.path.abspath(str(p))) for p in (
    C.CANDIDATE, C.PILOT, C.MR, "C:/t/r2x", "C:/t/iso/frozen-r12", "C:/Users/moham/Desktop/dev/dev/ep-platform/backend")]
GUARD = {"blocked": collections.Counter(), "write_opens": collections.Counter(), "refused_writes": [], "violations": [],
         "read_paths": set()}
_PY_PREFIXES = tuple(os.path.normcase(os.path.abspath(p)) for p in {sys.prefix, sys.base_prefix, sys.exec_prefix})


# --- guards -----------------------------------------------------------------------------------------------------------


def _norm(p) -> str | None:
    try:
        if isinstance(p, int):
            return None
        if isinstance(p, bytes):
            p = p.decode("utf-8", "replace")
        return os.path.normcase(os.path.abspath(os.fspath(p)))
    except Exception:
        return None


def _is_write(mode, flags) -> bool:
    if isinstance(mode, str):
        return any(c in mode for c in "wax+")
    if isinstance(flags, int):
        return bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC))
    return False


def _audit(event, args):
    if event == "open":
        path = _norm(args[0]) if args else None
        if path is None:
            return
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else None
        if _is_write(mode, flags):
            if not any(path.startswith(a) for a in WRITE_ALLOWED):
                GUARD["refused_writes"].append(path)
                raise PermissionError(f"ORCH-06 guard: write outside the work folder refused: {path}")
            GUARD["write_opens"][path] += 1
        elif not path.startswith(_PY_PREFIXES):
            GUARD["read_paths"].add(path)
    elif event in ("socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "subprocess.Popen", "os.system", "os.exec",
                   "os.spawn", "os.posix_spawn", "os.startfile", "ctypes.dlopen", "webbrowser.open"):
        if event == "ctypes.dlopen":
            return                          # library loading by imported extension modules; not a network or process path
        GUARD["violations"].append(event)
        raise PermissionError(f"ORCH-06 guard: {event} is blocked")


def _blocker(name):
    def blocked(*a, **k):
        GUARD["blocked"][name] += 1
        raise RuntimeError(f"ORCH-06 guard: {name} is blocked (no network, no subprocess, no provider)")
    return blocked


class _BlockedPopen:
    def __init__(self, *a, **k):
        GUARD["blocked"]["subprocess.Popen"] += 1
        raise RuntimeError("ORCH-06 guard: subprocess.Popen is blocked")


def install_guards() -> dict:
    removed = sorted(k for k in os.environ if k.startswith(("AI_", "ANTHROPIC", "OPENAI", "CLAUDE", "R34_OWNER")))
    for k in removed:
        os.environ.pop(k)
    os.environ["AI_ENABLED"] = "false"
    os.environ["DATABASE_URL"] = "sqlite:///C:/t/iso/work/r2x/r38/parity/r38-side/run/no-database-never-created.db"
    socket.socket.connect = _blocker("socket.connect")
    socket.socket.connect_ex = _blocker("socket.connect_ex")
    socket.create_connection = _blocker("socket.create_connection")
    socket.getaddrinfo = _blocker("socket.getaddrinfo")
    subprocess.Popen = _BlockedPopen
    subprocess.run = _blocker("subprocess.run")
    os.system = _blocker("os.system")
    os.popen = _blocker("os.popen")
    sys.addaudithook(_audit)
    return {"environment_removed": removed, "AI_ENABLED": "false", "DATABASE_URL": os.environ["DATABASE_URL"]}


def load_evaluator():
    """scripts.m2_eval6 of the candidate tree, imported in place and read-only; the provider classes are stubbed."""
    cand = C.check_candidate_modules()
    if str(C.CAND_BACKEND) not in sys.path:
        sys.path.insert(1, str(C.CAND_BACKEND))
    EV = importlib.import_module("scripts.m2_eval6")
    assert pathlib.Path(EV.__file__).resolve() == (C.CAND_BACKEND / "scripts/m2_eval6.py").resolve(), EV.__file__
    assert EV.EVALUATOR_VERSION == "m2-pilot-eval-2026-10-02.10", EV.EVALUATOR_VERSION
    ER = importlib.import_module("app.ai.evidence_reader")
    P = importlib.import_module("app.ai.provider")
    stubbed = []
    for name in ("ClaudeProvider", "OpenAiProvider", "ClaudeCodeProvider", "NullProvider", "RecordingProvider"):
        cls = getattr(P, name, None)
        if cls is not None:
            cls.__init__ = _blocker(f"provider.{name}.__init__")
            stubbed.append(name)
    P.get_provider = _blocker("provider.get_provider")
    P.set_provider = _blocker("provider.set_provider")
    for m in (EV, EV.ev4, EV.v3, ER, P):
        assert pathlib.Path(m.__file__).resolve().is_relative_to(C.CAND_BACKEND.resolve()), m.__file__
    TW = importlib.import_module("tripwire_r32")
    assert pathlib.Path(TW.__file__).resolve().parent == C.HARNESS_DIR.resolve()
    return EV, ER, TW, {"candidate_modules": cand, "provider_classes_stubbed": stubbed,
                        "evaluator_version": EV.EVALUATOR_VERSION, "register_evaluator_version": EV.ev4.EVALUATOR_VERSION,
                        "evidence_policy_version": ER.EVIDENCE_POLICY_VERSION, "reader_version": ER.READER_VERSION}


# --- code locations (verified against the candidate source at run time) -------------------------------------------------

CODE_LOCATIONS = {
    "emission.register_record": ("backend/scripts/m2_eval6.py", (79, 95), "def record_groups"),
    "emission.decision_status_in_POSITIVE": ("backend/scripts/m2_eval6.py", (90, 91), 'if rec.get("status") in ev4.POSITIVE'),
    "constant.POSITIVE": ("backend/scripts/m2_eval4.py", (52, 52), 'POSITIVE = ("approved", "ANN", "rejected")'),
    "emission.ai_groups": ("backend/scripts/m2_eval6.py", (166, 215), "def ai_groups"),
    "emission.ai_envelope_evidence_for": ("backend/scripts/m2_eval6.py", (141, 163), "evidence_reader.evidence_for"),
    "association.associate_group": ("backend/scripts/m2_eval6.py", (245, 277), "def associate_group"),
    "association.cross_page_by_identity": ("backend/scripts/m2_eval6.py", (268, 271), 'return e, "cross_page"'),
    "association.single_component": ("backend/scripts/m2_eval6.py", (272, 276), 'single_component_wrong_identity'),
    "association.negative_page": ("backend/scripts/m2_eval6.py", (325, 330), 'e, how = None, "negative_page"'),
    "association.dependents_on_own_page": ("backend/scripts/m2_eval6.py", (333, 346), 'how_dep = here[0], "own_page_component"'),
    "judge.judge_group": ("backend/scripts/m2_eval6.py", (280, 309), "def judge_group"),
    "compare.identity_same_identity": ("backend/scripts/m2_eval6.py", (238, 239), 'v3.same_identity(truth, value) in ("exact", "suffix")'),
    "compare.revision_norm_rev": ("backend/scripts/m2_eval6.py", (240, 241), "return truth == v3.norm_rev(value)"),
    "compare.decision_word_equality": ("backend/scripts/m2_eval6.py", (242, 242), "return truth == value"),
    "v3.same_identity": ("backend/scripts/m2_pilot_eval.py", (102, 113), "def same_identity"),
    "v3.norm_ref_whitespace_and_case_only": ("backend/scripts/m2_pilot_eval.py", (76, 77), 're.sub(r"\\s+", "", value or "").upper()'),
    "v3.alnum_near": ("backend/scripts/m2_pilot_eval.py", (80, 81), 're.sub(r"[^0-9A-Z]", "", (value or "").upper())'),
    "v3.split_suffix": ("backend/scripts/m2_pilot_eval.py", (96, 99), "def split_suffix"),
    "v3.norm_rev_first_token": ("backend/scripts/m2_pilot_eval.py", (84, 93), 'token = re.split(r"[\\s;]", text.strip().upper(), 1)[0]'),
    "v3.DECISION_WORDS": ("backend/scripts/m2_pilot_eval.py", (44, 46), "DECISION_WORDS = {"),
    "truth.reference_truth": ("backend/scripts/m2_eval4.py", (94, 100), "def reference_truth"),
    "truth.revision_truth": ("backend/scripts/m2_eval4.py", (80, 91), "def revision_truth"),
    "truth.decision_truth": ("backend/scripts/m2_eval4.py", (65, 77), "def decision_truth"),
    "truth.UNSCORABLE": ("backend/scripts/m2_eval4.py", (48, 48), "UNSCORABLE = {"),
    "critical.acceptance_outcomes": ("backend/scripts/m2_eval6.py", (392, 392), "critical = [r for r in judged if r[\"state\"] in ACCEPTANCE"),
    "score_layer.unscored_page": ("backend/scripts/m2_eval6.py", (318, 324), '"unscored_page"'),
}


def verify_code_locations() -> dict:
    out = {}
    for key, (rel, (a, b), expect) in CODE_LOCATIONS.items():
        lines = (C.CANDIDATE / rel).read_text(encoding="utf-8").splitlines()
        seg = "\n".join(lines[a - 1:b])
        ok = expect in seg
        out[key] = {"file": rel, "lines": f"{a}-{b}", "expect": expect, "verified": ok}
        assert ok, f"code location {key} not found at {rel}:{a}-{b}"
    return out


# --- rows ------------------------------------------------------------------------------------------------------------------


def register_row(page, field, value, sha) -> dict:
    rec = {"page": int(page), "reference": None}
    if field == "identity":
        rec["reference"] = value
    elif field == "revision":
        rec["printed_revision"] = value
    else:
        rec["status"] = value
    return {"state": "fresh", "sha256": sha, "extracted": {"records": [rec], "observations": []}}


def ai_row(ER, page, field, value, sha) -> dict:
    policy = ER.EVIDENCE_POLICY_VERSION
    obs = {"field": field, "value": value, "state": "validated", "page": int(page), "component": "own", "role": "own",
           "variant": "EV1", "version": ER.READER_VERSION, "policy": policy}
    entry = {"observations": [obs], "status": ER.COMPLETED, "history": [],
             "provenance": {"attempt": 1, "seq": 1, "policy": policy, "variant": "EV1", "profile": "default", "read_sha256": sha,
                            "version": ER.READER_VERSION}}
    env = {"profile": "default", "variant": "EV1", "read_sha256": sha, "stale": None,
           "pages": {str(int(page)): {"fields": {f"own:{field}": entry}}}}
    ai = {"schema": ER.AI_EVIDENCE_SCHEMA, "envelopes": {"default|EV1": env}, "last_written_key": "default|EV1",
          "attempts": [{"key": "default|EV1", "attempt": 1, "seq": 1, "outcome": ER.COMPLETED}], "superseded": [], "attempt_seq": 1}
    return {"state": "fresh", "sha256": sha, "extracted": {"records": [], "observations": [], "ai_evidence": ai}}


# --- evaluator verdicts ------------------------------------------------------------------------------------------------------

STATE_TO_VERDICT = {"recovered_clean": "correct", "recovered_mixed": "correct_and_wrong", "held_only": "held", "missed": "missed",
                    "tn": "absent_accepted", "unscorable": "excluded", "accepted_on_conflict": "critical_false_acceptance",
                    "conflict_held": "held", "conflict_missing": "missed"}


def evaluator_row_map(entry: dict, pdoc: dict) -> dict:
    """{(page, field): {"verdict", "state", "critical"}} for every labelled row of the document, from layers.evidence."""
    L = entry["layers"]["evidence"]
    comp_page = {i: str(r["page"]) for i, r in enumerate(pdoc["records"])}
    crit = collections.Counter()
    for r in L["critical"]:
        pg = comp_page[r["expected"]] if r.get("expected") is not None else str(r["page"])
        crit[(pg, r["field"])] += 1
    out = {}
    for comp in L["components"]:
        pg = str(comp["page"])
        for f in FIELDS:
            s = comp["fields"][f]
            if s in ("wrong_only", "fp"):
                v = "critical_false_acceptance" if crit[(pg, f)] else "wrong_not_accepted"
            else:
                v = STATE_TO_VERDICT[s]
            out[(pg, f)] = {"verdict": v, "state": s, "critical": crit[(pg, f)]}
    for pg in pdoc["no_record_pages"]:
        pg = str(pg)
        for f in FIELDS:
            fps = [r for r in L["judged"] if str(r["page"]) == pg and r["field"] == f and r["outcome"] == "fp" and r.get("expected") is None]
            if fps:
                v = "critical_false_acceptance" if crit[(pg, f)] else "wrong_not_accepted"
                out[(pg, f)] = {"verdict": v, "state": "fp", "critical": crit[(pg, f)]}
            else:
                out[(pg, f)] = {"verdict": "absent_accepted", "state": "tn", "critical": 0}
    for pg in pdoc["unvalidated_pages"]:
        for f in FIELDS:
            out[(str(pg), f)] = {"verdict": "excluded", "state": "unvalidated_page", "critical": 0}
    return out


def rule_of(EV, field, value, channel, fact: dict | None, row_state: str) -> tuple[str, str, list]:
    """(rule name, detail, code location keys) of the evaluator verdict for the offered fact."""
    v3, ev4 = EV.v3, EV.ev4
    emit = ["emission.register_record"] if channel == "register" else ["emission.ai_groups", "emission.ai_envelope_evidence_for"]
    if value is None:
        return "no_fact_offered", f"row outcome {row_state}", []
    if fact is None:
        if channel == "register" and field == "decision" and value not in ev4.POSITIVE:
            return ("emission:decision_status_not_in_POSITIVE",
                    f"record status {value!r} is not in m2_eval4.POSITIVE {ev4.POSITIVE}: record_groups emits no decision fact; "
                    f"row outcome {row_state}", emit + ["emission.decision_status_in_POSITIVE", "constant.POSITIVE"])
        return "emission:no_fact", f"no judged fact for the offered value; row outcome {row_state}", emit
    how, out, truth = fact["how"], fact["outcome"], fact.get("truth")
    locs = emit + ["association.associate_group", "judge.judge_group"]
    tkey = {"identity": "truth.reference_truth", "revision": "truth.revision_truth", "decision": "truth.decision_truth"}[field]
    if out == "unscored_page":
        return "score_layer:unscored_page", "page is unvalidated or unlabelled", emit + ["score_layer.unscored_page"]
    if how == "negative_page":
        return (f"association:negative_page->{out}", "a no-record page (all three fields ABSENT): every asserted fact is a false positive",
                locs + ["association.negative_page"] + (["critical.acceptance_outcomes"] if out == "fp" else []))
    if out == "unscorable":
        return (f"truth:{field}_unscorable->excluded", "the converter encodes NOT_SCORABLE as 'ambiguous', a member of m2_eval4.UNSCORABLE",
                locs + ["truth.UNSCORABLE", tkey])
    if out in ("fp", "held_on_negative"):
        return (f"truth:{field}_negative->{out}", "the encoded truth is a negative word (absent / UR / n/a): an asserted value is a false positive",
                locs + [tkey] + (["critical.acceptance_outcomes"] if out == "fp" else []))
    assoc = how
    if how in ("cross_page", "target_cross_page"):
        locs = locs + ["association.cross_page_by_identity"]
    if how in ("single_component", "single_component_wrong_identity"):
        locs = locs + ["association.single_component"]
    if field == "identity":
        r = v3.same_identity(truth, value) if truth is not None else "different"
        detail = (f"same_identity(truth {truth!r}, value {value!r}) = {r}: norm_ref {v3.norm_ref(str(truth))!r} vs {v3.norm_ref(str(value))!r}"
                  f"; alnum {v3.alnum(str(truth))!r} vs {v3.alnum(str(value))!r}; split_suffix base {v3.split_suffix(str(truth))[0]!r}")
        cmp = f"same_identity={r}" + ("(near is not accepted)" if r == "near" else "")
        locs += ["compare.identity_same_identity", "v3.same_identity", "v3.norm_ref_whitespace_and_case_only"] + \
            (["v3.alnum_near"] if r in ("near", "different") else []) + (["v3.split_suffix"] if r == "suffix" else []) + [tkey]
    elif field == "revision":
        nv = v3.norm_rev(value)
        cmp = "norm_rev_equal" if truth == nv else "norm_rev_differs"
        detail = f"norm_rev(value {value!r}) = {nv!r} vs truth {truth!r} (revision_truth of the encoded printed_revision)"
        locs += ["compare.revision_norm_rev", "v3.norm_rev_first_token", tkey]
    else:
        cmp = "word_equal" if truth == value else "word_differs"
        detail = f"decision word equality: value {value!r} == truth {truth!r} (decision_truth maps the encoded class word through DECISION_WORDS)"
        locs += ["compare.decision_word_equality", tkey, "v3.DECISION_WORDS"]
    if out in ("wrong", "wrong_unassociated", "accepted_on_conflict"):
        locs.append("critical.acceptance_outcomes")
    seen, ordered = set(), []
    for x in locs:
        if x not in seen:
            seen.add(x)
            ordered.append(x)
    return f"{field}:{assoc}:{cmp}->{out}", detail, ordered


# --- classification ----------------------------------------------------------------------------------------------------------


def classify(truth_kind: str, ev: str, hv: str) -> str:
    """Evaluator row verdict `ev` against harness row verdict `hv` (not_evaluated already resolved to the row outcome)."""
    if truth_kind == "not_scorable":
        if ev == "excluded" and hv == "excluded":
            return "c_not_scorable_excluded"
        if ev == "absent_accepted":
            return "c_violation_read_as_absent"
        return "c_violation_scored"
    if ev == hv:
        return "parity"
    if ev == "critical_false_acceptance" and hv in ("correct", "absent_accepted", "missed", "held", "excluded"):
        return "a_stricter_critical"
    if hv == "correct" and ev in ("missed", "held", "excluded", "wrong_not_accepted"):
        return "a_stricter_recovery"
    if hv == "critical_false_acceptance" and ev == "correct":
        return "b_looser_accepts_wrong"
    if hv == "critical_false_acceptance" and ev in ("missed", "absent_accepted", "held", "excluded"):
        return "b_looser_hides_wrong"
    if hv in ("missed", "absent_accepted", "held") and ev == "correct":
        return "b_looser_credit"
    return f"other:{hv}->{ev}"


def application_reachable(field: str, value) -> bool:
    """Whether the application can emit this value as an automatic acceptance in the r32 lanes: a decision fact is only ever
    one of m2_eval4.POSITIVE (register status) or an evidence_reader.option_decision output (validated AI decision)."""
    if value is None:
        return True
    return not (field == "decision" and value not in C.APPLICATION_DECISION_WORDS)


# --- the run -----------------------------------------------------------------------------------------------------------------


def scoped(REG: dict, PAGE: dict, key: str, scope: str) -> tuple[dict, dict]:
    """The evaluator input for one call: the whole frozen register (scope 'full', as score_lane.py passes it) or only the
    fixture's document (scope 'document'; evaluate() judges every document independently, so the document's entry is the
    same -- checked by the parity tests)."""
    if scope == "full":
        return REG, PAGE
    return ({"documents": [d for d in REG["documents"] if d["doc"] == key]},
            {"documents": {key: PAGE["documents"][key]}, "page1_corrections": PAGE.get("page1_corrections") or []})


def run(fixtures_path: pathlib.Path, out_path: pathlib.Path, limit: int | None = None, scope: str = "full",
        only: set | None = None) -> dict:
    t0 = time.perf_counter()
    guard_info = install_guards()
    LC, J, A = C.import_harness()
    truth = C.load_json("truth_r32")
    ein = C.load_json("labels_eval_input")
    fixtures_sha = C.sha256_file(fixtures_path)
    fx_all = json.loads(fixtures_path.read_text(encoding="utf-8"))
    assert fx_all["kind"] == "SYNTHETIC", "fixtures must be SYNTHETIC"
    EV, ER, TW, ev_info = load_evaluator()
    locations = verify_code_locations()
    REG, PAGE = ein["register"], ein["page"]
    corrections = PAGE.get("page1_corrections")
    ai_ctx = {"variant": "EV1", "profile": "default", "policies": [ER.EVIDENCE_POLICY_VERSION]}
    ctx_of = {"register": None, "ai_validated": ai_ctx}
    baseline_ev, baseline_h = {}, {}
    cases, mismatched_expectations = [], []
    fixtures = [fx for fx in fx_all["fixtures"] if only is None or fx["id"] in only]
    fixtures = fixtures[:limit] if limit else fixtures
    assert scope in ("full", "document"), scope
    for fx in fixtures:
        assert fx["kind"] == "SYNTHETIC" and fx["not_a_model_prediction"] is True
        pid, page, field, value = fx["pool_id"], fx["page"], fx["field"], fx["prediction"]["value"]
        doc = truth["documents"][pid]
        key, sha = doc["doc_key"], doc["staged_sha256"]
        pdoc = PAGE["documents"][key]
        truth_rows = {(r["page"], r["field"]) for r in A.doc_rows(truth, pid)}
        R_, P_ = scoped(REG, PAGE, key, scope)
        if pid not in baseline_ev:
            res0 = EV.evaluate(R_, P_, {}, corrections, ai_context=None)
            e0 = next(d for d in res0["documents"] if d["doc"] == key)
            baseline_ev[pid] = evaluator_row_map(e0, pdoc)
            baseline_h[pid] = C.harness_judge(J, truth, pid, [])
            assert set(baseline_ev[pid]) == truth_rows, (pid, sorted(set(baseline_ev[pid]) ^ truth_rows))
        for channel in ("register", "ai_validated"):
            ctx = ctx_of[channel]
            if value is None:
                rows = {}
            elif channel == "register":
                rows = {key: register_row(page, field, value, sha)}
            else:
                rows = {key: ai_row(ER, page, field, value, sha)}
            res = EV.evaluate(R_, P_, rows, corrections, ai_context=ctx)
            entry = next(d for d in res["documents"] if d["doc"] == key)
            L = entry["layers"]["evidence"]
            emap = evaluator_row_map(entry, pdoc)
            assert set(emap) == truth_rows
            facts_rec = [r for r in L["judged"] if r["field"] == field and str(r["page"]) == str(page)]
            other_judged = [r for r in L["judged"] if r not in facts_rec]
            assert not other_judged, (fx["id"], channel, other_judged)
            fact = facts_rec[0] if facts_rec else None
            assert len(facts_rec) <= 1, (fx["id"], channel, facts_rec)
            target = emap[(page, field)]
            emitted = fact is not None
            ev_verdict = "not_evaluated" if (value is not None and not emitted) else target["verdict"]
            rule, detail, locs = rule_of(EV, field, value, channel, fact, target["state"])
            # harness: on the pair, and as wired (through .10's emission functions)
            pair_facts = [] if value is None else [{"page": page, "field": field, "value": value, "state": POLICY_STATE[channel]}]
            h_pair = C.harness_judge(J, truth, pid, pair_facts)
            wired_facts = TW.facts_from_row(EV, rows.get(key), ctx, key) if rows else []
            h_wired = C.harness_judge(J, truth, pid, wired_facts)
            hp, hw = h_pair[(page, field)], h_wired[(page, field)]
            exp = fx["expected_harness"]["judge"]
            if hp != exp:
                mismatched_expectations.append({"fixture": fx["id"], "channel": channel, "expected": exp, "got": hp})
            side = []
            for rk in sorted(truth_rows, key=lambda x: (int(x[0]), FIELDS.index(x[1]))):
                if rk == (page, field):
                    continue
                e_r, h_r = emap[rk], h_pair[rk]
                changed = e_r != baseline_ev[pid][rk] or h_r != baseline_h[pid][rk]
                if changed or e_r["verdict"] != h_r["verdict"]:
                    tk = truth["rows"][C.row_key(pid, rk[0], rk[1])]["truth_kind"]
                    side.append({"row": C.row_key(pid, rk[0], rk[1]), "truth_kind": tk, "evaluator": e_r["verdict"], "evaluator_state": e_r["state"],
                                 "harness_pair": h_r["verdict"], "harness_outcome": h_r["outcome"], "class": classify(tk, e_r["verdict"], h_r["verdict"])})
            cases.append({
                "case_id": f"{fx['id']}/{channel}", "fixture_id": fx["id"], "channel": channel, "truth_key": fx["truth_key"], "pool_id": pid,
                "page": page, "field": field, "truth_kind": fx["truth_kind"], "group": fx["group"], "variant": fx["variant"],
                "intent": fx["intent"], "value": value, "compilation": fx["compilation"], "drawing_set": fx["drawing_set"],
                "cross_page_subgroup": fx.get("cross_page_subgroup"), "source_row": fx.get("source_row"),
                "application_reachable": application_reachable(field, value),
                "evaluator": {"verdict": ev_verdict, "row_verdict": target["verdict"], "row_state": target["state"], "emitted": emitted,
                              "fact": None if fact is None else {k: fact.get(k) for k in ("how", "outcome", "state", "truth", "near", "association")},
                              "fact_expected_page": (str(pdoc["records"][fact["expected"]]["page"]) if fact and fact.get("expected") is not None else None),
                              "rule": rule, "detail": detail, "code_locations": locs, "ai_evidence_state": entry.get("ai_evidence_state")},
                "harness_pair": hp, "harness_wired": hw | {"facts_from_row": len(wired_facts)},
                "class_vs_pair": classify(fx["truth_kind"], target["verdict"], hp["verdict"]),
                "class_vs_wired": classify(fx["truth_kind"], target["verdict"], hw["verdict"]),
                "side_rows": side})
    db_path = pathlib.Path("C:/t/iso/work/r2x/r38/parity/r38-side/run/no-database-never-created.db")
    out = {"kind": "ORCH-06 offline evaluator .10 run over SYNTHETIC fixtures", "statement": C.SYNTHETIC_STATEMENT,
           "reference_set_statement": C.REFERENCE_SET_STATEMENT,
           "fixtures": {"path": str(fixtures_path).replace("\\", "/"), "sha256": fixtures_sha, "count": len(fixtures),
                        "limit": limit, "only": sorted(only) if only else None},
           "register_scope": scope,
           "inputs": {k: {"path": str(C.FROZEN[k][0]).replace("\\", "/"), "sha256": C.FROZEN[k][1]} for k in ("truth_r32", "labels_eval_input")},
           "evaluator": ev_info | {"invocation": "EV.evaluate(register, page, rows, page['page1_corrections'], ai_context); layers.evidence",
                                   "ai_context_by_channel": ctx_of, "cwd": os.getcwd().replace("\\", "/")},
           "code_locations": locations, "harness_modules": C.check_harness_modules(),
           "guard": {"setup": guard_info, "blocked_calls": dict(GUARD["blocked"]), "violations": list(GUARD["violations"]),
                     "refused_writes": list(GUARD["refused_writes"]),
                     "provider_constructed": sum(v for k, v in GUARD["blocked"].items() if k.startswith("provider.")),
                     "network_or_process_attempts": sum(v for k, v in GUARD["blocked"].items() if not k.startswith("provider.")),
                     "sdk_modules_imported": sorted(m for m in sys.modules if m.split(".")[0] in ("anthropic", "openai", "claude_code_sdk",
                                                                                                   "claude_agent_sdk", "httpx", "requests")),
                     "database_file_created": db_path.exists(),
                     "files_opened_for_reading_outside_python": [
                         {"path": p.replace("\\", "/"), "exists": os.path.exists(p)} for p in sorted(GUARD["read_paths"])],
                     "note_on_reads": "audit 'open' events: an import probes for a cached .pyc that may not exist (exists false); "
                                      "nothing is written there (sys.dont_write_bytecode)"},
           "expected_harness_reproduced": not mismatched_expectations, "expected_harness_mismatches": mismatched_expectations[:50],
           "cases": cases, "seconds": round(time.perf_counter() - t0, 1)}
    sha = C.write_json(out, out_path)
    out["guard"]["write_opens"] = sorted(GUARD["write_opens"])
    return {"out": str(out_path).replace("\\", "/"), "sha256": sha, "cases": len(cases), "seconds": out["seconds"],
            "expected_harness_reproduced": out["expected_harness_reproduced"], "guard": {k: out["guard"][k] for k in (
                "blocked_calls", "violations", "refused_writes", "provider_constructed", "network_or_process_attempts", "sdk_modules_imported",
                "database_file_created")}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--scope", choices=("full", "document"), default="full")
    ap.add_argument("--only", help="comma-separated fixture ids")
    a = ap.parse_args(argv)
    fixtures, out = pathlib.Path(a.fixtures), pathlib.Path(a.out)
    assert fixtures.is_absolute() and out.is_absolute()
    assert os.path.normcase(os.path.abspath(str(out))).startswith(WRITE_ALLOWED[0]), "outputs only under the work folder"
    assert os.path.normcase(os.getcwd()).startswith(WRITE_ALLOWED[0]), "the working directory must be inside the work folder"
    summary = run(fixtures, out, a.limit, a.scope, set(a.only.split(",")) if a.only else None)
    print(json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False))
    return 0 if summary["expected_harness_reproduced"] and not summary["guard"]["violations"] and not summary["guard"]["refused_writes"] else 1


if __name__ == "__main__":
    sys.exit(main())
