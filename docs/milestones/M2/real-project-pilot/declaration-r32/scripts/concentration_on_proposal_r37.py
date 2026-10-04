"""ORCH-07 (R37DECL-IMPL): the frozen concentration rule v2 (concentration-r32-2026-10-03.2, concentration_r32.py
fc5052f8...) applied to the STRUCTURE of the frozen run set (RUN-SET-PROPOSAL.json 9058f3d6..., 24 documents).

No prediction exists and none is made: "gain sets" are hypothetical sets of documents on which C would recover a field
that B misses. Part 1 is exact combinatorics over the per-field matched projection (project, contractor, layout key of
each document, from the adapter's truth). Part 2 runs the FROZEN code (concentration_r32.field_concentration) on
synthetic lanes built from the truth itself (r34_scenarios.lane, the same construction Review 34 / 35 used) for a set of
gain sets and compares it with the oracle of Part 1 (more than half of a positive net gain in one project, contractor or
layout key -> NOT ELIGIBLE). Synthetic lanes are not results.

Usage: concentration_on_proposal_r37.py <out json (absolute, new)>
Imports the frozen harness package copy read-only with bytecode writing off, after checking every imported module
against BINDING-MANIFEST-R36 (harness_r36_package)."""
from __future__ import annotations

import collections
import itertools
import json
import math
import pathlib
import random
import sys
import time

sys.dont_write_bytecode = True
import r37common as C  # noqa: E402

MODULES = ("concentration_r32.py", "labels_adapter_r32.py", "lane_judge_r32.py", "literal_compare_r32.py", "inputs_r32.py",
           "r34_scenarios.py", "score_bcr_r32.py")
FIELDS = ("identity", "revision", "decision")
SEED = "orch07-concentration-on-proposal-2026-10-03"


def verify_modules() -> dict:
    man = json.loads(C.BINDING.read_text(encoding="utf-8"))
    bound = man["files"]["harness_r36_package"]
    out = {}
    for m in MODULES:
        p = (C.HARNESS_PACKAGE / m).as_posix()
        want = bound[p]
        got = C.sha256_file(p)
        if got != want:
            raise C.PacketMismatch(f"PACKET MISMATCH: {p} {got} != {want}")
        out[m] = got
    return out


def load_harness():
    if str(C.HARNESS_PACKAGE) not in sys.path:
        sys.path.insert(0, str(C.HARNESS_PACKAGE))
    import concentration_r32 as K  # noqa: E402
    import labels_adapter_r32 as A  # noqa: E402
    import r34_scenarios as SC  # noqa: E402
    return K, A, SC


# ---- part 1: exact combinatorics over the matched projection ------------------------------------------------------------
def oracle(gain_docs, meta) -> str:
    """Pure gains (no losses, no failures): NOT ELIGIBLE iff one project, contractor or layout key holds more than half."""
    n = len(gain_docs)
    if n == 0:
        return "UNDETERMINED"
    for key in ("project", "contractor", "layout_key"):
        c = collections.Counter(meta[d][key] for d in gain_docs)
        if max(c.values()) > n / 2:
            return "NOT ELIGIBLE"
    return "ELIGIBLE"


