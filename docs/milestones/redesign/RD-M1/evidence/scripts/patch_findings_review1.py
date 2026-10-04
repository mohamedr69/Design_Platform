"""Apply independent-review round 1 changes to findings.py (producer edit, recorded for audit)."""
import os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "findings.py")
s = open(p, encoding="utf-8").read()
R = [
    ('evidence="E01 script line 51 (original) inserts', 'evidence="Original script line 51 (= E01 line 53) inserts'),
    ("E01 lines 51/60/69/78/87 (PC-A path) vs 96/105 (G path).",
     "original script lines 51/60/69/78/87 (PC-A path) vs 96/105 (G path) = E01 lines 53/62/71/80/89 vs 98/107."),
    ('evidence="cad.py:118-121; E01 lines 51-54.', 'evidence="cad.py:118-121; original script lines 51-54 (= E01 lines 53-56).'),
    ("actual=\"_drawn() makes every review-sourced change in status 'proposed' (AI-placed, never approved) as well as approved ones;",
     "actual=\"_drawn() makes every review-sourced change in status 'proposed' as well as approved ones. The change itself was accepted "
     "by an engineer in the Drawings Review; what is unapproved is the AI's placement / symbol / erase target;"),
    ("Of 92,093 indexed segments only 9,461 (~10%) are on an explicit wall layer (06-WALL); 28,491 are raw layer '0',",
     "Of 92,093 indexed segments only 9,461 (~10%, by RAW layer; the effective layer of the 28,491 raw-layer-'0' segments was not "
     "determined in bulk) are on an explicit wall layer (06-WALL); 4,351 (4.7%) come from entities with the DXF invisible flag "
     "(group 60) set, 3,973 of them on raw layer '0' (found by the independent reviewer, re-run by the producer: "
     "evidence/scripts/invisible_flag.py);"),
    ("cause=\"walls.build filters on the decomposed entity's raw layer (walls.py:164); recursive_decompose keeps '0' for block content "
     "instead of the INSERT's layer, and layer on/frozen/plot state is not considered; the filter is a deny-list.\",",
     "cause=\"walls.build filters on the decomposed entity's raw layer (walls.py:164); recursive_decompose keeps '0' for block content "
     "instead of the INSERT's layer; layer on/frozen/plot state, viewport freeze and the entity invisible flag (walls.py:159-170 never "
     "reads dxf.invisible) are not considered; the filter is a deny-list.\","),
    ('actual="Two APPROVED modules (drawn by Apply) are mounted on the non-plotting parking-block line of F005:',
     "actual=\"Two APPROVED modules (drawn by Apply) are mounted on parking-block geometry admitted through raw layer '0' "
     "(effective layer 29-PARKING, which NOT_WALLS would exclude) - F005:"),
    ("evidence=\"E07 (if:e9335f7e336e:CT21 moved=True on_wall=True; if:d6137c203008:CT21 approved on_wall=True); crop R02 A vs B; "
     "E11 probe 'invisible-rect-left-edge'.\",",
     "evidence=\"E07 (if:e9335f7e336e:CT21 moved=True on_wall=True; if:d6137c203008:CT21 approved on_wall=True); crop R02 A vs B "
     "(no line plotted there - visual); E11 probe 'invisible-rect-left-edge'. Note: E11 'visible' reflects LAYER state only "
     "(on/frozen/plot); it does not read the entity invisible flag or viewport freeze. The segment under CT2 FOR ZCV "
     "(y 161.288-162.588) has invisible=1; the segment under CT2 FOR ELECTRIC PUMP (y 156.288-158.788) has invisible=0, so why it "
     "does not plot is UNEXPLAINED (independent review).\","),
    ('cause_status="CONFIRMED for wall source (F005); visual placement judgement PROPOSED (AI)",',
     'cause_status="CONFIRMED: modules sit on parking-block geometry (data + code). Not plotting: PROPOSED (visual), explained by the '
     'invisible flag for the ZCV segment only. Engineering judgement: PROPOSED (AI)",'),
    ('it failed (F001).",\n  evidence="E02 jobs 118/119;',
     "it failed (F001). Likely reason it was still running in the copy: the DB was copied between the Apply's output commit "
     "(12:55:35) and the job finishing (PC-A sync worker last heartbeat 12:55:33 - independent review).\",\n"
     '  evidence="E02 jobs 118/119;'),
]
for a, b in R:
    assert a in s, a[:70]
    s = s.replace(a, b)

