/** The Drawings page's records (backend app/routers/drawings.py). */

export type Status =
  | "approved"
  | "approved_as_noted"
  | "under_review"
  | "not_approved"
  | "reply_not_found"
  | "not_submitted";

export const STATUS_LABEL: Record<Status, string> = {
  approved: "Approved",
  approved_as_noted: "Approved as Noted",
  under_review: "Under Review",
  not_approved: "Not Approved",
  reply_not_found: "Answered – Reply Not Found",
  not_submitted: "Not Submitted",
};

export const OFFICIAL_STATUSES: Status[] = ["under_review", "approved", "approved_as_noted", "not_approved", "reply_not_found"];

/** A file found at a revision nothing proves was submitted. */
export interface Candidate {
  id: number;
  revision: string;
  path: string | null;
  page: number;
  file_sha256: string;
  detected_at: string | null;
  status: "available" | "confirmed" | "ignored" | "superseded" | "conflict";
  evidence: Record<string, unknown> & { note?: string; ai?: AiVerdict };
  decided_at: string | null;
  label: string;
}

export interface LogCell {
  revision?: string;
  status: Status;
  label: string;
  reference?: string | null;
  path?: string | null;
  page?: number;
  remarks?: string | null;
  modified?: string | null;
  /** Why a revision reads as it does ("R2 was submitted, so R1 was submitted and answered; ..."). */
  note?: string | null;
  /** "sync" | "submission" | "engineer" | "ai" */
  source?: string;
  /** An engineer set this status: it stands over the folder and the AI. */
  confirmed?: boolean;
  source_missing?: boolean;
  submitted_at?: string | null;
  reply_at?: string | null;
  /** The date the sheet itself says it was issued (its title block's DATE cell, else the last date of its
   *  revision history), as "YYYY-MM-DD". Not when it was submitted: that is `submitted_at`. */
  issued_on?: string | null;
  /** Not an official revision: a file found ("R1 available"). */
  candidate?: Candidate;
}

export interface Hint {
  kind: string;
  label: string;
  severity: "info" | "warning" | "error";
  revision?: string;
  note?: string | null;
  source?: "system" | "ai";
  issue_id?: number;
  candidate_id?: number;
  path?: string | null;
}

/** How the log is listed: a row per floor of the building, or a row per
 *  IFC plan sheet (a typical sheet for a run of floors is one row, as the
 *  shop drawing answering it is one submission). */
export type LogView = "floor" | "ifc";

/** The IFC plan sheet a row of the IFC view belongs to. */
export interface IfcSheetRef {
  key: string;
  drawing: string;
  revision: string;
  /** The sheet's reference: the drawing number its title block prints, else its layout name. */
  sheet: string;
  /** The layout (tab) name in the IFC file ("FA 111"). */
  layout: string;
  /** The number the title block prints, if any; and why it is not the reference when it is not. */
  number: string | null;
  number_note: string | null;
  title: string;
  /** The sheet's floor as it writes it ("Typical 3rd to 16th Floor"). */
  label: string;
  floors: number;
  floor_keys: string[];
  floor_names: string[];
  /** The floors in a few words ("floors 3-16", "Ground Floor"). */
  range: string;
}

/** A shop drawing, or an IFC floor no shop drawing covers yet (`reference` null);
 *  in the IFC view, a shop drawing under its IFC sheet, or a sheet's floors still to submit (`ifc_sheet`). */
export interface LogRow {
  key: string;
  id: number | null;
  source: "shop_drawing" | "ifc_floor" | "ifc_sheet";
  reference: string | null;
  /** The drawing's title as its title block reads. */
  title?: string | null;
  /** IFC view only: the sheet the row is under; null for a floor on no IFC sheet. */
  ifc?: IfcSheetRef | null;
  /** IFC view only: the first row of its sheet, and how many rows the sheet has. */
  group_first?: boolean;
  group_size?: number;
  /** IFC view only: the drawing covers only part of the sheet's floors; the drawing goes on beyond this sheet. */
  partial?: boolean;
  spans?: boolean;
  /** IFC view only: the other shop drawings covering floors of this sheet, and the sheet's floors not submitted yet. */
  others?: { id: number; reference: string; floors: string; floor_keys: string[]; latest_revision: string | null; latest_status: Status; label: string }[];
  not_submitted_floors?: string[];
  /** The floor's canonical name ("L02"); the project's own name for it under it ("1st Mechanical Floor"). */
  floor: string;
  floor_secondary?: string | null;
  floor_named: string | null;
  floor_keys: string[];
  floors: number;
  typical: boolean;
  confirmed: boolean;
  remarks: string;
  cells: Record<string, LogCell>;
  revisions: Record<string, LogCell>;
  latest_revision: string | null;
  latest_status: Status;
  latest_note: string | null;
  latest_path: string | null;
  latest_page: number;
  candidates: Candidate[];
  hints: Hint[];
  issues: number;
}

/** One file of the project's IFC folder (backend app/ifc/services/folder_import.py). */
export interface IfcFolderFile {
  path: string;
  name: string;
  ext: string;
  size: number;
  modified: string;
  /** A DWG or DXF: the platform can read it. */
  readable: boolean;
  /** The drawing it is read as, if it is. */
  drawing: { id: number; filename: string; revision: string; reference: string | null; in_force: boolean } | null;
  /** A read of it queued or running. */
  job: { id: number; status: string; message: string | null; stage: string | null; done: number | null } | null;
}

