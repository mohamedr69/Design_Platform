"""Pilot step 3: draw the document sample from the refreshed inventories (metadata only), by project and stratum with
a recorded seed; then open each drawn candidate once (this hydrates the OneDrive placeholder) to record its content hash,
page count and text-layer facts, and stage a copy under the sandbox tree. The frozen sample is what the pilot scores.

Strata (from path and extension only; contents verified later): scan-folder PDFs, shop-drawing covers/sheets,
material submittals, replies/comments, approvals/samples, specs, calcs, design sheets/BOQ, transmittals (Word),
other/uncategorised PDFs; unsupported formats are counted, never drawn."""
import json, os, sys, re, random, hashlib, pathlib, shutil, datetime, collections

S = pathlib.Path(sys.argv[1]); STAGE = pathlib.Path("C:/t/pilot/stage"); SEED = 20260928
inv = json.load(open(S / "PROJECT-INVENTORY.json", encoding="utf-8"))
PREFIX = "\\\\?\\"
STRATA = [("scan", r"\bscan"), ("design_sheet", r"design sheet|design\b.*\.pdf$|boq|bill of quant|\bdrf\b"), ("transmittal_word", None),
          ("reply", r"reply|comment|crs\b|response"), ("approval_sample", r"approv|sample|\bsar\b"), ("submittal", r"\bms\b|submittal|material|\bmas\b|method"),
          ("spec_compliance", r"spec|complian|standard"), ("calc", r"calc"), ("drawing_ifc_input", r"\bifc\b|input|tender|received from estimation|estimation"),
          ("shop_drawing", r"shop|\bsd\b|sdw|drawing|dwg|layout|plan"), ("other", None)]
QUOTA = {"30784": 40, "30088": 40, "29076": 55, "25091": 50, "19977": 32, "26082": 55, "27474": 2, "26369": 60, "13777": 40, "14119": 6}
CAP_PER_STRATUM = 0.45     # no stratum takes more than this share of a project's quota (template copies)
WORD = (".doc", ".docx")


def stratum_of(rel: str, ext: str) -> str:
    low = rel.lower().replace("\\", "/")
    if ext in WORD:
        return "transmittal_word" if re.search(r"transmit", low) else "other_word"
    if ext != ".pdf":
        return "unsupported"
    for name, rx in STRATA:
        if rx and re.search(rx, low):
            return name
    return "other"


rng = random.Random(SEED)
frozen = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "seed": SEED, "quota": QUOTA, "cap_per_stratum": CAP_PER_STRATUM,
          "strata_rules": [(n, rx) for n, rx in STRATA], "eligibility": "the sync's contract: .pdf files, and .doc/.docx files in a transmittal folder; everything else unsupported (counted, not drawn)",
          "projects": [], "documents": []}
