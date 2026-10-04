/** The FA Interfaces tab's calls (app/routers/fa_interfaces.py). */
import { api as platform, apiUrl } from '../../lib/api'

export type Modules = { CT1: number; CT2: number; CR: number }

export interface ScheduleRow {
  id: string
  no?: number
  floor_key: string
  floor: string
  location: string
  tag: string
  key: string
  equipment: string
  description: string
  discipline: string
  system: string
  contacts: string
  monitoring: number
  control: number
  alarm: string
  supervisory: string
  action: string
  modules: Modules
  module_qty: number
  source: string
  drawing_ref: string
  confidence: 'High' | 'Medium' | 'Engineer verified'
  /** drawing: read off a plan; engineer: a verification item settled; manual: added */
  basis: 'drawing' | 'engineer' | 'manual'
  evidence: string
  typical: boolean
  status: 'scheduled' | 'rejected'
  reason?: string
  manual_id?: string
}

export interface VerificationItem {
  id: string
  key: string
  equipment: string
  discipline: string
  system: string
  source: string
  ref: string
  reason: string
  proposed_floor_keys: string[]
  proposed_floors: string[]
  proposed_qty: number | null
  tags: string[]
  location: string
  labels: number
  evidence: string
  contacts: string
  monitoring: number
  control: number
  status: 'open' | 'resolved' | 'dismissed' | 'governed'
  decision?: { reason?: string; floor_keys?: string[]; qty?: number; tags?: string[]; location?: string; relative_path?: string; authority?: string }
  /** drawings that disagree (gate barriers): held until the engineer says which governs, on whose authority */
  conflict?: boolean
  drawings?: ConflictDrawing[]
  /** a governing choice whose drawing is no longer among them: not applied */
  decision_not_applied?: boolean
  /** the answers this one replaced, oldest first: never deleted */
  history?: { status: string; reason?: string; relative_path?: string; authority?: string; by?: number; at?: string }[]
}

export interface ConflictDrawing {
  relative_path: string
  label: string
  revision?: string | null
  points: number
  settled: number
  /** each fire alarm connection point with its lane role (ENTRY / EXIT) */
  connection_points?: { x: number; y: number; sheet: string; role: string | null; settled: boolean; why: string | null }[]
}

export interface Limitation {
  package: string
  kind: 'unsupported_files' | 'no_block_symbol'
  count: number
  files: string[]
  text: string
}

export interface CoverageFile {
  filename: string
  relative_path: string | null
  kind: 'folder' | 'fa_ifc' | 'schedule' | 'unsupported'
  revision: string | null
  /** read = verified now; stale = last known only, never counted (FI-P1 r3) */
  status: 'read' | 'failed' | 'superseded' | 'unread' | 'stale' | 'unsupported' | 'removed'
  reason: string | null
  present: boolean
  cloud_only: boolean
  last_known_at: string | null
  error: string | null
  modified: string | null
  size: number | null
  sheets: number
  plans: number
  items: number
  lifts: number
}

export type CoverageBadge =
  | 'unreachable'
  | 'no_folder'
  | 'not_synced'
  | 'missing_last_known'
  | 'missing'
  | 'received_not_read'
  | 'received_unreadable'
  | 'received'
  | 'received_fa_only'

export interface Coverage {
  discipline: string
  name: string
  folder: string | null
  purpose: string
  /** "available" only when the package's files are in the folder now */
  status: 'available' | 'missing' | 'failed' | 'not_provided'
  /** a drawing of it is read and verified now */
  read: boolean
  received: boolean
  badge: CoverageBadge
  badge_text: string
  pending: number
  files: CoverageFile[]
}

export interface FloorSummary {
  floor_key: string
  floor: string
  items: number
  monitoring: number
  control: number
  total: number
  modules: Modules
  module_qty: number
}

export interface TypeSummary {
  key: string
  equipment: string
  contacts: string
  qty: number
  monitoring: number
  control: number
  modules: Modules
  module_qty: number
}

export interface MatrixRule {
  no: number
  key: string
  name: string
  contacts: string
  monitoring: number
  control: number
  alarm: string
  supervisory: string
  action: string
  disciplines: string[]
  excluded: boolean
  modules: Modules
}

