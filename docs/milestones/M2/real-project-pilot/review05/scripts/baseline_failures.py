"""Run the three full-suite failures at several baselines, with the reviewer's isolated environment.
Usage: baseline_failures.py <out.json>"""
import os, sys, json, subprocess, tempfile, pathlib, xml.etree.ElementTree as ET

PY = r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\venv\Scripts\python.exe"
TARGETS = ["tests/test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index",
           "tests/test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it",
           "tests/test_submittal_one_per_system.py::test_the_page_counts_submittals_by_their_latest_revision"]
TREES = {"13eb73c (before M1/M2 commit)": "C:/t/wt/13eb73c", "ed7d221 (M1/M2 + File Sync V2 + BOQ V2 + Classification V2)": "C:/t/wt/ed7d221",
         "2221b43 (Review 01-03 committed)": "C:/t/wt/2221b43", "working tree (R4 + pilot fixes)": r"C:\Users\moham\Desktop\dev\dev\ep-platform"}
out = {}
for name, root in TREES.items():
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="m2r5b-", dir="C:/t"))
    env = dict(os.environ)
    env.update(AI_ENABLED="false", EXTRACTION_PROMOTE_OBSERVATIONS="false", DOCUMENT_CLASSIFICATION_V2="false", DATASHEET_LIBRARIES="{}", ARCHIVE_DATASHEET_LIBRARIES="{}",
               ARCHIVE_SUBMITTAL_LIBRARY="", PROJECTS_ROOT="", PROJECTS_ROOT_AUTODETECT="false", COMPLIANCE_KNOWLEDGE_SOURCE="", COMPLIANCE_KNOWLEDGE_AUTODETECT="false",
               COMPLIANCE_KNOWLEDGE_IMPORT_ON_START="false", SYNC_FILE_WORKERS="0", CACHE_ROOT=str(scratch / "cache"), LIBRARY_ROOT=str(scratch / "library"),
               UPLOADS_ROOT=str(scratch / "uploads"), TEMP=str(scratch), TMP=str(scratch), PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    for k in ("EP_TEST_DATABASE", "EP_PLATFORM_LIVE_ARCHIVE_ROOT", "DATABASE_URL"):
        env.pop(k, None)
    xml = scratch / "r.xml"
    per = {}
    for t in TARGETS:
        p = subprocess.run([PY, "-B", "-m", "pytest", t, "-q", "-p", "no:cacheprovider", "--basetemp", str(scratch / "bt"), "--junitxml", str(xml)],
                           cwd=pathlib.Path(root) / "backend", env=env, capture_output=True, text=True)
        res = "passed" if p.returncode == 0 else "failed"
        msg = ""
        if p.returncode:
            lines = [l for l in p.stdout.splitlines() if l.startswith("E ")]
            msg = " | ".join(lines[:4])[:400]
        per[t.split("::")[1]] = {"result": res, "rc": p.returncode, "message": msg}
    out[name] = per
    print(name, {k[:40]: v["result"] for k, v in per.items()}, flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
