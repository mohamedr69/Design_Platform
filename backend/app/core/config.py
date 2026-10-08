import os
from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def expand_path(value: str | None) -> str | None:
    """`~` and `%USERPROFILE%` / `$HOME` in a configured path, so one .env
    serves every machine the same OneDrive is synced to."""
    if value is None:
        return None
    value = os.path.expandvars(os.path.expanduser(value.strip()))
    return value or None


def find_synced_folder(name: str) -> str | None:
    """Where OneDrive put a synced SharePoint library on this machine.

    A library synced from SharePoint lands as `<Organisation>\\<Library> -
    <Folder>` directly under the user's profile (`C:\\Users\\x\\Juma Al
    Majid\\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects`), and a
    personal or business OneDrive keeps its folders under the path in the
    `OneDrive` / `OneDriveCommercial` variables. The folder is looked for by
    its name in all of those, exact name first, then as a prefix (a library
    renamed "... 2021 Projects (1)" by a second sync still counts)."""
    roots: list[Path] = []
    for candidate in (os.environ.get("OneDriveCommercial"), os.environ.get("OneDrive"), str(Path.home())):
        if candidate and Path(candidate).is_dir() and Path(candidate) not in roots:
            roots.append(Path(candidate))
    for pattern in (name, f"{name}*", f"*{name}*"):
        for root in roots:
            for depth in ("", "*/"):
                try:
                    hits = sorted(p for p in root.glob(f"{depth}{pattern}") if p.is_dir())
                except OSError:
                    hits = []
                if hits:
                    return str(hits[0])
    return None


