"""Step 4: the seeded initial labelling pool of 72 documents, from METADATA ONLY (directory entries, names, sizes, modified
times, attributes; no content read, no placeholder hydrated). The rules are fixed here, before the draw, and the full
seeded order is frozen so the two predeclared extensions are deterministic.

Rules (Review 31 plan v2 section 2 / FIELD-POPULATION-FEASIBILITY.v2):
  universe   every *.pdf under the verified project folder of each cohort project (PROJECT-VERIFICATION.json), size > 0;
             a path naming ANOTHER EP number (cross-project material) is excluded, fail closed
  stratum    review_signal if the relative path matches REVIEW; else drawing_signal if it matches DRAWING; else other
             (the same regular expressions as Review 31's selector, so the feasibility basis is unchanged)
  order      ascending sha256("<seed>|EP-<ep>|<relative path>") -- one global seeded order
  duplicates a file whose (lower-cased name, size) equals an earlier file in the seeded order is a duplicate copy and is
             skipped (recorded); the first in seeded order is the representative
  pool       quotas review_signal 40, drawing_signal 20, other 12, filled stratum by stratum in the seeded order with at most
             12 documents per project; if caps leave the pool short of 72, the remainder is filled from any stratum in the
             seeded order, still at most 12 per project (recorded as 'fill')
  extension-1 the next 36 review_signal documents in the seeded order, cumulative cap 18 per project
  extension-2 the next 36 review_signal documents, cumulative cap 24; when the cohort projects are exhausted under the cap,
             the alternate projects enter in their order (each needs the same verification first)
Seed: m2-r30-pool-2026-10-02 (declared in DRAFT-DECLARATION.v2). Writes FROZEN-SELECTION.json."""
import collections
import datetime
import hashlib
import json
import os
import pathlib
import re
import stat

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "FROZEN-SELECTION.json"
if OUT.exists():
    raise SystemExit("FROZEN-SELECTION.json exists: the selection is frozen")
SEED = "m2-r30-pool-2026-10-02"
REVIEW = re.compile(r"approv|comment|review|status|consultant|reply|stamp|resubmit|reject|\bnoc\b", re.I)
DRAWING = re.compile(r"shop ?d(?:wg|rawing)|\bdwg|\bsd\b|drawing|layout|riser|schematic", re.I)
EPNUM = re.compile(r"\bEP[- ]?(\d{4,6})\b", re.I)
QUOTA = {"review_signal": 40, "drawing_signal": 20, "other": 12}
CAP = 12
RECALL, OFFLINE = 0x400000, 0x1000
V = json.loads((HERE / "PROJECT-VERIFICATION.json").read_text(encoding="utf-8"))
assert V["cohort"] == ["3563", "22349", "27331", "15744", "26687", "29255"]


def universe(ep):
    root = "\\\\?\\" + V["results"][ep]["folder"]          # long-path prefix: no file beyond 260 characters is skipped
    out = []
    for dirpath, _d, files in os.walk(root):
        for f in files:
            if not f.lower().endswith(".pdf"):
                continue
            full = os.path.join(dirpath, f)
            st = os.stat(full, follow_symlinks=False)
            rel = os.path.relpath(full, root).replace("\\", "/")
            other_eps = {m.group(1) for m in EPNUM.finditer(rel)} - {ep}
            out.append({"ep": ep, "relative_path": rel, "size": st.st_size,
                        "modified_utc": datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat(timespec="seconds"),
                        "placeholder": bool(getattr(st, "st_file_attributes", 0) & (RECALL | OFFLINE)),
                        "stratum": "review_signal" if REVIEW.search(rel) else "drawing_signal" if DRAWING.search(rel) else "other",
                        "excluded": "names another EP number" if other_eps else ("empty file" if st.st_size == 0 else None),
                        "order_key": hashlib.sha256(f"{SEED}|EP-{ep}|{rel}".encode()).hexdigest()})
    return out


U = sorted((x for ep in V["cohort"] for x in universe(ep)), key=lambda x: x["order_key"])
seen, dups = {}, []
for x in U:
    if x["excluded"]:
        continue
    k = (pathlib.PurePosixPath(x["relative_path"]).name.lower(), x["size"])
    if k in seen:
        x["excluded"] = f"duplicate copy of EP-{seen[k]['ep']}/{seen[k]['relative_path']}"
        dups.append(x)
    else:
        seen[k] = x
eligible = [x for x in U if not x["excluded"]]
per_project, pool = collections.Counter(), []
for stratum, q in QUOTA.items():
    n = 0
    for x in eligible:
        if n >= q:
            break
        if x["stratum"] == stratum and x not in pool and per_project[x["ep"]] < CAP:
            pool.append(x | {"how": stratum})
            per_project[x["ep"]] += 1
            n += 1
for x in eligible:
    if len(pool) >= sum(QUOTA.values()):
        break
    if all(x["relative_path"] != p["relative_path"] or x["ep"] != p["ep"] for p in pool) and per_project[x["ep"]] < CAP:
        pool.append(x | {"how": "fill"})
        per_project[x["ep"]] += 1
taken = {(p["ep"], p["relative_path"]) for p in pool}
review_rest = [x for x in eligible if x["stratum"] == "review_signal" and (x["ep"], x["relative_path"]) not in taken]
pool = [dict(p, pool_id=f"F{i:03d}", selection_order=i) for i, p in enumerate(pool, 1)]
universe_digest = hashlib.sha256(json.dumps([[x["ep"], x["relative_path"], x["size"], x["modified_utc"]] for x in U]).encode()).hexdigest()
rules_text = __doc__
out = {"frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "authorization": "AUTHORIZATION-2026-10-02.md",
       "seed": SEED, "rules": rules_text, "rules_sha256": hashlib.sha256(rules_text.encode()).hexdigest(),
       "content_read": "none: directory entries, names, sizes, modified times and attributes only",
       "cohort": V["cohort"], "project_folders": {ep: V["results"][ep]["folder"] for ep in V["cohort"]},
       "universe": {"pdf_files": len(U), "eligible": len(eligible), "excluded": collections.Counter(str(x["excluded"]).split(" of ")[0] for x in U if x["excluded"]),
                    "by_project_stratum": {ep: dict(collections.Counter(x["stratum"] for x in eligible if x["ep"] == ep)) for ep in V["cohort"]},
                    "digest_sha256": universe_digest},
       "pool": [{k: p[k] for k in ("pool_id", "selection_order", "ep", "relative_path", "size", "modified_utc", "placeholder", "stratum", "how", "order_key")} for p in pool],
       "pool_counts": {"total": len(pool), "by_how": dict(collections.Counter(p["how"] for p in pool)), "by_project": dict(per_project)},
       "extension_order_review_signal": [{k: x[k] for k in ("ep", "relative_path", "size", "modified_utc", "order_key")} for x in review_rest],
       "duplicates_skipped": len(dups),
       "source_hash": "recorded at staging (SOURCE-MANIFEST.json): the bytes are hashed while the copy is read; nothing is read here"}
out["universe"]["excluded"] = dict(out["universe"]["excluded"])
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(hashlib.sha256(OUT.read_bytes()).hexdigest())
print(json.dumps({k: out[k] for k in ("universe", "pool_counts")}, indent=1), "extension candidates:", len(review_rest),
      dict(collections.Counter(x["ep"] for x in review_rest)))
