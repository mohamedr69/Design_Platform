"""Review 31 (R31-05): the executable dry run of the B / C / R / P contract over the already-staged four-arm sample.
NO model request, no ledger scope, no new document: B is the frozen final-A run; C, R and P run the frozen candidate
a8aaced through the capture store, with the frozen L3 captures as the inner provider (run_lane.py); scoring is offline
(score_lane.py + score_bcr.py) against the frozen r26.2 labels.

Order, as a live run would follow it:
  1. population gate (R31-02) on the labels -- for this sample it refuses (decision 6 < 12, no extension exists): a live
     run stops HERE. The dry run continues in EXERCISE MODE ONLY so that every later stage is executed and checked;
     nothing after this point is a result.
  2. lane C, then lane R (served from the capture of C), then the probe P;
  3. offline scoring of B, C and R; the stop controller replays the lane events and the post-hoc critical acceptances;
  4. score_bcr.evaluate with the declared equal caps;
  5. transparency: the rows of C and R equal the Review 29 replays (L3-ALL / L3-off) of the same candidate, so the store
     layer changes no answer; the ledger is unchanged;
  6. resume drill: C again over a copy of the capture with one dispatch reset to RESERVED -- nothing is re-sent.
Usage: dry_run.py <stamp>  -> C:/t/iso/work/r2x/r31/dry-run/<stamp>/ (sandboxes under C:/t/r2x/r31-dry/<stamp>/)"""
import hashlib
import json
import pathlib
import sqlite3
import subprocess
import sys

stamp = sys.argv[1]
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import score_bcr as S  # noqa: E402
import stop_rules  # noqa: E402

PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
OUT = pathlib.Path("C:/t/iso/work/r2x/r31/dry-run") / stamp
SBX = pathlib.Path("C:/t/r2x/r31-dry") / stamp
if OUT.exists() or SBX.exists():
    sys.exit("a dry run never reuses its folders")
