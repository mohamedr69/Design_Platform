"""ORCH-04.1 (R32APPLY2-IMPL) step 5: verify the fresh-cohort-r32-reviewed-2 package, then seal it.

Writes evidence/PACKAGE-CHECK.json, then evidence/EVIDENCE-MANIFEST.json LAST (every package file except the manifest
and the check, with sha256 and bytes), then re-hashes the manifest rows. Exit 0 only when every check passes.
Reads frozen inputs only (os.stat for the frozen-tree cutoff check; no image is opened); opens the AI ledger strictly
read-only (file:...?mode=ro, uri=True).
"""
import sys

sys.dont_write_bytecode = True

import datetime  # noqa: E402
import glob  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import sqlite3  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402

WORK = "C:/t/iso/work/r2x/r32c"
PILOT = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot"
PKG = PILOT + "/fresh-cohort-r32-reviewed-2"
SRC = PILOT + "/fresh-cohort-r32-reviewed"
PACKET = PILOT + "/fresh-cohort-r32"
REVIEWS = "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews"
R33 = REVIEWS + "/M2-review-33"
LABEL_REVIEW = REVIEWS + "/M2-label-review-r32-draft-1"
RESPONSE_MD = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md"
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
FROZEN_TREES = [PACKET, SRC, R33, LABEL_REVIEW, "C:/t/r2x/r32-stage", "C:/t/iso/work/r2x/r32", "C:/t/iso/work/r2x/r32b"]
CUTOFF = datetime.datetime(2026, 10, 3, 9, 50, 0, tzinfo=datetime.timezone.utc)
SHA = {
    "reviewed1": "00e53e8253adf86fc5cabbd1659576a2e728f4d0ef20b084f7aaba3157379779",
    "draft": "ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334",
    "review33": "8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804",
    "escalation_rulings_final": "e2fe503d96a3bc08c99ce52862d2017a567f6e2a6677744f43750c5ebc7611a0",
    "dispositions": "ceb8fdcc6cc3e54219ab22686fc663a66c93ca5ed44316255ddf24745018315b",
    "source_manifest": "64c0366737a5567284c6b862e5addbb0091f7bf98066745f081407a8b3fe31c6",
    "packet_manifest": "15c4114da23e3989b621fed0e43cf9519f9e82e075b972dc2d01f5583f82d0ed",
    "renders": "175a3a10ac871540dbbeb87f1ec7d2e68b369186d05a60bf5dd751b18e51e8be",
    "response_md_before": "f0a4ffacba2c7765133475352e939a8149e119f7eb1efef73c2faec77774c65b",
}
FROZEN_PATHS = {
    "reviewed1": SRC + "/labels/R32-LABELS-REVIEWED-1.json",
    "draft": PACKET + "/labels/R32-LABELS-DRAFT-1.json",
    "review33": R33 + "/INDEPENDENT-REVIEW.md",
    "escalation_rulings_final": R33 + "/ESCALATION-RULINGS.final.json",
    "dispositions": R33 + "/DISPOSITIONS.json",
    "source_manifest": SRC + "/evidence/EVIDENCE-MANIFEST.json",
    "packet_manifest": PACKET + "/evidence/EVIDENCE-MANIFEST.json",
    "renders": PACKET + "/RENDERS.json",
}
SCRIPTS = ["check_inputs_r32c.py", "copy_inputs_r32c.py", "apply_review33_r32.py", "count_population_r32c.py",
           "test_apply_review33_r32.py", "test_count_population_r32c.py", "verify_r32c_package.py"]
JUNIT = ["test_apply_review33_r32.xml", "test_count_population_r32c.xml"]
MANIFEST = "evidence/EVIDENCE-MANIFEST.json"
CHECK = "evidence/PACKAGE-CHECK.json"
EXPECTED_ALIASES = {"F031": "F001", "F052": "F038", "F059": "F046", "F070": "F067"}
EXPECTED_COUNTS = {"identity": 57, "revision": 38, "decision": 38}
AMENDMENT_IDS = ["(c)(ii)", "(d1)", "(e)/D-001", "(g)(1)", "(g2)/D-002", "(h)/D-003", "(d2)", "(f)",
                 "D-005 page reading"]
