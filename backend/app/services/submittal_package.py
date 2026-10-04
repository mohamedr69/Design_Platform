"""Assemble a material submittal package: cover, index, dividers, documents.

This is the submittal the team issues, built the way they build it by hand.
All of it is fixed here in Python -- the section list, where each section's
documents come from, how the cover and the dividers are made -- so the same
package comes out the same way on every project, with no model in the loop.

**The section list is the company's own.** It is read off
`templates/Index & divider.pdf` in the submittal builder (the index page lists
all seventeen). That number is the section's identity -- the checklist ticks
it, the generated sections are found by it -- but **the package numbers what
it encloses, in order**: 01, 02, 03 ... on the index and on each divider, with
no gaps for the sections left out (platform owner, 2 October 2026).

**Where a section's documents come from** is one of three places:

- the **submittal builder** -- the company documents that are the same on
  every job (Company Profile, Trade License, certificates, test reports);
- the **project** -- its specification, its drawings, the schedule built from
  its BOQ, and the datasheets for the parts the BOQ actually quotes;
- **nowhere yet** -- a section the platform cannot produce, which is carried
  into the package as a divider with no content rather than silently dropped.

A document the builder does not hold is looked for in the project's own
folder before it is called missing -- not across the whole archive, which is
a synced OneDrive tree where that search costs more than an hour.

Two of the company's templates are not PDFs, and each is handled the way its
document works. **Country of Origin** (.xlsx) is a table, so it is drawn here
from the sheet's data, laid out like the Schedule of Material. The **warranty**
(.docx) is a letter on the company letterhead, so it is filled in and converted
by Word rather than redrawn -- a tidier page built from its words would be a
different document wearing its text. Any other non-PDF original in the builder
is reported as needing a PDF rather than quietly left out.
"""

from __future__ import annotations

import io
import os
import dataclasses
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pymupdf

from app.services import boq_provenance

from app.models import Project

# The company's index, in template order. The number is the section's
# permanent identity, not its position in a particular package.
SECTIONS: list[tuple[int, str]] = [
    (1, "Company Profile"),
    (2, "Copy of Related Specification"),
    (3, "Approved List of Manufacturers"),
    (4, "Compliance Statement"),
    (5, "Schedule of Material"),
    # Added after the schedule on the platform owner's instruction. It is not
    # in the printed Index & divider template, which lists seventeen, so its
    # divider is made from one of the template's (see build_divider) and
    # every section after it moves down one.
    (6, "Battery Calculation"),
    (7, "Product Catalogue or Brochure"),
    (8, "Technical Data Sheet"),
    (9, "Copy of Related Drawings"),
    (10, "Trade License"),
    (11, "Certifications"),
    (12, "Test Reports"),
    (13, "Project Reference List"),
    (14, "Previous Approvals"),
    (15, "Country of Origin"),
    (16, "Warranty Certificate"),
    (17, "Material Sample Photos"),
    (18, "Others Documents (Certificates, Approvals Etc)"),
]

SECTION_NAMES = dict(SECTIONS)

# Which folder of the submittal builder holds each section's documents. A
# section not listed here is not a company document: it comes from the
# project, or it is not built yet.
LIBRARY_FOLDERS: dict[int, tuple[str, ...]] = {
    1: ("Company Profile",),
    7: ("Product Catalogue or Brochure",),
    10: ("Trade License",),
    11: ("ISO Certificates", "Civil defence certificates"),
    12: ("Test certificates",),
    13: ("Project Reference List",),
    14: ("Previous Approvals",),
    # 15 Country of Origin and 16 Warranty Certificate are drawn from their
    # templates, not merged -- see build_country_of_origin / build_warranty.
    17: ("templates/will_be_submitted_separatelly.pdf",),
    18: ("templates/not_applicable.pdf",),
}

# --- the fire-rated cables' index ---------------------------------------------------------
#
# A fire-rated cable submittal is a different package: eleven sections, the
# company's documents from COMMON and the cable brand's own folder of the
# submittal builder, the brand's whole datasheet library, and a warranty
# worded for the cable. Only when the cable brand was chosen on the Proposed
# Materials tab (the platform owner's instruction, 18 Sep 2026).
FRC_SECTIONS: list[tuple[int, str]] = [
    (1, "Company Profile"),
    (2, "Trade License"),
    (3, "ISO Certificate"),
    (4, "Manufacturer ISO Certificate"),
    (5, "Schedule of Material"),
    (6, "Product Data Sheet"),
    (7, "Authority Certificate"),
    (8, "Test Certificate"),
    (9, "Authorization Letter"),
    (10, "Previous Approvals"),
    (11, "Draft Warranty"),
]
# The submittal-builder folder of each section: looked for under the brand's
# folder first, then COMMON (app.services.company_library.submittal_path).
FRC_LIBRARY_FOLDERS: dict[int, tuple[str, ...]] = {
    1: ("Company Profile",),
    2: ("Trade License",),
    3: ("ISO Certificates",),
    4: ("ISO",),
    7: ("Civil defence certificate",),
    8: ("TEST CERTIFICATES",),
    9: ("AUTH",),
    10: ("PREVIOUS APPROVAL",),
}


@dataclass(frozen=True)
class PackageIndex:
    """The section list a package follows, and which numbers the platform
    fills from the project (None: that section is not in this index)."""

    sections: tuple[tuple[int, str], ...]
    folders: dict[int, tuple[str, ...]]
    spec: int | None = None
    schedule: int | None = None
    battery: int | None = None
    datasheet: int | None = None
    coo: int | None = None
    warranty: int | None = None
    # The datasheet section is the brand's whole library (the cables), not
    # the sheets of the BOQ's parts.
    library_datasheets: bool = False

    @property
    def names(self) -> dict[int, str]:
        return dict(self.sections)


def index_for(system_code: str | None) -> "PackageIndex":
    """The index a system's submittal follows: the fire-rated cables their
    own, everything else the company's seventeen-plus-one."""
    from app.services import system_rules

    if system_rules.canonical(system_code) == "FRC":
        return FRC_INDEX
    return FA_INDEX


# Sections the platform fills from the project itself.
SPEC_SECTION = 2
COMPLIANCE_SECTION = 4
SCHEDULE_SECTION = 5
BATTERY_SECTION = 6
DATASHEET_SECTION = 8
DRAWINGS_SECTION = 9

# Sections whose content the platform cannot produce yet. They are offered,
# and a package that includes one gets its divider and nothing behind it --
# which is what the checklist means by a section still to be filled.
NOT_BUILT: dict[int, str] = {
    3: "The approved list of manufacturers is not held by the platform yet.",
    4: "The compliance statement is written clause by clause and is not generated yet.",
    9: "Drawings are not assembled into the submittal yet.",
}

TEMPLATES = "templates"
COVER_TEMPLATE = "Cover Page - Material Submittal - R0.pdf"


def _template(library_root: Path, name: str) -> Path:
    """A template of the submittal builder. Templates are the company's, not
    a brand's, so they are found under COMMON (or the root, in the older
    layout); the path is returned even when the file is not there, so the
    caller's own "missing" handling still names it."""
    from app.services import company_library

    return company_library.submittal_path(library_root, None, f"{TEMPLATES}/{name}") or library_root / TEMPLATES / name
INDEX_TEMPLATE = "Index & divider.pdf"

_MERGEABLE = ".pdf"


@dataclass
class PackageDocument:
    """One file that goes into a section, or one that should and cannot."""

    name: str
    path: str | None = None
    source: str = ""          # "submittal builder", "project archive", "generated"
    pages: int = 0
    part_no: str | None = None
    # Every BOQ part this one sheet serves. Edwards documents a family on a
    # single sheet, so one PDF can cover several quoted parts -- it is merged
    # once and names them all, rather than appearing once per part.
    covers: list[str] = field(default_factory=list)
    missing_reason: str | None = None
    # The Schedule of Material block the sheet's parts are scheduled under:
    # the datasheets go in by block, each block behind a divider of its own.
    block: str | None = None
    # The part numbers to highlight on the sheet -- the proposed materials,
    # every other highlight it carries removed. None leaves it as filed.
    highlight: list[str] | None = None


@dataclass
class PackageSection:
    number: int
    name: str
    selected: bool
    documents: list[PackageDocument] = field(default_factory=list)
    note: str | None = None
    # What the platform draws for this section rather than merges:
    # "schedule", "battery", "coo" or "warranty" -- None for a merged one.
    producer: str | None = None

    @property
    def found(self) -> int:
        # A generated section (the schedule) has no file until the package is
        # built, but it is not missing anything.
        return sum(1 for d in self.documents if d.path or d.source == "generated")

    @property
    def missing(self) -> int:
        return sum(1 for d in self.documents if not d.path and d.source != "generated")


@dataclass
class PackagePlan:
    sections: list[PackageSection] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    library_found: bool = False
    library_path: str | None = None
    # The manufacturer the package is for; whose submittal-builder folder it draws on.
    brand: str | None = None
    # The part numbers the Schedule of Material proposes: what is highlighted
    # on the datasheets and the civil defence certificates.
    proposed: list[str] = field(default_factory=list)
    # How the catalogue prints a proposed part where the BOQ spells it
    # otherwise (the equipment table's aliases): {part: [spellings]}.
    aliases: dict[str, list[str]] = field(default_factory=dict)
    # "titled": the sheet's title and its Ordering Information table (the
    # fire alarm); "parts": the part numbers only, wherever a table lists
    # them, and read loosely -- the emergency lighting's sheets print the
    # order code without its "-M" and with a 0 for an O (platform owner).
    marking: str = "titled"

    @property
    def selected_sections(self) -> list[PackageSection]:
        return [s for s in self.sections if s.selected]

    def shown_number(self, section: PackageSection) -> int:
        """The section's number in this package: its place among the
        sections enclosed (1 for the first), not the company index's."""
        return next(i for i, s in enumerate(self.selected_sections, 1) if s is section)


# A spare copy left in the library ("... _copy.pdf", "... - Copy.pdf") is the
# same document twice, and twice in an issued submittal is a defect.
_COPY_RE = re.compile(r"[ _-]*(?:copy|\(\d+\))$", re.IGNORECASE)


def _pdfs_in(folder: Path) -> list[Path]:
    """Every PDF under a library folder, shallowest first, in name order."""
    if not folder.is_dir():
        return []
    found = sorted(
        (p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() == _MERGEABLE),
        key=lambda p: (len(p.parts), p.name.lower()),
    )
    kept: list[Path] = []
    stems = set()
    for path in found:
        stem = _COPY_RE.sub("", path.stem).strip().lower()
        if stem in stems:
            continue
        stems.add(stem)
        kept.append(path)
    return kept


def _non_pdf_originals(folder: Path) -> list[Path]:
    """Controlled originals a section holds that cannot be merged as they are."""
    if not folder.is_dir():
        return []
    return sorted(
        (p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in {".xlsx", ".xls", ".docx", ".doc"}),
        key=lambda p: p.name.lower(),
    )


def _library_documents(library: Path, section: int, brand: str | None = None,
                       folders: dict[int, tuple[str, ...]] | None = None) -> list[PackageDocument]:
    from app.services import company_library

    found: list[PackageDocument] = []
    for entry in (folders if folders is not None else LIBRARY_FOLDERS).get(section, ()):
        # The brand's own folder first, then COMMON, then the older flat layout.
        target = company_library.submittal_path(library, brand, entry) or library / entry
        if target.is_file():
            if target.suffix.lower() == _MERGEABLE:
                found.append(PackageDocument(name=target.name, path=str(target), source="submittal builder"))
            else:
                # A controlled .docx/.xlsx original. Converting it here would
                # need Office and would change the document on its way in.
                found.append(PackageDocument(
                    name=target.name, source="submittal builder",
                    missing_reason=f"{target.suffix.lstrip('.').upper()} original -- add a PDF of it to the submittal builder.",
                ))
            continue
        pdfs = _pdfs_in(target)
        for pdf in pdfs:
            found.append(PackageDocument(name=pdf.name, path=str(pdf), source="submittal builder"))
        if not target.exists():
            found.append(PackageDocument(name=entry, missing_reason="Not in the submittal builder."))
        elif not pdfs:
            # The folder is there but holds only originals (Country of Origin
            # is an .xlsx). Name them, so the gap is a task and not a silence.
            originals = _non_pdf_originals(target)
            for original in originals:
                found.append(PackageDocument(
                    name=original.name, source="submittal builder",
                    missing_reason=f"{original.suffix.lstrip('.').upper()} original -- add a PDF of it to the submittal builder.",
                ))
            if not originals:
                found.append(PackageDocument(name=entry, missing_reason="The submittal builder folder is empty."))
    return found


