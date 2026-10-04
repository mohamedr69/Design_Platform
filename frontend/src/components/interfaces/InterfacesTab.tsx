import { useCallback, useEffect, useMemo, useState } from 'react'
import { useJob } from '../../lib/useJob'
import { Button, Card, ErrorBox, Spinner, Stat } from '../ifc/ui'
import {
  interfacesApi,
  SCAN_KIND,
  type Coverage,
  type Decision,
  type InterfaceSchedule,
  type ScheduleRow,
  type VerificationItem,
} from './api'

type Tab = 'schedule' | 'verify' | 'summary' | 'drawings' | 'matrix'

/** The BOQ page's "FA Interfaces" tab: the Fire Alarm Interface Schedule.
 *  The other trades' IFC drawings -- fire fighting, smoke management,
 *  ventilation, access control, and the architecture -- are read from the
 *  project folder for the equipment the fire alarm monitors or controls; the
 *  interface matrix gives each its contacts, signals and action, floor by
 *  floor. What the drawings do not settle waits in Verification Required
 *  until an engineer says where and how many. */
export default function InterfacesTab({ projectId, canEdit }: { projectId: number; canEdit: boolean }) {
  const [data, setData] = useState<InterfaceSchedule | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [tab, setTab] = useState<Tab>('schedule')

  const load = useCallback(
    () =>
      interfacesApi
        .get(projectId)
        .then(setData)
        .catch((e) => setError(`The interface schedule could not be loaded: ${(e as Error).message}`)),
    [projectId],
  )
  useEffect(() => {
    void load()
  }, [load])

  const scan = useJob(projectId, SCAN_KIND, interfacesApi.scanPath(projectId), (job) => {
    if (job.status === 'failed') setError(job.error ?? 'The drawings could not be read')
    void load()
  })
  const hydrate = useJob(projectId, SCAN_KIND, interfacesApi.hydratePath(projectId), (job) => {
    if (job.status === 'failed') setError(job.error ?? 'The drawings could not be read')
    void load()
  })

  const act = useCallback(
    async (fn: () => Promise<InterfaceSchedule>) => {
      setBusy(true)
      setError('')
      try {
        setData(await fn())
        return true
      } catch (e) {
        setError((e as Error).message)
        return false
      } finally {
        setBusy(false)
      }
    },
    [],
  )
  const decide = useCallback((body: Decision) => act(() => interfacesApi.decide(projectId, body)), [act, projectId])

  if (!data) return error ? <ErrorBox message={error} /> : <Spinner label="Loading the interface schedule…" />

  const t = data.totals
  const progress = scan.job?.progress as { done?: number; total?: number; message?: string } | undefined
  const tabs: { key: Tab; label: string; count?: number | string }[] = [
    { key: 'schedule', label: 'Interface Schedule', count: data.rows.length },
    { key: 'verify', label: 'Verification Required', count: data.verification.length },
    { key: 'summary', label: 'Summary' },
    { key: 'drawings', label: 'Drawings Received', count: `${data.coverage.filter((c) => c.status === 'available' && c.folder !== null).length}/${data.coverage.filter((c) => c.folder !== null).length}` },
    { key: 'matrix', label: 'Interface Matrix' },
  ]

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 max-w-3xl">
          <h2 className="text-lg font-semibold tracking-tight">Fire alarm interface schedule</h2>
          <p className="mt-1 text-sm text-slate-600">
            The equipment of the other trades the fire alarm monitors or controls, floor by floor: fire fighting (pumps, ZCV, ACV,
            FM200, pre-action), smoke management (extract, pressurization and jet fans, motorized dampers), ventilation (AHU, FAHU,
            fresh air fans), access control, lifts and doors. Read from the IFC drawings in the project folder; the interface matrix
            gives each its contacts and signals. Nothing is scheduled that a drawing does not show.
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {data.scanned_at ? `Drawings last read ${new Date(data.scanned_at + 'Z').toLocaleString()}` : 'The drawings have not been read yet.'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {canEdit && (
            <Button onClick={() => void scan.start()} disabled={scan.active}>
              {scan.active ? 'Reading drawings…' : data.scanned_at ? 'Read drawings again' : 'Read drawings'}
            </Button>
          )}
          <a
            href={interfacesApi.exportUrl(projectId)}
            className="inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            Export schedule to Excel
          </a>
          <a
            href={interfacesApi.exportPdfUrl(projectId)}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Export PDF
          </a>
        </div>
      </div>

      {scan.active && (
        <Card className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="min-w-0">
            <Spinner label={progress?.message ?? 'Queued'} />
            {progress?.total ? (
              <div className="mt-2 h-1.5 w-72 max-w-full overflow-hidden rounded-full bg-slate-100">
                <div className="h-full bg-brand-600 transition-all" style={{ width: `${Math.round(((progress.done ?? 0) / progress.total) * 100)}%` }} />
              </div>
            ) : null}
            <div className="mt-1 text-xs text-slate-500">A DWG is converted first: about 20 seconds a drawing, once. Unchanged drawings are not read again.</div>
            {scan.job?.status === 'queued' && Date.now() - new Date(scan.job.created_at + 'Z').getTime() > 60_000 && (
              <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-900">
                Still waiting for the IFC worker. If its window was opened before this tab was added, close it and run start.bat (or
                start the IFC worker again): the read then starts by itself.
              </div>
            )}
          </div>
          {canEdit && (
            <Button variant="ghost" onClick={() => void scan.cancel()}>
              Stop
            </Button>
          )}
        </Card>
      )}
      {(error || scan.error) && <ErrorBox message={error || scan.error || ''} onClose={() => setError('')} />}

      <EvidenceBanner
        data={data}
        canEdit={canEdit}
        busy={busy || scan.active || hydrate.active}
        onPublish={(reason, override) =>
          act(() =>
            interfacesApi.publishCurrent(projectId, { reason, expected_sources_digest: data.current_sources_digest, override }),
          )
        }
        onHydrate={() => void hydrate.start()}
      />

      <CoverageStrip coverage={data.coverage} onOpen={() => setTab('drawings')} />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Stat label="Interface lines" value={known(data, t.items)} tone="blue" />
        <Stat label="Monitoring signals" value={known(data, t.monitoring)} />
        <Stat label="Control signals" value={known(data, t.control)} />
        <Stat
          label="FA modules (est.)"
          value={
            data.totals_known ? <span title={`CT1 ${t.modules.CT1} · CT2 ${t.modules.CT2} · CR ${t.modules.CR}`}>{t.module_qty}</span> : '—'
          }
        />
        <Stat label="To verify (not counted)" value={known(data, t.to_verify)} tone={t.to_verify ? 'amber' : 'green'} />
      </div>

      {data.last_known.length > 0 && (
        <LastKnownCard
          data={data}
          canEdit={canEdit}
          busy={busy}
          onConfirm={(paths) => act(() => interfacesApi.confirmRemoved(projectId, paths))}
        />
      )}

      {(data.conflicts.length > 0 || data.matrix.unclear_rows.length > 0) && (
        <Card className="border-amber-200 bg-amber-50/60 px-4 py-3 text-sm text-amber-900">
          <div className="font-semibold">For the engineer to check</div>
          <ul className="mt-1 list-disc space-y-0.5 pl-5">
            {data.conflicts.map((c) => (
              <li key={c}>{c}</li>
            ))}
            {data.matrix.unclear_rows.length > 0 && (
              <li>
                Rows {data.matrix.unclear_rows.join(' and ')} of the interface matrix are not legible on the copy transcribed and are not
                applied.
              </li>
            )}
          </ul>
        </Card>
      )}

      <div role="tablist" className="flex flex-wrap gap-1 border-b border-slate-200">
        {tabs.map((x) => (
          <button
            key={x.key}
            role="tab"
            aria-selected={tab === x.key}
            onClick={() => setTab(x.key)}
            className={`-mb-px inline-flex items-center gap-1 border-b-2 px-4 py-2 text-sm font-medium transition ${
              tab === x.key ? 'border-brand-600 text-brand-700' : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {x.label}
            {x.count !== undefined && (
              <span
                className={`ml-1 rounded-full px-2 py-0.5 text-xs ${
                  x.key === 'verify' && data.verification.length
                    ? 'bg-amber-100 text-amber-800'
                    : tab === x.key
                      ? 'bg-brand-100 text-brand-700'
                      : 'bg-slate-100 text-slate-600'
                }`}
              >
                {x.count}
              </span>
            )}
          </button>
        ))}
      </div>

      <fieldset disabled={!canEdit || busy} className={busy ? 'opacity-70' : ''}>
        {tab === 'schedule' && <ScheduleTab data={data} canEdit={canEdit} onDecide={decide} projectId={projectId} act={act} />}
        {tab === 'verify' && <VerifyTab data={data} canEdit={canEdit} onDecide={decide} />}
        {tab === 'summary' && <SummaryTab data={data} />}
        {tab === 'drawings' && <DrawingsTab data={data} />}
        {tab === 'matrix' && <MatrixTab data={data} />}
      </fieldset>
    </div>
  )
}

/* ------------------------------------------------------------------ evidence (FI-P1 r3) */

/** A total the page can vouch for, or "—": never a 0 that only means "not known". */
function known(data: InterfaceSchedule, value: number): number | string {
  return data.totals_known ? value : '—'
}

function when(at: string | null): string {
  return at ? new Date(at + 'Z').toLocaleString() : ''
}

/** What the schedule on the page is built from, said before anything else:
 *  the drawings as verified now, a provisional reading, or the last published
 *  schedule shown because its drawings cannot be verified now. */
function EvidenceBanner({
  data,
  canEdit,
  busy,
  onPublish,
  onHydrate,
}: {
  data: InterfaceSchedule
  canEdit: boolean
  busy: boolean
  onPublish: (reason: string, override: boolean) => Promise<boolean>
  onHydrate: () => void
}) {
  if (data.view_state === 'current') return null
  const reasons = data.view_reasons.join('; ')
  let tone = 'border-amber-200 bg-amber-50 text-amber-900'
  let title = 'Provisional'
  let text = reasons
  if (data.primary === 'published') {
    tone = 'border-rose-200 bg-rose-50 text-rose-900'
    title = `Last published ${when(data.published_at)} — not verified now`
    text = `${reasons}. The schedule below is the last published one${data.published_basis === 'seeded' ? ' (taken over from the readings saved before publishing existed)' : ''}; nothing in it is verified against the drawings now.`
  } else if (data.primary === 'none') {
    tone = 'border-rose-200 bg-rose-50 text-rose-900'
    title = 'Not read completely: no schedule yet'
    text = `${reasons}. No totals are shown until the drawings are read.`
  }
  const notSynced = data.evidence.cloud_only > 0 || data.coverage.some((c) => c.files.some((f) => f.reason === 'not_synced'))
  const canPublish = canEdit && data.evidence.root !== 'unreachable' && data.evidence.root !== 'not_configured' && data.view_state !== 'not_read'
  const publish = () => {
    const reason = window.prompt('Publish the schedule built from the drawings read and verified now. Why?')
    if (!reason?.trim()) return
    void onPublish(reason, false).then((ok) => {
      if (!ok && window.confirm('It was refused (see the message). Publish anyway, on purpose?')) void onPublish(reason, true)
    })
  }
  return (
    <Card className={`flex flex-wrap items-start justify-between gap-3 px-4 py-3 text-sm ${tone}`}>
      <div className="min-w-0 max-w-3xl">
        <div className="font-semibold">{title}</div>
        <div className="mt-0.5">{text}</div>
        {data.current_summary && data.primary !== 'current' && (
          <div className="mt-1 text-xs">
            Verified now: {data.evidence.read_current} drawing(s), {data.current_summary.rows} line(s), {data.current_summary.totals.interface_points}{' '}
            interface point(s).
          </div>
        )}
        {data.published_at && data.primary === 'current' && (
          <div className="mt-1 text-xs">
            Published {when(data.published_at)}
            {data.published_by ? ` by ${data.published_by}` : ''}
            {data.published_reason ? `: ${data.published_reason}` : ''}
          </div>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {canEdit && notSynced && (
          <Button variant="secondary" onClick={onHydrate} disabled={busy}>
            Download and read
          </Button>
        )}
        {canPublish && (data.publish_offered || data.primary !== 'current') && (
          <Button variant="secondary" onClick={publish} disabled={busy}>
            Publish current
          </Button>
        )}
      </div>
    </Card>
  )
}

const REASON_TEXT: Record<string, string> = {
  read_failed: 'could not be read again',
  not_synced: 'not synced (cloud-only)',
  folder_missing: 'its folder is missing or empty',
  ifc_root_missing: 'the drawings folder is not synced',
  listing_failed: 'its folder could not be listed',
  missing: 'missing from its folder',
  changed_since_read: 'changed since it was read',
}

/** Readings kept for audit that count for nothing now (FI-P1 r3 S8.3). */
function LastKnownCard({
  data,
  canEdit,
  busy,
  onConfirm,
}: {
  data: InterfaceSchedule
  canEdit: boolean
  busy: boolean
  onConfirm: (paths: string[]) => Promise<boolean>
}) {
  const removable = data.last_known.filter((k) => k.reason === 'missing' || k.reason === 'folder_missing')
  const notApplied = Object.values(data.decisions_not_applied).reduce((a, b) => a + b, 0)
  return (
    <Card className="border-slate-300 bg-slate-50 px-4 py-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="font-semibold text-slate-700">Last known, not current — not counted</div>
        {canEdit && removable.length > 0 && (
          <Button
            variant="ghost"
            disabled={busy}
            onClick={() => {
              if (window.confirm(`Confirm that ${removable.length} drawing(s) were removed from the folders on purpose?`))
                void onConfirm(removable.map((k) => k.relative_path))
            }}
          >
            Confirm removed ({removable.length})
          </Button>
        )}
      </div>
      <ul className="mt-1 space-y-0.5 text-slate-600">
        {data.last_known.map((k) => (
          <li key={`${k.package}-${k.relative_path}`}>
            <span className="font-medium">{k.filename ?? k.relative_path}</span> ({k.package}) — {REASON_TEXT[k.reason ?? ''] ?? k.reason}
            {k.last_known_at ? `; last read ${when(k.last_known_at)}` : ''}
            {Object.keys(k.counts_by_key).length > 0 && (
              <span className="text-xs text-slate-500">
                {' '}
                · {Object.entries(k.counts_by_key).map(([key, n]) => `${key.replace(/_/g, ' ')} ${n}`).join(', ')}
              </span>
            )}
          </li>
        ))}
      </ul>
      {notApplied > 0 && (
        <div className="mt-1 text-xs text-slate-500">
          {notApplied} engineer decision(s) are kept on these drawings and apply again when they are read and current.
        </div>
      )}
    </Card>
  )
}

/* ------------------------------------------------------------------ coverage */

const COVERAGE_STYLE: Record<Coverage['status'], string> = {
  available: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  missing: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  failed: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  not_provided: 'bg-slate-100 text-slate-600 ring-slate-500/20',
}
const COVERAGE_TEXT: Record<Coverage['status'], string> = {
  available: 'Received',
  missing: 'Missing',
  failed: 'Not read',
  not_provided: 'Not provided',
}

const BADGE_STYLE: Partial<Record<Coverage['badge'], string>> = {
  received: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  received_fa_only: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  received_not_read: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  received_unreadable: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  missing: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  missing_last_known: 'bg-slate-100 text-slate-700 ring-slate-500/20',
  unreachable: 'bg-slate-100 text-slate-700 ring-slate-500/20',
  no_folder: 'bg-slate-100 text-slate-700 ring-slate-500/20',
  not_synced: 'bg-slate-100 text-slate-700 ring-slate-500/20',
}

function CoverageStrip({ coverage, onOpen }: { coverage: Coverage[]; onOpen: () => void }) {
  return (
    <Card className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 text-sm">
      <span className="font-medium text-slate-700">Drawings</span>
      {coverage.map((c) => (
        <span key={c.discipline} className="inline-flex items-center gap-1.5">
          <span className="text-slate-600">{c.name}</span>
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${BADGE_STYLE[c.badge] ?? COVERAGE_STYLE[c.status]}`}>
            {c.badge_text ?? COVERAGE_TEXT[c.status]}
          </span>
        </span>
      ))}
      <button type="button" onClick={onOpen} className="ml-auto text-sm text-brand-700 hover:underline">
        Details
      </button>
    </Card>
  )
}

