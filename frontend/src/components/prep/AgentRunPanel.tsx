/** What the last placing of the drawing's devices did: the placement agents,
 * the coordination (columns, 6.3 m coverage, the coordination agents), the
 * orchestrator's floor reviews, and the platform's gate -- as the FA
 * Interfaces run panel shows its agents and Opus review. */
import { useState } from "react";

import type { Job } from "../../lib/useJob";
import type { Run } from "./types";

const STAGES = [
  ["placement", "Placement agents"],
  ["coordination", "Coordination"],
  ["review", "Orchestrator review"],
  ["done", "Gate"],
] as const;

export function StageProgress({ run, job, canEdit, onStop }: { run: Run | null; job: Job | null; canEdit: boolean; onStop: () => void }) {
  const progress = job?.progress as { done?: number; total?: number; message?: string } | undefined;
  // the run this job is making: one not finished yet (the last one's, until the new one starts)
  const stage = run && run.finished_at === null ? run.stage : "placement";
  const at = STAGES.findIndex(([key]) => key === stage);
  return (
    <section className="mt-4 rounded-2xl border border-brand-200 bg-brand-50/50 p-4 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        {STAGES.map(([key, label], i) => (
          <span
            key={key}
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              i < at ? "bg-green-100 text-green-800" : i === at ? "bg-brand-600 text-white" : "bg-white text-gray-400"
            }`}
          >
            {i < at ? "✓ " : ""}
            {label}
          </span>
        ))}
        {canEdit && (
          <button type="button" onClick={onStop} className="ml-auto rounded-lg px-3 py-1.5 text-sm text-gray-600 hover:bg-white">
            Stop
          </button>
        )}
      </div>
      <div className="mt-3 font-semibold text-navy-900">{progress?.message ?? "Queued: waiting for the IFC worker"}</div>
      {progress?.total ? (
        <div className="mt-2 h-1.5 w-96 max-w-full overflow-hidden rounded-full bg-white">
          <div className="h-full bg-brand-600" style={{ width: `${Math.round(((progress.done ?? 0) / progress.total) * 100)}%` }} />
        </div>
      ) : null}
      <div className="mt-1 text-xs text-gray-500">The changes below update as the agents answer. You can leave this page.</div>
    </section>
  );
}

export function AgentRunPanel({ run, agentsOn }: { run: Run; agentsOn: boolean }) {
  const [open, setOpen] = useState(false);
  const gate = run.gate;
  const co = run.coordination;
  const pl = run.placement;
  const rv = run.review;
  const tone =
    gate?.state === "ready"
      ? "border-green-200 bg-green-50/60"
      : gate
        ? "border-amber-200 bg-amber-50/60"
        : "border-gray-200 bg-white";
  return (
    <section className={`mt-4 rounded-2xl border p-4 text-sm ${tone}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-base font-semibold text-navy-900">
            {gate === null
              ? "Placing…"
              : gate.state === "ready"
                ? "Ready for the draftsman"
                : `Needs the engineer: ${gate.reasons.length} thing${gate.reasons.length === 1 ? "" : "s"} to settle`}
          </div>
          <div className="mt-1 text-xs text-gray-600">
            {run.ai ? (
              <>
                {run.parallel} agents at once · placement and coordination on {run.model} · review on {run.orchestrator_model}
              </>
            ) : (
              <>Agents off: placed at the review&rsquo;s points and coordinated by the platform alone</>
            )}{" "}
            · detector radius {run.radius.smoke} m (smoke), {run.radius.heat} m (heat)
            {run.finished_at ? ` · finished ${new Date(run.finished_at).toLocaleString()}` : ""}
          </div>
        </div>
        <button type="button" onClick={() => setOpen(!open)} className="text-xs font-semibold text-brand-700 hover:underline">
          {open ? "Hide reports" : "Show reports"}
        </button>
      </div>

      {gate && gate.reasons.length > 0 && (
        <ul className="mt-3 list-disc space-y-0.5 pl-5 text-amber-900">
          {gate.reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}
      {!agentsOn && (
        <p className="mt-3 rounded-lg bg-white/70 px-3 py-2 text-xs text-gray-600">
          The placement, coordination and orchestrator agents are switched off on this installation (PREP_AI_ENABLED). The platform still
          places every change, keeps devices off columns and each other, and measures each room&rsquo;s coverage; turn the agents on to
          have Opus place, coordinate and review them.
        </p>
      )}

      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <div className="rounded-xl bg-white/80 p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">1 · Placement</div>
          {pl ? (
            <div className="mt-1 text-navy-900">
              {pl.placed} placed{pl.failed ? `, ${pl.failed} failed` : ""} of {pl.total}
              <div className="text-xs text-gray-500">
                {pl.by === "platform" ? "by the platform" : `${pl.calls} agent calls${pl.seconds ? ` · ${Math.round(pl.seconds)} s` : ""}`}
              </div>
            </div>
          ) : (
            <div className="mt-1 text-gray-400">—</div>
          )}
        </div>
        <div className="rounded-xl bg-white/80 p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">2 · Coordination</div>
          {co ? (
            <div className="mt-1 text-navy-900">
              {co.rooms} room{co.rooms === 1 ? "" : "s"} measured · {co.issues} with something to settle
              <div className="text-xs text-gray-500">
                {co.columns ?? 0} columns read · {co.moved} moved · {co.added} detector{co.added === 1 ? "" : "s"} added
                {co.agent_rooms ? ` · ${co.agent_rooms} rooms by the agent` : ""}
                {co.refused ? ` · ${co.refused} agent answers refused` : ""}
                {co.gaps_left ? ` · ${co.gaps_left} short of coverage` : ""}
                {co.open_rooms ? ` · ${co.open_rooms} not measurable` : ""}
              </div>
            </div>
          ) : (
            <div className="mt-1 text-gray-400">—</div>
          )}
        </div>
        <div className="rounded-xl bg-white/80 p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">3 · Orchestrator review</div>
          {rv ? (
            <div className="mt-1 text-navy-900">
              {rv.state === "off"
                ? "Not run (agents off)"
                : rv.state === "nothing"
                  ? "Nothing to review"
                  : `${rv.floors.filter((f) => f.state === "done").length} of ${rv.floors.length} floors reviewed`}
              {rv.state !== "off" && rv.state !== "nothing" && (
                <div className="text-xs text-gray-500">
                  {rv.floors.reduce((n, f) => n + (f.verdicts?.reject ?? 0), 0)} rejected ·{" "}
                  {rv.floors.reduce((n, f) => n + (f.verdicts?.check ?? 0), 0)} to check · {rv.calls} calls
                </div>
              )}
            </div>
          ) : (
            <div className="mt-1 text-gray-400">—</div>
          )}
        </div>
      </div>

      {open && (
        <div className="mt-4 space-y-4">
          {rv && rv.floors.some((f) => f.state === "done") && (
            <div>
              <h3 className="font-semibold text-navy-900">The orchestrator, floor by floor</h3>
              <ul className="mt-2 space-y-2">
                {rv.floors.map((f) => (
                  <li key={f.page} className="rounded-lg bg-white/80 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold">{f.floor}</span>
                      {f.recommendation && (
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                            f.recommendation === "ready_for_draftsman" ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {f.recommendation === "ready_for_draftsman" ? "ready for the draftsman" : "needs the engineer"}
                        </span>
                      )}
                      {f.state === "failed" && <span className="text-xs text-red-700">not reviewed: {f.reason}</span>}
                    </div>
                    {f.summary && <p className="mt-1 text-gray-700">{f.summary}</p>}
                    {f.open_questions && f.open_questions.length > 0 && (
                      <ul className="mt-1 list-disc pl-5 text-xs text-gray-600">
                        {f.open_questions.map((q) => (
                          <li key={q}>{q}</li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {co?.rooms_detail && co.rooms_detail.length > 0 && (
            <div>
              <h3 className="font-semibold text-navy-900">Rooms coordinated</h3>
              <div className="mt-2 overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead className="text-left text-gray-500">
                    <tr>
                      <th className="py-1 pr-3">Floor</th>
                      <th className="py-1 pr-3">Room</th>
                      <th className="py-1 pr-3">Coverage</th>
                      <th className="py-1 pr-3">Found</th>
                      <th className="py-1 pr-3">By</th>
                    </tr>
                  </thead>
                  <tbody>
                    {co.rooms_detail.map((r) => (
                      <tr key={r.key} className="border-t border-gray-100 align-top">
                        <td className="py-1 pr-3">{r.floor}</td>
                        <td className="py-1 pr-3">{r.room || "—"}</td>
                        <td className="py-1 pr-3">
                          {r.open || !r.after ? (
                            <span className="text-amber-700">not measured</span>
                          ) : (
                            <span className={r.after.ok ? "text-green-700" : "text-red-700"}>
                              {Math.round(r.after.covered * 100)}% of {r.after.area_m2} m² at {r.radius} m
                            </span>
                          )}
                        </td>
                        <td className="py-1 pr-3">
                          {r.issues.join("; ") || "—"}
                          {r.refused.length > 0 && <div className="text-red-700">refused: {r.refused.join("; ")}</div>}
                        </td>
                        <td className="py-1 pr-3">{r.by}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {run.agents.length > 0 && (
            <div>
              <h3 className="font-semibold text-navy-900">Agents ({run.agents.length})</h3>
              <div className="mt-2 max-h-80 overflow-auto">
                <table className="min-w-full text-xs">
                  <thead className="sticky top-0 bg-white text-left text-gray-500">
                    <tr>
                      <th className="py-1 pr-3">Stage</th>
                      <th className="py-1 pr-3">Agent</th>
                      <th className="py-1 pr-3">Floor</th>
                      <th className="py-1 pr-3">State</th>
                      <th className="py-1 pr-3">Time</th>
                      <th className="py-1 pr-3">Outcome</th>
                    </tr>
                  </thead>
                  <tbody>
                    {run.agents.map((a, i) => (
                      <tr key={i} className="border-t border-gray-100 align-top">
                        <td className="py-1 pr-3">{a.stage}</td>
                        <td className="py-1 pr-3">{a.label}</td>
                        <td className="py-1 pr-3">{a.floor}</td>
                        <td className={`py-1 pr-3 ${a.state === "failed" ? "text-red-700" : "text-gray-700"}`}>{a.state}</td>
                        <td className="py-1 pr-3">{a.seconds} s</td>
                        <td className="py-1 pr-3 text-gray-600">{a.outcome}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
