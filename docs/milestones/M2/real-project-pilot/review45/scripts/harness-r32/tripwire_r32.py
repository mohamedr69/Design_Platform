"""ORCH-05.1 (Review 33 C-5): the per-field critical tripwire and the fact extraction of the r32 lane scorer.

facts_from_row(EV, row, ai_context, doc_key): the emitted facts of one application row, by the FROZEN evaluator .10
emission functions (scripts.m2_eval6 record_groups / observation_groups / ai_groups of C:/t/iso/cand-r30n, imported
read-only), flattened to {"page", "field", "value", "state", "reader", "layer"}; only the three fields.
tripwire(truth, pool_id, facts, source_sha256=None): lane_judge_r32 over the document -> {"resolved": [...],
"unresolved": [...]}: a critical acceptance on RESOLVED truth is attributed to (pool id, page, field) and stops B
(INVALID) or C (RESULT); on unresolved truth (NOT_SCORABLE rows) it is reported only. ORCH-08: the row's source sha256
is passed to the judge (its evidenced cross-page rule CP-R38 needs it), so the tripwire and the scorer judge alike.
CLI (lane B, which runs in the baseline tree and cannot import the candidate's scripts in-process):
  tripwire_r32.py <truth json> <rows json {pool id: row}> <out json>   -- AI context none (B's evidence reader is off)
It imports no application module for B (ai_groups is not called without an AI context), makes no model request, and
writes only <out json>."""
from __future__ import annotations

import importlib
import json
import pathlib
import sys

import lane_judge_r32 as J

CAND_BACKEND = "C:/t/iso/cand-r30n/backend"
FIELDS = ("identity", "revision", "decision")


def load_evaluator():
    """scripts.m2_eval6 of the candidate tree, read-only (no bytecode written)."""
    sys.dont_write_bytecode = True
    if CAND_BACKEND not in sys.path:
        sys.path.insert(0, CAND_BACKEND)
    ev = importlib.import_module("scripts.m2_eval6")
    assert pathlib.Path(ev.__file__).resolve().is_relative_to(pathlib.Path(CAND_BACKEND).resolve()), ev.__file__
    return ev


def facts_from_row(EV, row, ai_context=None, doc_key=None) -> list[dict]:
    groups = EV.record_groups(row) + EV.observation_groups(row)
    if ai_context is not None:
        groups += EV.ai_groups(row, ai_context, doc_key)
    out = []
    for g in groups:
        for f in g["facts"]:
            if f.get("field") in FIELDS and f.get("value") not in (None, ""):
                out.append({"page": str(g["page"]), "field": f["field"], "value": f["value"], "state": f["state"],
                            "reader": g.get("reader"), "layer": g.get("layer")})
    return out


def tripwire(truth, pool_id, facts, source_sha256=None) -> dict:
    """ORCH-08: the source sha256 of the row the facts came from is passed to the judge (an evidenced cross-page
    association needs the declared source bytes, page_relations_r38 (S)); without it no cross-page association is made."""
    jd = J.judge_document(truth, pool_id, {"facts": facts, "source_sha256": source_sha256})
    s = J.critical_split(jd)
    return {"pool_id": pool_id, "resolved": s["resolved"], "unresolved": s["unresolved"],
            "fields": {f: {"critical": len(v["critical"]), "unresolved": len(v["unresolved"])} for f, v in jd["fields"].items()}}


def main(argv) -> int:
    """<truth json> <rows json: {pool_id: row}> <out json>: one tripwire result per document, in the given order."""
    truth_path, rows_path, out_path = argv[1], argv[2], argv[3]
    truth = json.loads(pathlib.Path(truth_path).read_text(encoding="utf-8"))
    rows = json.loads(pathlib.Path(rows_path).read_text(encoding="utf-8"))
    EV = load_evaluator()
    res = {}
    for pool_id, row in rows.items():
        facts = facts_from_row(EV, row, None, None)
        res[pool_id] = tripwire(truth, pool_id, facts, (row or {}).get("sha256")) | {"facts": len(facts), "evaluator": EV.EVALUATOR_VERSION}
    pathlib.Path(out_path).write_text(json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
