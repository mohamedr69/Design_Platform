"""Every drawing primitive with the layer it is really drawn on, whether it
is shown, and where it is in the model (M8, ORCH-036).

Ported from the RD-M1 evidence script
docs/milestones/redesign/RD-M1/evidence/scripts/effective_layer.py (which
stays as it is):

  effective layer  AutoCAD draws an entity on layer "0" inside a block on the
                   layer of the INSERT that places it, recursively; any other
                   layer is the entity's own. BYBLOCK / BYLAYER change colour
                   and linetype, never the layer, so nothing more is needed.
  visibility       an entity is shown when its own invisible flag is off and
                   its effective layer is on, thawed and plottable (DEFPOINTS
                   never plots) -- and, for an index built for a paper-space
                   viewport, not frozen in that viewport (the VIEWPORT
                   entity's frozen-layer list). An INSERT above it hides it
                   by the AutoCAD rule (engineer decision 2, A-16): an
                   invisible INSERT, or one on a frozen layer (or one frozen
                   in the viewport), hides all its content; one on an off or
                   no-plot layer hides only the content it passes its layer
                   to (layer "0", reason insert_layer_off /
                   insert_layer_no_plot) -- content on its own layer is shown
                   by that layer.
  transform        the INSERT chain's matrices composed with
                   app.ifc.dxf.geometry.chain_matrix (translation, scale
                   including a mirror, rotation, base point), depth-capped,
                   a block inserting itself refused.
  title / frame    (engineer decision 1, A-16) content under a block whose own
                   name is a title block's, a sheet frame's or a border's
                   (FRAME_BLOCKS, settings.prep_frame_blocks) is no wall and
                   no room boundary; nor is layer-"0" content a dimension or
                   text block (ANNOTATION_BLOCKS, "DIM_TEXT") passes a wall
                   layer to. Reason title_frame.
  units            (engineer decision 3, A-16) the drawing's $INSUNITS gives
                   metres per drawing unit; a unitless drawing ($INSUNITS 0,
                   missing or not a length) has no known unit and what is
                   measured from it is held "not measured, units unknown"
                   (M3 P-07). $MEASUREMENT and $LUNITS are read and reported:
                   neither names a length unit by itself (GC-01 is in metres
                   with $MEASUREMENT 0, "imperial").

Nothing here writes to the drawing.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Callable, Iterator

MAX_DEPTH = 16              # nested INSERTs followed (GC-01's walls are 3-4 deep)
NO_PLOT_LAYERS = {"DEFPOINTS"}
# A bound xref's layer "X-REF_PLAN$0$06-WALL", an unbound one's "PLAN|06-WALL":
# the layer's own name is what follows.
XREF_PREFIX = re.compile(r"^.*(?:\$\d+\$|\|)")

# Why a segment is not a candidate, in the order they are decided.
REASONS = ("below_min_length", "invisible", "layer_frozen", "layer_off", "layer_no_plot", "viewport_frozen",
           "insert_invisible", "insert_layer_frozen", "insert_layer_off", "insert_layer_no_plot",
           "insert_viewport_frozen", "title_frame", "deny_listed", "not_allow_listed")
# An INSERT hidden for one of these hides all its content (AutoCAD: frozen,
# frozen in the viewport, the invisible flag); off and no-plot hide only the
# content that takes the INSERT's layer (engineer decision 2, A-16).
HIDES_ALL = {"invisible", "layer_frozen", "viewport_frozen"}

# Engineer decision 1 (A-16, option B): the block names, in the INSERT chain,
# of a title block, a sheet frame or a border -- everything under them is
# neither wall nor boundary (GC-01: CCSD > ...$0$T.FRAM inserted on 06-WALL).
# The default of settings.prep_frame_blocks; matched on the block's own name
# (a bound xref's prefix taken off, as the layers), case-insensitively.
FRAME_BLOCKS = r"T\.FRAM|TITLE|FRAME|BORDER|SHEET"
# ... and, the same treatment, layer-"0" content of a dimension / text block
# that its INSERT puts on a wall layer (GC-01: X-REF_ DIM_TEXT on 06-WALL).
ANNOTATION_BLOCKS = r"DIM|TEXT"

# Metres per drawing unit by $INSUNITS (the DXF reference's unit codes).
# 0 is unitless: no length unit is known.
INSUNITS_M = {1: 0.0254, 2: 0.3048, 3: 1609.344, 4: 0.001, 5: 0.01, 6: 1.0, 7: 1000.0, 8: 2.54e-8, 9: 2.54e-5,
              10: 0.9144, 11: 1e-10, 12: 1e-9, 13: 1e-6, 14: 0.1, 15: 10.0, 16: 100.0, 17: 1e9,
              18: 149597870700.0, 19: 9460730472580800.0, 20: 3.0856775814913673e16,
              21: 1200.0 / 3937.0, 22: 100.0 / 3937.0, 23: 3600.0 / 3937.0, 24: 6336000.0 / 3937.0}
UNIT_NAMES = {1: "in", 2: "ft", 3: "mi", 4: "mm", 5: "cm", 6: "m", 7: "km", 8: "uin", 9: "mil", 10: "yd",
              11: "angstrom", 12: "nm", 13: "um", 14: "dm", 15: "dam", 16: "hm", 17: "Gm", 18: "au", 19: "ly",
              20: "pc", 21: "us_ft", 22: "us_in", 23: "us_yd", 24: "us_mi"}


def drawing_units(doc) -> dict:
    """The drawing's length unit (engineer decision 3, A-16): metres per
    drawing unit from $INSUNITS, or `known` False -- the index built from it
    is then held "not measured, units unknown" (M3 P-07), never measured
    against a guessed unit."""
    header = doc.header

    def read(name):
        try:
            value = header.get(name)
            return None if value is None else int(value)
        except (TypeError, ValueError):
            return None

    insunits, measurement, lunits = read("$INSUNITS"), read("$MEASUREMENT"), read("$LUNITS")
    factor = INSUNITS_M.get(insunits) if insunits else None
    return {"insunits": insunits, "measurement": measurement, "lunits": lunits,
            "unit": UNIT_NAMES.get(insunits) if factor else None, "factor_to_m": factor, "known": factor is not None,
            "source": "$INSUNITS" if factor else None,
            "lengths_in": "m" if factor else "drawing units (units unknown: not converted)"}


def local_name(layer: str) -> str:
    """The layer's own name, a bound or unbound xref's prefix taken off."""
    return XREF_PREFIX.sub("", layer or "")


def effective_layer(raw: str | None, parent: str | None) -> str:
    raw = raw or "0"
    return parent if (raw == "0" and parent) else raw


class FrameRule:
    """Engineer decision 1 (A-16): whether a primitive is title-block, sheet-
    frame or border content (any block of its INSERT chain named so), or a
    dimension / text block's layer-"0" content -- reason "title_frame"."""

    def __init__(self, deny_blocks: str | None = None, annotation_blocks: str | None = None):
        if deny_blocks is None:
            from app.core.config import get_settings

            deny_blocks = get_settings().prep_frame_blocks
        self.deny_blocks = deny_blocks
        self.annotation_blocks = ANNOTATION_BLOCKS if annotation_blocks is None else annotation_blocks
        self._frame = re.compile(deny_blocks, re.I) if deny_blocks else None
        self._annotation = re.compile(self.annotation_blocks, re.I) if self.annotation_blocks else None
        self._seen: dict[tuple, str | None] = {}

    def rules(self) -> dict:
        return {"deny_blocks": self.deny_blocks, "annotation_blocks": self.annotation_blocks}

    def reason(self, item: "Item") -> str | None:
        if not item.chain:
            return None
        key = (item.chain, item.raw_layer == "0")
        if key not in self._seen:
            names = [local_name(b) for b in item.chain]
            hit = (self._frame is not None and any(self._frame.search(n) for n in names)) or (
                key[1] and self._annotation is not None and any(self._annotation.search(n) for n in names))
            self._seen[key] = "title_frame" if hit else None
        return self._seen[key]

    def blocks(self, item: "Item") -> list[str]:
        """The chain's block names the rule matched (for the evidence)."""
        out = []
        for b in item.chain:
            n = local_name(b)
            if (self._frame is not None and self._frame.search(n)) or (
                    item.raw_layer == "0" and self._annotation is not None and self._annotation.search(n)):
                out.append(b)
        return out