def structure(field_docs, meta) -> dict:
    cells = collections.Counter((meta[d]["project"], meta[d]["contractor"], meta[d]["layout_key"]) for d in field_docs)
    keys = sorted(cells)
    by_size_total = collections.Counter()
    by_size_eligible = collections.Counter()
    for vec in itertools.product(*[range(cells[k] + 1) for k in keys]):
        s = sum(vec)
        ways = math.prod(math.comb(cells[k], v) for k, v in zip(keys, vec))
        by_size_total[s] += ways
        if s == 0:
            continue
        ok = True
        for i in range(3):
            tot = collections.Counter()
            for k, v in zip(keys, vec):
                tot[k[i]] += v
            if max(tot.values()) > s / 2:
                ok = False
                break
        if ok:
            by_size_eligible[s] += ways
    groups = {}
    for i, name in enumerate(("project", "contractor", "layout_key")):
        c = collections.Counter(k[i] for k in keys for _ in range(cells[k]))
        groups[name] = dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))
    n = len(field_docs)
    min_eligible = min((s for s in by_size_eligible if by_size_eligible[s]), default=None)
    return {"matched_projection": n, "documents": sorted(field_docs, key=lambda x: int(x[1:])), "groups": groups,
            "gain_sets_by_size": {str(s): {"total": by_size_total[s], "eligible": by_size_eligible.get(s, 0),
                                           "eligible_share": round(by_size_eligible.get(s, 0) / by_size_total[s], 4)} for s in range(1, n + 1)},
            "smallest_eligible_net_gain": min_eligible,
            "eligible_reachable": min_eligible is not None,
            "largest_single_group": {name: {"group": next(iter(g)), "documents": next(iter(g.values())),
                                            "gain_confined_to_it_is_never_eligible": True,
                                            "documents_needed_elsewhere_to_dilute_a_full_gain_there": next(iter(g.values()))}
                                     for name, g in groups.items()},
            "never_eligible": [
                "any positive net gain confined to one project (every size 1..n)",
                "any positive net gain confined to one layout key (every size)",
                "a net gain of 1 (one document is 100 % of it)",
                "a net gain of 2 unless the two documents differ in project (= contractor) AND layout key",
                "any gain in which one project, contractor or layout key holds more than half of the net gain"]}


# ---- part 2: the frozen code on synthetic lanes ------------------------------------------------------------------------
def run_code(K, SC, T, run, field, gain_docs) -> str:
    miss = {(p, field) for p in gain_docs}
    B = SC.lane(T, run, "B", miss=miss, own=100)
    Cl = SC.lane(T, run, "C", own=100, inherited=100)
    return K.field_concentration(B, Cl, T, field, docs=set(run))["outcome"]


def cross_check(K, SC, T, run, field_docs, meta, field, rng, *, randoms=120) -> dict:
    sets = [()]
    sets += [(d,) for d in field_docs]
    sets += list(itertools.combinations(field_docs, 2))
    by_project = collections.defaultdict(list)
    for d in field_docs:
        by_project[meta[d]["project"]].append(d)
    for p, ds in by_project.items():
        for r in range(1, len(ds) + 1):
            sets += list(itertools.combinations(ds, r))
    for _ in range(randoms):
        r = rng.randint(3, len(field_docs))
        sets.append(tuple(sorted(rng.sample(field_docs, r))))
    seen, results, mismatches = set(), collections.Counter(), []
    for s in sets:
        key = tuple(sorted(s))
        if key in seen:
            continue
        seen.add(key)
        got = run_code(K, SC, T, run, field, list(key))
        want = oracle(list(key), meta)
        results[(len(key), got)] += 1
        if got != want:
            mismatches.append({"gain_documents": list(key), "code": got, "oracle": want})
    return {"checked": len(seen), "mismatches": mismatches,
            "outcomes_by_size": {f"{size}:{outcome}": n for (size, outcome), n in sorted(results.items())}}


