"""ORCH-02.1 (R32APPLY-IMPL) step 6: verify the fresh-cohort-r32-reviewed package, then seal it.

Writes evidence/PACKAGE-CHECK.json, then evidence/EVIDENCE-MANIFEST.json LAST (every package file except the
manifest and the check, with sha256 and bytes), then re-hashes the manifest rows. Exit 0 only when all checks pass.
Reads frozen inputs only; opens the AI ledger strictly read-only (mode=ro).
"""
import datetime
import glob
import hashlib
import importlib.util
import json
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed"
PACKET = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32"
REVIEW = ("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/"
          "master-roadmap/reviews/M2-label-review-r32-draft-1")
RESPONSE_MD = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md"
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
FROZEN_TREES = [PACKET, REVIEW, "C:/t/r2x/r32-stage", "C:/t/iso/work/r2x/r32"]
CUTOFF = datetime.datetime(2026, 10, 3, 6, 20, 0, tzinfo=datetime.timezone.utc)
SHA = {
    "draft": "ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334",
    "final": "920a21d63871d1618b36deb623e4121d31f3d52949d9c5617536aab7af9d4c5b",
    "consolidated": "70f94632884af028f31d66f76557807801cf00fcca37251a2ade25c9de3a3ff8",
    "critique": "ad6798dc9aba2b1bd20ec6f4db74fbe353bdad93e01144b3ee1d32ab48387eef",
    "dispositions": "e8828becdad00cec0ce18eec371fc1aeeb246496eda5e57aae71c5388e4d30a7",
    "conventions": "5c09d4d2bc0867b8af93c93cd0e67c362f96bfeed5a0c109361931ce7dd5e570",
    "packet_manifest": "15c4114da23e3989b621fed0e43cf9519f9e82e075b972dc2d01f5583f82d0ed",
    "response_md_before": "6e296c28160b138d140d6c6dd275e1cd41e0a19827b24136b76dbabbf33fa0d4",
}
MANIFEST = "evidence/EVIDENCE-MANIFEST.json"
CHECK = "evidence/PACKAGE-CHECK.json"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def package_files():
    out = []
    for root, dirs, files in os.walk(PKG):
        dirs.sort()
        for n in sorted(files):
            rel = os.path.relpath(os.path.join(root, n), PKG).replace("\\", "/")
            if rel not in (MANIFEST, CHECK):
                out.append(rel)
    return sorted(out)