# independent restatement of Review 33 section 4.4 (keys that may differ per row); not imported from the apply script
ALLOWED = {
    ("F069", "pages", "1", "identity"): {"state", "literal", "candidates", "review_status", "open_question",
                                         "review33_ruling"},
    ("F069", "pages", "3", "identity"): {"state", "literal", "candidates", "review_status", "open_question",
                                         "review33_ruling"},
    ("F069", "review", "identity"): {"resolved_for_scoring", "open_question", "review33_ruling"},
    ("F019", "pages", "1", "revision"): {"review_status", "open_question", "review33_ruling"},
    ("F019", "review", "revision"): {"resolved_for_scoring", "carries_fact", "open_question", "review33_ruling"},
    ("F019", "questions", "1"): {"ruling", "open_question", "review33_ruling"},
    ("F019",): {"unresolved_review33_marks"},
}
FIELDS = ("identity", "revision", "decision")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dumps(obj):
    return json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n"


def dump(obj, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(obj))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def listing(root):
    out = []
    for r, dirs, files in os.walk(root):
        dirs.sort()
        for n in sorted(files):
            out.append(os.path.relpath(os.path.join(r, n), root).replace("\\", "/"))
    return sorted(out)


def package_files():
    return [rel for rel in listing(PKG) if rel not in (MANIFEST, CHECK)]


