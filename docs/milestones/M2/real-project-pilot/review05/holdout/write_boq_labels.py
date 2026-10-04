"""Holdout BOQ labels (M2 review 05): every row of the four holdout Design Sheets, from renders, before the reader ran."""
import json, sys

R = sys.argv[1]
sample = json.load(open(R + "/holdout/HOLDOUT-SAMPLE.json", encoding="utf-8"))


def L(page, qty, part, desc, group=None, kind="line", **kw):
    return {"page": page, "kind": kind, "group": group, "quantity": qty, "part_number": part, "description": desc, **kw}


def H(page, desc):
    return {"page": page, "kind": "heading", "group": desc, "quantity": None, "part_number": None, "description": desc}


sheets = {
 "28605": [L(1, "9", "SL2-42D3D-CGL-M", "Surface Mounted Emergency Light"),
           L(1, "140", "RT2RHEO200CGL3HIPM", "RTECH MR HEO CGL+ 200 MNM 3H IP65", multiline_part="RT2RHEO200CGL3HIP / M (the part wraps its last M)"),
           L(1, "35", "SL2-42D3D-CGL-M +SL2RB +SL2DC3I", "Exit Directional, Corridor Recessed, 30 metre viewing distance", multiline_part="two lines"),
           L(1, "1", "CTR400CGL2KS-M", "Menvier Brand CGLine+ Web Compact Controlle(r) (cut at the cell edge)")],
 "19138": [H(1, "IO64 Fire Alarm Control Panel"),
           L(1, "1", None, "IO64 Single loop fire alarm control panel, with built-in system relays, 4 x 20 character backlit LCD display, 2 Nac's (3.75 amps), rechargeable batteries ... Components are:", "IO64 Fire Alarm Control Panel"),
           L(1, "1", "IO64G-2", "FACP,1LOOP,64PT,230V", "IO64 Fire Alarm Control Panel", kind="component", note="quantity printed '( 1 )' in the description"),
           L(1, "2", "12V8A", "Battery 8 AH, 12 volt cells", "IO64 Fire Alarm Control Panel", kind="component", note="quantity printed '( 2 )' in the description"),
           H(1, "Field Devices"),
           *[L(1, q, p, d, "Field Devices") for q, p, d in (("11", "SIGA-PD", "Intelligent Photoelectric Smoke Detector"),
                                                              ("1", "SIGA-HRD", "Intelligent Fixed Temperature / Rate-of-Rise Heat Detector"),
                                                              ("12", "SIGA-SB", "Signature Detector Base"),
                                                              ("1", "SIGA-278", "Manual Pull Station - Double Action, 1-stage"),
                                                              ("3", "G1R-HDVM", "Genesis Temporal Horn-strobe, RED"),
                                                              ("1", "757-7A-T", "15/75 cd Temporal Horn/Strobe - 24 Vdc, RED"),
                                                              ("1", "757A-WB", "Weatherproof Box, Cast - RED"),
                                                              ("1", "SIGA-CT2", "Dual Input Module"),
                                                              ("2", "SIGA-CR", "Control Relay Module"),
                                                              ("2", "TP606", "2\"x4\" GI Concealed Back Box Single Gange"),
                                                              ("3", "27193-11", "Surface Mount Box - Indoor, RED, 1-gang"))]],
 "8430": [H(1, "Praesideo System"),
          *[L(1, q, p, d, "Praesideo System") for q, p, d in (
              ("2", "PRS-NCO3", "Network Controller (INCL. PRS-SW)"), ("1", "LBB4404/00", "Cobra Net Interface"),
              ("27", "LBB4416/01", "Network Cable Assembly 0.5m"), ("4", "LBB4416/02", "Network Cable Assembly 2m"),
              ("1", "LBB4430/00", "Call Station Basic"), ("1", "PRS-CSNKP", "Numeric Keypad"), ("1", "PRS-CSR", "Remote Call Station"),
              ("1", "PRS-CSI", "Call Station Interface"), ("2", "PRS-48CH12", "48V Battery Charger Basic"),
              ("27", "LBB4443/00", "End of Line Supervision"), ("1", "LBB4428/00-EU", "Power Amplifier 8 X 60 W (EU)"),
              ("3", "PRS-4P125-EU", "Power Amplifier 4 X 125 W (EU)"), ("15", "PRS-1P500-EU", "Power Amplifier 1 X 500 W (EU)"),
              ("94", "LBC3086/41", "Ceiling Loudspeaker"), ("94", "LBC3081/02", "Metal Fire Dome"), ("12", "LBC3018/01", "Cabinet Loudspeaker"),
              ("515", "LH1-10M10E", "Horn Loudspeaker 10W, Evac"), ("1", "LBC1420/20", "Volume Control Fail Safe 100W (MK Double, w/ Mounting Box"),
              ("1", "PRS-SWCS", "PC Call Server"), ("1", "PRS-SWCSL-E", "PC Call Server NCO License E-code"), ("4", "PRS-FIN", "Fiber Interface"),
              ("1", None, "PC+Monitor"), ("1", None, "CD Changer"), ("1", None, "MP3 Player"), ("1", None, "FM/AM Tuner"),
              ("8", None, "Battery"), ("2", None, "PA Rack"))],
          H(1, "Optional"), H(1, "Recommended Spare Requirement as per Specification"),
          *[L(1, q, p, d, "Optional / spares") for q, p, d in (("12", "LBC3086/41", "Ceiling Loudspeaker"), ("12", "LBC3081/02", "Metal Fire Dome"),
                                                                ("11", "LH1-10M10E", "Horn Loudspeaker 10W, Evac"))],
          H(1, "Requirements as per Specification"),
          *[L(1, q, p, d, "Optional / requirements") for q, p, d in (("2", None, "PC+Monitor"), ("2", "PRS-CSC-E", "PC Call Station Client"),
                                                                      ("2", "LBB4430/00", "Call Station Basic"), ("2", "PRS-CSNKP", "Numeric Keypad"),
                                                                      ("2", "PRS-CSR", "Remote Call Station"), ("2", "PRS-CSI", "Call Station Interface"),
                                                                      ("1", None, "Printer"))]],
}
SCS = [("NKUKS2SAW", "NetKey 86mm x 86mm Faceplate", "11", "Copper ICT"), ("NK6X88MAW", "Cat 6A UTP RJ45 Punchdown Keystone Jack Module", "44", "Copper ICT"),
       ("NKFP24Y", "NetKey Patch Panel, 24 Port, 1 RU, BL", "1", "Copper ICT"), ("WMPFSE", "PatchLink Horizontal Single-Sided Manager, 1RU, 3.7 in. Depth", "1", "Copper ICT"),
       ("NUL6X04WH-FEG", "Copper Cable, Cat 6A, 23 AWG, U/UTP, LSZH-1, White", "lot", "Copper ICT"),
       ("FPSN924", "24 fibre outside plant armored (single armor, single jacket) cable is OS2, EuroClass Fca and features 250um fibres", "lot", "Backbone Cabling"),
       ("FMT1", "Opticom Fiber Tray, Straight, 1 RU, 4 Port", "2", "Fiber Optic Accessories inside MTR"),
       ("CFAPPBL1", "Opticom Fiber Patch Panel, Flat, Black, 1 RU", "2", "Fiber Optic Accessories inside MTR"),
       ("FSC24", "Opticom Fiber Splice Holder, 24 Splices, Black", "2", "Fiber Optic Accessories inside MTR"),
       ("FAP12WAGSCZ", "Opticom Fiber Adapter Panel, OS2, 12 SC Simplex, APC Green", "4", "Fiber Optic Accessories inside MTR"),
       ("F91BNANNNSNM001", "SC APC TO PIGTAIL, 9/125 MICRON, SIMPLEX", "48", "Fiber Optic Accessories inside MTR")]