/* ------------------------------------------------------------------ schedule */

const CONFIDENCE_STYLE: Record<ScheduleRow['confidence'], string> = {
  High: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  Medium: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  'Engineer verified': 'bg-indigo-50 text-indigo-700 ring-indigo-600/20',
}

function ScheduleTab({
  data,
  canEdit,
  onDecide,
  projectId,
  act,
}: {
  data: InterfaceSchedule
  canEdit: boolean
  onDecide: (d: Decision) => Promise<boolean>
  projectId: number
  act: (fn: () => Promise<InterfaceSchedule>) => Promise<boolean>
}) {
  const [floor, setFloor] = useState('')
  const [system, setSystem] = useState('')
  const [adding, setAdding] = useState(false)
  const [showRejected, setShowRejected] = useState(false)
  const floorsWithRows = useMemo(() => data.floor_summary, [data])
  const systems = useMemo(() => [...new Set(data.rows.map((r) => r.system))], [data])
  const rows = data.rows.filter((r) => (!floor || r.floor_key === floor) && (!system || r.system === system))
  const byFloor = useMemo(() => {
    const m = new Map<string, ScheduleRow[]>()
    for (const r of rows) m.set(r.floor_key, [...(m.get(r.floor_key) ?? []), r])
    return [...m.entries()]
  }, [rows])

  const reject = (r: ScheduleRow) => {
    const reason = window.prompt(`Why is ${r.equipment} (${r.floor}) not an interface?`)
    if (reason?.trim()) void onDecide({ id: r.id, action: 'reject', reason })
  }

  return (
    <div className="space-y-3">
      <Card className="flex flex-wrap items-center gap-3 p-3 text-sm">
        <label className="flex items-center gap-2">
          <span className="font-medium text-slate-700">Floor</span>
          <select value={floor} onChange={(e) => setFloor(e.target.value)} className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm">
            <option value="">All floors</option>
            {floorsWithRows.map((f) => (
              <option key={f.floor_key} value={f.floor_key}>
                {f.floor} ({f.items})
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2">
          <span className="font-medium text-slate-700">System</span>
          <select value={system} onChange={(e) => setSystem(e.target.value)} className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm">
            <option value="">All systems</option>
            {systems.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <span className="text-xs text-slate-500">One line per item per floor: a typical plan for eleven floors gives eleven lines.</span>
        {canEdit && (
          <Button variant="secondary" className="ml-auto" onClick={() => setAdding(!adding)}>
            {adding ? 'Close' : '+ Add item'}
          </Button>
        )}
      </Card>

      {adding && (
        <ManualForm
          data={data}
          onCancel={() => setAdding(false)}
          onSave={async (body) => {
            if (await act(() => interfacesApi.addManual(projectId, body))) setAdding(false)
          }}
        />
      )}

      {!data.rows.length ? (
        <Card className="p-6 text-sm text-slate-500">
          {data.scanned_at
            ? 'Nothing is scheduled yet. Settle the items in Verification Required, or add what the drawings do not show.'
            : 'Read the drawings to start: the IFC drawings of each discipline are read from the project folder.'}
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-2.5">#</th>
                  <th className="px-3 py-2.5">Equipment</th>
                  <th className="px-3 py-2.5">Tag / location</th>
                  <th className="px-3 py-2.5">System</th>
                  <th className="px-3 py-2.5">Contact</th>
                  <th className="px-3 py-2.5 text-right">Mon.</th>
                  <th className="px-3 py-2.5 text-right">Ctrl</th>
                  <th className="px-3 py-2.5">Function / action</th>
                  <th className="px-3 py-2.5">Source drawing</th>
                  <th className="px-3 py-2.5">Confidence</th>
                  {canEdit && <th className="px-3 py-2.5" />}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {byFloor.map(([key, list]) => (
                  <FloorBlock key={key} rows={list} canEdit={canEdit} onDecide={onDecide} onReject={reject} projectId={projectId} act={act} />
                ))}
                <tr className="bg-slate-800 font-semibold text-white">
                  <td className="px-3 py-2" colSpan={5}>
                    {floor || system ? 'Shown' : 'Building total'}: {rows.length} lines
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">{rows.reduce((s, r) => s + r.monitoring, 0)}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{rows.reduce((s, r) => s + r.control, 0)}</td>
                  <td className="px-3 py-2" colSpan={canEdit ? 4 : 3}>
                    {rows.reduce((s, r) => s + r.module_qty, 0)} FA modules (est.)
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {data.rejected.length > 0 && (
        <Card className="px-4 py-3 text-sm">
          <button type="button" onClick={() => setShowRejected(!showRejected)} className="font-medium text-slate-700 hover:underline">
            {data.rejected.length} line{data.rejected.length > 1 ? 's' : ''} marked not an interface {showRejected ? '▾' : '▸'}
          </button>
          {showRejected && (
            <ul className="mt-2 space-y-1">
              {data.rejected.map((r) => (
                <li key={r.id} className="flex flex-wrap items-center gap-2 text-slate-600">
                  <span>
                    {r.floor} · {r.equipment} {r.tag !== 'Tag Not Identified' && r.tag} — {r.reason}
                  </span>
                  {canEdit && (
                    <Button variant="ghost" onClick={() => void onDecide({ id: r.id, action: 'restore' })}>
                      Restore
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}
    </div>
  )
}

function FloorBlock({
  rows,
  canEdit,
  onDecide,
  onReject,
  projectId,
  act,
}: {
  rows: ScheduleRow[]
  canEdit: boolean
  onDecide: (d: Decision) => Promise<boolean>
  onReject: (r: ScheduleRow) => void
  projectId: number
  act: (fn: () => Promise<InterfaceSchedule>) => Promise<boolean>
}) {
  const m = rows.reduce((s, r) => s + r.monitoring, 0)
  const c = rows.reduce((s, r) => s + r.control, 0)
  return (
    <>
      <tr className="bg-brand-50/60">
        <td className="px-3 py-1.5 text-sm font-semibold text-brand-800" colSpan={5}>
          {rows[0].floor}
        </td>
        <td className="px-3 py-1.5 text-right text-xs font-semibold tabular-nums text-brand-800">{m}</td>
        <td className="px-3 py-1.5 text-right text-xs font-semibold tabular-nums text-brand-800">{c}</td>
        <td className="px-3 py-1.5 text-xs text-brand-800" colSpan={canEdit ? 4 : 3}>
          {rows.length} line{rows.length > 1 ? 's' : ''}
        </td>
      </tr>
      {rows.map((r) => (
        <tr key={r.id} className="align-top hover:bg-slate-50">
          <td className="px-3 py-2 text-slate-500">{r.no}</td>
          <td className="px-3 py-2">
            <div className="font-medium text-slate-800">{r.equipment}</div>
            <div className="max-w-xs text-xs text-slate-500">{r.description}</div>
          </td>
          <td className="px-3 py-2">
            <div className={r.tag === 'Tag Not Identified' ? 'text-xs italic text-slate-400' : 'font-mono text-xs'}>{r.tag}</div>
            {r.location && <div className="text-xs text-slate-600">{r.location}</div>}
          </td>
          <td className="whitespace-nowrap px-3 py-2 text-slate-600">{r.system}</td>
          <td className="whitespace-nowrap px-3 py-2 font-mono text-xs">{r.contacts}</td>
          <td className="px-3 py-2 text-right tabular-nums">{r.monitoring}</td>
          <td className="px-3 py-2 text-right tabular-nums">{r.control}</td>
          <td className="max-w-sm px-3 py-2 text-xs text-slate-600">
            {r.alarm && <div>Alarm: {r.alarm}</div>}
            {r.supervisory && <div>Supervisory: {r.supervisory}</div>}
            {r.action && <div>Action: {r.action}</div>}
          </td>
          <td className="max-w-xs px-3 py-2 text-xs text-slate-600">
            <div className="font-medium text-slate-700">{r.source}</div>
            <div>{r.drawing_ref}</div>
            <div className="text-slate-400">{r.evidence}</div>
          </td>
          <td className="px-3 py-2">
            <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${CONFIDENCE_STYLE[r.confidence]}`}>
              {r.confidence}
            </span>
          </td>
          {canEdit && (
            <td className="whitespace-nowrap px-3 py-2 text-right">
              {r.basis === 'drawing' && (
                <>
                  {r.confidence !== 'Engineer verified' && (
                    <Button variant="ghost" onClick={() => void onDecide({ id: r.id, action: 'confirm' })} title="Checked against the drawing">
                      Confirm
                    </Button>
                  )}
                  <Button variant="ghost" onClick={() => onReject(r)} title="Not an interface: taken out of the schedule, with the reason">
                    Not an interface
                  </Button>
                </>
              )}
              {r.basis === 'manual' && r.manual_id && (
                <Button variant="ghost" onClick={() => void act(() => interfacesApi.removeManual(projectId, r.manual_id!))}>
                  Remove
                </Button>
              )}
            </td>
          )}
        </tr>
      ))}
    </>
  )
}

/** An item the drawings do not give: always with the drawing it is on. */
function ManualForm({
  data,
  onSave,
  onCancel,
}: {
  data: InterfaceSchedule
  onSave: (body: { key: string; floor_keys: string[]; qty: number; tags: string[]; location: string; source: string; drawing_ref: string; remarks: string }) => void
  onCancel: () => void
}) {
  const rules = data.matrix.rules.filter((r) => !r.excluded)
  const [key, setKey] = useState(rules[0]?.key ?? '')
  const [floors, setFloors] = useState<string[]>([])
  const [qty, setQty] = useState(1)
  const [tags, setTags] = useState('')
  const [location, setLocation] = useState('')
  const [source, setSource] = useState('')
  const [ref, setRef] = useState('')
  const [remarks, setRemarks] = useState('')
  const ok = key && floors.length > 0 && qty > 0 && source.trim()
  return (
    <Card className="space-y-3 p-4 text-sm">
      <div className="font-semibold">Add an item the drawings do not give</div>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="block">
          <span className="text-slate-700">Equipment</span>
          <select value={key} onChange={(e) => setKey(e.target.value)} className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5">
            {rules.map((r) => (
              <option key={r.key} value={r.key}>
                {r.no}. {r.name} ({r.contacts})
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-slate-700">Quantity on each floor</span>
          <input type="number" min={1} max={500} value={qty} onChange={(e) => setQty(Number(e.target.value))} className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5" />
        </label>
        <label className="block">
          <span className="text-slate-700">Tags (comma separated, optional)</span>
          <input value={tags} onChange={(e) => setTags(e.target.value)} className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5" />
        </label>
      </div>
      <FloorPicker floors={data.floors} value={floors} onChange={setFloors} />
      <div className="grid gap-3 md:grid-cols-2">
        <label className="block">
          <span className="text-slate-700">Source drawing (required)</span>
          <input value={source} onChange={(e) => setSource(e.target.value)} placeholder="e.g. SM-B4-01 SMOKE MANAGEMENT LAYOUT.dwg" className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5" />
        </label>
        <label className="block">
          <span className="text-slate-700">Drawing reference / sheet</span>
          <input value={ref} onChange={(e) => setRef(e.target.value)} className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5" />
        </label>
        <label className="block">
          <span className="text-slate-700">Location</span>
          <input value={location} onChange={(e) => setLocation(e.target.value)} className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5" />
        </label>
        <label className="block">
          <span className="text-slate-700">Remarks</span>
          <input value={remarks} onChange={(e) => setRemarks(e.target.value)} className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5" />
        </label>
      </div>
      <div className="flex gap-2">
        <Button
          disabled={!ok}
          onClick={() =>
            onSave({ key, floor_keys: floors, qty, tags: tags.split(',').map((s) => s.trim()).filter(Boolean), location, source, drawing_ref: ref, remarks })
          }
        >
          Add to the schedule
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </Card>
  )
}

function FloorPicker({ floors, value, onChange }: { floors: InterfaceSchedule['floors']; value: string[]; onChange: (v: string[]) => void }) {
  const name = new Map(floors.map((f) => [f.key, f.name]))
  return (
    <div>
      <div className="text-slate-700">Floors</div>
      <div className="mt-1 flex flex-wrap items-center gap-1.5">
        {value.map((k) => (
          <span key={k} className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-800 ring-1 ring-inset ring-brand-600/20">
            {name.get(k) ?? k}
            <button type="button" aria-label={`Remove ${name.get(k) ?? k}`} onClick={() => onChange(value.filter((v) => v !== k))} className="text-brand-600 hover:text-brand-900">
              ✕
            </button>
          </span>
        ))}
        <select
          value=""
          onChange={(e) => e.target.value && onChange([...value, e.target.value])}
          className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs"
        >
          <option value="">{value.length ? 'Add a floor…' : 'Choose a floor…'}</option>
          {floors
            .filter((f) => !value.includes(f.key))
            .map((f) => (
              <option key={f.key} value={f.key}>
                {f.name}
              </option>
            ))}
        </select>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ verification */

function VerifyTab({ data, canEdit, onDecide }: { data: InterfaceSchedule; canEdit: boolean; onDecide: (d: Decision) => Promise<boolean> }) {
  return (
    <div className="space-y-3">
      {!data.verification.length ? (
        <Card className="p-6 text-sm text-slate-500">Nothing left to verify.</Card>
      ) : (
        <>
          <p className="text-sm text-slate-600">
            What the drawings do not settle: an item shown only on a riser or schematic, outside every sheet, a system shown only by a note,
            a door the drawing does not say is automatic, the lifts. None of it is counted until you say where and how many.
          </p>
          {data.verification.map((g) => (
            <VerifyCard key={g.id} g={g} data={data} canEdit={canEdit} onDecide={onDecide} />
          ))}
        </>
      )}
      {data.settled.length > 0 && (
        <Card className="px-4 py-3 text-sm">
          <div className="font-medium text-slate-700">Settled</div>
          <ul className="mt-2 space-y-1">
            {data.settled.map((g) => (
              <li key={g.id} className="flex flex-wrap items-center gap-2 text-slate-600">
                <span className={g.status === 'resolved' ? 'text-emerald-700' : 'text-slate-500'}>{g.status === 'resolved' ? 'Scheduled' : 'Not scheduled'}</span>
                <span>
                  {g.equipment} ({g.source})
                  {g.status === 'resolved'
                    ? `: ${g.decision?.qty} on each of ${(g.decision?.floor_keys ?? []).map((k) => data.floors.find((f) => f.key === k)?.name ?? k).join(', ')}`
                    : ` — ${g.decision?.reason ?? ''}`}
                </span>
                {canEdit && (
                  <Button variant="ghost" onClick={() => void onDecide({ id: g.id, action: 'reopen' })}>
                    Reopen
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}

function VerifyCard({ g, data, canEdit, onDecide }: { g: VerificationItem; data: InterfaceSchedule; canEdit: boolean; onDecide: (d: Decision) => Promise<boolean> }) {
  const [floors, setFloors] = useState<string[]>(g.proposed_floor_keys)
  const [qty, setQty] = useState<number | ''>(g.proposed_qty ?? '')
  const [tags, setTags] = useState(g.tags.join(', '))
  const [location, setLocation] = useState(g.location)
  const lines = floors.length * (qty || 0)
  return (
    <Card className="space-y-3 p-4 text-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="font-semibold text-slate-800">
            {g.equipment} <span className="font-normal text-slate-500">· {g.system}</span>
          </div>
          <div className="mt-0.5 text-amber-800">{g.reason}</div>
        </div>
        <div className="text-right text-xs text-slate-500">
          <span className="font-mono">{g.contacts}</span> · {g.monitoring} monitoring / {g.control} control each
        </div>
      </div>
      <div className="grid gap-1 text-xs text-slate-600 md:grid-cols-2">
        <div>
          <span className="text-slate-400">Source: </span>
          {g.source}
          <div>{g.ref}</div>
        </div>
        <div>
          <span className="text-slate-400">Evidence: </span>
          {g.evidence}
        </div>
      </div>
      {canEdit && (
        <div className="space-y-3 border-t border-slate-100 pt-3">
          <FloorPicker floors={data.floors} value={floors} onChange={setFloors} />
          <div className="grid gap-3 md:grid-cols-3">
            <label className="block">
              <span className="text-slate-700">How many on each floor</span>
              <input
                type="number"
                min={1}
                max={500}
                value={qty}
                onChange={(e) => setQty(e.target.value ? Number(e.target.value) : '')}
                className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5"
              />
            </label>
            <label className="block">
              <span className="text-slate-700">Tags (comma separated)</span>
              <input value={tags} onChange={(e) => setTags(e.target.value)} className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5" />
            </label>
            <label className="block">
              <span className="text-slate-700">Location</span>
              <input value={location} onChange={(e) => setLocation(e.target.value)} className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5" />
            </label>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="success"
              disabled={!floors.length || !qty}
              onClick={() =>
                void onDecide({
                  id: g.id,
                  action: 'resolve',
                  floor_keys: floors,
                  qty: Number(qty),
                  tags: tags.split(',').map((s) => s.trim()).filter(Boolean),
                  location,
                })
              }
            >
              Schedule {lines ? `${lines} line${lines > 1 ? 's' : ''}` : 'it'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                const reason = window.prompt(`Why is ${g.equipment} not scheduled?`)
                if (reason?.trim()) void onDecide({ id: g.id, action: 'dismiss', reason })
              }}
            >
              Not an interface
            </Button>
          </div>
        </div>
      )}
    </Card>
  )
}

/* ------------------------------------------------------------------ summary, drawings, matrix */

function SummaryTab({ data }: { data: InterfaceSchedule }) {
  const t = data.totals
  const th = 'px-3 py-2 text-right'
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Card className="overflow-hidden">
        <div className="border-b border-slate-200 px-4 py-2.5 text-sm font-semibold">Floor summary</div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2 text-left">Floor</th>
                <th className={th}>Lines</th>
                <th className={th}>Monitoring</th>
                <th className={th}>Control</th>
                <th className={th}>Total</th>
                <th className={th}>Modules</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 tabular-nums">
              {data.floor_summary.map((f) => (
                <tr key={f.floor_key}>
                  <td className="px-3 py-1.5">{f.floor}</td>
                  <td className={th}>{f.items}</td>
                  <td className={th}>{f.monitoring}</td>
                  <td className={th}>{f.control}</td>
                  <td className={`${th} font-semibold`}>{f.total}</td>
                  <td className={th}>{f.module_qty}</td>
                </tr>
              ))}
              <tr className="bg-slate-50 font-semibold">
                <td className="px-3 py-2">Total</td>
                <td className={th}>{t.items}</td>
                <td className={th}>{t.monitoring}</td>
                <td className={th}>{t.control}</td>
                <td className={th}>{t.interface_points}</td>
                <td className={th}>{t.module_qty}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
      <div className="space-y-4">
        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 px-4 py-2.5 text-sm font-semibold">Equipment summary</div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-2 text-left">Equipment</th>
                  <th className="px-3 py-2 text-left">Contact</th>
                  <th className={th}>Qty</th>
                  <th className={th}>Mon.</th>
                  <th className={th}>Ctrl</th>
                  <th className={th}>CT1</th>
                  <th className={th}>CT2</th>
                  <th className={th}>CR</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 tabular-nums">
                {data.type_summary.map((s) => (
                  <tr key={s.key}>
                    <td className="px-3 py-1.5">{s.equipment}</td>
                    <td className="px-3 py-1.5 font-mono text-xs">{s.contacts}</td>
                    <td className={`${th} font-semibold`}>{s.qty}</td>
                    <td className={th}>{s.monitoring}</td>
                    <td className={th}>{s.control}</td>
                    <td className={th}>{s.modules.CT1}</td>
                    <td className={th}>{s.modules.CT2}</td>
                    <td className={th}>{s.modules.CR}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card className="px-4 py-3 text-sm">
          <div className="font-semibold">Overall</div>
          <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1">
            {[
              ['Monitoring signals', t.monitoring],
              ['Control signals', t.control],
              ['Interface points', t.interface_points],
              ['Monitoring modules (CT1 + CT2)', t.monitoring_modules],
              ['Control modules (CR)', t.control_modules],
              ['FA modules, estimated', t.module_qty],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between border-b border-slate-100 py-1">
                <dt className="text-slate-600">{k}</dt>
                <dd className="font-semibold tabular-nums">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-2 text-xs text-slate-500">
            Modules from the matrix's Required Contact: CT2 is one dual-input module, CT1 a single input, CR a relay; a lift takes two
            relays. Confirm against the panel's module configuration. Items still to verify are not counted.
          </p>
        </Card>
      </div>
    </div>
  )
}

function DrawingsTab({ data }: { data: InterfaceSchedule }) {
  return (
    <div className="space-y-3">
      {data.coverage.map((c) => (
        <Card key={c.discipline} className="overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-4 py-2.5">
            <div>
              <span className="font-semibold">{c.name}</span>
              <span className={`ml-2 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${BADGE_STYLE[c.badge] ?? COVERAGE_STYLE[c.status]}`}>
                {c.badge_text ?? COVERAGE_TEXT[c.status]}
              </span>
              <div className="text-xs text-slate-500">{c.purpose}</div>
            </div>
            {c.folder && <div className="font-mono text-xs text-slate-500">{c.folder}</div>}
          </div>
          {c.files.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-2">Drawing</th>
                    <th className="px-4 py-2">Status</th>
                    <th className="px-4 py-2">Modified</th>
                    <th className="px-4 py-2 text-right">Sheets</th>
                    <th className="px-4 py-2 text-right">Floor plans</th>
                    <th className="px-4 py-2 text-right">Items found</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {c.files.map((f) => (
                    <tr key={`${f.relative_path}-${f.filename}`}>
                      <td className="px-4 py-2">
                        <div className="font-medium">
                          {f.filename} {f.revision && <span className="text-xs text-slate-500">{f.revision}</span>}
                        </div>
                        <div className="text-xs text-slate-500">
                          {f.kind === 'fa_ifc' ? 'Fire alarm IFC drawing in force: its architectural background' : f.relative_path}
                        </div>
                        {f.error && <div className="text-xs text-rose-700">{f.error}</div>}
                      </td>
                      <td className="px-4 py-2 text-xs">
                        {f.status === 'read'
                          ? f.cloud_only
                            ? 'Read (cloud-only, unchanged)'
                            : 'Read'
                          : f.status === 'superseded'
                            ? 'Superseded: a later revision is read'
                            : f.status === 'unread'
                              ? f.reason === 'not_synced'
                                ? 'Not synced: download and read'
                                : 'Not read yet: read the drawings'
                              : f.status === 'stale'
                                ? `Last known only, not counted (${REASON_TEXT[f.reason ?? ''] ?? f.reason ?? 'not current'})`
                                : f.status === 'unsupported'
                                  ? 'Not readable (PDF or other): not counted'
                                  : 'Could not be read'}
                      </td>
                      <td className="whitespace-nowrap px-4 py-2 text-xs">{f.modified ? new Date(f.modified).toLocaleString() : '-'}</td>
                      <td className="px-4 py-2 text-right tabular-nums">{f.sheets}</td>
                      <td className="px-4 py-2 text-right tabular-nums">{f.plans}</td>
                      <td className="px-4 py-2 text-right tabular-nums">
                        {f.items}
                        {f.lifts > 0 && <span className="text-xs text-slate-500"> + {f.lifts} lifts</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            c.folder && (
              <div className="px-4 py-3 text-sm text-slate-500">
                No drawing in {c.folder}. File the contractor's IFC drawings (DWG or DXF) there, then read the drawings again.
              </div>
            )
          )}
        </Card>
      ))}
      {data.excluded_found.length > 0 && (
        <Card className="px-4 py-3 text-sm text-slate-600">
          <div className="font-medium text-slate-700">Seen, and excluded from the schedule</div>
          <ul className="mt-1 list-disc pl-5">
            {data.excluded_found.map((e, i) => (
              <li key={i}>
                {e.equipment}: {e.count} on {e.sheet} of {e.source} ("{e.text}")
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}

function MatrixTab({ data }: { data: InterfaceSchedule }) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 px-4 py-2.5 text-sm">
        <span className="font-semibold">{data.matrix.name}</span>
        <span className="text-slate-500"> · what the fire alarm does with each kind of equipment; applied to every line of the schedule</span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-3 py-2">#</th>
              <th className="px-3 py-2">Equipment</th>
              <th className="px-3 py-2">Contacts</th>
              <th className="px-3 py-2 text-right">Mon.</th>
              <th className="px-3 py-2 text-right">Ctrl</th>
              <th className="px-3 py-2">Alarm</th>
              <th className="px-3 py-2">Supervisory</th>
              <th className="px-3 py-2">Third-party action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 align-top">
            {data.matrix.rules.map((r) => (
              <tr key={r.key} className={r.excluded ? 'text-slate-400' : ''}>
                <td className="px-3 py-2">{r.no}</td>
                <td className="px-3 py-2 font-medium">
                  {r.name}
                  {r.excluded && <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-normal">excluded</span>}
                </td>
                <td className="whitespace-nowrap px-3 py-2 font-mono text-xs">{r.contacts}</td>
                <td className="px-3 py-2 text-right">{r.monitoring || '-'}</td>
                <td className="px-3 py-2 text-right">{r.control || '-'}</td>
                <td className="max-w-xs px-3 py-2 text-xs">{r.alarm || '-'}</td>
                <td className="max-w-xs px-3 py-2 text-xs">{r.supervisory || '-'}</td>
                <td className="max-w-xs px-3 py-2 text-xs">{r.action || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