# Searching for a missing company document is capped hard, because almost
# every call is a miss and a miss must be cheap.
_SEARCH_MAX_FILES = 5000


def _search_archive(folder: Path | None, name: str) -> Path | None:
    """Look for a document the builder does not hold, inside this project.

    The builder is the intended home for these, but a company document is
    sometimes filed only in the project that last used it -- so **the
    project's own folder** is where it is looked for.

    It is deliberately not the whole archive. The archive is a synced
    OneDrive tree, and walking it even to depth four took **seventy minutes**
    for a single document that was not there: every directory entry is a
    cloud-placeholder lookup. A project folder is a few hundred files and
    answers in well under a second.
    """
    import os

    if folder is None or not folder.is_dir():
        return None
    wanted = re.sub(r"[^a-z0-9]", "", name.lower())
    if not wanted:
        return None

    seen = 0
    for dirpath, _dirnames, filenames in os.walk(folder, onerror=lambda _exc: None):
        for filename in filenames:
            if not filename.lower().endswith(_MERGEABLE):
                continue
            seen += 1
            if seen > _SEARCH_MAX_FILES:
                return None
            if wanted in re.sub(r"[^a-z0-9]", "", Path(filename).stem.lower()):
                return Path(dirpath) / filename
    return None


def datasheet_documents(project: Project, libraries: dict, system_code: str | None = None,
                        links: dict | None = None) -> list[PackageDocument]:
    """One datasheet per part the BOQ quotes, each included once.

    A part legitimately recurs all over a BOQ -- every panel has its own CPU
    -- and the same part number under two headings is still one product, so
    its datasheet belongs in the package once. Parts are taken in BOQ order
    and the first appearance of each part number is the one kept; a datasheet
    shared by several parts (one sheet covering a family) is also merged in
    only once.

    A submittal covers one system, so only that system's lines are read. A
    fire alarm package that walked the whole BOQ would carry the emergency
    lighting parts as well, and report every one of them as a missing
    datasheet because they are another manufacturer's.

    `links` is the equipment table by key (app.services.equipment_currents
    .index): a part with a datasheet recorded there takes that sheet before
    the library is searched. That is how SL2-65D3D-CGL-M, which no sheet is
    named for and which its sheet calls SL2MNM65D3D, gets its datasheet.
    """
    from app.services import equipment_currents
    from app.services.datasheet_library import libraries_for

    documents: list[PackageDocument] = []
    seen_parts: set[str] = set()
    seen_paths: set[str] = set()
    wanted = (system_code or "").strip().upper() or None

    from app.services import battery_materials

    for item in project.boq_items:
        if wanted and (item.system_code or "").strip().upper() != wanted:
            continue
        part = (item.catalog_no or "").strip()
        key = re.sub(r"[^A-Z0-9]", "", part.upper())
        if not key or key in seen_parts or key in NO_DATASHEET:
            continue
        # The BOQ's battery by capacity ("12V65A") is not what is proposed:
        # the calculation's selection is, with its own datasheet (below).
        if battery_materials.is_battery_line(item):
            continue
        seen_parts.add(key)

        match = None
        absolute: Path | None = None
        row = (links or {}).get(equipment_currents.key_of(part))
        if row is not None and row.datasheet_path:
            mapped = equipment_currents.mapped_match(row, libraries)
            if mapped is not None:
                library, match = mapped
                absolute = Path(library.folder) / match.path
        for library in ([] if match is not None else libraries_for(item.manufacturer, libraries)):
            # An option code's sheet is its family's: SL2NM65D3-M is in the
            # sheet that lists SL2NM65D3.
            trimmed = part.rsplit("-", 1)[0] if "-" in part else ""
            found = library.find(part) or (library.find(trimmed) if len(re.sub(r"[^A-Z0-9]", "", trimmed.upper())) >= 6 else [])
            if found:
                # Best first. A text match is kept: Edwards documents several
                # parts on one sheet, so 3-ZA20A is in ZA.pdf and 4-MIC is in
                # the audio/telephone sheet -- named only in the text, and
                # still the datasheet for that part. Rejecting those lost 17
                # of EP-30784's 51 fire alarm parts.
                match = found[0]
                absolute = Path(library.folder) / match.path
                break
        if match is None or absolute is None:
            documents.append(PackageDocument(
                name=part, part_no=part,
                missing_reason="No datasheet in the manufacturer's library.",
            ))
            continue
        key_path = str(absolute)
        if key_path in seen_paths:
            # One sheet covering several parts: already in, so record that it
            # serves this part too instead of merging it a second time.
            for existing in documents:
                if existing.path == key_path:
                    existing.covers.append(part)
                    break
            continue
        seen_paths.add(key_path)
        documents.append(PackageDocument(
            name=absolute.name, path=key_path,
            source=f"{match.library} datasheet library", part_no=part, covers=[part],
        ))
    documents += _battery_datasheets(project, libraries, wanted, seen_paths)
    return documents


BATTERIES_BLOCK = "Batteries"


def _battery_datasheets(project: Project, libraries: dict, wanted: str | None, seen_paths: set[str]) -> list[PackageDocument]:
    """The datasheet of every battery the battery calculation selects --
    the panels', the APS' and the BPS' -- each once, behind a divider of
    their own (platform owner, 2 October 2026). The fire alarm's only."""
    from sqlalchemy.orm import Session as _Session

    from app.services import battery_materials
    from app.services.datasheet_library import libraries_for
    from app.services.system_rules import canonical

    session = _Session.object_session(project)
    if session is None or (wanted and canonical(wanted) != "FAS"):
        return []
    out: list[PackageDocument] = []
    for battery in battery_materials.selected_batteries(session, project):
        absolute = None
        if battery.datasheet_library and battery.datasheet_path:
            library = libraries.get(battery.datasheet_library) or next(
                (lib for name, lib in libraries.items() if name.upper() == battery.datasheet_library.upper()), None)
            if library is not None:
                absolute = Path(library.folder) / battery.datasheet_path
        if absolute is None or not absolute.is_file():
            for library in libraries_for(battery.manufacturer, libraries) or list(libraries.values()):
                found = library.find(battery.catalog_no)
                if found:
                    absolute = Path(library.folder) / found[0].path
                    break
        if absolute is None or not absolute.is_file():
            out.append(PackageDocument(name=battery.catalog_no, part_no=battery.catalog_no, block=BATTERIES_BLOCK,
                                       missing_reason="No datasheet on file for the selected battery."))
            continue
        if str(absolute) in seen_paths:
            for existing in out:
                if existing.path == str(absolute):
                    existing.covers.append(battery.catalog_no)
            continue
        seen_paths.add(str(absolute))
        out.append(PackageDocument(name=absolute.name, path=str(absolute), source="battery datasheet",
                                   part_no=battery.catalog_no, covers=[battery.catalog_no], block=BATTERIES_BLOCK))
    return out


def plan_package(
    project: Project,
    selected: set[int],
    library_root: Path | None,
    project_folder: Path | None,
    datasheet_libraries: dict | None = None,
    spec_documents: list[tuple[str, str]] | None = None,
    system_code: str | None = None,
    battery_panels=None,
    brand: str | None = None,
    datasheet_links: dict | None = None,
) -> PackagePlan:
    """What would go into the package, section by section, without building it.
    `brand` is the manufacturer the submittal's system is for, which decides
    whose folder of the submittal builder the company documents come from.
    The section list is the system's (index_for)."""
    index = index_for(system_code)
    plan = PackagePlan()
    plan.brand = brand
    plan.proposed = _proposed(project, system_code)
    plan.aliases = _aliases(project, plan.proposed)
    from app.services.system_rules import canonical as _canonical

    plan.marking = "parts" if _canonical(system_code) == "ELS" else "titled"
    if index is FRC_INDEX and not brand:
        plan.warnings.append("Choose the cable brand on the Proposed Materials tab (Fire Rated Cables): the package draws on the brand's folder of the submittal builder.")
    if library_root is None or not library_root.is_dir():
        plan.warnings.append(
            "The submittal builder folder was not found; company documents cannot be collected. "
            "Set SUBMITTAL_LIBRARY to its path."
        )
    else:
        plan.library_found = True
        plan.library_path = str(library_root)

    for number, name in index.sections:
        section = PackageSection(number=number, name=name, selected=number in selected)
        if not section.selected:
            plan.sections.append(section)
            continue

        if index is FA_INDEX and number in NOT_BUILT:
            section.note = NOT_BUILT[number]
        elif number == index.spec:
            for label, path in spec_documents or []:
                section.documents.append(PackageDocument(name=label, path=path, source="project archive"))
            if not section.documents:
                section.note = "No specification was found for this project."
        elif number == index.schedule:
            section.producer = "schedule"
            if index is FRC_INDEX:
                if schedule_blocks(project, system_code):
                    section.documents.append(PackageDocument(name="Schedule of Material", source="generated"))
                else:
                    section.note = "No cable is chosen on the Proposed Materials tab, so there is nothing to schedule."
            elif project.boq_items:
                section.documents.append(PackageDocument(name="Schedule of Material", source="generated"))
            else:
                section.note = "The BOQ is empty, so there is nothing to schedule."
        elif number == index.battery:
            # Sized from the saved BOQ, so it is the same calculation the
            # Battery page shows -- computed by the caller, which has the
            # database the part currents live in.
            section.producer = "battery"
            if battery_panels:
                section.documents.append(PackageDocument(name="Battery Calculation", source="generated"))
            else:
                section.note = "No panel could be sized from the BOQ, so there is no calculation to enclose."
        elif number == index.coo:
            # Built from the BOQ like the schedule, with the countries taken
            # from the company's own reference sheet.
            section.producer = "coo"
            if project.boq_items:
                section.documents.append(PackageDocument(name="Country of Origin", source="generated"))
            else:
                section.note = "The BOQ is empty, so there is nothing to declare."
        elif number == index.warranty:
            section.producer = "warranty"
            section.documents.append(PackageDocument(name="Warranty Certificate", source="generated"))
        elif number == index.datasheet and index.library_datasheets:
            # Every chosen cable brand's whole datasheet library: the fire
            # rated cable's, and the emergency lighting's monitoring cable's
            # (Ramcro) where the project has one.
            missing_brands = []
            for cable_brand in _cable_brands(project, brand):
                library = next((lib for name_, lib in (datasheet_libraries or {}).items()
                                if name_.upper() == cable_brand.upper()), None)
                if library is None:
                    missing_brands.append(cable_brand)
                    continue
                for pdf in _pdfs_in(library.folder):
                    section.documents.append(PackageDocument(name=pdf.name, path=str(pdf),
                                                             source=f"{cable_brand} datasheet library"))
            if missing_brands:
                section.note = f"No datasheet library is on file for {' & '.join(missing_brands)}."
            elif not section.documents:
                section.note = f"No datasheet library is on file for {brand}." if brand else "Choose the cable brand first."
        elif number == index.datasheet:
            section.documents = _by_block(project, system_code, datasheet_documents(
                project, datasheet_libraries or {}, system_code, datasheet_links))
            if not section.documents:
                section.note = (
                    f"The BOQ quotes no {system_code} part numbers to find datasheets for."
                    if system_code else "The BOQ quotes no part numbers to find datasheets for."
                )
        elif plan.library_found and library_root is not None:
            section.documents = _library_documents(library_root, number, brand, index.folders)
            # Anything the builder does not hold is looked for in the archive.
            for document in section.documents:
                if document.path is None and document.missing_reason == "Not in the submittal builder.":
                    found = _search_archive(project_folder, document.name)
                    if found is not None:
                        document.path = str(found)
                        document.source = "project archive"
                        document.missing_reason = None
            if not section.documents:
                section.note = "No document is mapped to this section."

        plan.sections.append(section)
    return plan


