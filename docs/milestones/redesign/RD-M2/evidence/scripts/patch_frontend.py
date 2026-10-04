"""RD-M2 frontend: wording never presents a proposed change as placed/ready; spot confirmation; output states."""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
R = [
    ("""  confirm: boolean;
  box?: number[];""",
     """  // the spot is to be confirmed before it can be drawn (RD-M2)
  confirm: boolean;
  requires_confirmation?: boolean;
  confirmed?: boolean;
  box?: number[];"""),
    ("""  // the interface schedule's modules: drawn only once approved
  source?: string;""",
     """  // review change or interface module: either is drawn only once approved (RD-M2)
  source?: string;"""),
    ("""  output: { status: string; error: string | null; relative: string | null; file: string | null; at: string | null; changes: number };""",
     """  output: {
    status: string;
    error: string | null;
    relative: string | null;
    file: string | null;
    at: string | null;
    changes: number;
    available?: boolean;
  };"""),
    ("""            The reviewed IFC drawing, copied with the changes accepted on Drawings Review made on it. The AI (Opus 5.5) places
            every ADD, REMOVE and REPLACE on the plan with the drawing&rsquo;s own symbols; you approve, move or skip each one; AutoCAD
            then makes them on a copy of the DWG &mdash; each marked on an EP-REDESIGN layer &mdash; filed in the project folder for the
            draftsman. Every module of the FA Interface Schedule (CR, CT1, CT2 &mdash; the shop drawing&rsquo;s own blocks) is placed beside
            its equipment too, and drawn once you approve it.""",
     """            The reviewed IFC drawing, copied with the changes accepted on Drawings Review made on it. The AI (Opus 5.5) proposes
            where every ADD, REMOVE and REPLACE goes, with the drawing&rsquo;s own symbols; you approve, move or skip each one. Only the
            changes you approve are drawn: AutoCAD makes them on a copy of the DWG &mdash; each marked on an EP-REDESIGN layer &mdash;
            checks what it made, and keeps it as a new platform copy to download (it is not filed in the project folder). Every module
            of the FA Interface Schedule (CR, CT1, CT2 &mdash; the shop drawing&rsquo;s own blocks) is proposed beside its equipment too,
            and drawn only once you approve it."""),
    ("""              {applyJob.active ? "AutoCAD is drawing…" : `Make redesigned drawing (${ready})`}""",
     """              {applyJob.active ? "AutoCAD is drawing…" : `Make redesigned drawing (${ready} approved)`}"""),
    ("""              <div className="text-xs uppercase tracking-wide text-gray-500">{k === "proposed" ? "Placed, to approve" : k}</div>""",
     """              <div className="text-xs uppercase tracking-wide text-gray-500">
                {k === "proposed" ? "Proposed, not drawn until approved" : k === "approved" ? "Approved, to draw" : k}
              </div>"""),
    ("""            {data.output.status === "made" ? (
              <div className="mt-1 text-sm">
                <a href={apiUrl(`/projects/${project.id}/redesign/${drawingId}/output.dwg`)} className="font-semibold text-brand-600 hover:underline">
                  Download DWG
                </a>
                <div className="mt-0.5 break-all text-[11px] text-gray-500">
                  {data.output.changes} changes · {data.output.relative ? `filed in ${data.output.relative}` : "not filed (project folder not reachable)"}
                </div>
              </div>
            ) : data.output.status === "failed" ? (
              <div className="mt-1 text-xs text-red-700">{data.output.error}</div>
            ) : (""",
     """            {data.output.status === "made" && data.output.available !== false ? (
              <div className="mt-1 text-sm">
                <a href={apiUrl(`/projects/${project.id}/redesign/${drawingId}/output.dwg`)} className="font-semibold text-brand-600 hover:underline">
                  Download DWG
                </a>
                <div className="mt-0.5 break-all text-[11px] text-gray-500">
                  {data.output.changes} approved changes, checked · a platform copy, not filed in the project folder
                </div>
              </div>
            ) : data.output.status === "made" ? (
              <div className="mt-1 text-xs text-amber-700">Made, but the file is not on this PC</div>
            ) : ["failed", "stale", "cancelled", "interrupted"].includes(data.output.status) ? (
              <div className="mt-1 text-xs text-red-700">{data.output.error}</div>
            ) : data.output.status === "making" ? (
              <div className="mt-1 text-sm text-gray-500">Being made…</div>
            ) : ("""),
    ("""          {c.source === "interface" && c.status === "proposed" && (
            <span className="text-xs text-amber-700">drawn once approved</span>
          )}""",
     """          {c.status === "proposed" && <span className="text-xs text-amber-700">not drawn until approved</span>}
          {c.status === "approved" && c.drawn && <span className="text-xs text-green-700">will be drawn</span>}"""),
    ("""        {c.confirm && (
          <div className="mt-1 rounded bg-amber-50 px-2 py-1 text-xs text-amber-800">
            Placed within about ±{(c.residual ?? 1).toFixed(1)} m on this sheet: check the spot, or click the picture to set it.
          </div>
        )}""",
     """        {c.confirm && (
          <div className="mt-1 flex flex-wrap items-center gap-2 rounded bg-amber-50 px-2 py-1 text-xs text-amber-800">
            <span>
              Placed within about ±{(c.residual ?? 1).toFixed(1)} m on this sheet: not drawn until you confirm the spot, or click the
              picture to set it.
            </span>
            {canEdit && (
              <button
                onClick={() => onChange({ confirmed: true })}
                disabled={busy}
                className="rounded border border-amber-600 px-2 py-0.5 font-semibold text-amber-800 disabled:opacity-50"
              >
                Confirm this spot
              </button>
            )}
          </div>
        )}"""),
]
for a, b in R:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", p)