for p in inv["projects"]:
    files = json.load(open(S / f"inventory-EP-{p['ep']}.json", encoding="utf-8"))["files"]
    by = collections.defaultdict(list); unsupported = collections.Counter()
    for f in files:
        st = stratum_of(f["relative_path"], f["extension"])
        if st in ("unsupported", "other_word"):
            unsupported[f["extension"]] += 1; continue
        by[st].append(f)
    eligible = sum(len(v) for v in by.values()); quota = min(QUOTA[p["ep"]], eligible)
    # allocation: every stratum present gets at least one; the rest proportional to size, capped
    strata = sorted(by, key=lambda k: -len(by[k])); alloc = {k: 1 for k in strata}
    remaining = quota - len(strata)
    weights = {k: len(by[k]) for k in strata}; total_w = sum(weights.values()) or 1
    for k in strata:
        alloc[k] += int(round(remaining * weights[k] / total_w))
    for k in strata:
        alloc[k] = min(alloc[k], len(by[k]), max(1, int(CAP_PER_STRATUM * quota)))
    # top up to the quota from strata with room, smallest strata first (diversity)
    room = sorted(strata, key=lambda k: len(by[k]))
    while sum(alloc.values()) < quota and any(alloc[k] < len(by[k]) for k in strata):
        for k in room:
            if sum(alloc.values()) >= quota: break
            if alloc[k] < len(by[k]): alloc[k] += 1
    drawn = []
    for k in strata:
        pool = sorted(by[k], key=lambda f: f["relative_path"].lower())
        rng.shuffle(pool)
        for f in pool[:alloc[k]]:
            drawn.append({**f, "stratum": k})
    frozen["projects"].append({"ep": p["ep"], "folder": p["folder"], "contractor": p["contractor"], "cohort": p["cohort"], "path": p["path"], "files": p["file_count"],
                               "eligible": eligible, "eligible_by_stratum": {k: len(by[k]) for k in strata}, "unsupported_by_extension": dict(unsupported.most_common()),
                               "quota": quota, "allocation": alloc, "drawn": len(drawn)})
    for f in drawn:
        frozen["documents"].append({"ep": p["ep"], "cohort": p["cohort"], "relative_path": f["relative_path"], "extension": f["extension"], "size": f["size"], "mtime_ns": f["mtime_ns"],
                                    "placeholder_before": f["recall_on_data_access"], "stratum": f["stratum"], "selection": "random within stratum, seed " + str(SEED)})
    print(p["ep"], p["cohort"], "eligible", eligible, "quota", quota, "alloc", alloc, flush=True)

# hydrate, hash, page facts, stage
import pymupdf
STAGE.mkdir(parents=True, exist_ok=True)
seen_hash = {}
for i, d in enumerate(frozen["documents"]):
    src = pathlib.Path(next(p["path"] for p in inv["projects"] if p["ep"] == d["ep"])) / d["relative_path"]
    long = PREFIX + str(src)
    dst = STAGE / f"EP-{d['ep']}" / d["relative_path"]
    try:
        with open(long, "rb") as h:
            data = h.read()
        d["sha256"] = hashlib.sha256(data).hexdigest(); d["bytes_read"] = len(data)
        d["hydrated_for_pilot"] = bool(d["placeholder_before"])
        dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(data); d["staged_path"] = str(dst)
        if d["sha256"] in seen_hash:
            d["duplicate_content_of"] = seen_hash[d["sha256"]]
        else:
            seen_hash[d["sha256"]] = f"EP-{d['ep']}/{d['relative_path']}"
        if d["extension"] == ".pdf":
            try:
                with pymupdf.open(stream=data, filetype="pdf") as pdf:
                    d["pages"] = pdf.page_count
                    texts = [len(pdf[k].get_text().strip()) for k in range(min(pdf.page_count, 3))]
                    d["text_chars_first_pages"] = texts; d["scan_like"] = all(t < 80 for t in texts)
                    d["rotation_first_page"] = pdf[0].rotation if pdf.page_count else None
                    d["images_first_page"] = len(pdf[0].get_images()) if pdf.page_count else None
            except Exception as exc:  # noqa: BLE001
                d["open_error"] = f"{type(exc).__name__}: {exc}"[:160]
    except OSError as exc:
        d["read_error"] = f"{type(exc).__name__}: {exc}"[:160]
    if i % 25 == 0:
        print("staged", i, flush=True)
frozen["accounting"] = {"drawn": len(frozen["documents"]), "read": sum(1 for d in frozen["documents"] if "sha256" in d), "read_errors": sum(1 for d in frozen["documents"] if "read_error" in d),
                        "open_errors": sum(1 for d in frozen["documents"] if "open_error" in d), "duplicate_content": sum(1 for d in frozen["documents"] if "duplicate_content_of" in d),
                        "hydrated": sum(1 for d in frozen["documents"] if d.get("hydrated_for_pilot")), "scan_like": sum(1 for d in frozen["documents"] if d.get("scan_like")),
                        "by_cohort": dict(collections.Counter(d["cohort"] for d in frozen["documents"])), "by_stratum": dict(collections.Counter(d["stratum"] for d in frozen["documents"]))}
json.dump(frozen, open(S / "FROZEN-SAMPLE.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(frozen["accounting"], indent=1))
