"""Markdown tables for ACCURACY-AND-COVERAGE.md from ACCURACY.json (candidate A and B) and the per-document files.
Usage: render_tables.py <scratch> -> writes <scratch>/tables.md"""
import json, sys, pathlib, collections, random

S = pathlib.Path(sys.argv[1])
A = json.load(open(S / "candidateA" / "ACCURACY.json", encoding="utf-8")); B = json.load(open(S / "ACCURACY.json", encoding="utf-8"))
labels = json.load(open(S / "GOLDEN-LABELS.json", encoding="utf-8"))
tiles = [x for x in json.load(open(S / "crops" / "index.json")) if x.get("whole")]
tile_of = {}
for i, x in enumerate(tiles): tile_of.setdefault(x["doc"], i)
sha_of = {d["doc"]: d.get("sha256") for d in labels["documents"]}
for d in labels["documents"]:
    if d["doc"] not in tile_of:
        twin = next((k for k, v in sha_of.items() if v == d.get("sha256") and k in tile_of), None)
        if twin: tile_of[d["doc"]] = tile_of[twin]
tb = json.load(open(S / "tb" / "index.json")); tb_sheet = {i[0]: n // 4 + 1 for n, i in enumerate(tb)}
out = []


def pct(x): return "--" if x is None else f"{100 * x:.1f} %"


def link(doc):
    t = tile_of.get(doc)
    if t is None: return "(Word / no render)"
    s = f"crops/sheet-{t // 4 + 1:03d}.jpg#tile-{t}"
    if t in tb_sheet: s += f", crops/tb-{tb_sheet[t]:03d}.jpg"
    return s


for name, rep in (("A (parse-2026-09-28.4, frozen before any fix)", A), ("B (parse-2026-09-28.5, after P-01..P-04)", B)):
    out.append(f"\n### Candidate {name}\n")
    for prof, r in rep["profiles"].items():
        out.append(f"\n**Profile `{prof}`** -- document outcomes (exclusive): " + ", ".join(f"{k} {v}" for k, v in sorted(r["outcomes"].items())) + "\n")
        out.append("| field | auto-accepted | correct | wrong | near (punctuation / suffix) | abstained (UR / held / no record) | unscorable (label absent, n/a, unknown, illegible) | precision of accepted | automatic recovery | review rate |")
        out.append("|---|---|---|---|---|---|---|---|---|---|")
        for f, v in r["field_rates"].items():
            out.append(f"| {f} | {v['accepted']} | {v['correct']} | {v['wrong']} | {v['near']} | {v['abstained']} | {v['unscorable']} | {pct(v['precision_of_accepted'])} | {pct(v['automatic_recovery'])} | {pct(v['review_rate'])} |")
        pg = r["pages"]
        out.append(f"\nPages: total {pg['total']}, visited {pg['visited']}, skipped by budget {pg['skipped']}, failed {pg['failed']}; OCR attempted on {pg['ocr_attempted']} pages, failed {pg['ocr_failed']}, left out by the OCR budget {pg['ocr_skipped_budget']}; stop reasons " + ", ".join(f"{k or 'none'} {v}" for k, v in pg["stop_reasons"].items()) + ".\n")
        for grp, title in (("by_cohort", "cohort"), ("by_project", "project"), ("by_stratum", "stratum (path rule)"), ("by_format", "format")):
            out.append(f"\nBy {title}:\n")
            out.append("| " + title + " | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |")
            out.append("|---|---|---|---|---|---|---|")
            for k, v in sorted(r[grp].items(), key=lambda kv: str(kv[0])):
                rt = v["rates"]
                out.append(f"| {k} | {v['documents']} | " + ", ".join(f"{a} {b}" for a, b in sorted(v["outcomes"].items())) + f" | {rt['reference']['correct']} / {rt['reference']['accepted']} ({rt['reference']['abstained']}) | {rt['revision']['correct']} / {rt['revision']['accepted']} ({rt['revision']['abstained']}) | {rt['decision']['correct']} / {rt['decision']['accepted']} ({rt['decision']['abstained']}) | {rt['system']['correct']} / {rt['system']['accepted']} |")
        crit = r["critical_failures"]
        out.append(f"\nCritical failures, profile `{prof}`: {len(crit)} -- " + ", ".join(f"{k} {v}" for k, v in collections.Counter(c["kind"] for c in crit).items()) + "\n")
        out.append("| kind | document | expected (label) | actual (reader) | render |")
        out.append("|---|---|---|---|---|")
        for c in crit:
            out.append(f"| {c['kind']} | `{c['doc']}` | `{c.get('expected', c.get('printed'))}` | `{c.get('actual', c.get('actual_reference'))}` | {link(c['doc'])} |")
# random correct controls from candidate B default
per = json.load(open(S / "per-document-default.json", encoding="utf-8"))
ok = [e for e in per if e["fields"] and all(v[0] in ("correct", "correct-later-record") for v in e["fields"].values() if v[0] != "unscorable") and any(v[0] == "correct" for v in e["fields"].values())]
random.seed(20260928); sample = random.sample(ok, min(12, len(ok)))
out.append("\n### Random correct controls (candidate B, default profile; seed 20260928)\n")
out.append("| document | cohort | reference | revision | decision | render |")
out.append("|---|---|---|---|---|---|")
for e in sample:
    a = e["actual"]
    out.append(f"| `{e['doc']}` | {e['cohort']} | `{a['reference']}` | `{a['revision']}` | `{a['status']}` | {link(e['doc'])} |")
(S / "tables.md").write_text("\n".join(out), encoding="utf-8")
print("tables.md", len(out), "lines; controls", len(ok))
