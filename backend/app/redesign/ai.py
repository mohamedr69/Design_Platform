"""What the model is asked for each change: where it goes on the plan, and
which symbol -- the drawing's own -- it is.

The model sees a piece of the plotted plan around the change (a red ring
where the review put it, the existing symbols nearby numbered in blue),
the drawing's legend, and the change as the engineer accepted it. It
answers in fractions of that image and in the numbers and symbol ids it
was given -- never in drawing coordinates, which the platform works out.
"""
from __future__ import annotations

PROMPT_VERSION = "drawing-redesign-2026-10-02.4"
TASK = "fa_drawing_redesign"

SYSTEM = """You redesign a fire alarm IFC floor plan for a fire alarm contractor in the UAE: the engineer has accepted a
change from the drawing review, and you decide exactly where it is drawn, so the draftsman's copy of the drawing
can be made from your answer.

You are shown a piece of the plotted floor plan around the change -- the red ring is roughly where the review put it
-- with the existing device symbols nearby marked with blue numbers, the drawing's own legend, the change, and the
symbols this drawing uses (id: name).

ADD: choose the symbol (its id) and the exact point on THIS image (x, y as fractions 0..1 of its width and height,
from the top-left) where it goes.
- Ceiling devices (smoke / heat / multi detectors, ceiling speakers, ceiling emergency lights): inside the room the
  change names, clear of walls, doors, text and other symbols, about central to the area it covers.
- Wall devices (manual call points, wall speakers, speaker- or sounder-flashers, fire telephone jacks, wall emergency
  lights): on the inside face of a wall of that room -- beside the door for call points and telephone jacks -- never
  in a door swing, a window or a corridor's middle.
- Exit signs above the exit door; directional signs on the wall or ceiling where the route turns, arrow along it.
- Several devices added at one door (a call point and a sounder flasher) go side by side on the wall, never on top
  of each other or of an existing symbol; the platform keeps the new ones clear of each other, so place each where
  it belongs.
- facing: the way a wall device faces -- away from its wall, into the room -- as up, down, left or right on THIS
  image; none for ceiling devices. (The platform turns each symbol to it.)
REMOVE: the numbered symbol to delete (candidate); 0 if none of the numbered ones is the device meant.
REPLACE: the numbered symbol to replace (candidate) and the symbol it becomes (its id).
symbol 0 when no symbol in the list is the device: the draftsman will draw it at your point.
For REMOVE give x, y of the symbol you chose (or -1, -1). Be careful: confidence low, with the reason in note (at most
20 words), whenever you are not sure; never invent a candidate number or a symbol id."""

SCHEMA = {
    "type": "object",
    "properties": {
        "candidate": {"type": "integer"},
        "symbol": {"type": "integer"},
        "x": {"type": "number"},
        "y": {"type": "number"},
        "facing": {"type": "string", "enum": ["none", "up", "down", "left", "right"]},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "note": {"type": "string"},
    },
    "required": ["candidate", "symbol", "x", "y", "facing", "confidence", "note"],
    "additionalProperties": False,
}


def read_answer(data: dict, candidates: int, symbols: set[int]) -> dict:
    """The answer, kept only where it is well formed: a candidate number
    the image had, a symbol id the list had, a point inside the image."""
    def num(key, default):
        try:
            return float(data.get(key, default))
        except (TypeError, ValueError):
            return default

    candidate = int(num("candidate", 0))
    symbol = int(num("symbol", 0))
    x, y = num("x", -1), num("y", -1)
    rotation = num("rotation", 0) % 360
    facing = data.get("facing") if data.get("facing") in ("up", "down", "left", "right") else None
    return {
        "facing": facing,
        "candidate": candidate if 1 <= candidate <= candidates else 0,
        "symbol": symbol if symbol in symbols else 0,
        "x": x if 0 <= x <= 1 else None,
        "y": y if 0 <= y <= 1 else None,
        "rotation": min((0, 90, 180, 270, 360), key=lambda r: abs(r - rotation)) % 360,
        "confidence": data.get("confidence") if data.get("confidence") in ("high", "medium", "low") else "low",
        "note": str(data.get("note") or "")[:200],
    }
