"""R16 saved-output replay: every STORED BOQ verification row (r2x-small-boq-B / -C; no model call), both label
versions (original Review 05 / amended r14.1), with and without the four verified H-06 row positions, through the
actual replay path (replay_core.replay_sheet, contract r16.1). Per row it is compared with the recorded r14 and r15
replays (association, join state, held candidates, outcome, blind correctness); summaries and accounting included.
Writes REPLAY-BOQ-r16.json."""
import collections
import hashlib
import json
import pathlib
import sys

H = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import boq_contract as bc  # noqa: E402
import replay_core as rc  # noqa: E402

W = pathlib.Path("C:/t/iso/work/r2x")
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
KEY = "EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf"
GEO = {6: 980.5, 23: 1795.5, 40: 2861.0, 37: 2718.5}   # verified by byte-identical regeneration of the H-06 crops (Review 14)
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
extraction = [v for k, v in json.load(open(W / "boq/holdout-A-r12-extraction.json", encoding="utf-8")).items() if k.replace("\\", "/") == KEY][0]
emitted = rc.build_emitted(extraction)
LABELS = {"original": (PILOT / "review05/holdout/HOLDOUT-BOQ-LABELS.json", lambda d: d["boq_design_sheets"]["sheets"]),
          "amended": (W / "labels/r14/BOQ-LABELS.amended-r14.1.json", lambda d: d["sheets"])}
PRIOR = {"r14": json.loads((W / "r14/REPLAY-BOQ.json").read_text(encoding="utf-8")),
         "r15": json.loads((W / "r15/REPLAY-BOQ-r15.json").read_text(encoding="utf-8")),
         "r15-geometry": json.loads((W / "r15/REPLAY-BOQ-r15-geometry.json").read_text(encoding="utf-8"))}
out = {"contract": bc.CONTRACT_VERSION, "replay_core": rc.REPLAY_CORE_VERSION, "sheet": KEY, "runs": {}}
for geometry in (False, True):
    for version, (f, pick) in LABELS.items():
        sheet_labels = [x for x in pick(json.loads(f.read_text(encoding="utf-8"))) if x["ep"] == "8430"][0]
        truth = [dict(r, ordinal=i, **({"y": GEO[i]} if geometry and i in GEO else {})) for i, r in enumerate(sheet_labels["rows"]) if r.get("kind") == "line"]
        for tag in ("r2x-small-boq-B", "r2x-small-boq-C"):
            stored_f = pathlib.Path(f"C:/t/r2x/runs/{tag}/out/BOQ.json")
            stored = json.loads(stored_f.read_text(encoding="utf-8"))
            sheet = stored["sheets"][next(iter(stored["sheets"]))]
            res = rc.replay_sheet(sheet["rows"], emitted, truth, bc)
            key = f"{tag}|{version}"
            prior_name = "r15-geometry" if geometry else "r15"
            deltas = {}
            for pname in ("r14", prior_name):
                prior_rows = {x["request_order"]: x for x in PRIOR[pname]["runs"][key]["rows"]}
                d = []
                for x in res["rows"]:
                    y = prior_rows[x["request_order"]]["after"]
                    if (x["truth_ordinal"], x["outcome"], x["blind_right"]) != (y["truth_ordinal"], y["outcome"], y["blind_right"]):
                        d.append({"request_order": x["request_order"], "emitted_id": x["emitted_id"], "prior": y, "r16": {k: x[k] for k in
                                  ("truth_ordinal", "join", "held_candidates", "held_reason", "outcome", "blind_right")}})
                deltas[pname] = d
            out["runs"][f"{key}|geometry={geometry}"] = {
                "stored_run_sha256": sha(stored_f), "labels_sha256": sha(f), "budget_deviation": "OBTAINED WITH THE PER-DOCUMENT BUDGET DEVIATION (R14-01)",
                "outcomes": res["outcomes"], "join_states": dict(collections.Counter(x["join"] for x in res["rows"])),
                "held_rows": {x["emitted_id"]: {"candidates": x["held_candidates"], "reason": x["held_reason"]} for x in res["rows"] if x["join"] == "held"},
                "accounting": res["accounting"], "row_deltas": {k: len(v) for k, v in deltas.items()}, "deltas": deltas, "rows": res["rows"],
                "join_summary": {"pairs": len(res["join"]["pairs"]), "held": res["join"]["held"], "unmatched_emitted": res["join"]["unmatched_emitted"],
                                 "unmatched_truth": res["join"]["unmatched_truth"]}}
p = H / "REPLAY-BOQ-r16.json"
p.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
for k, v in out["runs"].items():
    print(k, "| outcomes", v["outcomes"], "| joins", v["join_states"], "| deltas", v["row_deltas"], "| accounting ok",
          v["accounting"]["emitted"]["complete_and_disjoint"] and v["accounting"]["truth"]["complete"])
