"""ORCH-06 (Review 33 C-6), agent R35EVAL-IMPL: shared paths, frozen hashes, hash-checked loaders and the common verdict
vocabulary of the offline evaluator .10 parity test.

Nothing here writes. Every loader re-hashes the file it reads and raises PacketMismatch ("PACKET MISMATCH") on any
difference. The frozen harness modules are imported in place, read-only (no bytecode is written), after their hashes
are checked. File metadata (EP number, relative path, staged sha256) is used only as a KEY, never as evidence."""
from __future__ import annotations

import hashlib
import importlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
PACKAGE = PILOT / "evaluator-offline-r32"
WORK = pathlib.Path("C:/t/iso/work/r2x/r38/parity/r36-side")
REVIEW34 = PILOT / "review34"
HARNESS_DIR = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32")
CANDIDATE = pathlib.Path("C:/t/iso/cand-r29")
CAND_BACKEND = CANDIDATE / "backend"
CANDIDATE_HEAD = "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"
AI_LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
RESPONSE_LEDGER = PILOT.parent / "M2-REVIEW-RESPONSE.md"
TASK_START_UTC = "2026-10-03T13:46:07Z"
FROZEN_CUTOFF_UTC = "2026-10-03T13:50:00Z"

REFERENCE_SET_STATEMENT = "reference set independently AI-reviewed (Claude agents), not human-signed"
SYNTHETIC_STATEMENT = ("SYNTHETIC: every prediction value here is built from the r32 truth strings by a fixed rule. None is a "
                       "prediction of any model or of the application; no cohort document, page image, prediction or arm output "
                       "was read; no provider or model request was made.")

FROZEN = {
    "review34_manifest": (REVIEW34 / "evidence/EVIDENCE-MANIFEST.json",
                          "64d5ba0dda43fc86736eb56558a8eaa2e083231e28c4efd52eceb06abe5d7a86"),
    "labels_eval_input": (REVIEW34 / "LABELS-R32-EVAL-INPUT.json",
                          "4b2c73d59ab852fa45eb46ff58f0ee13242c2ccac4db0221f4b1b607edede5cc"),
    "truth_r32": (REVIEW34 / "dry-run/TRUTH-R32.json", "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064"),
    "converter_reconciliation": (REVIEW34 / "CONVERTER-RECONCILIATION.json",
                                 "e350d2fe78d6062cf59328d1caedfca8f8a72210d2d043c5c37068033b2624f3"),
    "reference_set_reviewed_2": (PILOT / "fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json",
                                 "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6"),
    "label_conventions_r32": (PILOT / "fresh-cohort-r32/LABEL-CONVENTIONS-R32.md",
                              "5c09d4d2bc0867b8af93c93cd0e67c362f96bfeed5a0c109361931ce7dd5e570"),
    "review33": (MR / "reviews/M2-review-33/INDEPENDENT-REVIEW.md",
                 "8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804"),
    "review34": (MR / "reviews/M2-review-34/INDEPENDENT-REVIEW.md",
                 "75061210ff7af6b3619d86563af308caf65d706b4b5dc760288899524bbc8f47"),
    "review35": (MR / "reviews/M2-review-35/INDEPENDENT-REVIEW.md",
                 "f4f668ac240cfdde229febe03f7a6a1b28a1120ab50c6b8ed04264ed2987fe31"),
}
HARNESS_MODULES = {
    "literal_compare_r32": "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09",
    "lane_judge_r32": "a0b6b7c83262ddb2d1337d5ed17296a5aa6fa26cc6ebbee18afcb3cf48f0ca45",
    "labels_adapter_r32": "ff9d2e6b9311bd9ceaaab76f1d3237c1129f8d6c1a70d56d831e11d0e02501ab",
    "tripwire_r32": "42dc6226700852f84762bdd7759bb7592de72778fe92aaad7f7993db291f14d0",
    "converter_r32": "4095a4967a7e7caa992feec4901e06c1836d263f62ab1ba884db8355c30f9704",
    "score_lane_r32": "c25f4d8994631b0fe5b52c1eb4d5bb0f7227f15a4b26c671e72e9c7e31c3c915",
}
EVALUATOR_SHA256 = "268d86231260392dc5592a6937803b8fcd15a41e9590b442f3f0a70dc57b4b4f"
# every candidate module evaluator .10 imports on the paths this test exercises (read-only, in place)
CANDIDATE_MODULES = {
    "backend/scripts/m2_eval6.py": EVALUATOR_SHA256,
    "backend/scripts/m2_eval4.py": "65f3e096dd8ec93be38f50db445eeb0a9837c1acde605f5569a575f1f31f79b5",
    "backend/scripts/m2_pilot_eval.py": "845584b076a42ad26eb576c23034890851d35d386e558437c06501399950fe97",
    "backend/app/ai/evidence_reader.py": "d74397b374fc91a69ed6b4d2ba4306e5fe89682144b2cf5275c7c4091c7ca07a",
    "backend/app/ai/provider.py": "d465961efb07b7f9df2597b37a228735238af433d950bf7095925e8cc43eb5ba",
    "backend/app/ai/guard.py": "ae25b75f4f16f3eee76667853eb84cf2f22fc6afb85825d26334697138c44631",
    "backend/app/core/config.py": "b4fbc07f5a50e147b3ca0d9ca70c5b52a062f2aab7b56c5ce9e468257e361155",
}