def _cable_brands(project: Project, brand: str | None) -> list[str]:
    """The fire rated cable submittal's brands: the cable's, and the
    monitoring cable's where the project has a monitored emergency lighting
    system -- each once."""
    from sqlalchemy.orm import Session as _Session

    from app.services import frc_cables

    brands = [brand] if brand else []
    session = _Session.object_session(project)
    if session is not None:
        row = frc_cables.get(session, project)
        if row is not None and row.brand:
            brands.append(row.brand)
        monitoring = frc_cables.monitoring_for(row, project)
        if monitoring and monitoring[0]:
            brands.append(monitoring[0])
    return list(dict.fromkeys(b.strip().upper() for b in brands if b and b.strip()))


def _aliases(project: Project, parts: list[str]) -> dict[str, list[str]]:
    """The equipment table's other spellings of the proposed parts -- the
    catalogue's order code for the BOQ's ("SL2-65D3D-CGL-M" is SL2MNM65D3D)."""
    from sqlalchemy.orm import Session as _Session

    from app.services import equipment_currents

    session = _Session.object_session(project)
    if session is None:
        return {}
    try:
        table = equipment_currents.index(session)
    except Exception:  # noqa: BLE001 -- nothing extra is matched rather than the package failing
        return {}
    out = {}
    pieces = [piece.strip() for part in parts for piece in part.split("+") if piece.strip()]
    for part in dict.fromkeys([*parts, *pieces]):
        row = table.get(equipment_currents.key_of(part))
        names = [a for a in (getattr(row, "aliases", None) or []) if a]
        if names:
            out[part] = names
    return out


def _proposed(project: Project, system_code: str | None) -> list[str]:
    """The Schedule of Material's part numbers, each once, in its order."""
    try:
        blocks = schedule_blocks(project, system_code)
    except Exception:  # noqa: BLE001 -- nothing is highlighted rather than the package failing
        return []
    out, seen = [], set()
    for _letter, _title, items in blocks:
        for item in items:
            part = (getattr(item, "catalog_no", None) or "").strip()
            key = re.sub(r"[^A-Z0-9]", "", part.upper())
            if key and key not in seen:
                seen.add(key)
                out.append(part)
    return out


def _by_block(project: Project, system_code: str | None, documents: list[PackageDocument]) -> list[PackageDocument]:
    """The datasheets in Schedule of Material order, each with its block
    (a sheet serving parts of two blocks goes with the first), and the
    schedule's part numbers to highlight on it. A sheet whose parts are on
    no block keeps its place after the rest, with no block."""
    try:
        blocks = schedule_blocks(project, system_code)
    except Exception:  # noqa: BLE001 -- the datasheets still go in, in BOQ order
        return documents
    first: dict[str, int] = {}
    proposed: list[str] = []
    for index, (_letter, _title, items) in enumerate(blocks):
        for item in items:
            part = (getattr(item, "catalog_no", None) or "").strip()
            key = re.sub(r"[^A-Z0-9]", "", part.upper())
            if key and key not in first:
                first[key] = index
                proposed.append(part)
    for document in documents:
        parts = document.covers or ([document.part_no] if document.part_no else [])
        found = [first[k] for k in (re.sub(r"[^A-Z0-9]", "", p.upper()) for p in parts) if k in first]
        if found and document.block is None:
            document.block = blocks[min(found)][1]
        if document.path:
            document.highlight = list(proposed)
    # the schedule's blocks in order, then the batteries, then what is on no block
    order = {title: index for index, (_l, title, _i) in enumerate(blocks)}
    order.setdefault(BATTERIES_BLOCK, len(order))
    return sorted(documents, key=lambda d: order.get(d.block, len(order)))


# --- building ---------------------------------------------------------------


def _rgb(value: int) -> tuple[float, float, float]:
    """0xccdbeb -> (0.80, 0.86, 0.92)."""
    return ((value >> 16 & 255) / 255, (value >> 8 & 255) / 255, (value & 255) / 255)


# The cover's own fonts (Century Gothic, Arial Narrow) are the company's, and
# are installed on the machines this runs on. Where they are not -- a test
# box, a Linux host -- the base-14 equivalents keep the page correct if not
# identical, rather than failing the build.
_FONT_FILES = {
    "gothic": r"C:\Windows\Fonts\GOTHIC.TTF",
    "gothicb": r"C:\Windows\Fonts\GOTHICB.TTF",
    "arialb": r"C:\Windows\Fonts\arialbd.ttf",
    "arialn": r"C:\Windows\Fonts\arialn.ttf",
    "arial": r"C:\Windows\Fonts\arial.ttf",
}
_FALLBACK = {"gothic": "helv", "gothicb": "hebo", "arialb": "hebo", "arialn": "helv", "arial": "helv"}

# The manufacturer a brand is made by, as the cover names it: Menvier is Eaton's.
_COVER_MAKERS = {"MENVIER": "EATON", "MENIVIER": "EATON"}


def _cover_maker(project: Project, code: str | None) -> tuple[str, str, str] | None:
    """(the manufacturer's name in place of the template's Edwards logo, the
    line under it, the discipline) for a system the template does not show;
    None for the fire alarm, whose cover the template is."""
    from sqlalchemy.orm import Session as _Session

    if code == "ELS":
        from app.routers.projects import _brand_for

        brand = (_brand_for("ELS", list(project.systems)) or "MENVIER").strip().upper()
        return _COVER_MAKERS.get(brand, brand), "Emergency Lighting System", "Electrical - Emergency Light System"
    if code == "FRC":
        from app.services import frc_cables

        session = _Session.object_session(project)
        row = frc_cables.get(session, project) if session is not None else None
        brands = [b for b in [row.brand if row else None, (frc_cables.monitoring_for(row, project) or (None,))[0]] if b]
        names = " & ".join(dict.fromkeys(b.strip().upper() for b in brands)) or "FIRE RATED CABLE"
        return names, "Fire Rated Cables", "Electrical - Fire Rated Cable"
    return None


def _font(page, name: str) -> tuple[str, str | None]:
    """(fontname, fontfile) for a cover field, falling back to a base font."""
    path = _FONT_FILES.get(name)
    if path and Path(path).is_file():
        try:
            page.insert_font(fontname=name, fontfile=path, set_simple=True)
            return name, path
        except Exception:  # noqa: BLE001
            pass
    return _FALLBACK.get(name, "helv"), None


def _replace(page, old: str, new: str, size: float, colour=(0, 0, 0), font: str = "gothicb") -> bool:
    """Swap one string on a template page, keeping its place and its look.

    Redacted with **no fill**. The project block is a navy box drawn under its
    text, and blanking the text with white punched a white hole through it --
    which is what made the replaced project name look wrong. `fill=False`
    removes the glyphs and leaves the artwork beneath untouched.

    The replacement is written in the colour and size the template used for
    that field, so the white-on-navy title stays white on navy.
    """
    boxes = page.search_for(old)
    if not boxes:
        return False
    for found in boxes:
        page.add_redact_annot(found, fill=False)
    try:
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    except TypeError:
        page.apply_redactions()

    fontname, fontfile = _font(page, font)
    # Shrink to fit rather than run over the edge of the box or the cell.
    width = pymupdf.get_text_length(new, fontname=_FALLBACK.get(font, "helv"), fontsize=size)
    room = max(boxes[0].width, 200)
    if width > room:
        size = max(6.0, size * room / width)

    # Every occurrence, not just the first: the template happens to name the
    # same company as Main Contractor and as MEP Contractor, and writing only
    # the first left the MEP cell blank on the issued cover.
    for found in boxes:
        # The template's own baseline, so the line sits where it did.
        page.insert_text((found.x0, found.y1 - found.height * 0.22), new,
                         fontname=fontname, fontfile=fontfile, fontsize=size, color=colour)
    return True


def _project_title(project: Project) -> str:
    return (project.project_name or f"EP-{project.ep_number}").strip()


def build_cover(library_root: Path, project: Project, revision: str, systems: str,
                system_code: str | None = None) -> pymupdf.Document | None:
    """The cover page, from the company's template.

    The template is the approved artwork -- logo, layout, the supplier block
    -- so it is opened and its project fields swapped, never redrawn.
    """
    template = _template(library_root, COVER_TEMPLATE)
    if not template.is_file():
        return None
    doc = pymupdf.open(template)
    page = doc[0]

    # Each field in the size, colour and font the template gave it. The
    # project name is white on the navy block; the two lines under it are the
    # paler blues that block uses; the parties are the company blue.
    plot = (project.plot_number or "").strip()
    location = ", ".join(part for part in [f"PLOT NO. {plot}" if plot else "", (project.location or "").strip()] if part)
    party = lambda value: (value or "").strip() or " "  # noqa: E731

    _replace(page, "Fire Alarm, Voice Evacuation & Fire Telephone System", systems, 13, _rgb(0x8C8C8E), "gothic")
    _replace(page, "SAMANA PARK MEADOWS (DLRC 4)", _project_title(project).upper(), 19, _rgb(0xFFFFFF), "gothicb")
    _replace(page, "PROPOSED 2B + G + 16 + R RESIDENTIAL BUILDING",
             (project.other_information or "").strip().upper() or " ", 11, _rgb(0xCCDBEB), "gothic")
    _replace(page, "PLOT NO. 648-8670, WADI AL SAFA 5, DLRC, DUBAI, U.A.E.",
             location.upper() or " ", 10, _rgb(0xA8BDD4), "gothic")
    _replace(page, "M/s. Samana IFS Holding Limited", party(project.client), 11, _rgb(0x0E4E89), "arialb")
    _replace(page, "M/s. Al Hilal Engineering Consultant", party(project.consultant), 11, _rgb(0x0E4E89), "arialb")
    _replace(page, "M/s. Italtech Contracting L.L.C", party(project.contractor), 11, _rgb(0x0E4E89), "arialb")
    _replace(page, "EP-30058", f"EP-{project.ep_number}", 9.5, _rgb(0x1F242B), "arialn")
    # Searched with its label's spacing so a bare "R0" elsewhere is not hit.
    _replace(page, "R0", revision, 9.5, _rgb(0x1F242B), "arialn")
    _replace(page, "06-09-2026", date.today().strftime("%d-%m-%Y"), 9.5, _rgb(0x1F242B), "arialn")

    # The system's own manufacturer and discipline: the template is the fire
    # alarm's (Edwards, EST4); the emergency lighting is Eaton's, the cables
    # the brands chosen (platform owner, 2 October 2026).
    from app.services.system_rules import canonical

    maker = _cover_maker(project, canonical(system_code))
    if maker is not None:
        name, line, discipline = maker
        label = next(iter(page.search_for("SYSTEM MANUFACTURER")), None)
        logo = next((pymupdf.Rect(info["bbox"]) for info in page.get_image_info()
                     if label is not None and abs(info["bbox"][0] - label.x0) < 30
                     and 0 < info["bbox"][1] - label.y1 < 40), None)
        if logo is not None:
            page.add_redact_annot(logo, fill=False)
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_REMOVE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                                  text=pymupdf.PDF_REDACT_TEXT_NONE)
            fontname, fontfile = _font(page, "gothicb")
            size = 18.0
            while size > 9 and pymupdf.get_text_length(name, fontname="hebo", fontsize=size) > 220:
                size -= 0.5
            page.insert_text((label.x0, logo.y1 - 6), name, fontname=fontname, fontfile=fontfile, fontsize=size,
                             color=_rgb(0x4D4D4F))
        _replace(page, "EST4 Life Safety Platform", line, 9, _rgb(0x8C8C8E), "arial")
        _replace(page, "Electrical - Fire Alarm & Life Safety", discipline, 9.5, _rgb(0x1F242B), "arialn")
    return doc


