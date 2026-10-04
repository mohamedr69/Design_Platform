"""M2 Round 2 exploration, step 3: stage the frozen selection (EXPLORATION-SELECTION.json, hash-checked) through the
approved isolated workflow: read each original once (hydrating its OneDrive placeholder), hash it, copy it under
C:/t/r2x/stage, and record page/text facts. Originals are only read, never written.

Distinct content: a file whose SHA-256 was already staged in this cohort, or in the exposed rounds (the Round 1
FROZEN-SAMPLE, the BOQ set and the Review 05 holdout), is a duplicate -- recorded, never counted as a new
independent document -- and is replaced from the SAME project and stratum's frozen replacement order (rank order,
never by content). Unreadable files are replaced the same way. A stratum with no replacement left is a shortfall,
reported; nothing is taken from another project or cohort, and the sealed cohort is never touched.
BOQ name candidates are staged as well (the separate BOQ set; which are real BOQ tables is established afterwards)."""
import collections
import datetime
import hashlib
import json
import pathlib
import sys

import pymupdf

SEL = pathlib.Path("C:/t/iso/work/r2x/EXPLORATION-SELECTION.json")
SEL_SHA = sys.argv[1]
STAGE = pathlib.Path("C:/t/r2x/stage")
OUT = pathlib.Path("C:/t/iso/work/r2x/EXPLORATION-MANIFEST.json")
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PREFIX = "\\\\?\\"
assert hashlib.sha256(SEL.read_bytes()).hexdigest() == SEL_SHA, "the frozen selection changed"
sel = json.loads(SEL.read_text(encoding="utf-8"))
assert all("sealed" not in str(d.get("cohort", "")) for d in sel["documents"])


def exposed_hashes() -> dict:
    """SHA-256 -> where it was staged before (the exposed cohorts), from the frozen manifests."""
    out = {}
    for path in [PILOT / "FROZEN-SAMPLE.json", PILOT / "FROZEN-BOQ-SET.json", PILOT / "review05" / "holdout" / "HOLDOUT-SAMPLE.json",
                 PILOT / "review05" / "holdout" / "HOLDOUT-BOQ-SET.json"]:
        if not path.exists():
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        for x in d.get("documents") or d.get("sheets") or []:
            if x.get("sha256"):
                out.setdefault(x["sha256"], f"exposed:{path.name}:EP-{x.get('ep')}/{x.get('relative_path')}")
    return out


def read_original(rec: dict) -> bytes:
    return open(PREFIX + str(pathlib.Path(rec["folder"]) / rec["relative_path"]), "rb").read()


def stage_one(rec: dict, data: bytes) -> dict:
    rel = rec["doc_key"].split("/", 1)[1]
    dst = STAGE / f"EP-{rec['ep']}" / pathlib.PurePosixPath(rel)
    long = pathlib.Path(PREFIX + str(dst).replace("/", "\\"))
    long.parent.mkdir(parents=True, exist_ok=True)
    if not long.exists():
        long.write_bytes(data)
    facts = {"staged_path": str(dst), "staged_path_length": len(str(dst))}
    if rec["extension"] == ".pdf":
        try:
            with pymupdf.open(stream=data, filetype="pdf") as pdf:
                facts["pages"] = pdf.page_count
                texts = [len(pdf[k].get_text().strip()) for k in range(min(pdf.page_count, 3))]
                facts["text_chars_first_pages"] = texts
                facts["scan_like"] = all(t < 80 for t in texts)
                if pdf.page_count:
                    r = pdf[0].rect
                    facts["first_page_size_pt"] = [round(r.width), round(r.height)]
        except Exception as exc:  # noqa: BLE001
            facts["open_error"] = f"{type(exc).__name__}: {exc}"[:160]
    return facts


seen = exposed_hashes()
exposed_known = len(seen)
replacements = collections.defaultdict(list)
for r in sorted(sel["replacements"], key=lambda r: (r["ep"], r["stratum"], r["rank_in_stratum"])):
    replacements[(r["ep"], r["stratum"])].append(r)