FIELDS = ("identity", "revision", "decision")
DRAWING_SETS = ("F014", "F016", "F038")          # Review 34 R34-06 / Review 35 section 6 item 10
COMPILATIONS_PAGE_KEYED = ("F002", "F035", "F043")
APPLICATION_DECISION_WORDS = ("approved", "ANN", "rejected")   # m2_eval4.POSITIVE; evidence_reader.option_decision outputs


class PacketMismatch(RuntimeError):
    pass


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check(name: str) -> str:
    path, expected = FROZEN[name]
    got = sha256_file(path)
    if got != expected:
        raise PacketMismatch(f"PACKET MISMATCH: {name} {path} sha256 {got} != {expected}")
    return got


def load_json(name: str):
    check(name)
    return json.loads(pathlib.Path(FROZEN[name][0]).read_text(encoding="utf-8"))


def check_harness_modules() -> dict:
    out = {}
    for mod, expected in HARNESS_MODULES.items():
        got = sha256_file(HARNESS_DIR / f"{mod}.py")
        if got != expected:
            raise PacketMismatch(f"PACKET MISMATCH: harness module {mod} sha256 {got} != {expected}")
        out[mod] = got
    return out


def check_candidate_modules() -> dict:
    out = {}
    for rel, expected in CANDIDATE_MODULES.items():
        got = sha256_file(CANDIDATE / rel)
        if got != expected:
            raise PacketMismatch(f"PACKET MISMATCH: candidate module {rel} sha256 {got} != {expected}")
        out[rel] = got
    return out


def import_harness():
    """literal_compare_r32, lane_judge_r32, labels_adapter_r32 of the frozen review34 harness, in place, read-only."""
    check_harness_modules()
    if str(HARNESS_DIR) not in sys.path:
        sys.path.insert(0, str(HARNESS_DIR))
    LC = importlib.import_module("literal_compare_r32")
    J = importlib.import_module("lane_judge_r32")
    A = importlib.import_module("labels_adapter_r32")
    for m in (LC, J, A):
        assert pathlib.Path(m.__file__).resolve().parent == HARNESS_DIR.resolve(), m.__file__
    return LC, J, A


def write_json(obj, path) -> str:
    path = pathlib.Path(path)
    assert path.is_absolute(), path
    text = json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return sha256_text(text)


# --- the common verdict vocabulary ----------------------------------------------------------------------------------
# A verdict is about ONE truth row (pool id, page, field) after one synthetic fact was offered.
#   correct                     value row recovered cleanly (the offered value is accepted as this row's value)
#   correct_and_wrong           value row recovered and also contradicted (mixed)
#   critical_false_acceptance   an automatic acceptance (accepted / validated) judged wrong, or a false positive on an
#                               ABSENT row: a critical on resolved truth (fires the per-field tripwire)
#   wrong_not_accepted          wrong but not an automatic acceptance (observed state; not used by the two channels here)
#   held                        the correct value exists only as held evidence
#   missed                      value row, nothing credited to it
#   absent_accepted             ABSENT row, true negative (nothing asserted against it)
#   excluded                    NOT_SCORABLE row (harness) / unscorable or unscored page (evaluator)
#   not_evaluated               evaluator only: the offered value never became a fact (emission filter)
VERDICTS = ("correct", "correct_and_wrong", "critical_false_acceptance", "wrong_not_accepted", "held", "missed",
            "absent_accepted", "excluded", "not_evaluated")
ROW_SEMANTICS = {"not_evaluated": None}      # not_evaluated is resolved to the row outcome for classification


def harness_row_verdict(jr: dict) -> dict:
    """lane_judge_r32.judge_row output -> the common verdict (plus the harness's own outcome words)."""
    outcome = jr.get("outcome")
    crit = len(jr.get("critical") or [])
    if jr["truth_kind"] == "not_scorable":
        verdict = "excluded"
    elif outcome == "recovered_mixed":
        verdict = "correct_and_wrong"
    elif crit:
        verdict = "critical_false_acceptance"
    elif outcome == "recovered_clean":
        verdict = "correct"
    elif outcome in ("wrong_only", "fp"):
        verdict = "wrong_not_accepted"
    elif outcome == "held_only":
        verdict = "held"
    elif outcome == "missed":
        verdict = "missed"
    elif outcome == "tn":
        verdict = "absent_accepted"
    else:
        raise ValueError(f"unknown harness outcome {outcome!r}")
    return {"verdict": verdict, "outcome": outcome, "critical": crit, "cross_page": jr.get("cross_page", 0),
            "unresolved_kinds": sorted({u["kind"] for u in jr.get("unresolved") or []}),
            "match_kinds": jr.get("match_kinds") or []}


def harness_judge(J, truth: dict, pool_id: str, facts: list) -> dict:
    """{(page, field): harness verdict} for every labelled row of the document, given the offered facts."""
    jd = J.judge_document(truth, pool_id, {"facts": facts})
    return {(r["page"], r["field"]): harness_row_verdict(r) for r in jd["rows"]}


def row_key(pool_id: str, page, field: str) -> str:
    return f"{pool_id}|{page}|{field}"
