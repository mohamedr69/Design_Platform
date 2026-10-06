import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, api, apiUrl } from "../lib/api";
import { PROJECT_EDITOR_ROLES } from "../lib/types";
import { useAuth } from "../context/AuthContext";
import { useJob, type Job } from "../lib/useJob";
import { useProject } from "./ProjectWorkspace";

type Status = "present" | "absent" | "not_required" | "unclear" | "wrong";
type Action = "none" | "add" | "remove" | "replace";

interface Overview {
  drawings: { id: number; filename: string; revision: string; pages: { page: number; sheet: string; title: string; floor: string }[] }[];
  rules: { system: string; name: string; rule: string }[];
}

interface Finding {
  id: string;
  page: number;
  floor: string;
  sheet: string;
  room: string;
  room_type: string;
  system: string;
  system_name: string;
  kind: "room" | "unclear" | "other" | "sheet" | "spacing" | "fls";
  severity?: string | null;
  action: Action;
  device: string;
  instruction: string;
  issue: string;
  seen: string;
  box: number[];
  mark: number[] | null;
  decision: "open" | "accepted" | "dismissed";
  note: string;
  by_ruling: boolean;
  /** The model's recommendation, before any engineer's wording. */
  proposal?: string;
  /** A decision made on an earlier proposal for this finding: it does not
   * carry over (the proposal changed, or cannot be shown unchanged), so the
   * finding is open again and this is its history. */
  previous_decision?: {
    status: "accepted" | "dismissed";
    note: string | null;
    instruction: string | null;
    at: string | null;
    changed: string[];
    /** Why it does not carry over: the proposal changed, or nothing shows it is the same one. */
    reason: "proposal_changed" | "not_verifiable";
    message: string;
  } | null;
}

interface Ruling {
  id: number;
  decision: "accepted" | "dismissed";
  room: string;
  system: string;
  system_name: string;
  action: string;
  device: string;
  instruction: string;
  note: string;
  at: string | null;
}

export type ReviewState = "done" | "partial" | "not_reviewed" | "running" | "blocked" | "failed" | "stopped";

interface Review {
  drawing: { id: number; filename: string; revision: string };
  status: "idle" | "running" | "done" | "stopped" | "failed" | "blocked";
  error: string | null;
  /** What the review comes to: "done" only when a model answered every part of
   * every plan; a plot no model answered is "not_reviewed". */
  state: ReviewState;
  state_message: string | null;
  /** The models that actually answered; `model` is only the one asked for. */
  answered_by: string[];
  model: string;
  calls: number;
  started_at: string | null;
  finished_at: string | null;
  floors: {
    page: number;
    sheet: string;
    title: string;
    floor: string;
    windows: number;
    windows_done: number;
    windows_failed: number;
    sheet_status: string;
    rooms: { id: string; name: string; room_type: string; status: string; checks: Record<string, { status: Status; seen: string }> | null }[];
  }[];
  findings: Finding[];
  stats: Record<string, Record<Status, number>>;
  systems: Record<string, string>;
  rules: { system: string; name: string; rule: string }[];
  rulings: Ruling[];
  fls: { folder: string; files: string[]; floors_matched: number; floors: number };
  counts: {
    rooms: number;
    reviewed: number;
    open: number;
    accepted: number;
    dismissed: number;
    unclear: number;
    add: number;
    remove: number;
    replace: number;
  };
}