def own_diff(a, b, path=()):
    """Independent leaf diff (dict keys, equal-length lists by index, canonical JSON leaves)."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                yield path + (k,)
            else:
                yield from own_diff(a[k], b[k], path + (k,))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from own_diff(x, y, path + (str(i),))
    elif json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
        yield path


def main():
    checks, problems = {}, []

    def check(name, ok, detail=None):
        checks[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            problems.append(name)

    files = package_files()
    hashes = {rel: {"sha256": sha256_file(PKG + "/" + rel), "bytes": os.path.getsize(PKG + "/" + rel)}
              for rel in files}

    # 1 frozen inputs
    got = {k: sha256_file(p) for k, p in FROZEN_PATHS.items()}
    check("frozen_inputs_unchanged", all(got[k] == SHA[k] for k in got), got)
    sm = load(FROZEN_PATHS["source_manifest"])
    bad = [rel for rel, meta in sm["files"].items() if sha256_file(SRC + "/" + rel) != meta["sha256"]]
    check("source_package_manifest_45_files_rehashed", len(sm["files"]) == 45 and not bad,
          {"listed": len(sm["files"]), "mismatches": bad})
    ihc = load(PKG + "/evidence/INPUT-HASH-CHECK.json")
    check("input_hash_check_match_and_copy_equal",
          ihc["result"] == "MATCH" and hashes["evidence/INPUT-HASH-CHECK.json"]["sha256"]
          == sha256_file(WORK + "/INPUT-HASH-CHECK.json"),
          {"result": ihc["result"], "checked_at_utc": ihc["checked_at_utc"],
           "full_hashes_recorded": ihc["full_hashes_recorded"]})

    # 2 copies unchanged
    lab_ok = (hashes["labels/R32-LABELS-REVIEWED-1.json"]["sha256"] == SHA["reviewed1"] == got["reviewed1"]
              and hashes["labels/R32-LABELS-DRAFT-1.json"]["sha256"] == SHA["draft"] == got["draft"])
    check("label_copies_equal_frozen", lab_ok,
          {k: hashes[k] for k in ("labels/R32-LABELS-REVIEWED-1.json", "labels/R32-LABELS-DRAFT-1.json")})
    cm = load(PKG + "/review-33/COPY-MANIFEST.json")
    src_files = listing(R33)
    rows_bad = [x["path"] for x in cm["files"]
                if not (x["source_sha256"] == x["copy_sha256"] == sha256_file(R33 + "/" + x["path"])
                        == hashes["review-33/" + x["path"]]["sha256"])]
    copy_files = sorted(rel[len("review-33/"):] for rel in files if rel.startswith("review-33/")
                        and rel != "review-33/COPY-MANIFEST.json")
    check("review33_folder_copy_complete_and_equal",
          sorted(x["path"] for x in cm["files"]) == src_files == copy_files and not rows_bad
          and hashes["review-33/INDEPENDENT-REVIEW.md"]["sha256"] == SHA["review33"]
          and hashes["review-33/ESCALATION-RULINGS.final.json"]["sha256"] == SHA["escalation_rulings_final"]
          and hashes["review-33/DISPOSITIONS.json"]["sha256"] == SHA["dispositions"],
          {"source_files": len(src_files), "copied": len(cm["files"]), "mismatches": rows_bad})
    ec = load(PKG + "/evidence/COPY-MANIFEST.json")
    pin = ec["groups"]["packet-inputs"]["files"]
    pin_src = listing(SRC + "/packet-inputs")
    pin_bad = [x["path"] for x in pin if not (x["source_sha256"] == x["copy_sha256"] == sha256_file(x["source"])
                                              == hashes[x["copy"]]["sha256"])]
    pin_copy = sorted(rel[len("packet-inputs/"):] for rel in files if rel.startswith("packet-inputs/"))
    check("packet_inputs_copy_complete_and_equal",
          sorted(x["path"] for x in pin) == pin_src == pin_copy and not pin_bad,
          {"source_files": pin_src, "mismatches": pin_bad})
    lrows = ec["groups"]["labels"]["files"]
    check("label_copy_records_consistent",
          all(x["source_sha256"] == x["copy_sha256"] == x["frozen_sha256"] == hashes[x["copy"]]["sha256"]
              for x in lrows) and len(lrows) == 2, [x["path"] for x in lrows])

    # 3 scripts and the work folder
    sc_bad = [s for s in SCRIPTS if hashes.get("scripts/" + s, {}).get("sha256") != sha256_file(WORK + "/" + s)]
    check("package_scripts_equal_work_folder", not sc_bad, {"mismatches": sc_bad})

    # 4 reviewed-2
    r1 = load(PKG + "/labels/R32-LABELS-REVIEWED-1.json")
    r2_path = PKG + "/labels/R32-LABELS-REVIEWED-2.json"
    r2 = load(r2_path)
    ap = r2["applied"]
    bind_ok = (r2["version"] == "r32-labels-reviewed-2" and "NOT human-signed" in r2["status"]
               and "Review 33" in r2["status"]
               and r2["derived_from"] == {"version": "r32-labels-reviewed-1", "sha256": SHA["reviewed1"]}
               and ap["review33_sha256"] == SHA["review33"]
               and ap["escalation_rulings_final_sha256"] == SHA["escalation_rulings_final"]
               and ap["dispositions_sha256"] == SHA["dispositions"]
               and ap["conditions_applied"] == ["C-1", "C-2"])
    check("reviewed2_parses_and_binds_hashes", bind_ok,
          {"version": r2["version"], "status": r2["status"], "derived_from": r2["derived_from"],
           "applied": {k: ap[k] for k in ("review33_sha256", "escalation_rulings_final_sha256",
                                          "dispositions_sha256", "conditions_applied")}})
    check("generator_sha256_matches_script_copies",
          r2["generator"]["sha256"] == sha256_file(WORK + "/apply_review33_r32.py")
          == hashes["scripts/apply_review33_r32.py"]["sha256"], r2["generator"])
    A = module("apply_review33_r32_v", PKG + "/scripts/apply_review33_r32.py")
    meta = {"reviewed1_sha256": hashes["labels/R32-LABELS-REVIEWED-1.json"]["sha256"],
            "generated_at_utc": r2["generated_at_utc"], "generator_script": r2["generator"]["script"],
            "generator_sha256": r2["generator"]["sha256"]}
    with open(PKG + "/review-33/INDEPENDENT-REVIEW.md", encoding="utf-8") as f:
        review_text = f.read()
    rebuilt = A.build_reviewed2(r1, load(PKG + "/review-33/ESCALATION-RULINGS.final.json"),
                                {"review33_sha256": hashes["review-33/INDEPENDENT-REVIEW.md"]["sha256"],
                                 "escalation_rulings_final_sha256":
                                     hashes["review-33/ESCALATION-RULINGS.final.json"]["sha256"],
                                 "dispositions_sha256": hashes["review-33/DISPOSITIONS.json"]["sha256"]},
                                meta, review33_text=review_text)
    with open(r2_path, "rb") as f:
        r2_bytes = f.read()
    check("reviewed2_rebuilds_byte_identical_from_package_copies", dumps(rebuilt).encode("utf-8") == r2_bytes,
          {"reviewed2_sha256": hashes["labels/R32-LABELS-REVIEWED-2.json"]["sha256"]})
    unexpected = A.check_only_enumerated_changes(r1, r2)
    check("reviewed2_differs_only_at_enumerated_keys (apply-script check)", unexpected == [], unexpected)
    own_bad, own_docs = [], set()
    for p in own_diff(r1["documents"], r2["documents"]):
        own_docs.add(p[0])
        ok = any(p[:len(k)] == k and len(p) == len(k) + 1 and p[len(k)] in v for k, v in ALLOWED.items())
        if not ok:
            own_bad.append("/".join(p))
    esc_bad = ["/".join(p) for p in own_diff(r1["escalations"], r2["escalations"])
               if not (len(p) == 2 and p[1] in ("status", "ruled_by"))]
    same_top = all(json.dumps(r1[k], sort_keys=True) == json.dumps(r2[k], sort_keys=True)
                   for k in ("agents", "convention_rulings", "count_once_aliases"))
    check("reviewed2_differs_only_at_enumerated_keys (independent restatement)",
          not own_bad and not esc_bad and own_docs == {"F019", "F069"} and same_top,
          {"unexpected_document_paths": own_bad, "unexpected_escalation_paths": esc_bad,
           "documents_differing": sorted(own_docs), "agents_conventions_aliases_unchanged": same_top})
    d69, d19 = r2["documents"]["F069"], r2["documents"]["F019"]
    rows = {
        "F069/p1/identity": d69["pages"]["1"]["identity"], "F069/p3/identity": d69["pages"]["3"]["identity"],
    }
    rows_ok = all(f["state"] == "ambiguous" and f["literal"] is None and f["review_status"] == "ruled (Review 33, D-004)"
                  and f["association"] == "resolved" and f["excluded_from_scoring"] is True
                  and [c["literal"] for c in f["candidates"]] == ["EP-15744"]
                  and all(c["printed_label"] == "Refrence" and c["role"].startswith("not established on the page")
                          for c in f["candidates"])
                  and "open_question" not in f for f in rows.values())
    f19 = d19["pages"]["1"]["revision"]
    rows_ok = rows_ok and (f19["state"] == "ambiguous" and [c["literal"] for c in f19["candidates"]] == ["00", "01"]
                           and f19["excluded_from_scoring"] is True and f19["review_status"] == "ruled (Review 33, D-005)"
                           and "open_question" not in f19)
    docs_ok = ((d69["review"]["identity"]["resolved_for_scoring"], d69["review"]["identity"]["carries_fact"])
               == ("no", "no") and (d19["review"]["revision"]["resolved_for_scoring"],
                                    d19["review"]["revision"]["carries_fact"]) == ("no", "no")
               and d19["questions"][1]["ruling"] == "ruled (Review 33, D-005)"
               and [m["status"] for m in d19["unresolved_review33_marks"]] == ["ruled (Review 33, D-005)"])
    esc_ok = (len(r2["escalations"]) == 6 and all(
        e["status"] == "ruled (Review 33, %s)" % e["disposition_id"]
        and e["ruled_by"]["review33_sha256"] == SHA["review33"]
        and e["ruled_by"]["escalation_rulings_final_sha256"] == SHA["escalation_rulings_final"]
        for e in r2["escalations"]))
    left = []
    for pid, d in r2["documents"].items():
        for pg, page in (d.get("pages") or {}).items():
            for fld in FIELDS:
                x = page.get(fld)
                if x and (x["review_status"] == "unresolved" or "open_question" in x):
                    left.append("%s/p%s/%s" % (pid, pg, fld))
        for fld in FIELDS:
            x = d["review"][fld]
            if "unresolved" in (x["resolved_for_scoring"], x["carries_fact"]) or "open_question" in x:
                left.append("%s/%s" % (pid, fld))
        left += ["%s question" % pid for q in d["questions"] if q["ruling"].startswith("unresolved")
                 or "open_question" in q]
    ann = r2["count_once_alias_annotations"]
    ann_ok = ({k: v["of"] for k, v in ann.items()} == EXPECTED_ALIASES == r2["count_once_aliases"]
              and ann["F031"]["ruling"] == ann["F059"]["ruling"] == "Review 33 (c)(ii)" and "caveat" in ann["F031"]
              and ann["F052"]["ruling"] == ann["F070"]["ruling"] == "frozen convention section 1")
    am = r2["convention_amendments_and_interpretations"]
    am_ok = ([x["id"] for x in am["items"]] == AMENDMENT_IDS and am["condition_c2_verbatim"] in review_text
             and all(q in review_text for x in am["items"] for q in x["review33_verbatim"]))
    log_ok = all(e["provenance"].startswith("Review 33 ") and e["review33_sha256"] == SHA["review33"]
                 for e in r2["change_log"])
    check("reviewed2_enumerated_rows_escalations_aliases_amendments",
          rows_ok and docs_ok and esc_ok and not left and ann_ok and am_ok and log_ok,
          {"page_rows_ok": rows_ok, "document_question_rows_ok": docs_ok, "escalations_ruled_ok": esc_ok,
           "still_unresolved_or_open": left, "alias_annotations_ok": ann_ok, "amendment_list_ok": am_ok,
           "amendment_ids": [x["id"] for x in am["items"]], "change_log_entries": len(r2["change_log"]),
           "change_log_provenance_ok": log_ok, "page_field_status_counts": ap["page_field_status_counts"]})
    check("reviewed2_lineage_keeps_reviewed1_metadata",
          all(json.dumps(r2["lineage"]["reviewed_1"][k], sort_keys=True) == json.dumps(r1[k], sort_keys=True)
              for k in ("version", "status", "derived_from", "applied", "generated_at_utc", "generator")))

    # 5 FIELD-POPULATION equals a recount
    C = module("count_population_r32c_v", PKG + "/scripts/count_population_r32c.py")
    renders = load(FROZEN_PATHS["renders"])
    scope = C.in_scope_from_renders(renders)
    ei = load(PKG + "/packet-inputs/EVIDENCE-INDEX.json")
    ei_scope = {}
    for x in ei["renders"]:
        ei_scope.setdefault(x["pool_id"], []).append(str(x["page"]))
    check("in_scope_pages_renders_equal_evidence_index",
          {k: sorted(v) for k, v in scope.items()} == {k: sorted(v) for k, v in ei_scope.items()},
          {"documents": len(scope), "pages": sum(len(v) for v in scope.values())})
    fp = load(PKG + "/FIELD-POPULATION.json")
    recount = C.count_population(r2, scope)
    fp_wo = {k: v for k, v in fp.items() if k != "source"}
    check("field_population_equals_recount",
          json.dumps(fp_wo, sort_keys=True) == json.dumps(recount, sort_keys=True)
          and fp["source"]["reviewed_sha256"] == hashes["labels/R32-LABELS-REVIEWED-2.json"]["sha256"]
          and fp["source"]["review33_sha256"] == SHA["review33"]
          and fp["source"]["escalation_rulings_final_sha256"] == SHA["escalation_rulings_final"]
          and fp["source"]["in_scope_pages_from"]["sha256"] == SHA["renders"],
          {"gate_counts": recount["gate_counts"], "gate_action": recount["gate_action"],
           "excluded_unresolved": recount["excluded_unresolved"],
           "upper_bound_if_resolved": recount["upper_bound_if_resolved"]})
    check("field_population_expected_57_38_38_nothing_unresolved",
          fp["gate_counts"] == EXPECTED_COUNTS and fp["excluded_unresolved"] == {}
          and fp["upper_bound_if_resolved"] == EXPECTED_COUNTS and fp["status"] == "COUNTED"
          and fp["gate_action"] == "READY FOR INDEPENDENT PREPARATION REVIEW" and fp["extensions_used"] == 0
          and fp["stage"] == "initial pool after independent review and Review 33 rulings"
          and fp["consistency_check"]["ok"] is True and fp["count_once_aliases"] == EXPECTED_ALIASES,
          {"gate_counts": fp["gate_counts"], "excluded_unresolved": fp["excluded_unresolved"],
           "consistency": {k: fp["consistency_check"][k] for k in
                           ("ok", "checked_carries_fact_yes", "checked_carries_fact_no",
                            "yes_without_supporting_page", "no_with_supporting_page",
                            "labelled_pages_outside_scope", "in_scope_pages_without_labels")}})
    C1 = module("count_population_r32_frozen", SRC + "/scripts/count_population_r32.py")
    old = C1.count_population(r2)
    check("frozen_reviewed1_count_function_agrees_on_reviewed2",
          old["gate_counts"] == EXPECTED_COUNTS and all(v == [] for v in old["excluded_unresolved"].values())
          and old["upper_bound_if_resolved"] == EXPECTED_COUNTS and old["consistency_check"]["ok"] is True,
          {"script": SRC + "/scripts/count_population_r32.py", "gate_counts": old["gate_counts"],
           "excluded_unresolved": old["excluded_unresolved"]})

    # 6 junit
    junit = {}
    for x in sorted(glob.glob(PKG + "/tests/*.xml")):
        root = ET.parse(x).getroot()
        suites = [root] if root.tag == "testsuite" else list(root)
        t = sum(int(s.get("tests", 0)) for s in suites)
        fl = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
        junit[os.path.basename(x)] = {"tests": t, "failures_or_errors": fl}
    check("junit_all_pass", sorted(junit) == JUNIT and all(v["failures_or_errors"] == 0 and v["tests"] > 0
                                                           for v in junit.values())
          and all(hashes["tests/" + j]["sha256"] == sha256_file(WORK + "/tests/" + j) for j in JUNIT), junit)

    # 7 frozen trees not modified after the cutoff (os.stat only; no file is opened)
    late, counted = [], {}
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
    check("frozen_trees_not_modified_after_2026-10-03T09:50:00Z", not late and all(counted.values()),
          {"files_statted": counted, "modified_after_cutoff": late})

    # 8 ledger read-only
    con = sqlite3.connect("file:" + LEDGER + "?mode=ro", uri=True)
    try:
        entries = con.execute("select count(*) from entries").fetchone()[0]
        scopes = con.execute("select count(*) from scopes").fetchone()[0]
    finally:
        con.close()
    check("ai_ledger_read_only_483_entries_17_scopes", entries == 483 and scopes == 17,
          {"entries": entries, "scopes": scopes, "opened": "file:" + LEDGER + "?mode=ro (uri=True)"})

    # 9 response ledger untouched before the step-6 append
    check("response_file_unchanged_before_append", sha256_file(RESPONSE_MD) == SHA["response_md_before"],
          sha256_file(RESPONSE_MD))

    pycache = [rel for rel in files if "__pycache__" in rel or rel.endswith(".pyc")]
    check("no_bytecode_in_package", not pycache, pycache)

    if "--dry-run" in sys.argv[1:]:
        for name, c in checks.items():
            print("ok" if c["ok"] else "FAIL", name, "" if c["ok"] else json.dumps(c["detail"], ensure_ascii=False)[:2000])
        print("dry run: nothing written; problems", problems)
        return 0 if not problems else 1

    result = {
        "task": "ORCH-04.1 R32APPLY2-IMPL step 5",
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "package": PKG,
        "checks": checks,
        "problems": problems,
        "ok": not problems,
        "files_checked": len(files),
        "file_hashes": hashes,
        "note": "EVIDENCE-MANIFEST.json is written after this check from the same file hashes and lists every "
                "package file except itself and this check; it binds this check's sha256",
    }
    dump(result, PKG + "/" + CHECK)

    manifest = {
        "package": "fresh-cohort-r32-reviewed-2 (r32-labels-reviewed-2: r32-labels-reviewed-1 with the Independent "
                   "Preparation Review 33 rulings applied mechanically; counted field populations; AI-reviewed, NOT "
                   "human sign-off)",
        "reviewed2_labels_sha256": hashes["labels/R32-LABELS-REVIEWED-2.json"]["sha256"],
        "reviewed1_labels_sha256": SHA["reviewed1"],
        "draft_labels_sha256": SHA["draft"],
        "review33_sha256": SHA["review33"],
        "escalation_rulings_final_sha256": SHA["escalation_rulings_final"],
        "dispositions_sha256": SHA["dispositions"],
        "field_population_sha256": hashes["FIELD-POPULATION.json"]["sha256"],
        "package_check_sha256": sha256_file(PKG + "/" + CHECK),
        "package_check_ok": not problems,
        "written_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": hashes,
    }
    dump(manifest, PKG + "/" + MANIFEST)
    m = load(PKG + "/" + MANIFEST)
    resealed = [rel for rel, meta in m["files"].items() if sha256_file(PKG + "/" + rel) != meta["sha256"]]
    unlisted = [rel for rel in package_files() if rel not in m["files"]]
    print("checks", sum(c["ok"] for c in checks.values()), "/", len(checks), "problems", problems)
    print("manifest", sha256_file(PKG + "/" + MANIFEST), "files", len(m["files"]), "rehash mismatches", resealed,
          "unlisted", unlisted)
    print("package_check", m["package_check_sha256"], "reviewed2", m["reviewed2_labels_sha256"])
    return 0 if (not problems and not resealed and not unlisted) else 1


if __name__ == "__main__":
    sys.exit(main())