def build_index(library_root: Path, plan: PackagePlan, project: Project) -> pymupdf.Document:
    """The index page, listing the sections this package carries.

    Drawn rather than taken from the template, because the template's index
    lists all seventeen and this one lists what was chosen, numbered in
    order (`PackagePlan.shown_number`).
    """
    doc = pymupdf.open()
    page = doc.new_page(width=595.32, height=841.92)
    page.insert_text((44, 70), "PROJECT:", fontname="hebo", fontsize=9, color=(0.45, 0.45, 0.45))
    page.insert_text((44, 88), _project_title(project).upper()[:70], fontname="hebo", fontsize=13)
    page.insert_text((44, 130), "SUBMITTAL INDEX", fontname="hebo", fontsize=20, color=(0.75, 0.1, 0.15))

    top = 165
    page.draw_rect(pymupdf.Rect(44, top, 551, top + 24), color=None, fill=(0.75, 0.1, 0.15))
    page.insert_text((56, top + 16), "NO.", fontname="hebo", fontsize=9.5, color=(1, 1, 1))
    page.insert_text((100, top + 16), "DESCRIPTION", fontname="hebo", fontsize=9.5, color=(1, 1, 1))
    page.insert_text((420, top + 16), "STATUS", fontname="hebo", fontsize=9.5, color=(1, 1, 1))

    y = top + 24
    for section in plan.selected_sections:
        page.draw_rect(pymupdf.Rect(44, y, 551, y + 26), color=(0.85, 0.85, 0.85), width=0.5)
        page.insert_text((56, y + 17), f"{plan.shown_number(section):02d}", fontname="helv", fontsize=9.5)
        page.insert_text((100, y + 17), section.name[:58], fontname="helv", fontsize=9.5)
        status = "Enclosed" if section.found else "To be filled"
        page.insert_text((420, y + 17), status, fontname="helv", fontsize=9, color=(0.35, 0.35, 0.35))
        y += 26
    return doc


def _centre(page, bbox, text: str, size: float, colour, font: str = "hebo") -> None:
    """Replace a centred line, keeping it centred in the box it occupied."""
    page.add_redact_annot(pymupdf.Rect(bbox), fill=False)
    try:
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    except TypeError:
        page.apply_redactions()
    middle = (bbox[0] + bbox[2]) / 2
    while size > 5 and pymupdf.get_text_length(text, fontname=font, fontsize=size) > 470:
        size -= 0.5
    width = pymupdf.get_text_length(text, fontname=font, fontsize=size)
    # a line longer than the one it replaces is kept on the page
    page.insert_text((max(36.0, min(middle - width / 2, page.rect.width - 36 - width)), bbox[3] - (bbox[3] - bbox[1]) * 0.14), text,
                     fontname=font, fontsize=size, color=colour)


def build_divider(library_root: Path, number: int, project: Project, name: str | None = None) -> pymupdf.Document | None:
    """The section divider, on the company's divider artwork.

    The template holds one divider per section after its index page, found by
    the **name** printed on it -- not by its number, which the template fixed
    when the index had seventeen sections. Adding Battery Calculation moved
    every section after it down one, so a number match would now miss every
    one of them.

    Two things are therefore rewritten on the page: the big number, to the
    section's number in *this* index, and the project. A section the template
    has no divider for -- Battery Calculation -- borrows another's artwork
    and has its title rewritten too, so it looks like the rest of the set
    rather than like a page from somewhere else.
    """
    template = _template(library_root, INDEX_TEMPLATE)
    if not template.is_file():
        return None
    name = name or SECTION_NAMES[number]
    wanted = name.split("(")[0].strip().lower()

    with pymupdf.open(template) as source:
        pages = [i for i in range(len(source)) if "SUBMITTAL SECTION" in source[i].get_text()]
        if not pages:
            return None
        match = next((i for i in pages if wanted in source[i].get_text().lower()), None)
        borrowed = match is None
        divider = pymupdf.open()
        divider.insert_pdf(source, from_page=match if match is not None else pages[0],
                           to_page=match if match is not None else pages[0])

    page = divider[0]
    spans = [
        span
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
        if span["text"].strip()
    ]
    # The big pale number, and the section title under it.
    printed = max((s for s in spans if re.fullmatch(r"\d{1,2}", s["text"].strip())), key=lambda s: s["size"], default=None)
    title = next((s for s in spans if 15 < s["size"] < 40), None)

    if borrowed and title is not None:
        _centre(page, title["bbox"], name, title["size"], _rgb(title["color"]))
    if printed is not None and printed["text"].strip() != f"{number:02d}":
        _centre(page, printed["bbox"], f"{number:02d}", printed["size"], _rgb(printed["color"]))
    # The small "PAGE 07" the template prints under the number is the
    # template's numbering too, and was left saying 07 on section 08.
    for span in spans:
        label = span["text"].strip()
        if re.fullmatch(r"PAGE\s*\d{1,2}", label, re.IGNORECASE) and label.upper() != f"PAGE {number:02d}":
            _centre(page, span["bbox"], f"PAGE {number:02d}", span["size"], _rgb(span["color"]), font="helv")

    _replace(page, "IVY GARDEN 2 - 1B+G+5P+34+R RESIDENTIAL BUILDING", _project_title(project).upper()[:60], 11)
    return divider


def _blank(page, bbox) -> None:
    page.add_redact_annot(pymupdf.Rect(bbox), fill=False)
    try:
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    except TypeError:
        page.apply_redactions()


def build_block_divider(library_root: Path, project: Project, number: int, section: str, block: str) -> pymupdf.Document | None:
    """A divider inside the datasheet section, one per Schedule of Material
    block (the panel, the BPS, the APS ...): the section's divider artwork
    with the block's name for its title, and **no number** -- it divides the
    section, it is not a section of the index (platform owner, 1 October 2026)."""
    divider = build_divider(library_root, number, project, section)
    if divider is None:
        return None
    # A BOQ heading read with the sheet's project line before it
    # ("PROJECT : BINGHATTI TITANIA / Booster Power Supply") is the block's name after it.
    block = re.sub(r"^\s*PROJECT\s*:[^/]*/\s*", "", block, flags=re.IGNORECASE) or block
    page = divider[0]
    spans = [
        span
        for b in page.get_text("dict")["blocks"]
        for line in b.get("lines", [])
        for span in line["spans"]
        if span["text"].strip()
    ]
    wanted = section.split("(")[0].strip().lower()
    title = next((sp for sp in spans if sp["text"].strip().lower().startswith(wanted)), None) \
        or next((sp for sp in spans if 15 < sp["size"] < 40), None)
    for span in spans:
        text = span["text"].strip()
        if span is title:
            _centre(page, span["bbox"], block, span["size"], _rgb(span["color"]))
        elif re.fullmatch(r"\d{1,2}", text) or re.fullmatch(r"PAGE\s*\d{1,2}", text, re.IGNORECASE):
            _blank(page, span["bbox"])
        elif text.upper() == "SUBMITTAL SECTION":
            _centre(page, span["bbox"], section.upper(), span["size"], _rgb(span["color"]), font="helv")
    return divider


# What a datasheet's own highlights are: text markup someone added to the
# filed copy, for another project. Removed before the proposed parts are marked.
_MARKUP = {pymupdf.PDF_ANNOT_HIGHLIGHT, pymupdf.PDF_ANNOT_UNDERLINE, pymupdf.PDF_ANNOT_STRIKE_OUT,
           pymupdf.PDF_ANNOT_SQUIGGLY}
_EDGE = "()[]{},;:.'\"*"


def _part_keys(part: str) -> set[str]:
    """How a part may be printed: whole, and without its "/230" -- the APS
    sheet says APS6A where the BOQ quotes APS6A/230."""
    keys = {re.sub(r"[^A-Z0-9]", "", part.upper())}
    head = part.split("/")[0]
    if head != part and len(re.sub(r"[^A-Z0-9]", "", head.upper())) >= 4:
        keys.add(re.sub(r"[^A-Z0-9]", "", head.upper()))
    return {k for k in keys if k}


_ORDERING = re.compile(r"^\s*ordering\s+information\b", re.IGNORECASE)
_APPROVAL = re.compile(r"CIVIL\s+DEFEN[CS]E", re.IGNORECASE)
# The sections a civil defence certificate is filed in: Certifications,
# Previous Approvals, Others Documents (Certificates, Approvals Etc). The
# rest -- the company profile, the test reports -- are not read for one.
_CERTIFICATE_SECTION = re.compile(r"certif|approv|other", re.IGNORECASE)


def _text_lines(page, textpage=None) -> list[tuple[str, float, pymupdf.Rect]]:
    """(text, largest type size, box) of every line on the page."""
    out = []
    for block in page.get_text("dict", textpage=textpage)["blocks"]:
        for line in block.get("lines", []):
            spans = [span for span in line["spans"] if span["text"].strip()]
            if spans:
                out.append(("".join(span["text"] for span in line["spans"]).strip(),
                            max(span["size"] for span in spans), pymupdf.Rect(line["bbox"])))
    return out


def _ordering_regions(page, lines) -> list[pymupdf.Rect]:
    """The Ordering Information sections on a page: from the heading down to
    the next heading of its size in its column, else the foot of the page.
    A heading in the sheet's main column (right of the sidebar) keeps the
    section to that column."""
    width, height = page.rect.width, page.rect.height
    regions = []
    for text, size, box in lines:
        if not _ORDERING.match(text) or len(text) > 60:
            continue
        left = box.x0 - 12 if box.x0 > width * 0.25 else 0
        bottom = height
        for other, other_size, other_box in lines:
            if (other_box.y0 > box.y1 + 2 and other_box.y0 < bottom and abs(other_size - size) <= 1.5
                    and other_box.x0 >= left - 5 and not _ORDERING.match(other)):
                bottom = other_box.y0
        regions.append(pymupdf.Rect(left, box.y0 - 2, width, bottom))
    return regions


def _title_boxes(page, lines) -> list[pymupdf.Rect]:
    """The datasheet's title on its first page: the large lines in its top
    half ("EST4 LCD Display Module") and the series line under them ("4-LCD
    Series") -- every line at least about half the size of the largest."""
    lines = [line for line in lines if line[2].y0 < page.rect.height * 0.5]
    largest = max((size for _t, size, _b in lines), default=0)
    if largest < 20:
        return []
    return [box for _t, size, box in lines if size >= largest * 0.45]


def _loose(key: str) -> str:
    """A key as a scanned or retyped sheet may print it: O and 0 alike."""
    return key.replace("O", "0")


def _spellings(part: str, aliases: dict[str, list[str]] | None, loose: bool) -> set[str]:
    """Every key a part may be printed under: its own, the equipment
    table's aliases, and -- read loosely -- without the "-M" brand suffix
    (CTR400CGL2KS-M is printed CTR400CGL2KS) and with an "IPM" order code's
    M off (RT2RHEO200CGL3HIPM is printed RT2RHE0200CGL3HIP)."""
    if "+" in part:
        # a body with its accessories ("SL2-42D3D-CGL-M+SL23I"): each piece
        # is printed on its own
        return set().union(*(_spellings(piece.strip(), aliases, loose) for piece in part.split("+") if piece.strip()))
    keys = set(_part_keys(part))
    for alias in (aliases or {}).get(part, []):
        keys |= _part_keys(alias)
    if loose:
        if part.strip().upper().endswith("-M"):
            keys |= _part_keys(part.strip()[:-2])
        keys |= {k[:-1] for k in keys if k.endswith("IPM")}
        keys = {_loose(k) for k in keys}
    return {k for k in keys if len(k) >= 4}


def _wanted(parts: list[str], aliases: dict[str, list[str]] | None = None, loose: bool = False) -> dict[str, list[str]]:
    """{printed key: the proposed parts printed under it} -- one key can be
    two parts' (the same luminaire body under two exit signs)."""
    wanted: dict[str, list[str]] = {}
    for part in parts:
        for key in _spellings(part, aliases, loose):
            wanted.setdefault(key, [])
            if part not in wanted[key]:
                wanted[key].append(part)
    return wanted


def _first(words) -> list:
    """The words that open their line -- a table row's order code, the
    description following it on the same line."""
    seen: set[tuple[int, int]] = set()
    out = []
    for w in words:
        if (w[5], w[6]) not in seen:
            seen.add((w[5], w[6]))
            out.append(w)
    return out


def _word_key(word: str, loose: bool = False) -> str:
    key = re.sub(r"[^A-Z0-9]", "", word.strip(_EDGE).upper())
    return _loose(key) if loose else key