const KIND_TEXT: Record<Finding["kind"], string> = {
  room: "Room",
  unclear: "Unclear: check by eye",
  other: "Outside the named rooms",
  sheet: "Floor review",
  spacing: "Across floors (every ~5 floors)",
  fls: "Against the FLS drawing",
};
const ACTION_STYLE: Record<Action, string> = {
  add: "bg-red-600 text-white",
  remove: "bg-blue-600 text-white",
  replace: "bg-amber-500 text-white",
  none: "bg-gray-200 text-gray-600",
};
// How each end of a review is shown: only a completed review is green.
const STATE_STYLE: Record<ReviewState, string> = {
  done: "bg-emerald-50 text-emerald-900",
  partial: "bg-amber-50 text-amber-900",
  not_reviewed: "bg-amber-50 text-amber-900",
  running: "bg-sky-50 text-sky-900",
  blocked: "bg-red-50 text-red-800",
  failed: "bg-red-50 text-red-800",
  stopped: "bg-gray-50 text-gray-700",
};
const ACTION_TEXT: Record<Action, string> = { add: "ADD", remove: "REMOVE", replace: "REPLACE", none: "CHECK" };
const STATUS_STYLE: Record<Status, string> = {
  present: "bg-emerald-50 text-emerald-700",
  absent: "bg-rose-50 text-rose-700",
  not_required: "bg-gray-50 text-gray-400",
  unclear: "bg-amber-50 text-amber-800",
  wrong: "bg-orange-100 text-orange-800",
};
const STATUS_TEXT: Record<Status, string> = { present: "✓", absent: "✗", not_required: "n/r", unclear: "?", wrong: "≠" };

/** Drawings Review: the fire alarm IFC drawing plotted, and every room the
 * plans name looked at by the AI (Opus 5.5) for detection, speakers, fire
 * telephone jacks, call points, emergency lights and exit / directional
 * signs against the company's coverage rules. The AI reports; the engineer
 * accepts or dismisses each finding. */