def special_cases(K, SC, T, run, has, meta) -> dict:
    """Named cases on the real structure (synthetic lanes, not results)."""
    out = {}
    dec = has["decision"]
    emaar = [d for d in dec if meta[d]["layout_key"] == "emaar-mirage-document-submittal"]
    others = [d for d in dec if d not in emaar]
    out["decision gain on all 6 EP-27331 / EMAAR documents"] = {"gain": emaar, "outcome": run_code(K, SC, T, run, "decision", emaar)}
    out["decision gain on the 6 EMAAR + 6 other decision documents"] = {"gain": emaar + others[:6], "outcome": run_code(K, SC, T, run, "decision", emaar + others[:6])}
    out["decision gain on the 6 EMAAR + 7 other decision documents"] = {"gain": emaar + others[:7], "outcome": run_code(K, SC, T, run, "decision", emaar + others[:7])}
    out["decision gain on every decision document (16)"] = {"gain": dec, "outcome": run_code(K, SC, T, run, "decision", dec)}
    one_each = []
    for p in sorted({meta[d]["project"] for d in dec}):
        one_each.append(next(d for d in dec if meta[d]["project"] == p))
    out["decision gain one document in each decision project (5)"] = {"gain": one_each, "outcome": run_code(K, SC, T, run, "decision", one_each)}
    # negative-control leg: C accepts a decision on one negative control, with the spread gain above
    negs = [p for p in run if T["documents"][p]["decision_control"] == "negative"]
    miss = {(p, "decision") for p in one_each}
    B = SC.lane(T, run, "B", miss=miss, own=100)
    Cl = SC.lane(T, run, "C", own=100, inherited=100, extra={negs[0]: [{"page": "1", "field": "decision", "value": "approved", "state": "accepted"}]})
    out["spread decision gain (5) plus one false acceptance on a negative control"] = {
        "gain": one_each, "negative_control": negs[0], "outcome": K.field_concentration(B, Cl, T, "decision", docs=set(run))["outcome"]}
    # failure leg: revision gain spread, two losses inside one project
    rev = has["revision"]
    by_p = collections.defaultdict(list)
    for d in rev:
        by_p[meta[d]["project"]].append(d)
    lose = by_p["EP-26687"][:2]
    gain = [by_p[p][0] for p in sorted(by_p) if p != "EP-26687"]          # one revision document in each other project
    B = SC.lane(T, run, "B", miss={(p, "revision") for p in gain}, own=100)
    Cl = SC.lane(T, run, "C", miss={(p, "revision") for p in lose}, own=100, inherited=100)
    r = K.field_concentration(B, Cl, T, "revision", docs=set(run))
    out["revision gain one document in each project but EP-26687, 2 losses inside EP-26687 (failure leg)"] = {
        "gain": gain, "lost": lose, "net_gain": r["net_gain"], "failures": r["failures"], "outcome": r["outcome"], "reasons": r["reasons"]}
    # the same gain without the losses: spread, ELIGIBLE
    out["revision gain one document in each project but EP-26687 (no loss)"] = {"gain": gain, "outcome": run_code(K, SC, T, run, "revision", gain)}
    out["negative decision controls in the run set"] = sorted(negs, key=lambda x: int(x[1:]))
    return out


def main(target):
    t0 = time.time()
    hashes = verify_modules()
    K, A, SC = load_harness()
    T, run = SC.load()
    meta = {p: {"project": T["documents"][p]["project"], "contractor": T["documents"][p]["contractor"], "layout_key": T["documents"][p]["layout_key"],
                "stratum": T["documents"][p]["stratum"]} for p in run}
    has = {f: [p for p in run if A.has_fact(T, p, f) and A.primary(T, p, f)] for f in FIELDS}
    rng = random.Random(SEED)
    out = {"name": "CONCENTRATION-ON-PROPOSAL (ORCH-07)", "rule_version": K.RULE_VERSION, "thresholds": K.THRESHOLDS,
           "harness_modules_sha256": hashes, "run_set_sha256": C.FROZEN["run_set_proposal"][1], "run_set_documents": len(run),
           "contractor_equals_project": all(len({meta[d]["contractor"] for d in run if meta[d]["project"] == p}) == 1 for p in {m["project"] for m in meta.values()})
           and len({m["contractor"] for m in meta.values()}) == len({m["project"] for m in meta.values()}),
           "fields": {}, "cross_check": {}, "special_cases": None,
           "statement": ("hypothetical gain sets over the frozen run-set structure; synthetic lanes made from the truth; no prediction, "
                         "no reader, no model; not results"),
           "reference_set_statement": K.REFERENCE_SET_STATEMENT}
    for f in FIELDS:
        out["fields"][f] = structure(has[f], meta)
        out["cross_check"][f] = cross_check(K, SC, T, run, has[f], meta, f, rng)
    out["special_cases"] = special_cases(K, SC, T, run, has, meta)
    out["seconds"] = round(time.time() - t0, 1)
    out["mismatches_total"] = sum(len(v["mismatches"]) for v in out["cross_check"].values())
    sha = C.write_json_once(target, out)
    print(json.dumps({"written": str(target), "sha256": sha, "mismatches_total": out["mismatches_total"],
                      "checked": {f: v["checked"] for f, v in out["cross_check"].items()},
                      "smallest_eligible": {f: v["smallest_eligible_net_gain"] for f, v in out["fields"].items()},
                      "special": {k: v.get("outcome") if isinstance(v, dict) else v for k, v in out["special_cases"].items()},
                      "seconds": out["seconds"]}, indent=1))


if __name__ == "__main__":
    p = pathlib.Path(sys.argv[1])
    assert p.is_absolute()
    main(p)
