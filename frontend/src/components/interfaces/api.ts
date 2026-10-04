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
  status: 'open' | 'resolved' | 'dismissed'
  decision?: { reason?: string; floor_keys?: string[]; qty?: number; tags?: string[]; location?: string }
}

export interface CoverageFile {
  filename: string
  relative_path: string | null
  kind: 'folder' | 'fa_ifc' | 'schedule'
  revision: string | null
  status: 'read' | 'failed' | 'superseded' | 'unread'
  error: string | null
  modified: string | null
  size: number | null
  sheets: number
  plans: number
  items: number
  lifts: number
}

export interface Coverage {
  discipline: string
  name: string
  folder: string | null
  purpose: string
  status: 'available' | 'missing' | 'failed' | 'not_provided'
  /** a drawing of it was read into the schedule */
  read: boolean
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
}

export type DecisionAction = 'reject' | 'restore' | 'confirm' | 'resolve' | 'dismiss' | 'reopen'

export interface Decision {
  id: string
  action: DecisionAction
  reason?: string
  floor_keys?: string[]
  qty?: number
  tags?: string[]
  location?: string
}

const base = (projectId: number) => `/projects/${projectId}/fa-interfaces`

export const SCAN_KIND = 'fa_interfaces_scan'

export const interfacesApi = {
  get: (projectId: number) => platform.get<InterfaceSchedule>(base(projectId)),
  scanPath: (projectId: number) => `${base(projectId)}/scan/jobs`,
  decide: (projectId: number, body: Decision) => platform.post<InterfaceSchedule>(`${base(projectId)}/decisions`, body),
  addManual: (projectId: number, body: Omit<ManualItem, 'id'> & { discipline?: string | null }) =>
    platform.post<InterfaceSchedule>(`${base(projectId)}/manual`, body),
  removeManual: (projectId: number, id: string) => platform.delete<InterfaceSchedule>(`${base(projectId)}/manual/${id}`),
  exportUrl: (projectId: number) => apiUrl(`${base(projectId)}/export.xlsx`),
  exportPdfUrl: (projectId: number) => apiUrl(`${base(projectId)}/export.pdf`),
}
