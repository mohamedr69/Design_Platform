"""Holdout selection for M2 review 05 (predeclared; run before any document is opened).

Eligible: an EP project folder under the archive root that is not one of the ten pilot projects and whose contractor
folder is not a pilot contractor; with >= 8 PDFs under document-control folders (approval / submittal / shop drawing /
scan / MS / transmittal / reply names), >= 1 Design Sheet PDF, and >= 1 Word document (.doc/.docx). Metadata only:
names, sizes and attributes -- no file is opened or recalled. Order: all EP folders sorted, shuffled with the seed; the
first K eligible are taken, one per contractor."""
import json, os, random, re, sys, stat, time
ROOT = r"C:\Users\moham\Juma Al Majid\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
SEED, K, FILE_CAP = 20260929, 4, 4000
inv = json.load(open(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\PROJECT-INVENTORY.json", encoding="utf-8"))
pilot_eps = {p["ep"] for p in inv["projects"]}
pilot_contractors = {p["path"].split("\\")[-2].strip().lower() for p in inv["projects"]}
DOC_DIRS = re.compile(r"approv|submitt|shop\s*d|\bsd\b|scan|\bms\b|method|transmit|reply|comment|material|sample|drawing", re.I)
folders = []
for contractor in sorted(os.listdir(ROOT)):
    cpath = os.path.join(ROOT, contractor)
    if not os.path.isdir(cpath): continue
    for name in sorted(os.listdir(cpath)):
        m = re.match(r"^EP-?\s?(\d{4,5})\b", name)
        if m and os.path.isdir(os.path.join(cpath, name)):
            folders.append((contractor, name, m.group(1), os.path.join(cpath, name)))
rng = random.Random(SEED); order = folders[:]; rng.shuffle(order)
taken, seen_contractors, log = [], set(), []
for contractor, name, ep, path in order:
    why = None
    if ep in pilot_eps: why = "pilot project"
    elif contractor.strip().lower() in pilot_contractors: why = "pilot contractor"
    elif contractor in seen_contractors: why = "contractor already taken"
    if why:
        log.append({"ep": ep, "folder": name, "contractor": contractor, "skip": why}); continue
    t0 = time.time(); files = []
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            full = os.path.join(dirpath, f)
            try: st = os.stat(full)
            except OSError: continue
            files.append((os.path.relpath(full, path), st.st_size, getattr(st, "st_file_attributes", 0)))
        if len(files) > FILE_CAP: break
    pdf_doc = [f for f in files if f[0].lower().endswith(".pdf") and DOC_DIRS.search(os.path.dirname(f[0]) + " " + f[0])]
    design = [f for f in files if f[0].lower().endswith(".pdf") and re.search(r"design", os.path.basename(f[0]), re.I)]
    word = [f for f in files if f[0].lower().endswith((".doc", ".docx"))]
    entry = {"ep": ep, "folder": name, "contractor": contractor, "files": len(files), "doc_control_pdfs": len(pdf_doc), "design_pdfs": len(design), "word": len(word), "walk_s": round(time.time() - t0, 1)}
    if len(files) > FILE_CAP: entry["skip"] = "over the file cap"
    elif len(pdf_doc) >= 8 and design and word:
        entry["selected"] = True; taken.append({**entry, "path": path}); seen_contractors.add(contractor)
    else: entry["skip"] = "not eligible (doc-control PDFs / design sheet / Word)"
    log.append(entry)
    if len(taken) == K: break
json.dump({"seed": SEED, "k": K, "root": ROOT, "pilot_eps": sorted(pilot_eps), "pilot_contractors": sorted(pilot_contractors), "ep_folders": len(folders), "taken": taken, "log": log},
          open(sys.argv[1], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(folders), "folders;", len(log), "examined;", [ (t["ep"], t["contractor"], t["doc_control_pdfs"], t["design_pdfs"], t["word"]) for t in taken])
