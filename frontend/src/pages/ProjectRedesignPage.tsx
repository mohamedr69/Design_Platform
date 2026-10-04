/** Drawings Redesign: the reviewed fire alarm IFC drawing, copied with the
 * accepted changes made on it (app.redesign).
 *
 * 1. Plan: every accepted ADD / REMOVE / REPLACE of the Drawings Review is
 *    placed by the model -- the point, the drawing's own symbol to insert,
 *    the existing symbol to erase.
 * 2. Adjust: the engineer approves each one, moves it (a click on its
 *    picture), picks another symbol, or skips it.
 * 3. Make: AutoCAD makes the changes on a copy of the DWG, each marked on an
 *    EP-REDESIGN layer, filed in the project folder for the draftsman. */
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "../context/AuthContext";
import { ApiError, api, apiUrl } from "../lib/api";
import { PROJECT_EDITOR_ROLES } from "../lib/types";
import { useJob, type Job } from "../lib/useJob";
import { useProject } from "./ProjectWorkspace";

interface DrawingRow {
  id: number;
  filename: string;
  revision: string;
  review_status: string | null;
  redesign_status: string;
  output_status: string;
}

interface Candidate {
  n: number;
  name: string;
  block: string;
  erasable: boolean;
}

interface Placed {
  symbol?: number;
  name: string;
  block: string | null;
  rotation: number;
  page: number[];
}

interface Change {
  id: string;
  page: number;
  sheet: string;
  floor: string;
  room: string;
  system_name: string;
  action: "add" | "remove" | "replace";
  device: string;
  instruction: string;
  status: "pending" | "proposed" | "approved" | "skipped" | "failed";
  candidates: Candidate[];
  remove: (Candidate & { page: number[] }) | null;
  insert: Placed | null;
  placeholder: boolean;
  note: string;
  error: string | null;
  moved: boolean;
  confidence: string | null;
  residual: number | null;
  confirm: boolean;
  box?: number[];
  // the interface schedule's modules: drawn only once approved
  source?: string;
  interface?: { code: string; for: string; equipment: string; tag: string };
  drawn?: boolean;
}

interface Symbol {
  id: number;
  name: string;
  code: string;
  block: string;
  count: number;
}

interface Redesign {
  drawing: { id: number; filename: string; revision: string } | null;
  review: { status: string | null; undecided: number };
  status: string;
  error: string | null;
  calls: number;
  changes: Change[];
  symbols: Symbol[];
  counts: Record<string, number>;
  output: { status: string; error: string | null; relative: string | null; file: string | null; at: string | null; changes: number };
  folder: string;
}

const ACTION_STYLE: Record<Change["action"], string> = {
  add: "bg-green-600 text-white",
  remove: "bg-red-600 text-white",
  replace: "bg-amber-500 text-white",
};

const STATUS_STYLE: Record<Change["status"], string> = {
  pending: "bg-gray-100 text-gray-600",
  proposed: "bg-sky-50 text-sky-700",
  approved: "bg-green-50 text-green-700",
  skipped: "bg-gray-100 text-gray-400",
  failed: "bg-red-50 text-red-700",
};

