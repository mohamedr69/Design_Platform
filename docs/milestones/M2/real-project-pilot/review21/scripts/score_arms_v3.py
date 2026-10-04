"""Four-arm scorer, version 3: every planned document and every declared page (coverage_v3 with caller-enforced binding
to source hash / profile / variant / arm policy), the accepted evaluator .9 recovery over ALL planned documents, field-
specific matched subsets with IDs (read in both arms of each declared pair), transport state separate, extra emitted
facts outside the declared scope, usage per arm. Functions are importable for the integration tests; `main` scores a
declaration's runs. Usage: score_arms_v3.py --declaration D --declaration-sha SHA --runs ROOT --tags A=..,L1=..,.. --out DIR"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import pathlib
import sqlite3
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import coverage_v3 as cv  # noqa: E402

SCORER_VERSION = "score-arms-2026-09-30.v3"
PAIRS = {"ROI alone": ("L1", "L2"), "X on whole page": ("L1", "L3"), "X on ROI": ("L2", "L4"), "ROI under X": ("L3", "L4")}
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def stop_of(att) -> str:
    """TRANSPORT state only: never coverage."""
    if att is None:
        return "not_attempted"
    bad = sorted({str(c.get("outcome")) for c in att.get("calls") or [] if str(c.get("outcome", "")) != "ok"})
    return "no_transport_stop" if not bad else "transport_stop: " + "; ".join(b[:80] for b in bad)


def arm_coverage(planned: list[dict], rows: dict, ctx: dict, *, max_pages: int) -> dict:
    docs, transport, extras = [], {}, []
    planned_keys = {p["doc"] for p in planned}
    for p in planned:
        row = rows.get(p["doc"])
        att, reason = cv.select_attempt(row, p, ctx)
        docs.append(cv.document_coverage(p, att, max_pages=max_pages, reason=reason))
        transport[p["doc"]] = stop_of(att)
        extras += cv.extra_facts(row, p, ctx, max_pages=max_pages)
    for key, row in rows.items():
        if key not in planned_keys:
            extras += cv.extra_facts(dict(row, doc=key), None, ctx, max_pages=max_pages)
    return {"documents": docs, "summary": cv.summarize(docs), "transport": transport, "extra_facts_outside_scope": extras}


def field_read_in_both(cov_a: dict, cov_b: dict, field: str, planned: list[dict]) -> list[str]:
    by = lambda cov: {d["doc"]: d for d in cov["documents"]}
    a, b = by(cov_a), by(cov_b)
    out = []
    for p in planned:
        da, db = a.get(p["doc"]), b.get(p["doc"])
        if not da or not db or da["state"] == "unsupported_input":
            continue
        # in-scope pages only: pages beyond the reader scope are readable by no arm (they are reported, not compared)
        scope = lambda d: [pc for pn, pc in d["pages"].items() if int(pn) <= d["in_scope_pages"]]
        if all(pc[field] == "completed_read" for pc in scope(da)) and all(pc[field] == "completed_read" for pc in scope(db)):
            out.append(p["doc"])
    return out


def usage_of(path: pathlib.Path) -> dict:
    u = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    fresh = [x for x in u if not x["cache_hit"]]
    by = collections.defaultdict(list)
    for x in fresh:
        by[x["task"]].append(x)
    return {"requests": len(fresh), "cache_hits": sum(1 for x in u if x["cache_hit"]), "outcomes": dict(collections.Counter(x["outcome"] for x in fresh)),
            "input_tokens_total_incl_cached": sum(x["input_tokens"] or 0 for x in fresh), "output_tokens": sum(x["output_tokens"] or 0 for x in fresh),
            "requests_without_token_usage": sum(1 for x in fresh if x["input_tokens"] is None),
            "by_task": {k: {"n": len(v), "latency_ms_median": statistics.median([x["latency_ms"] or 0 for x in v])} for k, v in by.items()}, "cost": "UNKNOWN"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--declaration", required=True); ap.add_argument("--declaration-sha", required=True)
    ap.add_argument("--runs", required=True); ap.add_argument("--tags", required=True); ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    assert sha(args.declaration) == args.declaration_sha, "the declaration changed"
    decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
    RUNS, OUT = pathlib.Path(args.runs), pathlib.Path(args.out)
    TAGS = dict(kv.split("=", 1) for kv in args.tags.split(","))
    OUT.mkdir(parents=True, exist_ok=True)
    HERE = pathlib.Path("C:/t/iso/work/r2x/review21")
    L = decl["labels"]
    for n, h in L["files"].items():
        assert sha(HERE / L["dir"] / n) == h, n
    REG = json.loads((HERE / L["dir"] / L["register"]).read_text(encoding="utf-8"))
    PAGE = json.loads((HERE / L["dir"] / L["page"]).read_text(encoding="utf-8"))
    planned = decl["sources"]["sample"]["documents_planned"]
    max_pages = decl["arms"][decl["doc_arms"][0]]["identities"]["MAX_PAGES_PER_DOCUMENT"]
    os.environ.setdefault("AI_ENABLED", "false")
    os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/score-no-db.db")
    for k in list(os.environ):
        if k.startswith("AI_EVIDENCE_"):
            os.environ.pop(k)
    sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
    os.chdir("C:/t/iso/frozen-r12/backend")
    from scripts import m2_eval5 as EV
    assert sha(EV.__file__) == decl["code"]["evaluator"]["sha256"]
    metrics = {"scorer": SCORER_VERSION, "coverage": cv.COVERAGE_VERSION, "evaluator": EV.EVALUATOR_VERSION, "declaration_sha256": args.declaration_sha,
               "tags": TAGS, "planned": [p["doc"] for p in planned], "max_pages": max_pages, "arms": {}, "coverage": {}}
    covs = {}
    for arm in ["A"] + list(decl["doc_arms"]):
        f = RUNS / TAGS.get(arm, "-") / "out/rows.json"
        if arm not in TAGS or not f.exists():
            metrics["arms"][arm] = {"status": "not run"}
            continue
        rows = json.loads(f.read_text(encoding="utf-8"))
        ctx = ({"variant": None} if arm == "A" else
               {"variant": "EV1", "profile": "default", "policies": [decl["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]]})
        ev = EV.evaluate(REG, PAGE, rows, PAGE.get("page1_corrections"), ai_context=ctx)
        (OUT / f"eval-{arm}.json").write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
        t = ev["totals"]["evidence"]
        entry = {"tag": TAGS[arm], "context": ctx,
                 "recovery_all_planned": {fld: {"recovery": x["recovery_counts"], "precision_numerator": x["precision_counts"].get("correct", 0),
                                                "precision_denominator": x["asserted_distinct"]} for fld, x in t["fields"].items()},
                 "critical": ev["totals"]["evidence"]["critical"], "usage": usage_of(RUNS / TAGS[arm] / "out/usage.json")}
        if arm != "A":
            c = arm_coverage(planned, rows, {"variant": "EV1", "profile": "default", "policy": ctx["policies"][0]}, max_pages=max_pages)
            covs[arm] = c
            metrics["coverage"][arm] = {"summary": c["summary"], "transport": c["transport"], "extra_facts_outside_scope": c["extra_facts_outside_scope"],
                                        "documents": c["documents"]}
            run = json.loads((RUNS / TAGS[arm] / "out/RUN.json").read_text(encoding="utf-8"))
            entry["runner"] = {k: run.get(k) for k in ("runner_state", "not_attempted", "tripwire", "seconds", "business_hashes")}
        metrics["arms"][arm] = entry
    metrics["pairs"] = {}
    for name, (a, b) in PAIRS.items():
        if a in covs and b in covs:
            metrics["pairs"][name] = {"arms": [a, b], "field_read_in_both": {fld: field_read_in_both(covs[a], covs[b], fld, planned) for fld in cv.REQUIRED_FIELDS},
                                      "required_complete_in_both": sorted(set(covs[a]["summary"]["complete_ids"]) & set(covs[b]["summary"]["complete_ids"])),
                                      "required_complete_in_scope_in_both": sorted(set(covs[a]["summary"]["complete_in_scope_ids"]) & set(covs[b]["summary"]["complete_in_scope_ids"]))}
    con = sqlite3.connect(f"file:{(RUNS / TAGS['A'] / 'db/default.db').as_posix()}?mode=ro", uri=True)
    bh = {t: hashlib.sha256(json.dumps([list(r) for r in con.execute(f"select * from {t} order by id")], default=str).encode()).hexdigest()
          for t in ("project_submittals", "project_shop_drawings", "project_actions")}
    bh["project_documents_role"] = hashlib.sha256(json.dumps([list(r) for r in con.execute("select id, role from project_documents order by id")]).encode()).hexdigest()
    con.close()
    metrics["no_business_change"] = {a: (metrics["arms"][a].get("runner") or {}).get("business_hashes") == bh for a in decl["doc_arms"] if "runner" in metrics["arms"].get(a, {})}
    (OUT / "ARMS-METRICS.v3.json").write_text(json.dumps(metrics, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
    for arm, v in metrics["arms"].items():
        if v.get("status"):
            print(arm, v["status"]); continue
        s = metrics["coverage"].get(arm, {}).get("summary", {})
        print(arm, "requests", v["usage"]["requests"], "| complete", s.get("documents_required_complete"), "/", s.get("documents_planned"),
              "| unsupported", s.get("documents_unsupported_input"), "| decision classes", s.get("page_field_classes", {}).get("own:decision"),
              "| extras", len(metrics["coverage"].get(arm, {}).get("extra_facts_outside_scope", [])))
    print("pairs", {k: {f: len(v) for f, v in p["field_read_in_both"].items()} for k, p in metrics["pairs"].items()}, "| business", metrics["no_business_change"])
    return metrics


if __name__ == "__main__":
    main()