export function ProjectDrawingReviewPage({
  embedded = false,
  drawingId: chosen = null,
  onChanged,
}: {
  /** Inside Drawings Preparation: its drawing, its heading. */
  embedded?: boolean;
  drawingId?: number | null;
  /** A review started or ended: the step's mark is read again. */
  onChanged?: () => void;
} = {}) {
  const { project } = useProject();
  const { user } = useAuth();
  const canEdit = user !== null && PROJECT_EDITOR_ROLES.includes(user.role);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [own, setDrawingId] = useState<number | null>(null);
  // inside Drawings Preparation the drawing is the tab's
  const drawingId = chosen ?? own;
  const [review, setReview] = useState<Review | null>(null);
  const [error, setError] = useState<string | null>(null);
  // What a decision also settled: the same comment on the other floors.
  const [notice, setNotice] = useState<string | null>(null);
  const [choosing, setChoosing] = useState(false);
  const [pages, setPages] = useState<number[]>([]);
  const [tab, setTab] = useState<"findings" | "rooms" | "rules">("findings");

  useEffect(() => {
    api
      .get<Overview>(`/projects/${project.id}/drawing-review`)
      .then((o) => {
        setOverview(o);
        if (o.drawings.length) setDrawingId((d) => d ?? o.drawings[0].id);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "The review could not be loaded"));
  }, [project.id]);

  const load = useCallback(() => {
    if (drawingId === null) return;
    api
      .get<Review>(`/projects/${project.id}/drawing-review/${drawingId}`)
      .then(setReview)
      .catch((e) => setError(e instanceof ApiError ? e.message : "The review could not be loaded"));
  }, [project.id, drawingId]);
  useEffect(() => load(), [load]);

  const job = useJob(project.id, "fa_drawing_review", `/projects/${project.id}/drawing-review/${drawingId}/jobs`, (j: Job) => {
    if (j.status === "failed") setError(j.error ?? "The review failed");
    load();
    onChanged?.();
  });
  // While a review runs, its findings appear floor by floor.
  useEffect(() => {
    if (!job.active) return;
    const timer = window.setInterval(load, 15000);
    return () => window.clearInterval(timer);
  }, [job.active, load]);

  const drawing = overview?.drawings.find((d) => d.id === drawingId) ?? null;

  async function start() {
    setError(null);
    setChoosing(false);
    try {
      const started = await api.post<Job>(`/projects/${project.id}/drawing-review/${drawingId}/jobs`, {
        pages: pages.length && drawing && pages.length < drawing.pages.length ? pages : null,
      });
      job.follow(started);
      onChanged?.();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The review could not be started");
    }
  }

  async function decide(finding: Finding, status: "accepted" | "dismissed" | "open", instruction = "", note = "") {
    setError(null);
    setNotice(null);
    try {
      const next = await api.post<Review & { applied?: { count: number; floors: string[] } }>(
        `/projects/${project.id}/drawing-review/${drawingId}/decisions`,
        { id: finding.id, status, note, instruction },
      );
      setReview(next);
      const applied = next.applied;
      if (applied && applied.count > 0) {
        const what = status === "open" ? "Reopened" : status === "accepted" ? "Accepted" : "Marked not needed";
        setNotice(
          `${what} the same comment on ${applied.count} other finding${applied.count === 1 ? "" : "s"} too: ` +
            applied.floors.join(", ") + ".",
        );
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The finding could not be saved");
    }
  }

  async function deleteRuling(id: number) {
    if (!window.confirm("Remove this ruling? The next review will no longer be given it.")) return;
    try {
      await api.delete(`/drawing-review/rulings/${id}`);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The ruling could not be removed");
    }
  }

  async function acceptAll(ids: string[]) {
    if (!ids.length || !window.confirm(`Accept all ${ids.length} changes shown for the draftsman?`)) return;
    try {
      setReview(await api.post<Review>(`/projects/${project.id}/drawing-review/${drawingId}/decisions/bulk`, { ids, status: "accepted" }));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The changes could not be accepted");
    }
  }

  if (!overview) return <p className="mt-6 text-sm text-gray-400">{error ?? "Loading…"}</p>;
  if (!overview.drawings.length) {
    return (
      <div className="mt-6">
        {!embedded && <h1 className="text-3xl font-bold text-navy-900">Drawings Review</h1>}
        <p className="mt-4 rounded-2xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-500">
          No fire alarm IFC drawing has been imported for this project. Import it on the BOQ page&apos;s As per IFC Drawings tab.
        </p>
      </div>
    );
  }
  const progress = job.job?.progress as { done?: number; total?: number; message?: string } | undefined;

  return (
    <div className="mt-2">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-3xl">
          {embedded ? (
            <p className="text-sm text-gray-600">
              The AI (Opus 5.5) reads every room the plans name against the coverage rules and proposes what to ADD, REMOVE or
              REPLACE. Accept the changes the draftsman should make: the accepted ones go on to Devices, where the agents place them.
            </p>
          ) : (
            <>
              <h1 className="text-3xl font-bold text-navy-900">Drawings Review</h1>
              <p className="mt-1 text-sm text-gray-600">
                The fire alarm IFC drawing, room by room, for the draftsman: the AI (Opus 5.5) reads every room the plans name against
                the coverage rules and proposes what to ADD, REMOVE or REPLACE -- detectors, speakers and sounder-flashers, fire
                telephone jacks, call points, emergency lights, exit and directional signs. The engineer accepts each change; the
                accepted ones are marked floor by floor on the Mark-up PDF for the draftsman.
              </p>
            </>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {!embedded && overview.drawings.length > 1 && (
            <select
              value={drawingId ?? ""}
              onChange={(e) => setDrawingId(Number(e.target.value))}
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
            >
              {overview.drawings.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} {d.revision}
                </option>
              ))}
            </select>
          )}
          {canEdit && (
            <button
              type="button"
              disabled={job.active}
              onClick={() => {
                setPages(drawing?.pages.map((p) => p.page) ?? []);
                setChoosing(!choosing);
              }}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
            >
              {job.active ? "Reviewing…" : review && review.counts.reviewed ? "Review again" : "Review drawing"}
            </button>
          )}
          {review && review.counts.accepted > 0 && (
            <a
              href={apiUrl(`/projects/${project.id}/drawing-review/${drawingId}/markup.pdf`)}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
              title="The accepted changes, floor by floor: action, device, room and instruction for the draftsman"
            >
              {embedded ? "Review schedule PDF" : "Draftsman schedule PDF"}
            </a>
          )}
          {review && review.counts.reviewed > 0 && (
            <a
              href={apiUrl(`/projects/${project.id}/drawing-review/${drawingId}/export.xlsx`)}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-navy-900 hover:bg-gray-50"
            >
              Export Excel
            </a>
          )}
        </div>
      </div>

      {error && error !== review?.state_message && (
        <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>
      )}
      {notice && (
        <p className="sticky top-2 z-20 mt-3 flex items-start justify-between gap-3 rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-900 shadow-sm">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="text-xs font-semibold text-sky-700 hover:underline">
            Close
          </button>
        </p>
      )}

      {choosing && drawing && (
        <section className="mt-4 rounded-2xl border border-gray-200 bg-white p-4 text-sm">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div className="font-semibold text-navy-900">Floors to review — {drawing.filename} {drawing.revision}</div>
            <div className="text-xs text-gray-500">
              About 6 minutes to plot the drawing (once per revision), then a few minutes for each part of a plan. A typical
              sheet stands for all its floors. Floors already reviewed are not asked again.
            </div>
          </div>
          <div className="mt-3 grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
            {drawing.pages.map((p) => (
              <label key={p.page} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={pages.includes(p.page)}
                  onChange={(e) => setPages((was) => (e.target.checked ? [...was, p.page] : was.filter((x) => x !== p.page)))}
                />
                <span>
                  <span className="font-medium">{p.floor}</span> <span className="text-xs text-gray-500">{p.sheet}</span>
                </span>
              </label>
            ))}
          </div>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              disabled={!pages.length}
              onClick={start}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
            >
              Review {pages.length} floor{pages.length === 1 ? "" : "s"}
            </button>
            <button type="button" onClick={() => setChoosing(false)} className="rounded-lg px-4 py-2 text-sm text-gray-600 hover:bg-gray-100">
              Cancel
            </button>
          </div>
        </section>
      )}

      {job.active && (
        <section className="mt-4 rounded-2xl border border-brand-200 bg-brand-50/50 p-4 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="font-semibold text-navy-900">{progress?.message ?? "Queued: waiting for the IFC worker"}</div>
              {progress?.total ? (
                <div className="mt-2 h-1.5 w-80 max-w-full overflow-hidden rounded-full bg-white">
                  <div className="h-full bg-brand-600" style={{ width: `${Math.round(((progress.done ?? 0) / progress.total) * 100)}%` }} />
                </div>
              ) : null}
              <div className="mt-1 text-xs text-gray-500">Findings appear below floor by floor as they come. You can leave this page.</div>
            </div>
            {canEdit && (
              <button type="button" onClick={() => void job.cancel()} className="rounded-lg px-3 py-1.5 text-sm text-gray-600 hover:bg-white">
                Stop
              </button>
            )}
          </div>
        </section>
      )}

      {review && (
        <>
          {review.state_message && !job.active && (
            <p className={`mt-3 rounded-lg px-3 py-2 text-sm ${STATE_STYLE[review.state]}`} role="status">
              {review.state_message}
            </p>
          )}
          {review.fls && (
            <p
              className={`mt-3 rounded-lg px-3 py-2 text-sm ${review.fls.files.length ? "bg-sky-50 text-sky-900" : "bg-amber-50 text-amber-900"}`}
            >
              {review.fls.files.length ? (
                <>
                  <b>FLS drawings:</b> {review.fls.files.join(", ")} &middot; exit and directional signs checked against the FLS on{" "}
                  {review.fls.floors_matched} of {review.fls.floors} floors reviewed
                  {review.fls.floors_matched < review.fls.floors && " (the other floors have no FLS sheet of the same floor)"}.
                </>
              ) : (
                <>
                  <b>No FLS drawings yet:</b> file them in {review.fls.folder} (PDF or DWG) and review again: the exit and directional
                  signs are then checked against the FLS escape routes, floor by floor. Until then they follow the routes on the FA drawing.
                </>
              )}
            </p>
          )}
          <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
            {[
              ["Rooms reviewed", `${review.counts.reviewed} / ${review.counts.rooms}`],
              ["Changes proposed", `${review.counts.add} add · ${review.counts.remove} remove · ${review.counts.replace} replace`],
              ["To decide", String(review.counts.open)],
              ["Accepted for draftsman", String(review.counts.accepted)],
              ["AI model", review.answered_by.length ? review.answered_by.join(", ") : `none answered (${review.model} asked)`],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-gray-200 bg-white px-4 py-3">
                <div className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</div>
                <div className="mt-1 truncate text-xl font-bold text-navy-900">{value}</div>
              </div>
            ))}
          </div>

          <div className="mt-5 flex gap-1 border-b border-gray-200" role="tablist">
            {(
              [
                ["findings", `Findings (${review.findings.length})`],
                ["rooms", `Rooms (${review.counts.rooms})`],
                ["rules", "Coverage rules"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                role="tab"
                aria-selected={tab === key}
                onClick={() => setTab(key)}
                className={`-mb-px border-b-2 px-4 py-2 text-sm font-semibold ${tab === key ? "border-brand-600 text-brand-700" : "border-transparent text-gray-500"}`}
              >
                {label}
              </button>
            ))}
          </div>

          {tab === "findings" && (
            <Findings projectId={project.id} drawingId={drawingId!} review={review} canEdit={canEdit} onDecide={decide} onAcceptAll={acceptAll} />
          )}
          {tab === "rooms" && <Rooms review={review} />}
          {tab === "rules" && (
            <section className="mt-4 rounded-2xl border border-gray-200 bg-white p-4 text-sm">
              <p className="text-gray-600">
                The company's coverage rules, as the engineers set them. The AI applies them as written; stair and lift-lobby detection
                (about every 5 floors / 23 m) is checked by the platform across the floors.
              </p>
              <ul className="mt-3 space-y-2">
                {review.rules.map((r) => (
                  <li key={r.system}>
                    <span className="font-semibold text-navy-900">{r.name}:</span> {r.rule}
                  </li>
                ))}
              </ul>
              <h3 className="mt-6 font-semibold text-navy-900">Engineers&apos; rulings ({review.rulings.length})</h3>
              <p className="mt-1 text-gray-600">
                Every change marked <b>Not needed</b> or <b>accepted</b> is kept here and given to the AI with the rules on every
                review after it, on every project. A &quot;not needed&quot; also settles the same change in the same kind of room on
                the other floors at once.
              </p>
              {review.rulings.length === 0 ? (
                <p className="mt-2 text-gray-400">None yet.</p>
              ) : (
                <ul className="mt-3 divide-y divide-gray-100">
                  {review.rulings.map((r) => (
                    <li key={r.id} className="flex flex-wrap items-start justify-between gap-2 py-2">
                      <div className="min-w-0">
                        <span
                          className={`mr-2 rounded px-1.5 py-0.5 text-xs font-bold ${r.decision === "dismissed" ? "bg-gray-200 text-gray-700" : "bg-emerald-100 text-emerald-800"}`}
                        >
                          {r.decision === "dismissed" ? "NOT NEEDED" : "CONFIRMED"}
                        </span>
                        <span className="font-medium">
                          {r.action.toUpperCase()} {r.device || r.system_name}
                        </span>{" "}
                        <span className="text-gray-500">in {r.room || "this kind of space"}</span>
                        {(r.note || r.instruction) && (
                          <div className="text-xs text-gray-500">{r.decision === "dismissed" ? r.note : r.instruction}</div>
                        )}
                      </div>
                      {canEdit && (
                        <button type="button" onClick={() => void deleteRuling(r.id)} className="text-xs text-rose-700 hover:underline">
                          Remove
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}

function Findings({
  projectId,
  drawingId,
  review,
  canEdit,
  onDecide,
  onAcceptAll,
}: {
  projectId: number;
  drawingId: number;
  review: Review;
  canEdit: boolean;
  onDecide: (f: Finding, status: "accepted" | "dismissed" | "open", instruction?: string, note?: string) => void;
  onAcceptAll: (ids: string[]) => void;
}) {
  const [floor, setFloor] = useState("");
  const [system, setSystem] = useState("");
  const [action, setAction] = useState<Action | "">("");
  const [state, setState] = useState<"open" | "accepted" | "dismissed" | "">("open");
  const [kinds, setKinds] = useState<"issues" | "all">("issues");
  const shown = useMemo(
    () =>
      review.findings.filter(
        (f) =>
          (!floor || f.floor === floor) &&
          (!system || f.system === system) &&
          (!action || f.action === action) &&
          (!state || f.decision === state) &&
          (kinds === "all" || f.action !== "none"),
      ),
    [review.findings, floor, system, action, state, kinds],
  );
  const floors = [...new Set(review.findings.map((f) => f.floor))];
  if (!review.findings.length) {
    return (
      <p className="mt-4 rounded-2xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-500">
        {review.state === "done"
          ? `Review completed: no changes proposed. ${review.counts.reviewed} of ${review.counts.rooms} rooms reviewed.`
          : review.state_message ?? "The drawing has not been reviewed yet."}
      </p>
    );
  }
  return (
    <div className="mt-4 space-y-3">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <select value={floor} onChange={(e) => setFloor(e.target.value)} className="rounded-lg border border-gray-300 bg-white px-2 py-1.5">
          <option value="">All floors</option>
          {floors.map((f) => (
            <option key={f}>{f}</option>
          ))}
        </select>
        <select value={system} onChange={(e) => setSystem(e.target.value)} className="rounded-lg border border-gray-300 bg-white px-2 py-1.5">
          <option value="">All systems</option>
          {Object.entries(review.systems).map(([key, name]) => (
            <option key={key} value={key}>
              {name}
            </option>
          ))}
        </select>
        <select value={action} onChange={(e) => setAction(e.target.value as typeof action)} className="rounded-lg border border-gray-300 bg-white px-2 py-1.5">
          <option value="">Add, remove and replace</option>
          <option value="add">Add</option>
          <option value="remove">Remove</option>
          <option value="replace">Replace</option>
        </select>
        <select value={state} onChange={(e) => setState(e.target.value as typeof state)} className="rounded-lg border border-gray-300 bg-white px-2 py-1.5">
          <option value="open">Open</option>
          <option value="accepted">Accepted</option>
          <option value="dismissed">Dismissed</option>
          <option value="">All</option>
        </select>
        <label className="flex items-center gap-1.5 text-gray-600">
          <input type="checkbox" checked={kinds === "all"} onChange={(e) => setKinds(e.target.checked ? "all" : "issues")} />
          show "unclear" too
        </label>
        <span className="text-xs text-gray-500">{shown.length} shown</span>
        {canEdit && shown.some((f) => f.decision === "open" && f.action !== "none") && (
          <button
            type="button"
            onClick={() => onAcceptAll(shown.filter((f) => f.decision === "open" && f.action !== "none").map((f) => f.id))}
            className="ml-auto rounded-lg border border-emerald-600 px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50"
          >
            Accept all shown
          </button>
        )}
      </div>
      {shown.map((f) => (
        <FindingCard key={f.id} f={f} projectId={projectId} drawingId={drawingId} canEdit={canEdit} onDecide={onDecide} />
      ))}
    </div>
  );
}

const QUICK_REASONS = ["Already shown on the drawing", "Not required by the code here", "Covered by another device", "Outside our scope"];

function FindingCard({
  f,
  projectId,
  drawingId,
  canEdit,
  onDecide,
}: {
  f: Finding;
  projectId: number;
  drawingId: number;
  canEdit: boolean;
  onDecide: (f: Finding, status: "accepted" | "dismissed" | "open", instruction?: string, note?: string) => void;
}) {
  // the reason for "not needed", and the draftsman's instruction to edit, are asked on the card itself
  const [mode, setMode] = useState<"none" | "dismiss" | "edit">("none");
  const [reason, setReason] = useState("");
  const [text, setText] = useState(f.instruction || f.issue);
  return (
        <article className="flex flex-wrap gap-4 rounded-2xl border border-gray-200 bg-white p-3">
          <a
            href={apiUrl(`/projects/${projectId}/drawing-review/${drawingId}/image?page=${f.page}&box=${f.box.join(",")}&width=1800${f.mark ? `&mark=${f.mark.join(",")}` : ""}`)}
            target="_blank"
            rel="noreferrer"
            title="Open larger"
          >
            <img
              loading="lazy"
              alt={`${f.room} on ${f.floor}`}
              src={apiUrl(`/projects/${projectId}/drawing-review/${drawingId}/image?page=${f.page}&box=${f.box.join(",")}&width=420${f.mark ? `&mark=${f.mark.join(",")}` : ""}`)}
              className="h-56 w-56 rounded-lg border border-gray-200 object-contain"
            />
          </a>
          <div className="min-w-0 flex-1 basis-80 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-navy-900">{f.floor}</span>
              <span className="text-gray-400">·</span>
              <span className="font-medium">{f.room || f.sheet}</span>
              {f.room_type && <span className="text-xs text-gray-500">({f.room_type})</span>}
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{KIND_TEXT[f.kind]}</span>
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{f.system_name}</span>
            </div>
            <p className="mt-2 flex flex-wrap items-baseline gap-2">
              <span className={`rounded px-2 py-0.5 text-xs font-bold ${ACTION_STYLE[f.action]}`}>{ACTION_TEXT[f.action]}</span>
              {f.device && <span className="font-semibold text-navy-900">{f.device}</span>}
            </p>
            <p className="mt-1 font-medium text-gray-900">{f.instruction || f.issue}</p>
            {f.instruction && f.issue && f.instruction !== f.issue && <p className="mt-0.5 text-xs text-gray-500">{f.issue}</p>}
            {f.seen && <p className="mt-0.5 text-xs text-gray-500">The AI saw: {f.seen}</p>}
            {f.previous_decision && f.decision === "open" && (
              <p className="mt-1 rounded bg-amber-50 px-2 py-1 text-xs text-amber-900">
                {f.previous_decision.status === "accepted" ? "Accepted" : "Dismissed"} earlier
                {f.previous_decision.at ? ` (${f.previous_decision.at.slice(0, 10)})` : ""}
                {f.previous_decision.note ? `: ${f.previous_decision.note}` : ""}. Not carried over:{" "}
                {f.previous_decision.message} Decide again.
              </p>
            )}
            {f.decision !== "open" && (
              <p className={`mt-1 text-xs font-medium ${f.decision === "accepted" ? "text-emerald-700" : "text-gray-500"}`}>
                {f.decision === "accepted"
                  ? "Accepted: on the draftsman's mark-up"
                  : f.by_ruling
                    ? `Not needed: ${f.note}`
                    : `Not needed${f.note ? `: ${f.note}` : ""}`}
              </p>
            )}
            {canEdit && mode === "dismiss" && (
              <div className="mt-2 rounded-lg border border-gray-200 bg-gray-50 p-2">
                <div className="text-xs font-medium text-gray-700">Why is it not needed? (kept as a ruling for the next reviews)</div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {QUICK_REASONS.map((r) => (
                    <button key={r} type="button" onClick={() => setReason(r)} className="rounded-full border border-gray-300 bg-white px-2 py-0.5 text-xs text-gray-700 hover:border-brand-400">
                      {r}
                    </button>
                  ))}
                </div>
                <input
                  autoFocus
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && reason.trim() && (onDecide(f, "dismissed", "", reason.trim()), setMode("none"))}
                  placeholder="e.g. electrical rooms have no speakers on this project"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
                />
                <div className="mt-1 flex gap-2">
                  <button
                    type="button"
                    disabled={!reason.trim()}
                    onClick={() => {
                      onDecide(f, "dismissed", "", reason.trim());
                      setMode("none");
                    }}
                    className="rounded-lg bg-gray-700 px-3 py-1 text-xs font-semibold text-white hover:bg-gray-800 disabled:opacity-40"
                  >
                    Save: not needed
                  </button>
                  <button type="button" onClick={() => setMode("none")} className="rounded-lg px-3 py-1 text-xs text-gray-600 hover:bg-gray-100">
                    Cancel
                  </button>
                </div>
              </div>
            )}
            {canEdit && mode === "edit" && (
              <div className="mt-2 rounded-lg border border-emerald-200 bg-emerald-50/50 p-2">
                <div className="text-xs font-medium text-gray-700">The instruction for the draftsman</div>
                <textarea value={text} onChange={(e) => setText(e.target.value)} rows={2} className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1 text-sm" />
                <div className="mt-1 flex gap-2">
                  <button
                    type="button"
                    disabled={!text.trim()}
                    onClick={() => {
                      onDecide(f, "accepted", text.trim());
                      setMode("none");
                    }}
                    className="rounded-lg bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-40"
                  >
                    Save &amp; accept
                  </button>
                  <button type="button" onClick={() => setMode("none")} className="rounded-lg px-3 py-1 text-xs text-gray-600 hover:bg-gray-100">
                    Cancel
                  </button>
                </div>
              </div>
            )}
            {canEdit && mode === "none" && (
              <div className="mt-2 flex flex-wrap gap-2">
                {f.decision === "open" ? (
                  <>
                    {f.action !== "none" && (
                      <>
                        <button type="button" onClick={() => onDecide(f, "accepted")} className="rounded-lg bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-700">
                          Accept for draftsman
                        </button>
                        <button type="button" onClick={() => setMode("edit")} className="rounded-lg border border-emerald-600 px-3 py-1 text-xs font-semibold text-emerald-700 hover:bg-emerald-50">
                          Edit &amp; accept
                        </button>
                      </>
                    )}
                    <button type="button" onClick={() => setMode("dismiss")} className="rounded-lg border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50">
                      Not needed
                    </button>
                  </>
                ) : (
                  <button type="button" onClick={() => onDecide(f, "open")} className="rounded-lg px-3 py-1 text-xs text-gray-600 hover:bg-gray-100">
                    Reopen
                  </button>
                )}
              </div>
            )}
          </div>
        </article>
  );
}

function Rooms({ review }: { review: Review }) {
  const systems = Object.entries(review.systems);
  return (
    <div className="mt-4 space-y-4">
      {review.floors.map((floor) => (
        <section key={floor.page} className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-gray-100 px-4 py-2.5">
            <div className="font-semibold text-navy-900">
              {floor.floor} <span className="text-xs font-normal text-gray-500">{floor.sheet} · {floor.title}</span>
            </div>
            <div className="text-xs text-gray-500">
              {floor.windows_done} of {floor.windows} parts reviewed
              {floor.windows_failed ? ` · ${floor.windows_failed} could not be reviewed` : ""}
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
                <tr>
                  <th className="px-3 py-2">Room</th>
                  <th className="px-3 py-2">What it is</th>
                  {systems.map(([key, name]) => (
                    <th key={key} className="px-2 py-2 text-center" title={name}>
                      {name.split(" ")[0].replace("/", "")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {floor.rooms.map((room) => (
                  <tr key={room.id}>
                    <td className="px-3 py-1.5 font-medium">{room.name}</td>
                    <td className="px-3 py-1.5 text-xs text-gray-500">{room.room_type ||
                        (room.status === "failed"
                          ? "could not be reviewed"
                          : room.status === "incomplete"
                            ? "not answered: asked again on the next review"
                            : "—")}</td>
                    {systems.map(([key]) => {
                      const check = room.checks?.[key];
                      return (
                        <td key={key} className="px-2 py-1.5 text-center" title={check?.seen}>
                          {check ? (
                            <span className={`inline-block min-w-8 rounded px-1.5 py-0.5 text-xs font-semibold ${STATUS_STYLE[check.status]}`}>
                              {STATUS_TEXT[check.status]}
                            </span>
                          ) : (
                            <span className="text-gray-300">·</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}
