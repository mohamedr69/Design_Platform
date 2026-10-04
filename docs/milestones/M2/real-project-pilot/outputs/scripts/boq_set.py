"""Pilot step 3 (BOQ / design-sheet set, labelled separately): the real Design Sheets and BOQs of the pilot projects,
chosen by name from the frozen inventories (Commercial / Scan folders, not shop drawings), hydrated one by one, hashed,
staged beside the main sample, every page rendered for row labelling. Frozen before any read. Usage: boq_set.py <scratch>"""
import json, sys, pathlib, hashlib, datetime
import pymupdf

S = pathlib.Path(sys.argv[1]); ROOT = pathlib.Path("C:/t/pilot"); OUT = S / "boq_pages"; OUT.mkdir(exist_ok=True)
inventory = json.load(open(S / "PROJECT-INVENTORY.json", encoding="utf-8"))
roots = {p["ep"]: p["path"] for p in inventory["projects"]}
cohort = {p["ep"]: p["cohort"] for p in inventory["projects"]}
CHOSEN = {"30784": [r"01- EP-30784 Scan\EP-30784 FAS Design.pdf", r"01- EP-30784 Scan\EP-30784 EML Design.pdf"],
          "30088": [r"01. Commercial Document\EP-30088 Design Sheet FAS.pdf", r"01. Commercial Document\EP-30088 Design Sheet ELS.pdf"],
          "29076": [r"01- EP-29076 - Scan\EP-29076 FAS Design.pdf"],
          "25091": [r"EP-25091 Scan\EP-25091 FAS Design.pdf", r"EP-25091 Scan\EP-25091 PA Design.pdf"],
          "19977": [r"EP-19977 Commercial\EP-19977 CBS Design.pdf"],
          "26082": [r"EP-26082 - COMMERCIAL\EP-26082 FAS Design.pdf", r"EP-26082 - COMMERCIAL\EP-26082 Aspiration Design.pdf", r"EP-26082 INPUTS\COMPLIANCE STATEMENT\FAS BOQ-R0.pdf"],
          "27474": [r"EP-27474 Scan\EP-27474 Design.pdf"],
          "26369": [r"EP-26369 Commercial\EP-26369 Design.pdf", r"MS FAS\BOQ.pdf"],
          "14119": [r"EP-14119 Commercial\EP-14119 BOQ.pdf"]}
sheets = []
for ep, rels in CHOSEN.items():
    inv = {f["relative_path"]: f for f in json.load(open(S / f"inventory-EP-{ep}.json", encoding="utf-8"))["files"]}
    for rel_hint in rels:
        matches = [k for k in inv if k.endswith(rel_hint)]
        if len(matches) != 1:
            sheets.append({"ep": ep, "hint": rel_hint, "error": f"{len(matches)} inventory matches"}); continue
        rel = matches[0]; f = inv[rel]; src = pathlib.Path("\\\\?\\" + str(pathlib.Path(roots[ep]) / rel))
        entry = {"ep": ep, "cohort": cohort[ep], "relative_path": rel, "size": f["size"], "mtime_ns": f["mtime_ns"], "placeholder_before": bool(f.get("recall_on_data_access")), "set": "boq_design_sheets"}
        try:
            data = src.read_bytes()
        except OSError as exc:
            entry["read_error"] = str(exc)[:160]; sheets.append(entry); continue
        entry["sha256"] = hashlib.sha256(data).hexdigest(); entry["bytes_read"] = len(data)
        dst = ROOT / "stage" / f"EP-{ep}" / rel; dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            dst.write_bytes(data)
        entry["staged_path"] = str(dst)
        try:
            pdf = pymupdf.open(stream=data, filetype="pdf"); entry["pages"] = pdf.page_count; entry["text_chars_first_pages"] = [len(pdf[i].get_text()) for i in range(min(3, pdf.page_count))]
            entry["scan_like"] = all(c < 50 for c in entry["text_chars_first_pages"]); tag = entry["sha256"][:12]; entry["page_images"] = []
            for i in range(min(pdf.page_count, 12)):
                name = f"{tag}-p{i + 1}.png"; pdf[i].get_pixmap(dpi=110).save(OUT / name); entry["page_images"].append(name)
            pdf.close()
        except Exception as exc:  # noqa: BLE001
            entry["open_error"] = str(exc)[:160]
        sheets.append(entry); print(ep, rel[-50:], entry.get("pages"), entry.get("scan_like"), flush=True)
frozen = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "selection": "by name: the Design Sheet / BOQ PDFs in each project's Commercial or Scan folder (all found, none random)",
          "sheets": sheets, "accounting": {"chosen": sum(len(v) for v in CHOSEN.values()), "staged": sum(1 for s in sheets if s.get("staged_path")), "hydrated": sum(1 for s in sheets if s.get("placeholder_before") and s.get("staged_path")),
                                           "projects": len({s["ep"] for s in sheets if s.get("staged_path")}), "pages": sum(s.get("pages") or 0 for s in sheets), "errors": [s for s in sheets if "error" in s or "read_error" in s or "open_error" in s]}}
json.dump(frozen, open(S / "FROZEN-BOQ-SET.json", "w", encoding="utf-8"), indent=1)
print(frozen["accounting"])
