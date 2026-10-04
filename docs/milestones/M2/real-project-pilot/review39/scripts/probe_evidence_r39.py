"""ORCH-08C: the package evidence of the two dynamic probes (no model, no provider: a local fake inside the child).
  drawings_ai_probe_r39.py  switch (DRAWINGS_AI_REVIEW_ENABLED=false and =true) and feed (1(d)), in BOTH trees
  unread_pages_probe_r39.py Verification 39's scenarios A, B, C with the candidate's own reader and budget
Usage: probe_evidence_r39.py <drawings json> <unread json>. Child databases live under C:/t/r2x/r39-sandbox/probe-*;
writes only those and the two output files."""
import datetime
import json
import pathlib
import subprocess
import sys
import uuid

H = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32")
sys.path.insert(0, str(H))
import run_state_r38 as RS  # noqa: E402
import sandbox_ingest_r32 as SI  # noqa: E402

TREES = {"baseline": "C:/t/iso/frozen-r12/backend", "candidate": "C:/t/iso/cand-r29/backend"}


def _root(tag):
    root = pathlib.Path(f"C:/t/r2x/r39-sandbox/probe-{tag}-{uuid.uuid4().hex[:6]}")
    (root / "db").mkdir(parents=True)
    return root


def run(script, args, cwd, env):
    r = subprocess.run([SI.PY, str(H / script), *args], cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{script} failed: {r.stderr[-1500:]}")
    return json.loads(pathlib.Path(args[-1]).read_text(encoding="utf-8"))


def main(dout, uout):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    d = {"taken_utc": now, "statement": "no model request: the child's provider is a local fake; the trees are used read-only", "trees": {}}
    for name, tree in TREES.items():
        d["trees"][name] = {}
        for mode, flag in (("switch", "false"), ("switch", "true"), ("feed", "true")):
            root = _root(f"dai-{name[:4]}")
            env = SI.sandbox_env(root, ai_enabled=True, extra={"DRAWINGS_AI_REVIEW_ENABLED": flag})
            d["trees"][name][f"{mode}-{flag}"] = run("drawings_ai_probe_r39.py", [mode, str(root / "PROBE.json")], tree, env)
    d["summary"] = {name: {"declared_false_switches_off": v["switch-false"]["enabled"]["on"] is False and v["switch-false"]["provider_calls"] == [],
                           "true_goes_live": v["switch-true"]["enabled"]["on"] is True,
                           "feed_provider_asked": v["feed-true"]["provider_calls"], "feed_answer_applied": v["feed-true"]["revision_after"],
                           "measured_unchanged": v["feed-true"]["measured_unchanged"],
                           "project_documents_flushed": v["feed-true"]["project_documents_flushed_during_review"]} for name, v in d["trees"].items()}
    pathlib.Path(dout).write_text(json.dumps(d, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    root = _root("unread")
    env = SI.sandbox_env(root, ai_enabled=False, extra={"AI_EVIDENCE_SCHEDULING": "required_first"})
    u = run("unread_pages_probe_r39.py", [str(root / "PROBE.json")], TREES["candidate"], env)
    u["taken_utc"] = now
    u["derived_unread_pages"] = {k: RS.unread_pages_of_attempt(u[k]["stored_summary"], 4) for k in ("A", "B", "C")}
    pathlib.Path(uout).write_text(json.dumps(u, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(d["summary"], default=str))
    print(json.dumps({k: [(x["page"], x["kind"]) for x in v] for k, v in u["derived_unread_pages"].items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
