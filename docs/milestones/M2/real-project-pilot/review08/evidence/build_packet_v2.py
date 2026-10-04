"""M2 review 08: the human-review packet, version 2 -- a successor of review07/human-review-packet (kept unchanged).
Same items and scope; identities recorded one per row (literal, printed label, role); a finding-group index of the 13
review 07 source findings. AI-prepared proposals only: every human_* column is left blank."""
import csv
import hashlib
import json
import pathlib
import re

PILOT = pathlib.Path(r"C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
V1 = PILOT / "review07/human-review-packet"
OUT = PILOT / "review08/human-review-packet-v2"
ADJ = pathlib.Path(r"C:/t/iso/work/r7/ADJUDICATIONS.json")
PAGES = "../../review07/human-review-packet/"          # page images stay in the v1 packet (not copied)
OUT.mkdir(parents=True, exist_ok=True)


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


components = list(csv.DictReader(open(V1 / "COMPONENT-ITEMS.csv", encoding="utf-8-sig")))
boq = list(csv.DictReader(open(V1 / "BOQ-ITEMS.csv", encoding="utf-8-sig")))
cases = json.load(open(ADJ, encoding="utf-8"))["cases"]

# --- the 13 finding groups, matched to packet items ----------------------------------------------------------------------
F11_SHEETS = [("345-LA-SS-5A-20002.pdf", "1", "R1029-05-BSB-DWG-ALL-ARC-1282"),
              ("R1029-18-AUR-DWG-GFL-PUA-INF-53001-PDF (D) - BELLAGIO.pdf", "1", "R1029-18-AUR-DWG-GFL-PUA-INF-53000"),
              ("R1029-08-IFS-DWG-L07-ICT-1207.pdf", "1", "R1029-07-IFS-DWG-ALL-GRO-ICT-8107"),
              ("345-LA-HS-5C-11000.pdf", "1", "R1029-03-BSB-DWG-GFL-ARC-1224"),
              ("R1029-07-W&A-DWG-TYP-GRO-INT-9011-01-PDF-A.pdf", "1", "A-DWG-TYP-GRO-INT-1102-01"),
              ("R1029-08-W&A-DWG-L05-PUA-INT-3250-PDF-B.pdf", "1", "A-DWG-L05-PUA-INT-3250"),
              ("R1029-07-W&A-DWG-L05-PUA-INT-3114-PDF-E.pdf", "1", "A-DWG-L05-PUA-INT-3114"),
              ("R1029-08-W&A-DWG-L14-GRO-INT-4315-01-PDF-B.pdf", "1", "A-DWG-TYP-GRO-INT-1102-01"),
              ("revised_gas_bellagio_part1xiba1741941453483 (1).pdf", "9", "R1029-02-IBA-DWG-B01-GAS-1213")]


def f11(r):
    return next((s for s in F11_SHEETS if r["doc"].startswith("EP-26082/") and r["doc"].endswith(s[0]) and r["page"] == s[1]), None)


TAV = ("TAV-TN-009782 (1).pdf", "TAV-TN-000731.pdf", "TAV-TN-011156 (1).pdf")
MATCH = {
    7: lambda r: r["doc"].startswith("EP-13777/") and r["doc"].endswith(TAV) and r["page"] == "1",
    # review 07 recorded this file under EP-29076; it is in EP-26082 (GOLDEN-LABELS.json, the packet, the det .8 output)
    10: lambda r: r["doc"] == "EP-26082/EP-26082 MOM/L0749-Minutes of Weekly MEP Meeting No. 020 - Final Issuance.pdf" and r["page"] == "1",
    11: lambda r: f11(r) is not None,
}
DECISION = {   # what a person must settle, per group (AI-prepared wording; the decision itself is the reviewer's)
    1: ("unresolved", "Which printed identity is this document's own for evaluation: the building permit number (B2312982) or the request reference (REQ-2387569)? Record both with their printed labels and roles."),
    2: ("unresolved", "Does the ticked, signed CODE B stamp on page 3 (sheet 02 of 02) give this component's decision? If so the label is incomplete."),
    3: ("confirm", "Confirm the printed Doc No. literal (label EP-30784). The OCR reading TEP-30784 was observed, never accepted."),
    4: ("confirm", "Confirm the printed LPO number literal (label LPO/1050000159). The OCR reading was observed, never accepted."),
    5: ("confirm", "Confirm the quotation's own reference (label EP-19977-R1); the Ref-line drawing is a referenced (priced) drawing."),
    6: ("confirm", "Confirm the quotation's own reference (label EP - 19977 - R4-B0); the Ref-line drawings are referenced (priced) drawings."),
    7: ("unresolved", "Each transmittal prints the consultant's mail number (TAVC-TRANSMIT-...) and the contractor's reference number (K&A-WTRAN-...). Record both; say which one the register evaluates, or that both are the same document's own numbers."),
    8: ("unresolved", "Page 1 is the company's own cover (EP-26369/SS/FA/101, Revision). Is it a component of this document? The label has none on page 1."),
    9: ("unresolved", "Page 3 is a cover carrying another project's number (EP-30627/SS/EML/ 1293). Is it part of this document (association), and is it a component?"),
    10: ("unresolved", "The minutes print the contractor's outgoing letter number (10789-CSCEC-OUT-L0...) and the meeting letter number (L0749). Which is the minutes' own identity for evaluation?"),
    11: ("confirm", "Confirm each sheet's own number; the numbers read came from the sheet's reference table or a part number (pre-existing since Candidate C)."),
    12: ("unresolved", "The Dar review form prints its own document number (OCR ICDS-DOC-01943; the leading I is unverified) and the method statement it reviews (D15015-0200S-FS-EL-MS-0022). Which is the component's own identity, and what is the exact literal?"),
    13: ("unresolved", "The Bosch letter prints its own reference BSS/AE/ALARABIA/170315-047. Is the letter a component (it is labelled a no-record page)?"),
}
EXTRA = {   # printed identities the review 07 adjudication found beside the label (AI-prepared proposals)
    1: [("B2312982", "Permit Number", "permit")],
    5: [("D1902-FC-DWG-EM-B1200", "Ref", "referenced_document")],
    6: [("D1902-FC-DWG-EF-B1200", "Ref", "referenced_document")],
    8: [("EP-26369/SS/FA/101", "(company cover)", "own_document")],
    9: [("EP-30627/SS/EML/ 1293", "(cover)", "unclassified")],
    10: [("10789-CSCEC-OUT-L0", "(letter reference; literal as OCR read it)", "unclassified")],
    12: [("ICDS-DOC-01943", "(form's document number; leading I unverified)", "own_document"),
         ("D15015-0200S-FS-EL-MS-0022", "(reviewed document)", "reviewed_document")],
    13: [("BSS/AE/ALARABIA/170315-047", "Ref", "own_document")],
}

groups = []
item_groups: dict = {}
for n, case in enumerate(cases, 1):
    match = MATCH.get(n) or (lambda r, c=case: r["doc"] == c["doc"] and r["page"] == str(c["page"]))
    items = [r for r in components if match(r)]
    gid = f"F{n:02d}"
    assert items, (gid, case["doc"])
    for r in items:
        item_groups.setdefault(r["item"], []).append(gid)
    status, decide = DECISION[n]
    group = {"group": gid, "category": case["category"], "run": case["run"], "field": case["field"], "value_read": case["value"],
             "label": case["label"], "review07_resolution": case["resolution"], "status": status, "to_decide": decide,
             "items": [{"item": r["item"], "cohort": r["cohort"], "doc": r["doc"], "page": r["page"],
                        "page_image": PAGES + r["page_image"] if r["page_image"] else ""} for r in items]}
    if n == 10:
        group["correction"] = "Review 07 recorded the project as EP-29076; the file is in EP-26082 (GOLDEN-LABELS.json, packet item C0245, the det .8 output)."
    groups.append(group)

# --- identities: one row per printed identity ------------------------------------------------------------------------------


def split_reference(text):
    """The label's identities: split at top-level ';' only; the literal is the text before the first top-level ' (';
    the parenthesised remainder is the label author's free-form note (source, confidence, a cut cell ...), kept whole
    as a note and never read as a printed label."""
    parts, depth, cur = [], 0, ""
    for ch in text or "":
        depth += (ch == "(") - (ch == ")")
        if ch == ";" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    out = []
    for part in [p.strip() for p in parts if p.strip()]:
        i = part.find(" (")
        literal, note = (part[:i].strip(), part[i:].strip()) if i > 0 else (part, "")
        out.append(("" if literal.lower() == "unknown" else literal, note))
    return out


identities = []
for r in components:
    rows = []
    for k, (literal, note) in enumerate(split_reference(r["proposed_reference"])):
        rows.append({"literal": literal, "printed_label": "", "note": note, "role": ("own_document" if k == 0 else "unclassified") if literal else "",
                     "origin": "AI-drafted Golden label (proposed_reference)"})
    for gid in item_groups.get(r["item"], []):
        n = int(gid[1:])
        extra = [(f11(r)[2], "", "referenced_document")] if n == 11 else EXTRA.get(n, [])
        for literal, label, role in extra:
            if literal not in [x["literal"] for x in rows]:
                rows.append({"literal": literal, "printed_label": label if not label.startswith("(") else "",
                             "note": label if label.startswith("(") else ("read from the sheet's reference table or a part number" if n == 11 else ""),
                             "role": role, "origin": f"AI-prepared from review 07 finding {gid} -- not human"})
    for k, x in enumerate(rows, 1):
        identities.append({"item": r["item"], "identity_no": k, "proposed_literal": x["literal"], "proposed_printed_label": x["printed_label"],
                           "proposed_role": x["role"], "proposal_note": x["note"], "proposal_origin": x["origin"], "human_literal": "",
                           "human_printed_label": "", "human_role": "", "human_own_for_evaluation": "", "human_status": "", "human_notes": ""})

# --- component and BOQ items ---------------------------------------------------------------------------------------------
comp_cols = ["item", "cohort", "scope", "finding_group", "doc", "page", "page_image", "component", "proposed_reference", "proposed_printed_revision",
             "proposed_decision", "proposed_decision_actor", "proposed_label_confidence", "label_origin", "proposed_identity_rows",
             "human_identity_status", "human_own_identity_for_evaluation", "human_printed_revision", "human_revision_status",
             "human_decision", "human_decision_actor", "human_decision_status", "human_association_status", "human_uncertainty",
             "human_reviewer", "human_date", "human_notes"]
count: dict = {}
for x in identities:
    count[x["item"]] = count.get(x["item"], 0) + 1
comp_out = []
for r in components:
    row = {c: "" for c in comp_cols}
    row.update({k: r[k] for k in comp_cols if k in r and not k.startswith("human_")})
    row["page_image"] = PAGES + r["page_image"] if r["page_image"] else "open the original"
    row["finding_group"] = "; ".join(item_groups.get(r["item"], []))
    row["proposed_identity_rows"] = count.get(r["item"], 0)
    comp_out.append(row)
boq_cols = ["item", "cohort", "scope", "doc", "page", "page_image", "row", "kind", "proposed_part_number", "proposed_quantity", "proposed_description",
            "label_note", "label_origin", "human_row_type", "human_part_number", "human_part_status", "human_quantity", "human_quantity_source",
            "human_quantity_status", "human_uncertainty", "human_reviewer", "human_date", "human_notes"]
boq_out = []
for r in boq:
    row = {c: "" for c in boq_cols}
    row.update({k: r[k] for k in boq_cols if k in r and not k.startswith("human_")})
    row["page_image"] = PAGES + r["page_image"] if r["page_image"] else "open the original"
    boq_out.append(row)


def write_csv(name, cols, rows):
    with open(OUT / name, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


write_csv("COMPONENT-ITEMS-v2.csv", comp_cols, comp_out)
write_csv("IDENTITIES-v2.csv", list(identities[0]), identities)
write_csv("BOQ-ITEMS-v2.csv", boq_cols, boq_out)
(OUT / "FINDINGS-INDEX.json").write_text(json.dumps({"groups": groups}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

to_decide = [g for g in groups if g["status"] == "unresolved"]
L = ["# Findings index: the 13 Review 07 source findings", "",
     "**Status: prepared by AI, not reviewed.** Each group links the packet rows and page images it concerns. "
     "The Review 07 table stays unchanged in `../../review07/ADJUDICATIONS.md`; the one correction is noted under F10.", "",
     f"**{len(to_decide)} groups ({sum(len(g['items']) for g in to_decide)} items) need a decision**: a fact or an association that the "
     f"source leaves open for this packet. The other {len(groups) - len(to_decide)} groups "
     f"({sum(len(g['items']) for g in groups if g['status'] != 'unresolved')} items) need only a confirmation of the label literal. "
     "Until a person settles them, none of these is counted as an AI success or as a confirmed error.", "",
     "| Group | Status | Category | Field | Read | Label | Items (page image) |", "|---|---|---|---|---|---|---|"]
for g in groups:
    links = ", ".join(f"[{i['item']}]({i['page_image'].replace(' ', '%20')})" if i["page_image"] else i["item"] for i in g["items"])
    status = "**DECIDE**" if g["status"] == "unresolved" else "confirm"
    L.append(f"| {g['group']} | {status} | {g['category']} | {g['field']} | `{g['value_read'][:48]}` | {str(g['label'])[:60]} | {links} |")
L += ["", "## What each group asks", ""]
for g in groups:
    head = "**Decide**" if g["status"] == "unresolved" else "Confirm"
    n = len(g["items"])
    L.append(f"- **{g['group']}** ({n} item{'s' if n != 1 else ''}, {g['items'][0]['doc'].split('/')[0]}, {g['items'][0]['cohort']}). {head}: {g['to_decide']}"
             + (f" *Correction:* {g['correction']}" if g.get("correction") else "") + f" Review 07 resolution: {g['review07_resolution']}.")
L += ["", "Each item also carries its group ID in the `finding_group` column of `COMPONENT-ITEMS-v2.csv`; its printed identities are in `IDENTITIES-v2.csv`.", ""]
(OUT / "FINDINGS-INDEX.md").write_text("\n".join(L), encoding="utf-8", newline="\n")

manifest = {
    "packet": "m2-source-review-packet v2", "date": "2026-09-29", "instructions": "INSTRUCTIONS-v2.md", "schema": "PACKET-SCHEMA-v2.json",
    "predecessor": {"path": "../../review07/human-review-packet/", "unchanged": True,
                    "sha256": {n: sha(V1 / n) for n in ("COMPONENT-ITEMS.csv", "BOQ-ITEMS.csv", "INSTRUCTIONS.md", "PACKET-MANIFEST.json")}},
    "scope_unchanged": {"components": len(comp_out), "boq_rows": len(boq_out), "seed": json.load(open(V1 / "PACKET-MANIFEST.json", encoding="utf-8"))["seed"]},
    "identity_rows": len(identities), "items_with_more_than_one_identity": sum(1 for v in count.values() if v > 1),
    "finding_groups": len(groups), "finding_groups_to_decide": [g["group"] for g in to_decide],
    "finding_group_items": sum(len(g["items"]) for g in groups),
    "page_images": "linked from the v1 packet (pages/, 350 images, source hashes in its PACKET-MANIFEST.json); not copied",
    "human_columns_filled": 0, "reviewer": None,
    "generator": {"script": "review08/evidence/build_packet_v2.py", "sha256": sha(__file__)},
}
manifest["files"] = {n: sha(OUT / n) for n in ("COMPONENT-ITEMS-v2.csv", "IDENTITIES-v2.csv", "BOQ-ITEMS-v2.csv", "FINDINGS-INDEX.md", "FINDINGS-INDEX.json", "INSTRUCTIONS-v2.md", "PACKET-SCHEMA-v2.json")}
(OUT / "PACKET-MANIFEST-v2.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: manifest[k] for k in ("scope_unchanged", "identity_rows", "items_with_more_than_one_identity", "finding_groups_to_decide", "finding_group_items")}))
for g in groups:
    print(g["group"], g["status"], len(g["items"]), [i["item"] for i in g["items"]])
