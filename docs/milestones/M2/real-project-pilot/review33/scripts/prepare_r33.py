"""ORCH-05.1 step 1: from the hash-checked frozen inputs, write the package's derived files (deterministic, no model):
  PILOT/review33/dry-run/TRUTH-R32.json            the adapter output (normalised r32 truth)
  PILOT/review33/LABELS-R32-EVAL-INPUT.json         the converter output (evaluator .10 input, sidecar, reconciliation)
  PILOT/review33/CONVERTER-RECONCILIATION.json      reconciliation totals and the row table
  PILOT/review33/RUN-SET-PROPOSAL.json              the run-set selector's proposal (frozen only by ORCH-07)
Usage: prepare_r33.py"""
import hashlib
import json
import pathlib
import sys

R33 = pathlib.Path("C:/t/iso/work/r2x/r33")
sys.path.insert(0, str(R33 / "harness-r32"))
import converter_r32 as CV  # noqa: E402
import inputs_r32 as I  # noqa: E402
import labels_adapter_r32 as A  # noqa: E402
import run_set_selector_r32 as RS  # noqa: E402

PKG = I.PILOT / "review33"


def write(obj, path):
    text = json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    x = I.load_all()
    truth = A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])
    out = {}
    out["truth"] = write(truth, PKG / "dry-run" / "TRUTH-R32.json")
    ev = CV.convert(truth)
    out["eval_input"] = write(ev, PKG / "LABELS-R32-EVAL-INPUT.json")
    rec = {"totals": CV.reconciliation_totals(ev, truth), "rows": ev["reconciliation"], "sidecar_counts": {k: len(v) for k, v in ev["r32_sidecar"].items()},
           "labels_sha256": I.INPUTS["reviewed2_labels"][1], "converter": "converter_r32.py",
           "rule": "every reviewed-2 page-field row maps to exactly one evaluator truth position (records[page].field, no_record_pages[page] or unvalidated_pages[page]) or to an explicit exclusion"}
    out["reconciliation"] = write(rec, PKG / "CONVERTER-RECONCILIATION.json")
    inputs = {name: I.INPUTS[name][1] for name in ("reviewed2_labels", "renders", "source_manifest", "frozen_selection", "project_verification")}
    inputs["truth_r32_sha256"] = out["truth"]
    prop = RS.build_proposal(truth, inputs=inputs)
    out["run_set"] = write(prop, PKG / "RUN-SET-PROPOSAL.json")
    print(json.dumps({"written": out, "population": {f: len(v) for f, v in A.population(truth).items()},
                      "not_scorable": A.not_scorable_summary(truth)["rows"], "reconciliation": rec["totals"],
                      "run_set": {"count": prop["count"], "by_reason": prop["by_reason"], "shortfalls": prop["shortfalls"]}}, indent=1))


if __name__ == "__main__":
    main()
