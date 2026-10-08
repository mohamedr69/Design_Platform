import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api, apiUrl } from "../../lib/api";
import { useOnProjectChange } from "../../lib/projectChanges";
import { SyncDocumentsCard } from "../SyncDocumentsCard";
import { DrawingDetailPanel } from "./DrawingDetailPanel";
import { Chip, EyeIcon, FolderIcon, HintBadge, StatusIcon } from "./StatusChip";
import type { DrawingsLog, IfcFolderFile, LogRow, Status, SystemSummary } from "./types";
import { STATUS_LABEL, day } from "./types";

const SUMMARY_ORDER: Status[] = ["approved", "approved_as_noted", "under_review", "not_approved", "not_submitted", "reply_not_found"];
const PAGE_SIZES = [12, 25, 50, 100];

/** The group a row belongs to: its IFC sheet, or itself when it is on no sheet. */
function groupKey(row: LogRow): string {
  return row.ifc?.key ?? row.key;
}

function groupLabel(row: LogRow): string {
  return row.ifc ? `${row.ifc.sheet} · ${row.ifc.label}` : `${row.floor} (no IFC drawing)`;
}

/** The Drawings Log: one row per IFC drawing (a typical sheet for floors
 *  3 to 16 is one drawing, and the shop drawing submitted against it is
 *  one submission), with the selected system's shop drawing at each
 *  official revision. A file found at a newer revision is a hint ("R1
 *  available"), never a status. */