def _clear(page) -> None:
    for annot in list(page.annots() or []):
        if annot.type[0] in _MARKUP:
            page.delete_annot(annot)


def _inside(words, box: pymupdf.Rect) -> list:
    """The words whose middle lies in the box."""
    return [w for w in words if box.contains(pymupdf.Point((w[0] + w[2]) / 2, (w[1] + w[3]) / 2))]


def _alone(words) -> list:
    """The words that are their line's only word -- a table cell's part
    number, not one a sentence mentions."""
    per_line: dict[tuple[int, int], int] = {}
    for w in words:
        per_line[(w[5], w[6])] = per_line.get((w[5], w[6]), 0) + 1
    return [w for w in words if per_line[(w[5], w[6])] == 1]


def highlight_proposed(doc: pymupdf.Document, parts: list[str], own: list[str], *,
                       aliases: dict[str, list[str]] | None = None, marking: str = "titled") -> list[str]:
    """A datasheet as the package carries it: every highlight it was filed
    with removed, then two things marked (platform owner, 2 October 2026) --
    the sheet's title on its first page, and the proposed part numbers in
    its Ordering Information table, nowhere else. A sheet with no Ordering
    Information section has its proposed part numbers marked where they
    stand alone on a line (a table cell) instead. Returns the sheet's own
    parts (`own`) marked nowhere, for the package to say so. The document is
    the in-memory copy: the library's file is never written.

    `marking` "parts" (the emergency lighting): no title, and the proposed
    order codes marked in whatever table lists them, read loosely and under
    their aliases (`_spellings`).

    Each page's text is extracted once and every look at it reads that:
    a package of forty sheets is otherwise minutes of the same extraction."""
    loose = marking == "parts"
    titles = marking == "titled"
    wanted = _wanted(parts, aliases, loose)
    hit: set[str] = set()
    titled: set[str] = set()
    pages = []                                   # (page, its words, its Ordering Information regions)
    for index, page in enumerate(doc):
        _clear(page)
        textpage = page.get_textpage()
        words = page.get_text("words", textpage=textpage)
        plain = textpage.extractText()
        ordering = titles and "rdering" in plain
        lines = _text_lines(page, textpage) if (titles and index == 0) or ordering else []
        if titles and index == 0:
            for box in _title_boxes(page, lines):
                page.add_highlight_annot(box)
                inside = _inside(words, box)
                titled.update(_word_key(w[4]) for w in inside)
                # the title as one run too: "ES 65-12" is ES65-12
                titled.add(_word_key("".join(w[4] for w in inside)))
        pages.append((page, words, _ordering_regions(page, lines) if ordering else []))
    sections = any(regions for _p, _w, regions in pages)
    for page, words, regions in pages:
        if sections:
            # the Model # column: a part number that is its cell's only word,
            # not one the description beside it mentions
            candidates = [w for region in regions for w in _alone(_inside(words, region))]
        elif loose:
            # a table's order code: its cell's only word, or its row's first
            candidates = list({id(w): w for w in [*_alone(words), *_first(words)]}.values())
        else:
            candidates = _alone(words)
        for x0, y0, x1, y1, word, *_rest in candidates:
            key = _word_key(word, loose)
            if key in wanted:
                page.add_highlight_annot(pymupdf.Rect(x0, y0, x1, y1))
                hit.update(wanted[key])
    # the sheet's own parts marked nowhere -- not in its table, not in its title
    proposed = {part for named in wanted.values() for part in named}
    return [part for part in own
            if part not in hit and part in proposed
            and not any(k in t for k in _spellings(part, aliases, loose) for t in titled)]


def highlight_approvals(doc: pymupdf.Document, parts: list[str], *,
                        aliases: dict[str, list[str]] | None = None, marking: str = "titled") -> int:
    """The civil defence approval certificates in a document: on each page
    of one, the highlights it was filed with removed and the proposed part
    numbers in its models list marked. Returns how many pages were such
    certificates (0: the document is left as filed)."""
    loose = marking == "parts"
    wanted = _wanted(parts, aliases, loose)
    pages = 0
    for page in doc:
        textpage = page.get_textpage()
        if not _APPROVAL.search(textpage.extractText()):
            continue
        pages += 1
        _clear(page)
        for x0, y0, x1, y1, word, *_rest in page.get_text("words", textpage=textpage):
            # the certificates are scans read back to text: "BPSl0A" is BPS10A
            misread = re.sub(r"(?<=[A-Z0-9])l(?=[0-9A-Z])", "1", word)
            if _word_key(word, loose) in wanted or _word_key(misread, loose) in wanted:
                page.add_highlight_annot(pymupdf.Rect(x0, y0, x1, y1))
    return pages


# What the BOQ's ungrouped lines are: the detectors, sounders, call points
# and modules that hang off the panels rather than sitting inside one. The
# design sheets give them a block of their own, so the schedule does too.
UNGROUPED_BLOCK = "Field Devices"

_RED = (0.75, 0.1, 0.15)


ADDED_BLOCK = "Proposed materials (added beyond the BOQ)"

# The field-device blocks of a Schedule of Material, in the engineers' order.
INITIATING_BLOCK = "Initiating Devices"
NOTIFICATION_BLOCK = "Notification Appliances"
TELEPHONE_BLOCK = "Fire Telephone"
BMS_BLOCK = "BMS Gateway"
MODULES_BLOCK = "Modules"
BACK_BOXES_BLOCK = "Back Boxes"
# Parts scheduled with no datasheet of their own in the package: the
# weatherproof back box goes in with its speaker/strobe (platform owner,
# 1 October 2026). Keys as part numbers compare (letters and digits).
NO_DATASHEET = {"757AWB"}
OTHER_FIELD_BLOCK = "Other Field Devices"
FIELD_BLOCKS = (INITIATING_BLOCK, NOTIFICATION_BLOCK, TELEPHONE_BLOCK, BMS_BLOCK, MODULES_BLOCK, BACK_BOXES_BLOCK, OTHER_FIELD_BLOCK)

# The blocks of a monitored self-contained emergency light system's schedule.
ELS_PANEL_BLOCK = "Emergency Light Panel"
ELS_LIGHT_BLOCK = "Emergency Light"
ELS_EXIT_BLOCK = "Exit Light"
ELS_BLOCKS = (ELS_PANEL_BLOCK, ELS_LIGHT_BLOCK, ELS_EXIT_BLOCK)
FRC_BLOCK = "Fire Rated Cables"
_ELS_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (ELS_PANEL_BLOCK, ("CTR",), ("controller", "panel", "web compact", "monitoring unit", "gateway")),
    (ELS_EXIT_BLOCK, (), ("exit",)),
)


def els_category(item) -> str:
    """Which block of the emergency lighting schedule a line belongs to:
    the controllers, the exit signs, else the luminaires."""
    key = re.sub(r"[^A-Z0-9]", "", (item.catalog_no or "").upper())
    text = (item.description or "").lower()
    for block, prefixes, _words in _ELS_RULES:
        if key and any(key.startswith(prefix) for prefix in prefixes):
            return block
    for block, _prefixes, words in _ELS_RULES:
        if any(word in text for word in words):
            return block
    return ELS_LIGHT_BLOCK

# (block, part-number prefixes, description words) -- the part number first, the wording when it has none.
_FIELD_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (BMS_BLOCK, ("FSB",), ("bms", "gateway", "communication bridge", "field server")),
    (BACK_BOXES_BLOCK, ("TP434", "TP606", "27193", "GRSW", "757AWB"), ("back box", "backbox", "surface mount box", "electrical box", "wiring plate", "weatherproof box")),
    (MODULES_BLOCK, ("SIGACT", "SIGACC", "SIGACR", "SIGAUM", "SIGAIO", "SIGAMCT", "SIGAMCR", "SIGAMM", "SIGAREL", "SIGARM", "SIGAUIO", "SIGAMAB"), ("module", "relay")),
    (TELEPHONE_BLOCK, ("6830", "6833", "TCS"), ("telephone", "handset")),
    (NOTIFICATION_BLOCK, ("G1", "G4", "GC", "757", "202", "WSTIA", "ESTS186", "SIGALED"), ("horn", "strobe", "speaker", "sounder", "bell", "remote alarm led", "beacon")),
    (INITIATING_BLOCK, ("SIGAOSD", "SIGAHRD", "SIGAOSHD", "SIGAPS", "SIGAHFS", "SIGASB", "SIGAIB", "SIGALPS", "SIGA278", "SIGASD", "SDT", "STI", "EC3000", "SIGACO", "SIGAPHS"),
     ("detector", "base", "pull station", "call point", "beam", "duct", "sampling", "stopper", "gasket", "heat", "smoke")),
)


def field_category(item) -> str:
    """Which field-device block a BOQ line belongs to (FIELD_BLOCKS), by
    its part number, else by its wording, else Other Field Devices."""
    key = re.sub(r"[^A-Z0-9]", "", (item.catalog_no or "").upper())
    text = (item.description or "").lower()
    for block, prefixes, _words in _FIELD_RULES:
        if key and any(key.startswith(prefix) for prefix in prefixes):
            return block
    for block, _prefixes, words in _FIELD_RULES:
        if any(word in text for word in words):
            return block
    return OTHER_FIELD_BLOCK