def is_mesh(entity) -> bool:
    """A polyface or polygon mesh (POLYLINE): explicitly not read as a line
    (engineer decision 7, A-16) -- counted as mesh_not_read, never dropped
    silently."""
    return entity.dxftype() == "POLYLINE" and not (entity.is_2d_polyline or entity.is_3d_polyline)


def mesh_kind(entity) -> str:
    return "polyface" if getattr(entity, "is_poly_face_mesh", False) else "polygon_mesh"


def mline_length(item: "Item") -> float:
    """An MLINE's reference-line length in drawing units, in the model."""
    e = item.entity
    points = [v.location for v in getattr(e, "vertices", [])]
    if item.matrix is not None and points:
        points = list(item.matrix.transform_vertices(points))
    if len(points) > 1 and e.is_closed:
        points.append(points[0])
    return sum(math.hypot(b.x - a.x, b.y - a.y) for a, b in zip(points, points[1:]))


class LayerTable:
    """The drawing's layer states, and the layers frozen in one viewport."""

    def __init__(self, doc, viewport_frozen=()):
        self.state: dict[str, tuple[bool, bool, bool]] = {}
        for layer in doc.layers:
            name = layer.dxf.name
            plot = bool(layer.dxf.get("plot", 1)) and name.upper() not in NO_PLOT_LAYERS
            self.state[name.upper()] = (layer.is_on(), layer.is_frozen(), plot)
        self.viewport_frozen = {n.upper() for n in viewport_frozen}

    def hidden(self, layer: str) -> str | None:
        """Why a layer is not shown, or None. A layer missing from the table
        is shown (AutoCAD creates it on, thawed, plottable)."""
        key = (layer or "0").upper()
        on, frozen, plot = self.state.get(key, (True, False, key not in NO_PLOT_LAYERS))
        if frozen:
            return "layer_frozen"
        if not on:
            return "layer_off"
        if not plot:
            return "layer_no_plot"
        if key in self.viewport_frozen:
            return "viewport_frozen"
        return None


