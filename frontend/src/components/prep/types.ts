/** Drawings Preparation's data (app.redesign: service.view). */

export interface DrawingRow {
  id: number;
  filename: string;
  revision: string;
  review_status: string | null;
  /** What the review comes to (the Review step's mark): "done" only when a
   * model answered every part of every plan -- a plot alone is "not_reviewed". */
  review_state: "done" | "partial" | "not_reviewed" | "running" | "blocked" | "failed" | "stopped";
  redesign_status: string;
  output_status: string;
}

export interface Candidate {
  n: number;
  name: string;
  block: string;
  erasable: boolean;
}

export interface Placed {
  symbol?: number;
  name: string;
  block: string | null;
  rotation: number;
  page: number[];
}

export interface Coverage {
  open?: boolean;
  radius: number;
  area_m2?: number;
  uncovered_m2?: number;
  covered?: number;
  ok?: boolean;
  detectors?: number;
}

export interface Coordination {
  by: "agent" | "platform";
  moved_m: number;
  reason: string | null;
  refused: string | null;
}

export interface Check {
  verdict: "ok" | "check" | "reject";
  reason: string;
}

export interface Change {
  id: string;
  page: number;
  sheet: string;
  floor: string;
  room: string;
  system: string;
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
  // "interface": the FA Interface Schedule's modules; "coverage": a detector the
  // room's coverage needs. Both drawn only once approved.
  source?: string;
  interface?: { code: string; for: string; equipment: string; tag: string };
  drawn?: boolean;
  coverage?: Coverage;
  coordination?: Coordination;
  check?: Check;
}

export interface Symbol {
  id: number;
  name: string;
  code: string;
  block: string;
  count: number;
}

export interface AgentRecord {
  stage: "placement" | "coordination" | "review";
  label: string;
  floor: string;
  room: string;
  state: string;
  seconds: number;
  outcome: string;
}

export interface RoomDetail {
  key: string;
  floor: string;
  room: string;
  radius: number;
  open: boolean;
  issues: string[];
  refused: string[];
  by: "agent" | "platform";
  after: { area_m2: number; uncovered_m2: number; covered: number; ok: boolean } | null;
}

export interface FloorReview {
  page: number;
  floor: string;
  state: "done" | "failed" | "off";
  changes?: number;
  summary?: string;
  open_questions?: string[];
  recommendation?: "ready_for_draftsman" | "needs_engineer";
  verdicts?: Record<"ok" | "check" | "reject", number>;
  reason?: string;
}

export interface Run {
  started_at: string;
  finished_at: string | null;
  ai: boolean;
  model: string;
  orchestrator_model: string;
  parallel: number;
  radius: { smoke: number; heat: number };
  stage: "placement" | "coordination" | "review" | "done";
  agents: AgentRecord[];
  placement: { total: number; placed: number; failed: number; calls: number; seconds?: number; by?: string } | null;
  coordination: {
    rooms: number;
    issues: number;
    agent_rooms: number;
    agent_calls: number;
    moved: number;
    added: number;
    refused: number;
    open_rooms: number;
    gaps_left: number;
    columns: number | null;
    rooms_detail?: RoomDetail[];
  } | null;
  review: { state: "off" | "nothing" | "done" | "partial" | "failed"; model: string; calls: number; floors: FloorReview[] } | null;
  gate: { state: "ready" | "needs_engineer"; reasons: string[] } | null;
}

export interface Redesign {
  drawing: { id: number; filename: string; revision: string } | null;
  review: { status: string | null; undecided: number };
  status: string;
  error: string | null;
  calls: number;
  started_at: string | null;
  finished_at: string | null;
  changes: Change[];
  symbols: Symbol[];
  counts: Record<string, number>;
  output: { status: string; error: string | null; relative: string | null; file: string | null; at: string | null; changes: number };
  folder: string;
  run: Run | null;
  agents_on: boolean;
}
