"""Markdown tables of evaluator results, grouped (project / format / cohort / label confidence / stratum / scope)."""
import json, sys
def cell(v, f):
    x = (v.get("fields") or {}).get(f)
    if not x: return "-"
    return f"{x['tp']}/{x['accepted']} acc, {x['tp']}/{x['tp'] + x['wrong'] + x['near'] + x['missed'] + x['held']} rec" + (f", {x['held']} held" if x["held"] else "") + (f", fp {x['fp']}" if x["fp"] else "")
def table(result, group):
    rows = ["| " + group + " | docs | reference (accepted correct / readable recovered) | printed revision | decision | critical |", "|---|---|---|---|---|---|"]
    for k, v in result["by"][group].items():
        rows.append(f"| {k} | {v['documents']} | {cell(v, 'reference')} | {cell(v, 'revision')} | {cell(v, 'decision')} | {len(v['critical'])} |")
    return "\n".join(rows)
res = json.load(open(sys.argv[1], encoding="utf-8"))
for g in sys.argv[2:]:
    print(f"\n**By {g}**\n"); print(table(res, g))