NEW = '''
f(id="RD-M1-F032", primary="G. Workflow - manual decision overwritten (no concurrency control)", secondary="G. stale plan",
  severity="High", expected="An engineer's approve/skip/move made while a Plan or Apply runs is never lost; concurrent writers are detected.",
  actual="plan() writes the whole row.changes from its start-time list after every model answer (service.py:1175; also 1146, 1181), so a PATCH made during a Plan (job 102 ran 3.5 min) is overwritten. adjust()/set_status() have no status or version guard (service.py:662, 1247). Plan and Apply have different dedup keys (routers/redesign.py:74, key = kind:project:drawing), so both can run at once. refresh() inside Apply commits the row whenever coordination touches anything (service.py:1324-1325; 25 touches on GC-01).",
  evidence="Code; reported by the independent reviewer, verified by the producer against service.py:1173-1176 and routers/redesign.py:72-76.",
  reproduction="Read code. Not reproduced (would need concurrent live requests).", stage="15/16/19 engineer changes, plan persistence, Apply",
  cause_status="CONFIRMED (code); NOT REPRODUCED", cause="Whole-row JSON rewrite without optimistic locking.", confidence="High",
  deterministic="Timing-dependent", code="service.py:1146, 1175, 1181, 1247, 1324-1325; routers/redesign.py:70-90", milestone="RD-M6 workflow (proposed)")

f(id="RD-M1-F033", primary="H. CAD Apply - output overwritten (minute-resolution name)", secondary="H. output saved to wrong location",
  severity="Medium", expected="Every Apply output has a unique name; nothing is overwritten silently.",
  actual="The output name uses the stamp %Y-%m-%d %H%M (service.py:1383-1385); shutil.copyfile (cad.py:170) and open(..., wb) into the archive (service.py:1396) overwrite silently, so two Applies in the same minute replace the earlier DWG in uploads and in the archive. Jobs 103 and 104 ran 76 s apart (different minutes).",
  evidence="Code; E02 timings. Reported by the independent reviewer, verified by the producer.", reproduction="Read code.",
  stage="24 output registration", cause_status="CONFIRMED (code); NOT REPRODUCED", cause="Name collision.", confidence="High",
  deterministic="Timing-dependent", code="service.py:1383-1396; cad.py:169-170", milestone="RD-M2 (proposed)")

f(id="RD-M1-F034", primary="G. Workflow - Apply cannot be cancelled", severity="Low",
  expected="A running Apply honours the job's cancel request.",
  actual="apply() accepts check= but never calls it; the AutoCAD run can take up to 1,200 s (cad.py:34).",
  evidence="service.py:1360-1410 (no use of check); reported by the independent reviewer, verified by the producer.", reproduction="Read code.",
  stage="22/25", cause_status="CONFIRMED (code)", cause="Not implemented.", confidence="High", deterministic="Yes",
  code="service.py:1360-1410; cad.py:34, 159-161", milestone="RD-M2 (proposed)")

f(id="RD-M1-F035", primary="G. Workflow - confirm flag not gating", secondary="A. scale/origin error carried", severity="Low",
  expected="An added symbol flagged confirm (plot error above 1 m) is not drawn until confirmed.",
  actual="view() computes confirm (residual > CONFIRM_ABOVE_M) for display only; _drawn() ignores it. Not triggered on GC-01 (max residual 0.55 m).",
  evidence="service.py:1433-1434 vs 667-671; reported by the independent reviewer, verified by the producer.", reproduction="Read code.",
  stage="18", cause_status="CONFIRMED (code)", cause="Display-only flag.", confidence="High", deterministic="Yes",
  code="service.py:63, 667-671, 1433-1434", milestone="RD-M2 (proposed)")
'''
anchor = "\nCOLS = ["
assert anchor in s
s = s.replace(anchor, NEW + anchor, 1)
s = s.replace("(31 findings)", "(35 findings)")
open(p, "w", encoding="utf-8").write(s)
print("patched")
