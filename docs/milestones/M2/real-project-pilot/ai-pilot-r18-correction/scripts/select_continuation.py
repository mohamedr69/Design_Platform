"""Continuation sample (frozen before any new prediction): 7 PDF documents.
  controls (4, EXPOSED, predicted in the ai-accuracy-pilot): the sheets whose S discovery exhausted the 120 s job budget
    or hit the 300 s provider timeout -- BH2031 (A1, 265.9 s discovery), TEL-00 ST-B+R (A1 portrait, 145.4 s),
    DCH-...-74028 (A0, 95.0 s + budget), DJ-295 (A3, discovery timeout 300 s; not a drawing sheet by the application's
    test, so E does not locate it -- the deadline-bound timeout is what it controls)
  new (3, never predicted): drawing-size PDFs (long side > 1300 pt, the application's drawing-sheet test), 1-2 pages,
    from the 415-document exploration manifest (hash-checked), not in the small batch or the pilot sample; order =
    sha256(seed | doc_key); one per project, projects without a control first. Sealed projects are not in the manifest.
Writes CONTINUATION-SAMPLE.json."""
import hashlib
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x")
OUT = W / "ai-pilot-r18/CONTINUATION-SAMPLE.json"
MAN_SHA = "ee9df7b5e3e6f0035beec01643435e46f63d7f59eccfb9102d6633bf2b6f97cd"
PILOT_SHA = "3822df9ef792e6c6277e0bec3271dcee06dcdc6a15291a3e03ab0b25b6bf1917"
SB_SHA = "7039daa3f04935a35d9a272076be16510d4eb0a8885651f83f07af51f44d7139"
SEED = "m2-ai-pilot-r18-continuation-2026-09-30"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(W / "EXPLORATION-MANIFEST.json") == MAN_SHA and sha(W / "ai-pilot/PILOT-SAMPLE.json") == PILOT_SHA and sha(W / "SMALL-BATCH.json") == SB_SHA
man = json.loads((W / "EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))
pilot = json.loads((W / "ai-pilot/PILOT-SAMPLE.json").read_text(encoding="utf-8"))["documents"]
small = {d["sha256"] for d in json.loads((W / "SMALL-BATCH.json").read_text(encoding="utf-8"))["documents"]}
CONTROL_PREFIX = {"500833f7db2b": "S discovery 265.9 s, then elapsed-budget stop", "e740af954610": "S discovery 145.4 s, then elapsed-budget stop",
                  "1e98dc27bfaf": "S discovery 95.0 s, revision read refused by the elapsed budget", "b713d5e56599": "S discovery timed out (300 s)"}
controls = [dict({k: d[k] for k in ("doc_key", "ep", "stratum", "sha256", "staged_path", "pages", "scan_like", "first_page_size_pt")},
                 role="control_exposed", why=CONTROL_PREFIX[d["sha256"][:12]]) for d in pilot if d["sha256"][:12] in CONTROL_PREFIX]
assert len(controls) == 4
used = {d["sha256"] for d in pilot} | small
pool = [d for d in man["documents"] if d["extension"] == ".pdf" and d["sha256"] not in used and not d.get("open_error")
        and 1 <= (d.get("pages") or 0) <= 2 and max(d.get("first_page_size_pt") or [0]) > 1300]
rank = lambda d: hashlib.sha256(f"{SEED}|{d['doc_key']}".encode()).hexdigest()
pool.sort(key=rank)
control_eps = {c["ep"] for c in controls}
new = []
for prefer_new_project in (True, False):
    for d in pool:
        if len(new) == 3:
            break
        if d["ep"] in {n["ep"] for n in new} or (prefer_new_project and d["ep"] in control_eps) or d in new:
            continue
        new.append(d)
new = [dict({k: d[k] for k in ("doc_key", "ep", "stratum", "sha256", "staged_path", "pages", "scan_like", "first_page_size_pt")}, role="new") for d in new]
out = {"seed": SEED, "rule": __doc__, "manifest_sha256": MAN_SHA, "pilot_sample_sha256": PILOT_SHA, "small_batch_sha256": SB_SHA,
       "pool_size": len(pool), "documents": controls + new}
if OUT.exists():
    raise SystemExit("the continuation sample is frozen")
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for d in out["documents"]:
    print(d["role"], d["sha256"][:12], d["ep"], d["stratum"], d["pages"], d["first_page_size_pt"], "scan" if d.get("scan_like") else "", d["doc_key"][-70:])
print("sha256", sha(OUT))