def viewport_info(doc, handle: str) -> dict:
    """A paper-space VIEWPORT's frozen layers and view (centre, height, twist
    in degrees), by its handle."""
    vp = doc.entitydb.get(str(handle))
    if vp is None or vp.dxftype() != "VIEWPORT":
        raise ValueError(f"no VIEWPORT with handle {handle!r}")
    layout = None
    try:
        owner = doc.entitydb.get(vp.dxf.owner)
        layout = doc.layouts.get_layout_for_entity(vp).name if owner is not None else None
    except Exception:  # noqa: BLE001 -- the layout's name is only reported
        layout = None
    c = vp.dxf.get("view_center_point")
    return {"handle": str(handle), "layout": layout, "frozen_layers": sorted(vp.frozen_layers or []),
            "view_twist_deg": float(vp.dxf.get("view_twist_angle", 0.0) or 0.0),
            "view_center": [float(c.x), float(c.y)] if c is not None else None,
            "view_height": float(vp.dxf.get("view_height", 0.0) or 0.0)}


@dataclass
class Item:
    """One primitive met in the walk."""
    entity: object
    matrix: object | None          # block-to-model Matrix44, None at the top level
    layer: str                     # effective layer
    raw_layer: str
    reason: str | None             # why it is not shown, None when it is
    chain: tuple[str, ...]         # the block names above it, outermost first

    @property
    def via_insert(self) -> bool:
        return bool(self.chain)