export interface ManualItem {
  id: string
  key: string
  floor_keys: string[]
  qty: number
  tags: string[]
  location: string
  source: string
  drawing_ref: string
  remarks: string
}

export interface InterfaceSchedule {
  project: { id: number; ep_number: string; name: string | null }
  scanned_at: string | null
  coverage: Coverage[]
  floors: { key: string; name: string; order: number | null; ifc_sheet: string | null; registered: boolean }[]
  rows: ScheduleRow[]
  rejected: ScheduleRow[]
  verification: VerificationItem[]
  settled: VerificationItem[]
  manual: ManualItem[]
  floor_summary: FloorSummary[]
  type_summary: TypeSummary[]
  totals: {
    items: number
    monitoring: number
    control: number
    interface_points: number
    modules: Modules
    monitoring_modules: number
    control_modules: number
    module_qty: number
    to_verify: number
  }
  conflicts: string[]
  excluded_found: { equipment: string; source: string; sheet: string; count: number; text: string }[]
  matrix: { name: string; rules: MatrixRule[]; unclear_rows: number[] }
  /** FI-P1 r3 S8: what this schedule is built from */
  view_state: 'current' | 'provisional' | 'unverified' | 'not_read'
  primary: 'current' | 'published' | 'none'
  view_reasons: string[]
  publish_offered: boolean
  totals_known: boolean
  published_at: string | null
  published_basis: 'complete_scan' | 'engineer_accepted' | 'seeded' | 'run_accepted' | null
  published_by: string | null
  published_reason: string | null
  current_sources_digest: string
  current_summary: { totals: InterfaceSchedule['totals']; rows: number } | null
  last_known: LastKnown[]
  decisions_not_applied: Record<string, number>
  /** what the evidence cannot show: never taken as "no equipment" */
  limitations: Limitation[]
  evidence: {
    root: 'ok' | 'unreachable' | 'not_configured' | 'ifc_root_missing'
    read_current: number
    stale: number
    failed: number
    unread: number
    removed: number
    superseded: number
    unsupported: number
    cloud_only: number
    changed_since_read: number
    listing_failed: string[]
  }
}

export interface LastKnown {
  package: string
  relative_path: string
  filename: string | null
  reason: string | null
  last_known_at: string | null
  counts_by_key: Record<string, number>
}

export type DecisionAction = 'reject' | 'restore' | 'confirm' | 'resolve' | 'dismiss' | 'reopen' | 'govern'

export interface Decision {
  id: string
  action: DecisionAction
  reason?: string
  floor_keys?: string[]
  qty?: number
  tags?: string[]
  location?: string
  /** govern: the drawing that counts for a conflict, and whose confirmation the choice rests on
   *  (resolve / dismiss of a conflict need the authority too) */
  relative_path?: string
  authority?: string
}

/* ---- the drawing workflow (FI-P1): drawing agents, package reports, the Fable review */

export type CoverageState = 'complete' | 'partial' | 'unsupported' | 'not_attempted'
export type ReviewState = 'completed' | 'partial' | 'missing' | 'pending'
export type PublicationState = 'provisional' | 'complete_candidate' | 'accepted'

export interface AgentReport {
  agent_id: string
  source_id: string
  relative_path: string | null
  filename: string | null
  package: string
  status: string
  stale_reason: string | null
  execution_state: 'completed' | 'failed'
  coverage_state: CoverageState
  coverage_reason: string | null
  layouts: { sheets: number; plans: number }
  labels: number
  associations: Record<string, number>
  gate_points: { total: number; settled: number }
  look: {
    model_requested: string
    effort: string
    windows: number | null
    labels_expected: number | null
    labels_looked: number
    unread: Record<string, number>
    status: string | null
    /** asked in this run; the rest answered by an earlier run on the same file */
    looked_this_run?: number
  } | null
  /** damper labels on sheets that are not floor plans: not looked at, never counted */
  not_looked?: { sheet: string; title: string; labels: number; reason: string }[]
  duration_s: number
  error: string | null
}