def schedule_blocks(project: Project, system_code: str | None = None) -> list[tuple[str, str, list]]:
    """The BOQ as the design sheet lays it out: a lettered block per assembly.

    A flat run of every line in sequence is not how the engineers read a
    schedule -- the design sheet gives each assembly its own block (the main
    panel, the second panel, an amplifier cabinet, a booster power supply)
    and lists that assembly's parts under it. The BOQ already carries the
    grouping, because extraction kept each sheet's headings, so the blocks
    are its `group_heading`s in BOQ order.

    Returns (letter, title, lines). The title is the group heading -- "EST4
    Main Fire Alarm Control Panel", "Booster Power Supply" -- and never the
    group's own heading line, the one with no part number that spells the
    assembly out ("EST4 fire alarm control panel complete with power
    supply/charger, sealed lead acid..."). That line is a description of the
    assembly, not a name for it: using it made the main panel and the second
    panel read as the same block. It is left out of the parts as well, being
    the heading rather than one of them.
    """
    from app.services.system_rules import effective_code

    wanted = effective_code(system_code, project)
    order: list[str] = []
    grouped: dict[str, list] = {}
    for item in project.boq_items:
        if wanted and effective_code(item.system_code, project) != wanted:
            continue
        key = (item.group_heading or "").strip() or UNGROUPED_BLOCK
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(item)

    # The materials proposed on the Proposed Materials tab beyond the BOQ,
    # under the same system: the schedule is what is proposed for approval,
    # so they are on it, as a block of their own after the BOQ's.
    from sqlalchemy.orm import Session as _Session

    from app.models import ProjectProposedMaterial

    session = _Session.object_session(project)
    added = []
    if session is not None:
        for row in session.query(ProjectProposedMaterial).filter(ProjectProposedMaterial.project_id == project.id).order_by(ProjectProposedMaterial.id):
            if wanted and effective_code(row.system_code, project) != wanted:
                continue
            added.append(row)
    # The engineers' order, whatever the sheet's: the panel and its
    # equipment first, then the repeater panels, then the APS and BPS
    # cabinets -- the BOQ's own order within each -- then the field devices
    # by kind: initiating devices, notification appliances, fire telephone,
    # BMS gateway, modules, back boxes (FIELD_BLOCKS), and the materials
    # added on the tab at the end. The sheet's own field-device headings
    # ("Field Devices", "Super Duct") are replaced by those kinds.
    from app.services.battery_calculation import classify_group

    rank = {"panel": 0, "repeater": 1, "aps": 2, "bps": 3}
    cabinets = [key for key in order if classify_group(None if key == UNGROUPED_BLOCK else key) in rank]
    cabinets.sort(key=lambda key: rank[classify_group(None if key == UNGROUPED_BLOCK else key)])
    field: dict[str, list] = {}
    if wanted == "FRC":
        # The fire-rated cables the engineer chose, one block.
        from app.services import frc_cables

        cables = frc_cables.lines(session, project) if session is not None else []
        order, grouped = [], {}
        if cables:
            order.append(FRC_BLOCK)
            grouped[FRC_BLOCK] = cables
        if added:
            order.append(ADDED_BLOCK)
            grouped[ADDED_BLOCK] = added
        return _lettered(order, grouped)
    if wanted == "ELS":
        # A monitored self-contained emergency light system: the panel
        # (controllers), the emergency lights, the exit lights.
        lit: dict[str, list] = {}
        for key in order:
            for item in grouped[key]:
                if (item.catalog_no or "").strip():
                    lit.setdefault(els_category(item), []).append(item)
        order = [name for name in ELS_BLOCKS if name in lit]
        grouped = dict(lit)
        if added:
            order.append(ADDED_BLOCK)
            grouped[ADDED_BLOCK] = added
        return _lettered(order, grouped)
    if wanted != "FAS":
        # The fire alarm's kinds do not apply; another system keeps the
        # sheet's own blocks, cabinets first.
        order = cabinets + [key for key in order if key not in cabinets]
        if added:
            order.append(ADDED_BLOCK)
            grouped[ADDED_BLOCK] = added
        return _lettered(order, grouped)
    for key in list(order):
        block_items = grouped[key]
        if key in cabinets:
            # A BMS gateway quoted with the panel is still the gateway's block.
            grouped[key] = [i for i in block_items if field_category(i) != BMS_BLOCK]
            for item in block_items:
                if field_category(item) == BMS_BLOCK:
                    field.setdefault(BMS_BLOCK, []).append(item)
            continue
        for item in block_items:
            if not (item.catalog_no or "").strip():
                continue   # the heading line of a field block names nothing to schedule
            field.setdefault(field_category(item), []).append(item)
    order = cabinets + [name for name in FIELD_BLOCKS if name in field]
    grouped.update(field)
    # The batteries the calculation selects take the place, in each
    # cabinet's block, of the battery the BOQ quoted by capacity: panel
    # one's "12V65A" is scheduled as ES65-12.
    if session is not None:
        from app.services import battery_materials

        batteries = battery_materials.selected_batteries(session, project, per_panel=True)
        if batteries:
            for key in cabinets:
                chosen = [b for b in batteries if key in b.headings]
                if not chosen:
                    continue
                kept = [i for i in grouped[key] if not battery_materials.is_battery_line(i)]
                merged: dict[str, battery_materials.SelectedBattery] = {}
                for battery in chosen:
                    entry = merged.get(battery.catalog_no.upper())
                    if entry is None:
                        merged[battery.catalog_no.upper()] = dataclasses.replace(battery, panels=list(battery.panels), headings=[key])
                    else:
                        entry.quantity += battery.quantity
                        entry.panels += [p for p in battery.panels if p not in entry.panels]
                grouped[key] = kept + list(merged.values())
    if added:
        order.append(ADDED_BLOCK)
        grouped[ADDED_BLOCK] = added
    return _lettered(order, grouped)


def _lettered(order: list[str], grouped: dict[str, list]) -> list[tuple[str, str, list]]:
    blocks: list[tuple[str, str, list]] = []
    for index, key in enumerate(order):
        items = grouped[key]
        if not items:
            continue
        # The heading line describes the assembly; it is not one of its parts.
        parts = [i for i in items if (i.catalog_no or "").strip()]
        letter = chr(ord("A") + len(blocks)) if len(blocks) < 26 else f"A{len(blocks)}"
        blocks.append((letter, key, parts or items))
    return blocks


def build_schedule(project: Project, system_code: str | None = None) -> pymupdf.Document:
    """The Schedule of Material, one block per assembly (see schedule_blocks).

    **No quantity or unit column**, on every project. The schedule says what
    material is proposed for approval; how much of it the project buys is the
    BOQ's business and changes after the submittal has been approved. Putting
    it here invites the consultant to review a number that the document is
    not the record of.
    """
    doc = pymupdf.open()
    page = doc.new_page(width=841.92, height=595.32)  # landscape
    columns = [("SL.", 42), ("CAT. NO.", 82), ("DESCRIPTION", 200), ("MANUFACTURER", 640)]
    left, right = 36, 806

    def header(first: bool) -> float:
        nonlocal page
        if not first:
            page = doc.new_page(width=841.92, height=595.32)
        page.insert_text((40, 50), "SCHEDULE OF MATERIAL", fontname="hebo", fontsize=16, color=_RED)
        page.insert_text((40, 68), _project_title(project).upper()[:90], fontname="helv", fontsize=9, color=(0.4, 0.4, 0.4))
        if system_code:
            page.insert_text((40, 82), system_code, fontname="hebo", fontsize=8.5, color=(0.45, 0.45, 0.45))
        y = 94
        page.draw_rect(pymupdf.Rect(left, y, right, y + 20), color=None, fill=_RED)
        for label, x in columns:
            page.insert_text((x, y + 14), label, fontname="hebo", fontsize=8.5, color=(1, 1, 1))
        return y + 20

    y = header(first=True)

    def room(needed: float) -> None:
        nonlocal y
        if y + needed > 552:
            y = header(first=False)

    for letter, title, items in schedule_blocks(project, system_code):
        # Keep a block's heading with at least its first line.
        room(46)
        page.draw_rect(pymupdf.Rect(left, y, right, y + 22), color=None, fill=(0.93, 0.94, 0.96))
        page.insert_text((42, y + 15), letter, fontname="hebo", fontsize=9.5, color=_RED)
        page.insert_text((62, y + 15), title.upper()[:96], fontname="hebo", fontsize=9, color=(0.06, 0.12, 0.21))
        # How many line items the block lists -- not a quantity of anything.
        count = len(items)
        label = f"{count} item{'' if count == 1 else 's'}"
        width = pymupdf.get_text_length(label, fontname="helv", fontsize=7.5)
        page.insert_text((right - 8 - width, y + 15), label,
                         fontname="helv", fontsize=7.5, color=(0.45, 0.45, 0.45))
        y += 22

        for number, item in enumerate(items, 1):
            room(20)
            page.draw_rect(pymupdf.Rect(left, y, right, y + 18), color=(0.87, 0.87, 0.87), width=0.4)
            cells = [
                (f"{letter}{number}", 42, 36),
                ((item.catalog_no or "-"), 82, 114),
                ((item.description or "")[:104], 200, 436),
                ((item.manufacturer or "-")[:24], 640, 160),
            ]
            for text, x, width in cells:
                # The whole part number, never cut ("SL2-42D3D-CGL-M+SL23I"
                # is not "SL2-42D3D-CGL-M+SL"): a long one is set smaller to
                # fit its column.
                size = 7.5
                while size > 4.5 and pymupdf.get_text_length(text, fontname="helv", fontsize=size) > width:
                    size -= 0.25
                page.insert_text((x, y + 12), text, fontname="helv", fontsize=size)
            y += 18
        y += 8   # air between blocks, as the design sheet has
    from app.services.system_rules import canonical

    if canonical(system_code) == "FRC":
        # The cable sizes stand on the route lengths, which the shop drawings
        # settle (platform owner, 2 October 2026).
        room(30)
        page.insert_text((left + 6, y + 14), "NOTE: The voltage drop calculation will be submitted after the shop "
                         "drawings approval.", fontname="hebo", fontsize=8.5, color=_RED)
    return doc


def _number_pages(out: pymupdf.Document) -> None:
    """Continuous page numbers, bottom right, skipping the cover.

    Right-aligned by measuring the string: a fixed offset runs off the edge of
    a landscape page and clips the last digit.
    """
    total = out.page_count
    for index in range(1, total):
        page = out[index]
        text = f"Page {index + 1} of {total}"
        width = pymupdf.get_text_length(text, fontname="helv", fontsize=7.5)
        page.insert_text((page.rect.width - 40 - width, page.rect.height - 16), text,
                         fontname="helv", fontsize=7.5, color=(0.42, 0.42, 0.42))


def _battery_sheet(project: Project, panels, systems: str) -> pymupdf.Document:
    """The battery calculation, on the company's own sheet.

    The same document the Battery page exports, so the copy in the submittal
    and the copy sent separately are the one calculation.
    """
    from app.services.battery_pdf import battery_calculation_pdf, panel_manufacturer

    panels = list(panels or [])
    data = battery_calculation_pdf(
        project, panels, systems=systems.upper(),
        manufacturers={p.key: panel_manufacturer(project, p) for p in panels},
    )
    return pymupdf.open(stream=data, filetype="pdf")


@dataclass
class BuiltPackage:
    pdf: bytes
    manifest: list[tuple[str, str, int, int]]   # section, document, first page, last page
    warnings: list[str]
    pages: int


class PackageBuildError(RuntimeError):
    """A package that could not be assembled, naming the stage that failed.

    "The package could not be built" told the engineer nothing about which
    of forty documents to look at. The stage -- a section's generated page,
    a template, the final write -- is what makes the failure actionable.
    """


def build_package(
    project: Project,
    plan: PackagePlan,
    library_root: Path | None,
    revision: str = "R0",
    systems: str = "Fire Alarm System",
    system_code: str | None = None,
    battery_panels=None,
) -> BuiltPackage:
    """Merge the package in index order and return it as bytes."""
    out = pymupdf.open()
    manifest: list[tuple[str, str, int, int]] = []
    warnings: list[str] = list(plan.warnings)

    def append(label: str, name: str, source: pymupdf.Document) -> None:
        start = out.page_count + 1
        out.insert_pdf(source)
        manifest.append((label, name, start, out.page_count))

    def attempt(stage: str, produce):
        """Run one stage of the build; a failure names the stage."""
        try:
            return produce()
        except PackageBuildError:
            raise
        except Exception as exc:  # noqa: BLE001 -- pymupdf raises bare exceptions
            raise PackageBuildError(f"{stage} could not be produced ({exc})") from exc

    if library_root is not None and library_root.is_dir():
        cover = attempt("The cover page", lambda: build_cover(library_root, project, revision, systems, system_code))
        if cover is not None:
            append("Cover", COVER_TEMPLATE, cover)
            cover.close()
        else:
            warnings.append("The cover template was not found in the submittal builder; the package starts at the index.")

    index = attempt("The index page", lambda: build_index(library_root or Path("."), plan, project))
    append("Index", "index", index)
    index.close()

    for section in plan.selected_sections:
        shown = plan.shown_number(section)
        label = f"{shown:02d} {section.name}"
        if library_root is not None and library_root.is_dir():
            divider = attempt(f"The divider for {label}", lambda: build_divider(library_root, shown, project, section.name))
            if divider is not None:
                append(f"{label} -- divider", "divider", divider)
                divider.close()

        # The sections the platform draws rather than merges.
        generated = any(d.source == "generated" for d in section.documents)
        # A plan made by hand (without `producer`) is the fire alarm's index.
        producer = section.producer or {FA_INDEX.schedule: "schedule", FA_INDEX.battery: "battery",
                                        FA_INDEX.coo: "coo", FA_INDEX.warranty: "warranty"}.get(section.number)
        if generated and producer:
            builder = {
                "schedule": lambda: build_schedule(project, system_code),
                "battery": lambda: _battery_sheet(project, battery_panels, systems),
                "coo": lambda: build_country_of_origin(project, library_root, system_code, plan.brand),
                "warranty": lambda: build_warranty(project, library_root, system_code),
            }[producer]
            page = attempt(f"{label} (generated)", builder)
            append(label, section.name, page)
            page.close()
            continue

        divided: set[str] = set()
        for document in section.documents:
            if not document.path:
                warnings.append(f"{label}: {document.name} -- {document.missing_reason or 'not found'}")
                continue
            if document.block and document.block not in divided and library_root is not None and library_root.is_dir():
                divided.add(document.block)
                block = attempt(f"The divider for {document.block}",
                                lambda: build_block_divider(library_root, project, section.number, section.name, document.block))
                if block is not None:
                    append(f"{label} -- {document.block}", "divider", block)
                    block.close()
            try:
                with pymupdf.open(document.path) as source:
                    if document.highlight is not None:
                        own = document.covers or ([document.part_no] if document.part_no else [])
                        where = "printed on it" if plan.marking == "parts" else "in its Ordering Information"
                        for part in highlight_proposed(source, document.highlight, own,
                                                       aliases=plan.aliases, marking=plan.marking):
                            warnings.append(f"{label}: {document.name} -- {part} is not {where} to highlight.")
                    elif plan.proposed and _CERTIFICATE_SECTION.search(section.name):
                        # a civil defence certificate: the proposed models marked on it
                        highlight_approvals(source, plan.proposed, aliases=plan.aliases, marking=plan.marking)
                    append(label, document.name, source)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{label}: {document.name} could not be read ({exc}).")
        if section.note:
            warnings.append(f"{label}: {section.note}")

    _number_pages(out)
    out.set_metadata({
        "title": f"EP-{project.ep_number} - {_project_title(project)} - Material Submittal - {revision}",
        "author": "Al Arabia for Safety & Security L.L.C",
        "subject": f"Material Submittal - {systems}",
        "creator": "Engineering Project Platform",
    })
    # garbage=1: the same file as 3 here (each document goes in once), in a fifth of the time
    pdf = attempt("The finished package", lambda: out.tobytes(deflate=True, garbage=1))
    pages = out.page_count
    out.close()
    return BuiltPackage(pdf=pdf, manifest=manifest, warnings=warnings, pages=pages)


