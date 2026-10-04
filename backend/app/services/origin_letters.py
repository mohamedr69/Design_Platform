"""Country of origin as the manufacturer declares it, model by model.

The company's COO sheet (`submittal_package.read_origins`) gives some parts
a set's origin -- "USA/MEXICO/CANADA" for every EST4 panel module -- where
the manufacturer's own letter names one country per model. The letter is
the declaration a consultant will hold the submittal to, so its country
stands over the sheet's for the models it lists (platform owner, 2 October
2026). The sheet still answers for every model a letter does not list, and
for where the material is shipped from.

Kidde Global Solutions (KGS Fire & Security B.V.) -- Edwards / EST:
  - "Country of Origin and Quality Assurance", 23 September 2026 (Nobu Hotel)
  - "Country of Origin and Quality Assurance", 24 August 2026 (TECOM-A DCP-01)
The later letter wins where both list a model (they agree on every one).

Menvier (Eaton) -- the COO declared on The Oasis Mall's emergency lighting
submittal: the CGLine+ controllers are made in France, the luminaires, exit
signs and their accessories in Romania. Declared by range rather than by
model (`by_range`), so every Menvier part has its country.
"""
from __future__ import annotations

import re

SOURCES = {
    "KIDDE": "Kidde Global Solutions COO letters, 23 Sep 2026 and 24 Aug 2026",
}

# The letter's "UNITED STATES" / "UNITED KINGDOM", written the way the
# company's sheet writes a country.
_KIDDE = """
FW-CGSUL USA
PT-1S-220 THAILAND
FSB-PC4 USA
FSB-BRKT2 USA
4-CPU MEXICO
4-PPS/M MEXICO
4-LCD MEXICO
4-LCDLE USA
4-24L24S MEXICO
4-FWAL4 MEXICO
4-BRKT-CS USA
4-NET-TP USA
4-USBHUB MEXICO
4-COMREL MEXICO
3-SDDC2 MEXICO
3-SSDC2 MEXICO
3-ZA20A MEXICO
4-AUDTELS MEXICO
4-MIC MEXICO
4-FT MEXICO
3-CHAS7 CHINA
4-FIL USA
3-CAB14B CANADA
4-CAB24D CANADA
BC-1 CANADA
3-CAB7B CANADA
4-CAB16D CANADA
3-CAB5B CANADA
4-CAB8D CANADA
4-2ANN USA
4-LCDANN USA
4-2ANNMT USA
APS6A/230 CHINA
SIGA-AA50 MEXICO
SIGA-CT2 MEXICO
BPS10A/230 CHINA
SIGA-SD CHINA
SD-T42 MEXICO
ADLCU-2 UK
AD68-0100 UK
AACU-EOL UK
SIGA-OSD-FCN CHINA
SIGA-HRD-FCN CHINA
SIGA-OSHD-FCN CHINA
SIGA-SB CHINA
SIGA-IB CHINA
SIGA-LPS CHINA
SIGA-LED CHINA
SIGA-278 MEXICO
STI-1230 USA
STI-3002 USA
SIGA-CR MEXICO
SIGA-IO MEXICO
SIGA-UM MEXICO
SIGA-CC1 MEXICO
SIGA-CC2A MEXICO
G4SRN CHINA
G1ARN CHINA
EST-S186C CHINA
757-1A-S70 CHINA
757-1A-T CHINA
757-7A-SS70 CHINA
757-7A-T CHINA
202-7A-TW CHINA
6830-3 USA
6830-NY-F4 USA
6832-1 CHINA
6833-4 CHINA
TCS-6 USA
27193-11 CHINA
27193-16 CHINA
27193-21 USA
757A-WB INDIA
"""

_BRANDS = {"EDWARDS": "KIDDE", "EST": "KIDDE", "KIDDE": "KIDDE", "KGS": "KIDDE",
           "MENVIER": "MENVIER", "MENIVIER": "MENVIER", "EATON": "MENVIER"}
SOURCES["MENVIER"] = "Menvier COO, The Oasis Mall emergency lighting submittal"

# (part-number pattern, country), first match wins; None: no range rule.
_RANGES: dict[str, list[tuple[re.Pattern, str]]] = {
    "MENVIER": [
        (re.compile(r"^CTR"), "FRANCE"),          # CGLine+ controllers (the panels)
        (re.compile(r"."), "ROMANIA"),            # luminaires, exit signs, accessories
    ],
}
_TABLES = {"KIDDE": _KIDDE}


def _key(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def declared(brand: str | None) -> dict[str, str]:
    """{part key: country} the brand's manufacturer declares; empty for a
    brand with no letter on file."""
    table = _TABLES.get(_BRANDS.get((brand or "").strip().upper(), ""))
    out: dict[str, str] = {}
    for line in (table or "").strip().splitlines():
        model, country = line.rsplit(" ", 1)
        out[_key(model)] = country
    return out


def by_range(brand: str | None, part_no: str | None) -> str | None:
    """The country a brand declares for a whole range the part belongs to
    (Menvier: controllers France, everything else Romania); None when the
    brand declares none."""
    rules = _RANGES.get(_BRANDS.get((brand or "").strip().upper(), ""), [])
    key = _key(part_no or "")
    if not key:
        return None
    return next((country for pattern, country in rules if pattern.search(key)), None)


def source(brand: str | None) -> str | None:
    return SOURCES.get(_BRANDS.get((brand or "").strip().upper(), ""))
