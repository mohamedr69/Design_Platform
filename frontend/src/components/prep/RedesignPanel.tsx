/** Drawings Preparation's steps after the review (app.redesign):
 *
 *  devices     every change accepted on the review placed on the plan by the
 *              placement agents side by side, coordinated -- off the columns
 *              and each other, each room's detectors covering it at 6.3 m, the
 *              coordination agent on the rooms where something was wrong --,
 *              and reviewed floor by floor by the orchestrator; the engineer
 *              approves, moves (a click on the picture), re-symbols or skips;
 *  interfaces  the FA Interface Schedule's modules, each at its equipment's
 *              location, drawn once approved;
 *  output      the draftsman's PDF (each floor marked, then the schedule), and
 *              the copy of the drawing AutoCAD makes the changes on. */
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "../../context/AuthContext";
import { ApiError, api, apiUrl } from "../../lib/api";
import { PROJECT_EDITOR_ROLES } from "../../lib/types";
import { useJob, type Job } from "../../lib/useJob";
import { AgentRunPanel, StageProgress } from "./AgentRunPanel";
import type { Change, DrawingRow, Redesign, Symbol } from "./types";

export type Section = "devices" | "interfaces" | "output";

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

const CHECK_STYLE = { ok: "bg-green-50 text-green-700", check: "bg-amber-50 text-amber-800", reject: "bg-red-50 text-red-700" };

/** Wants the engineer's eye: the orchestrator asked, a room is short of
 * coverage or could not be measured, it was moved for coordination, it failed. */
function needsLook(c: Change): boolean {
  return (
    c.status === "failed" ||
    (c.check !== undefined && c.check.verdict !== "ok") ||
    (c.coverage !== undefined && (c.coverage.open === true || c.coverage.ok === false)) ||
    (c.coordination !== undefined && (c.coordination.moved_m > 1 || c.coordination.refused !== null))
  );
}