# --- reading a filled-in checklist -----------------------------------------

# The company's Material Submittal Checklist is a table: one numbered row per
# index section, and a tick in one of three columns. The tick is a character
# with a position, not a value in a field, so which column it is in is decided
# by its x against the column headings, and which row by its y against the
# row numbers. Reading it by text alone cannot work -- every row's text is the
# same tick.
_TICKS = "\u2713\u2714\u2612\u00d7xX"
CHECKLIST_COLUMNS = ("yes", "no", "na")


def read_checklist(data: bytes) -> tuple[dict[int, str], list[str]]:
    """Which sections a filled-in checklist marks Yes / No / N/A.

    Returns the answers by section number, and what could not be read. A row
    with no tick is left out rather than assumed, because "not ticked" on a
    checklist is not the same as "not included" -- it is not filled in.
    """
    warnings: list[str] = []
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            if not len(doc):
                return {}, ["The checklist has no pages."]
            page = doc[0]
            words = page.get_text("words")
    except Exception as exc:  # noqa: BLE001
        return {}, [f"The checklist could not be read ({exc})."]

    headers: dict[str, float] = {}
    for x0, _y0, x1, _y1, text, *_ in words:
        key = text.strip().lower().replace(".", "")
        if key in ("yes", "no", "n/a", "na") and key not in headers:
            headers["na" if key in ("n/a", "na") else key] = (x0 + x1) / 2
    if "yes" not in headers:
        return {}, ["This does not look like the material submittal checklist: no Yes/No/N/A columns."]

    # The row numbers down the left edge give each section's y.
    rows: dict[int, float] = {}
    left = min(x0 for x0, *_ in words) if words else 0
    for x0, y0, _x1, y1, text, *_ in words:
        text = text.strip()
        if text.isdigit() and x0 < left + 120:
            number = int(text)
            if number in SECTION_NAMES and number not in rows:
                rows[number] = (y0 + y1) / 2
    if not rows:
        return {}, ["No numbered rows were found on the checklist."]

    answers: dict[int, str] = {}
    for x0, y0, x1, y1, text, *_ in words:
        if text.strip() not in _TICKS:
            continue
        tick_x, tick_y = (x0 + x1) / 2, (y0 + y1) / 2
        number = min(rows, key=lambda n: abs(rows[n] - tick_y))
        if abs(rows[number] - tick_y) > 12:
            continue  # not on any row
        column = min(headers, key=lambda c: abs(headers[c] - tick_x))
        if abs(headers[column] - tick_x) > 30:
            continue  # not in any column
        answers[number] = column

    for number, _name in SECTIONS:
        if number not in answers:
            warnings.append(f"Section {number:02d} {SECTION_NAMES[number]} is not ticked on the checklist.")
    return answers, warnings


# --- Country of Origin and the warranty certificate -------------------------
#
# Both sections have a template in the submittal builder that is not a PDF --
# COO.xlsx and Draft Warranty.docx -- so neither could be merged as it stood.
# They are produced here instead, from those same templates, so the company's
# own wording and its own country data stay the authority, and the page is
# built the way the Schedule of Material is.

COO_SECTION = 15
WARRANTY_SECTION = 16

FA_INDEX = PackageIndex(sections=tuple(SECTIONS), folders=LIBRARY_FOLDERS, spec=SPEC_SECTION, schedule=SCHEDULE_SECTION,
                        battery=BATTERY_SECTION, datasheet=DATASHEET_SECTION, coo=COO_SECTION, warranty=WARRANTY_SECTION)
FRC_INDEX = PackageIndex(sections=tuple(FRC_SECTIONS), folders=FRC_LIBRARY_FOLDERS, schedule=5, datasheet=6, warranty=11,
                         library_datasheets=True)

COO_TEMPLATE = "Country Of Origin/COO.xlsx"
WARRANTY_TEMPLATE = "templates/Draft Warranty.docx"

# The standard warranty the company gives. The draft in the builder still
# says TWO YEARS, which is not the standard any more; the period is stated
# here so every project gets the same one.
WARRANTY_YEARS = 1
_YEAR_WORDS = {1: "ONE YEAR", 2: "TWO YEARS", 3: "THREE YEARS", 5: "FIVE YEARS"}


def read_origin_rows(library_root: Path | None, brand: str | None = None) -> list[tuple[str, str, str, str]]:
    """The rows of the company's country-of-origin sheet: (model,
    description, made in, shipped from), header and blanks left out. The
    sheet is the manufacturer's: under the brand's folder of the submittal
    builder, else COMMON, else the older layout."""
    if library_root is None:
        return []
    from app.services import company_library

    template = company_library.submittal_path(library_root, brand, COO_TEMPLATE) or library_root / COO_TEMPLATE
    if not template.is_file():
        return []
    try:
        import openpyxl
        sheet = openpyxl.load_workbook(template, data_only=True).worksheets[0]
    except Exception:  # noqa: BLE001
        return []
    rows: list[tuple[str, str, str, str]] = []
    for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row):
        cells = [c.value for c in row]
        if len(cells) < 6:
            continue
        model, description, made_in, shipped = cells[1], cells[2], cells[4], cells[5]
        if not model or not (made_in or shipped):
            continue
        if str(made_in).strip().upper() == "MADE IN":
            continue  # the header row
        rows.append((str(model), str(description or ""), str(made_in or "").strip(), str(shipped or "").strip()))
    return rows


def read_origins(library_root: Path | None, brand: str | None = None) -> dict[str, tuple[str, str]]:
    """Where each model is made and shipped from, out of the COO template.
    The country of origin of a part is a fact about the part, not about the
    project, so the company's filled-in sheet is read as the reference for
    every project. Nothing is inferred: a model the sheet does not list comes
    back blank for an engineer to complete, because inventing a country on a
    customs declaration is not something software should do.
    """
    origins: dict[str, tuple[str, str]] = {}
    for model, description, made_in, shipped in read_origin_rows(library_root, brand):
        where = (made_in, shipped)
        model_text = model.strip().upper()
        # The model as written is a key before it is split: "APS6A/230" is
        # the one part number the BOQ quotes, as well as the pair a slash
        # would make of it. And a model written with a wildcard digit --
        # "757-XA-SS70" covers 757-3A-SS70 and 757-7A-SS70 -- is every
        # number it stands for.
        keys = [re.sub(r"[^A-Z0-9]", "", model_text)]
        if re.search(r"-X[A-Z]?-", model_text):
            keys += [re.sub(r"[^A-Z0-9]", "", model_text.replace("X", digit, 1)) for digit in "0123456789"]
        keys += [re.sub(r"[^A-Z0-9]", "", part.upper()) for part in re.split(r"[\n,/]+", model)]
        # A row can cover a whole set rather than one model: "PANEL
        # ACCESSORIES" declares one origin for the parts named in its
        # description. Those are the part numbers a BOQ actually quotes, so
        # without reading them the panel's own modules all come back blank.
        if description:
            keys += [
                re.sub(r"[^A-Z0-9]", "", token.upper())
                for token in re.split(r"[,\n]+", description)
                # A catalogue number, not prose: short, carrying a digit, and
                # made only of the characters a part number uses. Spaces are
                # allowed because the sheet wraps them ("4- FWAL4", "4-NET- TP")
                # and the key strips them out anyway.
                if re.fullmatch(r"[A-Za-z0-9 /.+-]{3,18}", token.strip()) and re.search(r"\d", token)
            ]
        for key in keys:
            if key and len(key) >= 3 and key not in origins:
                origins[key] = where
    # The manufacturer's own letter names one country per model where the
    # sheet may give a set's ("USA/MEXICO/CANADA"): its country stands; the
    # sheet's shipped-from stays (app.services.origin_letters).
    from collections import Counter

    from app.services import origin_letters

    declared = origin_letters.declared(brand)
    if declared:
        shipped = Counter(s for _m, _d, _made, s in read_origin_rows(library_root, brand) if s).most_common(1)
        usual = shipped[0][0] if shipped else ""
        for key, country in declared.items():
            origins[key] = (country, (origins.get(key) or ("", ""))[1] or usual)
    return origins


def origin_key(item, origins: dict, library: dict[str, str]) -> str:
    """The key a BOQ line's origin is under: its own part number when the
    sheet lists it, else the catalogue's spelling of it -- what the part
    library settled it to when it was read (`catalog_canonical`), the
    equipment table's alias for it, or a one-confusion match now."""
    from app.services import equipment_currents

    def k(text) -> str:
        return re.sub(r"[^A-Z0-9]", "", str(text or "").upper())

    key = k(item.catalog_no)
    if not key or key in origins:
        return key
    for candidate in (getattr(item, "catalog_canonical", None), equipment_currents.canonical(item.catalog_no)):
        if candidate and k(candidate) in origins:
            return k(candidate)
    if library:
        settled, _record = boq_provenance.catalogued(item.catalog_no, library)
        if settled and k(settled) in origins:
            return k(settled)
    return key


def build_country_of_origin(
    project: Project, library_root: Path | None, system_code: str | None = None,
    brand: str | None = None,
) -> pymupdf.Document:
    """The Country of Origin table, laid out as the Schedule of Material is.

    Same lettered blocks in the same order, so the two read as one document
    set -- a reviewer who finds a part in the schedule finds it in the same
    place here. The two extra columns are the declaration itself.
    """
    origins = read_origins(library_root, brand)
    # A BOQ line read off a scan may still hold the scan's spelling of a
    # part ("SIGA-AASO" for SIGA-AA50): its origin is looked up under the
    # catalogue's spelling when the reading itself is not on the sheet.
    from sqlalchemy.orm import Session as _Session

    session = _Session.object_session(project)
    library = boq_provenance.part_library(session) if session is not None else {}
    doc = pymupdf.open()
    page = doc.new_page(width=841.92, height=595.32)
    # The country of origin only: where it is shipped from is not declared (platform owner, 2 October 2026).
    columns = [("SL.", 42), ("MODEL", 82), ("DESCRIPTION", 214), ("COO", 660)]
    left, right = 36, 806

    def header(first: bool) -> float:
        nonlocal page
        if not first:
            page = doc.new_page(width=841.92, height=595.32)
        page.insert_text((40, 50), "COUNTRY OF ORIGIN", fontname="hebo", fontsize=16, color=_RED)
        page.insert_text((40, 68), _project_title(project).upper()[:90], fontname="helv", fontsize=9, color=(0.4, 0.4, 0.4))
        if system_code:
            page.insert_text((40, 82), system_code, fontname="hebo", fontsize=8.5, color=(0.45, 0.45, 0.45))
        y = 94
        page.draw_rect(pymupdf.Rect(left, y, right, y + 20), color=None, fill=_RED)
        for label, x in columns:
            page.insert_text((x, y + 14), label, fontname="hebo", fontsize=8.5, color=(1, 1, 1))
        return y + 20

    y = header(first=True)

    def room(needed: float) -> None:
        nonlocal y
        if y + needed > 552:
            y = header(first=False)

    for letter, title, items in schedule_blocks(project, system_code):
        room(46)
        page.draw_rect(pymupdf.Rect(left, y, right, y + 22), color=None, fill=(0.93, 0.94, 0.96))
        page.insert_text((42, y + 15), letter, fontname="hebo", fontsize=9.5, color=_RED)
        page.insert_text((62, y + 15), title.upper()[:96], fontname="hebo", fontsize=9, color=(0.06, 0.12, 0.21))
        y += 22

        for number, item in enumerate(items, 1):
            room(20)
            page.draw_rect(pymupdf.Rect(left, y, right, y + 18), color=(0.87, 0.87, 0.87), width=0.4)
            key = origin_key(item, origins, library)
            made_in, _shipped = origins.get(key, ("", ""))
            if not made_in:
                # the manufacturer's declaration for the part's range (Menvier: France / Romania)
                from app.services import origin_letters

                made_in = origin_letters.by_range(brand or getattr(item, "manufacturer", None), item.catalog_no) or ""
            cells = [
                (f"{letter}{number}", 42),
                ((item.catalog_no or "-")[:18], 82),
                ((item.description or "")[:100], 214),
                (made_in[:26], 660),
            ]
            for text, x in cells:
                page.insert_text((x, y + 12), text, fontname="helv", fontsize=7.5)
            y += 18
        y += 8

    room(30)
    page.insert_text(
        (left + 6, y + 12),
        "A blank country is one the reference sheet does not list; it is to be completed before issue.",
        fontname="helv", fontsize=7, color=(0.45, 0.45, 0.45),
    )
    return doc