OUT.mkdir(parents=True)
SBX.mkdir(parents=True)
STORE = SBX / "capture.sqlite"
DECL = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
LD = pathlib.Path(DECL["harness_dir"]) / DECL["labels"]["dir"]
REG = json.loads((LD / DECL["labels"]["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((LD / DECL["labels"]["page"]).read_text(encoding="utf-8"))
UNC = json.loads((LD / DECL["labels"]["uncertainty"]).read_text(encoding="utf-8"))
planned = DECL["sources"]["sample"]["documents_planned"]
ENV = {"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "TEMP": "C:/t/iso/tmp", "TMP": "C:/t/iso/tmp", "SYSTEMROOT": "C:/Windows",
       "PATH": "C:/Windows/system32;C:/Windows"}
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"


def ledger_state():
    con = sqlite3.connect(f"file:{LEDGER}?mode=ro", uri=True)
    st = {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0]}
    con.close()
    return st


def run(args, log):
    with open(OUT / log, "w", encoding="utf-8") as f:
        r = subprocess.run([PY, *map(str, args)], stdout=f, stderr=subprocess.STDOUT, env=ENV, cwd=str(HERE))
    if r.returncode:
        sys.exit(f"{args[0]} failed ({r.returncode}); see {OUT / log}")


# ---- normalised labels: r26.2, independent review = the owner-delegated Codex AI review (never human sign-off) ---------
conf = {x["doc"]: x["confidence"] for x in REG["documents"]}
unc = {u["doc"] for u in UNC["uncertainty"]}
did = {x["doc"]: x["draft_id"] for x in REG["documents"]}
FIELD_OF = {"identity": "reference", "revision": "printed_revision", "decision": "decision"}
NO_DECISION = (None, "", "UR", "n/a")
labels = {"source": f"r26.2 ({DECL['labels']['version']}), manifest {DECL['labels']['manifest_sha256']}",
          "independent_review": "owner-delegated independent AI review by the Codex reviewer (Review 27); NOT human sign-off", "documents": {}}
for p in planned:
    if p["extension"] != ".pdf":
        continue
    recs = PAGE["documents"].get(p["doc"], {}).get("records", [])
    facts = {}
    for pn in range(1, min(p["pages"], 4) + 1):
        r = next((x for x in recs if x["page"] == pn), None)
        facts[str(pn)] = {f: (None if r is None or (f == "decision" and r.get(k) in NO_DECISION) or r.get(k) in (None, "") else r.get(k)) for f, k in FIELD_OF.items()}
    labels["documents"][p["doc"]] = {"draft_id": did.get(p["doc"]), "project": p["doc"].split("/", 1)[0], "stratum": "four-arm sample",
                                     "resolved": conf.get(p["doc"]) == "high" and p["doc"] not in unc, "independent_review": True,
                                     "in_scope_pages": min(p["pages"], 4), "facts": facts}
(OUT / "LABELS-NORMALISED.json").write_text(json.dumps(labels, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

report = {"stamp": stamp, "model_requests": 0, "ledger_before": ledger_state(),
          "B": {"run": "C:/t/r2x/runs/final-A (frozen accepted path, evidence reader off)", "requests_dispatched": 4}}
gate = S.population_gate(labels, extensions_used=len(S.EXTENSIONS))
report["population_gate"] = gate | {"note": "the frozen four-arm sample has no predeclared extension, so the gate is evaluated as with every extension used",
                                    "live_run_would": "stop here without any dispatch" if gate["action"] != "DISPATCH_ELIGIBLE" else "continue"}
report["exercise_mode"] = gate["action"] != "DISPATCH_ELIGIBLE"

# ---- lanes --------------------------------------------------------------------------------------------------------------
run(["run_lane.py", "C", SBX / "C", STORE, OUT], "lane-C.log")
run(["run_lane.py", "R", SBX / "R", STORE, OUT], "lane-R.log")
run(["run_lane.py", "P", SBX / "P-unused", STORE, OUT], "lane-P.log")
lanes = {k: json.loads((OUT / f"LANE-{k}.json").read_text(encoding="utf-8")) for k in "CRP"}
run(["score_lane.py", "B", "C:/t/r2x/runs/final-A/out/rows.json", "none", OUT / "lane-B.score.json"], "score-B.log")
run(["score_lane.py", "C", OUT / "rows-C.json", lanes["C"]["policy_version"], OUT / "lane-C.score.json"], "score-C.log")
run(["score_lane.py", "R", OUT / "rows-R.json", lanes["R"]["policy_version"], OUT / "lane-R.score.json"], "score-R.log")
N = {k: json.loads((OUT / f"lane-{k}.score.json").read_text(encoding="utf-8")) for k in "BCR"}

con = sqlite3.connect(f"file:{STORE.as_posix()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
q = lambda sql, *a: [dict(r) for r in con.execute(sql, a)]  # noqa: E731
store = {"requests_by_lane_state": q("select lane, state, count(*) n from requests group by lane, state order by lane, state"),
         "serves_by_lane_mode": q("select lane, served_lane, mode, count(*) n from serves group by lane, served_lane, mode"),
         "duplicate_bound_keys": q("select bound_key, count(*) n from requests group by bound_key having n > 1"),
         "r_rows_served_to_c": q("select count(*) n from serves where lane = 'C' and served_lane != 'C'")[0]["n"],
         "b_or_c_served_from_p": q("select count(*) n from serves where lane in ('B', 'C') and served_lane = 'P'")[0]["n"],
         "reference_serves_with_other_policy": q("select count(*) n from serves where mode = 'reference_from_capture' and policy != served_policy")[0]["n"],
         "capture_sha256": hashlib.sha256(STORE.read_bytes()).hexdigest()}
con.close()
report["store"] = store
n_req = lambda lane: sum(r["n"] for r in store["requests_by_lane_state"] if r["lane"] == lane)  # noqa: E731
for k, own in (("B", 0), ("C", n_req("C")), ("R", n_req("R"))):
    N[k]["requests"] = {"own_dispatched": own if k != "B" else report["B"]["requests_dispatched"], "inherited_from_b": 0 if k == "B" else report["B"]["requests_dispatched"]}
    N[k]["tokens"] = "replayed usage of the frozen L3 captures (dry run); a live run records provider-reported usage per lane"

# ---- stop controller: lane events in order, then the post-hoc critical acceptances ------------------------------------
ctl = stop_rules.StopController()
for k in "CRP":
    for e in lanes[k]["events"]:
        if e["kind"] != "dry_unrecorded":
            ctl.observe(e["lane"], e["kind"])
for k in "BCR":
    for doc, d in N[k]["documents"].items():
        for c in d["critical"]:
            ctl.observe(k, "critical", resolved=S.primary(labels, doc), detail=f"{did.get(doc)} p{c['page']} {c['field']}")
report["stop_controller"] = ctl.state() | {"note": "post-hoc in the dry run; the live runner evaluates the tripwire after every document"}

caps = {"B": 240, "C": 240}
res = S.evaluate(N["B"], N["C"], N["R"], labels, caps=caps, extensions_used=len(S.EXTENSIONS), seed="m2-r30-bootstrap-2026-10-02", stop_state=ctl.state())
(OUT / "SCORE-BCR.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
report["score_outcome"] = res["outcome"]
report["score_reasons"] = res["reasons_not_eligible"]
report["unequal_caps_check"] = S.request_gate(N["B"], N["C"], labels, {"B": 16, "C": 240}, "x")["reason"]


# ---- transparency against the Review 29 replays of the same candidate -------------------------------------------------
def obs(rows):
    return {k: [(o.get("page"), o.get("field"), o.get("component"), o.get("read"), o.get("support"))
                for o in ((((r.get("extracted") or {}).get("ai_evidence") or {}).get("envelopes") or {}).get("default|EV1", {}).get("observations") or [])]
            for k, r in rows.items()}


tr = {}
for k, ref in (("C", "L3-ALL"), ("R", "L3-off")):
    a = obs(json.loads((OUT / f"rows-{k}.json").read_text(encoding="utf-8")))
    b = obs(json.loads(pathlib.Path(f"C:/t/r2x/r29-replay/{ref}/out/rows.json").read_text(encoding="utf-8")))
    diff = sorted(did.get(d, d) for d in set(a) | set(b) if a.get(d) != b.get(d))
    sr = json.loads(pathlib.Path(f"C:/t/iso/work/r2x/r29/scores/{'ALL' if k == 'C' else 'off'}-L3.e10.json").read_text(encoding="utf-8"))
    tr[k] = {"review29_replay": ref, "documents_with_different_observations": diff,
             "recovery_review29": sr["recovery"], "recovery_dry_run_all_docs": {f: v["recovery"] for f, v in N[k]["totals_evidence"].items()},
             "critical_review29": len(sr["critical"]), "critical_dry_run": N[k]["critical_total"]}
report["transparency"] = tr
report["lanes"] = {k: {x: lanes[k].get(x) for x in ("policy_version", "seconds", "inner", "store_dispatched_to_inner", "lane_stop_state", "live_provider_attempts_blocked", "state_check")}
                   for k in "CR"} | {"P": {x: lanes["P"].get(x) for x in ("seconds", "inner", "lane_stop_state", "live_provider_attempts_blocked")} |
                                     {"probe": {k: v for k, v in lanes["P"]["probe"].items() if k != "rows"},
                                      "agreement": sum(1 for r in lanes["P"]["probe"]["rows"] if r.get("agrees")), "rows": lanes["P"]["probe"]["rows"]}}
# ---- resume drill: C again on a fresh copy of B, against a copy of the capture with one dispatch reset to RESERVED (the
# process died after sending it). Expected: zero dispatches to the inner provider (every request is served by its bound
# fingerprint), the reserved request is served as 'interrupted_charged' and never re-sent, no row is added.
import shutil  # noqa: E402

RESUME = SBX / "capture-resume.sqlite"
shutil.copyfile(STORE, RESUME)
rc = sqlite3.connect(str(RESUME))
victim = rc.execute("select seq, task, page from requests where lane = 'C' and state = 'answered' order by seq limit 1").fetchone()
rc.execute("update requests set state = 'reserved', answer = null, outcome = null, settled_at = null where seq = ?", (victim[0],))
rc.commit()
before = rc.execute("select count(*) from requests").fetchone()[0]
rc.close()
run(["run_lane.py", "C", SBX / "C-resume", RESUME, OUT, "C-resume"], "lane-C-resume.log")
rl = json.loads((OUT / "LANE-C-resume.json").read_text(encoding="utf-8"))
rc = sqlite3.connect(f"file:{RESUME.as_posix()}?mode=ro", uri=True)
after = rc.execute("select count(*) from requests").fetchone()[0]
vstate = rc.execute("select state from requests where seq = ?", (victim[0],)).fetchone()[0]
served = rc.execute("select mode, count(*) from serves where lane = 'C' group by mode").fetchall()
rc.close()
report["resume_drill"] = {"reset_to_reserved": {"seq": victim[0], "task": victim[1], "page": victim[2]}, "dispatched_to_inner": rl["store_dispatched_to_inner"],
                          "rows_before": before, "rows_after": after, "victim_state_after": vstate, "serves": dict(served),
                          "interrupted_served": sum(1 for e in rl["events"] if e.get("error") == "interrupted_charged"),
                          "passes": rl["store_dispatched_to_inner"] == 0 and before == after and vstate == "reserved"}
report["decision_coverage_note"] = ("exercise only: C made %d requests the frozen L3 run never recorded (DR / IG decision and identity reads); "
                                    "the dry run answers them 'unrecorded', so the decision coverage of C is understated here and says nothing "
                                    "about the candidate" % lanes["C"]["inner"]["dry_unrecorded"])
report["ledger_after"] = ledger_state()
assert report["ledger_after"] == report["ledger_before"], "the ledger changed"
(OUT / "DRY-RUN-REPORT.json").write_text(json.dumps(report, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("population_gate", "score_outcome", "transparency", "ledger_after")}, indent=1, default=str)[:6000])
print(json.dumps(store, indent=1, default=str)[:3000])