CCTV = [("AXIS P3267-L", "Indoor 5 MP dome with IR and deep learning", "3", "Cameras"), ("AXIS P1467-LE", "5 MP Bullet camera", "4", "Cameras"),
        ("AMG570-8GAT-3S-P240", "Industrial 11 Port Managed Switch, 8 x 10/100/1000Base-T(x)", "1", "Switch"),
        ("AMGPSU-I48-P240", "48 VDC, 240W (5A) Industrial Power Supply, DIN-Rail Mounting", "1", "Switch"),
        ("SFP-SM-1G-LX20-31", "SFP Single mode, 1Gb, 2 Fibers, 20Km, LC Connectors, 1310nm Tx/Rx, DDM", "2", "Transcievers"),
        ("310049", "ASI DAKER DK 1KVA BS", "1", "UPS in IDF"), ("310660", "EBC DK PLUS 1KVA", "1", "UPS in IDF"),
        ("310952", "RAIL KIT RACK DK (2U)", "2", "UPS in IDF"), ("311058", "CS102 SK - SNMP CARD", "1", "UPS in IDF")]
PASSIVE = [("NK6X88MAW", "Cat 6A UTP RJ45 Punchdown Keystone Jack Module", "7", "Copper Cabling: Panduit"), ("NKFP24Y", "NetKey Patch Panel, 24 Port, 1 RU, BL", "1", "Copper Cabling: Panduit"),
           ("WMPFSE", "PatchLink Horizontal Single-Sided Manager, 1RU, 3.7 in. Depth", "1", "Copper Cabling: Panduit"),
           ("NUL6X04WH-FEG", "Copper Cable, Cat 6A, 23 AWG, U/UTP, LSZH-1, White", "lot", "Copper Cabling: Panduit"),
           ("FPSN924", "24 fibre outside plant armored cable is OS2, EuroClass Fca and features 250um fibres", "lot", "Backbone Cabling"),
           ("FMT1", "Opticom Fiber Tray, Straight, 1 RU, 4 Port", "2", "Fiber Optic Accessories inside MTR"),
           ("CFAPPBL1", "Opticom Fiber Patch Panel, Flat, Black, 1 RU", "2", "Fiber Optic Accessories inside MTR"),
           ("FSC24", "Opticom Fiber Splice Holder, 24 Splices, Black", "2", "Fiber Optic Accessories inside MTR"),
           ("FAP12WAGSCZ", "Opticom Fiber Adapter Panel, OS2, 12 SC Simplex, APC Green", "4", "Fiber Optic Accessories inside MTR"),
           ("F91BNANNNSNM001", "SC APC TO PIGTAIL, 9/125 MICRON, SIMPLEX", "48", "Fiber Optic Accessories inside MTR")]


