"""ORCH-05C: Review 34's scenario structures (S1-S8 with S3a/S3b/S3c) rebuilt over the REAL r32 truth and the REAL run-set
proposal with SYNTHETIC lanes made from the truth itself (correct values copied from it, wrong values invented). No reader,
no model, no prediction: these exercise score_bcr_r32 / concentration_r32 on the real structure and are NOT results.
Used by test_concentration_r32.py, test_score_bcr_r32.py and the dry run (SCORER-SCENARIOS.json)."""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib

import inputs_r32 as I
import labels_adapter_r32 as A

FIELDS = A.FIELDS
RUN_SET_PATH = I.PILOT / "review33" / "RUN-SET-PROPOSAL.json"
RUN_SET_SHA256 = "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"
DEC_VALUE = {"approved": "approved", "approved as noted": "approved as noted", "revise and resubmit": "revise and resubmit", "rejected": "rejected"}


def load():
    """(truth, run-set pool ids): the adapter's truth from the hash-checked frozen inputs; the frozen run-set proposal."""
    x = I.load_all()
    truth = A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])
    raw = pathlib.Path(RUN_SET_PATH).read_bytes()
    if hashlib.sha256(raw).hexdigest() != RUN_SET_SHA256:
        raise I.PacketMismatch(f"PACKET MISMATCH: {RUN_SET_PATH}")
    return truth, [d["pool_id"] for d in json.loads(raw.decode("utf-8"))["documents"]]


def rows_of(T, pid):
    return sorted((r for r in T["rows"].values() if r["pool_id"] == pid), key=lambda r: (int(r["page"]), FIELDS.index(r["field"])))


def lane(T, run, name, miss=(), wrong=(), not_attempted=(), own=0, inherited=0, extra=None):
    """Every value row answered correctly (accepted) except (pid, field) in `miss`; `wrong` adds one accepted wrong value on
    the first scorable row of that field; decision coverage is a completed read / verified absence on scorable rows."""
    docs = {}
    for pid in run:
        facts, cov, done = [], {}, set()
        for r in rows_of(T, pid):
            f, pg = r["field"], r["page"]
            if r["truth_kind"] == "value" and (pid, f) not in miss:
                facts.append({"page": pg, "field": f, "value": r["literal"] if f != "decision" else DEC_VALUE[r["class"]], "state": "accepted"})
            if (pid, f) in wrong and (pid, f) not in done and r["truth_kind"] in ("value", "absent"):
                bad = "WRONG-R34-9" if f != "decision" else ("rejected" if r.get("class") != "revise and resubmit" else "approved")
                facts.append({"page": pg, "field": f, "value": bad, "state": "accepted"})
                done.add((pid, f))
            if f == "decision" and r["truth_kind"] != "not_scorable":
                cov.setdefault(pg, {})["decision"] = "completed_read" if r["truth_kind"] == "value" else "discovery_absent"
        facts += (extra or {}).get(pid, [])
        docs[pid] = {"attempted": pid not in not_attempted, "unsupported": False, "facts": facts, "coverage": cov}
    return {"lane": name, "documents": docs, "requests": {"own_dispatched": own, "inherited_from_b": inherited}, "synthetic": True}


def groups(T, run):
    proj = {pid: T["documents"][pid]["project"] for pid in run}
    has = {f: [p for p in run if T["documents"][p]["fields"][f]["has_fact"]] for f in FIELDS}
    by_proj_dec = collections.defaultdict(list)
    for p in has["decision"]:
        by_proj_dec[proj[p]].append(p)
    return proj, has, dict(by_proj_dec)


