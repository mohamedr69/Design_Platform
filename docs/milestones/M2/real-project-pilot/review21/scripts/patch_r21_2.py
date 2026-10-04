"""R21 patch 2 (before freeze): the derived switches resolve at USE time, so the reviewed legacy implications hold whether
a configuration comes from the environment or from a test that sets the legacy attributes (T => support v2 + required-
first; E => ROI + deadline). Identity strings are still computed at import from the environment (unchanged)."""
import pathlib

P = pathlib.Path("C:/t/iso/cand-ai4/backend/app/ai/evidence_reader.py")
s = P.read_bytes().decode("utf-8").replace("\r\n", "\n")


def sub(old, new, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:90])
    s = s.replace(old, new)


sub('''SUPPORT_V2 = _os.environ.get("AI_EVIDENCE_SUPPORT") == "v2" or TARGETED_ENABLED
REQUIRED_FIRST = _os.environ.get("AI_EVIDENCE_SCHEDULING") == "required_first" or TARGETED_ENABLED
DEADLINE_ENABLED = _os.environ.get("AI_EVIDENCE_DEADLINE") == "1" or EFFICIENT_ENABLED
ROI_ENABLED = _os.environ.get("AI_EVIDENCE_ROI") == "1" or EFFICIENT_ENABLED
''', '''SUPPORT_V2 = _os.environ.get("AI_EVIDENCE_SUPPORT") == "v2" or TARGETED_ENABLED
REQUIRED_FIRST = _os.environ.get("AI_EVIDENCE_SCHEDULING") == "required_first" or TARGETED_ENABLED
DEADLINE_ENABLED = _os.environ.get("AI_EVIDENCE_DEADLINE") == "1" or EFFICIENT_ENABLED
ROI_ENABLED = _os.environ.get("AI_EVIDENCE_ROI") == "1" or EFFICIENT_ENABLED


# the switches in force at USE time (the legacy implications hold whether the attributes were set by the environment at
# import or by a test afterwards): T => support v2 + required-first; E => ROI + deadline
def _support_v2() -> bool:
    return SUPPORT_V2 or TARGETED_ENABLED


def _required_first() -> bool:
    return REQUIRED_FIRST or TARGETED_ENABLED


def _deadline() -> bool:
    return DEADLINE_ENABLED or EFFICIENT_ENABLED


def _roi() -> bool:
    return ROI_ENABLED or EFFICIENT_ENABLED
''')
sub('''        timeout_s = None
        if DEADLINE_ENABLED:''', '''        timeout_s = None
        if _deadline():''')
sub('''    if SUPPORT_V2:
        return region_texts_v2(page, region, ocr_lines or [], ocr_timeout=_ocr_timeout(run))''',
    '''    if _support_v2():
        return region_texts_v2(page, region, ocr_lines or [], ocr_timeout=_ocr_timeout(run))''')
sub('''    if not DEADLINE_ENABLED or run is None:''', '''    if not _deadline() or run is None:''')
sub('''        before = run.calls
        if REQUIRED_FIRST:
            found = _read_page_required(''', '''        before = run.calls
        if _required_first():
            found = _read_page_required(''')
sub('''    if REQUIRED_FIRST:
        ctx = _read_page_required(run, page, sha256=sha256, number=number, facts=facts, reason=reason, ocr_lines=ocr_lines)''',
    '''    if _required_first():
        ctx = _read_page_required(run, page, sha256=sha256, number=number, facts=facts, reason=reason, ocr_lines=ocr_lines)''')
sub('''    """(discovered, located) -- `located` None when the page was discovered whole (always with ROI off)."""
    if ROI_ENABLED:''', '''    """(discovered, located) -- `located` None when the page was discovered whole (always with ROI off)."""
    if _roi():''')
sub('''    return discovered, ({"located": False, "route": "full_page"} if ROI_ENABLED else None)''',
    '''    return discovered, ({"located": False, "route": "full_page"} if _roi() else None)''')
for name in ("SUPPORT_V2", "REQUIRED_FIRST", "DEADLINE_ENABLED", "ROI_ENABLED"):
    body = s.split("MIN_REQUEST_S = ", 1)[1]          # after the import-time identity block: no direct use may remain
    assert f"if {name}" not in body and f"if not {name}" not in body and f"else {name}" not in body, name
P.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("R21 patch 2 applied")