export interface PackageReport {
  package: string
  name: string
  badge: CoverageBadge
  received: boolean
  sources: { source_id: string; filename: string | null; status: string; execution_state: string; coverage_state: CoverageState; coverage_reason: string | null }[]
  accepted_lines: number
  accepted_points: number
  held_items: { id: string; equipment: string; labels: number | null; reason: string; conflict: boolean }[]
  stale: { filename: string | null; reason: string | null }[]
  unsupported_files: string[]
  limitations?: Limitation[]
  /** "completed", or "missing (<state>: <reason>)" */
  orchestrator_review: string
}

export interface ReviewPart {
  state: string | null
  reason: string | null
  proposal: {
    summary?: string
    publication_recommendation?: string
    open_questions?: string[]
    conflict_proposals?: { conflict_id: string; reason: string }[]
    missing_or_suspect?: { detail: string }[]
  } | null
  notes: string[] | null
}

export interface InterfaceRun {
  run_id: number
  status: 'running' | 'completed' | 'failed' | 'stopped'
  agents: number
  coverage: Partial<Record<CoverageState, number>>
  packages: number
  review_state: ReviewState
  review_reasons: string[]
  publication_state: PublicationState
  /** why the run is not a complete candidate, decided by deterministic code */
  publication_reasons: string[]
  orchestrator_calls: number
  started_at: string | null
  finished_at: string | null
  error: string | null
  agent_reports: AgentReport[]
  package_reports: PackageReport[]
  review: {
    state: ReviewState
    reasons: string[]
    model_requested: string | null
    effort: string | null
    fp1: Record<string, ReviewPart>
    fp2: ReviewPart
    retries: string[]
    retries_today?: number
    retries_per_day?: number
  }
  accepted_at: string | null
  sources_digest: string | null
}

export const RUN_KIND = 'fa_interfaces_run'
export const REVIEW_KIND = 'fa_interfaces_review'

const base = (projectId: number) => `/projects/${projectId}/fa-interfaces`

export const SCAN_KIND = 'fa_interfaces_scan'

export const interfacesApi = {
  get: (projectId: number) => platform.get<InterfaceSchedule>(base(projectId)),
  scanPath: (projectId: number) => `${base(projectId)}/scan/jobs`,
  decide: (projectId: number, body: Decision) => platform.post<InterfaceSchedule>(`${base(projectId)}/decisions`, body),
  addManual: (projectId: number, body: Omit<ManualItem, 'id'> & { discipline?: string | null }) =>
    platform.post<InterfaceSchedule>(`${base(projectId)}/manual`, body),
  removeManual: (projectId: number, id: string) => platform.delete<InterfaceSchedule>(`${base(projectId)}/manual/${id}`),
  /** "Download and read": OneDrive cloud-only files brought down and read */
  hydratePath: (projectId: number) => `${base(projectId)}/scan/jobs?hydrate=true`,
  publishCurrent: (projectId: number, body: { reason: string; expected_sources_digest: string; override?: boolean }) =>
    platform.post<InterfaceSchedule>(`${base(projectId)}/publish-current`, body),
  confirmRemoved: (projectId: number, relativePaths: string[]) =>
    platform.post<InterfaceSchedule>(`${base(projectId)}/sources/confirm-removed`, { relative_paths: relativePaths }),
  runPath: (projectId: number) => `${base(projectId)}/runs/jobs`,
  latestRun: (projectId: number) => platform.get<{ run: InterfaceRun | null }>(`${base(projectId)}/runs/latest`),
  acceptRun: (projectId: number, runId: number) =>
    platform.post<{ run: InterfaceRun; schedule: InterfaceSchedule }>(`${base(projectId)}/runs/${runId}/accept`),
  /** Retry review: a job (202), counted against the day's bound when asked for */
  retryPath: (projectId: number, runId: number) => `${base(projectId)}/runs/${runId}/retry-review`,
  exportUrl: (projectId: number) => apiUrl(`${base(projectId)}/export.xlsx`),
  exportPdfUrl: (projectId: number) => apiUrl(`${base(projectId)}/export.pdf`),
}
