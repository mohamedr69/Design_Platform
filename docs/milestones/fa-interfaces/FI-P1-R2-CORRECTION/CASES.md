# FI-P1 r2: reported cases, reproduced read-only

Source data:
- The cached DXFs of EP-30880, under `uploads/EP-30880/interfaces/<sha24>.dxf` in the live checkout, read only.
- The project folder listing, `stat` only.

Method: the existing deterministic reader (`scan.read`, `scan._texts`) and ezdxf queries. No model calls, no writes.

| Drawing | sha24 |
|---|---|
| SMOKE LAYOUT.dwg (SM) | `fe304ccf33fac4f68bedbcbf` |
| VENTILATION LAYOUT.dwg (HVAC) | `8eea8dd66621d1ecfd0f49e0` |
| BINGHATTI TITANIA GATEBARRIER SYSTEM LAYOUT.dwg (GB) | `eda8dd8d07475ef00c8e299c` |
| Shop Drawings-Titania rev01.dwg (GB) | `a7fb4efa61a6ddb3f6b991ac` |

## Case 1: "Two MSD/smoke drawings exist, but the current workflow reads only one"

There are two causes, both confirmed.

### 1a. The other drawing's dampers are dropped per floor

`service._equipment_rows` keeps, for each (key, floor), only the drawing with the most untagged labels (the "winner" rule, service.py:694-712). Both SMOKE LAYOUT and VENTILATION LAYOUT carry damper labels. Comparing label positions per floor (≤ 0.5 m means the same spot):

| Floor | SM labels | HVAC labels | Same spot | SM only | HVAC only | Kept today |
|---|---|---|---|---|---|---|
| 3rd basement | 2 | 4 | 1 | 1 (the "SD" door tag at 701.8,154.4) | 3 (**the two adjacent MSDs at 719.2,154.4 / 720.1,154.7**, and an SD at 747.3,157.9) | HVAC only |
| 2nd basement | 1 | 1 | 0 | 1 | 1 | one of the two |
| 1st basement | 3 | 3 | 2 | 1 | 1 | one of the two |
| Ground | 5 | 5 | 5 | 0 | 0 | either (identical) |
| Podium 1 / 4 | 1 / 2 | 1 / 2 | all | 0 | 0 | either |
| Mechanical | 1 | 8 | 0 | 1 | 6+ | HVAC only; SM's MD dropped |
| Roof | 16 | 14 | 7 | 9 | 7 | SM only; **7 HVAC dampers dropped** |

The drawings show partly the same dampers (Ground, Podium) and partly different ones (Mechanical, Roof). The winner rule therefore loses real dampers. The Ground and Podium coincidences (every label within 0.5 m) are also the evidence that the two files share a model frame on those floors.

### 1b. Smoke-management drawings filed as PDF are not even listed

`Mechanical/SM/SD/` holds three PDFs:
- `MAJ002-GME-SDW-MH-KS-ZZZ-B01-010042 B1.pdf`
- `…-ZZZ-010043 B3,B2.pdf`
- `…-ZZZ-010030-R0 GF TO ROOF.pdf`

`discover()` keeps DWG/DXF only (service.py:115), so they appear nowhere: not in coverage, not as "not read". The same is true of the PDF copies in GB and ACS.

The visual look also hung on SMOKE LAYOUT (jobs 142/144), so VENTILATION's dampers were never looked at. Stage 0.3 removes that.

## Case 2: equipment position points to tag text

- `scan._texts` stores each label's text insertion or alignment point as the item's `x, y` (scan.py:52-59). No symbol, handle or bbox is stored.
- Untagged rows take `anchor` from the cluster's first label (service.py:719-722).
- Visual damper rows take the model's free point, never checked against geometry (visual.py:336-338).
- Example: the two MSDs' labels (MTEXT `5741C` at 719.25,154.40 and `5741E` at 720.07,154.66) sit 0.26 m and 0.46 m from their symbols, the INSERTs `5741B` (719.45,154.23) and `5741D` (720.53,154.72) of block `A$C0e331ec6`. Today the row points at the text.

## Case 3: Gate Barrier with separate ENTRY and EXIT barriers yields one interface

**Today.** The detector (detect.py:120) matches only the words "GATE BARRIER". In the GB layout it finds three labels, all notes:
- "GATE BARRIER" (1165.69,178.70)
- "GATE BARRIER NETWORK"
- "TO BE CONNECTED TO … GATE BARRIER NETWORK"

They are untagged, and on the ground-floor sheet they cluster into **one** gate barrier line. The shop drawing adds two cabling notes ("1 DATA POINT … GATE BARRIER CONTROL PANEL").

**What the GB layout's ground floor actually shows** (sheet `gf`, model space, metres):

| Evidence | Entry lane | Exit lane |
|---|---|---|
| Role labels | "PARKING ENTRY" (1159.30,180.74), "PARKING ENT." (1159.65,178.70) | "PARKING EXIT." (1165.06,178.28) |
| Fire-alarm connection note | "DRY CONTACT BY THIRD PARTY (2 Core) FIRE ALARM CABLE" (1162.25,181.70), leaders `6F68E`/`6F68F` | the same note (1164.55,177.04), leaders `6F544`/`6F545` |
| Lane geometry | SAFETY LOOP polyline `6E353` x 1159.68–1161.46 | SAFETY LOOP `6E350` x 1165.48–1167.27; PRESIDENTIAL LOOP FOR EXIT `6F66D` |

That is two barriers, each with its own fire-alarm dry-contact connection. Matrix rule 30 (`gate_barrier`, CR, "to open exit gate barrier … additional control module … to close Entrance Gate Barrier") gives each barrier its own CR.

**The shop drawing shows the same two lanes** on its ground-floor sheet: two "FIRE ALARM CABLE" notes at (1190.57,175.95) and (1195.76,175.76), PHOTOCEL, SAFETY/PRESENCE LOOPs and arm lengths. They sit about 30 m away in model space from the layout's lanes, so the frames are **not** shared.

**Traps that must not create barriers:**
- Its blocks `ENTRY A` / `EXIT A` (handles 688E4/688E5, 712B4/712B5) lie **outside every sheet viewport**. They are library or legend copies.
- Repeated per-lane labels (SAFETY LOOP, PRESENCE LOOP, PHOTOCEL, FIRE ALARM CABLE in typical details and schematics) are labels, not barriers.

**Required:** two CR interfaces from evidence (two distinct connection points on a plan sheet, each uniquely tied to a role and a lane), counted once across the two drawings, and never from a hard-coded "two".