# backend/, found from this file, so `.env` and the default data folders do not
# depend on the folder the server was started from.
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
# Where Tesseract's Windows installer puts it.
_TESSERACT_CANDIDATES = (
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tesseract-OCR" / "tesseract.exe",
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Tesseract-OCR" / "tesseract.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_DIR / ".env"), env_file_encoding="utf-8")

    app_name: str = "Engineering Project Platform"
    app_tagline: str = "Engineering a Safer Tomorrow"
    company_name: str = "Al Arabia for Safety & Security LLC"

    database_url: str = "sqlite:///./ep_platform.db"
    # One folder for everything the platform writes -- the database, the
    # uploads, the backups, the caches. Point it at a folder OneDrive syncs
    # and the same user finds their projects on every PC they sign in on;
    # left unset, everything stays under backend/ on this machine. ~ and
    # %VAR% are expanded. A DATABASE_URL, UPLOADS_ROOT or CACHE_ROOT set
    # explicitly is kept as set.
    data_root: str | None = None
    backups_root: str | None = None

    secret_key: str = "dev-secret-key-change-me-in-production"
    access_token_expire_minutes: int = 30
    cookie_name: str = "access_token"
    cookie_secure: bool = False

    max_failed_login_attempts: int = 5
    lockout_minutes: int = 15

    default_admin_email: str = "admin@ep-platform.com"
    default_admin_password: str = "ChangeMe123!"

    cors_origins: list[str] = ["http://localhost:5173"]

    # The project archive: the SharePoint library OneDrive syncs to every
    # office machine. Left unset, it is found by name on whichever machine
    # the platform runs (see `find_synced_folder`); set it only for an
    # archive kept somewhere unusual. `~` and %VARS% are expanded.
    # Production should replace this with Microsoft Graph search against
    # SharePoint -- see app/services/ep_resolver.py docstring.
    projects_root: str | None = None
    projects_root_name: str = "SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
    # Tests turn this off: their archives are the temporary folders they build.
    projects_root_autodetect: bool = True

    # --- The project register (app/services/project_register.py) --------
    # The company's own record of every job and the engineer designing it,
    # kept as a workbook in the archive. Read, never written: it is the
    # design manager's register, maintained outside the platform. Relative
    # to the archive root, or absolute.
    project_register: str = "Khaled Issa/Fire Alarm Project Details.xlsx"
    project_register_sheet: str = "Sheet1"

    # --- The archive index (app/services/ep_directory.py) ---------------
    # The archive's EP folders, walked once and then searched in the
    # database, so typing an EP number suggests projects instead of
    # walking a synced drive. Off means every Find Project walks the
    # archive as it used to.
    # When the rules for reading documents change, every project that has
    # already been synced reads itself again -- once, in the background:
    # the worker queues a sync for each when it starts. Off, a project keeps
    # what it was read as until someone presses Sync documents on it.
    reread_on_rules_change: bool = True
    # Document Classification V2 (app.services.document_classification):
    # off, nothing is classified and every path behaves as before; on, the
    # sync writes a metadata hint beside each new or changed row and the
    # processing an assessment from what it stored -- metadata only, never
    # a routing, a status or a record. Stored assessments stay when it is
    # turned off again.
    document_classification_v2: bool = False
    # M2 extraction: whether observations the current reader makes but the
    # accepted reader did not (a decision framed or highlighted into the
    # page, a cover of an untracked discipline, a scanned transmittal) are
    # promoted to records and statuses. Off: they are kept beside the
    # records as observations and candidates, and the registers see what
    # they saw before. On: the isolated evaluation path.
    extraction_promote_observations: bool = False

    # The background worker (app.workers.sync_worker), a process of its own
    # that runs the document syncs so they never slow the pages down.
    # How often an idle worker looks for a queued sync.
    worker_poll_seconds: float = 1.5
    # Run the worker below normal Windows priority, so the engineer's own
    # programs and the API are served first.
    worker_below_normal_priority: bool = True
    # How many documents one sync reads at the same time, each in a process
    # of its own. Three, not one per core: reading a document the first time
    # takes about 300 MB, and a CAD floor-plan set with 400,000 shapes a page
    # about 900 MB, on PCs with 16 GB shared with everything else -- three at
    # once stays under 3 GB. (A second reading comes from the page cache and
    # takes about 100 MB.) 0 or 1 reads them one after another in the worker
    # itself. The AI reads forms one at a time whatever this is.
    sync_file_workers: int = 3
    # The reader processes are replaced after this many files each: a
    # reader that has opened fifty documents holds on to memory MuPDF does
    # not give back. Done between files with nothing in flight
    # (document_sync.read_in_completion_order), never by the pool itself.
    sync_reader_recycle_tasks: int = 50
    # Nothing finished reading for this long while files were in flight:
    # the readers are stuck or gone. They are stopped, those files are
    # marked failed with the reason, and the rest are read by fresh
    # readers. A safety net against a hang -- EP-30784's first sync sat
    # for three hours on a reading that was never going to come back --
    # not a time a slow document is expected to keep to: a drawing set of
    # two hundred CAD sheets can take twenty minutes legitimately.
    sync_read_stall_seconds: int = 1800
    archive_index_enabled: bool = True
    # Scan on server start when the index has never been built, or has
    # gone stale, so a new machine needs nothing done to it.
    archive_index_scan_on_start: bool = True
    # How old a complete scan may get before the server runs another in
    # the background. This is what notices an EP folder added to OneDrive
    # today; the search box also records a folder it had to fall back to a
    # walk for, so a brand-new number is indexed the moment it is used.
    archive_index_refresh_minutes: int = 30

    @model_validator(mode="after")
    def _resolve_projects_root(self) -> "Settings":
        self.projects_root = expand_path(self.projects_root)
        # A shared .env can retain another Windows user's absolute OneDrive
        # path. When that path is unavailable, use this machine's synced copy.
        # Keep an unreachable explicit value only when no unambiguous synced
        # library can be found, so callers still report the configured error.
        if self.projects_root_autodetect and (
                not self.projects_root or not Path(self.projects_root).is_dir()):
            found = find_synced_folder(self.projects_root_name)
            if found:
                self.projects_root = found
        return self

    # Where documents uploaded through the platform are kept: a project's
    # own folder under here. Never the archive itself -- the platform reads
    # the archive, it does not write to it.
    uploads_root: str = "uploads"

    # Path to tesseract.exe. Unset: found on the PATH or where the Windows
    # installer puts it, so a new machine needs no setting.
    tesseract_cmd: str | None = None

    # AutoCAD's Core Console (accoreconsole.exe), which converts an uploaded
    # IFC DWG to DXF for the BOQ as per IFC drawings. Unset: found under
    # Program Files\Autodesk\AutoCAD <year>, newest first, then the free ODA
    # File Converter -- see app/ifc/dxf/convert.py. Only needed when AutoCAD
    # is installed somewhere else.
    accoreconsole_path: str | None = None

    # --- BOQ as per IFC drawings (app/ifc) ---------------------------------
    # The one limit on an uploaded DWG, DXF or zip, in MB: every check and
    # every message is worked out from it (app.ifc.services.upload).
    ifc_max_upload_mb: int = 500
    # A zip of the building: how many files it may hold, and how much its
    # drawings may come to unpacked (declared sizes, checked before anything
    # is unpacked, and actual bytes, checked while each is unpacked).
    ifc_max_zip_members: int = 200
    ifc_max_zip_unpacked_mb: int = 500
    # How many IFC reads run at the same time across every IFC worker. A
    # large drawing's read takes up to a GB of memory: raise it only on a
    # PC with the memory to spare.
    ifc_worker_concurrency: int = 2
    # Uploads waiting for the worker live in a staging folder; one no job
    # refers to any more is removed after this many hours.
    ifc_staging_max_age_hours: float = 24.0
    # A symbol whose letters and block name both name the same device, on a
    # fire alarm layer, is taken as that device without asking (source
    # "deterministic"). Off by default: a symbol's words are a hint, never an
    # answer -- a block name means different things to different consultants
    # -- so they only choose the candidates the AI and the engineer pick from.
    ifc_deterministic_auto_verify: bool = False
    # The AI review of symbols nothing else could identify (app.ifc.services.
    # ai_symbol_review). Runs only when AI_ENABLED is on as well. The model
    # sees one symbol's letters, block names and shape counts, and chooses
    # from a short list of device types Python picked -- never the drawing.
    ifc_ai_symbol_review_enabled: bool = True
    # The second look, at the symbol's small picture, for what the words
    # alone left uncertain.
    ifc_ai_visual_review_enabled: bool = True
    ifc_ai_batch_size: int = 15
    ifc_ai_visual_batch_size: int = 4
    # Unset: the provider's small tier (AI_MODEL_SMALL). A cheaper model is
    # enough for choosing one of five names.
    ifc_ai_model: str | None = None
    ifc_ai_visual_model: str | None = None
    # Below this the AI's answer is shown to the engineer, not taken.
    ifc_ai_auto_verify_threshold: float = 0.97
    ifc_ai_max_candidates: int = 5
    ifc_ai_max_calls_per_job: int = 20
    # Retries of a call that failed on the way (timeout, rate limit), not of
    # an answer the model gave.
    ifc_ai_retries: int = 1
    ifc_ai_timeout_s: float = 120.0

    # --- The Drawings page (app/services/shop_drawings, drawing_ai_review) --
    # The AI review of a system's shop drawings: only what the rules could
    # not settle (a reply that names no drawing the log knows, a candidate
    # revision a transmittal may have carried), one compact question each,
    # cached by the file's content. Runs only when AI_ENABLED is on as well.
    drawings_ai_review_enabled: bool = True
    drawings_ai_model: str | None = None
    drawings_ai_auto_accept_threshold: float = 0.97
    drawings_ai_max_calls_per_sync: int = 10
    drawings_ai_timeout_s: float = 90.0
    # The Drawings Assistant (app/services/drawings_chat): a chat on the
    # Drawings page that answers from the project's records and proposes
    # the changes the engineer asks for, each applied only by the engineer.
    # Runs only when AI_ENABLED is on as well; a project whose AI policy
    # is "blocked" gets none. The memory it is given is bounded by rows
    # and events, and by input tokens, so a tall building fits a call.
    drawings_chat_enabled: bool = True
    # Switched on by itself (DRAWINGS_CHAT_AI_ENABLED) like the drawing review, AI_ENABLED
    # staying off for the rest of the platform; AI_ENABLED on switches it on as well.
    drawings_chat_ai_enabled: bool = False
    drawings_chat_model: str | None = None
    drawings_chat_timeout_s: float = 120.0
    drawings_chat_max_rows: int = 150
    drawings_chat_max_events: int = 30
    drawings_chat_max_input_tokens: int = 24000
    drawings_chat_max_output_tokens: int = 1500
    drawings_chat_max_calls_per_project_per_day: int = 200
    # The model's look at documents the classification rules could only
    # guess (app/services/document_classification_ai): a document whose
    # answer is a path hint, unknown or ambiguous has its first page's text
    # read by the small model, several documents per call. Only a fresh
    # reading is sent, never twice for the same content and path, and the
    # answer is stored beside the rules' (source "ai"), never confirmed.
    # Switched on by itself (DOCUMENT_CLASSIFICATION_AI_ENABLED), AI_ENABLED
    # staying off for the rest of the platform; AI_ENABLED on switches it on too.
    document_classification_ai_enabled: bool = False
    document_classification_ai_model: str | None = None
    document_classification_ai_batch: int = 24
    document_classification_ai_page_chars: int = 2500
    document_classification_ai_max_calls_per_run: int = 100
    # The pass's own daily cap (rolling 24 hours, per project), counted on its
    # task alone and checked before each batch -- distinct from, and inside,
    # the platform's AI_MAX_CALLS_PER_PROJECT_PER_DAY shared by every task.
    document_classification_ai_max_calls_per_project_per_day: int = 25
    document_classification_ai_timeout_s: float = 240.0
    document_classification_ai_max_output_tokens: int = 5000
    # Opening a project folder in Explorer on the PC the platform runs on
    # (Drawings > Open folder). Only for a browser on that same PC: the
    # request must come from a loopback address with no proxy header on it,
    # from a page served on a loopback origin. Off, the button is refused.
    desktop_actions_enabled: bool = True

    @model_validator(mode="after")
    def _apply_data_root(self) -> "Settings":
        root = expand_path(self.data_root)
        self.data_root = root
        if not root:
            self.backups_root = self.backups_root or str(BACKEND_DIR / "backups")
            return self
        folder = Path(root)
        if self.database_url == "sqlite:///./ep_platform.db":
            self.database_url = "sqlite:///" + (folder / "ep_platform.db").as_posix()
        if self.uploads_root == "uploads":
            self.uploads_root = str(folder / "uploads")
        if not self.cache_root:
            self.cache_root = str(folder / ".cache")
        self.backups_root = self.backups_root or str(folder / "backups")
        return self

    @model_validator(mode="after")
    def _expand_cli(self) -> "Settings":
        self.ai_claude_cli = expand_path(self.ai_claude_cli) or "claude"
        return self

    @model_validator(mode="after")
    def _find_tesseract(self) -> "Settings":
        self.tesseract_cmd = expand_path(self.tesseract_cmd)
        if not self.tesseract_cmd:
            import shutil

            if not shutil.which("tesseract"):
                found = next((p for p in _TESSERACT_CANDIDATES if p.is_file()), None)
                self.tesseract_cmd = str(found) if found else None
        return self

    # --- The company library ------------------------------------------
    # Everything a submittal needs that is not about a particular project:
    # the company documents, the templates and the manufacturers'
    # datasheets. One local folder with a fixed structure, not the synced
    # archive -- see app/services/company_library.py for the layout and why.
    #
    # Unset means `backend/library`, resolved from the code rather than from
    # the working directory, so it does not matter where uvicorn is started.
    library_root: str | None = None

    # A manufacturer is normally *discovered*: a folder under
    # `library/datasheets/` is a library, named for the brand. This is the
    # override, for a library kept somewhere else -- relative to the library
    # root, or absolute. DATASHEET_LIBRARIES='{"MENVIER": "D:/menvier"}'
    datasheet_libraries: dict[str, str] = {}

    # The submittal builder: the company documents that go into every
    # material submittal (Company Profile, Trade License, ISO and
    # civil-defence certificates, test reports, ...) and the templates the
    # package is built from (cover page, index and dividers). Relative to
    # the library root, or absolute. Read, never written to.
    submittal_library: str = "submittal"

    # Derived data -- the datasheet index, above all. Never inside the
    # library: that folder can be read-only or synced. Unset means
    # `backend/.cache`.
    cache_root: str | None = None

    # How long a library's file listing is trusted before it is walked
    # again. Looking a BOQ's fifty parts up used to re-walk the folder fifty
    # times; over a synced drive that was the whole cost of the page. A
    # datasheet dropped in shows up within this many seconds, and Reindex on
    # the library page is the way to see it at once. 0 disables the throttle.
    library_rescan_seconds: float = 60.0

    # --- Selective AI assistance (app/ai) ---------------------------------
    # Off by default: every deterministic path runs without it. When on, a
    # model is asked only about issues the router marks eligible -- an
    # unreadable quantity cell, an unlabelled design sheet -- with the
    # evidence for that issue alone, and its answer is a proposal an
    # engineer accepts, never a value written by itself.
    ai_enabled: bool = False
    # Which way the model is reached: "claude-code" (Claude through the Claude
    # Code CLI, on the Claude subscription signed in on this server -- no API
    # key), "claude" (Anthropic API) or "openai" (OpenAI API). Each has its
    # own provider class in app/ai/provider.py behind one interface.
    ai_provider: str = "claude-code"
    # Tasks switched off on this server whatever else allows them, comma
    # separated (e.g. "answer_clauses,read_field"): the deployment control
    # for rolling a task back without a code change. See app/ai/evaluation.py.
    ai_disabled_tasks: str = ""
    # The AI verification of a project against its sources (app.ai.verification):
    # calls one run may make, calls a project may make in a day across runs, the
    # time a run may take, and whether a project that has never been verified is
    # verified when its BOQ or Project Info page is first opened.
    ai_verify_max_calls: int = 80
    ai_verify_max_calls_per_day: int = 240
    ai_verify_max_elapsed_s: float = 3600.0
    ai_verify_auto: bool = True
    # The AI read of a project's Design Sheets on its first open
    # (app.ai.sheet_reader): the model reads every page, the OCR read is the
    # witness, and the reading is stored for good -- a document with the same
    # content is never read again. Calls one document may take (a page is one
    # call per band, plus close-ups of disputed rows), calls a project may
    # make in a day across reads, the time a read may take, and the
    # reasoning depth for a whole page (the API provider only).
    ai_read_max_calls_per_document: int = 60
    ai_read_max_calls_per_project_per_day: int = 600
    ai_read_max_elapsed_s: float = 1800.0
    ai_read_effort: str = "high"
    # Time a read keeps in hand before starting a call: a page band or a
    # row close-up is not begun when less than this remains of
    # AI_READ_MAX_ELAPSED_S, so the limit stops the read between calls,
    # with everything so far kept, rather than in the middle of one.
    ai_read_band_reserve_s: float = 90.0
    ai_read_close_up_reserve_s: float = 20.0
    # A row the model read is scored against the page's own geometry (the
    # columns and Tesseract's words there: app.extraction.row_geometry), 0 to
    # 1. At or above HIGH the row is accepted on the model's reading and the
    # geometry alone; below LOW it needs the stronger verification; between,
    # the fast one. Set by benchmark (EP-30784), not by hand.
    boq_confidence_high: float = 0.85
    boq_confidence_low: float = 0.5
    # Whether every page is read a second time in full by the standard
    # model (the reader before 2026-09-27). Off, a row the geometry rates
    # high is accepted on the first reading; the rest are verified as row
    # crops, AI_VERIFY_ROWS_PER_CALL to a call, by the small tier first and
    # the standard tier only where that disagrees or cannot read the row.
    ai_read_full_second_pass: bool = False
    ai_verify_rows_per_call: int = 8
    # The Claude Code program for "claude-code": a name on the PATH or the full
    # path to claude.exe. Sign in once with `claude` as the user the server runs as.
    # ~ and %VAR% are expanded, so one .env serves every Windows user
    # (`%LOCALAPPDATA%\ep-platform\claude-2.1.288\claude.exe`), not just the one
    # whose name was typed into it.
    ai_claude_cli: str = "claude"
    # One Claude Code call, start to finish (it starts a process and may read an image).
    ai_cli_timeout_s: float = 300.0
    # At most this many model turns in one Claude Code call (`--max-turns`;
    # reading a picture with the Read tool is a turn): unset, the CLI's own
    # limit. A call that needs more ends as `max_turns`, with no answer.
    ai_cli_max_turns: int | None = None
    # The Claude Code program's own requests besides the one asked for: none of its non-essential traffic
    # (CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC -- without it, job 223's looks carried a Haiku request of the
    # CLI's own), and how many times it retries a failed request by itself (CLAUDE_CODE_MAX_RETRIES; 0: none,
    # a failed look is the review's to report; unset: the CLI's default of 10).
    ai_cli_disable_nonessential_traffic: bool = True
    ai_cli_max_retries: int | None = 0
    # Pictures sent inside the prompt (Claude Code's stream-json input) rather than as
    # files the model opens with its Read tool -- one turn a picture fewer, each turn
    # re-sending the conversation. Off until one live call on this CLI has shown it
    # answers from the picture at full size (2026-10-05: not yet probed).
    ai_cli_inline_images: bool = False
    # Drawings Review (app.review): the FA IFC drawing's rooms looked at by
    # the model, a few rooms a call. Its own model and limits -- a review is
    # ~80 vision calls, far past the per-document budget above.
    # Switched on by itself (DRAWING_REVIEW_AI_ENABLED) like the FA Interfaces
    # workflow and Drawings Preparation, AI_ENABLED staying off for the rest of
    # the platform; off, a review plots the drawing and stops "blocked".
    drawing_review_ai_enabled: bool = False
    drawing_review_model: str = "claude-opus-5-5"
    # Reasoning depth for those drawing looks (the review, the redesign's
    # placements, the interface schedule's damper look). Sent to the CLI as
    # --effort and to the API as output_config.effort; without it Claude Code
    # used its own default and the API AI_EFFORT ("low").
    drawing_review_effort: str = "high"
    drawing_review_max_calls: int = 300
    drawing_review_max_elapsed_s: float = 4 * 3600.0
    drawing_review_max_cost: float = 50.0
    drawing_review_timeout_s: float = 600.0
    drawing_review_windows_per_call: int = 2
    # Each look through Claude Code: its pictures inside the message (no Read turn a picture), the turn
    # limit given to the CLI, and the most turns a reply may *report* before the review stops sending looks
    # (Claude Code 2.1.289 answers a one-turn structured look as num_turns 2: jobs 220-221). A reported
    # turn is not a model request; the CLI does not say how many requests it made.
    drawing_review_inline_images: bool = True
    drawing_review_cli_max_turns: int | None = 1
    drawing_review_max_reported_turns: int = 2
    # Calls at once (each a Claude Code process); the provider caps it again at AI_MAX_CONCURRENCY.
    drawing_review_parallel: int = 2
    # Drawings Preparation (app.redesign: the review's devices placed on the plan): the
    # Opus placement agents, side by side; the Opus coordination agent on each room the
    # platform found a clash or a coverage gap in; the Opus orchestrator reviewing every
    # floor's placed devices. Switched on by itself (PREP_AI_ENABLED) like the FA
    # Interfaces workflow, AI_ENABLED staying off for the rest of the platform; off,
    # the devices are placed at the review's point and coordinated by the platform alone.
    prep_ai_enabled: bool = False
    prep_model: str = "claude-opus-5-5"
    prep_orchestrator_model: str = "claude-opus-5-5"
    prep_effort: str = "high"
    prep_agent_parallel: int = 4
    prep_max_concurrency: int = 4
    # The detection's coverage on plan (the engineers, 6 October 2026): no point of a
    # room further than this from a detector -- NFPA 72's 0.7 x 9.1 m spacing.
    prep_smoke_radius_m: float = 6.3
    prep_heat_radius_m: float = 6.3
    # The drawing's columns: what is drawn on a layer like these, column-sized.
    prep_column_layers: str = r"COLUMN|\bCOLS?\b|S-COL|A-COL|STR.*COL|PILLAR|\bCOL[-_ ]"
    # The drawing's walls (app.redesign.walls, M8): only lines whose effective layer's
    # own name (a bound xref's "X$0$" prefix taken off) is like these are walls --
    # EP-30880: 06-WALL, 11-GLASS-1, 10-SILL; finishes drawn along a wall (23-WALL-TILES)
    # are not. Case-insensitive; walls.NOT_WALLS still refuses what it names.
    prep_wall_layers: str = r"^(?!.*(?:TILE|FINISH)).*(?:WALL|PARTITION|CURTAIN|GLASS|GLAZ|SILL)"
    # The interface schedule's damper pictures (app.interfaces.render): drawn in
    # a child process with a deadline per picture and for opening the drawing;
    # an overrun kills the child and that window is reported unread, never
    # empty. Restarts: how many times the drawing is opened again after an
    # overrun. ezdxf's own hatch-pattern timeout is kept short. In-process
    # drawing (no time box; stop between pictures only) is the rollback.
    fa_render_window_timeout_s: float = 120.0
    fa_render_plan_timeout_s: float = 900.0
    fa_render_restarts: int = 1
    fa_render_hatching_timeout_s: float = 2.0
    fa_render_in_process: bool = False
    # A OneDrive cloud-only placeholder (Files On-Demand) that is new or
    # changed: opened by a read, which makes OneDrive bring it down; false
    # leaves it "not synced" until the engineer asks to download and read.
    # An unchanged file read before is never opened again either way.
    fa_read_cloud_only_files: bool = True
    # The FA Interfaces drawing workflow (fa_interfaces_run): drawing agents (one
    # per drawing, the damper look on drawing_review_model at drawing_review_effort)
    # running FA_AGENT_PARALLEL drawings at once -- each opens its drawing in a child
    # process, about 2 GB for EP-30880's, so this is a memory bound too; and the Opus
    # review: the orchestrator reviewing their reports (coverage, conflicts), its own
    # model, effort, time, input size, and a budget reserved apart from the agents'.
    # (Fable held this role until 2026-10-05; it is Opus now, an exact-model request.)
    # A review that cannot run leaves the run provisional and says so; it is retried
    # at most FA_ORCHESTRATOR_RETRIES_PER_DAY.
    fa_agent_parallel: int = 2
    # The workflow's models -- the Opus drawing agents and the Opus review -- switched
    # on by themselves while AI_ENABLED stays off for the rest of the platform (no
    # background AI work anywhere else). AI_ENABLED on switches them on as well.
    fa_ai_enabled: bool = False
    fa_orchestrator_model: str = "claude-opus-5-5"
    fa_orchestrator_effort: str = "high"
    fa_orchestrator_timeout_s: float = 900.0
    fa_orchestrator_max_input_tokens: int = 150_000
    fa_orchestrator_max_output_tokens: int = 8_000
    fa_orchestrator_retries_per_day: int = 3
    # The orchestrator's own calls in a day, per project (W-BUD, review F10): its
    # allowance is reserved apart from the drawing agents' looks -- those are bounded
    # by the drawing review's budget and never consume it -- and a run whose
    # orchestrator could not be served within it starts no paid look at all.
    fa_orchestrator_max_calls_per_day: int = 64
    # The Opus finding review (app.interfaces.findings): every item that would go to
    # Verification Required is first looked at by Opus on the original drawing views
    # and the supporting evidence, and comes back present (scheduled), absent or not
    # an interface (excluded, kept for traceability) or unresolved (to the engineer).
    # Items one run may review, at once, per call, a day per project; drawing views
    # shown per item. An item past the bound stays for the engineer, said "not
    # reviewed", and the run stays provisional.
    fa_findings_model: str = "claude-opus-5-5"
    fa_findings_effort: str = "high"
    fa_findings_max_per_run: int = 80
    fa_findings_parallel: int = 4
    fa_findings_timeout_s: float = 600.0
    fa_findings_max_output_tokens: int = 4_000
    fa_findings_max_calls_per_day: int = 240
    fa_findings_views: int = 3
    # Time and calls (2026-10-05, measured on EP-30880's fresh run: 40 min, 112 calls).
    # Items of one sheet and one kind reviewed together, up to this many a call
    # (1: one call an item, as before); damper windows shown in one look call (1: one
    # a call, as before); the workflow's model calls at once (its own route; the
    # platform's shared route keeps AI_MAX_CONCURRENCY); drawings read side by side
    # (each DWG converted by its own Core Console, ~250 MB, DWG_CONVERT_PARALLEL at once
    # across the process); drawings drawn side by side for the finding review.
    fa_findings_per_call: int = 3
    fa_look_windows_per_call: int = 2
    fa_max_concurrency: int = 4
    fa_read_parallel: int = 2
    fa_render_parallel: int = 2
    dwg_convert_parallel: int = 2
    # The key, for the API providers only. Put it here (backend/.env is
    # gitignored) or let the vendor SDK read OPENAI_API_KEY or ANTHROPIC_API_KEY.
    ai_api_key: str | None = None
    # Model IDs are configuration, verified against the account's own model
    # list rather than assumed. The small tier makes the first reading; the
    # standard tier makes the second, independent one and the escalation for
    # a reply the first botched. Both are Claude Fable 5.1 (claude-fable-5-1):
    # the readings are of scanned engineering documents and accuracy is the
    # point; a second reading is independent by being of a different image
    # (a full-resolution close-up), not a different model. For "claude-code"
    # a Claude Code alias (fable, opus, sonnet) or the full id both work.
    ai_model_small: str = "claude-fable-5-1"
    ai_model_standard: str = "claude-fable-5-1"
    # Reasoning depth for these short extraction tasks.
    ai_effort: str = "low"
    ai_timeout_s: float = 60.0
    ai_max_concurrency: int = 2
    ai_max_retries: int = 3
    # Budgets. Estimated cost uses the prices below (per million tokens, in
    # the account's billing currency); reconcile against invoices.
    ai_max_input_tokens_per_task: int = 6000
    ai_max_output_tokens_per_task: int = 800
    ai_max_calls_per_document: int = 12
    ai_max_calls_per_project_per_day: int = 60
    ai_max_cost_per_job: float = 0.50
    ai_max_elapsed_s_per_job: float = 120.0
    ai_max_escalations_per_document: int = 2
    # Prices per million tokens, in the account's billing currency. Left at
    # zero on purpose: a made-up price is worse than none. Set them from the
    # vendor's current pricing page and the cost column and the per-job cost
    # cap start working; until then only the call-count and time limits bind.
    ai_price_input_per_million: float = 0.0
    ai_price_output_per_million: float = 0.0
    ai_price_cached_input_per_million: float = 0.0
    # How long a validated result is reused for the same evidence.
    ai_cache_ttl_days: int = 90
    # Field-level OCR confidence below which a DRF value is offered to the
    # model for a second reading (calibrated on the ten reviewed DRFs:
    # correct values read at 77-96, noise at 24-30, EP-31725's plot at 54).
    ai_ocr_review_confidence: float = 60.0

    # --- Compliance statements ------------------------------------------
    # A compliance statement is answered clause by clause. Python reads the
    # clauses, reuses answers from the company's past statements and writes
    # the workbook; the model is asked only about clauses nothing settles,
    # many at a time. These bound that one kind of call.
    ai_compliance_batch_clauses: int = 25
    ai_compliance_max_input_tokens: int = 9000
    ai_compliance_max_output_tokens: int = 3000
    ai_compliance_max_calls_per_statement: int = 12
    ai_compliance_max_elapsed_s: float = 600.0
    # A past answer is reused without asking when its clause reads this much
    # like the new one (0-1, word-level similarity).
    compliance_reuse_similarity: float = 0.86
    # Below this a past clause is not the same clause at all.
    compliance_hint_similarity: float = 0.6

    # --- The compliance knowledge base --------------------------------
    # The source collection: the folder holding the Compliance Response
    # Database workbook (Compliance_Response_Database.xlsx) and its exports.
    # An import source only -- the records are copied into the application
    # database, which is what autofill queries. Unset means no import can
    # run on this machine; the knowledge already imported keeps working.
    compliance_knowledge_source: str | None = None
    # Unset source: use the `data base` folder at the top of the repository
    # when it holds the workbook, so a fresh clone has its knowledge base.
    # Tests turn this off.
    compliance_knowledge_autodetect: bool = True
    # On startup, import the knowledge base in the background when nothing
    # has been imported yet and the source is reachable.
    compliance_knowledge_import_on_start: bool = True

    # --- Fallback: the library as it was filed in the archive -----------
    # Used only for what the local library does not hold, so a machine that
    # has not copied it across yet behaves exactly as before.
    # `scripts/sync_library.py` makes that copy.
    archive_datasheet_libraries: dict[str, str] = {
        "EDWARDS": "Systems/01- FAVE/01- Edwards - UL&EN/01- EST4",
    }
    archive_submittal_library: str = "Systems/01- FAVE/01- Edwards - UL&EN/01- EST4/submittal builder"


@lru_cache
def get_settings() -> Settings:
    return Settings()
