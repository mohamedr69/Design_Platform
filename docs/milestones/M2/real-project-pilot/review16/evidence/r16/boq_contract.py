"""R14-02: the typed BOQ comparison and truth-join contract for the Round 2 exploration harness (replaces the lossy
comparison and first-candidate join of the submitted r2x_boq.py; the application's evidence_reader is not changed).

CONTRACT_VERSION r2x-boq-contract-2026-09-30.r16.1  (r15.1 preserved in the Review 15 package; value comparisons unchanged;
R16-01: verified rows bound every fallback match -- see join_rows)

Part identifiers (`part_state`, `parts_equal`)
  * absent  : None, empty or whitespace only (a blank part cell). Two absent parts are equal ("a blank cell stays blank").
  * literal : upper case with whitespace removed (line wraps), EVERY other character kept -- '+', '-', '/', '.' are
              meaningful: PT-1S != PT-1S+ (the same literal rule as evidence_reader.part_literal).
Quantities (`parse_quantity`, `quantities_equal`)
  * absent     : None / empty. NOT equal to numeric zero ("0 is present, never absent").
  * unreadable : an explicit unreadable marker ('?', 'unreadable', 'illegible').
  * number     : optional sign, digits, optional decimal part; thousands separators accepted only in the strict
                 1,234 / 1,234,567 form; an optional unit word after the number. Compared as Decimal:
                 1 == 1.0, 1.0 != 10, -1 != 1, 0 != absent.
                 Units: a count unit (no, nos, no., pc, pcs, ea, each, unit, units, nr) or no unit are the same unit;
                 any other unit must match exactly (case-insensitive).
  * text       : anything else (e.g. '1,5', 'LS', '2 sets of 3'); equal only as the same literal (upper, whitespace
                 collapsed). A text value is never equal to a number.
Truth join (`join_rows`) -- R15-02: alignment never uses a SCORED value (part number or quantity)
  * per source document hash and page;
  * 1. GEOMETRY first: a truth row that carries a VERIFIED row position ('y', same render scale as the emitted rows)
       is paired with the one emitted row within GEOMETRY_TOLERANCE of it ('matched_geometry'); two candidates on either
       side -> held; a verified truth row with no emitted row near it is MISSED (it is never offered to another row);
  * 2. the rest: truth rows in print order and emitted rows in geometry (y) order, aligned one-to-one and
       order-preserving on DESCRIPTION similarity only (token Jaccard >= 0.5; the description is not a scored field);
  * 3. a pair is HELD ('ambiguous', with every equally good truth candidate listed) when an equally good alignment gives
       the emitted row another truth row -- e.g. a single emitted duplicate of two identical source rows. Held candidates
       are reported, never resolved by a value; unmatched rows on both sides stay visible.
  Consequence: a quantity misread can no longer select the truth row that makes it correct (Review 15 probe).
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

CONTRACT_VERSION = "r2x-boq-contract-2026-09-30.r16.1"
COUNT_UNITS = {"no", "nos", "no.", "nos.", "pc", "pcs", "ea", "each", "unit", "units", "nr", "number"}
UNREADABLE = {"?", "unreadable", "illegible"}
_NUM = re.compile(r"^([+-]?)(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?\s*([A-Za-z][A-Za-z.]*)?$")


# --- parts -----------------------------------------------------------------------------------------------------------
def part_state(value) -> tuple[str, str | None]:
    if value is None or not str(value).strip():
        return "absent", None
    return "literal", re.sub(r"\s+", "", str(value).upper())


def parts_equal(a, b) -> bool:
    return part_state(a) == part_state(b)


# --- quantities ------------------------------------------------------------------------------------------------------
def parse_quantity(value) -> tuple:
    """('absent',) | ('unreadable',) | ('number', Decimal, unit|None) | ('text', literal)."""
    if value is None:
        return ("absent",)
    if isinstance(value, bool):
        return ("text", str(value).upper())
    if isinstance(value, (int, float, Decimal)):
        return ("number", Decimal(str(value)), None)
    s = str(value).strip()
    if not s:
        return ("absent",)
    if s.lower() in UNREADABLE:
        return ("unreadable",)
    m = _NUM.match(s)
    if m:
        sign, whole, frac, unit = m.groups()
        try:
            number = Decimal(f"{sign}{whole.replace(',', '')}{'.' + frac if frac else ''}")
        except InvalidOperation:
            return ("text", re.sub(r"\s+", " ", s.upper()))
        unit = unit.lower() if unit else None
        return ("number", number, None if unit in COUNT_UNITS else unit)
    return ("text", re.sub(r"\s+", " ", s.upper()))


def quantities_equal(a, b) -> bool:
    pa, pb = parse_quantity(a), parse_quantity(b)
    if pa[0] != pb[0]:
        return False
    if pa[0] == "number":
        return pa[1] == pb[1] and pa[2] == pb[2]
    if pa[0] == "text":
        return pa[1] == pb[1]
    return pa[0] == "absent"          # absent == absent; unreadable is never 'equal' to anything


# --- descriptions (alignment evidence only; never scored) ------------------------------------------------------------
def _tokens(text) -> set:
    return set(re.findall(r"[a-z0-9]+", str(text or "").lower()))


def description_similarity(a, b) -> float:
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


# --- the join --------------------------------------------------------------------------------------------------------
GEOMETRY_TOLERANCE = 22.0      # render pixels at the extractor's dpi (rows are ~45 px apart on the EP-8430 sheet)


def _pair_score(e: dict, t: dict) -> float:
    """Alignment evidence: description similarity only -- NOT the part number or the quantity (both are scored)."""
    sim = description_similarity(e.get("description"), t.get("description"))
    return sim if sim >= 0.5 else 0.0


def _align(emitted: list[dict], truth: list[dict], forbid: frozenset = frozenset()) -> tuple[float, list]:
    n, m = len(emitted), len(truth)
    best = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            s = _pair_score(emitted[i], truth[j])
            take = s + best[i + 1][j + 1] if s > 0 and (i, j) not in forbid else float("-inf")
            best[i][j] = max(take, best[i + 1][j], best[i][j + 1])
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        s = _pair_score(emitted[i], truth[j])
        if s > 0 and (i, j) not in forbid and abs(best[i][j] - (s + best[i + 1][j + 1])) < 1e-9:
            pairs.append((i, j))
            i, j = i + 1, j + 1
        elif abs(best[i][j] - best[i + 1][j]) < 1e-9:
            i += 1
        else:
            j += 1
    return best[0][0], pairs


def _candidates(e, t, i, j, score) -> list:
    """Every truth index the emitted row i takes in some equally good alignment (j first); None = unpaired equally well."""
    cands, forbid = [j], {(i, j)}
    while True:
        alt, pairs = _align(e, t, frozenset(forbid))
        if abs(alt - score) > 1e-9:
            return cands
        mine = [jj for ii, jj in pairs if ii == i]
        if not mine:
            return cands + [None]
        cands.append(mine[0])
        forbid.add((i, mine[0]))


def join_rows(emitted: list[dict], truth: list[dict], tolerance: float = GEOMETRY_TOLERANCE) -> dict:
    """emitted: rows with 'page', 'y' (geometry), 'part_number', 'quantity', 'description' and an 'id';
    truth: label rows of kind 'line' with 'page', 'ordinal' (print order), 'description' and, when VERIFIED, 'y'.
    Returns {'pairs': [(emitted id, truth ordinal, 'matched_geometry'|'matched'|'ambiguous')],
             'held': {emitted id: [candidate truth ordinals]}, 'held_reasons': {emitted id: reason},
             'unmatched_emitted': [...], 'unmatched_truth': [...], 'intervals': {page: [...]}}.

    R16-01 contract (r16.1): every VERIFIED truth row is a boundary for the whole page, whether or not an emitted row
    was matched to it. Truth rows without a position are placed in the interval between the verified rows that
    enclose them in print order; emitted rows (not consumed by geometry) in the interval between the verified
    positions that enclose them. A fallback (description) match is only possible INSIDE the same interval, so no
    confirmed association crosses a verified row. Verified positions that contradict print order are not used to
    guess: every emitted row of that page is held (reason 'verified positions contradict print order')."""
    out = {"pairs": [], "held": {}, "held_reasons": {}, "unmatched_emitted": [], "unmatched_truth": [], "intervals": {}}
    for page in sorted({r["page"] for r in emitted} | {r["page"] for r in truth}):
        e_all = sorted([r for r in emitted if r["page"] == page], key=lambda r: r["y"])
        t_all = sorted([r for r in truth if r["page"] == page], key=lambda r: r["ordinal"])
        anchors = [t for t in t_all if t.get("y") is not None]                 # print order
        if any(anchors[k]["y"] >= anchors[k + 1]["y"] for k in range(len(anchors) - 1)):
            for x in e_all:
                out["held"][x["id"]] = [t["ordinal"] for t in t_all]
                out["held_reasons"][x["id"]] = "verified positions contradict print order"
            out["unmatched_truth"] += []
            continue
        # 1. verified geometry (physical identity), exactly as r15.1
        used_e = set()
        for t in anchors:
            near = [x for x in e_all if abs(x["y"] - t["y"]) <= tolerance]
            back = [tt for tt in anchors if near and abs(near[0]["y"] - tt["y"]) <= tolerance]
            if len(near) == 1 and len(back) == 1:
                out["pairs"].append((near[0]["id"], t["ordinal"], "matched_geometry"))
                used_e.add(near[0]["id"])
            elif len(near) > 1 or len(back) > 1:
                for x in near:
                    out["held"].setdefault(x["id"], []).append(t["ordinal"])
                    out["held_reasons"][x["id"]] = "geometry: more than one emitted row within tolerance of a verified row"
                    used_e.add(x["id"])
            else:
                out["unmatched_truth"].append(t["ordinal"])                  # verified position, nothing emitted there: missed
        # 2. intervals bounded by EVERY verified row (matched or not)
        a_ord = [t["ordinal"] for t in anchors]
        a_y = [t["y"] for t in anchors]
        n_int = len(anchors) + 1
        t_int = [[] for _ in range(n_int)]
        e_int = [[] for _ in range(n_int)]
        for t in t_all:
            if t.get("y") is None:
                t_int[sum(1 for o in a_ord if o < t["ordinal"])].append(t)
        for x in e_all:
            if x["id"] not in used_e:
                e_int[sum(1 for y in a_y if y < x["y"])].append(x)
        out["intervals"][page] = [{"interval": k, "truth": [t["ordinal"] for t in t_int[k]], "emitted": [x["id"] for x in e_int[k]]} for k in range(n_int)]
        # 3. fallback inside each interval only: order + description (never a scored value); ties held
        for k in range(n_int):
            e, t = e_int[k], t_int[k]
            if not e or not t:
                out["unmatched_emitted"] += [x["id"] for x in e]
                out["unmatched_truth"] += [x["ordinal"] for x in t]
                continue
            score, pairs = _align(e, t)
            paired_e, paired_t = set(), set()
            for i, j in pairs:
                cands = _candidates(e, t, i, j, score)
                if len(cands) == 1:
                    out["pairs"].append((e[i]["id"], t[j]["ordinal"], "matched"))
                    paired_t.add(j)
                else:
                    out["pairs"].append((e[i]["id"], t[j]["ordinal"], "ambiguous"))
                    out["held"][e[i]["id"]] = [t[c]["ordinal"] for c in cands if c is not None]
                    out["held_reasons"][e[i]["id"]] = f"fallback: an equally good alignment inside interval {k}"
                    paired_t.update(c for c in cands if c is not None)
                paired_e.add(i)
            out["unmatched_emitted"] += [e[i]["id"] for i in range(len(e)) if i not in paired_e]
            out["unmatched_truth"] += [t[j]["ordinal"] for j in range(len(t)) if j not in paired_t]
    return out


# --- the submitted (old) expressions, kept verbatim for the before / after demonstration ------------------------------
def old_norm(text):
    """app.ai.evidence_reader.norm as the submitted r2x_boq.py used it (see tests: the import is compared to this)."""
    from app.ai.evidence_reader import norm
    return norm(text)


def old_values_equal(a, b) -> bool:
    return old_norm(a) == old_norm(b)


def old_join(pairs: list[dict], r: dict) -> list[dict]:
    """The submitted join (r2x_boq.py lines 142-154): value match on page / part / quantity / accepted, then a
    12-character description prefix, then the first candidate."""
    norm = old_norm
    row = r["row"]
    match = [p for p in pairs if p.get("emitted") and int(p.get("page") or (p.get("emitted") or {}).get("page") or 0) == int(r["page"])
             and norm(p["emitted"].get("part_number")) == norm(row.get("part_number"))
             and norm(p["emitted"].get("quantity")) == norm(row.get("quantity"))
             and bool(p["emitted"].get("accepted")) == bool(r.get("accepted_by_reader"))]
    if len(match) > 1:
        match = [p for p in match if norm(p["emitted"].get("description"))[:12] == norm(row.get("description"))[:12]] or match[:1]
    return match