@dataclass
class WalkStats:
    entities: int = 0
    inserts: int = 0
    depth_capped: int = 0
    self_inserts: int = 0
    missing_blocks: int = 0
    unreadable_inserts: int = 0
    kinds: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"entities": self.entities, "inserts": self.inserts, "depth_capped": self.depth_capped,
                "self_inserts": self.self_inserts, "missing_blocks": self.missing_blocks,
                "unreadable_inserts": self.unreadable_inserts, "kinds": dict(sorted(self.kinds.items()))}


def walk(doc, kinds: set[str], table: LayerTable, *, check: Callable | None = None,
         stats: WalkStats | None = None, max_depth: int = MAX_DEPTH) -> Iterator[Item]:
    """Every entity of the given kinds in model space, at any depth up to
    `max_depth` INSERTs, with its effective layer, visibility and matrix."""
    from app.ifc.dxf.geometry import chain_matrix

    stats = stats if stats is not None else WalkStats()

    def visit(entities, parent_m, parent_layer, chain_reason, chain, upper_chain, depth):
        for e in entities:
            stats.entities += 1
            if check and stats.entities % 20000 == 0:
                check()
            kind = e.dxftype()
            raw = e.dxf.get("layer", "0") or "0"
            eff = effective_layer(raw, parent_layer)
            own = "invisible" if e.dxf.get("invisible", 0) else table.hidden(eff)
            if own and own != "invisible" and raw == "0" and parent_layer:
                # its layer is its INSERT's: the INSERT's layer state is what hides it
                own = f"insert_{own}"
            if kind == "INSERT":
                stats.inserts += 1
                name = e.dxf.name
                if name.upper() in upper_chain:
                    stats.self_inserts += 1
                    continue
                if depth >= max_depth:
                    stats.depth_capped += 1
                    continue
                block = doc.blocks.get(name)
                if block is None:
                    stats.missing_blocks += 1
                    continue
                # frozen / viewport-frozen / invisible hide the whole block; off and
                # no-plot reach only the content that takes this INSERT's layer
                base = own[len("insert_"):] if own and own.startswith("insert_") else own
                reason = chain_reason or (f"insert_{base}" if base in HIDES_ALL else None)
                try:
                    copies = list(e.multi_insert()) if e.mcount > 1 else [e]
                except Exception:  # noqa: BLE001 -- an array that cannot be expanded is read once
                    copies = [e]
                for ins in copies:
                    try:
                        m = chain_matrix(ins, parent_m)
                    except Exception:  # noqa: BLE001 -- a degenerate insert places nothing
                        stats.unreadable_inserts += 1
                        continue
                    yield from visit(block, m, eff, reason, chain + (name,), upper_chain | {name.upper()},
                                     depth + 1)
                continue
            if kind not in kinds:
                continue
            stats.kinds[kind] = stats.kinds.get(kind, 0) + 1
            yield Item(e, parent_m, eff, raw, own or chain_reason, chain)

    yield from visit(doc.modelspace(), None, None, None, (), frozenset(), 0)


FLATTEN = 0.01             # an arc's chords stray at most this far from it (block units)


def model_vertices(item: Item) -> list:
    """The primitive's flattened vertices in model coordinates (Vec3), or []
    when it cannot be read: its centre line (ezdxf.path), so a polyline drawn
    with a width is its line, not the outline of its width (which
    disassemble.make_primitive returns, and walls.py v1 indexed). A polyface
    or polygon mesh is not a line."""
    from ezdxf import path

    e = item.entity
    if e.dxftype() == "POLYLINE" and not (e.is_2d_polyline or e.is_3d_polyline):
        return []
    try:
        vertices = list(path.make_path(e).flattening(FLATTEN))
    except Exception:  # noqa: BLE001 -- a line that cannot be read is no line here
        return []
    if item.matrix is not None and vertices:
        vertices = list(item.matrix.transform_vertices(vertices))
    return vertices
