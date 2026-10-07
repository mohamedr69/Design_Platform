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
                   entity's frozen-layer list) -- and every INSERT above it
                   is shown by the same rule (ORCH-036 item 3: an INSERT on an
                   off layer hides its whole content here, which is stricter
                   than AutoCAD for content on explicit layers; see the M8
                   implementation report).
  transform        the INSERT chain's matrices composed with
                   app.ifc.dxf.geometry.chain_matrix (translation, scale
                   including a mirror, rotation, base point), depth-capped,
                   a block inserting itself refused.

Nothing here writes to the drawing.
"""
from __future__ import annotations

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
           "insert_viewport_frozen", "deny_listed", "not_allow_listed")


def local_name(layer: str) -> str:
    """The layer's own name, a bound or unbound xref's prefix taken off."""
    return XREF_PREFIX.sub("", layer or "")


def effective_layer(raw: str | None, parent: str | None) -> str:
    raw = raw or "0"
    return parent if (raw == "0" and parent) else raw


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
                reason = chain_reason or (f"insert_{own}" if own else None)
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
