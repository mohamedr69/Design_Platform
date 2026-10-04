"""ORCH-06C (R36HARNESS-IMPL): judge EVERY labelled row of each fixture's document with one harness (row-level what-if).

Usage: judge_all_rows_r36.py <old|new> <out json (absolute, under C:/t/iso/work/r2x/r36/)>
  old = the frozen review34 harness, imported in place and read-only (no bytecode is written)
  new = the r36 copy C:/t/iso/work/r2x/r36/harness-r32 (the one changed module)
For each of the 4,805 SYNTHETIC fixtures (frozen, hash-checked) and each automatic-acceptance state (accepted, validated):
lane_judge_r32.judge_document(TRUTH-R32, pool id, {facts: [the fixture's one offered fact]}) -- every row of that document
is recorded as (outcome, criticals, cross-page copies, match kinds, unresolved kinds). This is the population of
Verification 36's what-if (state accepted: 42,804 row judgements). Pure: reads the fixtures, the truth and the harness;
writes only <out json>. No evaluator, no provider, no network."""
import hashlib
import importlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
HARNESS = {"old": PILOT / "review34" / "scripts" / "harness-r32", "new": pathlib.Path("C:/t/iso/work/r2x/r36/harness-r32")}
LC_SHA = {"old": "ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6",
          "new": "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09"}
SAME = {"lane_judge_r32": "a0b6b7c83262ddb2d1337d5ed17296a5aa6fa26cc6ebbee18afcb3cf48f0ca45",
        "labels_adapter_r32": "ff9d2e6b9311bd9ceaaab76f1d3237c1129f8d6c1a70d56d831e11d0e02501ab"}
FIXTURES = (PILOT / "evaluator-offline-r32" / "SYNTHETIC-PREDICTIONS.json", "9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774")
TRUTH = (PILOT / "review34" / "dry-run" / "TRUTH-R32.json", "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064")
STATES = ("accepted", "validated")


def sha(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def frozen(pair):
    raw = pair[0].read_bytes()
    if hashlib.sha256(raw).hexdigest() != pair[1]:
        raise SystemExit(f"PACKET MISMATCH: {pair[0]}")
    return json.loads(raw.decode("utf-8"))


def main(which, out):
    out = pathlib.Path(out)
    assert out.is_absolute() and out.as_posix().startswith("C:/t/iso/work/r2x/r36/"), out
    H = HARNESS[which]
    hashes = {"literal_compare_r32": sha(H / "literal_compare_r32.py"), **{m: sha(H / f"{m}.py") for m in SAME}}
    if hashes["literal_compare_r32"] != LC_SHA[which] or any(hashes[m] != want for m, want in SAME.items()):
        raise SystemExit(f"PACKET MISMATCH: harness {which} {hashes}")
    sys.path.insert(0, str(H))
    LC = importlib.import_module("literal_compare_r32")
    J = importlib.import_module("lane_judge_r32")
    for m in (LC, J, importlib.import_module("labels_adapter_r32")):
        assert pathlib.Path(m.__file__).resolve().parent == H.resolve(), m.__file__
    fx = frozen(FIXTURES)
    truth = frozen(TRUTH)
    assert fx["kind"] == "SYNTHETIC"
    rows = {}
    for f in fx["fixtures"]:
        v = f["prediction"]["value"]
        for state in STATES:
            facts = [] if v is None else [{"page": f["page"], "field": f["field"], "value": v, "state": state}]
            jd = J.judge_document(truth, f["pool_id"], {"facts": facts})
            for r in jd["rows"]:
                rows[f"{f['id']}|{state}|{r['page']}|{r['field']}"] = [r["outcome"], len(r["critical"]), r.get("cross_page", 0),
                                                                     sorted(r.get("match_kinds") or []),
                                                                     sorted({u["kind"] for u in r.get("unresolved") or []}), r["truth_kind"]]
    res = {"kind": f"ORCH-06C row-level judgements ({which} harness)", "harness_dir": H.as_posix(), "harness_hashes": hashes,
           "fixtures_sha256": FIXTURES[1], "truth_sha256": TRUTH[1], "states": list(STATES), "fixtures": len(fx["fixtures"]),
           "rows_judged": {s: sum(1 for k in rows if k.split("|")[1] == s) for s in STATES},
           "row_fields": ["outcome", "criticals", "cross_page", "match_kinds", "unresolved_kinds", "truth_kind"], "rows": rows}
    text = json.dumps(res, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({"which": which, "rows_judged": res["rows_judged"], "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