def _docx_paragraphs(path: Path) -> list[str]:
    """The text of a .docx, paragraph by paragraph.

    A .docx is a zip of XML, so its wording can be read without Word and
    without a new dependency -- which is what lets the warranty keep the
    company's own text instead of a copy of it pasted into this file.
    """
    import zipfile

    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return []
    paragraphs: list[str] = []
    for block in re.split(r"</w:p>", xml):
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", block))
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()
        if text:
            paragraphs.append(text)
    return paragraphs


# --- the warranty, as the company's own document ---------------------------
#
# The warranty is a letter on the company's letterhead, and it is issued as
# that letter. So the .docx in the submittal builder is **filled in and
# converted**, not redrawn here: its layout, fonts, logo and signature block
# are the document, and a tidier page built from its words would be a
# different document wearing its text.
#
# Filling happens in the file's own XML, so every run keeps its formatting.
# Converting needs Word, which is what the machines this runs on have; where
# Word is not there, the drawn fallback below keeps the package buildable and
# says on its face that it is not the letterhead.

_WORD_PDF = 17          # wdFormatPDF


def _docx_runs(xml: str) -> list[str]:
    return re.findall(r"<w:t[^>]*>[^<]*</w:t>", xml)


def _fill_docx(template: Path, replace) -> bytes | None:
    """The template with its text replaced, still a .docx.

    Word splits a paragraph into runs wherever formatting changes, and a
    phrase can straddle them ("TWO" in one run, "YEARS" in the next), so the
    paragraph is joined, rewritten, and the result put back on its first run
    with the rest of that paragraph's text cleared. Runs a paragraph does not
    change are left exactly as they were.
    """
    import zipfile

    try:
        with zipfile.ZipFile(template) as archive:
            names = archive.namelist()
            parts = {name: archive.read(name) for name in names}
    except Exception:  # noqa: BLE001
        return None

    document = parts.get("word/document.xml")
    if document is None:
        return None
    xml = document.decode("utf-8", "replace")

    out: list[str] = []
    for index, block in enumerate(re.split(r"(</w:p>)", xml)):
        if index % 2 or "<w:t" not in block:
            out.append(block)
            continue
        runs = _docx_runs(block)
        # Unescaped on the way in and escaped on the way out. Reading the raw
        # XML and escaping it again turned the "&" of "manufactured &
        # supplied" into "&amp;" on the issued letter.
        texts = [_unescape(re.sub(r"<[^>]+>", "", run)) for run in runs]
        joined = "".join(texts)
        rewritten = replace(joined)
        if rewritten == joined:
            out.append(block)
            continue
        # Put the whole paragraph on its first run; blank the others. The
        # first run carries the paragraph's own formatting, which is what a
        # line like "PROJECT: ..." is set in.
        new_block = block
        first = True
        for run, text in zip(runs, texts):
            body = _escape(rewritten) if first else ""
            new_block = new_block.replace(run, re.sub(r">[^<]*</w:t>$", f">{body}</w:t>", run), 1)
            first = False
        out.append(new_block)

    parts["word/document.xml"] = "".join(out).encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.writestr(name, parts[name])
    return buffer.getvalue()


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _unescape(text: str) -> str:
    return text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def docx_to_pdf(data: bytes) -> bytes | None:
    """Convert a .docx to PDF with Word, or None where Word is not there.

    Word is asked to export, which is what keeps the letterhead identical to
    the one the team sends out. Everything is torn down in a finally block:
    a Word process left running would hold the file and the next build would
    wait on it.
    """
    if os.name != "nt":
        return None
    try:
        import pythoncom  # noqa: F401
        import win32com.client
    except ImportError:
        return None

    folder = Path(tempfile.mkdtemp(prefix="warranty-"))
    source, target = folder / "warranty.docx", folder / "warranty.pdf"
    source.write_bytes(data)
    word = None
    try:
        pythoncom.CoInitialize()
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(str(source), ReadOnly=False, Visible=False)
        try:
            document.SaveAs(str(target), FileFormat=_WORD_PDF)
        finally:
            document.Close(SaveChanges=0)
        return target.read_bytes() if target.is_file() else None
    except Exception:  # noqa: BLE001
        return None
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:  # noqa: BLE001
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:  # noqa: BLE001
            pass
        shutil.rmtree(folder, ignore_errors=True)


def warranty_replacements(project: Project, years: int = WARRANTY_YEARS, system_code: str | None = None):
    """How a line of the draft is rewritten for this project.

    Only two kinds of change: the parties, and the period. Every other word
    is the company's and is left alone -- except for a fire-rated cable
    warranty, where the system the draft names (fire alarm & voice
    evacuation) becomes the cable, and the manufacturer the cable brands
    (M/s. Fireguard & M/s. Ramcro).
    """
    from app.services import system_rules

    period = _YEAR_WORDS.get(years, f"{years} YEARS")
    code = system_rules.canonical(system_code)
    # The manufacturer of this system -- the emergency lighting's is not the
    # fire alarm's.
    from app.routers.projects import _brand_for

    brand = (_brand_for(system_code, list(project.systems)) if code else None) or next(
        (s.brand for s in project.systems if s.brand), None)
    cable = code == "FRC"
    # A warranty for another system than the draft's fire alarm: its name in
    # place of the draft's (platform owner, 2 October 2026).
    system_names = {"ELS": ("EMERGENCY LIGHTING SYSTEM", "emergency lighting system materials")}.get(code or "")
    if cable:
        from sqlalchemy.orm import Session as _Session

        from app.services import frc_cables

        session = _Session.object_session(project)
        row = frc_cables.get(session, project) if session is not None else None
        brands = [b for b in [row.brand if row else None, (frc_cables.monitoring_for(row, project) or (None,))[0]] if b]
        brand = " & ".join(f"M/s. {b.title()}" for b in dict.fromkeys(brands)) if brands else None
    party = lambda value: (value or "").strip() or "-"  # noqa: E731
    fields = {
        "DATE": date.today().strftime("%d/%m/%Y"),
        "PROJECT": _project_title(project),
        "CLIENT": party(project.client),
        "CONSULTANT": party(project.consultant),
        "MEP CONTRACTOR": party(project.contractor),
        "CONTRACTOR": party(project.contractor),
    }

    def replace(text: str) -> str:
        stripped = text.strip()
        for label, value in fields.items():
            # "MEP CONTRACTOR :" and "CONTRACTOR:" both occur; the longer
            # label is tried first because the dict is ordered that way.
            match = re.match(rf"^({re.escape(label)}\s*:\s*)", stripped, re.I)
            if match:
                return f"{match.group(1)}{value}"
        if re.match(r"^REF\s*NO", stripped, re.I):
            return re.sub(r"(:\s*).*$", rf"\g<1>EP-{project.ep_number}", stripped)
        new = re.sub(r"\b(ONE|TWO|THREE|FOUR|FIVE)\s+YEARS?\b", period, text, flags=re.I)
        if system_names:
            new = re.sub(r"FIRE ALARM\s*&\s*VOICE EVACUATION SYSTEM", system_names[0], new, flags=re.I)
            new = re.sub(r"fire alarm system materials", system_names[1], new, flags=re.I)
        if cable:
            new = re.sub(r"FIRE ALARM\s*&\s*VOICE EVACUATION SYSTEM", "FIRE RATED CABLE", new, flags=re.I)
            new = re.sub(r"fire alarm system materials", "fire rated cable materials", new, flags=re.I)
            if brand:
                new = re.sub(r"M/s\.\s*EDWARDS", brand, new, flags=re.I)
        elif brand:
            new = re.sub(r"M/s\.\s*EDWARDS", f"M/s. {brand}", new, flags=re.I)
        return new

    return replace


def build_warranty(
    project: Project, library_root: Path | None, system_code: str | None = None, years: int = WARRANTY_YEARS
) -> pymupdf.Document:
    """The warranty certificate: the company's letter, filled in.

    The draft is the document. It is filled and converted, so what goes into
    the package is the letterhead the team issues -- only the project's
    details and the warranty period differ from the file in the builder,
    which still reads TWO YEARS.
    """
    from app.services import company_library

    template = (company_library.submittal_path(library_root, None, WARRANTY_TEMPLATE) or library_root / WARRANTY_TEMPLATE)         if library_root else None
    if template is not None and template.is_file():
        filled = _fill_docx(template, warranty_replacements(project, years, system_code))
        if filled is not None:
            pdf = docx_to_pdf(filled)
            if pdf:
                return pymupdf.open(stream=pdf, filetype="pdf")

    return _drawn_warranty(project, template, years, system_code)


def _drawn_warranty(project: Project, template: Path | None, years: int, system_code: str | None = None) -> pymupdf.Document:
    """A plain rendering, for when Word is not available to convert the draft.

    It says so on the page. A warranty that silently did not look like the
    company's letter would be issued by someone who never noticed.
    """
    period = _YEAR_WORDS.get(years, f"{years} YEARS")
    paragraphs = _docx_paragraphs(template) if template and template.is_file() else []
    replace = warranty_replacements(project, years, system_code)
    body = [(replace(text), bool(re.match(r"^[A-Z ]+\s*:", text))) for text in paragraphs]

    if not body:
        body = [
            (f"The warranty draft was not found in the submittal builder ({WARRANTY_TEMPLATE}).", True),
            (f"The standard warranty period is {period} from Taking Over Certificate.", False),
        ]

    doc = pymupdf.open()
    page = doc.new_page(width=595.32, height=841.92)
    y = 70
    page.insert_text((56, y), "WARRANTY CERTIFICATE", fontname="hebo", fontsize=15, color=_RED)
    y += 18
    page.insert_text((56, y), "Not on the company letterhead: Word was not available to convert the draft.",
                     fontname="helv", fontsize=8, color=(0.65, 0.2, 0.2))
    y += 24

    for text, bold in body:
        if y > 770:
            page = doc.new_page(width=595.32, height=841.92)
            y = 70
        font = "hebo" if bold else "helv"
        size = 9.5 if bold else 9
        line = ""
        for word in text.split():
            trial = f"{line} {word}".strip()
            if pymupdf.get_text_length(trial, fontname=font, fontsize=size) > 480 and line:
                page.insert_text((56, y), line, fontname=font, fontsize=size)
                y += size + 4
                line = word
                if y > 790:
                    page = doc.new_page(width=595.32, height=841.92)
                    y = 70
            else:
                line = trial
        if line:
            page.insert_text((56, y), line, fontname=font, fontsize=size)
            y += size + 4
        y += 5
    return doc