export function DrawingsLogTab({
  projectId,
  canEdit,
  system,
  summary,
  openDrawing,
  onOpenDrawing,
  onSystemsKnown,
  onChanged,
  onReview,
}: {
  projectId: number;
  canEdit: boolean;
  system: string;
  summary: SystemSummary | null;
  openDrawing: number | null;
  onOpenDrawing: (id: number | null) => void;
  onSystemsKnown: (codes: string[]) => void;
  onChanged: () => void;
  onReview: () => void;
}) {
  const [log, setLog] = useState<DrawingsLog | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [sheet, setSheet] = useState("");
  const [status, setStatus] = useState<Status | "">("");
  const [query, setQuery] = useState("");
  const [issuesOnly, setIssuesOnly] = useState(false);
  const [showDetected, setShowDetected] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(12);

  const load = useCallback(() => {
    api
      .get<DrawingsLog>(`/projects/${projectId}/drawings/log?system=${encodeURIComponent(system)}&view=ifc`)
      .then((d) => {
        setLog(d);
        setError("");
        onSystemsKnown(d.systems);
      })
      .catch((e) => setError(`The drawings log could not be loaded: ${e.message}`));
  }, [projectId, system, onSystemsKnown]);

  useEffect(() => {
    load();
    setPage(1);
  }, [load]);
  // The records are the sync's and the engineer's: either changing reloads the log here.
  useOnProjectChange(["documents", "drawing"], load);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (log?.rows ?? []).filter(
      (r) =>
        (!sheet || groupKey(r) === sheet) &&
        (!status || r.latest_status === status) &&
        (!issuesOnly || r.hints.length > 0) &&
        (!q ||
          r.floor.toLowerCase().includes(q) ||
          (r.reference ?? "").toLowerCase().includes(q) ||
          r.remarks.toLowerCase().includes(q) ||
          (r.ifc ? `${r.ifc.sheet} ${r.ifc.label} ${r.ifc.title} ${r.ifc.range} ${r.ifc.floor_names.join(" ")}`.toLowerCase().includes(q) : false)),
    );
  }, [log, sheet, status, query, issuesOnly]);
  // The IFC drawings (and the floors on none), in the log's order, for the filter.
  const groups = useMemo(() => {
    const seen = new Map<string, string>();
    for (const r of log?.rows ?? []) if (!seen.has(groupKey(r))) seen.set(groupKey(r), groupLabel(r));
    return [...seen.entries()];
  }, [log]);
  const pages = Math.max(1, Math.ceil(rows.length / pageSize));
  const shown = rows.slice((Math.min(page, pages) - 1) * pageSize, Math.min(page, pages) * pageSize);

  const openFolder = async (path: string | null) => {
    setNotice("");
    try {
      await api.post(`/projects/${projectId}/drawings/open-folder`, path ? { path, system } : { system });
    } catch (e) {
      setNotice((e as Error).message);
    }
  };

  const exportLog = () =>
    api
      .download(`/projects/${projectId}/drawings/log/export.xlsx?system=${encodeURIComponent(system)}&view=ifc`, `EP-${log?.project.ep_number ?? projectId} Drawings Log ${system}.xlsx`)
      .catch((e) => setError(e.message));

  const selected = openDrawing !== null ? ([...(log?.rows ?? []), ...(log?.others ?? [])].find((r) => r.id === openDrawing) ?? null) : null;

  return (
    <div className="space-y-4">
      <SyncDocumentsCard projectId={projectId} canEdit={canEdit} compact onSynced={() => { load(); onChanged(); }} />
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-800">{error}</div>}
      {notice && <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-900">{notice}</div>}
      {log?.warnings.map((w) => (
        <div key={w} className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-900">{w}</div>
      ))}

      {/* The system's numbers: each status at the latest revision. Click one to filter. */}
      {log && (
        <div className="rounded-xl border border-gray-200 bg-white px-5 py-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div>
              <div className="text-base font-bold text-navy-900">{log.system_name} ({log.system})</div>
              <div className="text-xs text-gray-500">Shop drawing status summary · {log.sheets ? `${log.sheets} IFC drawings` : `${log.rows.length} drawings`}</div>
            </div>
            <IfcFolderPanel projectId={projectId} log={log} canEdit={canEdit} onQueued={(text) => { setNotice(text); load(); }} onError={setNotice} />
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-7">
            <Tile label={log.sheets ? "IFC Drawings" : "Drawings"} value={log.sheets || log.rows.length} active={!status && !issuesOnly} onClick={() => { setStatus(""); setIssuesOnly(false); setPage(1); }} />
            {SUMMARY_ORDER.map((s) => (
              <Tile key={s} label={STATUS_LABEL[s]} value={log.counts[s] ?? 0} icon={<StatusIcon status={s} className="h-5 w-5" />} active={status === s} onClick={() => { setStatus(status === s ? "" : s); setIssuesOnly(false); setPage(1); }} />
            ))}
            <Tile label="Review Items" value={log.review_items} tone="rose" active={issuesOnly} onClick={onReview} />
          </div>
        </div>
      )}

      <div className="flex gap-4">
        <div className={`min-w-0 flex-1 rounded-xl border border-gray-200 bg-white ${selected ? "hidden xl:block" : ""}`}>
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-gray-100 p-5">
            <div>
              <h2 className="text-xl font-bold">Drawings Log</h2>
              <p className="mt-1 text-sm text-gray-500">Each IFC drawing with the shop drawing submitted against it: its revision status, the latest consultant response and detected new revisions.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select value={sheet} onChange={(e) => { setSheet(e.target.value); setPage(1); }} className="rounded-lg border border-gray-300 px-3 py-2 text-sm" aria-label="IFC drawing">
                <option value="">All IFC Drawings</option>
                {groups.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
              </select>
              <select value={status} onChange={(e) => { setStatus(e.target.value as Status | ""); setPage(1); }} className="rounded-lg border border-gray-300 px-3 py-2 text-sm" aria-label="Status">
                <option value="">All Status</option>
                {SUMMARY_ORDER.map((s) => (
                  <option key={s} value={s}>{STATUS_LABEL[s]}{log?.counts[s] ? ` (${log.counts[s]})` : ""}</option>
                ))}
              </select>
              <input value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} placeholder="Search IFC drawing, floor or reference…" className="w-64 rounded-lg border border-gray-300 px-3 py-2 text-sm" aria-label="Search IFC drawing, floor or drawing reference" />
              {(sheet || status || query || issuesOnly) && (
                <button type="button" onClick={() => { setSheet(""); setStatus(""); setQuery(""); setIssuesOnly(false); setPage(1); }} className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">Clear</button>
              )}
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" checked={issuesOnly} onChange={(e) => { setIssuesOnly(e.target.checked); setPage(1); }} className="h-4 w-4" /> Issues only
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700" title="Show files found at a newer revision than the official latest">
                <input type="checkbox" checked={showDetected} onChange={(e) => setShowDetected(e.target.checked)} className="h-4 w-4" /> Show detected revisions
              </label>
              <button type="button" onClick={exportLog} disabled={!log?.rows.length} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-navy-900 hover:bg-gray-50 disabled:opacity-50">Export</button>
              <button type="button" onClick={() => openFolder(null)} disabled={!log?.folder} className="flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2 text-sm font-semibold text-navy-900 hover:bg-gray-50 disabled:opacity-50" title={log?.folder ?? "The project has no folder"}>
                <FolderIcon /> Folder
              </button>
            </div>
          </div>

          {log === null ? (
            <div className="p-6 text-sm text-gray-500">{error ? "" : "Loading the drawings log…"}</div>
          ) : log.rows.length === 0 ? (
            <div className="p-6 text-sm text-gray-600">
              No shop drawing of this system is in the project folder yet, and no IFC drawing is imported. Sync the documents once one is filed; the
              drawings still to submit show here once the IFC drawing is imported on{" "}
              <Link to={`/projects/${projectId}/boq`} className="font-medium text-brand-700 hover:underline">BOQ &gt; As per IFC Drawings</Link>.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="border-b border-gray-200 bg-gray-50 text-left text-sm font-semibold text-navy-900">
                  <tr>
                    <th className="px-3 py-3">#</th>
                    <th className="px-3 py-3">IFC Drawing</th>
                    <th className="px-3 py-3">Shop Drawing Reference</th>
                    {log.revisions.map((r) => (
                      <th key={r} className="px-3 py-3 text-center">{r}</th>
                    ))}
                    <th className="px-3 py-3 text-center">Latest Rev</th>
                    <th className="px-3 py-3">Latest Status</th>
                    <th className="px-3 py-3">Issues / Hints</th>
                    <th className="px-3 py-3 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {shown.map((r) => (
                    <LogTableRow
                      key={r.key}
                      row={r}
                      index={log.rows.indexOf(r) + 1}
                      revisions={log.revisions}
                      showDetected={showDetected}
                      selected={selected?.key === r.key}
                      projectId={projectId}
                      onOpen={() => r.id !== null && onOpenDrawing(r.id)}
                      onFolder={() => openFolder(r.latest_path)}
                      folder={!!log.folder}
                    />
                  ))}
                  {rows.length === 0 && (
                    <tr>
                      <td colSpan={log.revisions.length + 7} className="px-4 py-6 text-center text-gray-500">No drawing matches the filter.</td>
                    </tr>
                  )}
                </tbody>
              </table>
              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 px-5 py-3 text-sm text-gray-500">
                <span>Showing {shown.length ? (Math.min(page, pages) - 1) * pageSize + 1 : 0} to {(Math.min(page, pages) - 1) * pageSize + shown.length} of {rows.length} drawings</span>
                <div className="flex items-center gap-2">
                  <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded-md border border-gray-300 px-2 py-1 disabled:opacity-40" aria-label="Previous page">‹</button>
                  {Array.from({ length: pages }, (_, i) => i + 1).slice(Math.max(0, Math.min(page, pages) - 3), Math.max(0, Math.min(page, pages) - 3) + 6).map((n) => (
                    <button key={n} type="button" onClick={() => setPage(n)} aria-current={n === Math.min(page, pages)} className={`rounded-md px-2.5 py-1 ${n === Math.min(page, pages) ? "bg-brand-600 text-white" : "border border-gray-300 hover:bg-gray-50"}`}>{n}</button>
                  ))}
                  <button type="button" disabled={page >= pages} onClick={() => setPage(page + 1)} className="rounded-md border border-gray-300 px-2 py-1 disabled:opacity-40" aria-label="Next page">›</button>
                  <span className="ml-3">Rows per page</span>
                  <select value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }} className="rounded-md border border-gray-300 px-2 py-1" aria-label="Rows per page">
                    {PAGE_SIZES.map((n) => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
              </div>
              {/* Shop drawings for floors the IFC drawings have no sheet for: listed apart, not counted among the IFC drawings. */}
              {(log.others ?? []).length > 0 && !sheet && !status && !issuesOnly && !query && (
                <div className="border-t border-gray-100">
                  <div className="px-5 pb-1 pt-3 text-xs font-semibold text-gray-500">Not on an IFC drawing ({log.others!.length})</div>
                  <table className="min-w-full text-sm">
                    <tbody className="divide-y divide-gray-100">
                      {log.others!.map((r, i) => (
                        <LogTableRow
                          key={r.key}
                          row={r}
                          index={i + 1}
                          revisions={log.revisions}
                          showDetected={showDetected}
                          selected={selected?.key === r.key}
                          projectId={projectId}
                          onOpen={() => r.id !== null && onOpenDrawing(r.id)}
                          onFolder={() => openFolder(r.latest_path)}
                          folder={!!log.folder}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>

        {selected && selected.id !== null && (
          <DrawingDetailPanel
            projectId={projectId}
            drawingId={selected.id}
            canEdit={canEdit}
            summary={summary}
            onClose={() => onOpenDrawing(null)}
            onChanged={() => { load(); onChanged(); }}
          />
        )}
      </div>
    </div>
  );
}

function fileSize(bytes: number): string {
  return bytes >= 1e6 ? `${(bytes / 1e6).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1e3))} KB`;
}

/** The system's IFC folder in the project folder (03- Drawings/IFC/
 *  Electrical/FA for the fire alarm): the files there, which are read into
 *  the platform (the rows' sheets come from those), which are being read,
 *  and a Read button for a DWG or DXF not read yet. The read is the IFC
 *  worker's, as an upload on BOQ > As per IFC Drawings would be. */
function IfcFolderPanel({ projectId, log, canEdit, onQueued, onError }: {
  projectId: number; log: DrawingsLog; canEdit: boolean; onQueued: (notice: string) => void; onError: (notice: string) => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const folder = log.ifc_folder;
  const read = async (file: IfcFolderFile) => {
    setBusy(file.path);
    try {
      const job = await api.post<{ id: number; already_active?: boolean }>(`/projects/${projectId}/ifc-drawings/folder/jobs`, { path: file.path });
      onQueued(job.already_active ? `${file.name} is already being read (job ${job.id}).` : `${file.name} is queued for the IFC worker (job ${job.id}): the log updates when it is read.`);
    } catch (e) {
      const err = e as ApiError;
      const hint = err.code === "revision_confirmation_required" ? " Read it as a revision on BOQ > As per IFC Drawings." : "";
      onError(`${file.name} was not queued: ${err.message}${hint}`);
    } finally {
      setBusy(null);
    }
  };
  // The drawings the rows come from, in one line; the folder and its files
  // on hover. Only a DWG or DXF filed but not read yet is offered to read.
  const readNames = log.ifc.map((d) => `${d.filename} ${d.revision}`).join(", ");
  const whose = log.ifc_borrowed_from ? ` (${log.ifc_borrowed_from} drawings: none of this system is read)` : "";
  const pending = (folder?.files ?? []).filter((f) => f.readable && !f.drawing);
  const detail = folder?.folder
    ? `${folder.folder}${folder.reachable ? "" : " (not reachable on this PC)"}${folder.files.map((f) => `
${f.name} · ${fileSize(f.size)} · ${day(f.modified)}`).join("")}`
    : undefined;
  return (
    <div className="min-w-0 max-w-2xl text-xs text-gray-500" title={detail}>
      <span>IFC: {readNames || "no IFC drawing read yet"}{whose}</span>
      {pending.map((f) => (
        <span key={f.path} className="ml-2 inline-flex items-center gap-1.5">
          <span className="text-gray-700">{f.name}</span>
          {f.job ? (
            <span>{f.job.message ?? f.job.status}{typeof f.job.done === "number" ? ` ${f.job.done}%` : ""}</span>
          ) : canEdit ? (
            <button type="button" onClick={() => read(f)} disabled={busy === f.path} className="rounded border border-gray-300 px-1.5 py-px text-[11px] font-semibold text-navy-900 hover:bg-gray-50 disabled:opacity-50">
              {busy === f.path ? "Queuing…" : "Read"}
            </button>
          ) : null}
        </span>
      ))}
    </div>
  );
}

function Tile({ label, value, icon, active, onClick, tone }: { label: string; value: number; icon?: React.ReactNode; active?: boolean; onClick?: () => void; tone?: "rose" }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-left ${active ? "border-brand-500 bg-brand-50" : "border-gray-200 bg-white hover:bg-gray-50"}`}
    >
      {icon}
      <div className="min-w-0">
        <div className={`text-lg font-bold leading-tight ${tone === "rose" && value > 0 ? "text-rose-700" : "text-navy-900"}`}>{value}</div>
        <div className="truncate text-[11px] text-gray-500">{label}</div>
      </div>
    </button>
  );
}

/** The IFC drawing cell, as BOQ > As per IFC Drawings shows a sheet: its
 *  floor as the sheet writes it, the sheet number, how many floors it
 *  stands for and which. A second row under the same sheet (a shop
 *  drawing covering part of it, or the floors still to submit) says so. */
function IfcCell({ row }: { row: LogRow }) {
  const sheet = row.ifc;
  if (!sheet) {
    // A floor on no IFC drawing in force (the shop drawing's own, or an engineer's).
    return (
      <>
        <div className="font-semibold uppercase text-navy-900" title="On no IFC drawing: from the shop drawing or an engineer">{row.floor}</div>
        {row.floor_secondary && <div className="text-xs text-gray-500">{row.floor_secondary}</div>}
      </>
    );
  }
  // What the reference was read from, and what else was printed, on hover only.
  const about = [`${sheet.drawing} ${sheet.revision}`, sheet.title, sheet.layout !== sheet.sheet ? `layout ${sheet.layout}` : null, sheet.number_note].filter(Boolean).join(" — ");
  return (
    <>
      <div className="font-semibold uppercase text-navy-900">{sheet.label}</div>
      <div className="text-xs text-gray-500" title={about}>{sheet.sheet}</div>
      {sheet.floors > 1 && (
        <div className="mt-1 inline-flex rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700 ring-1 ring-inset ring-brand-600/20">{sheet.floors} floors</div>
      )}
      {sheet.floors > 1 && <div className="mt-0.5 text-xs text-gray-500">{sheet.range}</div>}
    </>
  );
}

function LogTableRow({ row, index, revisions, showDetected, selected, projectId, onOpen, onFolder, folder }: {
  row: LogRow; index: number; revisions: string[]; showDetected: boolean; selected: boolean; projectId: number;
  onOpen: () => void; onFolder: () => void; folder: boolean;
}) {
  const hints = showDetected ? row.hints : row.hints.filter((h) => h.kind !== "revision_candidate");
  return (
    <tr className={`${selected ? "bg-brand-50" : "hover:bg-gray-50"} ${row.id !== null ? "cursor-pointer" : ""}`} onClick={row.id !== null ? onOpen : undefined}>
      <td className="px-3 py-2.5 align-top text-gray-500">{index}</td>
      <td className="min-w-52 px-3 py-2.5 align-top"><IfcCell row={row} /></td>
      <td className="px-3 py-2.5 align-top font-mono text-xs text-gray-700">
        {row.reference ?? <span className="font-sans text-gray-400">Not submitted yet</span>}
        {row.confirmed && <span className="ml-1 text-[10px] text-gray-400" title="Corrected by an engineer">✎</span>}
        {row.title && <div className="mt-0.5 font-sans text-[11px] text-gray-500" title="The drawing's title">{row.title}</div>}
      </td>
      {revisions.map((rev) => {
        const cell = row.cells[rev];
        const beyond = row.latest_revision === null || Number(rev.slice(1)) > Number(row.latest_revision.slice(1));
        return (
          <td key={rev} className="px-2 py-2.5 text-center">
            <Chip cell={cell.candidate && !showDetected ? { ...cell, candidate: undefined } : cell} blank={beyond && !cell.candidate} />
          </td>
        );
      })}
      <td className="px-3 py-2.5 text-center font-medium">{row.latest_revision ?? "–"}</td>
      <td className="px-3 py-2.5"><Chip cell={{ status: row.latest_status, label: STATUS_LABEL[row.latest_status], path: row.latest_path }} blank={row.latest_revision === null} /></td>
      <td className="px-3 py-2.5">
        <div className="flex flex-wrap gap-1">
          {hints.length === 0 ? <span className="text-gray-300">—</span> : hints.slice(0, 3).map((h, i) => <HintBadge key={i} hint={h} />)}
          {hints.length > 3 && <span className="text-xs text-gray-500">+{hints.length - 3}</span>}
        </div>
      </td>
      <td className="px-3 py-2.5" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-center gap-3 text-brand-600">
          {row.latest_path ? (
            <a href={apiUrl(`/projects/${projectId}/logs/file?path=${encodeURIComponent(row.latest_path)}#page=${row.latest_page}`)} target="_blank" rel="noreferrer" title={`View ${row.latest_revision}`} className="hover:text-brand-800"><EyeIcon /></a>
          ) : (
            <span className="text-gray-300" title="Nothing submitted yet"><EyeIcon /></span>
          )}
          <button type="button" onClick={onFolder} disabled={!folder} title={row.latest_path ? "Open the folder of the latest submission" : "Open the shop drawings folder"} className="hover:text-brand-800 disabled:text-gray-300"><FolderIcon /></button>
          {row.id !== null && (
            <button type="button" onClick={onOpen} className="rounded px-1.5 text-lg leading-none text-gray-500 hover:bg-gray-100" aria-label={`Details of ${row.reference}`}>⋯</button>
          )}
        </div>
      </td>
    </tr>
  );
}
