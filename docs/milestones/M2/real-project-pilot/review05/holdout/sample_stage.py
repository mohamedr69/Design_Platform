import json, os, re, random, shutil, hashlib, sys
R = sys.argv[1]
sel = json.load(open(R + "/holdout/SELECTION.json", encoding="utf-8")); plan = json.load(open(R + "/holdout/HOLDOUT-PLAN.json", encoding="utf-8"))
Q = plan["quota_per_project"]; SEED = sel["seed"]; MAXB = 60 * 1024 * 1024
STAGE = "C:/t/holdout/stage"
frozen = json.load(open(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\FROZEN-SAMPLE.json", encoding="utf-8"))
fboq = json.load(open(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\FROZEN-BOQ-SET.json", encoding="utf-8"))
pilot_hashes = {d["sha256"] for d in frozen["documents"]} | {s["sha256"] for s in fboq["sheets"]}
def stratum(rel):
    low = rel.lower().replace(chr(92), "/"); name = low.rsplit("/", 1)[-1]; folder = low.rsplit("/", 1)[0] if "/" in low else ""
    if low.endswith((".doc", ".docx")):
        return "word_transmittal" if "transmit" in low else None
    if not low.endswith(".pdf"): return None
    if re.search(r"design", name): return "boq_design_sheet"
    if re.search(r"\back\b", name.replace(".", " ")): return "scanned_ack"
    if re.search(r"shop drawings|as built dwg|(^|/)[^/]*dwg(/|$)", folder): return "shop_drawing_sheet"
    if re.search(r"approv|comment|(^|/)[^/]*app(/|$)|mts-", low): return "approval_or_comments"
    if re.search(r"(^|/)ms(/|$)| ms |cataluge|catalog|certificate|calculation|commercial|scan doc|scan documents|test cert", low + " "): return "negative"
    return None
out = {"at": None, "documents": [], "skipped": []}
for t in sel["taken"]:
    files = []
    for dirpath, dirs, fs in os.walk(t["path"], onerror=lambda e: None):
        for f in fs:
            rel = os.path.relpath(os.path.join(dirpath, f), t["path"])
            s = stratum(rel)
            if s:
                try: size = os.stat(os.path.join(dirpath, f)).st_size
                except OSError: continue
                files.append((rel, s, size))
    rng = random.Random(SEED + int(t["ep"]))
    for s, q in Q.items():
        pool = sorted(r for r in files if r[1] == s); rng.shuffle(pool); n = 0
        for rel, _s, size in pool:
            if n == q: break
            if size > MAXB:
                out["skipped"].append({"ep": t["ep"], "relative_path": rel, "stratum": s, "reason": f"over 60 MB ({size // 1048576} MB)"}); continue
            src = os.path.join(t["path"], rel); dst = os.path.join(STAGE, f"EP-{t['ep']}", rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst)
            h = hashlib.sha256(open(dst, "rb").read()).hexdigest()
            out["documents"].append({"ep": t["ep"], "contractor": t["contractor"], "relative_path": rel, "stratum": s, "size": size, "sha256": h,
                                     "staged_path": dst, "overlaps_pilot_hash": h in pilot_hashes}); n += 1
import datetime; out["at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
json.dump(out, open(R + "/holdout/HOLDOUT-SAMPLE.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
import collections
print(len(out["documents"]), "staged;", dict(collections.Counter((d["ep"], d["stratum"]) for d in out["documents"])), "overlaps", sum(d["overlaps_pilot_hash"] for d in out["documents"]), "skipped", out["skipped"])
