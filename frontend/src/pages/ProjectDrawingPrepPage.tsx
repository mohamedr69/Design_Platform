/** Drawings Preparation: the fire alarm IFC drawing made ready for the
 * draftsman in one tab (platform owner, 6 October 2026), as four steps on one
 * drawing:
 *
 *  1. Review             the AI reads every room against the coverage rules and
 *                        proposes ADD / REMOVE / REPLACE; the engineer accepts;
 *  2. Devices            the accepted changes placed by agents side by side,
 *                        coordinated (columns, 6.3 m coverage) and reviewed by
 *                        the orchestrator; the engineer approves;
 *  3. Interface modules  the FA Interface Schedule's modules at their locations;
 *  4. Output             the draftsman's PDF, and the copy of the drawing with
 *                        the changes made on it. */
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { RedesignPanel } from "../components/prep/RedesignPanel";
import type { DrawingRow } from "../components/prep/types";
import { ApiError, api } from "../lib/api";
import { ProjectDrawingReviewPage } from "./ProjectDrawingReviewPage";
import { useProject } from "./ProjectWorkspace";

const STEPS = [
  ["review", "Review"],
  ["devices", "Devices"],
  ["interfaces", "Interface modules"],
  ["output", "Output: PDF & drawing copy"],
] as const;
type Step = (typeof STEPS)[number][0];

export function ProjectDrawingPrepPage() {
  const { project } = useProject();
  const [params, setParams] = useSearchParams();
  const [drawings, setDrawings] = useState<DrawingRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const step: Step = (STEPS.find(([key]) => key === params.get("step"))?.[0] ?? "review") as Step;
  const wanted = Number(params.get("drawing")) || null;

  const loadDrawings = useCallback(() => {
    api
      .get<{ drawings: DrawingRow[] }>(`/projects/${project.id}/redesign`)
      .then((body) => setDrawings(body.drawings))
      .catch((e) => setError(e instanceof ApiError ? e.message : "The drawings could not be loaded"));
  }, [project.id]);
  useEffect(() => loadDrawings(), [loadDrawings]);

  const drawing =
    drawings?.find((d) => d.id === wanted) ?? drawings?.find((d) => d.review_state === "done") ?? drawings?.[0] ?? null;

  function go(next: { step?: Step; drawing?: number }) {
    const p = new URLSearchParams(params);
    if (next.step) p.set("step", next.step);
    if (next.drawing) p.set("drawing", String(next.drawing));
    setParams(p, { replace: true });
  }

  function badge(key: Step): [string, string] | null {
    if (!drawing) return null;
    const done: [string, string] = ["✓", "text-green-700"];
    const busy: [string, string] = ["…", "text-gray-500"];
    if (key === "review") {
      // the checkmark only for a review a model completed: a plot alone, a blocked or failed run is not one
      const state = drawing.review_state;
      if (state === "done") return done;
      if (state === "running") return busy;
      if (state === "partial") return ["part", "text-amber-700"];
      if (state === "blocked" || state === "failed") return ["!", "text-red-700"];
      if (state === "not_reviewed" && drawing.review_status) return ["!", "text-amber-700"];
      return null;
    }
    if (key === "devices") return drawing.redesign_status === "planned" ? done : drawing.redesign_status === "planning" ? busy : null;
    if (key === "output") return drawing.output_status === "made" ? done : null;
    return null;
  }

  return (
    <div className="mt-2">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-3xl">
          <h1 className="text-3xl font-bold text-navy-900">Drawings Preparation</h1>
          <p className="mt-1 text-sm text-gray-600">
            The fire alarm IFC drawing made ready for the draftsman, step by step: reviewed room by room, the accepted devices placed and
            coordinated by agents (no device on a column or another device, every room covered at 6.3 m), the interface modules at their
            equipment, then a marked-up PDF for the draftsman and a copy of the drawing with the changes made on it.
          </p>
        </div>
        {drawings && drawings.length > 1 && drawing && (
          <select
            value={drawing.id}
            onChange={(e) => go({ drawing: Number(e.target.value) })}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
          >
            {drawings.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename} {d.revision}
                {d.review_state === "done" ? "" : d.review_state === "partial" ? " (partly reviewed)" : " (not reviewed)"}
              </option>
            ))}
          </select>
        )}
      </div>

      {error && <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}
      {drawings && drawings.length === 0 && (
        <p className="mt-6 rounded-2xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-500">
          No fire alarm IFC drawing has been imported for this project. Import it on the BOQ page&apos;s As per IFC Drawings tab.
        </p>
      )}

      {drawing && (
        <>
          <nav className="mt-5 flex flex-wrap gap-1 border-b border-gray-200" role="tablist">
            {STEPS.map(([key, label], i) => (
              <button
                key={key}
                role="tab"
                aria-selected={step === key}
                onClick={() => go({ step: key })}
                className={`-mb-px flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-semibold ${
                  step === key ? "border-brand-600 text-brand-700" : "border-transparent text-gray-500 hover:text-navy-900"
                }`}
              >
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] ${
                    step === key ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {i + 1}
                </span>
                {label}
                {badge(key) && <span className={`text-xs ${badge(key)![1]}`}>{badge(key)![0]}</span>}
              </button>
            ))}
          </nav>

          {step === "review" && <ProjectDrawingReviewPage embedded drawingId={drawing.id} onChanged={loadDrawings} />}
          {step !== "review" && (
            <RedesignPanel key={`${drawing.id}:${step}`} projectId={project.id} drawing={drawing} section={step} onChanged={loadDrawings} />
          )}
        </>
      )}
    </div>
  );
}
