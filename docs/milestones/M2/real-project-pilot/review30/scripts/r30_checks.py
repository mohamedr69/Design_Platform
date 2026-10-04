"""Review 30 (R30-01) package checks, importable and unit-tested (test_r30_checks.py).

check_commit_statements(texts, final_head, known_commits): every line of an owner-facing document that names a known
candidate commit and speaks of the candidate must name the FINAL candidate, unless the line marks that commit as
explicitly historical (first candidate commit, its patch, its contract freeze, its earlier test run). A line that names a
non-final commit together with "final" / "current" / "frozen candidate" is always a violation, historical marker or not.

check_test_counts(texts, junit_counts): every reported per-module test count ("`test_x.py` | N" in a table, or
"test_x.py ... N tests" in prose) must equal the count collected in the JUnit evidence; a module named with a count
but absent from the JUnit evidence is a violation; a reported suite total ("Review 29 tests (N)") must equal the sum."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

HISTORICAL = re.compile(r"\b(first candidate commit|historical|earlier run|earlier candidate|first commit|contract freeze|its patch|"
                        r"superseded|initial commit|revision 0)\b", re.I)
CURRENT = re.compile(r"\b(final|current|frozen candidate|the candidate is|candidate commit is)\b", re.I)
CANDIDATE = re.compile(r"\bcandidate\b", re.I)


def _short(commit: str) -> str:
    return commit[:7].lower()


def check_commit_statements(texts: dict, final_head: str, known_commits: list) -> list:
    final = _short(final_head)
    others = {_short(c) for c in known_commits} - {final}
    pat = re.compile(r"\b([0-9a-f]{7,40})\b", re.I)
    out = []
    for name, text in texts.items():
        for n, line in enumerate(text.splitlines(), 1):
            named = {_short(m.group(1)) for m in pat.finditer(line)} & (others | {final})
            stale = named & others
            if not stale:
                continue
            if CURRENT.search(line) and not (final in named and HISTORICAL.search(line)):
                out.append({"doc": name, "line": n, "why": "a non-final commit stated as final / current", "commits": sorted(stale), "text": line.strip()[:200]})
            elif CANDIDATE.search(line) and not HISTORICAL.search(line):
                out.append({"doc": name, "line": n, "why": "a non-final candidate commit without an explicit historical marker", "commits": sorted(stale),
                            "text": line.strip()[:200]})
    return out


def junit_module_counts(xml_path) -> dict:
    counts: dict = {}
    for case in ET.parse(xml_path).getroot().iter("testcase"):
        mod = (case.get("classname") or "").split(".")[-1]
        counts[mod] = counts.get(mod, 0) + 1
    return counts


TABLE = re.compile(r"`(?:[\w./-]*/)?(test_[A-Za-z0-9_]+)\.py`\s*\|\s*(?:New\.\s*)?(\d+)\b")
PROSE = re.compile(r"\b(test_[A-Za-z0-9_]+)\.py\b[^|\n]{0,60}?\b(\d+)\s+tests\b")
TOTAL = re.compile(r"Review 29 tests\s*\((\d+)")


def check_test_counts(texts: dict, junit_counts: dict, *, suite_prefix: str = "test_r29_") -> list:
    out = []
    expected_total = sum(v for k, v in junit_counts.items() if k.startswith(suite_prefix))
    for name, text in texts.items():
        for n, line in enumerate(text.splitlines(), 1):
            for m in list(TABLE.finditer(line)) + list(PROSE.finditer(line)):
                mod, cnt = m.group(1), int(m.group(2))
                if mod not in junit_counts:
                    out.append({"doc": name, "line": n, "module": mod, "reported": cnt, "junit": None, "why": "module not in the JUnit evidence"})
                elif junit_counts[mod] != cnt:
                    out.append({"doc": name, "line": n, "module": mod, "reported": cnt, "junit": junit_counts[mod], "why": "count differs from JUnit"})
            for m in TOTAL.finditer(line):
                if int(m.group(1)) != expected_total:
                    out.append({"doc": name, "line": n, "module": suite_prefix + "*", "reported": int(m.group(1)), "junit": expected_total,
                                "why": "suite total differs from JUnit"})
    return out