export function ProjectRedesignPage() {
  const { project } = useProject();
  const { user } = useAuth();
  const canEdit = user !== null && PROJECT_EDITOR_ROLES.includes(user.role);
  const [drawings, setDrawings] = useState<DrawingRow[]>([]);
  const [drawingId, setDrawingId] = useState<number | null>(null);
  const [data, setData] = useState<Redesign | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "todo">("all");
  const [kind, setKind] = useState<"review" | "interface">("review");
  const [floor, setFloor] = useState("");
  const [version, setVersion] = useState(0);

  useEffect(() => {
    api
      .get<{ drawings: DrawingRow[] }>(`/projects/${project.id}/redesign`)
      .then((body) => {
        setDrawings(body.drawings);
        setDrawingId((was) => was ?? body.drawings.find((d) => d.review_status === "done")?.id ?? body.drawings[0]?.id ?? null);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "The drawings could not be loaded"));
  }, [project.id]);

  const load = useCallback(() => {
    if (drawingId === null) return;
    api
      .get<Redesign>(`/projects/${project.id}/redesign/${drawingId}`)
      .then((body) => {
        setData(body);
        setVersion((v) => v + 1);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "The redesign could not be loaded"));
  }, [project.id, drawingId]);
  useEffect(() => load(), [load]);

  const planJob = useJob(project.id, "fa_redesign_plan", `/projects/${project.id}/redesign/${drawingId}/plan/jobs`, (j: Job) => {
    if (j.status === "failed") setError(j.error ?? "The redesign plan failed");
    load();
  });
  const applyJob = useJob(project.id, "fa_redesign_apply", `/projects/${project.id}/redesign/${drawingId}/apply/jobs`, (j: Job) => {
    if (j.status === "failed") setError(j.error ?? "The redesigned drawing could not be made");
    load();
  });
  useEffect(() => {
    if (!planJob.active) return;
    const timer = window.setInterval(load, 10000);
    return () => window.clearInterval(timer);
  }, [planJob.active, load]);

  async function start(kind: "plan" | "apply") {
    setError(null);
    try {
      const started = await api.post<Job>(`/projects/${project.id}/redesign/${drawingId}/${kind}/jobs`);
      (kind === "plan" ? planJob : applyJob).follow(started);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "It could not be started");
    }
  }

  async function change(c: Change, body: Record<string, unknown>) {
    setBusy(c.id);
    setError(null);
    try {
      setData(await api.patch<Redesign>(`/projects/${project.id}/redesign/${drawingId}/changes/${encodeURIComponent(c.id)}`, body));
      setVersion((v) => v + 1);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The change could not be saved");
    } finally {
      setBusy(null);
    }
  }

  async function many(ids: string[], status: "approved" | "skipped") {
    if (ids.length === 0) return;
    setBusy("many");
    setError(null);
    try {
      setData(await api.patch<Redesign>(`/projects/${project.id}/redesign/${drawingId}/changes`, { ids, status }));
      setVersion((v) => v + 1);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The changes could not be saved");
    } finally {
      setBusy(null);
    }
  }

  async function bringInterfaces() {
    setBusy("interfaces");
    setError(null);
    try {
      setData(await api.post<Redesign>(`/projects/${project.id}/redesign/${drawingId}/interfaces`));
      setVersion((v) => v + 1);
      setKind("interface");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The interface modules could not be brought in");
    } finally {
      setBusy(null);
    }
  }

  const drawing = drawings.find((d) => d.id === drawingId) ?? null;
  const all = data?.changes ?? [];
  const modules = all.filter((c) => c.source === "interface");
  const ofKind = all.filter((c) => (c.source === "interface") === (kind === "interface"));
  const floors = Array.from(new Set(ofKind.map((c) => c.floor)));
  const changes = ofKind
    .filter((c) => filter === "all" || ["proposed", "failed", "pending"].includes(c.status))
    .filter((c) => !floor || c.floor === floor);
  const ready = all.filter((c) => c.drawn).length;
  const planProgress = planJob.job?.progress as { done?: number; total?: number; message?: string } | undefined;
  const applyProgress = applyJob.job?.progress as { message?: string } | undefined;

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-3xl">
          <h1 className="text-3xl font-bold text-navy-900">Drawings Redesign</h1>
          <p className="mt-1 text-sm text-gray-600">
            The reviewed IFC drawing, copied with the changes accepted on Drawings Review made on it. The AI (Opus 5.5) places
            every ADD, REMOVE and REPLACE on the plan with the drawing&rsquo;s own symbols; you approve, move or skip each one; AutoCAD
            then makes them on a copy of the DWG &mdash; each marked on an EP-REDESIGN layer &mdash; filed in the project folder for the
            draftsman. Every module of the FA Interface Schedule (CR, CT1, CT2 &mdash; the shop drawing&rsquo;s own blocks) is placed beside
            its equipment too, and drawn once you approve it.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={drawingId ?? ""}
            onChange={(e) => setDrawingId(Number(e.target.value))}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
          >
            {drawings.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename} {d.revision}
                {d.review_status === "done" ? "" : " (not reviewed)"}
              </option>
            ))}
          </select>
          {canEdit && (
            <button
              onClick={() => void start("plan")}
              disabled={planJob.active || applyJob.active || drawing?.review_status !== "done"}
              title={drawing?.review_status === "done" ? "" : "Review the drawing first (Drawings Review)"}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {planJob.active ? "Placing…" : data?.changes.length ? "Place again with AI" : "Place changes with AI"}
            </button>
          )}
          {canEdit && data && drawing?.review_status === "done" && (
            <button
              onClick={() => void bringInterfaces()}
              disabled={planJob.active || applyJob.active || busy !== null}
              title="Place the FA Interface Schedule's modules again, as the schedule is now (your approvals and skips are kept)"
              className="rounded-lg border border-brand-600 px-4 py-2 text-sm font-semibold text-brand-700 disabled:opacity-50"
            >
              {busy === "interfaces" ? "Placing modules…" : "Interface modules"}
            </button>
          )}
          {canEdit && (
            <button
              onClick={() => void start("apply")}
              disabled={planJob.active || applyJob.active || ready === 0}
              className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {applyJob.active ? "AutoCAD is drawing…" : `Make redesigned drawing (${ready})`}
            </button>
          )}
        </div>
      </div>

      {error && <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}
      {planJob.active && (
        <p className="mt-4 rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-900">
          {planProgress?.message ?? "Placing the changes…"}
          {planProgress?.total ? ` (${planProgress.done ?? 0} of ${planProgress.total})` : ""}
        </p>
      )}
      {applyJob.active && (
        <p className="mt-4 rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-900">{applyProgress?.message ?? "AutoCAD is making the copy…"}</p>
      )}

      {data && (
        <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
          {(["proposed", "approved", "skipped", "failed"] as const).map((k) => (
            <div key={k} className="rounded-xl border border-gray-200 bg-white px-4 py-3">
              <div className="text-xs uppercase tracking-wide text-gray-500">{k === "proposed" ? "Placed, to approve" : k}</div>
              <div className="text-2xl font-bold text-navy-900">{data.counts[k] ?? 0}</div>
            </div>
          ))}
          <div className="rounded-xl border border-gray-200 bg-white px-4 py-3">
            <div className="text-xs uppercase tracking-wide text-gray-500">Redesigned drawing</div>
            {data.output.status === "made" ? (
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
            ) : (
              <div className="mt-1 text-sm text-gray-400">Not made yet</div>
            )}
          </div>
        </div>
      )}

      {data?.error && !planJob.active && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">{data.error}</p>}
      {data && data.review.undecided > 0 && (
        <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
          {data.review.undecided} finding{data.review.undecided === 1 ? " is" : "s are"} still undecided on Drawings Review: only the
          changes accepted there are in this redesign. Decide them, then place again.
        </p>
      )}

      {data && data.changes.length > 0 && (
        <div className="mt-5 flex flex-wrap items-center gap-2 text-sm">
          {(["review", "interface"] as const).map((k) => (
            <button
              key={k}
              onClick={() => {
                setKind(k);
                setFloor("");
              }}
              className={`rounded-lg px-3 py-1.5 font-semibold ${kind === k ? "bg-brand-600 text-white" : "border border-gray-300 text-gray-700"}`}
            >
              {k === "review" ? `Review changes (${all.length - modules.length})` : `Interface modules (${modules.length})`}
            </button>
          ))}
          <span className="mx-1 h-5 w-px bg-gray-300" />
          <button
            onClick={() => setFilter("all")}
            className={`rounded-lg px-3 py-1.5 ${filter === "all" ? "bg-navy-900 text-white" : "border border-gray-300 text-gray-700"}`}
          >
            All
          </button>
          <button
            onClick={() => setFilter("todo")}
            className={`rounded-lg px-3 py-1.5 ${filter === "todo" ? "bg-navy-900 text-white" : "border border-gray-300 text-gray-700"}`}
          >
            To approve
          </button>
          <select value={floor} onChange={(e) => setFloor(e.target.value)} className="rounded-lg border border-gray-300 px-2 py-1.5">
            <option value="">All floors</option>
            {floors.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
          {canEdit && (
            <span className="ml-auto flex gap-2">
              <button
                onClick={() => void many(changes.filter((x) => x.status === "proposed").map((x) => x.id), "approved")}
                disabled={busy !== null}
                className="rounded-lg border border-green-600 px-3 py-1.5 text-sm font-semibold text-green-700 disabled:opacity-50"
              >
                Approve all shown
              </button>
              <button
                onClick={() => void many(changes.filter((x) => x.status === "proposed").map((x) => x.id), "skipped")}
                disabled={busy !== null}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-semibold text-gray-700 disabled:opacity-50"
              >
                Skip all shown
              </button>
            </span>
          )}
        </div>
      )}
      {kind === "interface" && data && (
        <p className="mt-3 rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-900">
          {modules.length
            ? `The FA Interface Schedule's modules, each beside the equipment the trade's drawing shows it at (a typical plan's floors once). A module is drawn on the redesigned drawing only once you approve it; the loop addresses (P1/LP1/M…) are the draftsman's. ${modules.filter((c) => c.status === "failed").length} have no place on this drawing and are listed to draw by hand.`
            : "No module yet: press Interface modules to place the FA Interface Schedule's modules."}
        </p>
      )}

      {data && data.changes.length === 0 && !planJob.active && (
        <p className="mt-6 rounded-xl border border-dashed border-gray-200 p-6 text-center text-sm text-gray-500">
          {drawing?.review_status === "done"
            ? "Not placed yet. Accept the changes on Drawings Review, then place them with AI."
            : "Review this drawing on Drawings Review first; the redesign makes the changes accepted there."}
        </p>
      )}

      <div className="mt-3 space-y-3">
        {changes.map((c) => (
          <ChangeCard
            key={c.id}
            c={c}
            symbols={data?.symbols ?? []}
            canEdit={canEdit}
            busy={busy === c.id}
            image={apiUrl(`/projects/${project.id}/redesign/${drawingId}/changes/${encodeURIComponent(c.id)}/image?width=760&v=${version}`)}
            onChange={(body) => void change(c, body)}
          />
        ))}
      </div>
    </div>
  );
}

