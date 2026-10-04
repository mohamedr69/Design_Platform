"""Markdown view of HUMAN-REVIEW-WORKLIST.json for the package (crop paths relative to the package's worklist/ folder)."""
import json
import pathlib
import sys

src = pathlib.Path("C:/t/iso/work/r2x/worklist/HUMAN-REVIEW-WORKLIST.json")
out = pathlib.Path(sys.argv[1])
w = json.loads(src.read_text(encoding="utf-8"))
s = w["sections"]
L = ["# Round 2 human-review worklist (deliverable 3)", "",
     f"**Status: {w['status']}**", "",
     "Machine-readable file: [`HUMAN-REVIEW-WORKLIST.json`](HUMAN-REVIEW-WORKLIST.json). Its answer fields are empty. "
     "Packet v2 (`../review08/human-review-packet-v2/`) is preserved unchanged and linked by hash.", "",
     "## What must be reviewed", ""]
L += [f"- {r}" for r in w["rules"]["mandatory"]]
smp = w["rules"]["independent_sample"]
L += ["", f"**The independent sample.**", f"- Rate: {int(smp['rate'] * 100)} %, seed `{smp['seed']}`.", f"- Population: {smp['population']}.", f"- Ranking: {smp['ranking']}.",
      f"- When it was declared: {smp['declared_when']}.", "",
      "| Section | Items |", "|---|---|",
      f"| 1. Review 07 source findings | {w['counts']['source_findings_items']} items in {w['counts']['decide_groups']} DECIDE and {w['counts']['confirm_groups']} CONFIRM groups |",
      f"| 2. H-06 BOQ rows | {w['counts']['h06_rows']} |", f"| 3. Small-batch unresolved labels | {w['counts']['small_batch_unresolved']} |",
      f"| 4. Labelled decisions | {w['counts']['labelled_decisions']} (the small batch labels none, so decision accuracy is not measured by it) |",
      f"| 5. Critical disagreements | {len((s['5_critical_disagreements'] or {}).get('critical_false_accepts', [])) if isinstance(s['5_critical_disagreements'], dict) else 'pending'} critical false accepts (under provisional truth) |",
      f"| 6. Independent sample | {w['counts']['independent_sample']} of {s['6_independent_sample']['pool']} units |", ""]
L += ["## 1. Review 07 source findings", "", "| ID | Kind | Field | Question | Read | Label | Crops | Page image (v2) |", "|---|---|---|---|---|---|---|---|"]
for x in s["1_source_findings"]:
    crops = ", ".join(f"[{i + 1}](crops/findings/{c})" for i, c in enumerate(x["crops"])) or "-"
    note = f" *{x['ai_note']}*" if x.get("ai_note") else ""
    L.append(f"| {x['id']} | **{x['kind']}** | {x['field']} | {x['question']}{note} | `{x['value_read']}` | {x['label']} | {crops} | [page](../review08/human-review-packet-v2/{x['page_image_packet_v2']}) |")
L += ["", "## 2. H-06 BOQ rows (EP-8430)", "", "| ID | Row | Note | Crops | Question |", "|---|---|---|---|---|"]
for x in s["2_h06_boq_rows"]:
    L.append(f"| {x['id']} | {x['row_description']} | {x['note']} | " + ", ".join(f"[{c.split('/')[-1]}](crops/{c})" for c in x["crops"]) + f" | {x['question']} |")
L += ["", "## 3. Small-batch unresolved labels", "", "| ID | Document | Page | Question | Crop |", "|---|---|---|---|---|"]
for x in s["3_small_batch_unresolved"]:
    L.append(f"| {x['id']} | `{x['doc']}` | {x['page']} | {x['question']} | " + ", ".join(f"[crop](crops/small-batch/{c})" for c in x["crops"]) + f" ({x['located_by'][0]}) |")
L += ["", "## 5. Critical disagreements (from the scored runs; provisional truth)", ""]
d = s["5_critical_disagreements"]
if isinstance(d, dict):
    L += ["| Profile | Document | Page | Field | Value accepted | How | Why it needs a person | Crop |", "|---|---|---|---|---|---|---|---|"]
    for c in d["critical_false_accepts"]:
        L.append(f"| {c['profile']} | `{c['doc']}` | {c['page']} | {c['field']} | `{c['value']}` | {c.get('how')} | {c.get('review_note', '')} | "
                 + ", ".join(f"[crop](crops/critical/{f})" for f in c.get("crops", [])) + " |")
    L += ["", f"Cross-profile conflicts on one page and field: {len(d.get('cross_profile', []))} (listed in `DISAGREEMENTS.json`)."]
else:
    L.append(str(d))
L += ["", "## 6. Independent sample", "", "| Rank | Unit | Type | Document | Page |", "|---|---|---|---|---|"]
for x in s["6_independent_sample"]["items"]:
    L.append(f"| {x['rank']} | `{x['unit']}` | {x['type']} | `{x['doc']}` | {x['page']} |")
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("wrote", out)
