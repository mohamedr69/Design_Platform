import pathlib

p = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\app\services\document_control.py")
s = p.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)


sub('''    uncertain_start: bool = False
''', '''    uncertain_start: bool = False
    # Named as what the page is about, not as the page: a letter's or a comment sheet's "Subject: … Ref. X",
    # a clause's citation "(Ref: X)" (A23 comment sheet, Voltas quotation; M2 review 05).
    about: bool = False
    # A form's own control number printed in its footer ("R1029-CSCEC-FM-MAR-001_R01" over "Version Date"):
    # the template's identity, on every page made from it (MTG-1020 page 6; M2 review 05).
    template: bool = False

    @property
    def identity_candidate(self) -> bool:
        """Whether this may be the page's own number at all."""
        return not (self.cross_reference or self.about or self.template)
''')

sub('''                                      uncertain_start=bool(_SPLIT_START.search(before))))''',
    '''                                      uncertain_start=bool(_SPLIT_START.search(before)),
                                      about=bool(_SUBJECT_LINE.search(before) or _CITATION.search(before)),
                                      template=bool(_TEMPLATE_AFTER.search(text[match.end():match.end() + 60]))))''')

sub('''_SPLIT_START = re.compile(r"(?:^|[\\s|:])[A-Za-z] $|-[A-Z0-9]+ $")''',
    '''_SPLIT_START = re.compile(r"(?:^|[\\s|:])[A-Za-z] $|-[A-Z0-9]+ $")
_SUBJECT_LINE = re.compile(r"^\\W{0,3}Subject\\b", re.I)
_CITATION = re.compile(r"\\(\\s*ref(?:erence)?\\.?\\s*(?:no\\.?)?\\s*[:#]?\\s*$", re.I)
_TEMPLATE_AFTER = re.compile(r"^_R\\d+\\b|^[^\\n]{0,12}\\n\\s*Version\\s+(?:Date|No)\\b", re.I)

# A revision that is not the document's: a form's own edition ("Form No.: F-013 / Rev.0", a footer
# "LAC-SM-Feb. 2014 (Rev.02)") and a table's column header ("DRAWING No. / DOCUMENTS No. Rev" over the
# reference drawings). EP-19977's Emaar form read R0 from its template; NCC FA-047 read R2 from its footer;
# NCC FA-031's sheet read R1 from its reference table (M2 review 05).
_FORM_EDITION = re.compile(r"\\bForm\\s*(?:No|Ref)\\b|\\bAppendix\\s+[A-Z]\\d*\\b|\\bPage\\s*\\d+\\s*of\\s*\\d+|\\bVersion\\s+Date\\b|\\bIssue\\s+Date\\b", re.I)
_TABLE_HEADER = re.compile(r"\\b(?:DRAWING\\s*No|DOCUMENTS?\\s*No|DESCRIPTION|TITLE|SHEET)\\b", re.I)


def page_revision(text: str):
    """The page's own revision field as a REV match (group 1 the number), or None: the first REV that is
    not a form's edition, a table's column header or a date under the label."""
    for found in REV.finditer(text):
        line_start = text.rfind("\\n", 0, found.start()) + 1
        previous_start = text.rfind("\\n", 0, max(line_start - 1, 0)) + 1
        line_end = text.find("\\n", found.start())
        line = text[line_start:len(text) if line_end < 0 else line_end]
        if text[max(0, found.start() - 1):found.start()] == "(" or _FORM_EDITION.search(text[previous_start:len(text) if line_end < 0 else line_end]):
            continue
        rest = line.replace(line[found.start() - line_start:], "")
        if _TABLE_HEADER.search(line) and not re.search(r"\\d", rest):
            continue
        return found
    return None''')

sub('''    found = [c for c in reference_candidates(text) if not c.cross_reference]''',
    '''    found = [c for c in reference_candidates(text) if c.identity_candidate]''')

sub('''    serials = [c for c in candidates if c.kind == "serial" and c.category == category]''',
    '''    serials = [c for c in candidates if c.kind == "serial" and c.category == category and c.identity_candidate]''')

sub('''    revision_match = REV.search(text)
    revision = f"R{int(revision_match.group(1))}" if revision_match else None''',
    '''    revision_match = page_revision(text)
    revision = f"R{int(revision_match.group(1))}" if revision_match else None''')

sub('''        replies = [c for c in reference_candidates(text) if not c.cross_reference]''',
    '''        replies = [c for c in reference_candidates(text) if c.identity_candidate]''')

sub('''        revision_match = REV.search(text) or re.search(r"\\bR\\.?\\s*(\\d{1,3})\\b", text)''',
    '''        revision_match = page_revision(text) or re.search(r"\\bR\\.?\\s*(\\d{1,3})\\b", text)''')

sub('''    if _is_transmittal_form(text):
        return []''', '''    if _is_transmittal_form(text) or _COVERING_SHEET.search(text):
        return []''')

sub('''        own_before = [c for c in reference_candidates(text) if not c.cross_reference and not _listed(text, c)]''',
    '''        own_before = [c for c in reference_candidates(text) if c.identity_candidate and not _listed(text, c)]''')

sub('''    revision_match = None if geometry else REV.search(text)''',
    '''    revision_match = None if geometry else page_revision(text)''')

sub('''def _listed(text: str, candidate: ReferenceCandidate) -> bool:''',
    '''# A covering sheet sent with a document -- a fax cover, a transmittal letter -- names the document it
# carries ("kindly find attached … material submittal reference # A23-EFE-MAT-E-0033"); it is not that
# document (EFECO fax, EP-13777; M2 review 05).
_COVERING_SHEET = re.compile(r"\\bFACSIMILE\\s+TRANSMITTAL\\b|\\bFAX\\s+(?:COVER|TRANSMITTAL)\\b", re.I)


def _listed(text: str, candidate: ReferenceCandidate) -> bool:''')

sub('''                            if not found: found = ocr_found''',
    '''                            if sheet is not None and sheet.number:
                                # The title block gave the sheet's own number: OCR of its images adds a stamp or
                                # a decision, never another identity -- a callout's "DWG No. …-FA-00104" on the
                                # ICT sheet SA-H2-BEST-ICT-00100a is not the sheet (M2 review 05).
                                ocr_found = [r for r in ocr_found if re.sub(r"\\s+", "", r.reference).upper() == re.sub(r"\\s+", "", sheet.number).upper()]
                            if not found: found = ocr_found''')

p.write_text(s, encoding="utf-8")
print("ok")
