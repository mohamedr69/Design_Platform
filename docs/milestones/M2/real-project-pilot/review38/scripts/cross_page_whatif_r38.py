"""ORCH-08 (A-09 point 4; R34-06, R36-09): the cross-page what-if -- the HARNESS SIDE of the ORCH-06 parity re-run on the
frozen SYNTHETIC fixtures with the review36 harness (before) and the r38 harness (after, rule CP-R38), and every verdict
that changes. The evaluator side is not re-run (allowed by the task); its frozen verdicts are quoted from PARITY-MATRIX.json.

Usage:
  cross_page_whatif_r38.py pass <r36|r38> <out json> [nosource]   one side, in its own process (module names collide)
  cross_page_whatif_r38.py compare <r36 json> <r38 json> <r38-nosource json> <out json>
A pass uses the side's COPY of the parity scripts (make_parity_copy_r38.py): its guards (no network, no subprocess,
provider classes stubbed, writes only under the side's work folder), its harness import (hash-checked), its row builders
(register_row / ai_row) and its emission path (tripwire_r32.facts_from_row with evaluator .10's emission functions,
imported read-only). Per fixture (4,805) and channel (register: accepted; ai_validated: validated):
  harness_pair   lane_judge_r32 on the offered value itself, every labelled row of the document
  harness_wired  lane_judge_r32 on the facts .10's emission extracts from the same row
The r38 side gives the judge the document's staged sha256 as the lane document's source (as score_lane_r32 does); the
'nosource' pass shows the fail-closed behaviour without it. Writes only <out json>. No model, no provider, no prediction."""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
ROOT = pathlib.Path("C:/t/iso/work/r2x/r38/parity")
FIXTURES = (PILOT / "evaluator-offline-r32" / "SYNTHETIC-PREDICTIONS.json", "9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774")
MATRIX = (PILOT / "evaluator-offline-r32" / "PARITY-MATRIX.json", "73e189f2d0cfe05e55ba58837e991c008eaaf11fb928c300cf0670ead60aaccc")
H1 = (PILOT / "review36" / "H1-WHATIF-RESULT.json", "19b14ab3b23eb0be818ddb6c131a88bff116abb13ce5b7eac932313f925343aa")
STATE = {"register": "accepted", "ai_validated": "validated"}


def frozen(pair):
    raw = pair[0].read_bytes()
    if hashlib.sha256(raw).hexdigest() != pair[1]:
        raise SystemExit(f"PACKET MISMATCH: {pair[0]}")
    return json.loads(raw.decode("utf-8"))


def _rowmap(m):
    return {f"{k[0]}|{k[1]}": v for k, v in m.items()}