function ChangeCard({
  c,
  symbols,
  canEdit,
  busy,
  image,
  onChange,
}: {
  c: Change;
  symbols: Symbol[];
  canEdit: boolean;
  busy: boolean;
  image: string;
  onChange: (body: Record<string, unknown>) => void;
}) {
  const placing = c.action !== "remove";
  const pickable = c.action !== "add";
  return (
    <section className={`flex flex-col gap-4 rounded-xl border bg-white p-4 lg:flex-row ${c.status === "skipped" ? "opacity-60" : ""} border-gray-200`}>
      <div className="shrink-0">
        {c.box ? (
          <img
            src={image}
            loading="lazy"
            alt={`${c.action} on ${c.floor}`}
            className={`w-[380px] max-w-full rounded-lg border border-gray-200 ${canEdit && placing ? "cursor-crosshair" : ""}`}
            title={canEdit && placing ? "Click where the new symbol goes" : undefined}
            onClick={(e) => {
              if (!canEdit || !placing || busy) return;
              const r = e.currentTarget.getBoundingClientRect();
              onChange({ point: [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height] });
            }}
          />
        ) : (
          <div className="flex h-40 w-[380px] items-center justify-center rounded-lg border border-dashed text-xs text-gray-400">No picture</div>
        )}
        <div className="mt-1 text-[11px] text-gray-400">
          Red ring: the review&rsquo;s spot · blue: existing symbols · green: the new symbol · red cross: erased
        </div>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded px-2 py-0.5 text-xs font-bold ${ACTION_STYLE[c.action]}`}>{c.action.toUpperCase()}</span>
          <span className="font-semibold text-navy-900">{c.device || c.system_name}</span>
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_STYLE[c.status]}`}>
            {c.source === "interface" && c.status === "failed" ? "draw by hand" : c.status}
          </span>
          {c.confidence && c.source !== "interface" && <span className="text-xs text-gray-400">AI confidence: {c.confidence}</span>}
          {c.source === "interface" && c.status === "proposed" && (
            <span className="text-xs text-amber-700">drawn once approved</span>
          )}
        </div>
        <div className="mt-1 text-sm text-gray-600">
          {c.floor} ({c.sheet}) · {c.room || "—"}
        </div>
        <div className="mt-1 text-sm text-navy-900">{c.instruction}</div>
        {c.note && <div className="mt-1 text-xs italic text-gray-500">AI: {c.note}</div>}
        {c.error && <div className="mt-1 rounded bg-red-50 px-2 py-1 text-xs text-red-700">{c.error}</div>}
        {c.placeholder && (
          <div className="mt-1 rounded bg-amber-50 px-2 py-1 text-xs text-amber-800">
            No symbol of this device in the drawing: a marker is drawn, the draftsman draws the symbol.
          </div>
        )}
        {c.remove && !c.remove.erasable && (
          <div className="mt-1 rounded bg-amber-50 px-2 py-1 text-xs text-amber-800">
            This symbol is inside a block: marked to erase by hand, not erased.
          </div>
        )}
        {c.confirm && (
          <div className="mt-1 rounded bg-amber-50 px-2 py-1 text-xs text-amber-800">
            Placed within about ±{(c.residual ?? 1).toFixed(1)} m on this sheet: check the spot, or click the picture to set it.
          </div>
        )}
        {c.insert && (
          <div className="mt-2 text-xs text-gray-600">
            New symbol: <span className="font-semibold">{c.insert.name}</span>
            {c.insert.block ? ` (block ${c.insert.block})` : ""} · rotation {c.insert.rotation}°{c.moved ? " · moved by the engineer" : ""}
          </div>
        )}
        {c.remove && (
          <div className="text-xs text-gray-600">
            Erase: <span className="font-semibold">#{c.remove.n} {c.remove.name}</span>
          </div>
        )}
        {canEdit && c.box && (
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            {pickable && (
              <label className="flex items-center gap-1 text-gray-600">
                Erase
                <select
                  value={c.remove?.n ?? 0}
                  disabled={busy}
                  onChange={(e) => onChange({ candidate: Number(e.target.value) })}
                  className="rounded border border-gray-300 px-1.5 py-1"
                >
                  <option value={0}>— none —</option>
                  {c.candidates.map((k) => (
                    <option key={k.n} value={k.n}>
                      #{k.n} {k.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {placing && (
              <label className="flex items-center gap-1 text-gray-600">
                Symbol
                <select
                  value={c.insert?.symbol ?? 0}
                  disabled={busy}
                  onChange={(e) => onChange({ symbol: Number(e.target.value) })}
                  className="max-w-[220px] rounded border border-gray-300 px-1.5 py-1"
                >
                  <option value={0}>— draftsman draws it —</option>
                  {symbols.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {placing && c.insert && (
              <label className="flex items-center gap-1 text-gray-600">
                Rotation
                <select
                  value={c.insert.rotation}
                  disabled={busy}
                  onChange={(e) => onChange({ rotation: Number(e.target.value) })}
                  className="rounded border border-gray-300 px-1.5 py-1"
                >
                  {[0, 90, 180, 270].map((r) => (
                    <option key={r} value={r}>
                      {r}°
                    </option>
                  ))}
                </select>
              </label>
            )}
            <span className="ml-auto flex gap-2">
              {c.status !== "approved" && (c.insert || c.remove) && (
                <button
                  onClick={() => onChange({ status: "approved" })}
                  disabled={busy}
                  className="rounded bg-green-600 px-3 py-1.5 font-semibold text-white disabled:opacity-50"
                >
                  Approve
                </button>
              )}
              {c.status !== "skipped" ? (
                <button
                  onClick={() => onChange({ status: "skipped" })}
                  disabled={busy}
                  className="rounded border border-gray-300 px-3 py-1.5 font-semibold text-gray-700 disabled:opacity-50"
                >
                  Skip
                </button>
              ) : (
                <button
                  onClick={() => onChange({ status: "proposed" })}
                  disabled={busy}
                  className="rounded border border-gray-300 px-3 py-1.5 font-semibold text-gray-700 disabled:opacity-50"
                >
                  Undo skip
                </button>
              )}
            </span>
          </div>
        )}
      </div>
    </section>
  );
}