manifest = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "selection_sha256": SEL_SHA,
            "stage_root": str(STAGE), "exposed_hashes_known": exposed_known, "documents": [], "duplicates": [], "unreadable": [],
            "shortfall": [], "boq_candidates": []}


def take(rec: dict, role: str) -> str:
    """'ok' | 'duplicate' | 'unreadable' -- and record it."""
    try:
        data = read_original(rec)
    except OSError as exc:
        manifest["unreadable"].append({**rec, "role": role, "error": f"{type(exc).__name__}: {exc}"[:160]})
        return "unreadable"
    sha = hashlib.sha256(data).hexdigest()
    base = {**rec, "role": role, "sha256": sha, "bytes_read": len(data), "hydrated": bool(rec.get("placeholder_before"))}
    if sha in seen:
        manifest["duplicates"].append({**base, "duplicate_of": seen[sha]})
        return "duplicate"
    seen[sha] = f"exploration:{rec['doc_key']}"
    facts = stage_one(rec, data)
    manifest["documents" if role != "boq_candidate" else "boq_candidates"].append({**base, **facts})
    return "ok"


for i, rec in enumerate(sel["documents"]):
    status = take(rec, "primary")
    while status != "ok":
        pool = replacements[(rec["ep"], rec["stratum"])]
        if not pool:
            manifest["shortfall"].append({"ep": rec["ep"], "stratum": rec["stratum"], "for": rec["doc_key"], "reason": status})
            break
        nxt = pool.pop(0)
        status = take({**nxt, "replaces": rec["doc_key"]}, "replacement")
    if i % 25 == 0:
        print("staged", i, "docs", len(manifest["documents"]), "dup", len(manifest["duplicates"]), "unreadable", len(manifest["unreadable"]), flush=True)
primary_keys = {d["doc_key"] for d in manifest["documents"]}
for b in sel["boq_candidates"]:
    if b["doc_key"] in primary_keys:
        manifest["boq_candidates"].append({"doc_key": b["doc_key"], "ep": b["ep"], "role": "boq_candidate", "also_primary": True})
        continue
    inv = json.loads((pathlib.Path("C:/t/iso/work/r2x/inventory") / f"inventory-EP-{b['ep']}.json").read_text(encoding="utf-8"))
    multi = len(inv["project"]["folders"]) > 1
    hit = [x for x in inv["files"] if f"EP-{b['ep']}/" + ((x["folder_name"] + "/") if multi else "") + x["relative_path"].replace("\\", "/") == b["doc_key"]]
    x = hit[0]
    take({"ep": b["ep"], "doc_key": b["doc_key"], "folder": x["folder"], "relative_path": x["relative_path"], "extension": x["extension"], "size": x["size"],
          "mtime_ns": x["mtime_ns"], "path_length": x["path_length"], "placeholder_before": x["recall_on_data_access"], "stratum": "design_sheet",
          "selection": "BOQ name rule"}, "boq_candidate")
docs = manifest["documents"]
manifest["accounting"] = {"distinct_documents_staged": len(docs), "target": sel["target_distinct_documents"],
                          "duplicates": len(manifest["duplicates"]), "duplicates_of_exposed": sum("exposed:" in d["duplicate_of"] for d in manifest["duplicates"]),
                          "unreadable": len(manifest["unreadable"]), "shortfall": len(manifest["shortfall"]),
                          "open_errors": sum("open_error" in d for d in docs), "scan_like": sum(bool(d.get("scan_like")) for d in docs),
                          "pages_total": sum(d.get("pages") or 0 for d in docs), "hydrated": sum(bool(d.get("hydrated")) for d in docs),
                          "staged_paths_over_259": sum(d["staged_path_length"] > 259 for d in docs),
                          "by_project": dict(collections.Counter(d["ep"] for d in docs)), "by_stratum": dict(collections.Counter(d["stratum"] for d in docs)),
                          "by_extension": dict(collections.Counter(d["extension"] for d in docs)),
                          "boq_candidates_staged": sum(1 for b in manifest["boq_candidates"] if b.get("sha256") or b.get("also_primary"))}
OUT.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(manifest["accounting"], indent=1))
print("manifest sha256", hashlib.sha256(OUT.read_bytes()).hexdigest())