export function RedesignPanel({
  projectId,
  drawing,
  section,
  onChanged,
}: {
  projectId: number;
  drawing: DrawingRow;
  section: Section;
  onChanged?: () => void;
}) {
  const { user } = useAuth();
  const canEdit = user !== null && PROJECT_EDITOR_ROLES.includes(user.role);
  const drawingId = drawing.id;
  const [data, setData] = useState<Redesign | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "todo" | "look">("all");
  const [floor, setFloor] = useState("");
  const [version, setVersion] = useState(0);
  const base = `/projects/${projectId}/redesign/${drawingId}`;

  const load = useCallback(() => {
    api
      .get<Redesign>(base)
      .then((body) => {
        setData(body);
        setVersion((v) => v + 1);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "The drawing's preparation could not be loaded"));
  }, [base]);
  useEffect(() => load(), [load]);

  const planJob = useJob(projectId, "fa_redesign_plan", `${base}/plan/jobs`, (j: Job) => {
    if (j.status === "failed") setError(j.error ?? "The devices could not be prepared");
    load();
    onChanged?.();
  });
  const applyJob = useJob(projectId, "fa_redesign_apply", `${base}/apply/jobs`, (j: Job) => {
    if (j.status === "failed") setError(j.error ?? "The drawing copy could not be made");
    load();
    onChanged?.();
  });
  useEffect(() => {
    if (!planJob.active) return;
    const timer = window.setInterval(load, 8000);
    return () => window.clearInterval(timer);
  }, [planJob.active, load]);

  async function start(kind: "plan" | "apply") {
    setError(null);
    try {
      const started = await api.post<Job>(`${base}/${kind}/jobs`);
      (kind === "plan" ? planJob : applyJob).follow(started);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "It could not be started");
    }
  }

  async function change(c: Change, body: Record<string, unknown>) {
    setBusy(c.id);
    setError(null);
    try {
      setData(await api.patch<Redesign>(`${base}/changes/${encodeURIComponent(c.id)}`, body));
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
      setData(await api.patch<Redesign>(`${base}/changes`, { ids, status }));
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
      setData(await api.post<Redesign>(`${base}/interfaces`));
      setVersion((v) => v + 1);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The interface modules could not be placed");
    } finally {
      setBusy(null);
    }
  }

  const reviewed = drawing.review_status === "done";
  const all = data?.changes ?? [];
  const ofSection = all.filter((c) => (c.source === "interface") === (section === "interfaces"));
  const floors = Array.from(new Set(ofSection.map((c) => c.floor)));
  const shown = ofSection
    .filter((c) => filter === "all" || (filter === "todo" ? ["proposed", "failed", "pending"].includes(c.status) : needsLook(c)))
    .filter((c) => !floor || c.floor === floor);
  const ready = all.filter((c) => c.drawn).length;
  const jobsBusy = planJob.active || applyJob.active;

  if (!data) return <p className="mt-6 text-sm text-gray-400">{error ?? "Loading…"}</p>;

  return (
    <div>
      {error && <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}

      {section === "devices" && (
        <>
          <div className="mt-4 flex flex-wrap items-start justify-between gap-3">
            <p className="max-w-3xl text-sm text-gray-600">
              Every change accepted on the review is placed on the plan with the drawing&rsquo;s own symbols by{" "}
              {data.agents_on ? "Opus placement agents working side by side" : "the platform (the agents are off)"}, then coordinated:
              no device on a column or on another, and every room&rsquo;s detectors covering it within{" "}
              {data.run?.radius.smoke ?? 6.3} m &mdash; {data.agents_on ? "an Opus coordination agent settles each room where something is wrong, and the Opus orchestrator reviews every floor" : "the platform moves them to the best spots and adds what is missing"}. You approve, move (click the picture) or skip each one.
            </p>
            {canEdit && (
              <button
                onClick={() => void start("plan")}
                disabled={jobsBusy || !reviewed}
                title={reviewed ? "" : "Review the drawing first (step 1)"}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {planJob.active
                  ? "Preparing…"
                  : data.changes.some((c) => c.source !== "interface")
                    ? data.agents_on
                      ? "Prepare again with agents"
                      : "Place and coordinate again"
                    : data.agents_on
                      ? "Prepare devices with agents"
                      : "Place and coordinate devices"}
              </button>
            )}
          </div>
          {planJob.active && <StageProgress run={data.run} job={planJob.job} canEdit={canEdit} onStop={() => void planJob.cancel()} />}
          {data.error && !planJob.active && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">{data.error}</p>}
          {data.review.undecided > 0 && (
            <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
              {data.review.undecided} finding{data.review.undecided === 1 ? " is" : "s are"} still undecided on the review: only the
              changes accepted there are prepared here. Decide them, then prepare again.
            </p>
          )}
          {data.run && !planJob.active && <AgentRunPanel run={data.run} agentsOn={data.agents_on} />}
        </>
      )}

      {section === "interfaces" && (
        <div className="mt-4 flex flex-wrap items-start justify-between gap-3">
          <p className="max-w-3xl text-sm text-gray-600">
            The FA Interface Schedule&rsquo;s modules (CR, CT1, CT2 &mdash; the shop drawing&rsquo;s own blocks), each placed at the location the
            Interfaces tab found its equipment at, on the nearest wall, side by side with the others there, with its &ldquo;FOR …&rdquo; note.
            A module is drawn on the copy only once you approve it; {ofSection.filter((c) => c.status === "failed").length} have no place
            on this drawing and are listed to draw by hand.
          </p>
          {canEdit && (
            <button
              onClick={() => void bringInterfaces()}
              disabled={jobsBusy || busy !== null || !reviewed}
              title="Place the schedule's modules as the schedule is now (your approvals, moves and skips are kept)"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {busy === "interfaces" ? "Placing modules…" : ofSection.length ? "Place modules again" : "Place interface modules"}
            </button>
          )}
        </div>
      )}

      {section === "output" && (
        <Output
          projectId={projectId}
          data={data}
          ready={ready}
          canEdit={canEdit}
          making={applyJob.active}
          makingMessage={(applyJob.job?.progress as { message?: string } | undefined)?.message}
          disabled={jobsBusy}
          onMake={() => void start("apply")}
          base={base}
        />
      )}

      {section !== "output" && (
        <>
          <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
            {(
              [
                ["Placed, to approve", ofSection.filter((c) => c.status === "proposed").length],
                ["Approved", ofSection.filter((c) => c.status === "approved").length],
                ["Needs a look", ofSection.filter(needsLook).length],
                ["Skipped", ofSection.filter((c) => c.status === "skipped").length],
                [section === "interfaces" ? "Draw by hand" : "Failed", ofSection.filter((c) => c.status === "failed").length],
              ] as const
            ).map(([label, value]) => (
              <div key={label} className="rounded-xl border border-gray-200 bg-white px-4 py-3">
                <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
                <div className="text-2xl font-bold text-navy-900">{value}</div>
              </div>
            ))}
          </div>

          {ofSection.length > 0 && (
            <div className="mt-5 flex flex-wrap items-center gap-2 text-sm">
              {(
                [
                  ["all", "All"],
                  ["todo", "To approve"],
                  ["look", "Needs a look"],
                ] as const
              ).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setFilter(key)}
                  className={`rounded-lg px-3 py-1.5 ${filter === key ? "bg-navy-900 text-white" : "border border-gray-300 text-gray-700"}`}
                >
                  {label}
                </button>
              ))}
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
                    onClick={() => void many(shown.filter((x) => x.status === "proposed").map((x) => x.id), "approved")}
                    disabled={busy !== null}
                    className="rounded-lg border border-green-600 px-3 py-1.5 text-sm font-semibold text-green-700 disabled:opacity-50"
                  >
                    Approve all shown
                  </button>
                  <button
                    onClick={() => void many(shown.filter((x) => x.status === "proposed").map((x) => x.id), "skipped")}
                    disabled={busy !== null}
                    className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-semibold text-gray-700 disabled:opacity-50"
                  >
                    Skip all shown
                  </button>
                </span>
              )}
            </div>
          )}

          {ofSection.length === 0 && !planJob.active && (
            <p className="mt-6 rounded-xl border border-dashed border-gray-200 p-6 text-center text-sm text-gray-500">
              {!reviewed
                ? "Review this drawing first (step 1): the devices prepared here are the changes accepted there."
                : section === "interfaces"
                  ? "No module yet: press Place interface modules to bring in the FA Interface Schedule's modules."
                  : "Not prepared yet. Accept the changes on the review, then prepare them here."}
            </p>
          )}

          <div className="mt-3 space-y-3">
            {shown.map((c) => (
              <ChangeCard
                key={c.id}
                c={c}
                symbols={data.symbols}
                canEdit={canEdit}
                busy={busy === c.id}
                image={apiUrl(`${base}/changes/${encodeURIComponent(c.id)}/image?width=760&v=${version}`)}
                onChange={(body) => void change(c, body)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function Output({
  projectId,
  data,
  ready,
  canEdit,
  making,
  makingMessage,
  disabled,
  onMake,
  base,
}: {
  projectId: number;
  data: Redesign;
  ready: number;
  canEdit: boolean;
  making: boolean;
  makingMessage?: string;
  disabled: boolean;
  onMake: () => void;
  base: string;
}) {
  const all = data.changes;
  const toApprove = all.filter((c) => (c.source === "interface" || c.source === "coverage") && c.status === "proposed").length;
  const rejected = all.filter((c) => c.status === "proposed" && c.check?.verdict === "reject").length;
  return (
    <div className="mt-4 grid gap-4 lg:grid-cols-2">
      <section className="rounded-2xl border border-gray-200 bg-white p-5">
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">1 · For the draftsman</div>
        <h3 className="mt-1 text-lg font-semibold text-navy-900">Draftsman PDF</h3>
        <p className="mt-1 text-sm text-gray-600">
          Each floor&rsquo;s plan with every change marked and numbered where it was placed (green ADD, red REMOVE, amber REPLACE, purple
          module, a new detector&rsquo;s coverage dashed), then the schedule of the same numbers: action, device, room, instruction and the
          piece of plan.
        </p>
        <div className="mt-3 text-sm text-navy-900">{ready} change{ready === 1 ? "" : "s"} on it</div>
        <div className="mt-3 flex flex-wrap gap-2">
          <a
            href={apiUrl(`${base}/markup.pdf`)}
            className={`rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 ${ready === 0 ? "pointer-events-none opacity-50" : ""}`}
          >
            Export PDF for the draftsman
          </a>
          <a
            href={apiUrl(`/projects/${projectId}/drawing-review/${data.drawing?.id}/export.xlsx`)}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-navy-900 hover:bg-gray-50"
          >
            Review findings (Excel)
          </a>
        </div>
      </section>

      <section className="rounded-2xl border border-gray-200 bg-white p-5">
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">2 · On the drawing</div>
        <h3 className="mt-1 text-lg font-semibold text-navy-900">Add the changes to a copy of the drawing</h3>
        <p className="mt-1 text-sm text-gray-600">
          AutoCAD makes the changes on a copy of the DWG the review plotted &mdash; the drawing&rsquo;s own blocks inserted, the erased ones
          deleted, each change marked on an EP-REDESIGN layer &mdash; filed in the project folder ({data.folder}).
        </p>
        <div className="mt-3 text-sm text-navy-900">
          {ready} change{ready === 1 ? "" : "s"} to make
          {toApprove > 0 && <span className="text-amber-700"> · {toApprove} module or coverage detector{toApprove === 1 ? "" : "s"} not approved yet (left off)</span>}
          {rejected > 0 && <span className="text-red-700"> · {rejected} rejected by the orchestrator (left off unless approved)</span>}
        </div>
        {making && <p className="mt-2 rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-900">{makingMessage ?? "AutoCAD is making the copy…"}</p>}
        {!data.readiness.ready && (
          <div className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Not ready for the draftsman yet:
            <ul className="ml-4 list-disc">
              {data.readiness.blockers.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {canEdit && (
            <button
              onClick={onMake}
              disabled={disabled || ready === 0 || !data.readiness.ready}
              className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {making ? "AutoCAD is drawing…" : `Make the drawing copy (${ready})`}
            </button>
          )}
          {data.output.status === "made" && (
            <a href={apiUrl(`${base}/output.dwg`)} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-brand-700">
              Download DWG
            </a>
          )}
        </div>
        {data.output.status === "made" && (
          <div className="mt-2 break-all text-xs text-gray-500">
            {data.output.file} · {data.output.changes} changes ·{" "}
            {data.output.relative ? `filed in ${data.output.relative}` : "not filed (project folder not reachable)"}
            {data.output.at ? ` · ${new Date(data.output.at).toLocaleString()}` : ""}
          </div>
        )}
        {data.output.status === "failed" && <div className="mt-2 text-xs text-red-700">{data.output.error}</div>}
      </section>
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
  const cov = c.coverage;
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
          <div className="flex h-40 w-[380px] max-w-full items-center justify-center rounded-lg border border-dashed text-xs text-gray-400">
            No picture
          </div>
        )}
        <div className="mt-1 max-w-[380px] text-[11px] text-gray-400">
          Red ring: the review&rsquo;s spot · blue: existing symbols · green: the new symbol (and a detector&rsquo;s coverage) · orange:
          columns · red cross: erased
        </div>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded px-2 py-0.5 text-xs font-bold ${ACTION_STYLE[c.action]}`}>{c.action.toUpperCase()}</span>
          <span className="font-semibold text-navy-900">{c.device || c.system_name}</span>
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_STYLE[c.status]}`}>
            {c.source === "interface" && c.status === "failed" ? "draw by hand" : c.status}
          </span>
          {c.source === "coverage" && <span className="rounded-full bg-violet-50 px-2 py-0.5 text-xs font-semibold text-violet-700">added for coverage</span>}
          {c.check && (
            <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${CHECK_STYLE[c.check.verdict]}`} title={c.check.reason}>
              orchestrator: {c.check.verdict}
            </span>
          )}
          {c.confidence && c.source !== "interface" && <span className="text-xs text-gray-400">placement confidence: {c.confidence}</span>}
          {(c.source === "interface" || c.source === "coverage") && c.status === "proposed" && (
            <span className="text-xs text-amber-700">drawn once approved</span>
          )}
        </div>
        <div className="mt-1 text-sm text-gray-600">
          {c.floor} ({c.sheet}) · {c.room || "—"}
        </div>
        <div className="mt-1 text-sm text-navy-900">{c.instruction}</div>
        {c.note && <div className="mt-1 text-xs italic text-gray-500">Placement: {c.note}</div>}
        {c.check && c.check.verdict !== "ok" && (
          <div className={`mt-1 rounded px-2 py-1 text-xs ${c.check.verdict === "reject" ? "bg-red-50 text-red-800" : "bg-amber-50 text-amber-900"}`}>
            Orchestrator: {c.check.reason}
            {c.check.verdict === "reject" && " — left off the drawing unless you approve it."}
          </div>
        )}
        {c.coordination && (c.coordination.moved_m > 0 || c.coordination.reason || c.coordination.refused) && (
          <div className="mt-1 rounded bg-sky-50 px-2 py-1 text-xs text-sky-900">
            {c.coordination.moved_m > 0 ? `Moved ${c.coordination.moved_m} m by the ${c.coordination.by === "agent" ? "coordination agent" : "platform"}` : `Coordination (${c.coordination.by})`}
            {c.coordination.reason ? `: ${c.coordination.reason}` : ""}
            {c.coordination.refused && <div className="text-red-700">Refused: {c.coordination.refused}</div>}
          </div>
        )}
        {cov && (
          <div
            className={`mt-1 rounded px-2 py-1 text-xs ${
              cov.open ? "bg-amber-50 text-amber-900" : cov.ok ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"
            }`}
          >
            {cov.open
              ? `Room coverage not measured (its walls do not close a room here): check the ${cov.radius} m coverage by eye.`
              : `Room coverage at ${cov.radius} m: ${Math.round((cov.covered ?? 0) * 100)}% of ${cov.area_m2} m² with ${cov.detectors} detector${cov.detectors === 1 ? "" : "s"}${cov.ok ? "" : ` — ${cov.uncovered_m2} m² not covered`}.`}
          </div>
        )}
        {c.error && <div className="mt-1 rounded bg-red-50 px-2 py-1 text-xs text-red-700">{c.error}</div>}
        {c.placeholder && (
          <div className="mt-1 rounded bg-amber-50 px-2 py-1 text-xs text-amber-800">
            No symbol of this device in the drawing: a marker is drawn, the draftsman draws the symbol.
          </div>
        )}
        {c.remove && !c.remove.erasable && (
          <div className="mt-1 rounded bg-amber-50 px-2 py-1 text-xs text-amber-800">This symbol is inside a block: marked to erase by hand, not erased.</div>
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