export interface IfcFolder {
  system: string;
  /** The folder relative to the project ("03- Drawings/IFC/Electrical/FA"); null for a system whose IFC is not read. */
  folder: string | null;
  /** The project folder is on this PC and the IFC folder exists. */
  reachable: boolean;
  files: IfcFolderFile[];
  readable: string[];
}

export interface DrawingsLog {
  view: LogView;
  /** IFC view only: the IFC plan sheets in force (= the rows), and the shop drawings for floors the IFC has no sheet for, listed apart. */
  sheets?: number;
  groups?: number;
  others?: LogRow[];
  revisions: string[];
  rows: LogRow[];
  counts: Partial<Record<Status, number>>;
  submissions: number;
  review_items: number;
  candidates: number;
  floors: { key: string; name: string; secondary?: string | null; source: string; ifc_sheet: string | null }[];
  project: { id: number; ep_number: string; name: string | null };
  system: string;
  system_name: string;
  systems: string[];
  /** The IFC drawings the rows' sheets come from: the system's own, read into the platform. */
  ifc: { id: number; filename: string; revision: string; reference?: string | null; archive_path?: string | null }[];
  /** The system has no IFC drawing of its own: the sheets are this system's. */
  ifc_borrowed_from?: string | null;
  /** The system's IFC folder in the project folder, file by file. */
  ifc_folder?: IfcFolder;
  synced_at: string | null;
  reconciled_at: string | null;
  folder: string | null;
  warnings: string[];
}

export interface SystemSummary {
  code: string;
  name: string;
  floors: number;
  approved: number;
  approved_as_noted: number;
  under_review: number;
  not_approved: number;
  not_submitted: number;
  reply_not_found: number;
  approved_total: number;
  review_items: number;
  candidates: number;
  counts: Partial<Record<Status, number>>;
}

export interface DrawingsSummary {
  project: { id: number; ep_number: string; name: string | null };
  systems: SystemSummary[];
  synced_at: string | null;
}

/** The AI's structured answer about one finding: no reasoning, ever. */
export interface AiVerdict {
  task?: string;
  drawing_reference?: string | null;
  revision?: string | null;
  status?: string | null;
  assessment?: string | null;
  possible_same_floor?: boolean;
  evidence?: string | null;
  confidence?: number | null;
  reason_code?: string | null;
  requires_engineer?: boolean;
  validation?: string;
  validation_reason?: string | null;
  error?: string;
}

export interface Issue {
  id: number;
  key: string;
  kind: string;
  label: string;
  severity: "info" | "warning" | "error";
  source: "system" | "ai";
  system: string | null;
  shop_drawing_id: number | null;
  floor_key: string | null;
  text: string;
  detail: Record<string, unknown> & {
    revision?: string; candidate_id?: number; path?: string;
    /** A possible duplicate floor: the named floor and the level it may be. */
    alias_key?: string; canonical_key?: string; alias_label?: string; canonical_label?: string; evidence?: string;
  };
  ai: AiVerdict | null;
  created_at: string | null;
  updated_at: string | null;
  resolved_at: string | null;
  resolution: string | null;
}

export interface Issues {
  system: string;
  systems: string[];
  total: number;
  system_checks: Issue[];
  ai_review: Issue[];
}

export interface DrawingEvent {
  id: number;
  kind: string;
  text: string;
  system: string | null;
  shop_drawing_id: number | null;
  floor_key: string | null;
  detail: Record<string, unknown>;
  user_id: number | null;
  at: string | null;
}

export interface DrawingDetail extends LogRow {
  system: string;
  system_name: string;
  floor_source: Record<string, { source: string; ifc_sheet: string | null; active: boolean }>;
  revision_history: LogCell[];
  issues_list: Issue[];
  events: DrawingEvent[];
}

export function day(value: string | null | undefined): string {
  if (!value) return "–";
  // A date with no time of day (a sheet's issue date) is that day wherever the page is read.
  if (/^\d{4}-\d\d-\d\d$/.test(value))
    return new Date(`${value}T00:00:00Z`).toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" });
  const date = new Date(value.endsWith("Z") || value.includes("+") ? value : value + "Z");
  return date.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}

export function when(value: string | null | undefined): string {
  if (!value) return "–";
  const date = new Date(value.endsWith("Z") || value.includes("+") ? value : value + "Z");
  return date.toLocaleString(undefined, { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

/** The Drawings Assistant (backend app/services/drawings_chat.py). */
export interface AssistantStatus {
  available: boolean;
  reason: string | null;
  model: string | null;
  can_apply: boolean;
  actions: Record<string, string>;
}

/** A change the assistant proposes: the very call the page's own button
 *  makes, applied only when the engineer says so. */
export interface AssistantAction {
  kind: string;
  label: string;
  method: "POST" | "PUT" | "PATCH";
  path: string;
  body: Record<string, unknown>;
  drawing_id: number | null;
  drawing_reference: string | null;
  floor: string | null;
  reason: string;
}

export interface AssistantAnswer {
  system: string;
  reply: string;
  needs_engineer: boolean;
  actions: AssistantAction[];
  /** Proposals the records refused, with why. */
  dropped: { kind: string | null; reason: string }[];
  model: string;
  from_cache: boolean;
  can_apply: boolean;
  memory: { rows: number; rows_total: number; issues: number; events: number; truncated: boolean };
}