def section(page, rows, headings_at, rack=True, rack_page=None):
    out, seen = [], set()
    for part, desc, qty, group in rows:
        if group not in seen:
            out.append(H(page, group)); seen.add(group)
        out.append(L(page, qty, part, desc, group, note="the '#A' column beside it is an item number, not a quantity"))
    if rack:
        out.append(H(rack_page or page, "Racks")); out.append(L(rack_page or page, "1", None, "18U Rack", "Racks"))
    return out


s28569 = (section(1, SCS, None) +                       # Structured Cabling / AL Hamriyah (items 1-12)
          section(1, SCS, None, rack_page=2) +          # Structured Cabling / Al Zoraa (items 1-11 on page 1, rack 12 on page 2)
          [H(2, "Network Switches Brand: AMG"), H(2, "UPS Brand : Legrand"), H(2, "Passive Components")] +
          section(2, CCTV, None, rack=False) + section(2, PASSIVE, None) +       # CCTV / AL Hamriyah (page 2)
          [H(3, "Network Switches Brand: AMG"), H(3, "UPS Brand : Legrand"), H(3, "Passive Components")] +
          section(3, CCTV, None, rack=False) + section(3, PASSIVE, None))        # CCTV / AL Hamriyah again (page 3, printed title)
sheets["28569"] = s28569

out_sheets, frozen = [], []
for d in sample["documents"]:
    if d["stratum"] != "boq_design_sheet":
        continue
    rows = sheets[d["ep"]]
    out_sheets.append({"ep": d["ep"], "sha256_prefix": d["sha256"][:12], "relative_path": d["relative_path"], "rows": rows,
                       "pages": max(r["page"] for r in rows)})
    frozen.append({"ep": d["ep"], "relative_path": d["relative_path"], "sha256": d["sha256"], "staged_path": d["staged_path"], "cohort": "holdout"})
json.dump({"boq_design_sheets": {"labeller": "Claude (Fable 5.1), from renders of the staged holdout originals, before the reader ran. No countersignature claimed.",
                                 "sheets": out_sheets}}, open(R + "/holdout/HOLDOUT-BOQ-LABELS.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
json.dump({"sheets": frozen}, open(R + "/holdout/HOLDOUT-BOQ-SET.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
import collections
for s in out_sheets:
    print(s["ep"], len(s["rows"]), dict(collections.Counter(r["kind"] for r in s["rows"])))
