"""Deterministic BOQ evaluation for the M2 real-project pilot (M2 review 05, R5-04).

Runs the application's own deterministic reader, `app.services.design_sheet_extractor.extract_design_sheet`, on each
frozen Design Sheet with the model disabled, and scores what it emitted against the independently labelled rows.

Units: a *row* is one labelled row of a sheet. Equipment rows (kind "line" and "component") are scored; headings are
counted apart (a heading emitted as an equipment line is an extra, never a match); "component-or-heading" rows are
unscorable. An emitted row is either *accepted* (a BOQ line the reader stands behind) or *held* (an issue for the
engineer with the cell's readings, quantity and crop -- evidence, not an accepted value).

Per field, over equipment rows: tp / wrong (accepted, differs) / fp (accepted where truth has none) / tn / held /
missed. Critical: an accepted wrong part number, an accepted wrong quantity, an accepted line where the truth is a
heading or nothing.

Usage: python -m scripts.m2_boq_eval --labels GOLDEN-LABELS.json --set FROZEN-BOQ-SET.json --out result.json
       [--only EP-19977] [--reuse extraction.json]
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import json
import os
import re
import time
from pathlib import Path

BOQ_EVALUATOR_VERSION = "m2-boq-eval-2026-09-28.2"   # .2: versioned label corrections (--corrections)
EQUIPMENT = ("line", "component")


def part_key(text) -> str:
    return re.sub(r"[^A-Z0-9/+.-]", "", str(text or "").upper())


def quantity_key(text) -> str | None:
    if text is None:
        return None
    t = str(text).strip().replace(",", "")
    try:
        f = float(t)
        return str(int(f)) if f == int(f) else str(f)
    except ValueError:
        return t.upper() or None


def tokens(text) -> set:
    return set(re.findall(r"[A-Z0-9]{2,}", str(text or "").upper()))


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def similarity(truth: dict, emitted: dict) -> float:
    """How alike a labelled row and an emitted row are, 0..3: part number, description, quantity."""
    score = 0.0
    tp, ep = part_key(truth.get("part_number")), part_key(emitted.get("part_number"))
    if tp and ep:
        d = edit_distance(tp, ep)
        score += 1.5 if d == 0 else 1.0 if d <= max(1, len(tp) // 5) else 0.0
    a, b = tokens(truth.get("description")), tokens(emitted.get("description"))
    if a and b:
        score += len(a & b) / max(1, min(len(a), len(b)))
    if quantity_key(truth.get("quantity")) and quantity_key(truth.get("quantity")) == quantity_key(emitted.get("quantity")):
        score += 0.3
    return score


def align(truth: list[dict], emitted: list[dict], threshold: float = 0.6) -> list[tuple]:
    """Order-preserving alignment (both lists in reading order): pairs (t, e), (t, None) or (None, e)."""
    n, m = len(truth), len(emitted)
    best = [[0.0] * (m + 1) for _ in range(n + 1)]
    move = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        move[i][0] = "t"
    for j in range(1, m + 1):
        move[0][j] = "e"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = similarity(truth[i - 1], emitted[j - 1])
            options = [(best[i - 1][j], "t"), (best[i][j - 1], "e")]
            if s >= threshold:
                options.append((best[i - 1][j - 1] + s, "m"))
            best[i][j], move[i][j] = max(options, key=lambda o: o[0])
    pairs, i, j = [], n, m
    while i > 0 or j > 0:
        step = move[i][j]
        if step == "m":
            pairs.append((truth[i - 1], emitted[j - 1])); i -= 1; j -= 1
        elif step == "t":
            pairs.append((truth[i - 1], None)); i -= 1
        else:
            pairs.append((None, emitted[j - 1])); j -= 1
    return list(reversed(pairs))


def judge(truth_value, emitted_value, accepted: bool, key) -> str:
    t, e = key(truth_value), key(emitted_value)
    if not accepted:
        return "held" if e or t else "tn"
    if not t:
        return "fp" if e else "tn"
    if not e:
        return "missed"
    return "tp" if t == e else "wrong"


def rates(c: collections.Counter) -> dict:
    accepted = c["tp"] + c["wrong"] + c["fp"]
    positives = c["tp"] + c["wrong"] + c["missed"] + c["held"]
    return {**{k: c[k] for k in ("tp", "wrong", "fp", "tn", "held", "missed")}, "accepted": accepted,
            "precision_of_accepted": round(c["tp"] / accepted, 4) if accepted else None,
            "recovery_of_readable": round(c["tp"] / positives, 4) if positives else None}


def emitted_rows(extraction: dict) -> list[dict]:
    """Accepted lines and held review rows of one extraction, in reading order."""
    rows = []
    for line in extraction["lines"]:
        top = (line.get("row_bounds") or [line.get("y_px") or 0])[0]
        rows.append({"page": line["page"], "y": top, "part_number": line.get("catalog_no"), "quantity": line.get("quantity"),
                     "description": line.get("description"), "accepted": True, "catalog_check": line.get("catalog_check"),
                     "catalog_confidence": line.get("catalog_confidence")})
    for issue in extraction["issues"]:
        detail = issue.get("detail") or {}
        if not str(issue.get("target") or "").startswith("boq_line:"):
            continue
        region = issue.get("region") or detail.get("bbox") or [0, 0, 0, 0]
        rows.append({"page": issue.get("page"), "y": region[1], "part_number": detail.get("catalog_no"),
                     "quantity": detail.get("quantity") or detail.get("raw_quantity"), "description": detail.get("description"),
                     "accepted": False, "reason": detail.get("reason_code") or detail.get("reason"),
                     "catalog_alternates": detail.get("catalog_alternates"), "catalog_cell": detail.get("catalog_cell")})
    return sorted(rows, key=lambda r: (r["page"] or 0, r["y"] or 0))


def score_sheet(label: dict, extraction: dict) -> dict:
    out = {"ep": label["ep"], "relative_path": label["relative_path"], "pages": label.get("pages"),
           "truth": dict(collections.Counter(r["kind"] for r in label["rows"])), "state": extraction.get("state"),
           "outcome": extraction.get("outcome"), "failure": extraction.get("failure"),
           "emitted": {"accepted": len(extraction["lines"]), "held": sum(1 for i in extraction["issues"] if str(i.get("target") or "").startswith("boq_line:"))},
           "fields": {}, "rows": collections.Counter(), "critical": [], "pairs": []}
    fields = collections.defaultdict(collections.Counter)
    emitted = emitted_rows(extraction)
    for page in sorted({r["page"] for r in label["rows"]} | {r["page"] for r in emitted}):
        truth = [r for r in label["rows"] if r["page"] == page]
        mine = [r for r in emitted if r["page"] == page]
        for t, e in align(truth, mine):
            kind = t["kind"] if t else None
            if t is not None and kind not in EQUIPMENT and kind != "heading":
                out["rows"]["unscorable (component-or-heading)"] += 1
                continue
            if t is None:
                how = "extra accepted" if e["accepted"] else "extra held"
                out["rows"][how] += 1
                if e["accepted"]:
                    out["critical"].append({"kind": "accepted line where truth has none", "page": page, "emitted": _brief(e)})
                out["pairs"].append({"page": page, "how": how, "emitted": _brief(e)})
                continue
            if kind == "heading":
                if e is None:
                    out["rows"]["heading (not emitted)"] += 1
                else:
                    how = "heading emitted as accepted line" if e["accepted"] else "heading held"
                    out["rows"][how] += 1
                    if e["accepted"]:
                        out["critical"].append({"kind": "accepted line where truth is a heading", "page": page, "truth": t.get("description"), "emitted": _brief(e)})
                continue
            if e is None:
                out["rows"]["equipment missing"] += 1
                for f in ("part_number", "quantity", "description"):
                    if t.get(f) not in (None, ""):
                        fields[f]["missed"] += 1
                out["pairs"].append({"page": page, "how": "missing", "truth": _brief(t)})
                continue
            out["rows"]["equipment matched (accepted)" if e["accepted"] else "equipment matched (held)"] += 1
            states = {"part_number": judge(t.get("part_number"), e.get("part_number"), e["accepted"], part_key),
                      "quantity": judge(t.get("quantity"), e.get("quantity"), e["accepted"], quantity_key)}
            if e["accepted"]:
                a, b = tokens(t.get("description")), tokens(e.get("description"))
                states["description"] = ("tp" if a and len(a & b) / len(a) >= 0.6 else "wrong") if a else "tn"
            else:
                states["description"] = "held"
            for f, s in states.items():
                fields[f][s] += 1
            if states["part_number"] in ("wrong", "fp"):
                out["critical"].append({"kind": "accepted wrong part number", "page": page, "truth": t.get("part_number"), "emitted": e.get("part_number"),
                                        "catalog_confidence": e.get("catalog_confidence"), "catalog_check": e.get("catalog_check")})
            if states["quantity"] in ("wrong", "fp"):
                out["critical"].append({"kind": "accepted wrong quantity", "page": page, "part": t.get("part_number"), "truth": t.get("quantity"), "emitted": e.get("quantity")})
            out["pairs"].append({"page": page, "how": "matched", "fields": states, "truth": _brief(t), "emitted": _brief(e)})
    out["fields"] = {f: rates(c) for f, c in fields.items()}
    out["rows"] = dict(out["rows"])
    return out


def _brief(r: dict) -> dict:
    return {k: r.get(k) for k in ("part_number", "quantity", "description", "accepted", "reason", "kind") if r.get(k) is not None}


def totals(sheets: list[dict]) -> dict:
    fields = collections.defaultdict(collections.Counter)
    rows = collections.Counter()
    for s in sheets:
        rows.update(s["rows"])
        for f, v in s["fields"].items():
            for k in ("tp", "wrong", "fp", "tn", "held", "missed"):
                fields[f][k] += v[k]
    return {"rows": dict(rows), "fields": {f: rates(c) for f, c in fields.items()},
            "critical": sum(len(s["critical"]) for s in sheets), "sheets": len(sheets),
            "outcomes": dict(collections.Counter(s["outcome"] for s in sheets))}


def apply_corrections(labels: list[dict], corrections: list[dict]) -> list[dict]:
    """Apply versioned label corrections (each with its evidence); returns what was applied. A correction that
    matches no row is reported, never silently skipped."""
    applied = []
    for c in corrections:
        hits = [r for s in labels if s["ep"] == c["ep"] and s["relative_path"].endswith(c["relative_path_suffix"])
                for r in s["rows"] if r["page"] == c["page"] and str(r.get("description") or "").startswith(c["description_startswith"])
                and r.get(c["field"]) == c["old"]]
        for r in hits:
            r[c["field"]] = c["new"]
            r.update(c.get("set") or {})
        applied.append({**c, "rows_matched": len(hits)})
    return applied


def extract(sheet: dict) -> dict:
    from app.services import design_sheet_extractor as dse

    path = Path(sheet["staged_path"])
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    started = time.perf_counter()
    result = dse.extract_design_sheet(path)
    return {"sha256_matches_frozen": before == sheet["sha256"], "seconds": round(time.perf_counter() - started, 1),
            "state": result.state, "reader": result.reader, "failure": result.failure, "outcome": str(result.outcome),
            "lines": [dataclasses.asdict(l) for l in result.lines],
            "issues": [dataclasses.asdict(i) if dataclasses.is_dataclass(i) else dict(i) for i in result.issues],
            "notes": list(result.notes), "coverage": dataclasses.asdict(result.coverage),
            "source_unchanged": hashlib.sha256(path.read_bytes()).hexdigest() == before}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only")
    ap.add_argument("--reuse", help="score a stored extraction json instead of running the reader")
    ap.add_argument("--corrections", help="versioned label corrections (labels v2), applied before scoring")
    args = ap.parse_args(argv)
    from app.core.config import get_settings

    assert not get_settings().ai_enabled, "the deterministic track runs with the model disabled (AI_ENABLED=false)"
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))["boq_design_sheets"]["sheets"]
    applied = apply_corrections(labels, json.loads(Path(args.corrections).read_text(encoding="utf-8"))["corrections"]) if args.corrections else []
    frozen = json.loads(Path(args.set).read_text(encoding="utf-8"))["sheets"]
    stored = json.loads(Path(args.reuse).read_text(encoding="utf-8")) if args.reuse else {}
    sheets, extractions = [], {}
    for label in labels:
        if args.only and f"EP-{label['ep']}" not in args.only.split(","):
            continue
        sheet = next(s for s in frozen if s["ep"] == label["ep"] and s["relative_path"] == label["relative_path"])
        key = f"EP-{sheet['ep']}/{sheet['relative_path']}"
        extraction = stored.get(key) or extract(sheet)
        extractions[key] = extraction
        scored = score_sheet(label, extraction)
        scored["sha256_matches_frozen"] = extraction.get("sha256_matches_frozen")
        sheets.append(scored)
        print(key[-55:].ljust(55), scored["outcome"], scored["emitted"], {f: (v["tp"], v["accepted"], v["held"], v["missed"]) for f, v in scored["fields"].items()},
              "critical", len(scored["critical"]), flush=True)
    result = {"evaluator": BOQ_EVALUATOR_VERSION, "ai_enabled": False, "labels_corrections_applied": applied, "sheets": sheets, "totals": totals(sheets)}
    Path(args.out).write_text(json.dumps(result, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    Path(args.out).with_name(Path(args.out).stem + "-extraction.json").write_text(json.dumps(extractions, indent=1, default=str), encoding="utf-8")
    print(json.dumps(result["totals"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