def main():
    checks = {}
    problems = []

    def check(name, ok, detail=None):
        checks[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            problems.append(name)

    files = package_files()
    hashes = {rel: {"sha256": sha256_file(PKG + "/" + rel), "bytes": os.path.getsize(PKG + "/" + rel)}
              for rel in files}

    # 1 frozen inputs still as frozen
    frozen_paths = {"draft": PACKET + "/labels/R32-LABELS-DRAFT-1.json", "final": REVIEW + "/REVIEWER-RESPONSE.final.json",
                    "consolidated": REVIEW + "/REVIEWER-RESPONSE.json", "critique": REVIEW + "/CRITIQUE.json",
                    "dispositions": REVIEW + "/DISPOSITIONS.json", "conventions": PACKET + "/LABEL-CONVENTIONS-R32.md",
                    "packet_manifest": PACKET + "/evidence/EVIDENCE-MANIFEST.json"}
    got = {k: sha256_file(p) for k, p in frozen_paths.items()}
    check("frozen_inputs_unchanged", all(got[k] == SHA[k] for k in got), got)
    pm = load(frozen_paths["packet_manifest"])
    bad = [rel for rel, meta in pm["files"].items() if sha256_file(PACKET + "/" + rel) != meta["sha256"]]
    check("packet_manifest_110_files_rehashed", len(pm["files"]) == 110 and not bad,
          {"listed": len(pm["files"]), "mismatches": bad})

    # 2 copies
    check("draft_copy_sha256", hashes.get("labels/R32-LABELS-DRAFT-1.json", {}).get("sha256") == SHA["draft"],
          hashes.get("labels/R32-LABELS-DRAFT-1.json"))
    check("final_response_copy_sha256",
          hashes.get("review-r32-draft-1/REVIEWER-RESPONSE.final.json", {}).get("sha256") == SHA["final"],
          hashes.get("review-r32-draft-1/REVIEWER-RESPONSE.final.json"))
    cm = load(PKG + "/review-r32-draft-1/COPY-MANIFEST.json")
    src_files = sorted(os.path.relpath(os.path.join(r, n), REVIEW).replace("\\", "/")
                       for r, _, fs in os.walk(REVIEW) for n in fs)
    rows_bad = [x["path"] for x in cm["files"]
                if not (x["source_sha256"] == x["copy_sha256"] == sha256_file(REVIEW + "/" + x["path"])
                        == hashes["review-r32-draft-1/" + x["path"]]["sha256"])]
    check("review_folder_copy_complete_and_equal",
          sorted(x["path"] for x in cm["files"]) == src_files and not rows_bad,
          {"source_files": len(src_files), "copied": len(cm["files"]), "mismatches": rows_bad})
    pc = load(PKG + "/packet-inputs/COPY-MANIFEST.json")
    rows_bad = [x["path"] for x in pc["files"]
                if not (x["source_sha256"] == x["copy_sha256"] == sha256_file(x["source"])
                        == hashes[x["copy"]]["sha256"])]
    check("packet_input_copies_equal", len(pc["files"]) == 6 and not rows_bad,
          {"copied": [x["path"] for x in pc["files"]], "mismatches": rows_bad})

    # 3 reviewed file binds the hashes and rebuilds identically
    rv_path = PKG + "/labels/R32-LABELS-REVIEWED-1.json"
    rv = load(rv_path)
    ap = rv["applied"]
    bind_ok = (rv["version"] == "r32-labels-reviewed-1" and rv["derived_from"]["draft_sha256"] == SHA["draft"]
               and ap["final_response_sha256"] == SHA["final"] and ap["consolidated_sha256"] == SHA["consolidated"]
               and ap["critique_sha256"] == SHA["critique"] and ap["dispositions_sha256"] == SHA["dispositions"]
               and ap["conventions_sha256"] == SHA["conventions"] and "NOT human-signed" in rv["status"])
    check("reviewed_parses_and_binds_hashes", bind_ok,
          {"version": rv["version"], "derived_from": rv["derived_from"],
           "applied": {k: ap[k] for k in ("final_response_sha256", "consolidated_sha256", "critique_sha256",
                                          "dispositions_sha256", "conventions_sha256")}})
    gen_sha = rv["generator"]["sha256"]
    check("generator_sha256_matches_script_copies",
          gen_sha == sha256_file(HERE + "/apply_rulings_r32.py") == hashes["scripts/apply_rulings_r32.py"]["sha256"],
          rv["generator"])
    A = module("apply_rulings_r32_v", HERE + "/apply_rulings_r32.py")
    meta = {"draft_sha256": SHA["draft"], "final_response_sha256": SHA["final"],
            "consolidated_sha256": SHA["consolidated"], "critique_sha256": SHA["critique"],
            "dispositions_sha256": SHA["dispositions"], "conventions_sha256": SHA["conventions"],
            "generated_at_utc": rv["generated_at_utc"], "generator_script": rv["generator"]["script"],
            "generator_sha256": gen_sha}
    rebuilt = A.build_reviewed(load(PKG + "/labels/R32-LABELS-DRAFT-1.json"),
                               load(PKG + "/review-r32-draft-1/REVIEWER-RESPONSE.final.json"),
                               load(PKG + "/review-r32-draft-1/DISPOSITIONS.json"), meta)
    same = json.dumps(rebuilt, sort_keys=True, ensure_ascii=False) == json.dumps(rv, sort_keys=True, ensure_ascii=False)
    check("reviewed_rebuilds_identically_from_package_copies", same)
    final = load(PKG + "/review-r32-draft-1/REVIEWER-RESPONSE.final.json")
    check("all_rulings_applied_once",
          ap["page_field_rulings_applied"] == len(final["page_field_rulings"]) == 432
          and ap["document_field_rulings_applied"] == len(final["document_field_rulings"]) == 210
          and ap["question_rulings_applied"] == len(final["document_questions"]) == 56,
          {k: ap[k] for k in ("page_field_rulings_applied", "document_field_rulings_applied",
                              "question_rulings_applied")})
    fc = final["counts"]["page_field"]
    sc = ap["page_field_status_counts"]
    check("status_counts_equal_final_response_counts",
          all(sc[f]["accepted"] == fc[f]["accept"] and sc[f]["corrected"] == fc[f]["correct"]
              and sc[f]["rejected"] == fc[f]["reject"] and sc[f]["unresolved"] == fc[f]["unresolved"]
              for f in ("identity", "revision", "decision")), sc)
    check("convention_a_no_uncertain_row_without_note", ap["uncertain_without_association_note"] == [])

    # 4 FIELD-POPULATION equals a recount
    C = module("count_population_r32_v", HERE + "/count_population_r32.py")
    fp = load(PKG + "/FIELD-POPULATION.json")
    recount = C.count_population(rv)
    fp_wo = {k: v for k, v in fp.items() if k != "source"}
    check("field_population_equals_recount",
          json.dumps(fp_wo, sort_keys=True) == json.dumps(recount, sort_keys=True)
          and fp["source"]["reviewed_sha256"] == hashes["labels/R32-LABELS-REVIEWED-1.json"]["sha256"]
          and fp["source"]["final_response_sha256"] == SHA["final"],
          {"gate_counts": recount["gate_counts"], "gate_action": recount["gate_action"],
           "excluded_unresolved": recount["excluded_unresolved"],
           "upper_bound_if_resolved": recount["upper_bound_if_resolved"]})
    check("count_once_aliases_expected",
          fp["count_once_aliases"] == {"F031": "F001", "F052": "F038", "F059": "F046", "F070": "F067"},
          fp["count_once_aliases"])

    # 5 junit
    junit = {}
    for x in sorted(glob.glob(PKG + "/tests/*.xml")):
        root = ET.parse(x).getroot()
        suites = [root] if root.tag == "testsuite" else list(root)
        t = sum(int(s.get("tests", 0)) for s in suites)
        fl = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
        junit[os.path.basename(x)] = {"tests": t, "failures_or_errors": fl}
    check("junit_all_pass", len(junit) == 2 and all(v["failures_or_errors"] == 0 and v["tests"] > 0
                                                    for v in junit.values()), junit)

    # 6 frozen trees not modified after the cutoff (os.stat only; no file is opened)
    late = []
    counted = {}
    for tree in FROZEN_TREES:
        n = 0
        for r, _, fs in os.walk(tree):
            for name in fs:
                p = os.path.join(r, name)
                n += 1
                mt = datetime.datetime.fromtimestamp(os.stat(p).st_mtime, datetime.timezone.utc)
                if mt > CUTOFF:
                    late.append({"path": p.replace("\\", "/"), "mtime_utc": mt.strftime("%Y-%m-%dT%H:%M:%SZ")})
        counted[tree] = n
    check("frozen_trees_not_modified_after_2026-10-03T06:20:00Z", not late and all(counted.values()),
          {"files_statted": counted, "modified_after_cutoff": late})

    # 7 ledger read-only
    con = sqlite3.connect("file:" + LEDGER + "?mode=ro", uri=True)
    try:
        entries = con.execute("select count(*) from entries").fetchone()[0]
        scopes = con.execute("select count(*) from scopes").fetchone()[0]
    finally:
        con.close()
    check("ai_ledger_read_only_483_entries_17_scopes", entries == 483 and scopes == 17,
          {"entries": entries, "scopes": scopes, "opened": "file:" + LEDGER + "?mode=ro (uri=True)"})

    # 8 response ledger untouched before the step-7 append
    check("response_file_unchanged_before_append", sha256_file(RESPONSE_MD) == SHA["response_md_before"],
          sha256_file(RESPONSE_MD))

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = {
        "task": "ORCH-02.1 R32APPLY-IMPL step 6",
        "checked_at_utc": now,
        "package": PKG,
        "checks": checks,
        "problems": problems,
        "ok": not problems,
        "files_checked": len(files),
        "file_hashes": hashes,
        "note": "EVIDENCE-MANIFEST.json is written after this check from the same file hashes and lists every "
                "package file except itself and this check",
    }
    dump(result, PKG + "/" + CHECK)

    manifest = {
        "package": "fresh-cohort-r32-reviewed (r32-labels-reviewed-1 and counted field populations; initial pool "
                   "after owner-delegated independent Claude AI review; NOT human sign-off)",
        "reviewed_labels_sha256": hashes["labels/R32-LABELS-REVIEWED-1.json"]["sha256"],
        "draft_labels_sha256": SHA["draft"],
        "final_response_sha256": SHA["final"],
        "package_check_sha256": sha256_file(PKG + "/" + CHECK),
        "written_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": hashes,
    }
    dump(manifest, PKG + "/" + MANIFEST)
    # re-hash the manifest rows after sealing
    m = load(PKG + "/" + MANIFEST)
    resealed = [rel for rel, meta in m["files"].items() if sha256_file(PKG + "/" + rel) != meta["sha256"]]
    unlisted = [rel for rel in package_files() if rel not in m["files"]]
    print("checks", sum(c["ok"] for c in checks.values()), "/", len(checks), "problems", problems)
    print("manifest", sha256_file(PKG + "/" + MANIFEST), "files", len(m["files"]), "rehash mismatches", resealed,
          "unlisted", unlisted)
    return 0 if (not problems and not resealed and not unlisted) else 1


if __name__ == "__main__":
    sys.exit(main())
