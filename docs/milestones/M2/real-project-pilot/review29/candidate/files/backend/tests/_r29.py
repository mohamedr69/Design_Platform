"""Shared helpers for the Review 29 tests: explicit switch sets (every switch named, none implied), identities computed
by a fresh interpreter, synthetic pages built from structure (no stored document, no expected string copied from a
label file). No model, no network."""
from __future__ import annotations

import functools
import io
import json
import os
import subprocess
import sys

import pymupdf
import pytest
from PIL import Image, ImageDraw

from app.ai import evidence_reader as er

from .test_ai_pilot_r19 import _font

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_ENV = {"AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first", "AI_EVIDENCE_DEADLINE": "1"}
NEW = {"ig": "AI_EVIDENCE_IDGUARD", "ca": "AI_EVIDENCE_ADJUDICATE", "dr": "AI_EVIDENCE_DECISION_REGION", "pa": "AI_EVIDENCE_ASSOC"}


@functools.lru_cache(maxsize=None)
def _identities(env_items: tuple) -> tuple:
    base = {k: v for k, v in os.environ.items() if not k.startswith("AI_EVIDENCE_")}
    code = "import json; from app.ai import evidence_reader as er; print(json.dumps([er.READER_VERSION, er.EVIDENCE_POLICY_VERSION, er.PROMPTS]))"
    out = subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env={**base, "AI_ENABLED": "false", **dict(env_items)}, capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr.strip().splitlines()[-1])
    return tuple(json.loads(out.stdout.strip().splitlines()[-1]))


def identities(env: dict) -> tuple:
    return _identities(tuple(sorted(env.items())))


def env_for(*, roi=False, x=False, ig=False, ca=False, dr=False, pa=False) -> dict:
    env = dict(BASE_ENV)
    if roi:
        env["AI_EVIDENCE_ROI"] = "1"
    if x:
        env["AI_EVIDENCE_TARGETED"] = "1"
    for name, on in (("ig", ig), ("ca", ca), ("dr", dr), ("pa", pa)):
        if on:
            env[NEW[name]] = "1"
    return env


def configure(monkeypatch, **switches) -> tuple:
    """Set every reader switch explicitly (the R21 pattern) and the identities a fresh process derives for that set."""
    env = env_for(**switches)
    reader, policy, prompts = identities(env)
    for k, v in (("GUARD_ENABLED", True), ("SUPPORT_V2", True), ("REQUIRED_FIRST", True), ("DEADLINE_ENABLED", True), ("EFFICIENT_ENABLED", False),
                 ("ROI_ENABLED", bool(switches.get("roi"))), ("TARGETED_ENABLED", bool(switches.get("x"))),
                 ("IDGUARD_ENABLED", bool(switches.get("ig"))), ("ADJUDICATE_ENABLED", bool(switches.get("ca"))),
                 ("DECISION_REGION_ENABLED", bool(switches.get("dr"))), ("ASSOC_ENABLED", bool(switches.get("pa"))),
                 ("READER_VERSION", reader), ("EVIDENCE_POLICY_VERSION", policy)):
        monkeypatch.setattr(er, k, v)
    monkeypatch.setattr(er, "PROMPTS", dict(prompts))
    return reader, policy


def text_page(lines, *, width=595, height=842, rotation=0, doc=None):
    """A page with a text layer; lines: (x_frac, y_frac, text, fontsize) in DISPLAYED coordinates."""
    doc = doc or pymupdf.open()
    page = doc.new_page(width=width, height=height)
    if rotation:
        page.set_rotation(rotation)
    W, H = page.rect.width, page.rect.height
    for x, y, t, size in lines:
        p = pymupdf.Point(W * x, H * y) * page.derotation_matrix
        page.insert_text(p, t, fontsize=size, rotate=rotation)
    return doc


def png(lines, size=(640, 180), font=30):
    img = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, size[0] - 3, size[1] - 3], outline="black", width=3)
    for i, t in enumerate(lines):
        d.text((14, 12 + i * (font + 10)), t, fill="black", font=_font(font))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def scan_with_stamp(stamp_lines, *, rotation=0, at=(0.62, 0.08)):
    """A wholly scanned A1-sized sheet (no text layer) with a raster consultant stamp at `at` (displayed fractions),
    outside the title-block zone's bottom strip."""
    W, H = 2384, 1684
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    for i, t in enumerate(["PROJECT EXAMPLE", "DWG NO. QQ-77-01", "REV 01"]):
        d.text((int(W * 0.80), int(H * 0.86) + i * 34), t, fill="black", font=_font(26))
    stamp = Image.open(io.BytesIO(png(stamp_lines)))
    img.paste(stamp, (int(W * at[0]), int(H * at[1])))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    doc = pymupdf.open()
    page = doc.new_page(width=W, height=H)
    page.insert_image(page.rect, stream=buf.getvalue())
    if rotation:
        page.set_rotation(rotation)
    return doc


def norm_region(page, literal, *, pad=3):
    """The literal's displayed rectangle as 0..1000 of the page image (what a reader of the whole page would give)."""
    r = page.search_for(literal)[0] * page.rotation_matrix
    w, h = page.rect.width, page.rect.height
    return [max(0, int(r.x0 / w * 1000) - pad), max(0, int(r.y0 / h * 1000) - pad), min(1000, int(r.x1 / w * 1000) + pad), min(1000, int(r.y1 / h * 1000) + pad)]


def frac_region(x0, y0, x1, y1):
    return [int(x0 * 1000), int(y0 * 1000), int(x1 * 1000), int(y1 * 1000)]


def discovery(**kw) -> dict:
    base = {"page_kind": "other", "own_identity": "", "own_identity_label": "", "own_identity_region": [], "own_revision": "", "own_revision_label": "",
            "own_revision_region": [], "decision_options_printed": [], "decision_marked_option": "", "decision_mark_type": "none",
            "decision_actor": "unknown", "decision_region": [], "other_numbers": [], "notes": ""}
    return {**base, **kw}


def value_read(value, label="", legible=True):
    return {"label_text": label, "value": value, "legible": legible, "other_values_in_crop": []}


def context_read(value, label, role, region=(0, 0, 1000, 1000), legible=True):
    return {"value": value, "printed_label": label, "role": role, "region": list(region), "legible": legible}


def decision_read(marked, options, *, mark="stamp", actor="consultant", legible=True):
    return {"options_printed": list(options), "marked_option": marked, "mark_type": mark, "actor": actor, "legible": legible}


@pytest.fixture(autouse=False)
def no_submittal_reader(monkeypatch):
    from app.ai import submittal_reader
    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)


def envelope_obs(stage, ai, *, field=None, page=None, component="own", raw=False):
    """The observations the evaluator would see: the merged envelope for the stage's context, through evidence_for."""
    got = er.evidence_for(ai, sha256=stage.sha, profile="default", variant="EV1")
    assert got["state"] == "current", got
    return [o for o in got["envelope"]["observations"] if (field is None or o.get("field") == field)
            and (page is None or int(o.get("page") or 1) == page) and (component is None or o.get("component") == component)]
