"""AI accuracy pilot sample (frozen before any label or prediction for these files): up to 12 PDF documents from the
415-document exploration manifest (EXPLORATION-MANIFEST.json, hash-checked), none from the earlier 12-document small
batch, <= 3 pages each (bounds the pre-prediction labelling of the 4-page reading scope), <= 3 per project, >= 4
projects. Quotas by stratum (title-block drawings, covers / submittals, decision evidence, a scan, a negative
control); within a stratum, order = sha256(seed | doc_key). Word files are excluded (the evidence stage reads PDFs).
Reports every availability shortfall; never looks at the sealed cohort (not in this manifest)."""
import hashlib
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x")
MAN = W / "EXPLORATION-MANIFEST.json"
MAN_SHA = "ee9df7b5e3e6f0035beec01643435e46f63d7f59eccfb9102d6633bf2b6f97cd"
SB_SHA = "7039daa3f04935a35d9a272076be16510d4eb0a8885651f83f07af51f44d7139"
SEED = "m2-ai-pilot-2026-09-30"
QUOTA = [("shop_drawing", 2), ("drawing_ifc_input", 2), ("approval_sample", 2), ("reply", 2), ("submittal", 2), ("scan", 1), ("other", 1)]
CAP_PROJECT, MAX_PAGES = 3, 3
assert hashlib.sha256(MAN.read_bytes()).hexdigest() == MAN_SHA
assert hashlib.sha256((W / "SMALL-BATCH.json").read_bytes()).hexdigest() == SB_SHA
man = json.loads(MAN.read_text(encoding="utf-8"))
small = {d["sha256"] for d in json.loads((W / "SMALL-BATCH.json").read_text(encoding="utf-8"))["documents"]}
pool = [d for d in man["documents"] if d["extension"] == ".pdf" and d["sha256"] not in small and not d.get("open_error") and 1 <= (d.get("pages") or 0) <= MAX_PAGES]
rank = lambda d: hashlib.sha256(f"{SEED}|{d['doc_key']}".encode()).hexdigest()
chosen, per_project, shortfall = [], {}, []
for stratum, n in QUOTA:
    cands = sorted([d for d in pool if d["stratum"] == stratum], key=rank)
    got = 0
    for d in cands:
        if got == n:
            break
        if per_project.get(d["ep"], 0) >= CAP_PROJECT or d in chosen:
            continue
        chosen.append(d)
        per_project[d["ep"]] = per_project.get(d["ep"], 0) + 1
        got += 1
    if got < n:
        shortfall.append({"stratum": stratum, "wanted": n, "got": got, "eligible": len(cands)})
assert len(per_project) >= 4, per_project
out = {"seed": SEED, "rule": __doc__, "manifest_sha256": MAN_SHA, "excluded_small_batch_sha256": SB_SHA, "quota": QUOTA,
       "pool_size": len(pool), "shortfall": shortfall, "per_project": per_project,
       "documents": [{k: d[k] for k in ("doc_key", "ep", "stratum", "sha256", "staged_path", "pages", "scan_like", "first_page_size_pt")} for d in chosen]}
p = W / "ai-pilot/PILOT-SAMPLE.json"
p.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("pool", len(pool), "| chosen", len(chosen), "| projects", per_project, "| shortfall", shortfall)
for d in chosen:
    print(d["sha256"][:12], d["ep"], d["stratum"], d["pages"], "scan" if d.get("scan_like") else "", d["doc_key"].split("/", 1)[1][-80:])
print("sha256", hashlib.sha256(p.read_bytes()).hexdigest())