def build(T, run) -> dict:
    """{name: (B, C, R, stop_state, note)} -- Review 34's scenario definitions (section 6) on the r34 scorer."""
    proj, has, by_proj_dec = groups(T, run)
    dec, rev, ident = has["decision"], has["revision"], has["identity"]
    small = min(by_proj_dec.items(), key=lambda kv: (len(kv[1]), kv[0]))
    big = by_proj_dec["EP-27331"]
    L = lambda *a, **k: lane(T, run, *a, **k)  # noqa: E731
    sc = {}
    sc["S1 one wrong revision acceptance in C"] = (L("B", own=100), L("C", wrong={(rev[0], "revision")}, inherited=100), None, None,
                                                   f"C accepts one wrong revision on {rev[0]}; everything else identical to B")
    gid = {(p, "identity") for p in ident[:8]}
    sc["S2 identity gain 8 and one wrong decision acceptance"] = (
        L("B", miss=gid, own=100), L("C", wrong={(dec[3], "decision")}, miss={(dec[3], "decision")}, own=20, inherited=100), None, None,
        f"C gains identity on 8 documents; one wrong decision acceptance (no correct one) on {dec[3]}")
    g = {(p, "decision") for p in small[1]}
    sc["S3a decision gain 2 inside one project"] = (L("B", miss=g, own=100), L("C", own=10, inherited=100), None, None,
                                                    f"B misses decision on {small[1]} (all of {small[0]}'s decision documents); C gets them")
    g = {(p, "decision") for p in big[:3]}
    sc["S3b decision gain 3 inside EP-27331"] = (L("B", miss=g, own=100), L("C", own=20, inherited=100), None, None,
                                                 f"B misses decision on {big[:3]} (EP-27331, one contractor, one layout); C gets them")
    g = {(p, "decision") for p in big[:4]}
    sc["S3c decision gain 4 inside EP-27331"] = (L("B", miss=g, own=100), L("C", own=20, inherited=100), None, None,
                                                 f"B misses decision on {big[:4]} (EP-27331); C gets them")
    spread = [v[0] for k, v in sorted(by_proj_dec.items())][:4]
    g = {(p, "decision") for p in spread}
    sc["S3c-spread decision gain 4 over four projects"] = (L("B", miss=g, own=100), L("C", own=20, inherited=100), None, None,
                                                           f"B misses decision on {spread} (one document in each of four projects); C gets them")
    g = {(p, f) for p in small[1] for f in FIELDS if T["documents"][p]["fields"][f]["has_fact"]}
    sc["S3d every field gained on two documents of one project"] = (L("B", miss=g, own=100), L("C", own=16, inherited=100), None, None,
                                                                    f"B misses every field on {small[1]}; C recovers them")
    na = set(dec[:5])
    sc["S4a C does not attempt five decision documents"] = (L("B", own=100), L("C", not_attempted=na, inherited=100), None, None,
                                                            f"C not attempted on {sorted(na)}")
    sc["S4b as S4a with the comparison INCOMPLETE"] = (L("B", own=100), L("C", not_attempted=na, inherited=100), None,
                                                       {"comparison": "INCOMPLETE (C: budget stop)"}, "stop state INCOMPLETE")
    miss3 = {(p, "decision") for p in dec[:3]}
    sc["S5 identity gain 8 and decision recovery below 0.90"] = (L("B", miss=miss3 | gid, own=100), L("C", miss=miss3, own=20, inherited=100),
                                                                 None, None, f"C gains identity on 8 documents; B and C both miss decision on {dec[:3]}")
    lose = [p for p in rev if proj[p] == "EP-26687"][:2]
    gainr = [p for p in rev if proj[p] != "EP-26687"][:6]
    sc["S6 revision gain 6 elsewhere and loss 2 in EP-26687"] = (
        L("B", miss={(p, "revision") for p in gainr}, own=100), L("C", miss={(p, "revision") for p in lose}, own=10, inherited=100), None, None,
        f"C gains revision on {gainr}, loses {lose}")
    negs = [p for p in run if T["documents"][p]["decision_control"] == "negative"]
    fa = {negs[0]: [{"page": "1", "field": "decision", "value": "approved", "state": "accepted"}]}
    sc["S7 decision accepted on a negative control"] = (L("B", own=100), L("C", extra=fa, inherited=100), None, None, f"C accepts 'approved' on {negs[0]} p1")
    sc["S8 decision gain 2 in one project and identity loss 1"] = (L("B", miss={(p, "decision") for p in small[1]}, own=100),
                                                                   L("C", miss={(ident[-1], "identity")}, own=10, inherited=100), None, None,
                                                                   "decision +2 in one project, identity -1 elsewhere")
    return sc


def summarise(res) -> dict:
    rg = res["request_gate"]
    return {"outcome": res["outcome"], "outcome_by_field": res["outcome_by_field"], "comparison_state": res["comparison_state"],
            "candidate_basis": res["candidate"]["basis"],
            "reasons": {f: v["reasons_not_eligible"] for f, v in res["fields"].items()},
            "concentration": {f: {"outcome": v["outcome"], "net_gain": v["net_gain"], "failures": v["failures"], "reasons": v["reasons"],
                                  "largest_project": [v["groupings"]["project"]["largest_gain_group"], v["groupings"]["project"]["largest_gain_share"]],
                                  "largest_layout": [v["groupings"]["layout_key"]["largest_gain_group"], v["groupings"]["layout_key"]["largest_gain_share"]],
                                  "attribution_statement": v["attribution_statement"]} for f, v in res["concentration"]["fields"].items()},
            "request_gate": {"passes": rg["passes"], "net": rg.get("net_correct_facts"), "extra": rg.get("extra_requests"),
                             "ci95": (rg.get("net_gain_per_document") or {}).get("ci95"), "new_false": len(rg.get("new_false_accepts") or [])},
            "paired": {f: {"matched": res["paired"][f]["matched"], "verdict": res["paired"][f]["verdict"],
                           "ci95": (res["paired"][f]["paired_difference"] or {}).get("ci95")} for f in FIELDS},
            "precision_C": {f: res["metrics"]["C"]["fields"][f]["accepted_precision"] for f in FIELDS},
            "recovery_C": {f: res["metrics"]["C"]["fields"][f]["clean_recovery"] for f in FIELDS},
            "default_selected": res["default_selected"]}