def side_pass(side, out, source_bound=True):
    scripts = ROOT / f"{side}-side" / "scripts"
    sys.path.insert(0, str(scripts))
    import common_r35 as C
    import run_evaluator_offline_r32 as RUNP
    assert pathlib.Path(C.__file__).resolve().parent == scripts.resolve() and pathlib.Path(RUNP.__file__).resolve().parent == scripts.resolve()
    out = pathlib.Path(out)
    assert out.resolve().as_posix().lower().startswith((ROOT / f"{side}-side").resolve().as_posix().lower() + "/")
    guard = RUNP.install_guards()
    LC, J, A = C.import_harness()
    if side == "r38":
        C.SOURCE_BOUND = bool(source_bound)
    truth = C.load_json("truth_r32")
    EV, ER, TW, info = RUNP.load_evaluator()
    fx = frozen(FIXTURES)
    assert fx["kind"] == "SYNTHETIC"
    ai_ctx = {"variant": "EV1", "profile": "default", "policies": [ER.EVIDENCE_POLICY_VERSION]}
    cases = {}
    for f in fx["fixtures"]:
        assert f["not_a_model_prediction"] is True
        pid, page, field, value = f["pool_id"], f["page"], f["field"], f["prediction"]["value"]
        doc = truth["documents"][pid]
        key, sha = doc["doc_key"], doc["staged_sha256"]
        for channel in ("register", "ai_validated"):
            ctx = None if channel == "register" else ai_ctx
            if value is None:
                rows = {}
            elif channel == "register":
                rows = {key: RUNP.register_row(page, field, value, sha)}
            else:
                rows = {key: RUNP.ai_row(ER, page, field, value, sha)}
            pair = [] if value is None else [{"page": page, "field": field, "value": value, "state": STATE[channel]}]
            wired = TW.facts_from_row(EV, rows.get(key), ctx, key) if rows else []
            hp, hw = C.harness_judge(J, truth, pid, pair), C.harness_judge(J, truth, pid, wired)
            cases[f"{f['id']}/{channel}"] = {"pair": _rowmap(hp), "wired": _rowmap(hw), "target": f"{page}|{field}", "facts_from_row": len(wired)}
    res = {"side": side, "source_bound": source_bound if side == "r38" else None, "harness_modules": C.check_harness_modules(),
           "harness_dir": C.HARNESS_DIR.as_posix(), "fixtures_sha256": FIXTURES[1], "truth_sha256": C.FROZEN["truth_r32"][1],
           "evaluator": {k: info[k] for k in ("evaluator_version", "evidence_policy_version", "reader_version")}, "guard_setup": guard,
           "guard": {"violations": list(RUNP.GUARD["violations"]), "refused_writes": list(RUNP.GUARD["refused_writes"]),
                     "provider_constructed": sum(v for k, v in RUNP.GUARD["blocked"].items() if k.startswith("provider.")),
                     "network_or_process_attempts": sum(v for k, v in RUNP.GUARD["blocked"].items() if not k.startswith("provider.")),
                     "sdk_modules_imported": sorted(m for m in sys.modules if m.split(".")[0] in ("anthropic", "openai", "claude_code_sdk",
                                                                                                   "claude_agent_sdk", "httpx", "requests"))},
           "cases": cases}
    text = json.dumps(res, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({"side": side, "source_bound": res["source_bound"], "cases": len(cases), "guard": res["guard"],
                      "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}))


def _v(x):
    return {k: x[k] for k in ("verdict", "outcome", "critical", "cross_page")}


def compare(p36, p38, p38n, out):
    a, b, c = (json.loads(pathlib.Path(p).read_text(encoding="utf-8")) for p in (p36, p38, p38n))
    fx = {f["id"]: f for f in frozen(FIXTURES)["fixtures"]}
    matrix = {m["case_id"]: m for m in frozen(MATRIX)["cases"]}
    h1 = {x["case_id"] for x in frozen(H1)["case_level"]["changed"]}
    # 1. the r36-side copy reproduces the frozen matrix, except exactly the H1 cases review36 changed
    repro = [cid for cid, m in matrix.items() if (_v(a["cases"][cid]["pair"][a["cases"][cid]["target"]]) != _v(m["harness_pair"])
                                                   or _v(a["cases"][cid]["wired"][a["cases"][cid]["target"]]) != _v(m["harness_wired"]))]
    changed, side_changed, nosource = [], [], collections.Counter()
    for cid in sorted(a["cases"]):
        x, y, z = a["cases"][cid], b["cases"][cid], c["cases"][cid]
        t = x["target"]
        f = fx[cid.split("/")[0]]
        m = matrix[cid]
        for path in ("pair", "wired"):
            before, after = _v(x[path][t]), _v(y[path][t])
            if before != after:
                changed.append({"case_id": cid, "path": path, "truth_key": f["truth_key"], "field": f["field"], "group": f["group"], "intent": f["intent"],
                                "variant": f["variant"], "cross_page_subgroup": f.get("cross_page_subgroup"), "source_row": f.get("source_row"),
                                "value": f["prediction"]["value"], "truth_kind": f["truth_kind"], "compilation": f["compilation"],
                                "drawing_set": f["drawing_set"], "in_run_set": m.get("in_run_set"), "application_reachable": m.get("application_reachable"),
                                "before": before, "after": after, "after_without_source_hash": _v(z[path][t]),
                                "relationship": None, "evaluator_10_verdict_frozen": m["evaluator"]["verdict"]})
            for rk in x[path]:
                if rk != t and _v(x[path][rk]) != _v(y[path][rk]):
                    side_changed.append({"case_id": cid, "path": path, "row": rk, "before": _v(x[path][rk]), "after": _v(y[path][rk])})
            if _v(y[path][t]) != _v(z[path][t]):
                nosource[path] += 1
    # the rule's own reason for every changed and every kept association (pure call of the r38 page_relations_r38)
    sys.path.insert(0, "C:/t/iso/work/r2x/r38/harness-r32")
    import page_relations_r38 as REL
    truth = json.loads((PILOT / "review34" / "dry-run" / "TRUTH-R32.json").read_text(encoding="utf-8"))

    def why(fid):
        f = fx[fid]
        d = truth["documents"][f["pool_id"]]
        return REL.cross_page(truth, f["pool_id"], f["page"], f["prediction"]["value"], {"source_sha256": d["staged_sha256"]})
    for ch in changed:
        r = why(ch["case_id"].split("/")[0])
        ch["relationship"], ch["rule_why"], ch["rule_target_page"] = r["relationship"], r["why"], r["target_page"]
    trans = collections.Counter((ch["path"], ch["before"]["verdict"], ch["after"]["verdict"]) for ch in changed)
    by_group = collections.Counter((ch["path"], ch["group"], ch["intent"], ch["cross_page_subgroup"] or "-") for ch in changed)
    still_assoc = sorted({ch["case_id"] for ch in changed if ch["after"]["cross_page"]})
    kept = [cid for cid in a["cases"] if a["cases"][cid]["pair"][a["cases"][cid]["target"]]["cross_page"] and
            b["cases"][cid]["pair"][b["cases"][cid]["target"]]["cross_page"]]
    res = {"kind": "ORCH-08 cross-page what-if (harness side of the ORCH-06 parity re-run; evaluator side not re-run)",
           "rule": "CP-R38 (page_relations_r38, cross-page-r38-2026-10-03.1)",
           "statement": "SYNTHETIC fixtures only; no prediction, no model request; reference set independently AI-reviewed (Claude agents), not human-signed",
           "inputs": {"fixtures": FIXTURES[1], "parity_matrix": MATRIX[1], "h1_whatif": H1[1], "r36_pass": hashlib.sha256(pathlib.Path(p36).read_bytes()).hexdigest(),
                      "r38_pass": hashlib.sha256(pathlib.Path(p38).read_bytes()).hexdigest(), "r38_nosource_pass": hashlib.sha256(pathlib.Path(p38n).read_bytes()).hexdigest()},
           "harness": {"before": a["harness_modules"], "after": b["harness_modules"]},
           "reproduction_of_frozen_matrix_by_the_r36_copy": {"cases": len(matrix), "differing_cases": len(repro), "differing_are_exactly_the_h1_cases": set(repro) == h1,
                                                             "h1_cases": len(h1)},
           "cases": len(a["cases"]), "changed_target_verdicts": len(changed),
           "changed_by_path": dict(collections.Counter(ch["path"] for ch in changed)),
           "transitions": [{"path": k[0], "before": k[1], "after": k[2], "n": v} for k, v in sorted(trans.items())],
           "by_group": [{"path": k[0], "group": k[1], "intent": k[2], "subgroup": k[3], "n": v} for k, v in sorted(by_group.items())],
           "changed_in_run_set": sum(1 for ch in changed if ch["in_run_set"]),
           "associations_kept_with_evidence": {"pair_cases": len(kept), "case_ids": sorted(kept),
                                               "by_relationship": dict(collections.Counter(why(cid.split("/")[0])["relationship"] for cid in kept)),
                                               "fixtures": sorted({cid.split("/")[0] for cid in kept})},
           "changed_fixtures": sorted({ch["case_id"].split("/")[0] for ch in changed}),
           "changed_why": dict(collections.Counter(ch["rule_why"] for ch in changed if ch["path"] == "pair")),
           "side_rows_changed": len(side_changed), "side_rows": side_changed[:200],
           "without_source_hash": {"target_verdicts_differing_from_the_source_bound_pass": dict(nosource),
                                   "note": "fail closed: without the row's source sha256 no cross-page association is made"},
           "guards": {"r36": a["guard"], "r38": b["guard"], "r38_nosource": c["guard"]},
           "changed": changed}
    text = json.dumps(res, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    pathlib.Path(out).write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({k: res[k] for k in ("cases", "changed_target_verdicts", "changed_by_path", "transitions", "changed_in_run_set",
                                          "reproduction_of_frozen_matrix_by_the_r36_copy", "side_rows_changed")}, indent=1))
    return res


if __name__ == "__main__":
    if sys.argv[1] == "pass":
        side_pass(sys.argv[2], sys.argv[3], source_bound=not (len(sys.argv) > 4 and sys.argv[4] == "nosource"))
    else:
        compare(*sys.argv[2:6])
